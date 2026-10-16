# 确认报告（对象：P1-S7 通用计算的代码，`frappe_china` @ `61e94cf`）

**步骤**：P1-S7-R6 · `plannedDev` E 步（`confirm`）｜**日期**：2026-10-16｜**执行者**：Claude（Opus 5.5）｜**打tag**：否
**清单**：[R04 开发方案](../R04-开发方案/P1-S7-R4-C开发方案-总纲.md)总纲＋Part1～3 的 TS-001～017，判定基准为各切片验收条件 SL-001～012
**线索（不当结论）**：[D 回执 Part1](../R05-代码/P1-S7-R5-D回执-Part1.md)／[Part2](../R05-代码/P1-S7-R5-D回执-Part2.md)／[Part3](../R05-代码/P1-S7-R5-D回执-Part3.md)、[D 待验表](../R05-代码/P1-S7-R5-D待验表.md)、[D 讨论记录](../R05-代码/P1-S7-R5-D讨论记录.md)
**独立性**：D 步由 Codex 执行，TS-012 的补完由另一 Session 的 Claude 做；本步执行者没有参与 D。
**本步探针**：`Spike/P1S7R6-E/`，全部只写 `test.localhost`，并在事务里回滚；演示站只读。

## 逐项确认

「落地」看代码在不在，「生效」看是否真被调用、没被绕过，「根因」看原问题是否真的消失。✅ 通过，❌ 未通过，⚠️ 部分通过或证据不足。

