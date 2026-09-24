# P1-S2-R2 A调研：接入机制 — REST API v2

调研对象：Frappe 16.34.0（`D:\ERX-001\frappe-bench\apps\frappe`）、ERPNext 16.35.0。
全部结论为**读码所得**，推断处已标注。未实跑任何请求。

## ① 路径清单

分派总入口：`frappe/app.py:157-158` — `request.path.startswith("/api/")` → `frappe.api.handle(request)`。
路由表在 `frappe/api/__init__.py:91-100`，用 werkzeug `Map` + `Submount` 三段挂载：

| 挂载前缀 | 规则来源 | 注册点 |
|---|---|---|
| `/api` （无版本，旧路径） | v1 rules | `api/__init__.py:94` |
| `/api/v1` | v1 rules | `api/__init__.py:95` |
| `/api/v2` | v2 rules | `api/__init__.py:96` |

关键：`/api/resource/...` 与 `/api/v1/resource/...` 是**同一套规则**，v1 规则被挂了两次。`strict_slashes=False`，尾斜杠可省。匹配失败转 `frappe.DoesNotExistError`（`api/__init__.py:60-61`）。

v1 规则（`frappe/api/v1.py:144-152`）：

| 路径 | 方法 | endpoint |
|---|---|---|
| `/method/<path:method>` | 全部 | `handle_rpc_call` → `frappe.handler.handle()` |
| `/resource/<doctype>` | GET | `document_list`（走 `frappe.client.get_list`） |
| `/resource/<doctype>` | POST | `create_doc` |
| `/resource/<doctype>/<name>/` | GET / PUT / DELETE | `read_doc` / `update_doc` / `delete_doc` |
| `/resource/<doctype>/<name>/` | POST | `execute_doc_method`（方法名走 `run_method` 参数） |

v2 规则（`frappe/api/v2.py:274-302`）：

| 路径 | 方法 | endpoint |
|---|---|---|
| `/method/login`、`/method/logout`、`/method/ping`、`/method/upload_file` | — | 专用 endpoint（v2.py:276-279） |
| `/method/<method>` | 全部 | `handle_rpc_call`（v2.py:280） |
| `/method/run_doc_method` | GET/POST | `run_doc_method`（内存态文档跑控制器方法，v2.py:281-285） |
| `/method/<doctype>/<method>` | 全部 | `handle_rpc_call`，自动展开为该 doctype 控制器模块的方法（v2.py:28-34、286） |
| `/document/<doctype>` | GET | `document_list`（直接用 `frappe.qb.get_query`，**不走** `frappe.client`） |
| `/document/<doctype>` | POST | `create_doc` |
| `/document/<doctype>/<name>/` | GET | `read_doc` |
| `/document/<doctype>/<name>/copy` | GET | `copy_doc` |
| `/document/<doctype>/<name>/` | **PATCH** / PUT | `update_doc` |
| `/document/<doctype>/<name>/` | DELETE | `delete_doc` |
| `/document/<doctype>/<name>/method/<method>/` | GET/POST | `execute_doc_method` |
| `/doctype/<doctype>/meta` | GET | `get_meta` |
| `/doctype/<doctype>/count` | GET | `count` |

## ② v1 vs v2 差异

v2 独有（v1 无）：
- `/doctype/<dt>/meta`、`/doctype/<dt>/count`（v2.py:300-301）——v1 要靠 `/api/method/` 绕。
- `/document/<dt>/<name>/copy`（v2.py:291）——取一份可改后 POST 新建的干净副本，**对"从中间节点起跑"有用**。
- `/method/run_doc_method`（v2.py:242-271）——对**尚未入库的内存文档**跑白名单控制器方法（如 `set_missing_values`），返回修改后的文档。v1 的 `handler.run_doc_method` 存在但未注册为独立 v2 式路由。
- `/method/<doctype>/<method>` 双段形式，省掉写全模块路径。
- 分页信号：`frappe.response["has_next_page"]`（v2.py:159）。
- 显式方法语义：`/document/.../method/<method>/` 把方法名放进路径，v1 是塞 `run_method` 参数（v1.py:116）。
- PATCH 被接受（v2.py:292）。
- 列表参数用 `start`/`limit`（v2.py:121-122），v1 用 `limit_start`/`limit_page_length`（v1.py:20-23）。
- `read_doc` 把整数值的 Link 字段转字符串（v2.py:70-73），v1 不转。

