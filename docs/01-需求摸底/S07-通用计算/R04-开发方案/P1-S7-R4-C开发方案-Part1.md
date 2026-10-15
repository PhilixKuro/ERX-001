# P1-S7 通用计算 —— 开发方案·Part1：基础、自检、补货与选 BOM

**来源需求**：[R3 B 需求文档](../R03-需求文档/P1-S7-R3-B需求文档.md) §4.2～4.6、§4.10、§4.12～4.13｜**前置依赖**：无（本 Stage 第一个 Part）｜**日期**：2026-10-15｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S7-R4-C开发方案-总纲](P1-S7-R4-C开发方案-总纲.md)——架构决策 A1～A17、偏离、接口契约、技术假设、执行纪律都在那里，本 Part 不重复。

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-001** Ruff 基线与模块骨架 | 需求 TS-001、DEC-020；总纲 A1 | ① 容器内 `env/bin/ruff --version` 输出 `0.14.10`，且 `pyproject.toml` 的 `[tool.bench.dev-dependencies]` 锁同一版本；② 在 `apps/frappe_china` 下 `ruff check frappe_china` 与 `ruff format --check frappe_china` 均输出 0 处问题（贴输出）；③ 基线是 `frappe_china` 仓库里独立的一次提交，`git show --stat` 只含 `.py` 与 `pyproject.toml`，**全量测试用例数与提交前相同且全过**（Python 与 Node 两套各贴一次）；④ 测试站 migrate 后 `Module Def` 有 `Stock Plus`、`Production Plus`，Desk 侧栏不出现这两个模块的自动侧栏（`Workspace Sidebar` 两条记录 `items` 为空） |
| **SL-002** 覆盖自检 | 需求 TS-002、IM-007、`PH-P1073`、DEC-010 | ① 测试站把 `frappe_china` 挪离末位后 `bench migrate`：输出含 `problems` 逐条、`Error Log` 新增恰一条（标题见 TS-003）、`Administrator` 收到一条 `Notification Log`、migrate 退出码 0；随后归位、再 migrate，输出「通过」且不新增 `Error Log`；② `override_targets()` 返回 4 条，含 CRM `get_sidepanel_sections`；③ 单测：让 CRM 那条解析到别的 app，`check_app_order()["ok"]` 为假且 `problems` 点名该条；④ 单测：`check_app_order` 抛异常时 `after_migrate` 不抛、照样三处告警；⑤ 单测：无中式公司（`ok` 为真、`problems` 只有「无对象」一条）时不写 `Error Log`、不发通知；⑥ `docker/scripts/check_business_order.py` 对现行 `apps.json` 退出 0；对一份把 `hrms` 与 `crm` 对调的临时副本退出非 0，并打印两份顺序 |
| **SL-003** 补货参数、安全库存、再订货点 | 需求 TS-003～005、DEC-002／004／007～009；总纲 A4～A6，偏离 20／21 | ① 物料参数为空时取公司默认，物料填了取物料（单测，四个参数各一）；② 两站 `Stock Settings.auto_indent`＝0，`configure_apps.py` 有显式置 0 的一行，重跑第二次报「无改动」；③ 改 `lead_time_days` 保存后，已有的 `Item Lead Time.purchase_time` 同值、`buffer_time` 不变；无 `Item Lead Time` 的物料保存后仍无；④ 勾选物料的 `safety_stock`＝Z×σ×√LT，与测试里写死的手算值一致（Z＝1.6449、σ 为 90 天样本标准差、含零出库日）；⑤ 未勾选物料 `safety_stock` 的人填值不变；`lead_time_days`＝0 的勾选物料 `safety_stock` 写 0、结果含「提前期缺失」；⑥ 两仓库各有不同出库的物料，两行 `Item Reorder` 的再订货点各与手算一致且不相等；带 `warehouse_group` 的一行按组下仓库合计；⑦ 无 `Item Reorder` 行的勾选物料计算后仍无行、不报错；⑧ 窗口外（D−90 日）的一笔出库与一笔仓间调拨都不计入日需求 |
| **SL-004** 按成本选 BOM | 需求 TS-006、DEC-018／019／023；总纲 A10～A12，偏离 1／2 | ① 同一弹簧三个有效 BOM（数量、损耗率、工序各不同），`select_bom` 选单位成本最低者，三者单位成本与测试里写死的手算值一致；② 调高最低者所用原料的估价后再选，选择改变；选择前后三张 BOM 的库内成本字段与 `modified` 不变；③ 表单式新建工单（`bom_no` 为原生默认）保存后 `bom_no` 为选中项、工序与原料行属选中 BOM、工单有一条评论列出三个候选与各自单位成本；④ 销售订单 `make_work_orders` 与生产计划 `make_work_order` 两路径建出的工单 `bom_no` 均为选中项；生产计划保存后 `po_items.bom_no` 为选中项，取原料（`get_items_for_material_requests`）所展开的原料属选中 BOM；⑤ 新建工单时人手指定一个非默认、非选中的 BOM，保存后不被覆盖、评论注明「人工指定」并列出推荐项；⑥ 未勾「按成本自动选 BOM」的物料，三条路径都保持原生默认、不写评论；⑦ 物料无有效 BOM 时 `select_bom` 返回 `bom=None`、工单照原生报错 |
| **SL-005** 补货建议单与每日计算 | 需求 TS-007、DEC-001／003／005／006／021／022；§4.12／4.13；总纲偏离 10～15 | ① 同一物料勾三种规则、同日三者都触发，建议单出现同物料同仓库三条（规则各一）；② 同日再算一次条数不变；次日再算，三条的计算日期与建议量更新、仍为三条；③ 采纳生成一张已提交 MR（`transaction_date`＝计算日期、回指建议单），建议单状态「已采纳」并回填 MR；忽略不生成任何单据；已采纳的那条再算时另建新的一条；④ 列表批量采纳两条、其中一条已忽略：一条成功、一条报「状态不是待定」，互不影响；⑤ EOQ：建议量与手算一致，含 EOQ 低于 `min_order_qty` 时取 `min_order_qty` 一例、`min_order_qty`＝0 时取 EOQ 原值（只按库存单位是否须整数向上取整）一例、计划量高于再订货点不出建议一例、订货成本为空记「参数缺失」一例；⑥ 覆盖 N 天：盘点日的建议量与手算一致；非盘点日不出；目标量 ≤ 计划量不出；⑦ 按订单：两张销售订单经 BOM 展开的净缺料与手算一致，来源子表列两张订单；已有已提交 MR 覆盖的部分不重复建议；成品勾了「按成本自动选 BOM」时，展开所用的是 `select_bom` 选中的 BOM（与 SL-004 ③ 同一物料、同一选择，以原料集合为证）；⑧ `run_daily(D)`：建议单计算日期＝D；一笔 D＋1 日的出库不计入；同一 D 调两次结果相同；D 晚于今天时报错；⑨ 让一个物料在计算中抛异常，其余物料照常出结果、该物料进 `problems`；⑩ `run_now` 以 Stock User 调用被拒、以 Stock Manager 调用成功 |

