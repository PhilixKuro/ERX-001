# P1-S7 通用计算 —— 开发方案·Part2：批次换算、拆单、工序数量、计件

**来源需求**：[R3 B 需求文档](../R03-需求文档/P1-S7-R3-B需求文档.md) §4.7～4.9、§4.11.3｜**前置依赖**：Part1 的 TS-001、TS-002（基线与字段）｜**日期**：2026-10-15｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S7-R4-C开发方案-总纲](P1-S7-R4-C开发方案-总纲.md)

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-006** 批次级单位换算 | 需求 TS-008、IM-012、DEC-013；总纲 HT-008／009，偏离 18 | ① 同一物料（库存单位 kg、交易单位「支」、`weight_uom`＝kg、展开长度 0.5 m）两个批次线密度 0.010 与 0.012 kg/m：采购收货、库存凭证、发货三类单据的行选两个批次，保存后 `conversion_factor` 分别为 0.005 与 0.006，`stock_qty`（库存凭证为 `transfer_qty`）＝数量×系数；② 库存单位为「支」、交易单位 kg 的物料，系数取倒数（200 与 166.666667）；③ 批次未填线密度、或物料未填展开长度时，系数等于原生 `get_conversion_factor` 的物料级值；④ 行单位等于库存单位时系数为 1、不受批次影响；⑤ 前端选批次后系数当场变化（D 回执附一张截图）；⑥ 前端绕过（直接 API 保存带错系数的行）时服务端改回批次系数 |
| **SL-007** 工时与拆单解耦 | 需求 TS-009、IM-013、DEC-014；总纲 A13 | ① 工序勾 `create_job_card_based_on_batch_size`、`batch_size`＝100、BOM 工序 `time_in_mins`＝40、BOM 数量 1、拆分数量空：10000 支工单提交后该工序恰 1 张 Job Card，`for_quantity`＝10000、`time_required`＝4000；② 拆分数量填 2500：4 张卡、各 2500、各 1000 分；拆分数量 3000：4 张（3000×3＋1000）；③ 经 `make_job_card`（工单表单「建任务单」）路径同样按拆分数量拆；④ 未勾该选项的工序照原生（1 张、整单数量）；⑤ 上游 `split_qty_based_on_batch_size` 源码哈希与登记值不同时，守卫测试失败并打印两个哈希 |
| **SL-008** 工序间数量传递 | 需求 TS-010、IM-015、DEC-016；总纲 A14／A17，偏离 3～6 | ① 三工序、1000 支工单：第一道报 950 完工（损耗 50）提交后，第二、三道的未开工卡 `for_quantity` 均为 950、`time_required` 按比例为原值×0.95；② 第二道已开工（有时间行）时，第一道提交后第二道卡不变、提交时出提示含差额 50，第三道仍按 950 调；③ 取消第一道的卡后，第二、三道回到 1000；④ 第二道拆成 4 张各 250：第一道 950 提交后，最后一张变 200、其余不变；第一道再取消，最后一张回到 250；⑤ 第二道按 950 报工能提交，不须填损耗或待生产数；三道走完后生产入库 950（带损耗 50）能提交，工单状态为 Completed（HT-012）；⑥ 后道卡的 `items` 原料需求量按比例变化 |
| **SL-009** 计件工资 | 需求 TS-013、IM-016、DEC-017；总纲偏离 7～9／19 | ① 某员工当月两张已提交 Job Card（一道用 BOM 工序单价 0.2、一道 BOM 工序无单价而取工序主数据 0.1），计件额＝Σ完工数×单价，损耗不计，与手算一致；② 生成的计件汇总单逐行列来源 Job Card、工序、完工数、单价、金额、日期；无单价的行金额 0 并标注；③ 提交后有一张已提交 `Additional Salary`：组件「计件工资」、金额＝合计、`payroll_date`＝月末、`ref_doctype`／`ref_docname` 回指汇总单、`overwrite_salary_structure_amount`＝0；④ 同员工同期间再生成被跳过、结果里报出；⑤ 取消汇总单后该 `Additional Salary` 也已取消；⑥ 员工无薪资结构分配时，该员工进 `problems`、其余员工照常；⑦ 草稿 Job Card 的时间行不计 |

