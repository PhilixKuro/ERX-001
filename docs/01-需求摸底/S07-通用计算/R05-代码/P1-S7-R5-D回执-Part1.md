# P1-S7-R5 D回执·Part1

**日期**：2026-10-15｜**执行者**：Codex｜**打tag**：否
**依据**：[R04 开发方案总纲](../R04-开发方案/P1-S7-R4-C开发方案-总纲.md)及 [Part1](../R04-开发方案/P1-S7-R4-C开发方案-Part1.md)
**Spec**：`D-code-plannedDev-build.md`；回执按 `bricks/receipt.md`。

## 逐项执行结果

| 任务 | 对应切片 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-001 Ruff 基线清零 | SL-001 | app `pyproject.toml:20,41`、63 个 Python 文件（详见差异复核）、主仓库 `docker/scripts/setup.sh:377`、`docs/开发守则.md:237` | ✅完成 | 2026-10-15 | HT-001 go；Ruff 两门为 0；Python 改前／改后均 283/283，Node 均 86/86；用户许可后独立提交并推送 `39b2cec`，stat 范围已核 |
| TS-002 | SL-001 | modules.txt, module directories, empty workspace sidebars, custom_field fixtures, replenishment/types.py | DONE | 2026-10-15 | module definitions and sidebars verified on test.localhost; 22 custom fields synchronized; Ruff checks pass |
| TS-003 | SL-002 | install.py, hooks.py, test_after_migrate.py, check_business_order.py, setup.sh | DONE | 2026-10-15 | override coverage, order checks, migration failure reporting, targeted tests and order script verified |
| TS-004 补货参数与提前期同步 | SL-003 | `replenishment/params.py`, `replenishment/lead_time.py`, `hooks.py`, `docker/scripts/configure_apps.py`, `tests/test_replenishment_params.py` | DONE | 2026-10-15 | item values override company defaults; service level defaults to 95; existing Item Lead Time purchase_time sync preserves buffer_time; Stock Settings.auto_indent explicitly set to 0; Ruff and 3 targeted tests pass; first configure run changed 1 to 0, second reported no changes and DB value is 0 |
| TS-005/006 验证 | SL-004 | `bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_bom_selection`；Ruff 定向检查 | TS-005、TS-006 完成 | 2026-10-15 | 8/8 测试通过；Ruff check、format check、`node --check` 与 `git diff --check` 通过；test.localhost 真实验收覆盖 Work Order 自动切换、人工 BOM 保留、Production Plan 保存、Sales Order `make_work_orders` 四条路径 |
| TS-005 选 BOM 共用函数 | SL-004 | `production/bom_selection.py`、`tests/test_bom_selection.py` | ✅完成 | 2026-10-15 | 单位成本计算、原生默认 BOM 并列规则、损耗率≥100、数量为 0、无有效 BOM 均已覆盖；不写回 BOM 数据；8/8 定向测试通过；Ruff check/format 通过 |
| TS-006 选 BOM 三处接入 | SL-004 | `production/bom_selection.py`、`hooks.py`、`public/js/work_order.js`、`tests/test_bom_selection.py` | ✅完成 | 2026-10-15 | Work Order 新建自动选择并刷新工序/原料；人工 BOM 保留并写评论；Production Plan `validate` 仅替换原生默认 BOM；Sales Order `make_work_orders` 实测生成已选低成本 BOM；前端显示推荐提示；8/8 定向测试通过 |
| TS-007 需求取样、安全库存与再订货点 | SL-003 | `replenishment/demand.py`、`replenishment/safety_stock.py`、`replenishment/reorder_level.py`、`tests/test_replenishment_levels.py`、`tests/test_replenishment_stock.py` | ✅完成 | 2026-10-15 | 90 天需求窗口、白名单出库过滤、样本标准差、安全库存与现有 Item Reorder 行回写已落地；9/9 计算测试＋1/1 真实库存测试通过；真实事务覆盖窗口外出库、仓间调拨、D+1、组仓展开，实测再订货点 `1.834172917` 与 `1.856395139` 不相等 |
| TS-008 补货建议单与三规则 | SL-005 | `replenishment/rules.py`、`replenishment/suggestion.py`、`stock_plus/doctype/replenishment_{suggestion,basis_item,source_order}`、`fixtures/custom_field.json`、`tests/test_replenishment_rules.py`、`tests/test_replenishment_suggestion.py` | ✅完成 | 2026-10-15 | EOQ、定期复核、按销售订单三规则落地；参数缺失与逐项异常隔离；BOM 通过 `select_bom`，按 ERPNext 原生 `get_items_for_material_requests` 展开并按库存单位汇总；建议单按公司×物料×仓库×规则幂等更新 Pending，已采纳/忽略不复用；4/4 规则测试、4/4 建议单测试通过 |
| TS-009 每日计算与采购 | SL-005 | `replenishment/daily.py`、`stock_plus/doctype/replenishment_suggestion/replenishment_suggestion.py`、`public/js/replenishment_suggestion*.js`、`hooks.py`、`tests/test_replenishment_daily.py` | ✅完成 | 2026-10-15 | 固定顺序为安全库存→再订货点→三规则建议；未来日期拒绝、逐公司处理、错误进入 problems、核心入口不 commit；采纳有权限/状态检查、数量修改、Material Request 回指和 savepoint，批量动作按单条 savepoint 隔离失败；2/2 每日入口测试通过；建议单前端支持采纳、忽略、批量动作、立即计算与状态指示色 |

