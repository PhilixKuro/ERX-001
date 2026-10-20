# P1-S8 数据与操控 —— 开发方案·Part1：`frappe_debug` 骨架与 `frappe_china` 缺陷修复

**来源需求**：[R4 B 需求文档](../R04-需求文档/P1-S8-R4-B需求文档.md) §4.5～4.8、§4.10～4.14｜**前置依赖**：无（本 Stage 第一个 Part）｜**日期**：2026-10-20｜**编写者**：Claude（Opus 5.5）
**总纲**：[P1-S8-R5-C开发方案-总纲](P1-S8-R5-C开发方案-总纲.md)——架构决策 A1～A20、偏离、接口契约、技术假设、执行纪律都在那里，本 Part 不重复。

## 切片划分与验收

| 切片 | 功能点 | 验收条件 |
|---|---|---|
| **SL-001** `frappe_debug` 骨架与装序（基础设施） | 需求 TS-001、`PH-P1074`；A1 | ① 测试站 `bench --site test.localhost list-apps` 末行为 `frappe_debug`，`frappe_china.install.check_app_order()["ok"]` 为真（贴输出）；② `grep -rn frappe_debug frappe-bench/apps/frappe_china/frappe_china --include=*.py --include=*.js --include=*.html --include=*.json` 只命中 `install.py` 的 `TAIL_APPS` 一行与 README（贴输出）；③ 单测：`reorder_installed_apps` 调用后、提交前 `frappe.clear_cache` 未被调用，`frappe.db.commit()` 后被调用一次；调用后 `rollback()` 则不调用；④ `frappe_debug` 测试套件在测试站可跑（至少一条冒烟用例），`ruff check`／`ruff format --check` 对 `frappe_debug` 0 告警 |
| **SL-002** 完工入库账务 | 需求 TS-002、CR-003、OB-065／055／041、DEC-015／016、BR-008 | ① 新建中式测试公司：`expenses_added_to_stock_account` 为该公司 `410199` 科目、`400101` 的 `account_type` 为空、`Wire Transfer`／`Cheque`／`Credit Card`／`Bank Draft` 四种收付款方式各有一行该公司 → `1002` 科目；② 迁移补丁对一家「`expenses_added_to_stock_account` 为空、`400101` 为 `Cost of Goods Sold`、无银行收付款行」的中式公司补齐三项，对已填了别的值的公司不改、对非中式公司不动，第二次运行无改动；③ 有工序成本的工单完工入库（附加费用行不填科目）提交成功，GL 只有三类行：借成品存货科目、贷在产品科目、贷 `410199`；无任何 `root_type` 为 Income／Expense 的行；`400101` 在该凭证上借贷合计相等（含为 0 不出行的情形）；与 R2 对照数同构（借 `1405`／贷 `1409`／贷 `410199`）；④ 工单发料单与完工入库单保存时 `frappe.message_log` 无「销售成本」类提示（`stock_entry.py:934-945`）；⑤ 付款单选 `Wire Transfer` 时 `paid_from` 自动为 `1002`、不弹「缺失科目」；⑥ 非中式科目表的公司做同样的完工入库，差异科目保持原生取法 |
| **SL-003** 工艺损耗反算 | 需求 TS-003、CR-004、`PH-P1089`、DEC-013／014／037；A14／A15／A18 | ① BOM 三道工序 3%／1%／1%、数量 1000、单位「支」：保存后 `process_loss_percentage` 只读，值为 A18 结果 4.9（理论 4.9303），表单出提示写明理论值与取值；数量 1500 → 4.8、300 → 4.0、2500 → 4.92；数量 1234、7 → 0 且出提示；每种数量**存两次**都不报错；三道全空时整体值可手填、不被改；② SO 5000 支、BOM 整体 5%、无工序损耗率：生产计划「取销售订单」带出后保存，`planned_qty`＝5264、`cn_recommended_qty`＝5264；③ 同 SO、工序 3%／1%／1%：`planned_qty`＝5261；④ 超产比例 0：5264 支工单（生产计划建）能提交；该订单另建 1 支工单提交被拦（`OverProductionError`）；先提交 5000 支、再建 265 支被拦；上游 `validate_work_order_against_so` 源码 sha256 与登记值不同时守卫测试失败并打印两个哈希；⑤ 计划数量人改为 5300 后再保存仍为 5300，表单显示「推荐 5264」；把 BOM 换成工序 3%／1%／1% 的 BOM 后保存变为 5261；把订单数量改为 6000、生产计划重新取订单后变为按 6000 反算；⑥ 按订单补货：R2 同构数据（5000 支、8.68 kg／千支、整体 5%）建议量＝ 5264 × 8.68 ÷ 1000 ＝ 45.69152（按建议量字段精度），来源子表的未交数量仍记 5000 |
| **SL-004** 税模板沿用与改名 | 需求 TS-004、OB-034／035、DEC-018／019；偏离 3／4 | ① 测试公司下，报价单选 `13% 专票 不含税价` 模板，经 CRM 商机路径（`create_customer` 建客户，HT-013）建的客户 `tax_category`＝`13% 专票 不含税价`；由报价单 `make_sales_order` 生成订单，调 `get_party_details` 后 `taxes_and_charges` 仍为该不含税模板；② 测试站一家按旧名建好的中式公司跑改名补丁：9 个 `Tax Category`、12 个税模板 `title`／记录名、13 条 `Tax Rule` 的引用全部换成新名，税率、科目、`included_in_print_rate`、规则条数逐条不变（补丁前后各取一次比对）；第二次运行无改动；③ `grep -rn "P13专票\|P0无税\|P3专票\|P1专票\|P9专票\|P6专票" frappe_china` 在 `.py`、`.json` 中只命中补丁里的旧名映射表；全量测试过 |
| **SL-005** 工时口径 | 需求 TS-005、OB-048／050／025；A16／A17 | ① BOM 数量 1000、工序 卷簧 50 分（勾「基于批量创建」、`batch_size` 2500）／回火 18 分／磨端 36 分：5000 支工单保存后三行 `time_in_mins`＝250／90／180；表单新建、生产计划建、销售订单建三条路径相同；② 关产能计划、卷簧拆分数量 2000：提交后三张卷簧卡 `time_required`＝100／100／50；③ 开产能计划（测试内临时开、结束还原）：三张卷簧卡 `time_required` 同 ②，各卡 `scheduled_time_logs` 合计等于 `time_required`，第二张卡的起时等于第一张卡的止时（或其后）；④ 负荷报表在该工位、该周的需求工时＝（100＋100＋50）÷ 60；⑤ 固定时间工序与 `bom ≠ 工单 bom_no`（多级 BOM 展开）的工序行不被改；⑥ 测试站新开 BOM 表单，「工序」子表默认显示工序、工位、工序时间（分钟）、工序损耗率四列（截图） |
| **SL-006** 换 BOM 人确认 | 需求 TS-006、OB-046；A13 | ① 测试站浏览器：生产计划取销售订单后点保存，弹框列出候选 BOM 与单位成本；点「保留当前」→ 保存后 `bom_no` 不变、`cn_bom_source`＝`kept`；再保存点「换用推荐」→ `bom_no` 为推荐项、`cn_bom_source`＝`confirmed`（截图两张）；② 由该计划建出的工单评论为「由生产计划带入」；表单新建工单经弹框确认换用的评论为「按成本推荐、人已确认」；人手指定非默认 BOM 的为「人工指定」并列推荐项；服务端建单（`make_work_orders`、按订单补货展开）为「按成本自动选用」；③ 单测：`cn_bom_source` 有值时服务端不改 `bom_no`；为空时照 S7 自动选；④ S7 `test_bom_selection*` 中断言「静默替换」的用例改为断言新口径，D 回执逐条列出 |
| **SL-007** 补货口径与呈现 | 需求 TS-007、OB-082／083／037／038；A11／A12；偏离 7 | ① 单测：线材在原料仓 90 天内发料（`Material Transfer for Manufacture`，原料仓 → 在制品仓）6 次、完工入库在在制品仓扣料 6 次、另有一笔仓间调拨：日需求序列只含 6 次发料、发生在原料仓；② 同数据：该物料有一行原料仓的 `Item Reorder`、提前期 7 天：`safety_stock` 与再订货点取同一序列，再订货点＞`safety_stock`＞0，两值与测试里写死的手算值一致；③ 不经在制品仓（`skip_transfer`）的工单直接从原料仓完工入库时，该出库计入；④ 无 `Item Reorder` 行的物料，安全库存取该公司全部非在制品仓；⑤ `run_daily` 的每一步结果含 `changes`，安全库存行列旧值→新值，再订货点行列物料×仓库旧值→新值，建议步对未触发的物料给出原因；「立即计算」弹窗按物料成表、物料号可点开（截图）；⑥ 补货建议列表首列为物料号（`item_code`）、另列物料名称；依据子表默认显示依据项、数值、说明，来源订单子表默认显示订单、物料、未交数量；依据项 23 个选项中文界面全为中文（截图）；⑦ S7 补货测试中因口径改变而变的期望值逐条改，D 回执列出 |
| **SL-008** 演示画面译名与显示 | 需求 TS-008、OB-024／029／039／042／059／068～071、`PH-P1097` | ① 工序与 BOM 工序的计件单价填 0.004 保存后读回 0.004、表单显示 0.004；② CRM 线索 7 个状态、商机 7 个状态在 `/crm` 下拉与看板中为中文（截图）；③ 提交采购入库后的绿色提示为「已成功提交采购入库」类中文（截图）；④ 库存与账面对比报表无差异时表格区显示「无差异」（截图）；有差异时照常列行；⑤ 质检单「检验类型」三项为来料检验／出货检验／过程检验，且电话场景的 `Incoming`／`Outgoing`（CRM 通话）仍为呼入／呼出；⑥ SPC 报表列名与摘要中文会话下全中文（截图），HT-009 的原因写进 D 回执；⑦ 计件汇总结果弹窗分「已创建」「已跳过」「问题」三段，各段无内容时写「无」；⑧ 计件汇总列表有员工姓名列；⑨ 计件明细「单价来源」列三种值都为中文；数量为 0 的时间行不进明细；⑩ 负荷报表按周、起始日为周三时首桶标签为该周三的日期，按月、起始日为 15 日时首桶标签为 15 日；其余桶不变 |
| **SL-009** 策略对比报表与侧栏入口 | 需求 TS-009／010、DEC-001／012／035、OB-009／067／031；偏离 8／14／17 | ① 小数据（一个物料、三段各 10 天、手工造采购订单与出入库）：四项指标与段内天数与测试里写死的手算值一致，持有成本按天数 ÷ 365 折算；② 缺料次数：段内三张工单——计划开工日原料不足且实际开工晚 → 计；原料不足但实际开工不晚 → 不计；实际开工晚但原料够 → 不计：结果 1；③ 段数 1 或 4、段起止颠倒、段重叠时报错；物料筛选为空时缺省取启用了任一补货规则的物料；④ 中文会话下列名全中文，图表显示三段总成本柱（截图）；⑤ 业务流程侧栏新增 14 个入口（需求 §4.12 的 13 个＋供应商评分），每个可点开；⑥ 浏览器打开 `/desk/quotation/new?sidebar=Business%20Flow` 时左侧栏为「业务流程」（HT-011，截图） |
| **SL-010** 演示站前置数据 | 需求 TS-011、OB-005／016、DEC-024 | ① 测试站跑前置配置后 `Gender`、`Salutation` 有 frappe 向导的那几条，员工表单性别下拉为中文；② `Stock Settings.enable_serial_and_batch_no_for_item`＝1；③ `Administrator` 的 `first_name`＝「演示管理员」、desk 右上角显示该名；④ 第二次运行报「无改动」 |