v1 独有 / v2 缺的：
- **v2 没有批量写入路由**。`insert_many`、`bulk_update` 只能经 `/api/v2/method/frappe.client.insert_many` 调用（方法本身在 `client.py:232`、`306`）——即 v2 也能用，但是走 RPC 通道而非 document 路由。
- v1 的 `document_list` 支持 `expand` / `expand_links` 参数做链接字段展开（v1.py:16-17、82-86）；**v2 的 `read_doc`/`document_list` 没有这个能力**（读码对比 v2.py:64-160，无 expand 分支）。这是**唯一查实的"仅 v1 有"的便利能力**。
- v1 `create_doc` 用 `get_request_form_data()`（v1.py:132-141）解析裸 body JSON；v2 `create_doc` 直接吃 `frappe.form_dict`（v2.py:172）。**推断**：两者对 `Content-Type: application/json` 的 body 都能work（form_dict 由 app 层填充），但 v1 的解析路径更宽松。此点未实跑验证。

**结论：脚本可以只用 v2**，唯一代价是放弃 `expand_links` 自动展开（可用多次 GET 替代）。

## ③ 白名单规则

装饰器 `frappe.whitelist(allow_guest=False, xss_safe=False, methods=None)` 在 `frappe/__init__.py:439-476`：
- `methods` 缺省为 `["GET","POST","PUT","DELETE"]`（`__init__.py:454-455`）；写入 `allowed_http_methods_for_whitelisted_func[fn]`（:466）。
- 函数对象加入全局 `whitelisted` 集合（:465）；`allow_guest=True` 才进 `guest_methods`（:468-469）。
- 校验一：`is_whitelisted(method)`（`__init__.py:479-495`）——**按函数对象**判成员，非按字符串路径。Guest 且不在 `guest_methods` → `PermissionError`。Guest 且不在 `xss_safe_methods` 时会对整个 `form_dict` 做 HTML 转义（:489-494）。
- 校验二：`is_valid_http_method(method)`（`handler.py:99-110`）——当前请求方法不在该函数的 `methods` 列表则 `throw_permission_error()`。`in_safe_exec` 或后台 job 时跳过（:100-104）。

`/api/v2/method/` 的可调用范围（`v2.py:36-51`）：先 `frappe.override_whitelisted_method`，再查 Server Script `_api` 映射（可被 Server Script 劫持，:39-41），再 `frappe.get_attr(method)` 按点分路径取属性，然后 `is_whitelisted` + `is_valid_http_method`，最后 `frappe.call(method, **frappe.form_dict)`。
**即：任何被 `@frappe.whitelist()` 装饰过的、可由点分路径取到的模块级函数都能调**，无路径白名单表、无模块前缀限制。文档级方法另有 `doc.is_whitelisted(method_name)`（`model/document.py:1665-1670`），同样落到全局 `is_whitelisted`。

## ④ ⭐ 建单 + 提交的最小调用序列

**最少 2 个 HTTP 调用**（建 + 提交）。**1 个调用也可行**，见方案 B。

### 方案 A（2 调用，推荐，路由最正统）

**调用 1 — 建草稿**
```
POST /api/v2/document/Sales Order
Content-Type: application/json
Authorization: token <api_key>:<api_secret>
```
```json
{
  "customer": "演示客户A",
  "company": "演示公司",
  "transaction_date": "2026-09-23",
  "delivery_date": "2026-09-30",
  "currency": "CNY",
  "conversion_rate": 1,
  "selling_price_list": "标准售价",
  "plc_conversion_rate": 1,
  "items": [
    {"item_code": "FG-001", "qty": 10, "uom": "Nos",
     "delivery_date": "2026-09-30", "rate": 100}
  ]
}
```
返回 `data.name`（如 `SAL-ORD-2026-00001`）与 `data.modified`。
子表**嵌套写入**由 `frappe.new_doc(doctype, **data)`（v2.py:175）承接——`new_doc` 走 `Document.update`，对 Table 字段接受 dict 列表。**此点为推断**（未实跑），依据是 `create_doc` 直接把整个 payload 交给 `new_doc`，无子表剥离逻辑。

**调用 2 — 提交（三种查实的做法，任选）**