## 全量验证

| 门 | 改前基线 | 改后结果 |
|---|---|---|
| Python 全量 | 283/283：278 integration（1729.030s）＋5 old-frappe-test-class-category（0.255s），均 OK，退出 0 | 283/283：278 integration（1773.899s）＋5 old-frappe-test-class-category（0.254s），均 OK，退出 0 |
| Node 全量 | 86/86，无跳过 | 86/86，无跳过，退出 0（153.522681ms） |
| Ruff check | 2003 条：RUF001 741、RUF002 471、RUF003 740、I001 39、B905 4、E701 3、E702 3、RUF007 1、RUF059 1 | `All checks passed!`，退出 0 |
| Ruff format --check | 61 个文件待格式化、45 个已符合 | `106 files already formatted`，退出 0 |

**基线逐项对比**：两次 Python 日志中的用例名、数量和通过结果一致（278＋5）；两次 Node 日志均 86 pass、0 fail、0 skipped。日志在 `frappe-bench/logs/s7-r5-{python,node}-{before,after}.log`。全量翻译测试随 Python 套件通过，CSV 未改。

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-001 | `env/bin/ruff --version`；两条 ruff 命令输出；提交后 `git show --stat HEAD`；两次全量测试对比 | 容器内 pip 实装 0.14.10 后 `bench setup requirements --python`；app 内 `../../env/bin/ruff check frappe_china`、`../../env/bin/ruff format --check frappe_china`；bench 根目录两次 `bench --site test.localhost run-tests --app frappe_china`；app 内两次 `node --test frappe_china/tests/*.cjs`；独立提交后 `git show --stat HEAD` | 全通过；版本 0.14.10；Python 283→283、Node 86→86；两项 Ruff 检查退出 0；提交 `39b2cec` 仅 63 个 `.py` 与 `pyproject.toml`（2445 行增加、968 行删除） |
| TS-001 | `setup.sh` 安装版本读 `pyproject.toml` | `bash -n` 检查；从脚本摘出原样 6.1 段在当前 bench 运行 | 两项退出 0；输出 `Requirement already satisfied: ruff==0.14.10` 与 `ruff 0.14.10 已安装`；未运行完整 setup/up |
| TS-004 | parameter fallback, lead-time sync, and auto_indent | targeted test module plus two configure_apps.py runs on test.localhost; tabSingles query | DONE | 2026-10-15 | 3/3 tests pass; first run changed Stock Settings.auto_indent from 1 to 0, second reported no changes; DB value 0; lead-time sync test passes |
| TS-007～009 | 需求取样、补货规则、建议单与每日入口 | `bench --site test.localhost run-tests --app frappe_china --module frappe_china.tests.test_replenishment_levels --skip-before-tests`；同样方式运行 `test_replenishment_stock`、`test_replenishment_rules`、`test_replenishment_daily`、`test_replenishment_suggestion`；`frappe.db.exists` 检查 DocType 与 Custom Field；Ruff、`node --check`、`git diff --check` | 2026-10-15 | 9＋1＋4＋2＋4＝20 个定向测试全部通过；`Replenishment Suggestion` 与 `Material Request-cn_replenishment_suggestion` 已存在；相关 Ruff、JS 语法和差异检查通过 |