执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-001 Ruff 基线清零 | SL-001 | 否 |
| TS-002 新模块骨架与新字段框架 | SL-001 | 否 |
| TS-003 覆盖自检与顺序比对 | SL-002 | 否 |
| TS-004 补货参数、`auto_indent`、提前期同步 | SL-003 | 否 |
| TS-005 选 BOM 共用函数 | SL-004 | 否 |
| TS-006 选 BOM 三处接入与评论 | SL-004 | 否 |
| TS-007 需求取样、安全库存、再订货点 | SL-003 | 否 |
| TS-008 补货建议单与三种规则 | SL-005 | 否 |
| TS-009 每日计算入口与采纳 | SL-005 | 否 |

---

## 任务 TS-001：Ruff 基线清零（对应切片 SL-001）

### 目标

一次还清 `PH-P1019`：容器里装上锁版本 ruff，`frappe_china` 全部 Python 文件 lint 与 format 都 0 告警，作为独立一次提交，先于一切功能改动（需求 DEC-020）。

### 具体改动

1. **装 ruff**（HT-001）：`frappe_china/pyproject.toml` 的 `[tool.bench.dev-dependencies]` 加 `ruff = "==0.14.10"`（与 `.pre-commit-config.yaml` 的 `rev: v0.14.10` 同版本）。容器内 `env/bin/pip install ruff==0.14.10`。`docker/scripts/setup.sh` 在装完 app 后加一段 `"$BENCH_DIR/env/bin/pip" install "ruff==0.14.10"`，版本号从 `pyproject.toml` 读（`tomllib`），不在两处写死。
2. **记基线**：改动前先跑一次全量测试（`bench --site test.localhost run-tests --app frappe_china`、`node --test frappe_china/tests/*.cjs`），用例数与结果写进 D 回执「全量验证」节，作为整个 D 步的回归基线。
3. **`pyproject.toml` 的 `[tool.ruff.lint] ignore`** 追加 `RUF001`、`RUF002`、`RUF003`（中文全角标点误报），各带一句注释。
4. `ruff check --fix frappe_china`，余项逐条手修；不能修又确属误报的，**行内** `# noqa: <码>` 并写原因，不扩大全局忽略。
5. `ruff format frappe_china`。
6. 再跑全量测试，与第 2 步基线逐项对比。
7. **停下来请求提交许可**（总纲纪律 9）。获许可后在 `frappe_china` 仓库提交一次，信息形如 `style: Ruff 0.14.10 baseline (PH-P1019)`；`docker/scripts/setup.sh` 那一行属主仓库，随 D 步其余主仓库改动一起报。
8. `docs/开发守则.md`「工具链索引」的 Ruff 行改为「已装进 bench 环境（`setup.sh` 装、版本读 `pyproject.toml`），基线 0」——**这是常驻文件**，写前载入 `docs/流程体系/常驻文件契约.md` 按其判据写。

### 验证方式

SL-001 ①②③：`env/bin/ruff --version`；两条 ruff 命令输出；提交后 `git show --stat HEAD`；两次全量测试对比。

---

## 任务 TS-002：新模块骨架与新字段框架（对应切片 SL-001）

### 目标