执行每个切片前，对照该切片验收条件检查方案覆盖性——如发现按方案写出的代码无法通过验收条件，暂停反馈，不硬写。

## 任务清单

| 任务 | 对应切片 | 可并行否 |
|---|---|---|
| TS-001 `frappe_debug` 骨架、装序、`after_commit` | SL-001 | 否 |
| TS-002 账务修正与迁移 | SL-002 | 否 |
| TS-003 损耗率字段与整体值 | SL-003 | 否 |
| TS-004 计划数量反算、超产替换、按订单放大 | SL-003 | 否 |
| TS-005 税模板沿用与改名 | SL-004 | 否 |
| TS-006 工时口径与 BOM 工序表列 | SL-005 | 否 |
| TS-007 换 BOM 人确认与来源记录 | SL-006 | 否 |
| TS-008 补货口径与结果呈现 | SL-007 | 否 |
| TS-009 演示画面译名与显示 | SL-008 | 否 |
| TS-010 策略对比报表 | SL-009 | 否 |
| TS-011 业务流程侧栏入口 | SL-009 | 否 |
| TS-012 演示站前置数据 | SL-010 | 否 |

---

## 任务 TS-001：`frappe_debug` 骨架、装序、`after_commit`（对应切片 SL-001）

### 目标

建 `frappe_debug` app 装到测试站末位，`frappe_china` 不引用它；顺带关掉 `reorder_installed_apps` 「先清缓存后提交」的窗口（需求 §4.5、`PH-P1074`）。

