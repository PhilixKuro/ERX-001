# P1-S5 开发方案 · Part3：应用配置、CRM、Insights、Raven 与三问

**来源需求**：[B 需求文档](../R02-需求文档/P1-S5-R2-B需求文档.md) §4.5～§4.7（需求 TS-008～011）｜**前置依赖**：Part2 全部任务（四个 App 已装在两站）｜**日期**：2026-10-05｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S5-R3-C开发方案-总纲.md](P1-S5-R3-C开发方案-总纲.md)（执行纪律见总纲 §九，本 Part 不重复）

## 接口契约

### 1. 应用配置脚本（总纲 A6）

```text
docker/configure-apps.sh [--site <站点>]        # 宿主侧入口，缺省取 .env 的 SITE_NAME；同 seed-demo.sh 的写法载入 .env、MSYS 防改写
  └─ 容器内：env/bin/python /workspace/docker/scripts/configure_apps.py --site <站点> --company <公司>
```

```python
# docker/scripts/configure_apps.py  —— 独立脚本：frappe.init/connect → 依次调下列函数 → commit → destroy
def configure_crm(company: str) -> dict: ...        # 返回改了哪些字段（旧值→新值），已是目标值的不写
def configure_raven() -> dict: ...                  # 同上；密钥不出现在返回值与输出里，只报「已设」／「未设」
def ensure_bot_and_functions() -> dict: ...         # 返回 {"bot": 名, "functions": [名…], "created": [...], "updated": [...]}
```

所需环境变量（`docker/.env`，不进 git；`docker/.env.example` 只加键名与注释、不加值）：

| 键 | 用途 | 缺省 |
|---|---|---|
| `RAVEN_LLM_URL` | LiteLLM 的 OpenAI 兼容地址 | `http://host.docker.internal:7999/v1` |
| `RAVEN_LLM_KEY` | LiteLLM 密钥（用户提供） | 无；**未设时 `configure_raven` 跳过密钥字段并打警告，不报错** |
| `RAVEN_LLM_MODEL` | bot 用的模型别名（用户提供，DEC-011） | 无；未设时 bot 照建、`model` 留空并打警告 |

### 2. 三问数据集（总纲 A7）

```python
# frappe_china/tests/raven_dataset.py
PREFIX: Final = "_FCT"                 # 与 tests/utils.py 的 TEST_PREFIX 同
def build(company: str | None = None) -> dict:    # 建全部数据并提交；返回各单据号。company 缺省时新建一家中式测试公司
def expected() -> dict:                            # 只从本模块常量算出标准答案，不读库
def verify_built(names: dict) -> list[str]:        # 反查库里的金额、概率、数量、单价、BOM 成本与常量一致；返回不一致项，空表示一致
def teardown(names: dict) -> None:                 # 逆序撤销并删除 build 建的全部记录（含公司），删前逐条核名字带 PREFIX
QUESTIONS: Final[dict[str, str]]                   # 三问问法原文（定稿见 TS-012），问 3 的销售订单号占位 {so}
```

### 3. 退路：自写查询函数（仅在触发时实现，需求 §4.6.4；总纲 A8）