建总纲 A1 的两个模块、两个普通包与本 Stage 全部新字段，后续任务只往里填逻辑。

### 具体改动

- `modules.txt` 追加两行 `Stock Plus`、`Production Plus`；建目录 `frappe_china/stock_plus/`、`frappe_china/production_plus/`（各带 `__init__.py`、`doctype/`、`report/`，后者另有 `page/`）。
- `frappe_china/workspace_sidebar/stock_plus.json`、`production_plus.json`：同 `cn_tax.json` 形态（`name`／`title`／`module` 逐字等于模块名、`items: []`、`app: frappe_china`）。
- 普通包 `frappe_china/replenishment/`（`__init__.py`、`types.py` 放总纲 §5.1 的 TypedDict）、`frappe_china/production/`（`__init__.py`）。
- **新字段**全部进 `fixtures/custom_field.json`，并把字段名加进 `hooks.py` 的 `fixtures` 过滤清单。字段名、类型如下（label 用英文源词，中文进 csv；`insert_after` 由执行者按表单位置定）：

| DocType | 字段 | 类型 | 说明 |
|---|---|---|---|
| Company | `cn_replenishment_section` | Section Break | 「补货参数」 |
| Company | `cn_replenishment_enabled` | Check | 每日计算处理本公司 |
| Company | `cn_order_cost` | Currency | 每次订货成本 S |
| Company | `cn_holding_rate` | Percent | 年持有成本率 h |
| Company | `cn_review_days` | Int | 盘点周期 N |
| Company | `cn_review_start_date` | Date | 盘点起算日 |
| Company | `cn_service_level` | Percent，default 95 | 服务水平 |
| Item | `cn_replenishment_section` | Section Break | 「补货规则」，放在原生「Auto re-order」节之后 |
| Item | `cn_rule_eoq`、`cn_rule_periodic`、`cn_rule_order` | Check | 三种规则启用 |
| Item | `cn_auto_replenishment_params` | Check | 自动计算补货参数 |
| Item | `cn_order_cost`、`cn_holding_rate`、`cn_review_days`、`cn_service_level` | 同 Company | 物料覆盖，空即取公司（`cn_service_level` 无 default） |
| Item | `cn_auto_select_bom` | Check | 按成本自动选 BOM（放制造节） |
| Item | `cn_unit_length_m` | Float，precision 6 | 单支展开长度（m） |
| Batch | `cn_linear_density` | Float，precision 6 | 线密度（kg/m） |
| BOM Operation | `cn_job_card_split_qty` | Int | 任务单拆分数量 |
| BOM Operation | `cn_piece_rate` | Currency | 计件单价（元／件） |
| Operation | `cn_piece_rate` | Currency | 计件单价（兜底） |
| Material Request | `cn_replenishment_suggestion` | Link → `Replenishment Suggestion`，read_only | 来源建议单 |

  `Material Request` 那一条要等 TS-008 建出 DocType 才能 migrate 通过：本任务先建其余字段，该条在 TS-008 加。
- 本任务新增的 label 与 Section 标题补 `zh.csv`。

### 验证方式

测试站 `bench migrate`；单测（`tests/test_s7_scaffold.py`）断言：两个 `Module Def` 存在、两条 `Workspace Sidebar` 存在且 `items` 为空、上表字段（除 MR 一条）在各自 meta 里存在且类型一致。SL-001 ④。

---

## 任务 TS-003：覆盖自检与顺序比对（对应切片 SL-002）

### 目标

`check_app_order()` 在每次 migrate 后自动跑，覆盖断言扩到全部 whitelisted 覆盖，不过时三处告警、不中断（需求 §4.6、DEC-010）；`setup.sh` 比对业务 app 顺序（`PH-P1073`）。

### 具体改动

**`frappe_china/install.py`**

```python
def override_targets() -> tuple[str, ...]:
    """读 frappe_china.hooks 模块的 override_whitelisted_methods 键（importlib 直接取模块属性，
    不经 frappe.get_hooks，免得被别的 app 的同名键混入）。"""

# WHITELIST_TARGETS 常量删除；check_app_order() 中改为 for target in override_targets()。
# tests/test_install.py 里引用 WHITELIST_TARGETS 的用例同步改为 override_targets()。

ALERT_TITLE: Final = "frappe_china override self-check failed"   # Error Log 标题，经 _()

def after_migrate() -> None:
    try:
        result = check_app_order()
        failed, problems = not result["ok"], result["problems"]
    except Exception:
        failed, problems = True, [frappe.get_traceback()]
    print(通过 或 逐条 problems)        # 只打印，不 raise
    if not failed:
        return
    frappe.log_error(title=_(ALERT_TITLE), message="\n".join(problems))
    for user in _alert_recipients():   # 总纲偏离 16
        Notification Log：type="Alert"，subject=_(ALERT_TITLE)，email_content=problems 前 20 条
    frappe.db.commit()                 # after_migrate 在 migrate 末尾，通知须落库
```