### 具体改动

1. **先问用户**（总纲纪律 9）：远程仓库名（建议 `PhilixKuro/FrappeDebug`，与 `FrappeChina` 同形）、可见性。获答前只本地 `git init`，`main` 分支。
2. **手写骨架**（`bench new-app` 会交互提问，子 Agent 读 `frappe/utils/boilerplate.py:42-72`）：以 `frappe_china` 的 `pyproject.toml`、`frappe_china/__init__.py`、`hooks.py` 头部、`modules.txt`、`patches.txt`、`.pre-commit-config.yaml` 为样板，写 `frappe-bench/apps/frappe_debug/`：
   - `pyproject.toml`：`name = "frappe_debug"`，`[tool.bench.frappe-dependencies]` 与 `frappe_china` 同；ruff 配置照抄。
   - `frappe_debug/hooks.py`：`app_name`、`app_title = "Frappe Debug"`、`required_apps = ["frappe_china"]`；不注册 `override_*`、`regional_overrides`、`translated_search_doctypes`、译名 csv。
   - `modules.txt`：`Frappe Debug`；`frappe_debug/frappe_debug/__init__.py`。
   - 目录（A1）：`builders/`、`scenario/`、`demo/`、`data/`、`public/js/demo/`、`public/demo/`、`tests/`（`tests/test_smoke.py`：断言 app 已装、`frappe_china` 在其前）。
   - README：一句定位（演示与造数专用，客户正式库不装）＋「客户正式库从空站新建，不从演示站快照或备份恢复」（需求 §4.5 末条）。
3. **装到测试站**：`bench pip install -e apps/frappe_debug`（或 `bench setup requirements`）→ 把 `frappe_debug` 加进 `sites/apps.txt` → `bench --site test.localhost clear-cache` → `install-app frappe_debug` → `bench execute frappe_china.install.reorder_installed_apps` → `check_app_order`。
4. **`docker/apps.json` 与 `setup.sh`**：远程仓库获准建好并推送后，按 `frappe_china` 条目同形加一条（`url`／`branch: main`／`commit`／`app_name`），排在 `frappe_china` 之后；`docker/lock-apps.sh` 填 commit。`setup.sh` 不改（按 `apps.json` 顺序装、6.2 段归位，子 Agent 读 `setup.sh:351-397`）。`check_business_order.py` 不改（只比业务 app）。
5. **`frappe_china/install.py` `reorder_installed_apps`**（`:215-224`）：

```python
def reorder_installed_apps() -> dict:
    ...  # 前段不变：update_installed_apps_order、update_versions
    # PH-P1074：广播须在新顺序提交之后，否则别的进程在窗口内按旧库值重建钩子缓存
    frappe.db.after_commit.add(frappe.clear_cache)
    frappe.db.after_commit.add(frappe.client_cache.erase_persistent_caches)
    return ...
```

`frappe.db.after_commit` 是 v16 的 `CallbackManager`（`frappe/database/database.py:130`、`:1194` 提交后跑、`:1203` 回滚时清）。`setup.sh` 6.2 段经 `bench execute` 调它，`bench execute` 末尾 `frappe.db.commit()`（`frappe/commands/utils.py:315-316`）。其它调用方若自己不提交，D 步 grep 全部调用点核一遍、补提交或注明。

### 验证方式

SL-001 ①②④ 贴命令输出；③ 单测 `frappe_china/tests/test_install.py` 加两条（mock `frappe.clear_cache` 计数）。记下 `frappe_china` 与 `frappe_debug` 两套测试的用例数作基线。

---

## 任务 TS-002：账务修正与迁移（对应切片 SL-002）

### 目标

完工入库不手填费用科目、不产生损益分录（需求 §4.7、BR-008）；银行类收付款方式带银行科目。

### 具体改动

1. **`cn_tax/data/company_defaults.json`**：`default_accounts` 加 `"expenses_added_to_stock_account": "410199"`（`accounting/company.py:145-158` 逐个 `db_set`，无须改代码；410199 在科目表中为 `Expenses Included In Valuation` 类型）；新增块 `"mode_of_payment_account": {"Wire Transfer": "1002", "Cheque": "1002", "Credit Card": "1002", "Bank Draft": "1002"}`。
2. **科目表 json**（`cn_smes_chart_of_accounts2024.json:875-879`）：`400101` 的 `account_type` 改 `""`。父科目 `4001` 不动（需求只说 `400101`）。
3. **`accounting/company.py`**：`build_cn_company` 内新增 `set_cn_mode_of_payment_accounts(company)`——对映射里每个收付款方式记录（存在才处理；记录名英文，子 Agent 读 `erpnext/setup/setup_wizard/operations/install_fixtures.py:255-263`），在其 `accounts` 子表找该公司行，无则 append `{company, default_account}`，有且为空则填；有别的值不动。
4. **差异科目统一**，新文件 `accounting/stock_entry_accounts.py`：

```python
UNIFY_PURPOSES: Final = ("Manufacture", "Repack")

def unify_difference_account(doc, method=None) -> None:
    """Stock Entry before_validate（A 步 DEC-015；挂 before_validate 而非 validate：
    原生 validate_difference_account 在 controller validate 里先按旧科目出提示，stock_entry.py:322）。
    purpose 不在 UNIFY_PURPOSES、或公司不是中式科目表（is_cn_chart）→ 返回。
    取该公司 account_number=400101 的明细科目；取不到 frappe.log_error 一条并返回（不 throw）。
    全部 items 行 expense_account 改为它（无论原值）。"""
```

   `hooks.py`：`"Stock Entry": {"before_validate": [batch_uom.apply_batch_factor, stock_entry_accounts.unify_difference_account]}`（列表，顺序如此）。