| # | 清单项 | 落地否 | 生效否 | 根因消除否 | 验收标准 | 验证方式（本步实跑） | 结论 |
|---|---|---|---|---|---|---|---|
| 1 | TS-001 Ruff 基线清零 | ✅ | ✅ | ✅ | SL-001 ①②③ | 容器内 `ruff --version` 为 0.14.10，`pyproject.toml:20` 锁同版本；`ruff check` 输出 `All checks passed!`，`format --check` 160 文件通过；`git show --stat 39b2cec` 只含 63 个 `.py` 与 `pyproject.toml`；前后 283/283 沿用 D 日志（提交前的状态本步无法重现） | ✅ |
| 2 | TS-002 模块骨架与字段 | ✅ | ✅ | ✅ | SL-001 ④ | `modules.txt` 有两个模块；两个侧栏 json 的 `items` 为空；fixtures 共 27 条，含方案表全部字段与 MR 回指；演示站只读快照显示两个 Module Def 存在、侧栏 0 项 | ✅ |
| 3 | TS-003 覆盖自检与顺序比对 | ✅ | ✅ | ✅ | SL-002 ①～⑥ | ② `override_targets()` 读自身 hooks，共 4 条（含 CRM）；⑥ `check_business_order.py` 对原件退出 0，对调 hrms／crm 后退出 1 并打印两份顺序；③～⑤ 有单测；① 测试站实跑通过，只差通过时打印「通过」，见 IT-006 | ⚠️（IT-006） |
| 4 | TS-004 补货参数、`auto_indent`、提前期同步 | ✅ | ✅ | ✅ | SL-003 ①②③ | 读 `params.py`、`lead_time.py`；单测 3/3 在全量内；演示站只读 `auto_indent`＝0 | ✅ |
| 5 | TS-005 选 BOM 共用函数 | ✅ | ✅ | ✅ | SL-004 ①②⑦ | **单测全是桩**（`BomStub`）。本步造真 BOM 实跑（`it-bom-probe`）：三张 BOM 单位成本 9.183673／37.894737／70.000000，与手算一致；选中最低者；三张 BOM 的库内成本与 `modified` 不变；把原料估价调到 50 后改选 B2；无 BOM 的物料返回 `None` | ✅（测试薄，见复核建议） |
| 6 | TS-006 选 BOM 三处接入与评论 | ✅ | ✅ | ✅ | SL-004 ③～⑥ | 同一探针，原生默认设为最贵的 B1：表单式新建工单换成 B3，工序与原料行属 B3，有评论；人工指定 B2 不被覆盖，评论含「手动指定」；销售订单 `make_work_orders` 建出 B3；生产计划保存前行上 B1、保存后 B3，按它展开的原料属 B3，下达的工单为 B3；取消勾选后保持 B1、无评论。前端提示只有工单新建页截图（D 回执 `ts017-demo-work-order.png`），提示内容本步未核 | ✅ |
| 7 | TS-007 需求取样、安全库存、再订货点 | ✅ | ✅ | ❌ | SL-003 ④～⑧ | 见 IT-002、IT-003 | ❌ |
| 8 | TS-008 补货建议单与三种规则 | ✅ | ❌ | ❌ | SL-005 ①②⑤⑥⑦ | 见 IT-001、IT-004 | ❌ |
| 9 | TS-009 每日计算入口与采纳 | ✅ | ⚠️ | ⚠️ | SL-005 ③④⑧⑨⑩ | `it-adopt-probe` 真实记录：采纳生成已提交 MR，`transaction_date`＝计算日，有回指，状态改为「已采纳」，数量覆盖为 7；忽略不生成 MR；批量采纳两条，一条成功，另一条报「不是待定」，互不影响；Stock User 调 `run_now` 被拒，Stock Manager 通过。⑧ 的窗口端点见 IT-003；`run_daily` 真实出建议被 IT-001 挡住，⑧ 无法端到端判 | ⚠️（依赖 IT-001） |
| 10 | TS-010 批次系数 | ✅ | ✅ | ✅ | SL-006 ①～⑥ | 读 `batch_uom.py`，换算方向表与方案一致，精度 9；单测 3/3 用真实三类单据，含篡改修复；Node 1/1；⑤ 截图 `ts010-purchase-receipt-batch-factors.png` 存在 | ✅ |
| 11 | TS-011 拆单覆盖 | ✅ | ✅ | ✅ | SL-007 ①～⑤ | 读 `job_card_split.py`；上游函数（erpnext `work_order.py:2902-2915`）与登记一致；守卫哈希测试在全量内；真实工单提交与 `make_job_card` 两条路径各有测试；README「后端覆盖登记」一行 | ✅ |
| 12 | TS-012 工序间数量传递 | ✅ | ✅ | ✅ | SL-008 ①～⑥（⑤ 按 D 讨论第 7 步 A 改后的口径） | 读 `operation_flow.py`：`realign` 级联、`_is_started`、`_shift`、`_set_card_qty` 同时改时长、排程末行与原料量，与方案一致；方案外新增 `sync_operation_loss` 经用户裁决。定向 6/6 在全量内 | ✅（偏离已裁决） |
| 13 | TS-013 计件汇总单与 Additional Salary | ✅ | ✅ | ✅ | SL-009 ①～⑦ | 读 `piece_rate.py` 与 DocType；单测 4/4 用真实员工、薪资结构与 Job Card：1190 与手算一致、BOM 单价优先于 Operation、草稿不计、重复跳过、取消联动、无分配员工被隔离 | ✅ |
| 14 | TS-014 产能负荷报表 | ✅ | ✅ | ✅ | SL-010 ①～⑦ | 读报表代码；单测在真实工作中心、假日表与卡上算得 14／64／21.875%，未排期、无产能、零数量、完成与取消排除都有断言；Node formatter 1/1 | ✅ |
| 15 | TS-015 SPC 计算与报表 | ✅ | ✅ | ✅ | SL-011 ①～⑤ | 读 `spc.py`：d₂ 表、σ 组内取各组 R/d₂ 的均值、Nelson 8 条在 z 上判并标在窗口末点，与方案一致；单测含 16 个 Nelson 用例与真实检验单 | ✅ |
| 16 | TS-016 控制图页面 | ✅ | ✅ | ✅ | SL-011 ⑥ | vendor 文件与 Insights 包 sha256 均为 `bf4a2235…`；`.pre-commit-config.yaml` 已排除 vendor 目录；逐点着色用 CSS 变量；截图三张存在；Node 测试在全量内 | ✅ |
| 17 | TS-017 收尾、全量回归、演示站落地 | ✅ | ✅ | ⚠️ | SL-012 ①～⑤ | ① README 各节齐全；②④ 见下方回归与演示站快照；③ 演示站只读：`check_app_order` ok、`auto_indent`＝0、计件组件存在、侧栏空；⑤ 365 天回放有结果，但见 IT-005 | ⚠️ |

**需求 AC 覆盖**（总纲 §三末表）：AC-001～004、AC-006 落在 SL-005，受 IT-001 影响；AC-007～009 受 IT-002／IT-003 影响；其余 AC 所在切片已通过。

## 问题详情

### IT-001 EOQ 与定期复核规则写不进建议单（TS-008，SL-005 ①②⑤⑥）