执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-010 批次系数 | SL-006 | 否 |
| TS-011 拆单覆盖 | SL-007 | 否 |
| TS-012 工序间数量传递 | SL-008 | 否 |
| TS-013 计件汇总单与 Additional Salary | SL-009 | 否 |

---

## 任务 TS-010：批次系数（对应切片 SL-006）

### 目标

选了批次的单据行，`conversion_factor` 取该批次的「单支重量」换算（需求 §4.11.3）。前端带出、服务端在 `before_validate` 复核（HT-009：原生 validate 随后用新系数算派生量）。

### 具体改动

**换算方向的判定**（需求留 C 定）：以物料原生字段 `weight_uom` 认重量侧。单支重量 `w`＝`cn_unit_length_m`×批次 `cn_linear_density`（单位：`weight_uom`／支）。

| 库存单位 | 行单位 | 系数 |
|---|---|---|
| ＝`weight_uom` | ≠`weight_uom` | `w`（每支多少重量单位） |
| ≠`weight_uom` | ＝`weight_uom` | `1 / w` |
| 其它（含两者相同、`weight_uom` 为空） | | 不处理，回落原生 |

线密度字段的 label 写「kg/m」，description 写「单位：物料重量单位／米；物料重量单位须为 kg」；`weight_uom` 为空的物料不处理（不报错），README 已知限制写一句。

**`frappe_china/production/batch_uom.py`**

```python
BATCH_UOM_DOCTYPES: Final = {           # 父 DocType → (子表字段, 派生量字段)
    "Purchase Receipt": ("items", "stock_qty"),
    "Stock Entry": ("items", "transfer_qty"),
    "Delivery Note": ("items", "stock_qty"),
}

def batch_factor(item_code: str, batch_no: str | None, uom: str) -> float | None:
    """按上表返回系数；任一条件不满足返回 None（调用方回落原生）。
    精度：flt(x, 9)，与 conversion_factor 字段精度一致（执行者核 meta 的 precision）。"""

@frappe.whitelist()
def get_batch_conversion_factor(item_code: str, batch_no: str, uom: str) -> dict:
    """前端用：{"conversion_factor": batch_factor(...) or 原生 get_conversion_factor(item_code, uom)["conversion_factor"],
                "source": "batch" | "item"}。权限：Item read。"""

def apply_batch_factor(doc, method=None) -> None:
    """三类单据 before_validate：逐行，有 batch_no 时算 batch_factor；非 None 且与行值不同即改 row.conversion_factor。
    行无 batch_no 不动（原生物料级值已在）。"""
```

- **`hooks.py`**：三类 DocType 各加 `"before_validate": "frappe_china.production.batch_uom.apply_batch_factor"`（与既有的 Sales Order、Quotation 条目并存）。
- **前端** `frappe_china/public/js/batch_uom.js`，经 `doctype_js` 挂到三类单据：子表 `batch_no` 与 `uom` 两个字段变化时调 `get_batch_conversion_factor`，`frappe.model.set_value(cdt, cdn, "conversion_factor", …)`，后续派生量由原生 `conversion_factor` handler 重算（`transaction.js:1691-1715`、`stock_entry.js:1053-1055`）。只追加 handler，不改原生 handler。注意 `Purchase Receipt` 的 `doctype_js` 与既有 `Journal Entry`／`Payment Entry` 条目同在一个 dict，三类单据另加三个键。
- 批次换算对 `Purchase Receipt` 的 `received_stock_qty`、`rejected` 系列字段：原生 validate 以 `conversion_factor` 重算（HT-009 的依据），本任务不另处理；测试只断言 `stock_qty`。

### 验证方式

单测 `tests/test_batch_uom.py`：SL-006 ①～④、⑥（三类单据各造一张草稿 `insert()`；⑥ 直接给行写错系数再 `save()`）。SL-006 ⑤：测试站开采购收货表单选两个批次截图（`Spike/P1S7R5-D/` 下，与既有截图同法；没有浏览器自动化时手工截）。

---

## 任务 TS-011：拆单覆盖（对应切片 SL-007）

### 目标

工时仍按 `batch_size` 折算，拆单改读「任务单拆分数量」，为空则整单一张（需求 §4.7、DEC-014；总纲 A13，HT-003／004）。

### 具体改动

**`frappe_china/production/job_card_split.py`**

