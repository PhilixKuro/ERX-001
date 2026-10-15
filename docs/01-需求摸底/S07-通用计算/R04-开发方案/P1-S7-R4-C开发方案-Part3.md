# P1-S7 通用计算 —— 开发方案·Part3：负荷报表、SPC、收尾

**来源需求**：[R3 B 需求文档](../R03-需求文档/P1-S7-R3-B需求文档.md) §4.11.1、§4.11.2、§4.13、§八 AC-023｜**前置依赖**：Part1 TS-002（模块）；TS-017 依赖全部任务｜**日期**：2026-10-15｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S7-R4-C开发方案-总纲](P1-S7-R4-C开发方案-总纲.md)

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-010** 产能负荷报表 | 需求 TS-011、IM-010、DEC-011；HT-015 | ① 一个工作中心（两个时段共 8 小时、`production_capacity`＝2、假日表含所选周的周三、周六、周日）、一张未开工卡（`time_required` 600 分）与一张完成一半的卡（`time_required` 480 分、`for_quantity` 100、`total_completed_qty` 50），同在该周：该周行需求工时＝(600＋240)/60＝14.00、产能工时＝4 天×8×2＝64.00、负荷率与手算一致（`Workstation Working Hour` 无星期维度，时段每天都算，休息日全靠假日表扣）；② 无 `expected_start_date` 的卡进「未排期」行，需求有值、产能与负荷率为空；③ 负荷率＞100% 的格标红（格式化函数单测断言返回的 HTML 含标红样式）；④ 报表返回的 `chart` 是柱状图、含需求与产能两组；⑤ 已完成、已取消的卡不计；`for_quantity`＝0 的卡需求记 0；⑥ 无工作时段的工作中心产能为 0 时，负荷率空、备注列写「无产能」；⑦ 日、周、月三种时间桶各出一次，桶边界正确（周桶以周一起算） |
| **SL-011** SPC 报表与控制图 | 需求 TS-012、IM-011、DEC-012；总纲 A15，HT-013 | ① 一组 28 个子组（含 n＝3、n＝5 不等大小与 2 个 n＝1 组），报表摘要的 X̿、R̄、σ_组内、σ_总体、Cpk、Ppk 与测试里写死的手算值一致（6 位小数内）；② 一个读数为 `abc`、一个为空：剔除计数＝1（空值不计为剔除）；③ 只给 20 个 n≥2 子组时摘要标「样本不足、仅供参考」，数值照出；④ Nelson 8 条每条各有一个只命中该条的序列与一个恰好不命中的序列（共 16 个用例）；⑤ 只有上限或只有下限时 Cpk／Ppk 取单侧；上下限都无时两者为空并在摘要说明；⑥ 控制图页面上判异点与非判异点颜色不同、悬停显示触发的规则号（截图）；从报表能跳转到页面并带上筛选 |
| **SL-012** 收尾 | 需求 TS-014、AC-023；§4.13 | ① README 有「后端覆盖登记」节与拆单一行、「按某日计算」接口约定、两个新模块的划分判据、本 Stage 新增的已知限制；② 测试站全量测试（Python 与 Node）用例数比 TS-001 基线只增不减、全过；`test_translation_quality`、`test_translations` 过；`translation_check.run` 在两站均通过；③ 演示站 migrate 后 `check_app_order()["ok"]` 为真且未新增 `Error Log`；`auto_indent`＝0；`计件工资` 组件存在；两个新模块侧栏为空；④ 演示站业务数据（GL、SLE、客户、供应商、物料、各类发票与凭证、补货建议单、计件汇总单）仍为 0、`Translation` 为 0；⑤ 测试站跑一次 365 天回放（演示物料规模的造数，见 TS-017）记下 `run_daily` 总耗时，写进 D 回执（LG-008） |

执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-014 产能负荷报表 | SL-010 | 否 |
| TS-015 SPC 计算与报表 | SL-011 | 否 |
| TS-016 控制图页面 | SL-011 | 否 |
| TS-017 收尾、全量回归与演示站落地 | SL-012 | 否 |

---

## 任务 TS-014：产能负荷报表（对应切片 SL-010）

### 目标

Script Report「产能负荷」，一行一个工作中心×时间桶，需求侧按未完成比例、产能侧按时段×并行数跳假日（需求 §4.11.1、DEC-011）。

### 具体改动

**Report `Capacity Load`**（模块 `Production Plus`，`report_type`＝Script Report，`ref_doctype`＝Job Card，角色 Manufacturing User／Manufacturing Manager／System Manager）。报表名用英文源词、中文进 csv（S4 的法定报表用中文名，是因为法定格式要求列头不经翻译，本表无此要求）。