```python
# frappe_china/ai/queries.py   —— 只读，一律 frappe.get_list（带权限）
@frappe.whitelist()
def top_weighted_deals(limit: int = 3) -> list[dict]: ...                 # 问 1：[{deal, expected_deal_value, probability, weighted}]
@frappe.whitelist()
def supplier_price_quality(item_code: str) -> list[dict]: ...             # 问 2：[{supplier, avg_rate, received_qty, rejected_qty, reject_rate}]
@frappe.whitelist()
def bom_unit_profit(sales_order: str, item_code: str) -> list[dict]: ...  # 问 3：[{bom, total_cost, quantity, unit_cost, so_rate, unit_profit}]
```
算法与 `expected()` 同一口径（见 TS-012 第 1 步的表）。触发哪一问才写哪一个函数。

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-005** CRM 链路与看板 | 需求 TS-008；DEC-007／008；LG-004／085；AC-001 | ① 两站跑 `configure-apps.sh` 后：`ERPNext CRM Settings.enabled=1`、`is_erpnext_in_different_site=0`、`sync_products=1`、`create_customer_on_status_change=0`、`erpnext_company`＝该站中式公司；`FCRM Settings.currency=CNY`；再跑一次输出「无改动」（幂等）。② 测试站：`/crm` 建 Lead → 转 Deal（金额、概率、预计成交日都填）→ 推进两档 → Deal 页生成报价单：公司、联系人、明细已预填，`quotation_to=CRM Deal`。③ 报价单提交 → 生成销售订单并保存：站上新增一个客户，其 `crm_deal` 指向该 Deal，销售订单的 `customer` 即它（LG-085 实测）。④ 新 Deal 的 `currency` 为 CNY；报价单与销售订单 `currency` 为 CNY，`conversion_rate`＝1（LG-004）。⑤ `/crm` 看板「预测收入」该月有值、等于 `金额×概率÷100`；「转化」各档计数含该 Deal。⑥ 异常路径：在未启用集成的情况下（临时把 `enabled` 置 0）Deal 页不出现生成报价单的入口或点了报错「ERPNext is not integrated with the CRM」；验完恢复 1。⑦ 清掉 Lead、Deal、报价单、销售订单、客户、临时物料后，测试站无残留（按名字前缀查） |
| **SL-006** Insights | 需求 TS-009；DEC-016；RS-005；AC-007 | ① 两站 `list-apps` 含 `insights`；② 登录后 `/insights` 返回 200 且页面标题含 Insights；③ 演示站对 `Site DB` 数据源建一个查询「`tabCompany` 行数」，结果为 1；④ **异常路径（装不上时）**：当场在 Stage 概况登记延迟需求（编号 `SH-P1S5006`，原文写失败的依赖与报错原文）、在路线文档 §四 S6 注明 331 条译名扣除；`apps.json` 去掉 Insights 条目；其余三个 App 的验收照常 |
| **SL-007** Raven 与三问 | 需求 TS-010／011；DEC-009～014／020；LG-006／009；RS-006／007；AC-003 | ① `configure-apps.sh` 后：`Raven Settings` 的 `enable_ai_integration=1`、`enable_local_llm=1`、`local_llm_provider=OpenAI Compatible`、`local_llm_api_url` 为配置值；密钥字段非空（不打印值）。② 演示 bot 存在、`is_ai_bot=1`、`model_provider=Local LLM`；其 `bot_functions` 恰为 TS-009 表中 15 条，**类型只有 `Get List`／`Get Document`／`Custom Function`**；站上无 `Update`／`Create`／`Delete`／`Submit`／`Cancel`／`Set Value` 类的 `Raven AI Function`。③ 向 bot 发「你好」得到非报错回复（连接通）；`RAVEN_LLM_KEY` 故意设错时同一操作得到报错回复或后台 Error Log 记一条鉴权失败（依赖不可用的异常路径），恢复后再通。④ 报表通道：让 bot 跑一次 `Item-wise Purchase History` 并复述行数，与界面上同一报表同一过滤条件的行数一致（LG-006），不通则记下并按需求 §4.6.4 处理。⑤ `raven_dataset.build()` 后 `verify_built()` 返回空；数据满足 TS-012 第 1 步「判别性」五条（单测断言）。⑥ 三问各跑 3 次，测试报告按 TS-012 第 4 步的格式写成，每问给出结论「答得出／答不出／改走退路后答得出」。⑦ `teardown()` 后测试站无 `_FCT` 前缀记录；演示站从未建过三问数据 |

**执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。**

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-009 应用配置脚本（CRM、Raven 设置、bot 与只读工具） | SL-005、SL-007 | 否 |
| TS-010 CRM 实点与看板（测试站） | SL-005 | 否 |
| TS-011 Insights 验收 | SL-006 | 否 |
| TS-012 Raven 连通、报表通道、三问数据与实测 | SL-007 | 否 |