## 偏离与暂停

- 方案预设执行者 Claude，本轮由 Codex 执行；不改方案设计。
- TS-001 属纯格式与 lint 基线，按 atdd 唯一例外，以已有测试改前／改后回归核行为不变。
- 依赖验证在本轮容器内完成并填 D 待验表，没有另开 SA Session；未改动上游 app 源码或写演示站。
- `setup.sh` 的 pip 安装沿用已有 `GIT_PROXY`（显式 `PIP_PROXY` 优先），避免容器直连 PyPI 超时；只运行摘出的 6.1 工具安装段，未运行完整 setup/up。

## 差异复核

- app 改动为 63 个 `.py` 与 `pyproject.toml`，没有新增功能文件，译名 CSV、json 与 Node 用例未改。
- Ruff 自动修复 39 项 I001；三处 `zip` 显式传 `strict=False`（保留原行为）；相邻行检查改 `pairwise(rows)`；未使用变量 `rows` 改 `_rows`；E701/E702 由格式化器展开。
- 63 个变更 Python 文件与 HEAD 的 AST 对比：忽略 import 排序，并归一上述显式等价修正后，无其他差异；新增 import 仅 `itertools.pairwise`。一次性复核脚本与结果在 `frappe-bench/logs/s7-r5-review-ast.py`、`s7-r5-ast-review.json`，不进 app。
- app 与主仓库 `git diff --check` 均退出 0。
- 用户于 2026-10-15 明确指示「提交并推送」。app 独立提交 `39b2cec1a2d7ccd5ceb81cba24ffa1926a1ef97c`（`style: Ruff 0.14.10 baseline (PH-P1019)`）已推送 `origin/main`；提交后 stat 确认仅 64 个既定文件。主仓库 `docker/apps.json` 仅更新 `frappe_china` 的 commit，其余 app 锁不变；安装脚本、开发守则和本轮记录一并纳入本次主仓库提交。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| Ruff 作为 bench 开发依赖锁定于 app 的 `pyproject.toml`，setup 从该文件读取；工具链索引已改写 | 依赖 | TS-001（按既定方案落实，无额外约定） |

## 未做项

| 项 | 为什么没做 |
|---|---|
| tag | 本步打tag=否，未创建 |
| TS-007～009 | 已完成；TS-005、TS-006 已完成 |
| Part2／3 的 TS-010～017 | 不属本 Part；最新进度见 Part2 回执与 Stage 概况 |

## 状态值

D step ongoing; TS-001 committed and pushed; TS-002～009 completed; subsequent tasks are tracked in Part2 and the Stage overview; this Part1 functional work remains uncommitted pending D-step closeout.

## 复核建议

重点复核：`order_proposals` 复用 ERPNext 原生 `get_items_for_material_requests`，BOM 选择走 `select_bom`；采纳入口的权限、状态检查与 savepoint，以及取消后不回滚的 Material Request 约束；批量动作的单条失败隔离；建议单真实 DocType 集成覆盖仍偏薄，目前主要由 mock 控制器测试和规则/每日入口定向测试支撑。后续任务进度见 Part2；本轮功能改动尚未提交。

2026-10-16 Part2 全量回归发现并定向复现 TS-005 测试的语言断言错误：测试基类设中文，注释实际含「手动指定」，旧断言却要求英文 `Manually specified`。已仅修正测试期望；`test_bom_selection` 8/8 复验通过（日志 `frappe-bench/logs/s7-r5-part2-bom-selection-recheck.log`），生产行为未改。