- `_alert_recipients()`：`Has Role` 中 `role="System Manager"`、`parenttype="User"` 且用户 `enabled=1` 的 `parent`，并上 `"Administrator"`，去掉 `"Guest"`，排序去重。
- 建通知用 `frappe.get_doc({"doctype": "Notification Log", ...}).insert(ignore_permissions=True)`，不走 `enqueue_create_notification`（migrate 进程不保证有 worker）。
- **`hooks.py`**：`after_migrate = ["frappe_china.install.after_migrate"]`。

**`docker/scripts/check_business_order.py`**（新增，宿主或容器内均可跑，纯标准库）

```python
def main(apps_json: str, install_py: str) -> int:
    """apps.json 中 app_name 属于 BUSINESS_APP_ORDER 的条目的出现顺序，
    与 install.py 的 BUSINESS_APP_ORDER（ast 解析该赋值，不 import frappe）比对。
    不一致：打印「apps.json：…／install.py：…」，返回 1；一致返回 0。"""
```

- `docker/scripts/setup.sh` 在第 6 段 `reorder_installed_apps` 那行之后调它；非零即 `exit 1`。

### 验证方式

- 单测 `tests/test_after_migrate.py`：SL-002 ②～⑤（mock `check_app_order` 的返回与抛异常；断言 `Error Log` 与 `Notification Log` 的条数变化，清理只删本测试造的、按标题与时间正向限定）。
- 测试站实跑 SL-002 ①：挪位用 `update_installed_apps_order`，跑完以 `reorder_installed_apps` 归位，清缓存，核 `check_app_order()["ok"]` 为真。命令与输出贴 D 回执。
- SL-002 ⑥：`python docker/scripts/check_business_order.py docker/apps.json <install.py>` 两次（原件与临时副本，副本放 `frappe-bench/tmp/`，用后删）。

---

## 任务 TS-004：补货参数、`auto_indent`、提前期同步（对应切片 SL-003）

### 目标

参数取值的单一入口；原生自动建单显式关闭；保存物料时同步提前期（需求 §4.2.2、§4.2.4、§4.5）。

### 具体改动

**`frappe_china/replenishment/params.py`**

```python
class ItemParams(TypedDict):
    order_cost: float | None      # S
    holding_rate: float | None    # h（百分数，如 20 表示 20%）
    review_days: int | None       # N
    review_start: date | None     # 只取公司
    service_level: float          # 百分数；物料与公司都空时取 95
    lead_time_days: int           # Item.lead_time_days，空记 0
    valuation_rate: float         # Item.valuation_rate，空记 0
    min_order_qty: float

def get_item_params(item_code: str, company: str) -> ItemParams:
    """物料字段非空（is not None 且不为 0——Int/Currency 未填即 0，故 0 视为未填）取物料，否则取公司。"""
```

- 「0 视为未填」写进 docstring，并在 README「已知限制」写一句：物料上无法把参数覆盖成 0。

**`frappe_china/replenishment/lead_time.py`**

```python
def sync_lead_time(doc, method=None) -> None:
    """Item on_update：若存在 name == doc.name 的 Item Lead Time，且其 purchase_time != doc.lead_time_days，
    db.set_value purchase_time = doc.lead_time_days（不触发其 save）。无记录不建。"""
```

- `hooks.py`：`doc_events["Item"] = {"on_update": "frappe_china.replenishment.lead_time.sync_lead_time"}`。

**`docker/scripts/configure_apps.py`**：新增 `configure_stock(notes) -> dict`，把 `Stock Settings.auto_indent` 置 0（走既有 `_apply` 形态，可重复跑、第二次报无改动），在 `main` 里与 CRM、Raven 同列；`preflight` 无须新增检查。

### 验证方式

单测 `tests/test_replenishment_params.py`：SL-003 ①③。SL-003 ②：两站各跑两次 `docker/configure-apps.sh --site …`，贴输出；再查 `tabSingles`。**演示站这一步放到 TS-017 做**（纪律 4），本任务只跑测试站。

---

## 任务 TS-005：选 BOM 共用函数（对应切片 SL-004）

### 目标

实现总纲 §5.3 的 `select_bom`：按单位成本选 BOM，不改写任何 BOM 的库内数据（需求 §4.10、DEC-018）。

### 具体改动

**`frappe_china/production/bom_selection.py`**

```python
def select_bom(item_code, company=None) -> BomChoice:
    if not Item.cn_auto_select_bom:
        return {"bom": _native_default(item_code), "auto": False, "candidates": []}
    names = BOM where item=item_code, is_active=1, docstatus=1 （company 给了则再按 company 过滤）
    if not names: return {"bom": None, "auto": True, "candidates": []}
    candidates = [_unit_cost(frappe.get_doc("BOM", n)) for n in names]
    candidates.sort(key=(unit_cost, 0 if 是原生默认 else 1, name))   # 并列：先原生默认，再名称序（需求 §4.10）
    return {"bom": candidates[0]["bom"], "auto": True, "candidates": candidates}

def _unit_cost(bom) -> BomCandidate:
    for row in bom.operations:                     # 总纲 A10：预置后走 update_hour_rate=False 分支
        rate = Workstation.hour_rate（无 workstation 取 Workstation Type.hour_rate；都无保持行上原值）
        row.hour_rate = rate / bom.conversion_rate if bom.conversion_rate else rate
    bom.calculate_cost(save_updates=False, update_hour_rate=False)
    loss = flt(bom.process_loss_percentage)
    if loss >= 100: unit_cost = inf，并在候选里带 note「损耗率≥100%」
    unit_cost = (bom.raw_material_cost + bom.operating_cost) / bom.quantity / (1 - loss/100)
    # 不扣副产品（secondary_items_cost）：需求 §4.10 公式不含它；拿不准处见回执
```