---

## 任务 TS-009：应用配置脚本（对应 SL-005、SL-007）

### 目标
两站的 CRM 集成、Raven 连接、演示 bot 与只读工具由一个幂等脚本配出，新机器与 S7 可重放（总纲 A6）。

### 具体改动

1. **`docker/configure-apps.sh`**（宿主侧，照 `docker/seed-demo.sh` 的骨架）＋**`docker/scripts/configure_apps.py`**（容器内）。脚本找不到对应 DocType 时（某 App 没装）跳过该段并打一行说明，不报错。`--company` 缺省取站上唯一一家 `chart_of_accounts = 小企业会计准则(2024)` 的公司；有零家或多家时报错要求显式传。

2. **`configure_crm(company)`**：

   | 对象 | 字段 | 值 | 说明 |
   |---|---|---|---|
   | `FCRM Settings` | `currency` | `CNY` | 设一次后被 CRM 设成只读（`fcrm_settings.py:105-113`），已是 CNY 则不写 |
   | `ERPNext CRM Settings` | `enabled`／`is_erpnext_in_different_site`／`sync_products`／`create_customer_on_status_change`／`erpnext_company` | `1`／`0`／`1`／`0`／`company` | `erpnext_company` 被生成报价单时用作公司（`erpnext_crm_settings.py:459-490`）；启用时 CRM 会建自定义字段与报价单预填脚本（`validate`） |
   | `FCRM Settings` | `enable_forecasting` | **不改（保持 0）** | 看板的预测收入查询不读它（`dashboard.py:657-730`），开了反而要求每张 Deal 必填金额与日期（`crm_deal.py:255-259`）；前端是否以它门控图表未验证（HT-014） |

   **Deal 币种**（LG-004）：先不加任何配置，依 HT-005（新建 Deal 时 `currency` 取全局默认 CNY）。TS-010 第 2 步实测不成立时，在本函数加一条 `Property Setter`：`CRM Deal.currency` 的 `default` 为 `CNY`（L0），重跑。

3. **`configure_raven()`**：`Raven Settings` 设 `enable_ai_integration=1`、`enable_local_llm=1`、`local_llm_provider="OpenAI Compatible"`、`local_llm_api_url=$RAVEN_LLM_URL`、`openai_compatible_api_key=$RAVEN_LLM_KEY`（Password 字段，经 `doc.set` 后 `save`，框架加密存）。`enable_openai_services` 不动。输出只报「密钥：已设／未设」。

