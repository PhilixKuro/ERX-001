# P1-S8 数据与操控 —— 开发方案·Part2：场景参数文件与一年期场景生成器

**来源需求**：[R4 B 需求文档](../R04-需求文档/P1-S8-R4-B需求文档.md) §4.3、§4.9｜**前置依赖**：Part1 全部（硬次序②，RW-03）｜**日期**：2026-10-20｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S8-R5-C开发方案-总纲](P1-S8-R5-C开发方案-总纲.md)——A1～A3、A7、A19，偏离 12／13／16，HT-019／020 在那里。

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-011** 一年期场景生成器 | 需求 TS-012、CR-012、DEC-011／012／026／038／039、`PH-P1092`／`1096`；§4.9.3 十二条约束 | ① 参数校验（单测）：缺必填键、起止颠倒、时间线日期落在场景外、三规则启用日次序颠倒、分布参数越界、`E` 晚于今天，各一例，均在造任何单据前报错并指出键名；② 测试站事务内造 **14 天**（含一个周日、一个月末）的小场景：全部业务单据 `docstatus=1`，库中无 `docstatus=1` 而无 GL／SLE 的应有凭证（逐单据类型核：采购入库、完工入库、发货、发票、付款、日记账均有 GL；入库出库均有 SLE）；单据 `posting_date`／`transaction_date` 随生成顺序不减（按 `creation` 排序后核）；③ s8dev 整年实跑（S→E 前一天）：GL Entry 与 SLE 条数与「各类已提交单据 × 每张应有行数」的汇总一致（D 回执附按单据类型的计数表）；**三规则依次**：[S, S＋4月) 只有按订单规则的建议与采纳，[S＋4月, S＋8月) 另有经济订货量，其后另有覆盖 N 天；三段各有已采纳的建议单与对应物料需求、采购订单；④ 整年总耗时与每日耗时分布记 D 回执（HT-019）；⑤ 月末结转：第二段跑完时，S 所在月起到 D2 上上个月每月一张已提交的月末结转凭证、D2 上一个月没有；整年跑完时 S 所在月起到 E 前一个月每月一张（D2 上一个月由第三段开头补结）；现金流量底稿同此规则、每月一张已提交（含无现金流的月）；每月一张折旧日记账（借 `5602070`、贷 `1602020`，金额＝参数月折旧额）；期初一张：借 `1002` 与 `1601` 明细、贷 `3001`；⑥ 供应商评分：每家供应商的记分卡按月补出 S～E 上月的各期，各期总分非空，E 所在月无期；⑦ 同一工位任意两条工序卡时间行不重叠；无跨天的卡（每条时间行的起止同一天、且在工位工作时段内）；工序卡时间行合计 ＝ 该卡 `time_required`（OB-057）；⑧ SPC：第 6 幕所看物料与参数在 D2 前 90 天内子组数 ≥25；判异点只出现在参数文件设定的异常段内（读回 `spc.py` 的结果核）；⑨ 第 6 幕前置：D2 之后 4 周内有已排程未完工的卡，至少一个工位某一周负荷 >100%（调 `capacity_load.execute` 核）；第 9 幕前置：E 当天调 `run_daily(E)` 后至少一种线材出经济订货量建议，且该线材至少两家供应商有带 `supplier`／`valid_from` 的采购价；⑩ 缺料：参数设一种线材在第一段末故意断料，生成器推迟了至少一张工单的首张卡报工，策略对比报表第一段缺料次数 ＝ 生成器记录的推迟张数；⑪ 拆单补丁在后台任务里生效：卷簧工序按 `cn_job_card_split_qty` 拆了卡（`PH-P1092`）；⑫ 第二、三段从已有数据续跑：在第一段末尾手工插入一张交货日在第二段的 5000 支订单（模拟第 1 幕），第二段照常排产、完工、发货、开票、收款 |

执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-013 场景参数文件与加载校验 | SL-011 | 否 |
| TS-014 建单辅助、主数据与期初 | SL-011 | 否 |
| TS-015 每日全链 | SL-011 | 否 |
| TS-016 每月任务、缺料、第 6／9 幕前置 | SL-011 | 否 |
| TS-017 生成器入口、后台任务与一年实跑 | SL-011 | 否 |

**本 Part 的环境**：单测在 `test.localhost`（事务内、`commit=False`）；TS-017 起在 `s8dev.localhost`（总纲纪律 4）。

---

## 任务 TS-013：场景参数文件与加载校验（对应切片 SL-011 ①）

### 目标

改场景只改一份 YAML、不改代码（需求 DEC-011、§4.9.1）。

### 具体改动