| 做法 | 请求 | 依据 |
|---|---|---|
| **A1（最少字段，首选）** | `POST /api/v2/document/Sales Order/<name>/method/submit/` | `v2.py:294-298` 路由 → `execute_doc_method`；`Document.submit` 在 `model/document.py:1346-1349` 有 `@frappe.whitelist()`，故 `doc.is_whitelisted("submit")` 通过；`PERMISSION_MAP["POST"]="write"`（v2.py:22-25）。**无需带 body。** |
| A2 | `PUT`/`PATCH /api/v2/document/Sales Order/<name>/` body `{"docstatus": 1, "modified": "<原值>"}` | `update_doc`（v2.py:194-207）→ `doc.save()`；`check_docstatus_transition(0)` 见 docstatus 由 0 变 1 时把 `_action` 设为 `"submit"` 并 `check_permission("submit")`（`document.py:1129-1134`）。**确实可行**，但需回传 `modified` 否则 `TimestampMismatchError`（`document.py:1108-1114`）。 |
| A3 | `POST /api/v2/method/frappe.client.submit` body `{"doc": {...完整文档 JSON...}}` | `client.py:270-282`，`methods=["POST","PUT"]`。要求传**整份文档**，对脚本更啰嗦。 |

**A1 是最少字段的提交方式。** A2 可行但需 `modified` 做乐观锁。

### 必填字段表（`reqd: 1`）

Sales Order（`erpnext/selling/doctype/sales_order/sales_order.json`，`autoname: naming_series:`，`is_submittable: 1`）：

| 字段 | 类型 | options | 默认 | 说明 |
|---|---|---|---|---|
| `naming_series` | Select | `SAL-ORD-.YYYY.-` | 无 | 只有一个选项，**推断**可省（Select 单选项通常自动取首项）——未查实，建议显式传 |
| `customer` | Link | Customer | — | 须传 |
| `order_type` | Select | Sales/Maintenance/Shopping Cart | `Sales` | 有默认，可省 |
| `company` | Link | Company | — | 须传 |
| `transaction_date` | Date | — | `Today` | 有默认，可省 |
| `currency` | Link | Currency | — | 须传 |
| `conversion_rate` | Float | — | — | 须传（本币单据传 1） |
| `selling_price_list` | Link | Price List | — | 须传 |
| `price_list_currency` | Link | Currency | — | **read_only=1**，服务端填 |
| `plc_conversion_rate` | Float | — | — | 须传（传 1） |
| `items` | Table | Sales Order Item | — | 须传，至少一行 |
| `status` | Select | Draft/… | `Draft` | **read_only=1**，服务端填 |

Sales Order Item（`.../sales_order_item/sales_order_item.json`）：

| 字段 | 类型 | options | 说明 |
|---|---|---|---|
| `item_code` | Link | Item | 须传 |
| `item_name` | Data | — | 标 reqd 但由 `item_code` 联带取值，**推断**可省 |
| `qty` | Float | — | 须传 |
| `uom` | Link | UOM | 标 reqd，通常由 item 的 `stock_uom` 联带；**建议显式传**，参见 MEMORY 里 v16 `stock_uom` 缺口那条 |
| `conversion_factor` | Float | — | **read_only=1**，服务端算 |

**额外硬性字段（不在 reqd 里但 submit 必过）**：`delivery_date`。`sales_order.py:425-445` 的 `validate_delivery_date`：当 `order_type == "Sales"` 且 `skip_delivery_note` 为假时，若行项与单头都无 `delivery_date` → `frappe.throw(_("Please enter Delivery Date"))`（:445）。且 `transaction_date > 行项 delivery_date` 也 raise（:437-443）。**脚本必须传 `delivery_date` 且不早于 `transaction_date`。**

### 方案 B（1 调用）

```
POST /api/v2/method/frappe.client.insert
body: {"doc": {"doctype": "Sales Order", ...全部字段..., "docstatus": 1}}
```
`client.py:220-228`。**但 `docstatus:1` 能否在 insert 时直接生效未查实**——`check_docstatus_transition` 对新文档走的是 `if not previous ... return`（`document.py:1103-1106`），即新建时**不做**转换检查，故 `docstatus=1` 可能被直接写入而**跳过 `on_submit` 钩子**。对本项目的 23 环节闭环（需要 `on_submit` 触发下游单据）**这是坑，不要用**。此为推断，标记为风险项。

### 隐含依赖（须先存在）