**`frappe_china/production_plus/report/capacity_load/capacity_load.py`**

```python
def execute(filters) -> tuple[columns, data, None, chart]:
    company、from_date、to_date 必填；bucket ∈ {Day, Week, Month}，默认 Week；workstations 可多选
    buckets = _buckets(from_date, to_date, bucket)        # [(key, start, end)]；周桶以周一为首、首尾桶按筛选区间截断
    demand = _demand(filters)    # {(ws, key|UNSCHEDULED): 分钟}
    capacity = _capacity(filters, buckets)   # {(ws, key): 小时}
    rows：每个出现过需求或在筛选范围内的工作中心 × 每个桶；外加需求非零的「未排期」行
    chart：type="bar"，labels＝桶标签，datasets＝[需求工时合计, 产能工时合计]（所选工作中心合计）

def _demand(filters):
    Job Card：company、docstatus != 2、status not in ("Completed", "Cancelled")、workstation in …（若给）、
              非纠正卡；expected_start_date 落在区间内 或 为空
    remaining = time_required × (1 − total_completed_qty / for_quantity)，for_quantity ≤ 0 记 0，结果 max(0, …)
    桶：date(expected_start_date)；为空 → UNSCHEDULED

def _capacity(filters, buckets):
    每个工作中心：hours_per_day = Σ working_hours.hours × production_capacity（HT-015：不看 enabled，同原生）
    holidays = Holiday List(holiday_list) 的日期集合；holiday_list 为空则不扣
    每天 d：d 不在 holidays → 加 hours_per_day 到 d 所在桶
```

- 列：工作中心、时间桶、需求工时（Float，小时，2 位）、产能工时、负荷率（Percent）、备注（Data：「无产能」「未排期」）。
- 标红：`capacity_load.js` 的 `formatter`，负荷率列值＞100 时包一层带红色样式的 span（用 Frappe 既有的 `text-danger` 类，不写内联色值）。
- 筛选「工作中心」用 `MultiSelectList`。

### 验证方式

单测 `tests/test_capacity_load.py`：直接调 `execute(filters)`，SL-010 ①②④～⑦；③ 单测 Python 侧不可测 js formatter：把判定写成 js 内的一个小函数，`tests/test_capacity_load.cjs` 用 node 断言（同 S6 既有 `.cjs` 测试做法）。

---

## 任务 TS-015：SPC 计算与报表（对应切片 SL-011）

### 目标

X̄-R 控制图数据、Cpk／Ppk、Nelson 8 条，供报表与页面共用（需求 §4.11.2、DEC-012）。

### 具体改动

**`frappe_china/production/spc.py`**（纯计算部分不依赖 frappe，便于单测）

```python
D2: Final = {2: 1.128, 3: 1.693, 4: 2.059, 5: 2.326, 6: 2.534, 7: 2.704, 8: 2.847, 9: 2.970, 10: 3.078}
MIN_SUBGROUPS: Final = 25

class Subgroup(TypedDict):
    inspection: str; date: str; values: list[float]; n: int
    mean: float; range: float | None; z: float | None; rules: list[int]

class SpcResult(TypedDict):
    subgroups: list[Subgroup]
    grand_mean: float | None; r_bar: float | None
    sigma_within: float | None; sigma_overall: float | None
    usl: float | None; lsl: float | None
    cpk: float | None; ppk: float | None
    readings: int; rejected: int; signals: int
    insufficient: bool; notes: list[str]

def load_subgroups(filters) -> tuple[list[Subgroup], int, tuple[usl, lsl], list[str]]:
    """Quality Inspection docstatus=1、item_code、readings.specification＝参数；可选 report_date 区间、
    inspection_type、工作中心（reference_type='Job Card' 时 join Job Card.workstation）。
    按 report_date、检验单名排序。每行读 reading_1..reading_10：去空白后为空 → 跳过（不计剔除）；
    float() 失败 → rejected += 1。全部读数为空或非数字的行不成组。
    规格限：取各行 min_value／max_value；0 视为未设（Float 未填即 0）；各行不一致时取最后一个子组的值，notes 记一条。"""

def compute(subgroups, usl, lsl) -> SpcResult:
    multi = [g for g in subgroups if g.n >= 2]
    X̿ = mean(g.mean for g in multi)；R̄ = mean(g.range for g in multi)
    σ_within = mean(g.range / D2[g.n] for g in multi)          # 子组大小不一：各组 R/d₂(n) 的均值（需求留 C 定）
    σ_overall = statistics.stdev(全部子组的全部读数，含 n＝1 组)
    Cpk = min(USL − X̿, X̿ − LSL) / (3σ_within)；只有一侧限则只取该侧；两侧都无 → None，notes 记
    Ppk 同式用 σ_overall（中心仍用 X̿，「同式」照需求字面）
    每个 n≥2 子组：z = (mean − X̿) / (σ_within / sqrt(n))      # 按各组 n 标准化，控制限 ±3 即 X̿ ± 3σ/√n
    rules = nelson([g.z for g in multi])；n＝1 组 z、rules 为空，不进图
    insufficient = len(multi) < MIN_SUBGROUPS
    n＞10 的子组：D2 无该值 → 不进 X̄-R（只进 Ppk），notes 记「子组大小超过 10」

def nelson(z: list[float]) -> list[list[int]]:
    """逐点返回触发的规则号（规则在 z 上判，区：|z|>3、>2、>1）。窗口规则把命中标在窗口末点：
    1 |z|>3；2 连续 9 点同号（z≠0）；3 连续 6 点严格单调（即 5 个差同号）；4 连续 14 点差值交替变号；
    5 连续 3 点中 ≥2 点 z>2（或 ≥2 点 z<−2）；6 连续 5 点中 ≥4 点 z>1（或 <−1）；
    7 连续 15 点 |z|<1；8 连续 8 点 |z|>1（两侧均可）。"""
```