5. **迁移补丁** `patches/s8_cn_accounting_defaults.py`（登 `patches.txt` `[post_model_sync]`），照 `fd004_default_accounts.py:13-30` 的形态：对每家 `is_cn_chart` 公司 ① `expenses_added_to_stock_account` 为空才写 `410199`；② 该公司 `400101` 科目 `account_type == "Cost of Goods Sold"` 才改为空；③ 调第 3 步的函数。取不到科目 `log_error`＋`print`，不抛。
6. **HT-001**：先按第 1 步跑 SL-002 ③；附加费用行没有自动带出 `410199` 时，在 `unify_difference_account` 里给 `additional_costs` 中 `expense_account` 为空的行补该公司 `410199`，D 回执记偏离。

### 验证方式

`tests/test_s8_accounting.py`：SL-002 ①②③④⑥（④ 断言 `frappe.message_log` 不含该提示的源词）；⑤ 单测调原生 `get_bank_cash_account` 或付款单 `set_missing_values`，断言 `paid_from`。S4 `test_default_account_postings` 等既有用例中断言完工入库分录或 `400101` 类型的，同任务内按新口径改、回执列出。

---

## 任务 TS-003：损耗率字段与整体值（对应切片 SL-003 ①）

### 目标

工序损耗率填了就自动算整体值，且整数单位下存得进（需求 §4.6.1、A18）。

### 具体改动

1. **Custom Field**（fixtures、`hooks.py` fixtures 名单）：`BOM Operation-cn_process_loss_percentage`（Percent，标签 `Process Loss % (Operation)`，`insert_after: time_in_mins`，`in_list_view: 1`）。
2. **新文件** `production/process_loss.py`：总纲 §5.1 的四个函数。`whole_number_loss_percentage` 伪代码：

```python
def whole_number_loss_percentage(quantity, theoretical):
    q = flt(quantity)
    loss = floor(q * theoretical / 100 + 1e-9)
    while loss > 0:
        p = flt(loss * 100 / q, 9)            # 按 Percent 字段库内精度 decimal(21,9)
        if (q * p / 100) % 1 == 0:            # 与 bom.py:1371 同一判式
            return p, False
        loss -= 1
    return 0.0, True
```

3. **BOM `validate`** 钩子 `bom_process_loss(doc, method=None)`：`overall_loss_percentage(doc)` 为 None → 返回（手填照旧）；否则产品库存单位 `must_be_whole_number` 时取 `whole_number_loss_percentage(doc.quantity, 理论值)`，不是时取 `flt(理论值, 9)`；写 `doc.process_loss_percentage` 并调 `doc.set_process_loss_qty()`；取值与理论值不同时 `frappe.msgprint`（黄色）写明两者；置 0 时写偏离 6 的那句。
   **挂点顺序**：原生 `validate` 在 `:300` 先 `set_process_loss_qty`、`:301` 再 `validate_uoms`，`doc_events validate` 在类方法之后。改挂 **`before_validate`**，使原生 validate 用的是新值。
4. **前端**：`public/js/bom.js`（`doctype_js` 加 `"BOM"`）：工序子表 `cn_process_loss_percentage` 变化时，若任一行有值则 `frm.set_df_property("process_loss_percentage", "read_only", 1)`；`refresh` 同判。不在前端算值（以服务端为准，保存后刷新）。
5. **译名**：字段标签、提示两句进 `zh.csv`。

### 验证方式

`tests/test_process_loss.py`：`whole_number_loss_percentage` 对 1000／1500／300／2500／1234／7 的期望值（4.9／4.8／4.0／4.92／0／0）写死；每种数量建 BOM `insert` 后再 `save` 一次（HT-003）；全空时手填 5 不被改；产品单位非整数单位时整体值＝4.930300000。

---

## 任务 TS-004：计划数量反算、超产替换、按订单放大（对应切片 SL-003 ②～⑥）

### 目标

生产计划从订单带出时按合格率放大、人改不覆盖；放大后的工单能提交；按订单补货同一口径（需求 §4.6.2～4.6.4）。

### 具体改动

1. **Custom Field**（`Production Plan Item`，A14）：`cn_demand_qty`（Float，只读，标签 `Order Pending Qty`）、`cn_recommended_qty`（Float，只读，标签 `Recommended Qty`）、`cn_recommended_bom`（Link BOM，只读，`hidden: 1`）。
2. **`production/process_loss.py` 加** `production_plan_planned_qty(doc, method=None)`，在 `hooks.py` 的 Production Plan `validate` 里**排在** `bom_selection.production_plan_validate` **之后**（列表）：

```python
for row in doc.po_items:
    if not row.sales_order_item or not row.bom_no: continue      # 范围：只管从订单带出的（需求 LG-006）
    demand = 订单待生产量(row)       # HT-005：同 production_plan.py:397-399，SO 行 stock_qty − max(work_order_qty, delivered×cf, 0)
                                     # combine_items 时 row 对应多行 SO：按 prod_plan_references 求和（读码确认后定）
    recommended = required_input_qty(row.bom_no, demand)
    changed = (flt(row.cn_demand_qty) != demand) or (row.cn_recommended_bom != row.bom_no) or not row.cn_recommended_qty
    if changed or flt(row.planned_qty) == flt(row.cn_recommended_qty):
        row.planned_qty = recommended
    row.cn_demand_qty, row.cn_recommended_qty, row.cn_recommended_bom = demand, recommended, row.bom_no
doc.calculate_total_planned_qty()     # 原生已在 :139 算过，改了要重算
```

   注意 `row.cn_recommended_qty` 为空（首次）也按「变了」处理。`planned_qty` 被原生用于 `pending_qty`（`:185-192`），不另处理。
3. **前端** `public/js/production_plan.js`（`doctype_js`）：`po_items` 行 `planned_qty ≠ cn_recommended_qty` 时，在行的 `planned_qty` 字段描述显示「推荐 {0}」（`frm.fields_dict.po_items.grid` 逐行 `set_field_property` 或 `refresh` 时用 `frappe.meta.get_docfield(...).description`，执行者选）。
4. **超产替换**，新文件 `production/overproduction.py`（A15）：