- **现象**：只要触发 EOQ 或定期复核，`upsert` 就报 `Row #1: Basis cannot be "actual_qty". It should be one of "Projected Qty", …`。该物料进 `problems`，一条建议都不落库。`it-daily-probe` 走真实 `run_daily`，结果为 `suggestions processed 0 skipped 2`，两条报错。`it-basis-probe` 直接调 `upsert` 也得到同样结果。
- **定位**：`replenishment/rules.py:36-37` 的 `_basis()` 把 `parts` 的字典键（`actual_qty`、`reorder_level`、`average_daily_demand`……）原样写进 `basis` 字段；该字段是 Select，选项是 `Projected Qty`……`Net Shortage` 这些英文源词（`replenishment_basis_item.json`）。按订单规则手写 `"Net Shortage"`，不受影响。
- **为何测试全绿**：`test_replenishment_rules.py` 只断言 `qty` 与 `mr_type`，不碰 `basis`；`test_replenishment_suggestion.py` 和 `test_replenishment_daily.py` 把 `frappe.get_doc` 与 `upsert` 都 mock 掉了。365 天回放每天只出库 1 支，再订货点总低于计划量，两条规则从没触发过（结果 `ok: true`）。
- **与 D 回执不一致**：Part1 TS-008「三规则落地；4/4 规则测试、4/4 建议单测试通过」，Part1 复核建议也承认「建议单真实 DocType 集成覆盖仍偏薄」。
- **建议**：`_basis` 改为从字段键映射到 Select 选项，键和选项一一对应（如 `actual_qty`→`Actual Qty`、`eoq`→`EOQ`、`net_shortage`→`Net Shortage`）；`parts` 里没有对应选项的键（如 `projected_qty` 与 `Projected Qty` 已对上，`target_qty`→`Target Qty`）逐个核。补一条不 mock 的集成测试，走 `run_daily`，触发 EOQ 与定期复核各一条，断言建议单落库、触发依据各行可读。
- **建议档位**：`本Session修`（改动在一个函数，另补一条集成测试）
- **待裁决点**：—
- **状态**：待裁决 → 用户 2026-10-16 裁决「按建议来」：`本Session修` → **已修复**（见当场修清单）

### IT-002 计划量少扣三项预留，和原生 `projected_qty` 不一致（TS-007，SL-005 判触发与建议量）

- **现象**：`it-window-probe` 给 Bin 设 `reserved_qty_for_production`＝10。原生 `Bin.projected_qty`＝83，本 app 的 `projected_qty()` 得 93。
- **定位**：`replenishment/demand.py:175-199` 只算 实际＋已订＋已请购＋计划生产−已预留。原生 `bin.py:78-88` 还要减 `reserved_qty_for_production`、`reserved_qty_for_sub_contract`、`reserved_qty_for_production_plan`。需求 §4.2.3 写「计划量＝原生 `Bin.projected_qty`……原生口径不改」，方案 TS-007 签名也写「Σ Bin.projected_qty」。
- **影响**：工单一领料，原料的计划量就虚高。EOQ 可能该触发不触发，定期复核的建议量偏小。演示讲的正是「生产领料 → 该进料」这条链。
- **建议**：直接取 `Bin.projected_qty` 求和作为计划量；触发依据仍逐项列出，补上三项预留，让人能手算。测试加一例：有生产预留时与原生相等。
- **建议档位**：`本Session修`
- **待裁决点**：—（需求原文已定口径）
- **状态**：待裁决 → 用户 2026-10-16 裁决「按建议来」：`本Session修` → **已修复**（见当场修清单）

### IT-003 取样窗口少一天，D−89 那天的出库不计（TS-007，SL-003 ④⑥、SL-005 ⑧）

- **现象**：`it-window-probe` 在 D−90、D−89、D 各出库 1、2、4。返回 90 格，合计 4，首格为 0。D−89 的 2 支没算进去。
- **定位**：`demand.py:104-106` 取 `start = D − 89`，SQL 条件却是 `posting_date > start`（`:131`），实际只覆盖 89 天，而均值和标准差仍按 90 天算。方案 TS-007 docstring 写「从 D−89 到 D」共 90 个日需求。需求的记法 `(D−89, D]` 说「共 90 天」，两种读法只有含 D−89 才是 90 天。
- **影响**：σ 与 d̄ 系统性偏低（漏一天，分母还是 90）；与手算对不上。现有真实测试 `test_replenishment_stock` 只断言「D−90 不计入」，没断言「D−89 计入」，所以没拦住。
- **建议**：条件改为 `>=`（或 `start = D − 90` 配 `>`，二选一，与「90 天含 D」一致）；测试补「D−89 的出库计入」。
- **建议档位**：`本Session修`
- **待裁决点**：需求 `(D−89, D]` 的字面是左开区间，那只有 89 天，与「共 90 天」自相矛盾。本报告按「90 天、含 D−89」判；若用户认定是左开，则改的是需求与方案的「共 90 天」。用户「按建议来」即取本报告读法：90 天、含 D−89。
- **状态**：待裁决 → 用户 2026-10-16 裁决「按建议来」：`本Session修` → **已修复**（见当场修清单）