```python
UPSTREAM_SHA256: Final = "<执行时取上游函数 inspect.getsource 的 sha256 填入>"

def split_qty(wo_doc, row, qty):
    """替换 work_order.split_qty_based_on_batch_size。保持原函数的副作用与返回约定：
    设 row.batch_size（不按批建卡时设为 row.qty or wo.qty，同原生）、row.job_card_qty、调 get_serial_nos_for_job_card、返回剩余 qty。"""
    by_batch = cint(Operation.create_job_card_based_on_batch_size)
    if not by_batch:
        return _original(wo_doc, row, qty)                  # 未勾：完全走原生
    split = cint(_bom_operation_split_qty(wo_doc, row))    # BOM Operation.cn_job_card_split_qty
    chunk = split if split > 0 else qty                     # 空 → 整单一张
    row.job_card_qty = min(chunk, qty)
    qty -= row.job_card_qty
    get_serial_nos_for_job_card(row, wo_doc)
    return qty
    # row.batch_size 不改（保持 BOM 的 100），工时折算原生在 set_work_order_operations 已做完

def _bom_operation_split_qty(wo_doc, row) -> int:
    """取该工序行所属 BOM（Work Order Operation.bom；make_job_card 路径的 row 是 _dict，
    row.name 即 Work Order Operation 行名，从库里取 bom 与 operation），对应到 BOM Operation 行。
    对应规则：同一 BOM 内同 operation 的第 k 次出现 ↔ BOM Operation 中同 operation 的第 k 行；
    对不上返回 0（即整单一张，并 frappe.log_error 一条，便于发现对应规则失效）。"""

_original = None
def ensure_patched() -> None:
    """幂等：work_order 模块属性不是 split_qty 时，记下原函数到 _original 并替换。"""

def before_submit_work_order(doc, method=None) -> None:
    ensure_patched()
```

- **调用点**（A13）：`hooks.py` 加 `before_request = ["frappe_china.production.job_card_split.ensure_patched"]`、`before_job = [同]`；`doc_events["Work Order"]["before_submit"] = …before_submit_work_order`。`make_job_card` 是 HTTP 入口，经 `before_request` 已补。
- **守卫测试**：`inspect.getsource(_original or 当前模块上的原函数)` 的 sha256 与 `UPSTREAM_SHA256` 比，不同则失败并打印新旧哈希与「复核 job_card_split.split_qty 是否仍与上游语义一致，再更新哈希」。
- **README「后端覆盖登记」**一行（总纲 §七）：接入点 `work_order.split_qty_based_on_batch_size`（模块属性替换）／文件 `production/job_card_split.py`／作用／依赖 erpnext `12cd563f` 的 `work_order.py:2902-2915` 函数体与 `:1228`、`:2853` 两个按全局名调用的调用点／失效症状「勾了按批建卡的工序又按 `batch_size` 拆成多张卡」／复验法「跑 `test_job_card_split`」。

### 验证方式

单测 `tests/test_job_card_split.py`：SL-007 ①～⑤。①② 走 `work_order.submit()`；③ 调 `work_order.make_job_card(wo.name, json.dumps([row]))`（行形状同 `work_order.js:425-436`）。测试 `setUp` 显式 `ensure_patched()`，`tearDown` 不还原（同进程其余测试也应看到补丁后的行为）。

---

## 任务 TS-012：工序间数量传递（对应切片 SL-008）

### 目标

前道 Job Card 提交或取消后，按预计产出把其后各道未开工卡的数量对齐（需求 §4.8、DEC-016；总纲 A14／A17，偏离 3～6）。

### 具体改动

**`frappe_china/production/operation_flow.py`**