4. **`ensure_bot_and_functions()`**：按名 upsert。bot 名 `ERX 分析助手`（`autoname: field:bot_name`）；`is_ai_bot=1`、`model_provider="Local LLM"`、`model=$RAVEN_LLM_MODEL`、`allow_bot_to_write_documents=0`、`enable_code_interpreter=0`、`enable_file_search=0`、`debug_mode=1`（让报错回复带原因，便于实测；演示前由 S7 关掉，记进 S7 输入）。`instruction` 全文：

   > 你是华东弹簧有限公司的经营分析助手，只读，不修改任何数据。回答任何问题前，先用工具取数，不凭记忆回答。只统计已提交的单据（docstatus = 1），草稿与已取消的单据不算。回答的最后一段列出你用到的单据号或报表名。金额保留两位小数，百分比保留一位小数。用中文回答。

   **只读工具 15 条**（`Raven AI Function`，`autoname: field:function_name`，名字即工具名，须是合法标识符）：

   | # | function_name | type | reference_doctype | 用于 |
   |---|---|---|---|---|
   | 1 | `list_crm_deals` | Get List | CRM Deal | 问 1 |
   | 2 | `get_crm_deal` | Get Document | CRM Deal | 问 1 |
   | 3 | `list_crm_deal_statuses` | Get List | CRM Deal Status | 问 1（状态类型 Won／Lost） |
   | 4 | `list_purchase_receipts` | Get List | Purchase Receipt | 问 2（主表：供应商、单号、docstatus） |
   | 5 | `get_purchase_receipt` | Get Document | Purchase Receipt | 问 2（整单含明细：`received_qty`／`rejected_qty`／`qty`／`rate`，LG-009） |
   | 6 | `list_suppliers` | Get List | Supplier | 问 2 |
   | 7 | `list_items` | Get List | Item | 问 2、问 3 |
   | 8 | `get_item` | Get Document | Item | 问 2、问 3 |
   | 9 | `list_sales_orders` | Get List | Sales Order | 问 3 |
   | 10 | `get_sales_order` | Get Document | Sales Order | 问 3（明细里的单价） |
   | 11 | `list_boms` | Get List | BOM | 问 3（`item`／`is_active`／`total_cost`／`quantity`） |
   | 12 | `get_bom` | Get Document | BOM | 问 3 |
   | 13 | `list_customers` | Get List | Customer | 问法外的追问 |
   | 14 | `get_supplier` | Get Document | Supplier | 同上 |
   | 15 | `run_report` | **Custom Function** → `raven.ai.functions.get_report_result` | — | 报表通道（DEC-009）；`params` 显式写 JSON Schema：`report_name`（string，必填，描述里列出可用报表名：`Item-wise Purchase History`、`Purchase Analytics`、`Purchase Receipt Trends`、`Supplier Quotation Comparison`、`BOM Explorer`、`BOM Stock Report`）、`filters`（object，必填，描述写明各报表常用的过滤键 `company`／`from_date`／`to_date`） |

   每条的 `description` 用中文一句话写清「取什么、何时用」；Get List 类的描述里列出该问要用的字段名（AI 只能取 `meta.fields` 里的字段，`parent` 不在其中——LG-009），例如 #4：「列采购入库单。常用字段：name、supplier、posting_date、docstatus。明细（收货数、拒收数、单价）不在这里，用 get_purchase_receipt 逐张取。」
   upsert 后把 15 条按上表顺序写进 bot 的 `bot_functions`；**再查站上有无非这 15 条、且类型属于写操作（`Update`／`Create`／`Delete` 等）的 `Raven AI Function`**——有则列出名字并报错退出，不删（不擅自删别人的记录），交用户处理。

5. **`docker/.env.example`** 加三个键名与注释（无值）；`docker/README.md` 加「配置四个 App」一节：何时跑、要先在 `.env` 填哪三个值、跑两次是安全的。

### 验证方式
两站各跑两次：第一次输出改动清单，第二次输出「无改动」。SL-005 ①、SL-007 ①② 的字段逐个在回执里贴值（密钥只贴「已设」）。

## 任务 TS-010：CRM 实点与看板（对应 SL-005）

### 目标
完成标志①：线索到销售订单的链路在 `/crm` 与 `/desk` 两套界面间实点通过（DEC-007／008）。

### 具体改动（操作步骤，测试站）

测试站浏览器访问须另起服务（`erx.localhost` 是默认站点）：容器内 `../env/bin/python -m frappe.utils.bench_helper frappe --site test.localhost serve --port 6787`，宿主访问 `http://localhost:6787`，用完结束（项目概况「开发环境」所记做法）。