- **「判异点」**＝`rules` 非空的点；`signals`＝判异点数。
- 窗口规则标末点（不标窗口内全部点），在 README 写一句。理由：演示时一点一色，标全部窗口点会把一段正常点染成异常。

**Report `SPC Control Chart`**（模块 `Production Plus`，Script Report，`ref_doctype`＝Quality Inspection）

- 筛选：物料（必填）、检验参数（必填，Link `Quality Inspection Parameter`）、日期区间、检验类型、工作中心。
- 摘要（`report_summary`）：Cpk、Ppk、子组数（n≥2）、读数数、剔除数、判异点数；`insufficient` 时加一项「样本不足、仅供参考」。
- 表格：日期、检验单（Link）、n、X̄、R、触发规则（如 `1, 5`）。
- 图（`chart`）：line，labels＝子组序号，datasets＝X̄、UCL、CL、LCL（UCL/LCL 按各点 n 逐点给值）。
- `spc_control_chart.js` 加一个按钮「打开控制图」，以当前筛选跳到 TS-016 的页面（`frappe.set_route("spc-chart", 筛选…)`，筛选进 URL query）。

### 验证方式

单测 `tests/test_spc.py`：`compute`、`nelson` 用常量数据（SL-011 ①③④⑤，16 个 Nelson 用例各一个短序列）；`load_subgroups` 用站上造的检验单（SL-011 ②，及「n＝1 组只进 Ppk」）。手算值在测试注释里列出逐组 X̄、R、R/d₂。

---

## 任务 TS-016：控制图页面（对应切片 SL-011）

### 目标

自有 Page，同一筛选与计算，echarts 画 X̄ 图、判异点逐点着色、悬停显示规则（需求 §4.11.2、DEC-012 7d；总纲 A15，HT-013）。

### 具体改动

- **vendor 文件**：把 `apps/insights/frontend/node_modules/echarts/dist/echarts.min.js` 原样复制为 `frappe_china/public/js/vendor/echarts-5.6.0.min.js`，同目录放 `ECHARTS-LICENSE`（复制自同包 `LICENSE`）。README「已知限制」或「许可」节写一行来源、版本与许可证（Apache-2.0）。vendor 文件**不经 ruff／prettier**：加进 `.pre-commit-config.yaml` 的排除、`ruff` 只管 Python 无须处理。
- **Page `spc-chart`**（模块 `Production Plus`，标题源词 `SPC Control Chart`，角色同报表）：`frappe_china/production_plus/page/spc_chart/spc_chart.json`／`.js`。
- **后端**：`frappe_china/production/spc.py` 加

```python
@frappe.whitelist()
def get_chart_data(filters: str | dict) -> SpcResult:
    """权限：Quality Inspection read。load_subgroups + compute，与报表同一函数。"""
```

- **前端**（`spc_chart.js`）：页面顶部用 `page.add_field` 放与报表相同的五个筛选，并从 `frappe.route_options` 取初值；`frappe.require("/assets/frappe_china/js/vendor/echarts-5.6.0.min.js")` 后建图：