```python
UPSTREAM_SHA256: Final = "dd34f0798ed5604f5ac1c1038ad6b6c18d643eebaceadbb6f93e49851959b6a6"   # 执行时复核
_original = None

def validate_work_order_against_so(self):
    """照原生 work_order.py:645-682 逐行抄写，唯一改动：
    allowance 上限 = required_input_qty(self.bom_no, so_qty) × (1 + 原生比例/100)；
    self.bom_no 为空或无 BOM 时回落原生 so_qty。其余（总量算法、打包明细、错误类型与消息）不变。"""

def ensure_patched() -> None:
    """幂等：WorkOrder.validate_work_order_against_so 不是本函数时，记下原函数并替换。"""

def before_validate_work_order(doc, method=None) -> None:
    ensure_patched()
```

   `hooks.py`：`before_request`、`before_job` 列表追加 `overproduction.ensure_patched`；Work Order `before_validate` 加 `before_validate_work_order`。README「后端覆盖登记」加一行（格式同拆单行：覆盖文件、作用、依赖上游 `work_order.py:645-682` 函数体与 `:586` 调用点、锁定 commit、失效症状「5264 支工单提交报 OverProductionError」、复验 `test_overproduction`）。**ADR-0004** 文末修订记录加一行「2026-10-xx P1-S8：`WorkOrder.validate_work_order_against_so` 运行时替换（非 `override_doctype_class`），见 frappe_china README 后端覆盖登记」，状态行不改。
5. **按订单补货**（`replenishment/rules.py:198`）：`"planned_qty": pending` 改为 `required_input_qty(choice["bom"], pending)`（放在 `:193` 选完 BOM 之后）；`:209` 来源子表仍记 `pending`（未交数量的语义不变）。
6. **译名**：三个字段标签、「推荐 {0}」进 csv。

### 验证方式

`tests/test_process_loss.py`（续）：SL-003 ②③⑤（服务端：带出→保存→改值→保存→换 BOM→保存，逐步断言）；`tests/test_overproduction.py`：SL-003 ④ 三例＋哈希守卫＋「`run-tests` 进程中未经 `before_request` 也生效」一例；`tests/test_replenishment_rules.py` 按订单用例期望值按新口径改（回执列出），新增 SL-003 ⑥。⑤ 的前端提示在测试站截一张图。

---

## 任务 TS-005：税模板沿用与改名（对应切片 SL-004）

### 目标

从报价单来的订单不换税模板；税种名看得懂（需求 §4.8）。

### 具体改动

1. **服务端修根**（子 Agent 读码：CRM 前端 `erpnext_sales_order_customer.js:2-15` 在订单 `refresh` 时 `set_value('customer')`，触发 `sales_common.js:168-172` → `get_party_details` 按客户重取税模板；新客户无税种落兜底）：新文件 `accounting/customer_tax.py`：

```python
def customer_tax_category_from_quotation(doc, method=None) -> None:
    """Customer before_insert。doc.crm_deal 有值且 doc.tax_category 为空时：
    取 crm_deal 下最近一张未取消报价单（Quotation.crm_deal）的 tax_category；
    报价单无 tax_category 而有 taxes_and_charges 时，取该模板的 tax_category。都无则不动。"""
```

   `hooks.py` `doc_events["Customer"] = {"before_insert": …}`。客户有了税种后，前端重取得到同一模板（HT-022），订单不再被换。**不改前端、不改兜底规则**。
2. **改名**：`cn_tax/data/tax_setup.json` 九个税种、十二个模板 `title`、十三条规则里的引用，按需求 §4.8 表与偏离 4 改为新名（新名清单 D 步按 json 实际条目列成映射表放补丁里，先在回执贴出映射全表）。新名含空格与 `%`，D 步先在测试站建一个 `13% 专票 含税价` 的 `Tax Category` 确认命名不被拒。
3. **改名补丁** `patches/s8_rename_tax_categories.py`（`[post_model_sync]`）：`OLD_TO_NEW: Final = {...}`；对每家中式公司：`Tax Category` 用 `frappe.rename_doc("Tax Category", old, new, force=True)`（链接字段随改）；税模板（`Sales Taxes and Charges Template`／`Purchase Taxes and Charges Template`）改 `title` 并 `rename_doc` 到 `{新 title} - {缩写}`；补丁前后各记一次 `(模板, 税率, 科目, included_in_print_rate)` 与规则条数，不等即 `log_error`。新名已存在、旧名不存在即跳过（幂等）。
4. **测试旧名**：偏离 3 的 32 行全部换新名；`tests/utils.py:14-22` 若是常量表，改常量即可。

### 验证方式

`tests/test_customer_tax.py`：SL-004 ①（调 `erpnext.crm.frappe_crm_api.create_customer`，HT-013；再 `make_sales_order`＋`get_party_details`）；`tests/test_taxes.py` 加 SL-004 ②；③ 贴 grep 输出与全量结果。

---

## 任务 TS-006：工时口径与 BOM 工序表列（对应切片 SL-005）

### 目标

工单工序时间按 BOM 数量折算；拆单后每张卡按本卡数量排程（需求 §4.10）。

### 具体改动

1. **OB-048**，新文件 `production/operation_time.py`：

```python
def work_order_operation_time(doc, method=None) -> None:
    """Work Order before_validate（A16）。docstatus==0 且 bom_no 有值时：
    bom_qty = BOM.quantity；bom_ops = 该 BOM 的 BOM Operation 按 idx（name → time_in_mins, fixed_time）。
    对 operations 中 row.bom == doc.bom_no 且 not row.fixed_time 的行，按 (bom, operation, 同 operation 第 k 次出现) 对到 BOM Operation：
        row.time_in_mins = flt(bom_op.time_in_mins) * flt(doc.qty) / flt(bom_qty)
    对不上的行不动并 frappe.log_error 一条。改了任一行时调 doc.calculate_operating_cost()。"""
```

   对应规则与 `job_card_split._bom_operation_split_qty`（`job_card_split.py:50-62`）一致，可抽成共用函数。`hooks.py` Work Order `before_validate` 列表（与 TS-004 的 `before_validate_work_order` 并列，顺序：先 `ensure_patched` 再本函数）。
2. **OB-050**，同文件：

```python
def job_card_scheduled_time(doc, method=None) -> None:
    """Job Card before_insert（A17）。无 scheduled_time_logs、或 work_order 为空 → 返回。
    wo_qty = Work Order.qty；op_time = Work Order Operation(doc.operation_id).time_in_mins。
    want = op_time / wo_qty * doc.for_quantity；排程行合计 ≤ want + 1e-6 → 返回。
    从首行起累加，到 want 为止：截短最后一行（to_time = from_time + 剩余分钟、time_in_mins 同步），删去其后的行。
    doc.time_required = want。"""
```

   `prepare_data_for_job_card`（`work_order.py:1243-1245`）在 `create_job_card` 返回后读 `job_card_doc.scheduled_time_logs[-1]`，是同一对象，截短后的止时即传给下一张卡（HT-007）。