**`frappe_debug/data/scenario.yaml`** 结构（键名定稿；数值由 D 步按弹簧厂常识填，回执列出关键取值）：

```yaml
company: {name: 华东弹簧有限公司, abbr: HDS}       # 只在 s8dev／演示站存在；测试用小场景另给
timeline:
  months: 12                 # S = E 前 12 个月的当月 1 日
  rule_order_from: +0m       # 相对 S
  rule_eoq_from: +4m
  rule_periodic_from: +8m
  d1: {month: +3m, weekday_on_or_after: 2}     # S＋3 月该月第一个周三起的工作日（避开周日与假日）
  d2: {month: +6m, first_workday: true}
  end: today                 # E；也可写具体日期（不得晚于今天）
calendar: {holiday_list: 场景假日, weekly_off: [Sunday], holidays: [...]}
opening: {capital: 5000000, bank: 3000000, assets: [{name: 卷簧机, account: 1601…, cost: …, monthly_depreciation: …}, ...]}
items:
  products: [{code: SPR-C-2.0x20x50, name: 压簧 YA 2×20×50, uom: 支, boms: [...], price: …}, ...]   # 压簧＋拉簧，国标标记（需求 §4.9.1）
  materials: [{code: WIRE-65MN-2.0, uom: 千克, rules: [order, eoq, periodic], lead_time_days: 7, suppliers: [...]}, ...]
boms: {...}                  # 每产品 2～3 张；工序、工位、time_in_mins、cn_process_loss_percentage、cn_piece_rate、cn_job_card_split_qty
workstations: [{name, hour_rate, production_capacity, working_hours: [[08:00, 17:00]]}]
parties: {customers: 30, suppliers: 12, name_pool: [...]}
demand: {weekly_orders: {mean: 6, sd: 1.5}, qty: {mean: 3000, sd: 800, round: 500}, lead_days: [10, 20]}   # 平稳、无季节（DEC-012）
quality: {params: [{name: 自由长度, mean: 50.0, sd: 0.15, usl: 50.5, lsl: 49.5}], anomaly: {from: +5m-10d, to: +5m-3d, shift_sd: 2.2}}
loss: {operation_actual: {sd_pct: 0.4}}     # 实际损耗围绕工序损耗率波动
prices: {supplier_trend: [...]}            # 每家每月一条采购价（Item Price 带 supplier、valid_from）
staff: {employees: 12, piece_rate_component: 计件工资, salary_structure: {...}}
shortage: {item: WIRE-65MN-2.0, window: [+3m+20d, +3m+27d]}   # SL-011 ⑩
act_targets:                  # 第 6、7、9 幕前置（§4.9.3 第 9、10 条；偏离 16）
  act6_overload: {workstation: 卷簧机-1, week_after_d2: 2, load_pct: 115}
  act7_order: {qty: 2000, due: d2}
  act9_eoq_item: WIRE-65MN-2.0
```

**`frappe_debug/scenario/params.py`**：

```python
@dataclass(frozen=True)
class Scenario:
    raw: dict
    S: date; E: date; D1: date; D2: date
    rule_dates: dict[str, date]      # order / eoq / periodic
    segments: list[tuple[date, date]]   # 预跑三段：[S, D1−1]、[D1+1, D2−1]、[D2+1, E−1]（需求 §4.4.9）
    ...

def load_scenario(path: str | None = None, end: date | None = None) -> Scenario:
    """读 YAML（缺省 frappe_debug/data/scenario.yaml），解析相对日期、校验；问题汇总成一次 frappe.throw（逐条列键名与原因）。
    end 缺省取 timeline.end（today → frappe.utils.getdate()）。E 晚于今天即报错（§4.9.3 第 12 条）。
    D1 须落在 [S＋3月, S＋4月)（只按订单期）；D2 为 S＋6 月第一个工作日；三段每段至少 1 天。"""

def dates(sc: Scenario) -> dict[str, str]:   # 供演示配置引用：{"S","D1","D2","E"}
```

### 验证方式

`frappe_debug/tests/test_params.py`：SL-011 ① 六例；一例完整合法参数解析出的 S／D1／D2／E／segments 与写死值一致（以 E＝2026-10-20 为例：S＝2025-10-01）。

---

## 任务 TS-014：建单辅助、主数据与期初（对应切片 SL-011 ②⑤）

### 目标

生成器与演示命名函数共用的建单辅助（ADR-0010，A1）；按参数建主数据与期初余额。

### 具体改动

1. **`frappe_debug/builders/dates.py`**（A19）：