- **Customer**（`customer` Link）、**Item**（`item_code` Link）、**Company**、**Currency**、**Price List**（`selling_price_list`）、**UOM**。
- **财年（Fiscal Year）**：未在本次调研中查实 Sales Order 的直接依赖点（Sales Order 本身无 `fiscal_year` reqd 字段）。**推断**下游 Sales Invoice / GL 环节必需。标记未查实。
- Item 的 `stock_uom`、默认价目表/币种——见 MEMORY 的 `erx001-v16-fresh-install-gaps.md`，v16 全新装有缺口。

## ⑤ `frappe.client` 可用白名单方法

全在 `D:\ERX-001\frappe-bench\apps\frappe\frappe\client.py`，均可经 `/api/v2/method/frappe.client.<name>` 调用：

| 方法 | 行号 | allowed methods | 签名要点 / 限制 |
|---|---|---|---|
| `get_list` | 26 | 默认全部 | 列表查询 |
| `get_count` | 78 | 默认全部 | 计数 |
| `get` | 94 | 默认全部 | 取单文档 |
| `get_value` | 120 | 默认全部 | 取字段值 |
| `get_single_value` | 175 | 默认全部 | `(doctype, field)` Single 型 |
| `set_value` | 183 | POST, PUT | `(doctype, name, fieldname, value=None)`；`fieldname` 可为 dict/JSON 批量改多字段；**禁改标准字段**（`default_fields + child_table_fields` → throw，:191-192）；**能改子表行**（istable 分支 :208-214）；内部 `doc.save()`，**故也能用来提交**（传 `docstatus`）——但 `docstatus` 属标准字段，会被 :191 拦掉。**推断不可用于提交。** |
| `insert` | 220 | POST, PUT | `(doc)` JSON 或 dict |
| `insert_many` | 231 | POST, PUT | `(docs)` 列表；**上限 200**（:239-240）；返回 name 列表。**批量造数据首选。** |
| `save` | 245 | POST, PUT | `(doc)` 整份文档 |
| `rename_doc` | 259 | POST, PUT | `(doctype, old_name, new_name, merge=False)` |
| `submit` | 270 | POST, PUT | `(doc)` **要整份文档 JSON**，非 `(doctype, name)` |
| `cancel` | 284 | POST, PUT | `(doctype, name)` — 注意与 `submit` 签名不对称 |
| `delete` | 296 | DELETE, POST | `(doctype, name)` |
| `bulk_update` | 305 | POST, PUT | `(docs)` JSON 列表，每项须有 `docname`；**失败不中断**，返回 `{"failed_docs": [...]}`（:311-322）。 |
| `has_permission` | 324 | 默认全部 | `(doctype, docname, perm_type="read")` |
| `get_doc_permissions` | 335 | 默认全部 | — |
| `get_password` | 346 | 默认全部 | — |
| `get_js` | 360 | 默认全部 | — |
| `get_time_zone` | 363 | 默认全部 | **allow_guest=True** |
| `attach_file` | 369 | POST, PUT | — |
| `is_document_amended` | 414 | 默认全部 | — |
| `validate_link_and_fetch` | 426 | GET, POST | — |

注：`insert_doc`（:528）、`delete_doc`（:547）**无 whitelist 装饰器**，仅内部用，外部不可调。

## ⑥ 拿不准 / 未实跑的

1. **子表嵌套写入**（`items` 数组随 POST 一次写入）——推断可行，依据是 `create_doc` 无子表剥离逻辑（v2.py:171-180），但未实跑。**这是第 4 点调用序列的关键假设，建议优先实跑验证。** 若不成立，退路是先建单头再对每行 `POST /api/v2/method/frappe.client.set_value` 或用 `insert` 传整份文档。
2. `naming_series` 单选项是否可省——未查实。
3. **方案 B（insert 时直接 `docstatus:1`）是否跳过 `on_submit`**——推断会跳过，属风险项，未实跑。对 23 环节闭环影响大。
4. **财年依赖**——未查实 Sales Order 的直接依赖点。
5. v1 vs v2 对裸 JSON body 的解析差异（v1 `get_request_form_data` vs v2 直吃 `form_dict`）——未实跑。
6. 鉴权形式（`Authorization: token key:secret`）本次未读 `frappe/auth.py` 求证，按 Frappe 惯例写入示例，**标为未查实**。
7. Sales Order 的字段级权限、`Customer` 的 default price list 联带逻辑未查。