3. **OB-025**：Property Setter fixtures（`hooks.py` fixtures 加 `{"dt": "Property Setter", "filters": [["name", "in", [...]]]}`，新建 `fixtures/property_setter.json`）：`BOM Operation` 的 `operation`、`workstation`、`time_in_mins` 三字段 `in_list_view=1`、`columns` 合计不超过 10（工序损耗率由 TS-003 的 Custom Field 自带 `in_list_view`）。Routing 用的是同一子表 `BOM Operation`，一处生效。D 步先看现状哪几列已是 `in_list_view`，只补缺的。

### 验证方式

`tests/test_operation_time.py`：SL-005 ①（三路径）②③（开产能计划的用例在 `setUp` 存原值、`tearDown` 还原）⑤；④ 调 `capacity_load.execute`；`tests/test_capacity_load.py` 既有期望值若因口径改变而变，按新口径改并列出；⑥ 截图。

---

## 任务 TS-007：换 BOM 人确认与来源记录（对应切片 SL-006）

### 目标

界面上有更便宜的 BOM 时由人点头；工单评论如实记来源（需求 §4.11.1，A13）。

### 具体改动

1. **Custom Field**：`Production Plan Item-cn_bom_source`、`Work Order-cn_bom_source`（Select，选项 `\nconfirmed\nkept\nmanual`，只读，`hidden: 1`）。
2. **服务端**（`production/bom_selection.py`）：
   - `production_plan_validate`：行 `cn_bom_source` 有值 → `continue`（不改）；为空 → 照现逻辑。
   - `work_order_before_insert`：先判来源，记到 `doc.flags.cn_bom_choice["source"]`：
     - `doc.production_plan` 有值 → `"plan"`，**不改 BOM**；
     - `doc.cn_bom_source == "confirmed"` → `"confirmed"`；`"kept"` → `"kept"`；
     - `bom_no` 非默认且非空 → `"manual"`（现「人工指定」分支）；
     - 其余 → 照现逻辑自动选，`"auto"`。
   - `_format_choice`：按 source 写五种措辞：「由生产计划带入」「按成本推荐、人已确认」「按成本推荐、人选择保留」「人工指定」「按成本自动选用」；候选表照旧。旧的 `Applied automatically`／`Manually specified` 两个源词不再用（csv 留着无害，`translation_check` 若报未用键按其规则处理）。
3. **前端**：`public/js/production_plan.js`（TS-004 已建）与 `public/js/work_order.js`（已有）各加 `before_save`：

```js
async before_save(frm) {
    // 生产计划：逐行；工单：单个。只看 cn_bom_source 为空、物料勾了自动选 BOM 的
    const rec = await frappe.xcall("frappe_china.production.bom_selection.recommend_bom", {item_code, company});
    if (!rec.auto || !rec.bom || rec.bom === row.bom_no) return;
    const choice = await 弹框(候选表, 按钮 "换用推荐" / "保留当前");   // 返回 Promise
    if (choice === "use") { row.bom_no = rec.bom; row.cn_bom_source = "confirmed"; } else { row.cn_bom_source = "kept"; }
}
```

   HT-006：`before_save` 返回 Promise 时保存会等它。D 步先在测试站表单上试一次；不成立按 HT-006「不成立时」改挂点。弹框按钮文字与标题进 csv。
4. **S7 测试**：`test_bom_selection_hooks` 中「生产计划建工单评论为『手动指定』」等断言改为新措辞；`production_plan_validate` 静默替换的用例保留（`cn_bom_source` 为空时仍自动），另加有值不改的用例。

### 验证方式

`tests/test_bom_selection_hooks.py`：SL-006 ②（五类来源各一）③④；SL-006 ① 测试站浏览器两张截图（`Spike/P1S8R6-D/` 下，探针脚本先断言站点名）。

---

## 任务 TS-008：补货口径与结果呈现（对应切片 SL-007）

### 目标

安全库存与再订货点同一套需求序列、原料按生产消耗计；计算结果看得懂（需求 §4.11.2）。

### 具体改动

1. **`replenishment/demand.py`**（A11）：
   - `DEMAND_STOCK_ENTRY_PURPOSES` 加 `"Material Transfer for Manufacture"`。
   - 新函数 `wip_warehouses(company: str | None) -> set[str]`：`Manufacturing Settings.default_wip_warehouse` ∪ `Work Order.wip_warehouse`（`docstatus=1`、该公司，distinct）；结果按请求缓存（`frappe.local` 上的 dict）。
   - `daily_demand(item_codes, warehouses, as_of, company=None)`：SQL 的 Stock Entry 分支追加 `AND sle.warehouse NOT IN (在制品仓集合)`（集合为空时不加）；发货单、销售发票分支不加。`warehouses` 参数语义不变。调用方全部改传 `company`。
2. **`replenishment/safety_stock.py`**（A12）：每个物料的仓库范围 ＝ 该物料 `Item Reorder` 行经 `warehouses_of_row` 展开的并集（只取该公司的仓）；无行时 ＝ 该公司全部叶子仓 − 在制品仓集合。不再一次性取全公司（`:49-50` 改为逐物料，物料少，可接受；或按范围分组批量查，执行者选）。跨公司检查（`other_demand`）保持。
3. **`changes` 明细**（总纲 §5.2）：三步在写值处 append `ChangeRow`；`suggestions` 步对已勾规则而未出建议的物料×仓库也 append 一行 `outcome="not_triggered"`、`reason` 写触发条件与实际值（EOQ：计划量与再订货点；覆盖 N 天：非盘点日／目标量 ≤ 计划量；按订单：无净缺料）。`skipped` 计数照旧。
4. **弹窗**（`public/js/replenishment_suggestion_list.js:55-79` `show_replenishment_result`）：每公司一张表：物料（`frappe.utils.get_form_link("Item", code, true)`）／仓库／项目（安全库存、再订货点、建议量）／旧值／新值／结果／原因；问题清单照旧列在表下。`changes` 为空时写「无变化」。
5. **列表与子表**：`replenishment_suggestion.json` 的 `item_code` 设 `in_list_view: 1`、排在 `item_name` 之前；`replenishment_basis_item.json` 的依据项、数值、说明三字段，`replenishment_source_order.json` 的订单、物料、未交数量三字段设 `in_list_view: 1`；三个 json 调大 `modified`。依据项 23 个选项（`Projected Qty`…`Net Shortage`）逐个查 `zh.csv`，缺的补（已有如 `Net Shortage,净短缺`）；与官方词典撞键且官方译文不合用的，按 S7 A16 换源词不覆盖——依据项是 Select 存值，换源词要改存值与 `rules.py` 写入处，D 步先列出撞键的几个再定。