```python
def dated(doc, day: date, time: str = "10:00:00"):
    """meta 有 set_posting_time → 置 1、posting_date、posting_time；有 transaction_date → 置之；
    有 schedule_date／delivery_date 且为空或早于 day → 置 day 或 day＋提前期（调用方传）。返回 doc。"""
```

   其余 `builders/` 函数按单据分文件（`selling.py`、`buying.py`、`manufacturing.py`、`accounts.py`、`crm.py`），每个形如 `make_and_submit_purchase_receipt(po: str, day: date, rejected: dict | None = None) -> str`：经原生 mapper（V-04 用过的 `make_purchase_receipt`、`make_purchase_invoice`、`get_payment_entry`、work_order `make_stock_entry`、`make_delivery_note`、`make_sales_invoice`；另加 `quotation.make_sales_order`、`material_request.make_purchase_order`、`production_plan` 的 `get_items`／`make_work_order`）→ `dated` → `insert` → `submit`，返回单号。**不得** `docstatus: 1` 直接 insert、不裸写表（§4.9.3 第 1 条）。
2. **`frappe_debug/scenario/masters.py`** `build_masters(sc) -> dict`：按参数幂等建（存在即跳过）：假日表、单位核对（只用 `frappe_china` 已建的「千克」「支」，不建新单位，OB-013）、物料组、物料（产品勾 `cn_auto_select_bom`；线材按参数勾三规则、`Item Reorder` 行、提前期）、物料价格（销售价；采购价按 `prices.supplier_trend` 每家每月一条，`supplier`＋`valid_from`）、工位（`working_hours`、`holiday_list`）、工序（`create_job_card_based_on_batch_size`、`cn_piece_rate`）、BOM（提交，带工序损耗率与拆分数量）、客户与供应商（名称池）、员工（带性别）、薪资结构与分配（`from_date`＝S）、质检参数与模板、公司补货参数（`cn_order_cost`、`cn_holding_rate`、`cn_review_days`、`cn_review_start_date`、`cn_service_level`）。**规则启用不在此做**：三规则勾选按启用日由每日循环打开（TS-015）。产能计划：`Manufacturing Settings.disable_capacity_planning=1`（V-04、HT-020）。
3. **期初**（`scenario/opening.py`，偏离 13）：S 日一张日记账：借 `1002` 银行、借各固定资产对应 `1601` 明细，贷 `3001` 实收资本；金额按参数。
4. **CRM 主数据**：线索来源、商机状态沿用 CRM 默认（TS-009 已加译）。

### 验证方式

`test_masters.py`：小参数在测试站事务内 `build_masters` 两次，第二次无新增；期初日记账 GL 借贷与参数一致。

---

## 任务 TS-015：每日全链（对应切片 SL-011 ②③⑦⑧⑪⑫）

### 目标

每个工作日按库存推导应做之事、逐张提交（A3），日期严格不减。

### 具体改动

**`frappe_debug/scenario/day.py`** `run_day(sc, day, rng) -> DayResult`，固定顺序（同一天内各单据时刻按顺序递增，`time` 参数逐步 +1 分钟起，保证「日期不减」也对 posting_time 成立）：

| # | 动作 | 推导依据（查库） |
|---|---|---|
| 0 | 规则开关：`day` ＝ 某规则启用日 → 给该规则的物料打勾 | 参数 |
| 1 | CRM：按 `demand.weekly_orders` 抽样今天的新需求 → 线索 → 商机（金额、概率、预计成交日；状态单向推进）→ 报价单（`crm_deal`）→ 销售订单（交货日 ＝ day ＋ `lead_days` 抽样） | 随机（`rng` 由参数里的种子＋日期决定，重跑同结果） |
| 2 | 排产：未建生产计划、交货日 − 生产周期 ≤ day 的订单行 → 生产计划（取销售订单，TS-004 反算生效）→ 提交 → `make_work_order` → 工单提交（建卡；拆单补丁在后台任务中由 `before_job` 打上，⑪） | `Sales Order Item` 待生产量 |
| 3 | 补货：`run_daily(as_of_date=day, company)`；采纳全部 `Awaiting Decision` 建议（`replenishment_suggestion.adopt`）→ 生成的物料需求按 `material_request.make_purchase_order` 建采购订单（供应商取该物料当月价最低者）→ 提交 | 建议单 |
| 4 | 收货：`schedule_date ≤ day` 的未收采购订单 → 采购入库（按参数比例填拒收数）→ 采购发票 → 付款（`Wire Transfer`，`1002`） | `Purchase Order` 未收数 |
| 5 | 发料与报工：料够的已提交未开工工单（**缺料则跳过、记推迟**，TS-016）→ 发料（`Material Transfer for Manufacture`）→ 按工序顺序报工：每张卡一次报完（`completed_qty`＝本卡数量 − 实际损耗，损耗按工序损耗率加 `loss.operation_actual` 抽样，取整），时间行由**工位时段分配器**给出 → 卡提交（后道卡数量由 S7 的工序间数量传递 `operation_flow.py` 自动调）→ 首道/末道各一张质检（读数按 `quality` 分布，异常段按 `shift_sd` 偏移）→ 完工入库 | `Work Order`、`Job Card` |
| 6 | 交付：成品已入库、交货日 ≤ day 的订单行 → 发货单 → 销售发票 → 收款（隔 `rng` 抽的 0～15 天，按发票到期推导） | `Sales Order Item` 已交数 |