1. 建临时物料 `_FCT CRM 演示簧`（库存物料，`stock_uom` 取「支」）并设一个标准售价；确认 CRM 的产品同步把它映射进 `CRM Product`（`sync_products=1`；同步是后台任务，没出现时在 CRM 设置页点一次同步）。
2. `/crm` 建 Lead（组织名 `_FCT 客户 CRM`、联系人、手机号）→ 转为 Deal；在 Deal 上填 `expected_deal_value=100000`、`probability=50`、`expected_closure_date` 取本月最后一天，产品加一行 `_FCT CRM 演示簧`。**查 `currency`**：为 CNY 则 HT-005 成立；为空或其它则按 TS-009 第 2 条加 Property Setter、删掉这条 Deal 重做本步。
3. 把 Deal 状态推进两档（`Qualification` → `Demo/Making` → `Proposal/Quotation`）。
4. Deal 页点生成报价单（新标签页打开 `/desk/quotation/new`）：核公司、联系人、明细预填，`quotation_to=CRM Deal`、`party_name`＝该 Deal；补交货日期等必填后提交。
5. 报价单上「创建 → 销售订单」→ 填交货日期 → 保存：核站上新出现一个客户（`crm_deal`＝该 Deal），销售订单 `customer` 为它；核报价单与销售订单 `currency=CNY`、`conversion_rate=1`。
6. 回 `/crm` 看板：「预测收入」本月值为 50000.00（`100000×50÷100×汇率 1`）；「转化」含 Deal 推进过的各档计数。
7. 异常路径（SL-005 ⑥）：`ERPNext CRM Settings.enabled` 临时置 0，刷新 Deal 页核入口与报错；恢复 1 后重跑 `configure-apps.sh` 确认「无改动」。
8. 清理：逆序删除销售订单（未提交，直接删）、报价单（取消后删）、客户、联系人、Deal、Lead、`CRM Product`、物料；按 `_FCT` 前缀查无残留。

### 验证方式
SL-005 ②～⑦ 每步截图（存 `Spike/P1-S5-R4-TS010-*.png`，与 S4 的界面证据同一放法）并在回执里写关键值。

## 任务 TS-011：Insights 验收（对应 SL-006）

### 目标
用最小代价验掉 RW-02（DEC-016）。

### 具体改动（操作步骤）

1. 两站 `list-apps` 核 `insights`（TS-006／007 已装）。装失败的情形已在 TS-006 第 1 步转到本任务的异常路径：执行 SL-006 ④ 的四个动作后本任务结束。
2. 演示站浏览器打开 `/insights`，登录状态下页面可用；数据源列表有 `Site DB`（Insights 安装时自建，`insights_data_source_v3.py:64-67`）。
3. 新建查询：数据源 `Site DB`、表 `tabCompany`、计数 → 结果 1。截图存证后**删除该查询**（不在演示站留 Insights 记录以外的东西）。

### 验证方式
SL-006 ①～③ 截图与数值写进回执。

## 任务 TS-012：Raven 连通、报表通道、三问数据与实测（对应 SL-007）

### 目标
完成标志③：只读 bot 经 LiteLLM 连通，用户那三问各实测 3 次并记录答得出与否（DEC-010）。

### 具体改动

**第 1 步：三问数据集 `frappe_china/tests/raven_dataset.py`**（总纲 A7）。全部名字带 `_FCT` 前缀；建在测试站一家新建的中式测试公司下；**不含税**（采购入库、销售订单都不挂税模板，`rate` 即不含税单价，避免「含税／不含税」成为答错原因）。

问 1 数据（`CRM Deal`，概率显式写入、与状态默认概率一致）：

| Deal | 状态 | `expected_deal_value` | `probability` | 加权金额 |
|---|---|---|---|---|
| `_FCT 商机 01` | Qualification | 1,000,000 | 10 | 100,000 |
| `_FCT 商机 02` | Demo/Making | 800,000 | 25 | **200,000** |
| `_FCT 商机 03` | Proposal/Quotation | 300,000 | 50 | 150,000 |
| `_FCT 商机 04` | Negotiation | 250,000 | 70 | **175,000** |
| `_FCT 商机 05` | Ready to Close | 200,000 | 90 | **180,000** |
| `_FCT 商机 06` | Demo/Making | 500,000 | 25 | 125,000 |
| `_FCT 商机 07` | Ready to Close | 150,000 | 90 | 135,000 |
| `_FCT 商机 08`（干扰） | Won | 2,000,000 | 100 | — |
| `_FCT 商机 09`（干扰） | Lost | 1,500,000 | 0 | — |

标准答案：**02（200,000）、05（180,000）、04（175,000）**。只按金额排的前 3 是 01／02／06，不同；含进已赢的 08 时它会排第一。