```js
series: [
  { type: "line", name: __("Subgroup Mean"), data: points.map(p => ({
      value: [p.idx, p.mean],
      itemStyle: { color: p.rules.length ? SIGNAL_COLOR : NORMAL_COLOR },   // 逐点着色（HT-013）
      symbolSize: p.rules.length ? 9 : 5,
      rules: p.rules })) },
  { type: "line", name: "UCL", data: …, lineStyle: { type: "dashed" }, symbol: "none" },
  { type: "line", name: "CL",  data: …, symbol: "none" },
  { type: "line", name: "LCL", data: …, lineStyle: { type: "dashed" }, symbol: "none" },
]
tooltip.formatter: 检验单、日期、X̄、n，及「触发规则：1, 5」（无则不显示该行）
```

  颜色取 Frappe 的 CSS 变量（`--red-500`／`--blue-500` 之类，执行者核 desk 现有变量名），不写死色值。摘要区与报表同（Cpk、Ppk、子组数、样本不足提示）。
- 页面全部文案走 `__()`，源词进 csv（A16）。

### 验证方式

- 测试站造 28 个子组（含两处判异：一点越 3σ、一段连续 9 点同侧），开页面截图两张：整体、悬停在判异点上。截图存 `Spike/P1S7R5-D/`。SL-011 ⑥。
- 单测 `tests/test_spc.py` 加一条：`get_chart_data` 与报表 `execute` 对同一筛选给出相同的 `cpk`、`ppk`、`signals`。
- HT-013 不成立（echarts 加载失败或无全局 `echarts`）→ 暂停反馈。

---

## 任务 TS-017：收尾、全量回归与演示站落地（对应切片 SL-012）

### 目标

把本 Stage 的约定与覆盖成文、全量回归、量一次 365 天回放耗时，最后上演示站（需求 TS-014、AC-023、LG-008；§4.13）。

### 具体改动

1. **README**（`frappe_china/README.md`）：
   - 「模块边界」加两个模块与两个包的职责，及判据：注册模块只装 DocType／Report／Page，计算逻辑放同名普通包。
   - 新增「后端覆盖登记」节（TS-011 已写的那一行在此节）。
   - 新增「按某日计算」节：原样写总纲 §5.2 的四条接口约定，并列出两个入口的全名。
   - 「已知限制」：本方案各任务提到的限制（物料参数无法覆盖成 0、MR 取消不回滚建议单、`weight_uom` 为空的物料不做批次换算、工作时段不看 `enabled`、Nelson 窗口规则标末点、按订单不扣成品库存、子装配 BOM 不参与按成本选择）。
2. **回放耗时**（SL-012 ⑤，LG-008）：`frappe-bench/tmp/replay_probe.py`（用后删）在测试站一家测试公司下造 30 个物料、每物料 2 个仓库行、三规则全勾，逐日造少量出库并 `run_daily(D)` 365 次，记总耗时与单日最大耗时；**整段在事务里跑、最后 rollback**，`Error Log` 按标题正向清理。结果写 D 回执；单日超过 10 秒时记为 S8 的输入，不在本 Stage 优化。
3. **全量回归**（SL-012 ②）：Python、Node 两套全量；`test_translation_quality`；两站 `translation_check.run`。与 TS-001 基线对比写进 D 回执。
4. **演示站落地**（SL-012 ③④）：
   1. 核演示站基线（总纲纪律 4）；
   2. `docker/backup.sh`，另存到 `docker/backups/保留-S7上线前/`；
   3. `bench --site erx.localhost migrate`，看输出的自检结果；
   4. `docker/configure-apps.sh --site erx.localhost` 两次（第二次应「无改动」）；
   5. `bench build --app frappe_china`，重启 `bench start`（日志仍写 `frappe-bench/logs/bench-start.log`）；
   6. 复核：`check_app_order()`、`auto_indent`、`Salary Component` 计件工资、两个空侧栏、业务数据计数、`Translation` 为 0；
   7. 演示站开工单表单与控制图页面各截一张，确认前端资源已加载（不造业务数据：工单表单只开新建页不保存，控制图页面空数据即可）。
5. **常驻文件**：开发守则「工具链索引」Ruff 行（TS-001 已改）；本 Stage D 回执「新增约定」中确属长效的约定，按 `常驻文件契约.md` 判据移交 `开发守则.md`——**由 Workflow 收尾步骤做，本任务只在回执里列出候选**。

### 验证方式

SL-012 ①～⑤，逐项证据贴 D 回执（命令与输出、截图路径）。