**工位时段分配器**（HT-020，§4.9.3 第 4、5 条）：`scenario/slots.py`

```python
class SlotAllocator:
    """按 (工位, 日期) 记已占用区间，初始从库里读该日已有的 Job Card Time Log（含现场单据）。
    take(workstation, day, minutes) -> (from_dt, to_dt) | None：在工位当日工作时段内找第一段连续空闲 ≥ minutes；
    当天放不下返回 None（调用方把这张卡留到下一个工作日，不跨天、不排夜班）。"""
```

报工分钟 ＝ 卡的 `time_required`（OB-057：不用短计时）。工序卡数量较大、单张超过一个工作日时，由参数 `cn_job_card_split_qty` 保证拆小（参数校验：任一工序「拆分数量 × 单件工时」须 ≤ 工位单日时长，否则 TS-013 报错）。

**事务**：每天一个事务，`commit` 失败 `rollback` 并抛出（整段停，状态文件记失败日与 traceback），不跳过某天继续。

### 验证方式

`test_day.py`：测试站事务内 14 天小场景（SL-011 ②），断言单据类型计数、日期不减、GL／SLE 齐全、同工位不重叠（⑦）；⑪ 在 TS-017 的后台任务里核（`run-tests` 进程不经 `before_job`，单测里显式调 `ensure_patched`）；⑫ 在 TS-017。

---

## 任务 TS-016：每月任务、缺料、第 6／9 幕前置（对应切片 SL-011 ⑤⑥⑧⑨⑩）

### 目标

月末结转、底稿、折旧、计件按月落；缺料推迟；为第 6、7、9 幕造出要看的局面。

### 具体改动

1. **`scenario/monthly.py`** `run_month_end(sc, month_last_day)`，在 `run_day` 处理完当月最后一个日历日后调（若该日为周日，在该日照样调，单据日期取该日）：
   - 计件：`make_piece_rate_summaries(company, month_last_day)`（S7 接口，按某日计算约定）。
   - 折旧：一张日记账，借 `5602070`、贷 `1602020`，金额 ＝ Σ参数月折旧（偏离 13）。
   - 月末结转：`accounting.closing.generate_month_end_closing(company, fiscal_year, month)`。**D2 的上一个月（S＋5 月）在第二段末不结**，留给第 7 幕现场结；结转要求前月已结（子 Agent 读 `closing.py:373`），故第三段（D2 之后）处理每个月末前，`run_month_end` 先查此前有无未结的月、有则按序补结（彩排时第 7 幕已结，补结即跳过；s8dev 单独跑生成器时由它补上）。
   - 现金流量底稿：新建 `Cash Flow Worksheet`（company、fiscal_year、month）→ `get_cash_flow_items()` → insert → submit；与结转同一跳过与补结规则（底稿要求按月顺序提交）。缺代码的行被拦时（`cash_flow_worksheet.py:115-122`）记问题并停。
2. **缺料**（DEC-012／035，偏离 8）：TS-015 第 5 步判「料够」：工单 `required_items` 中属补货物料的行，`source_warehouse` 实时结存 ≥ 待发数量。不够则当天不发料、记 `Scenario Event`（`frappe_debug` 的普通 DocType：日期、类型「缺料推迟」、工单、物料、缺口）；`planned_start_date` 不改。`shortage` 参数指定的窗口内，生成器把该线材的到货（第 4 步）推迟到窗口末，造出断料。
3. **第 6 幕超载**（§4.9.3 第 9 条）：生成第二段末（D2 前一天）时，对 `act6_overload.workstation` 额外排入若干张未开工的卡：计划开工落在 D2 后第 `week_after_d2` 周、`scheduled_time_logs` 由分配器给时段（只写排程、不写报工，HT-014），使该周需求工时 ÷ 产能 ≥ `load_pct`。这些卡挂在交货日在第三段的真实订单的工单上（第三段照常完工）。
4. **第 7 幕订单**（偏离 16）：第二段内保证有一张 `act7_order` 订单——交货日 ＝ D2、在 D2 前已完工入库、未发货。
   **第 6 幕的计件月份**：D2 是该月第一个工作日，D2 所在月几乎没有报工，现场要生成的是 **D2 上一个月**的计件汇总（偏离 19）。故生成器对 D2 上一个月**跳过计件汇总**（与跳过结转同一规则），第三段开头 `run_month_end` 补结前月时一并补计件（计件按员工×期间已存在即跳过，S7 接口约定第 2 条，现场生成过的不会重复）。