- `_native_default(item_code)`：`erpnext.manufacturing.doctype.work_order.work_order.get_item_details(item_code, skip_bom_info=True, throw=False)` 的 `bom_no`，取不到再取 `erpnext.stock.get_item_details.get_default_bom(item_code)`。
- `default_boms(item_code)`：上面两个函数结果的并集（去空）。
- 实现时**禁止**调 `bom.update_cost(...)`、`bom.save()`、`row.db_update()`；单测守住（见下）。
- `recommend_bom`：`frappe.has_permission("BOM", "read", throw=True)` 后调 `select_bom`。
- 浮点：`unit_cost` 按 `Currency` 精度 `flt(..., 6)` 比较，避免浮点抖动把并列判成不并列。

### 验证方式

单测 `tests/test_bom_selection.py`（自建三张 BOM：数量 1／10／100、损耗 0／5／2%、工序时长不同）：SL-004 ①②⑥⑦；② 中断言选择前后 `frappe.db.get_value("BOM", n, ["raw_material_cost","operating_cost","total_cost","modified"])` 不变、BOM Operation 行的 `hour_rate`／`modified` 不变。手算值写成常量。

---

## 任务 TS-006：选 BOM 三处接入与评论（对应切片 SL-004）

### 目标

工单新建、生产计划、按订单补货三处都用 `select_bom`；人改过不覆盖、只提示；工单评论记录选择（需求 §4.10、DEC-019／023；总纲 A11／A12，偏离 1／2）。按订单那一处在 TS-008 调用，本任务只做前两处。

### 具体改动

**`frappe_china/production/bom_selection.py`**（续）

```python
def work_order_before_insert(doc, method=None) -> None:
    choice = select_bom(doc.production_item, doc.company)
    if not choice["auto"] or not choice["bom"]:
        return
    if doc.bom_no and doc.bom_no not in default_boms(doc.production_item):
        doc.flags.cn_bom_choice = {**choice, "applied": False}      # 人工指定
        return
    if doc.bom_no != choice["bom"]:
        doc.bom_no = choice["bom"]
        doc.set_work_order_operations()                              # HT-007
        doc.set_required_items()
    doc.flags.cn_bom_choice = {**choice, "applied": True}

def work_order_after_insert(doc, method=None) -> None:
    choice = doc.flags.get("cn_bom_choice")
    if choice: doc.add_comment("Comment", _format_choice(choice))   # 候选、单位成本、选中项、是否人工指定

def production_plan_validate(doc, method=None) -> None:
    for row in doc.po_items:
        choice = select_bom(row.item_code, doc.company)
        if not choice["auto"] or not choice["bom"]: continue
        if row.bom_no and row.bom_no not in default_boms(row.item_code): continue   # 人工指定，不改
        row.bom_no = choice["bom"]
```

- `_format_choice`：一段 HTML 表格（BOM、原料成本、工序成本、数量、损耗率、单位成本、是否选中），标题行与固定文字走 `_()`。
- 生产计划不写评论（需求只要求工单）；子装配行（`sub_assembly_items`）不改：它们取 BOM Item 行上的 `bom_no`（`production_plan.py:2052-2125`），属 BOM 结构，不在本需求范围，进回执拿不准处。
- **`hooks.py`**：`doc_events["Work Order"] = {"before_insert": …work_order_before_insert, "after_insert": …work_order_after_insert}`；`doc_events["Production Plan"] = {"validate": …production_plan_validate}`。
- **前端提示**：`frappe_china/public/js/work_order.js`（`doctype_js` 追加）——`bom_no` 字段变化且文档未保存时，调 `recommend_bom`；`auto` 为真且推荐项不等于当前值时，`frm.dashboard.set_headline_alert` 显示「按成本推荐的是 {0}（单位成本 {1}）」。已保存的工单在 `refresh` 时同样提示一次（数据取评论里记录的那次选择即可，不再算）。只追加提示，不改字段值。

### 验证方式

单测 `tests/test_bom_selection_hooks.py`：SL-004 ③④⑤⑥。三条路径分别用：`frappe.new_doc("Work Order")` 填 `production_item` 后按原生 `get_item_details` 带出 `bom_no` 再 `insert()`；`sales_order.make_work_orders(json.dumps({"items": [...]}), so, company)`；生产计划 `get_items()` → `save()` → `make_work_order()`。断言工单 `bom_no`、工序行 `bom`、原料行 `item_code` 集合、评论内容；生产计划另断言 `get_items_for_material_requests(plan.as_dict())` 返回的原料集合属选中 BOM。前端提示在 TS-017 演示站截图一张。

---

## 任务 TS-007：需求取样、安全库存、再订货点（对应切片 SL-003）