问 2 数据（物料 `_FCT 压簧 Φ2.0`，三家供应商；每张入库单一行，收货数 1000）：

| 供应商 | 已提交入库单的单价（`rate`） | 每张拒收数 | 合格数（`qty`） | 平均单价（按 `qty` 加权） | 拒收率 |
|---|---|---|---|---|---|
| `_FCT 供应商甲` | 0.50／0.52／0.48 | 80 | 920 | 0.50 | 8.0% |
| `_FCT 供应商乙` | 0.60／0.62／0.58 | 10 | 990 | **0.60** | 1.0% |
| `_FCT 供应商丙` | 0.70／0.72 | 5 | 995 | 0.71 | 0.5% |

干扰项：甲的一张**草稿**入库单（收货 3000、拒收 0、单价 0.40）——算进去甲的拒收率变 4.0%、平均单价变低，会被错选；丙的一张**已取消**入库单（收货 1000、拒收 0、单价 0.30）。
「平均单价」定为**按合格入库数量 `qty` 加权的不含税单价 `rate`**（需求 §4.6.5 留 C 步定）；本数据每家各张的 `qty` 相同，故加权与简单平均相等——**有意为之**：问法问的是「选哪家」，平均法不该成为答错的来源；S7 的 100 条数据若各张数量不同，三问须重测（RS-007 已含）。
问法里的取舍规则：**拒收率不超过 5% 的供应商里平均单价最低者**。标准答案：**乙**。最便宜的是甲、拒收率最低的是丙，三者互不相同。

问 3 数据（物料 `_FCT 拉簧 T-1`；一张已提交销售订单，该物料单价 12.00；原料用 `_FCT 钢丝 A／B／C`，物料主数据 `valuation_rate` 分别 8.00／7.50／7.80，BOM 的 `rm_cost_as_per = Valuation Rate`、无工序、无废料）：

| BOM | `is_active` | `quantity` | 原料 | `total_cost` | 单位成本 | 单位利润 |
|---|---|---|---|---|---|---|
| B1（`is_default`） | 1 | 1 | 钢丝 A 1 kg | 8.00 | 8.00 | 4.00 |
| B2 | 1 | **10** | 钢丝 B 10 kg | 75.00 | 7.50 | **4.50** |
| B3 | 1 | 1 | 钢丝 C 1 kg | 7.80 | 7.80 | 4.20 |
| B4（干扰） | **0** | 1 | 钢丝 A 0.75 kg | 6.00 | — | — |

标准答案：**B2，单位利润 4.50**。不做除法时 B2 成本 75.00、排最差；算进无效的 B4 时它会被选中。
另建一张**草稿**销售订单（同物料、单价 20.00）作干扰——问法指定了单号，误用它即答错。

**判别性五条**（写进 `tests/test_raven_dataset.py` 的断言，从常量算）：问 1 加权前 3 ≠ 只按金额前 3，且无并列；问 2 最便宜者、拒收率最低者、答案三者互不相同；问 2 含进草稿时答案改变；问 3 有一个 `quantity ≠ 1` 的有效 BOM，不做除法时答案改变；问 3 含进无效 BOM 时答案改变。
`verify_built()` 在 `build()` 末尾自动调用，不一致即抛错（例如 ERPNext 算出的 `total_cost` 与 75.00 不符——那说明建法不对，不得改常量迁就）。
测试 `test_raven_dataset.py`：CRM 未装时 `skipTest`；在测试事务里 `build()` → 断言 `verify_built()` 为空 → 由事务回滚清理（不调 `teardown`）。

**第 2 步：连通**（SL-007 ③）。用户先在 `docker/.env` 填好三个 `RAVEN_*` 值（**执行者向用户索要，不自行编造**）；测试站跑 `configure-apps.sh --site test.localhost`。Raven 前端在 `/raven`；以 Administrator 登录（Raven 安装时已为其建 `Raven User`），给 bot 发私信「你好」，得到中文回复即通。异常路径：把 `RAVEN_LLM_KEY` 临时改错、重跑配置、再发一次，记下回复或 Error Log；改回、重跑、再通。**全程不把密钥写进任何地方**。