### IT-004 按订单规则不看物料的「按订单补货」勾选（TS-008，SL-005 ⑦）

- **现象**：`it-adopt-probe` 中，成品 BOM 含两种原料，只有一种勾了 `cn_rule_order`。按订单规则对两种都出了建议（`unflagged_present: true`）。
- **定位**：`replenishment/rules.py:148-229` 整个函数没有读 `cn_rule_order`；全 app 也只在 fixtures 里出现这个字段名。方案 TS-008 写明「只留物料勾了 cn_rule_order=1 的行」。
- **另核**：已提交 MR 覆盖的部分不重复建议，成立（MR 4 支后建议量从 10 降为 6）；按 `select_bom` 选中的 BOM 展开，由逐项确认第 6 行的生产计划实跑佐证。
- **建议**：在 `grouped` 汇总前按 `Item.cn_rule_order` 过滤；测试补一例：未勾选的原料不出建议。
- **建议档位**：`本Session修`
- **待裁决点**：—
- **状态**：待裁决 → 用户 2026-10-16 裁决「按建议来」：`本Session修` → **已修复**（见当场修清单）

### IT-005 365 天回放没覆盖出建议的路径（TS-017，SL-012 ⑤）

- **现象**：回放的造数（每天 1 支、两仓轮流出库、再订货点算出来远低于期初 10 支）让 EOQ 一次都不触发；定期复核按 30 天周期，库存始终高于目标量也不出。回放 `ok: true` 是「从没写过建议单」的结果，所以 IT-001 没有被它暴露。118.68s 的耗时只是「取样＋算参数」的耗时，不含建议单写入。
- **定位**：`Spike/P1S7R5-D/ts017-replay.py:33-37`（期初 10 支／仓、日出库 1 支）。
- **建议**：IT-001 修后重跑一次回放，造数调到能触发（如日出库 3～5 支、期初更低），记下建议单条数与耗时，写进 SB／修复回执。
- **建议档位**：`本Session修`（随 IT-001 修完后重跑即可，不改生产代码）
- **待裁决点**：—
- **状态**：待裁决 → 用户 2026-10-16 裁决「按建议来」：`本Session修` → **已修复**（见当场修清单）

### IT-006 migrate 自检通过时不打印「通过」（TS-003，SL-002 ①）

- **背景**：D 回执 Part1 的 TS-003 只写「verified」，没有命令与输出，也找不到对应日志。本步在测试站按方案实跑（`Spike/P1S7R6-E/sl002-migrate.sh`，输出 `sl002-migrate.log`，两份 migrate 日志 `frappe-bench/logs/s7-r6-e-sl002-{displaced,restored}.log`）。
- **实测**：把 `frappe_china` 挪到 crm 之前再 migrate：退出 0；输出逐条列出两条问题（装载顺序、撞源词译名）；Error Log 新增恰一条（标题 `frappe_china override self-check failed`）；`Administrator` 收到一条通知（另一个启用的 System Manager `crm.admin@example.com` 也收到）。用 `reorder_installed_apps` 归位后再 migrate：退出 0；Error Log 与通知都没新增；`check_app_order()["ok"]` 为真，装序已复原。告警、不中断、归位后不再告警这三层都成立。
- **未通过之处**：验收原文要求归位后「输出『通过』」；`install.py:152-153` 在 `ok` 为真时直接 `return`，什么都不打印。方案伪代码 `print(通过 或 逐条 problems)` 也要求两种情况都打印。
- **建议**：`after_migrate` 在通过时打印一行（如 `frappe_china override self-check passed`）。
- **建议档位**：`本Session修`
- **待裁决点**：—
- **状态**：待裁决 → 用户 2026-10-16 裁决「按建议来」：`本Session修` → **已修复**（见当场修清单）