5. **第 9 幕**（§4.9.3 第 10 条）：第三段的需求与采购节奏由参数保证 E 当天 `act9_eoq_item` 计划量低于再订货点：生成器在 E 前 `lead_time_days` 天起停止为该物料采纳经济订货量建议（建议照出，状态留 `Awaiting Decision` 后在 E−1 统一忽略），使 E 当天 `run_daily(E)` 必然再出一条。至少两家供应商有该线材历史价（`masters` 已建）。
6. **供应商评分**（偏离 12）：第三段最后一天处理完后：每家供应商 `frappe.db.set_value("Supplier", s, "creation", S)`（只改时间戳，不改业务字段；V-07 做法），再建按月记分卡（标准取原生默认、等级行自带 `min_grade`／`max_grade`，V-07 探针注意），`on_update` 自动补期。
7. **用户列表设置**（§4.9.3 第 11 条）：每段末尾删 `__UserSettings` 中 Administrator 的列表筛选设置（`frappe.cache` 与 `tabDefaultValue` 两处，执行者读 `frappe/model/utils/user_settings.py` 后定）。

### 验证方式

`test_monthly.py`：测试站事务内跨两个月末的小场景：结转、底稿、折旧、计件各一；D2 上月跳过与其后补结（参数把 D2 放在第二个月）。⑧⑨⑩ 在 TS-017 的整年数据上核。

---

## 任务 TS-017：生成器入口、后台任务与一年实跑（对应切片 SL-011 ③④⑤⑥⑧⑨⑩⑪⑫）

### 目标

彩排页能以后台任务发起任一段并轮询完成（A7、需求 §4.4.9、§4.9.4）；在 s8dev 实跑一整年并核验收。

### 具体改动

1. **`frappe_debug/scenario/runner.py`**：总纲 §5.3 的 `start_generate`／`generate_status`／`generate`。
   - `generate`：`load_scenario()` → 第一次调用（库里无 `Scenario Event` 类型「主数据」记录）时 `build_masters`＋期初 → 对 `[from_date, to_date]` 逐日 `run_day`、遇月末 `run_month_end`；**进度写状态文件** `sites/{站}/private/frappe_debug/generate.json`（`{job_id, state, day, started, error}`，每天写一次）；生成器运行期间设 `frappe.flags.in_scenario_generator = True`（A8 服务端兜底据此跳过）。
   - 先置 `frappe.flags` 再调 `frappe_china.production.job_card_split.ensure_patched()` 与 `overproduction.ensure_patched()`（防进程未经 `before_job`）。
   - 参数校验：`from_date ≤ to_date`、`to_date < 今天`、`from_date` 不早于库中最后一张生成器单据的次日（不乱序补单，§4.9.3 第 2 条），否则 throw。
2. **s8dev 站**（总纲纪律 4）：由演示站清洁基准备份（`20261017_232126`，S8 概况）`bench new-site s8dev.localhost` ＋ `bench --site s8dev.localhost restore`，装上 `frappe_debug`、跑 migrate、归位与 `check_app_order`；跑 `configure_apps` 前置（TS-012）；容器内 `bench serve --port 6787`（单进程，日志写 `frappe-bench/logs/`）。
3. **整年实跑**：`bench --site s8dev.localhost execute frappe_debug.scenario.runner.generate --kwargs "{'from_date': S, 'to_date': D1−1}"`，再模拟第 1～5 幕（插入一张 5000 支订单，⑫），再跑第二、三段。**跑之前**整库备份一次（s8dev 的生成前状态），以便重跑。
4. **验收核对脚本** `frappe_debug/scenario/verify.py` `verify(sc) -> dict`：SL-011 ③⑤⑥⑦⑧⑨⑩ 的查询，逐项 `ok/detail`，`bench execute` 打印；结果贴 D 回执。

### 验证方式

SL-011 ③～⑫ 全部由 `verify` 输出＋耗时表给出证据。⑪：查一张卷簧工单的卡数与 `cn_job_card_split_qty` 对得上。整年总耗时 >2 小时按 HT-019 处理。