**第 3 步：报表通道**（SL-007 ④，HT-007）。数据集建好后（第 4 步之前）问 bot：「用报表通道跑一次 Item-wise Purchase History，过滤条件公司为 {测试公司}，告诉我一共几行。」与 `/desk/query-report/Item-wise Purchase History` 同过滤条件的行数比对。不通即在回执记 LG-006「不通」及原因，三问照常先走现成工具。

**第 3 步之前**：`bench --site test.localhost execute frappe_china.tests.raven_dataset.build`，记下返回的单据号；问 3 问法里的 `{so}` 用它填。

**第 4 步：三问实测**。问法原文（`QUESTIONS` 常量，定稿）：

- **问 1**：「当前进行中的商机里，按『预计成交金额 × 成交概率』算加权金额，加权金额最高的前 3 个是哪几个？请给出每个商机的加权金额，并说明依据。」
- **问 2**：「物料『_FCT 压簧 Φ2.0』有几家供应商供过货。按采购入库单统计：平均单价按合格入库数量加权；拒收率＝拒收数量 ÷ 收货数量。在拒收率不超过 5% 的供应商里，哪一家平均单价最低？请列出每家的平均单价与拒收率，并说明依据。」
- **问 3**：「销售订单 {so} 上的物料『_FCT 拉簧 T-1』有几个有效 BOM。按『订单单价 − BOM 单位成本』算单位利润，单位成本＝BOM 总成本 ÷ BOM 数量。哪个 BOM 的单位利润最高？请列出每个有效 BOM 的单位成本与单位利润，并说明依据。」

每问 3 次，**每次是一条新的私信**（Raven 对每条发给 bot 的私信新开一个对话线程，`raven/ai/ai.py:31-86`，故三次互不共享上下文）。判「对」须同时满足：所列名次或所选对象与 `expected()` 一致；数值误差不超过 0.01（金额）或 0.1 个百分点（拒收率）；回答里列出了依据（单据号或报表名）。

工具调用记录：从 LiteLLM 的请求日志取每次对话里的 `tool_calls`（函数名与参数），HT-015；取不到时该列写「未取到」，不影响判定（判定只看回答本身）。

**测试报告** `docs/01-需求摸底/S05-演示链路/R04-代码/P1-S5-R4-三问测试报告.md`（D 步产物，结构如下，每问一节）：

```
## 问 N
- 问法原文：…
- 模型别名：…（RAVEN_LLM_MODEL 的值）
- 标准答案：…（expected() 的输出）
| 次 | 回答摘要（名次／数值） | 对错 | 依据是否列出 | 工具调用 |
- 结论：答得出／答不出／改走退路后答得出
```

**第 5 步：退路**（需求 §4.6.4）。某问 3 次未全对，或报表通道不通且该问依赖它：为该问实现 `frappe_china/ai/queries.py` 中对应函数（接口契约 §3），加一条 `Custom Function` 记录（`function_path` 指向它，`pass_parameters_as_json=0`）、挂到 bot，**重跑该问 3 次**，报告注明「改走退路」；并按 RW-04 在回执里写一句「该问是否进演示」的建议，交用户裁决。函数配单测（用第 1 步数据集，断言与 `expected()` 一致）。

**第 6 步：清理**。`bench --site test.localhost execute frappe_china.tests.raven_dataset.teardown --kwargs "{'names': <第 3 步之前记下的返回值>}"`；按 `_FCT` 前缀查测试站无残留；Raven 的测试私信不清（它们是 Raven 自己的消息记录，不进业务数据；测试站可随时整站重建）。

### 验证方式
SL-007 ①～⑦ 逐条；测试报告写成；`run-tests --module frappe_china.tests.test_raven_dataset` 全过（CRM 未装时跳过）。