### 目标

一套日需求取样，安全库存与再订货点、三种规则共用（需求 §4.2.3 公共口径、§4.3、§4.4；总纲 A4～A6）。

### 具体改动

**`frappe_china/replenishment/demand.py`**

```python
DEMAND_STOCK_ENTRY_PURPOSES: Final = ("Material Issue", "Manufacture", "Material Consumption for Manufacture")
DEMAND_VOUCHER_TYPES: Final = ("Delivery Note", "Sales Invoice")
WINDOW_DAYS: Final = 90

def daily_demand(item_codes: list[str], warehouses: list[str] | None, as_of: date) -> dict[str, list[float]]:
    """返回 {item_code: [90 个日需求，从 D−89 到 D]}，无出库日为 0。
    warehouses 为 None 表示不按仓库过滤（安全库存用，按当次公司的全部仓库——由调用方传该公司仓库清单）。
    一条 SQL：SLE 按 (item_code, posting_date) 汇总 −actual_qty，条件为
      is_cancelled=0 且 actual_qty<0 且 posting_date ∈ (D−89, D] 且 warehouse in warehouses 且
      (voucher_type in DEMAND_VOUCHER_TYPES
       或 voucher_type='Stock Entry' 且 voucher_no 对应 Stock Entry.purpose in DEMAND_STOCK_ENTRY_PURPOSES)。
    Stock Entry 的 purpose 经 join `tabStock Entry` 取（SLE 无 purpose 列）。"""

def mean_and_stdev(series: list[float]) -> tuple[float, float]:
    """均值＝sum/90；σ＝statistics.stdev（样本，总纲 A5）；全 0 时 σ=0。"""

def warehouses_of_row(reorder_row) -> list[str]:
    """warehouse_group 有值：取该组下全部叶子仓（lft/rgt），否则 [warehouse]（总纲 A6）。"""

def projected_qty(item_code: str, warehouses: list[str]) -> tuple[float, dict]:
    """Σ Bin.projected_qty 及构成（actual/ordered/indented/planned/reserved 各项之和），供触发依据。"""
```

**`frappe_china/replenishment/safety_stock.py`**

```python
def z_value(service_level: float) -> float:
    """NormalDist().inv_cdf(service_level/100)；service_level 不在 (50, 100) 时返回 None 并由调用方记问题。"""

def compute_safety_stock(company: str, as_of: date) -> StepResult:
    items = Item where cn_auto_replenishment_params=1 and disabled=0
    company_warehouses = Warehouse where company=company and is_group=0
    other_companies = 启用补货的其它公司
    批量取 daily_demand(items, company_warehouses, as_of)
    for item:
        若该物料在 other_companies 的仓库里窗口内也有需求：problems 记「物料在多家启用公司有出库」，skip（总纲偏离 21）
        p = get_item_params(item, company)
        if p.lead_time_days <= 0: 写 0，problems 记「提前期缺失」，continue
        z = z_value(p.service_level)；为 None 记问题 continue
        ss = flt(z * σ * sqrt(LT), Item.safety_stock 精度)
        与现值不同才 frappe.db.set_value("Item", item, "safety_stock", ss)（不触发 Item.save，免得跑 sync_lead_time 等）
```

**`frappe_china/replenishment/reorder_level.py`**

```python
def compute_reorder_levels(company: str, as_of: date) -> StepResult:
    rows = Item Reorder 子表行，父物料 cn_auto_replenishment_params=1，行仓库（或组）属本公司
    for row:
        p = get_item_params(item, company)
        if p.lead_time_days <= 0: problems 记「提前期缺失」，不写本行，continue（总纲偏离 20）
        d̄ = mean(daily_demand([item], warehouses_of_row(row), as_of))
        level = flt(d̄ * LT + Item.safety_stock（此刻库内值）, 行字段精度)
        与现值不同才 frappe.db.set_value("Item Reorder", row.name, "warehouse_reorder_level", level)
```

- 两个函数**不 commit**（由每日入口统一处理）；单物料异常 `try/except` 记 `problems`（含物料名与异常摘要），并 `frappe.log_error` 一条。

### 验证方式

单测 `tests/test_safety_stock.py`、`tests/test_reorder_level.py`：造一家测试公司（`_FCT` 前缀）、两个仓库、一个组仓；用库存凭证与发货单按指定日期造 90 天出库（含零出库日、含一笔仓间调拨与一笔窗口外出库，SL-003 ⑧）。SL-003 ④～⑦。手算值（σ 用样本标准差）写成常量，例如 9 天有出库的序列先在测试注释里给出逐项求和。

---

## 任务 TS-008：补货建议单与三种规则（对应切片 SL-005）

### 目标

新 DocType「补货建议单」；三种规则各自判触发、算建议量，按 物料×仓库×规则 去重写入（需求 §4.2.1、§4.2.3；DEC-001／003／006／021／022；总纲 A7～A9，偏离 11～15）。

### 具体改动

**DocType `Replenishment Suggestion`**（模块 `Stock Plus`，不可提交，`naming_rule` 用 naming series `RS-.YYYY.-.#####`）