## 全量回归 + 未执行项

**回归范围与结果**（本步自跑，2026-10-16）：

| 门 | 结果 | 对比 |
|---|---|---|
| Python 全量 `run-tests --app frappe_china` | **344/344**：336 integration（1760.058s）＋5＋3，均 OK，退出 0。日志 `frappe-bench/logs/s7-r6-e-python-full.log` | 与 D 回执 Part2 的 344 相同；比 TS-001 基线 283 只增不减 |
| Node `node --test frappe_china/tests/*.cjs` | **89/89**，0 fail、0 skip | 基线 86 → 89 |
| Ruff | `check` 全过；`format --check` 160 文件 | 基线 0 告警保持 |
| 演示站只读快照 | `check_app_order` ok、装序 7 个、科目 266、只有 `华东弹簧有限公司`；GL／SLE／客户／供应商／物料／各类发票凭证／工单／Job Card／MR／补货建议单／计件汇总单／`Translation` 均为 0；scheduler 关 | 与 S6 收口基线一致 |

全量全绿并不代表补货链路是对的：IT-001～004 都落在被 mock 或断言没覆盖的地方。

**未执行项确认**：方案标为「不做」「延迟」的（IM-014 整条 `SH-P1S7005`、批量「已过时」标注、发票类批次换算、scheduler 月结、子装配 BOM 选择、成品库存扣减），代码里都没有对应实现，未被意外改动。`sync_operation_loss` 是方案外新增，经 D 讨论第 7 步用户裁决，不算违规。

**译名**：本步只抽查了源词是否进 csv。`Ignore`、`Target Qty` 官方 erpnext 已有译文，不进 csv 符合 A16。`frappe_china override self-check failed` 既不在 csv 也不在官方词典，Error Log 标题与通知会显示英文——该串只给管理员看，不在演示屏单内，本步不另立未通过项，留给 F 步审核判。

## 当场修清单

文件位置在 `frappe-bench/apps/frappe_china/` 下。

| # | 对应未通过项 | 改动位置（文件:行） | 用户确认于 |
|---|---|---|---|
| 1 | IT-001 | `frappe_china/replenishment/rules.py:38-73` 新增 `BASIS_OPTIONS`，把字段键映射到 Select 选项；三项生产／委外预留共用 `Reserved Qty`，备注写原字段名。`:268` 按订单规则也走 `_basis` | 2026-10-16「按建议来」 |
| 2 | IT-002 | `frappe_china/replenishment/demand.py:18-27` 列出原生 8 个构成项；`:102-116` 计划量直接取 `Bin.projected_qty` 求和，构成项只作展示 | 同上 |
| 3 | IT-003 | `frappe_china/replenishment/demand.py:30-33`（docstring）、`:58` 条件改为 `>=`，窗口为 D−89～D 共 90 天 | 同上 |
| 4 | IT-004 | `frappe_china/replenishment/rules.py:238-247` 汇总前按 `Item.cn_rule_order=1` 过滤 | 同上 |
| 5 | IT-005 | 不改生产代码；回放改用能触发的造数重跑：`Spike/P1S7R6-E/it005-replay.py`，结果见下方「复核」 | 同上 |
| 6 | IT-006 | `frappe_china/install.py:9` 新增 `PASS_MESSAGE`，`:153-155` 通过时打印 | 同上 |
| 测试 | — | 新增 `frappe_china/tests/test_replenishment_integration.py`（4 条，不 mock：窗口两端、与原生计划量相等、`run_daily` 真写出 EOQ 与定期复核建议单且幂等、按订单只出勾选物料）；`test_after_migrate.py` 加通过打印一条；`test_replenishment_levels.py` 的计划量用例改为原生口径；`test_replenishment_rules.py` 的按订单用例改为断言按勾选过滤 | 同上 |

### 复核（本步当场）

拿暴露问题的原探针重跑，输出见 `Spike/P1S7R6-E/*-after.log`：