```python
def realign(work_order: str, from_idx: int) -> list[str]:
    """从 Work Order Operation idx == from_idx 的那道起，逐道向后级联。返回提示消息列表。
    wo = frappe.get_doc("Work Order", work_order)（for_update 锁工单行，防两张前道卡同时提交）
    ops = sorted(wo.operations, key=idx)；纠正卡（is_corrective_job_card）一律不计不改
    planned = wo.qty                                    # 首道计划量
    for op in ops:
        cards = Job Card where work_order, operation_id=op.name, docstatus!=2, 非纠正卡
        submitted = [c for c in cards if c.docstatus == 1]
        drafts    = [c for c in cards if c.docstatus == 0]
        started   = [c for c in drafts if _is_started(c)]
        idle      = [c for c in drafts if not _is_started(c)]   # 按 name 排序，「最后一张」＝排序末位
        if op.idx > from_idx:                           # 只改本道之后的
            target_idle = planned − Σ submitted.for_quantity − Σ started.for_quantity
            current_idle = Σ idle.for_quantity
            diff = target_idle − current_idle
            if diff and idle: _shift(idle, diff)          # 差额落最后一张；扣成负数时依次往前一张扣，至多扣到 0（偏离 4）
            elif diff and not idle: messages.append(差额提示)
        produced = Σ submitted.total_completed_qty + max(0, planned − Σ submitted.for_quantity)
        planned = produced                              # 下一道的计划量（A17）
    return messages

def _is_started(card) -> bool:      # 偏离 5
    return card.status != "Open" or any(t.from_time for t in card.time_logs)

def _set_card_qty(card, new_qty) -> None:   # 总纲 A14
    ratio = new_qty / card.for_quantity if card.for_quantity else 0
    time_required = WO Operation.time_in_mins / wo.qty * new_qty     # 同 work_order.py:2987
    frappe.db.set_value("Job Card", card.name, {"for_quantity": new_qty, "time_required": time_required})
    scheduled_time_logs 末行：time_in_mins 按 time_required − 其余行之和、to_time = from_time + 该时长
    items 子表各行：required_qty × ratio（ratio 为 0 时置 0）

def on_job_card_submit(doc, method=None) -> None:
    if doc.is_corrective_job_card or not doc.work_order: return
    for m in realign(doc.work_order, 本卡工序的 idx): frappe.msgprint(m)

def on_job_card_cancel(doc, method=None) -> None: 同上
```

- `for_quantity` 原为 0 的卡加回数量时 `ratio` 无从算：`items` 改为按原生 `get_required_items` 的口径重取（`required_qty × new_qty ÷ wo.qty`，`job_card.py:773`）。执行者统一用这一口径即可，不必区分。
- **`hooks.py`**：`doc_events["Job Card"] = {"on_submit": …on_job_card_submit, "on_cancel": …on_job_card_cancel}`。追加的处理器在原生 `on_submit`／`on_cancel`（已 `update_work_order`）之后、同一事务内执行（读码已确认，`frappe/model/document.py:1634-1661`）。
- 提示文案（源词，进 csv）：`Operation {0}: all Job Cards have started; {1} units differ from the previous operation's expected output. Please adjust manually.`
- 第二道已开工时第三道照调：第二道尚无已提交卡，其预计产出＝0＋max(0, 950−0)＝950，第三道即按 950 调（SL-008 ②）。已开工卡的数量不被改，只体现在本道的差额提示里。

### 验证方式

单测 `tests/test_operation_flow.py`：SL-008 ①～⑥。造三道工序的 BOM（第二道勾按批建卡、拆分数量 250，用于 ④；①～③ 用另一张不拆的 BOM），`Manufacturing Settings.disable_capacity_planning` 两种取值各跑一遍 ①（测试内 `set_single_value`、随事务回滚），覆盖有无 `scheduled_time_logs` 两种情形。⑤ 走完三道后建 `Manufacture` 库存凭证（`fg_completed_qty`＝950、`process_loss_qty`＝50）提交，断言工单 `status`；HT-012 的结论写进 D 回执。

---

## 任务 TS-013：计件汇总单与 Additional Salary（对应切片 SL-009）

### 目标

按员工按月汇总已提交 Job Card 的完工数×单价，提交后生成并提交一张 `Additional Salary`（需求 §4.9、DEC-017；总纲偏离 7～9／19，HT-014）。HRMS 未装时整块零动作（开发守则「依赖可选 app 的代码按 DocType 是否存在分支」）。

### 具体改动

**DocType `Piece Rate Summary`**（模块 `Production Plus`，可提交，naming series `PRS-.YYYY.-.#####`）