### 验证方式

`tests/test_replenishment_stock.py`／`test_replenishment_levels.py`：SL-007 ①～④（手算值写死）；`test_replenishment_daily.py`：⑤ 的 `changes` 结构与三类 outcome；⑥ 截图三张；⑦ 既有期望值变更逐条列入回执。

---

## 任务 TS-009：演示画面译名与显示（对应切片 SL-008）

### 目标

演示九幕画面上的英文、错译、空表与精度问题（需求 §4.13 A 类中归 TS-008 的十项）。

### 具体改动

| 项 | 改法 |
|---|---|
| OB-024 计件单价精度 | `custom_field.json` 的 `Operation-cn_piece_rate`、`BOM Operation-cn_piece_rate` 加 `"precision": "4"`，调大 `modified`（HT-010）；`piece_rate.py` 计算处若有 `flt(x, 2)` 一并改按字段精度 |
| OB-029 CRM 状态中文 | 两个状态 DocType 有 `translated_doctype: 1`，`/crm` 渲染时 `__(name)`（`crm/frontend/src/stores/statuses.js:98-101`）：**加译不改名**（`crm/api/form.py:158`、`crm_deal.py:115` 硬编码 `Qualification`）。`zh.csv` 补 14 个状态键：线索 New／Contacted／Nurture／Qualified／Converted／Unqualified／Junk，商机 Qualification／Demo/Making／Proposal/Quotation／Negotiation／Ready to Close／Won／Lost。官方已有译文的（`New` 新建、`Qualified` 已认证、`Converted` 已转化、`Unqualified` 未认证、`Qualification` 资质、`Won` 赢单、`Lost` 未成交，读 zh.po 核过）与 CRM 场景不合用的（如 `Qualification` 资质、`Qualified` 已认证），用 context 键（`Qualification,需求确认,CRM Deal Status`）——D 步先核 CRM 前端 `__()` 调用是否带 context；不带则只能覆盖无 context 键，须登记 `translation_overrides.py` 并逐条写依据（DEC-020 OB 分流 A 类），撞名影响面在回执列出。拟定译名：新线索／已联系／培育中／合格／已转化／不合格／无效；需求确认／方案演示／报价／谈判／待成交／赢单／未成交 |
| OB-039 提交成功提示 | HT-008：`hooks.py` `extend_bootinfo = "frappe_china.boot.translate_success_actions"`——对 `bootinfo.success_action` 每条，`message`／`first_success_message` 若等于 `"{0} has been submitted successfully".format(ref_doctype)` 的英文形，则改为 `_("{0} has been submitted successfully").format(_(ref_doctype))`（官方 zh.po 有该键：「已成功提交{0}」）。只在 `frappe.local.lang == "zh"` 时改；用户自改过的 message 不动。不成立按 HT-008 改前端 |
| OB-042 对账报表无差异 | `desk_patches.js` 加一段：包装 `frappe.views.QueryReport.prototype.get_no_result_message`，`this.report_name === "Stock and Account Value Comparison"` 且报表已执行过（`this.data` 是数组）时返回含「无差异」的同形 HTML（源词 `No difference between stock and account values`，进 csv），否则委托原方法；标记 `__frappe_china_no_diff`；README Desk 前端覆盖登记加一行（依赖 `query_report.js:105-112`、`:2374-2380`）；Node 测试加一例 |
| OB-059 质检类型 | `zh.csv` 加 context 键：`Incoming,来料检验,Quality Inspection`、`Outgoing,出货检验,Quality Inspection`、`In Process,过程检验,Quality Inspection`。Select 控件按 `__(v, null, doctype)` 取（`select.js:172-175`），列表与表单的 Select formatter 已由本 app 带 context（README S6 SL-006）。CRM 通话的 `Incoming`／`Outgoing` 无 context，不受影响 |
| OB-068 SPC 列名 | HT-009：csv 已有这些键。D 步先以中文会话在测试站跑报表复现；常见原因是报表 json 的 `columns` 或 prepared report 缓存、或 `execute` 在 `_()` 前就构造了常量。按定位结果修，回执写原因。「样本不足」醒目化放演示后（需求 §4.13） |
| OB-069 计件弹窗 | `piece_rate_summary_list.js:10-11`：改为三段 `<h5>已创建</h5><ul>…</ul>`／已跳过／问题，各段空时写「无」；段名源词 `Created`／`Skipped`／`Problems` 查官方词典后定（已有合用译文则不进 csv） |
| OB-070 员工姓名列 | `piece_rate_summary.json` 的 `employee_name` 设 `in_list_view: 1`，调大 `modified` |
| OB-071 单价来源中文 | `piece_rate_summary_item.json` 的 `rate_source` 选项 `BOM Operation`／`Operation` 缺中文：选项是存值，不改存值，加 context 键 `BOM Operation,BOM 工序,Piece Rate Summary Item`、`Operation,工序主数据,Piece Rate Summary Item`；`piece_rate.py:38-55` 跳过 `completed_qty == 0` 的时间行 |
| `PH-P1097` 首桶标签 | `capacity_load.py:_buckets`（`:9-22`）：`result.append((str(key), …))` 的 key 改为 `max(key, start)`——即首桶取实际起算日，其余桶 `start` 本就等于 `key`。图表 `labels` 随之 |

### 验证方式

`tests/test_s8_labels.py`：SL-008 ①⑤⑦⑨⑩ 与 ③ 的 `extend_bootinfo` 函数级测试；`test_capacity_load.py` 加 ⑩；Node 测试加 ④；②③④⑥⑧ 测试站截图（`Spike/P1S8R6-D/`）；切片结束跑译名三件套。

---

## 任务 TS-010：策略对比报表（对应切片 SL-009 ①～④）

### 目标

第 8 幕一屏看清三段补货策略的效果，指标全按真实单据算（需求 §4.14，DEC-035，A20）。

### 具体改动