| 项 | 修前 | 修后 |
|---|---|---|
| IT-001 | `it-daily-probe`：`suggestions processed 0 skipped 2`，两条 `Basis cannot be "actual_qty"` | `processed 2`、`problems` 为空；落库两张：EOQ 64、定期复核 6（EOQ 手算 √(2×40.5556×20/0.4)＝63.68，Nos 取整 64）。`it-basis-probe` 写入成功，首行为 `Actual Qty` |
| IT-002 | 本 app 93、原生 83 | 两者都是 83 |
| IT-003 | 90 格，合计 4，首格 0 | 90 格，合计 6，首格 2（D−89 计入），D−90 不计 |
| IT-004 | 未勾选的原料也出建议 | 只剩勾选原料（10 支）；已提交 MR 覆盖后降到 6，与修前相同 |
| IT-005 | 365 天全程零建议 | 造数调为期初 40／仓、日出库 3 支、提前期 60 天、盘点周期 7 天：69 天出了建议，共写入或更新 1922 次，最后剩 60 张待定单（物料×仓库×规则去重）；`ok` 为真、无问题；总耗时 **176.47s**、单日最长 **2.55s**，低于 10s 阈值；回滚后物料、建议单、台账、公司设置都复原。结果 `Spike/P1S7R6-E/it005-replay-result.json` |
| IT-006 | 通过时不输出 | 打印 `frappe_china override self-check passed`（单测断言）。本步没有再跑一次完整 migrate 去看这一行：迁移一次 6～8 分钟，改动只有一行 `print` |

**定向测试**：新增集成 4/4；`test_replenishment_levels` 9/9、`_rules` 4/4、`_stock` 1/1、`_daily` 2/2、`_suggestion` 4/4、`test_after_migrate` 3/3。修 `_rules` 时，按订单用例先因新加的 `frappe.get_all` 撞上旧 mock 而报错，改为 mock `get_all` 并断言按勾选过滤后转绿。日志 `frappe-bench/logs/s7-r6-e-fix-targeted.log`。

**修后全量**：Python **349/349**：341 integration（1815.752s）＋5＋3，均 OK，退出 0（日志 `frappe-bench/logs/s7-r6-e-after-fix-full.log`），比修前 344 多 5 条新增、一条未少；Node 89/89；Ruff check 全过，format --check 161 文件通过。

## 总体结论

**全部通过**（修后）：IT-001～IT-006 经用户裁决为 `本Session修`，已当场修完并复核（见「当场修清单」）。修前存在这六个未通过项，这一事实保留在上文。其余 12 个任务（TS-001、002、004～006、010～016）逐项通过，其中 TS-005／006 是本步用真实 BOM 补的证据。

## 状态值

`全部通过`——首轮核出 IT-001～006 六个未通过项（修前状态为 `有未通过项`），用户裁决全部 `本Session修`，本步当场修完；修后复核与全量 349/349 均通过。

## 复核建议

1. **IT-001 是本报告代价最大的一条**：它让演示主线「系统知道何时进多少料」的两条规则在真实环境里一条建议都出不来。查法：`bench --site test.localhost execute "exec(open('/workspace/Spike/P1S7R6-E/it-daily-probe.py', encoding='utf-8').read(), globals())"`，看 `suggestions` 一步的 `problems`。
2. **与 D 回执声称不一致处**：TS-008（「三规则落地」，见 IT-001、IT-004）；TS-007（「90 天需求窗口」，见 IT-003；「计划量」见 IT-002）；TS-003（只写 verified，无证据；本步补跑后成立，只差打印「通过」，见 IT-006）；TS-005／006（「test.localhost 真实验收覆盖四条路径」，仓库里的测试全是桩，本步补跑后结论成立）。共同点是：断言只覆盖数量，mock 挡住了 DocType 校验与字段过滤。
3. **验收条件本身可疑**：SL-005 ⑧ 与需求 §4.2.3 的窗口记法 `(D−89, D]` 和「共 90 天」不能同时成立（IT-003 的待裁决点）。
4. **拿不准处**：IT-002 的判定依据是需求原文「原生 `Bin.projected_qty`」，方案签名里的构成项列举（`actual/ordered/indented/planned/reserved`）可能是执行者照抄后少了三项，也可能是 C 步有意简化；方案没写理由，本报告按需求判。

## 版本交付

用户 2026-10-16 指示「提交并推送」。app 修复提交 `acf97e629772eacce4ecf41394fbe083fab6b7e2`，已推送 `FrappeChina/main`；主仓库 `docker/apps.json` 的 `frappe_china` commit 同步更新，并与本报告、两份概况、`Spike/P1S7R6-E/` 探针一起提交。`Spike/P1S7R6-E/` 都是脚本、依赖当时站点状态的探针输出和回放结果，没有可重生成的产物，全部保留。