| 字段 | 类型 | 说明 |
|---|---|---|
| `employee`、`employee_name` | Link Employee／Data（fetch） | 必填 |
| `company` | Link，必填 | |
| `from_date`、`to_date` | Date，必填 | 自然月首尾 |
| `currency` | Link，只读 | 公司本位币 |
| `total_amount` | Currency，只读 | Σ行金额 |
| `additional_salary` | Link Additional Salary，只读 | 提交后回填 |
| `items` | Table → `Piece Rate Summary Item` | |

子表 `Piece Rate Summary Item`：`job_card`（Link）、`work_order`（Link）、`operation`（Link）、`log_date`（Date）、`completed_qty`（Float）、`rate`（Currency）、`rate_source`（Select：BOM Operation／Operation／无单价，源词按 A16）、`amount`（Currency）。

**`frappe_china/production/piece_rate.py`**

```python
PIECE_RATE_COMPONENT: Final = "计件工资"     # 记录名（偏离 19）
PIECE_RATE_ABBR: Final = "JJGZ"

def ensure_component() -> None:
    """HRMS 在时：Salary Component 不存在则建（type=Earning、depends_on_payment_days=0、is_tax_applicable=1），幂等。
    挂 after_install 与 after_app_install("hrms")（install.py 两个既有入口里追加调用），并在 after_migrate 里补一次。"""

def collect_rows(employee, company, from_date, to_date) -> list[dict]:
    """Job Card Time Log 行：父卡 docstatus=1、company、非纠正卡；行 employee＝employee；
    行日期＝date(from_time) 或（无 from_time 时）父卡 posting_date，落在 [from_date, to_date]（偏离 7）。
    单价：BOM Operation.cn_piece_rate（按 Job Card.bom_no＋operation 对应，同 TS-011 的对应规则）＞0 取之；
    否则 Operation.cn_piece_rate ＞0 取之；否则 rate=0、rate_source=无单价（需求 §4.9）。
    amount = flt(completed_qty × rate, 金额精度)。损耗不计：只用 completed_qty。"""

class PieceRateSummary(Document):
    def validate(self): 重算 items 与 total_amount（collect_rows），from_date/to_date 须为同一自然月首尾
    def on_submit(self):
        if total_amount <= 0: throw「无计件金额」
        sal = Additional Salary：employee、company、currency、salary_component=PIECE_RATE_COMPONENT、
              amount=total_amount、payroll_date=to_date、overwrite_salary_structure_amount=0、
              ref_doctype="Piece Rate Summary"、ref_docname=self.name
        sal.insert(); sal.submit()          # 员工无薪资结构时 HRMS throw（HT-014），整单提交失败，原样报给用户
        self.db_set("additional_salary", sal.name)
    def on_cancel(self):
        已提交的 additional_salary → cancel()
        # 原生在 on_cancel 之后才查回链（document.py run_post_save_methods），此处先取消 AS，回链检查即过；
        # 若实测仍被「有已提交单据链接」拦住，暂停反馈，不加 ignore_links

def make_piece_rate_summaries(company, as_of_date) -> SummaryResult:   # 总纲 §5.2
    from_date, to_date = D 所在自然月首尾；D > today → throw
    employees = collect 期间内有已提交卡时间行的员工
    for emp:
        已有 docstatus=1 的同员工同期间单 → skipped
        否则在 savepoint 里 new → insert → submit；失败回滚该员工、problems 记原因
    return result

@frappe.whitelist()
def make_for_period(company: str, as_of_date: str) -> SummaryResult:
    """列表按钮用。权限：HR Manager 或 System Manager；调 make_piece_rate_summaries 后 commit。"""
```

- 「已有」只认已提交的单（需求 §4.9）；人手建的草稿不挡生成。人手提交同员工同期间第二张单时，`validate` 拒绝。
- HRMS 不在时：`make_piece_rate_summaries` 返回 `problems=["HRMS 未安装"]`、不建任何单；DocType 本身照常存在（表单可开但提交会报错，提示同上）。
- 列表 js：「按月生成」按钮弹框选公司与日期，调 `make_for_period`，结果逐条显示。

### 验证方式

单测 `tests/test_piece_rate.py`（HRMS DocType 不在时 `skipTest`）：造员工、`Salary Structure`（含一个基本工资组件）＋已提交 `Salary Structure Assignment`、两张工单的已提交 Job Card（时间行带员工），SL-009 ①～⑦；⑥ 另造一个无薪资结构分配的员工。期望金额写成常量。