| 字段 | 类型 | 说明 |
|---|---|---|
| `company`、`item_code`、`warehouse` | Link，必填，`in_standard_filter` | |
| `item_name`、`stock_uom` | Data／Link，`fetch_from` item_code，只读 | |
| `rule` | Select：`EOQ`／`Periodic Review`／`Against Sales Order`，必填 | 三选一；源词按总纲 A16 查官方词典后定，下同 |
| `calculation_date` | Date，必填 | 计算日 D |
| `suggested_qty` | Float，必填 | 库存单位；采纳前可改 |
| `status` | Select：待定／已采纳／已忽略三值，默认第一个，只读 | 源词由执行者按 A16 选官方词典里没有的词 |
| `material_request_type` | Select（同 `Item Reorder.material_request_type` 选项） | 采纳时用 |
| `material_request` | Link → Material Request，只读 | 采纳后回填 |
| `basis` | Table → `Replenishment Basis Item` | 触发依据（总纲 A7） |
| `source_orders` | Table → `Replenishment Source Order` | 仅按订单规则 |

- 子表 `Replenishment Basis Item`：`basis`（Select，固定选项：Projected Qty、Actual Qty、Ordered Qty、Indented Qty、Planned Qty、Reserved Qty、Reorder Level、Average Daily Demand、Annual Demand、Order Cost、Holding Cost Rate、Valuation Rate、Holding Cost、Lead Time Days、Review Days、Safety Stock、Target Qty、EOQ、Min Order Qty、Net Shortage）、`value`（Float）、`note`（Data）。源词同样先查官方词典，官方已有且译文合用的直接用（如 `Projected Qty`、`Safety Stock`）。
- 子表 `Replenishment Source Order`：`sales_order`（Link）、`sales_order_item`（Data）、`item_code`（Link，成品）、`pending_qty`（Float）。
- 权限：Stock Manager 读写建删；Stock User、Purchase User 只读。`status`、`material_request` 只经 TS-009 的方法改。
- 列表视图：`in_list_view` 物料、仓库、规则、计算日期、建议量、状态；状态指示色（待定橙、已采纳绿、已忽略灰）放 `replenishment_suggestion_list.js`。

**`frappe_china/replenishment/rules.py`**

```python
class Proposal(TypedDict):
    item_code: str; warehouse: str; rule: str
    qty: float; mr_type: str
    basis: list[tuple[str, float, str]]        # (basis 选项, 值, 备注)
    sources: list[dict]                        # 仅按订单

def eoq_proposals(company, as_of, problems) -> list[Proposal]:
    rows = Item Reorder 行，父物料 cn_rule_eoq=1，行仓库（或组）属本公司
    for row:
        pq, parts = projected_qty(item, warehouses_of_row(row))
        if pq > row.warehouse_reorder_level: continue              # 不触发
        p = get_item_params(item, company); d̄ = mean(daily_demand(...))
        D_year = d̄ * 365; H = p.valuation_rate * p.holding_rate / 100
        if not (D_year and p.order_cost and H): problems「参数缺失：…」; continue   # 需求 §4.2.3
        q = sqrt(2 * D_year * p.order_cost / H)
        if p.min_order_qty and q < p.min_order_qty: q = p.min_order_qty
        q = ceil(q) if 库存单位 must_be_whole_number else flt(q, 精度)
        mr_type = row.material_request_type or "Purchase"

def periodic_proposals(company, as_of, problems) -> list[Proposal]:
    同上取行，父物料 cn_rule_periodic=1
    p = get_item_params(...)
    if not (p.review_days and p.review_start): problems「参数缺失」; continue
    if as_of < p.review_start or (as_of - p.review_start).days % p.review_days: continue   # 非盘点日
    target = d̄ * (N + LT) + Item.safety_stock
    q = target - pq；q <= 0 不出（需求 §4.2.3）

def order_proposals(company, as_of, problems) -> list[Proposal]:
    so_rows = Sales Order Item，SO docstatus=1、company、status not in (Closed, Completed, On Hold)、
              transaction_date <= as_of；pending_stock_qty = (qty − delivered_qty) × conversion_factor − work_order_qty（总纲 A9、偏离 15）
    po_items = [{"item_code", "bom_no": select_bom(item, company)["bom"]（auto 为假时即原生默认）,
                 "planned_qty": pending_stock_qty, "include_exploded_items": 1, "sales_order", "idx"} …]   # 无 BOM 的成品原样给，原生按外购处理
    doc = {"company": company, "po_items": po_items, "ignore_existing_ordered_qty": 1,
           "include_non_stock_items": 0, "include_subcontracted_items": 1,
           "include_safety_stock": 0, "consider_minimum_order_qty": 0, "for_warehouse": None}
    rows = get_items_for_material_requests(doc)     # 原生 production_plan.py:1744；调用前后保存还原 frappe.message_log，压掉其 msgprint
    只留物料勾了 cn_rule_order=1 的行；无仓库的行 problems「无默认仓库」
    按 (item_code, warehouse) 汇总 quantity × conversion_factor（换回库存单位），sources 汇总来源 sales_order
    mr_type = 行 material_request_type or "Purchase"（偏离 14）

def upsert(company, as_of, proposal) -> str:
    """去重：同 company×item×warehouse×rule 且状态为待定的一条，加 for_update 读；有则覆盖
    calculation_date、suggested_qty、material_request_type、basis、source_orders 后 save；无则 insert。返回单名。"""
```