新 Script Report `Replenishment Strategy Comparison`（`stock_plus/report/replenishment_strategy_comparison/`，`ref_doctype: Stock Ledger Entry`，角色 Stock Manager／Stock User／System Manager）。

**筛选**：`company`（必填）、`items`（MultiSelectList Item，空 → 勾了 `cn_rule_eoq`／`cn_rule_periodic`／`cn_rule_order` 任一的物料）、`period_1_from`／`period_1_to`、`period_2_from`／`period_2_to`、`period_3_from`／`period_3_to`（前两段必填）。

```python
def execute(filters):
    periods = _periods(filters)          # 2～3 段；起 ≤ 止；段间不重叠；否则 frappe.throw
    items = _items(filters)
    order_cost, holding_rate = Company.cn_order_cost, Company.cn_holding_rate   # 缺任一 → 消息里注明、总成本列为空
    rows = [_period_row(p, items, company, order_cost, holding_rate) for p in periods]
    return columns, rows, None, chart(总成本柱)

def _period_row(p, items, company, order_cost, holding_rate):
    days = (p.to - p.from).days + 1
    avg_value = mean(每日库存金额(d) for d in p)   # 见下
    po_count = Purchase Order 张数：docstatus=1、company、transaction_date ∈ p、子表含 items 中任一
    total = po_count * order_cost + avg_value * holding_rate/100 * days/365
    shortage = _shortage_count(p, items, company)
    return {period, from, to, days, avg_value, po_count, total, shortage}
```

- **每日库存金额**：对 items × 该公司仓库，取每个 (物料, 仓库) 在 `p.from` 前最后一条 SLE 的 `stock_value` 作起点，再按日期顺序把段内 SLE 的 `stock_value` 逐日推进（一次 SQL 取段内全部 SLE＋起点，Python 逐日累计），不逐日查库。`is_cancelled=0`。
- **缺料次数**（DEC-035、偏离 8）：段内 `planned_start_date` 落在 p 的已提交工单中，满足 ① `actual_start_date` 为空或 `date(actual_start_date) > date(planned_start_date)`，且 ② `required_items` 中属 items 的某原料，在其 `source_warehouse` 于 `planned_start_date` 当日（含）末的结存 `qty_after_transaction` < 该行 `required_qty`。`actual_start_date` 由首张工序卡提交时写入，取最早的报工起时（子 Agent 读 `job_card.py:1076-1086`、`work_order.py:1597-1601`）。
- **列**（中文进 csv）：时间段、起、止、天数、平均库存金额、采购次数、库存相关总成本、缺料次数。
- **图表**：`{"type": "bar", "data": {"labels": [时间段], "datasets": [{"name": 库存相关总成本, "values": [...]}]}}`。

### 验证方式

`tests/test_strategy_comparison.py`：SL-009 ①②③（小数据手算值写死，含 10 天 × 持有成本率的折算）；④ 截图。报表跑满 15 秒会被上游改为 Prepared Report（开发守则「探针三条纪律」第 3 条）：测试数据小不会触发；s8dev 一年数据上跑一次计时，记 D 回执。

---

## 任务 TS-011：业务流程侧栏入口（对应切片 SL-009 ⑤⑥）

### 目标

演示链路用到的页面都能从业务流程侧栏进入；第 1 幕报价单落在业务流程侧栏（需求 §4.12、OB-009／067／031、偏离 14）。

### 具体改动

1. `workspace_sidebar/business_flow.json`（现 7 节 51 个入口，子 Agent 核过；无供应商评分）加 14 个入口，调大 `modified`：
   - 基础资料：Holiday List、Quality Inspection Parameter、Quality Inspection Template、Batch
   - 采购：Replenishment Suggestion、Supplier Scorecard
   - 生产：Piece Rate Summary、Capacity Load（Report）、SPC Control Chart（Report）、spc-chart（Page）、Replenishment Strategy Comparison（Report）
   - 人事（新节，或并入基础资料，执行者定）：Salary Structure、Salary Structure Assignment
   - 设置（并入基础资料）：Stock Settings、Manufacturing Settings
   - 其中 Report 型 `link_type: "Report"`、Page 型 `link_type: "Page"`。README「模块边界」的「7 个分节、51 个入口」随改。
2. **OB-031**：`frappe_debug` 的第 1 幕命名函数用 `/desk/quotation/new?quotation_to=CRM%20Deal&party_name={deal}&crm_deal={deal}&sidebar=Business%20Flow` 在同一标签页打开（Part3 TS-024）。本任务只验 HT-011：测试站浏览器打开 `/desk/quotation/new?sidebar=Business%20Flow`，看左侧栏。
3. `test_business_flow_navigation.py` 的入口数断言随改。

### 验证方式

SL-009 ⑤：`test_business_flow_navigation` 断言 14 个新入口存在且 `link_to` 可解析；测试站逐个点开（截图一张总览）。⑥：截图；HT-011 不成立按总纲该行处理。

---

## 任务 TS-012：演示站前置数据（对应切片 SL-010）

### 目标

性别、称呼、批号开关、管理员显示名四项前置（需求 TS-011、OB-005／016、DEC-024）。

### 具体改动

`docker/scripts/configure_apps.py` 加 `configure_demo_prerequisites(notes) -> dict`，在 `main` 里排在 `configure_stock` 之后：

```python
def configure_demo_prerequisites(notes):
    from frappe.desk.page.setup_wizard.install_fixtures import update_genders, update_salutations
    before = (count Gender, count Salutation)
    update_genders(); update_salutations()            # 原生带 ignore_if_duplicate（install_fixtures.py:26/41）
    changed = _apply(Stock Settings, {"enable_serial_and_batch_no_for_item": 1})
    changed |= _apply(User "Administrator", {"first_name": "演示管理员"})    # 只在当前为 "Administrator" 时改
    return {...}   # 与既有 configure_* 同形，用于「无改动」判断
```

`Gender`、`Salutation` 是 `translated_doctype`（读 json 核过），记录名保持英文、界面经译名显示；csv 已有则不补。`preflight` 无须新增检查（四项都是已知可写的）。**脚本只在测试站跑**，演示站在 TS-026 跑。

### 验证方式

测试站跑 `docker/configure-apps.sh --site test.localhost` 两次，贴两次输出（第二次「无改动」）；SL-010 ①～③ 查询结果与截图。`configure_apps` 既有测试（若有）补一例。切片结束跑 `frappe_china` 全量。