- 「计划量」与需求一致：原生 `projected_qty`；`basis` 子表把 `parts` 各项、再订货点、算式每个输入与中间结果逐行写入，足以手算（需求 §4.2.1）。
- `material_request_type` 取值域与 `Item Reorder` 一致（`Purchase/Transfer/Material Issue/Manufacture`）。
- **`hooks.py` fixtures**：本任务加 TS-002 留下的 `Material Request-cn_replenishment_suggestion`。

### 验证方式

单测 `tests/test_replenishment_rules.py`：SL-005 ⑤⑥⑦（逐规则造数、手算期望值写成常量）；`tests/test_replenishment_suggestion.py`：SL-005 ①② 的去重部分（直接调三个 `*_proposals` 与 `upsert`）。

---

## 任务 TS-009：每日计算入口与采纳（对应切片 SL-005）

### 目标

总纲 §5.2 的 `run_daily`／`run_now`／`scheduled_daily`；建议单的采纳、忽略与批量动作（需求 §4.2.1、§4.12、§4.13；DEC-005；总纲 A8，偏离 10）。

### 具体改动

**`frappe_china/replenishment/daily.py`**

```python
def run_daily(as_of_date=None, company=None) -> DailyResult:
    D = getdate(as_of_date or today())
    if D > getdate(today()): frappe.throw(_("Calculation date {0} is later than today").format(D))
    companies = [company] if company else Company where cn_replenishment_enabled=1
    for c in companies:
        steps = [compute_safety_stock(c, D), compute_reorder_levels(c, D)]   # 次序固定（需求 §4.12）
        problems = []; written = 0
        for fn in (eoq_proposals, periodic_proposals, order_proposals):
            for p in fn(c, D, problems):
                try: upsert(c, D, p); written += 1
                except Exception: problems.append(...); frappe.log_error(...)
        steps.append({"step": "suggestions", "processed": written, ...})
    return result

def scheduled_daily():
    result = run_daily()
    frappe.db.commit()
    if not result["ok"]: frappe.log_error(title=_("Daily replenishment calculation has problems"), message=…)
```

- `run_now`：`frappe.only_for(("System Manager", "Stock Manager"))`；调 `run_daily(as_of_date)` 后 `frappe.db.commit()` 并返回结果；前端以对话框列出每公司三步的条数与 `problems`。
- docstring 原样写总纲 §5.2 的四条接口约定。
- **`hooks.py`**：`scheduler_events = {"daily": ["frappe_china.replenishment.daily.scheduled_daily"]}`。

**`frappe_china/stock_plus/doctype/replenishment_suggestion/replenishment_suggestion.py`**

```python
@frappe.whitelist()
def adopt(name: str, qty: float | None = None) -> str:
    """Stock Manager。行锁读；status 非待定 → throw。qty 给了即覆盖 suggested_qty（须 > 0）。
    建 Material Request：material_request_type＝单上的值（`Transfer` 映射为 MR 的 `Material Transfer`，
      同原生 reorder_item.py:241-244；其余同名），company，transaction_date＝schedule_date＝calculation_date，
      cn_replenishment_suggestion＝name，items 一行（item_code、qty＝suggested_qty、uom＝stock_uom、
      conversion_factor＝1、warehouse、schedule_date）。insert → submit。
    回填 material_request、status＝已采纳。返回 MR 名。"""

@frappe.whitelist()
def ignore(name: str) -> None: ...      # 同权限；非待定 throw；status＝已忽略

@frappe.whitelist()
def bulk_action(names: list[str] | str, action: str) -> list[dict]:
    """action ∈ {"adopt", "ignore"}。逐条在 savepoint 里调 adopt/ignore，失败回滚该条、记原因；
    返回 [{"name", "ok", "result" 或 "error"}]（总纲偏离 10）。"""
```

- MR 的 `transaction_date` 用计算日期（总纲 A8）：S8 回放中采纳也按模拟日出单；`schedule_date` 不得早于 `transaction_date`，二者同值即可。
- 表单 js：待定时显示「采纳」（弹框可改建议量）与「忽略」两个按钮；表头加「立即计算」按钮调 `run_now`。列表 js：两个批量动作调 `bulk_action`，结果逐条 `msgprint`。
- MR 被取消时：建议单**不回滚状态**（已采纳是人的决定，MR 取消另属一次决定）；README「已知限制」写一句。

### 验证方式

单测 `tests/test_replenishment_daily.py`：SL-005 ①～④、⑧～⑩。⑧ 的「D＋1 出库不计入」：先 `run_daily(D)` 记下建议量，再造一笔 D＋1 日的出库、再 `run_daily(D)`，建议量不变（同时证明幂等）；D＋1 晚于今天时这笔出库无法过账，测试里 D 取今天之前 2 天。⑨：mock 一个物料的 `get_item_params` 抛异常。⑩：`frappe.set_user` 切到只有 Stock User 角色的测试用户。
