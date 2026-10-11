# P1-S6-R5-E 确认报告（对象：D 代码 Part1～Part4）

**日期**：2026-10-11｜**执行者**：Claude（Opus 5.5）｜**Spec**：`E-verify-plannedDev-confirm.md`＋`bricks/confirm.md`＋`play-confirm.md`，打tag=否
**清单**：R3 开发方案总纲＋Part1～4 的 TS-001～015 与 SL-001～010 验收条件；D 期间用户批准的方案补充 DEC-023～027 一并当清单。
**回归范围**：`bench --site test.localhost run-tests --app frappe_china` 全量＋宿主 Node 用例。

> **本报告取代此前同名文件**。前一版由 CodeX 在未经 E 步流程的情况下写成，状态值写为 `全部通过`（原文见主仓库提交 `b5d8eb8`）。本次按 Spec 重新独立核对，D 回执与旧报告只当线索：每条声称都对照代码、证据文件与截图核过，可跑的都实跑了。
> **核法**：四个 Part 各派一个只读子 Agent 逐条核（不改项目文件、不做 git 写操作、演示站只读）；全量回归与 Node 用例由主 Session 实跑。临时脚本与输出都在 `Spike/P1S6R5-E/{part1..part4}/`。另有一次越界须披露：Part1 子 Agent 为验 SL-002⑤，在测试站直接调了一次改名补丁函数 `execute()`。补丁在第一道幂等判断就返回了，前后 `tabDocType` 中 `Cash Flow Worksheet` 的 `modified` 不变，未写库。

## 逐项确认

| # | 清单项 | 落地否 | 生效否 | 根因消除否 | 验收标准 | 验证方式（本次实做） | 结论 |
|---:|---|---|---|---|---|---|---|
| 1 | TS-001 基线脚本 | 是 | 是 | 是（Part1 时点） | SL-001① | 原样跑报 `Unlocked commit for frappe_china: 35b5b77 != 1d51db2`。改用包装脚本跳过锁，并换回 Part1 时点的 csv 复算，得 5513／905／185／2，与回执一致。HEAD 上复算：缺口 23、撞名 1000 | ❌ IT-001 |
| 2 | TS-002 自检函数与 labels.py 收窄 | 是 | 是 | 是 | SL-001②④ | 两站只读跑 `translation_check.run`，都打印「译名自检通过」。读 `labels.py:33-38`，`try/except` 已删。读用例：db 为 None 时不取数，`DoesNotExistError` 照常抛。全量回归中这些用例都通过 | ✅ |
| 3 | TS-003 测试改造与覆盖清单 | 是 | 是 | 否 | SL-001③⑤⑥ | 四项反证用例齐全，且都断言清理干净。但「资产」用例判别力不足。HEAD 上覆盖清单被机械填满，守卫失效 | ❌ IT-002、IT-003 |
| 4 | TS-004 底稿改名与补丁 | 是 | 是 | 是 | SL-002①～⑤ | 只读查：旧表不存在，新表存在，`Patch Log` 有该补丁。自做 grep 剩 4 处命中，都可按语义排除。看了搜索截图。两个补丁用例都断言 `rename_doc` 未被调用 | ⚠ 主体通过；IT-004 |
| 5 | TS-005 S4 四处小缺陷与分隔符 | 是 | 是 | 是 | SL-003①～⑥ | 逐处读代码（`month_end_closing_voucher_list.js:48`、`unmapped.py:21/128`、`cash_flow_worksheet.py:285-288`、`closing.py:163-179/402`），csv 中两列 `"{0}; {1}"` 已不存在。看了前后对比截图。全量回归中对应用例都通过 | ✅ |
| 6 | TS-006 演示线档 | 部分 | 部分 | 否 | SL-004①～⑤⑦；csv 三段 | 实跑基线：演示面缺口 1，演示撞名 191 组，没有「同义保留」表，仍有异义同译。收付款方向全表未写进 csv。73 组占用表缺失。覆盖清单依据是乱码。csv 未分三段，`CSV_SECTIONS` 与 `test_csv_sections_sorted` 都不存在。缺 `Dr` 截图。Timesheet 全族逐条比对的用例正确 | ❌ IT-003、IT-006～IT-009、IT-011、IT-012 |
| 7 | TS-007 批量档与分层抽检 | 部分 | 是 | 否 | SL-005①～④；DEC-023 | 复跑抽样，结果与 D 逐字节相同（规则初筛 100/100）。**人工复判**同一批 100 条：繁体 22 条、逐词直译至少 6 条，超过 10 条的门槛。修复只改了样本内 59 条，样本外 0 条，没有回扫。csv 现有「中文：」占位 629 行、「???」67 行。缺口 23 条不在白名单内 | ❌ IT-005、IT-006、IT-015 |
| 8 | TS-008 裸渲染点 | 是 | 部分 | 部分 | SL-006①～⑤ | 代码与契约一致（幂等，只改 status 分支，On Hold 原样）。只有两张列表徽标截图。没有 states 与 Property Setter 两条原定做法的实测，没有筛选下拉和表单 status 截图，没有撤钩反证。README 三行栏目不符合 A6 | ❌ IT-013、IT-014 |
| 9 | TS-009 按钮抽检 | 部分 | — | 否 | SL-004⑥ | 抽检表 23 词，没有「现译」列。抽 5 词对照 erpnext 源码，动作描述与源码不符：`sales_invoice.js:378/402`、`purchase_invoice.js:155` 实为「从…获取物料」，`work_order.js:944`。`Payment` 在销售发票上方向错，却判了一致。定稿列有 7 词与现译不同，且没写进 csv | ❌ IT-010 |
| 10 | TS-010 业务流程图标与侧栏 | 是 | 是 | 是 | SL-007①～④⑥～⑧；DEC-024／025 | 侧栏 json 逐行对照方案表：58 行（7 节、51 项）全部一致。图标 json 与两种 svg 齐全。51/51 点击，`/undefined` 请求 0。Node 13/13 通过。④ 的改前快照拍在首次导入之后。⑦ 两次实验结果相反，回执没提失败那次。另有用 `set_value` 直接改演示站 `modified` 的操作，回执未披露 | ❌ IT-016、IT-017 |
| 11 | TS-011 树形点检 | 是 | 是 | 是 | SL-007⑤ | 两轮共 10 条全对，PNG 15 张，实看 4 张。`is_tree` 集合自做 grep，恰好五个 | ✅ |
| 12 | TS-012 开账跳转 | 是 | 是 | 是 | SL-008①～④ | 复刻逐字段对照 `stock_controller.js:114-134`、`journal_entry.js:79-96`、`payment_entry.js:423-441`，一致。4 张凭证的 `route_options` 与分录行数都核过。缺类时告警 1 条、不抛错。README 行号错 | ⚠ 通过；IT-019 |
| 13 | TS-013 不刷新六例 | 是 | — | — | SL-009①～⑤ | 六例结论齐全，例 2 按 LG-073 处理。例 1、5 复现前没验实时通道。例 3、4 复现步骤不能照着做 | ❌ IT-018 |
| 14 | TS-014 逐屏核与基准点 | 部分 | 部分 | 否 | SL-010①～⑥⑧；DEC-026／027 | ① 演示站只读实测：自检为空，装序 ok，科目 266。② 屏清单映射到需求 §4.9：表二三个前端在演示站零屏通过；表一缺多个交互屏；已填主数据 47 屏 pass=false 后未复跑，仍有中英混排和繁体。④ 方案指定的脚本和截图缺失（E 自做等价探针得 `{}`）。⑤ 回执无演示站 diff（E 用 S6 前的备份 `20261008_211805` 补比，结果为 0）。⑥ 数据清洁，但测试态备份放错目录，`restore.sh` 默认取带数据的那套。⑧ 反证与方案不等价。DEC-027 外另有未批准的 datatable 适配 | ❌ IT-020～IT-027 |
| 15 | TS-015 全量回归与常驻文件 | 部分 | — | 否 | SL-010⑦；TS-015 第 2～5 步 | 本次实跑 242/242 通过（见下节）。主仓库与七个 app 工作树 clean。README 主体已改写。开发守则缺四条约定。项目概况三处失真。HT-008／HT-014 没列出交 Stage 收口 | ❌ IT-028～IT-031 |

另：IT-032 记前一执行者在 E 期间未经裁决改测试文件，以及抢先回写概况。

## 问题详情

建议档位、待裁决点、状态三格按流程规范 §2.3；状态初始都为 `待裁决`。

### Part1

| 项 | 清单项 | 现象 | 定位 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|
| **IT-001** | TS-001／SL-001① | 基线脚本在 HEAD 上因提交锁不一致，直接拒跑。`P1S6R4-baseline.out.json` 被 Part2 重跑覆盖，Part1 时点的数字只剩在 git `4de6d93` 里 | `Spike/P1S6R4-baseline.py:248-249`；`docker/apps.json` 里 frappe_china 锁 `1d51db2`，实际 HEAD `35b5b77` | apps.json 锁更新到 S6 最终提交，Part1 时点输出另存一个固定名字 | `新Session修` | 改 apps.json 锁属版本控制文件，提交须用户许可 | 待新Session修 |
| **IT-002** | TS-003／SL-001③ | 「资产」反证只断言清单里有「资产」。第 1 项（Translation 记录）本身就会输出这个词，第 4 项（法定列头）失效时用例照样通过 | `frappe_china/tests/test_translation_check.py:86` | 断言改为 `any(p.startswith("法定列头被翻译：资产") for p in problems)` | `本Session修` | — | 已修复 |
| **IT-003** | TS-003／SL-001⑤、SL-004⑤ | HEAD 上覆盖清单 218 条，正好等于六 app 交集，「交集 ⊆ OVERRIDES」形同虚设。其中 207 条 `basis` 是乱码 `"S6 ????????????"`，不属于契约规定的四类依据；144 条 `ours` 本身就是「中文：…」「???…」这类坏译文。失败时也不按方案报出多出的键 | `frappe_china/tests/translation_overrides.py:22-228`；`test_translations.py:156`；来源提交 `35b5b77` | 随 IT-005 一并处理：坏行删掉或改译，留下的逐条写真实依据；断言改成报出差集 | `出方案修` | 与 IT-005 同一取舍 | 待详细修复方案 |
| **IT-004** | TS-004／SL-002① | 迁移过来的那条底稿没有经 `/desk/cash-flow-worksheet/<name>` 打开过。浏览器里打开的是另造的 UI 数据，迁移探针只经 `get_doc` 读过 | `Spike/P1S6R4-rename-probe.json`；D 回执 Part1 第 23 行 | 接受现有证据（探针 `get_doc`＋新名表单截图），或在测试站重造旧名状态后补打开 | `延迟或不修` | 接受现有证据，还是补跑 | 不做（接受现有证据／追认） |

### Part2

| 项 | 清单项 | 现象 | 定位 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|
| **IT-005** | TS-007／SL-005②；DEC-023 | **批量档译文大面积不可用**：<br>- 「中文：xx」占位 629 行，「???」67 行；<br>- 繁体约数百行（如「過帳」「項目」「帳戶」）；<br>- 逐词直译大量，如 `Are you sure you want to log out?` → `是 您 sure 您 want 至 日志 out?`。<br>抽检的 100/100 只是规则初筛，人工复判超过 10 条门槛。D 只修了样本内 59 条，没有回扫（DEC-023 要求回扫后重抽） | `frappe_china/translations/zh.csv`（如第 173、699、700 行）；`Spike/P1S6R4-repair-batch.py`；E 人工复判见 `Spike/P1S6R5-E/part2/review20.txt`、`samp_est.txt` | 先定重译路线，再整批处理。抽检规则补繁体、逐词直译、占位三类，并加人工复判。处理完重抽 | `出方案修` | ① 路线：整批重译 ／ 删坏行回落官方或 zh_TW 原译再补缺口 ／ 只保演示线、其余延迟（与 DEC-001 冲突）；② 繁体算不算判据 2 的「不可用」 | 待详细修复方案 |
| **IT-006** | TS-007／SL-005① | 六 app 缺口合计 23 条（frappe 4、erpnext 5、crm 2、hrms 4、raven 8），都不在 `UNTRANSLATED` 白名单内，也没写理由。白名单只作用于本 app 源词。演示面另有 1 条缺口：`Role Allowed to over bill `，源词带尾空格，csv 键没有，配不上 | `tests/test_translations.py:120`；`Spike/P1S6R5-E/part2/baseline.out.json` | 补译，或进白名单并写理由；白名单的作用范围要扩到基线脚本 | 并入 IT-005 | — | 待详细修复方案 |
| **IT-007** | TS-006／SL-004① | 演示撞名 191 组。D 回执没有「同义保留」表，组内仍有异义同译：`Stock Ledger`／`Stock Ledger Entry`→物料凭证（方案点名的已知一例）、`Is Paid`／`Paid`、`Payment Type`／`Type of Payment`、`Paid Amount`／`Payment Amount` 等 | D 回执 Part2；`baseline.out.json` 的 `demo_collisions` | 191 组逐组判同义还是异义；异义的定词，同义的进保留表 | 并入 IT-005 | — | 待详细修复方案 |
| **IT-008** | TS-006／SL-004② | S3 §1.1／§1.3 的收付款方向全表（约 20 行，如 `Paid Amount` 四个 context、`Received Amount`、`Mode of Payment` 等）没写进 csv。`test_named_terms` 没覆盖这些键，也没覆盖 `Settings`、无 context 的 `Unpaid`／`Paid` 和按钮定稿键 | `tests/test_named_terms.py:12-44` | 写进 csv，同时进 OVERRIDES 与测试 | 并入 IT-005 | — | 待详细修复方案 |
| **IT-009** | TS-006／SL-004④⑦ | S3 的 73 组改词没有占用重查表。`occupancy.py` 只读 csv、不读官方 po，与契约「合并字典」不符：`"Stock Ledger" "物料凭证"` 判可用，实际已被官方的 `Stock Ledger Entry` 占用 | `Spike/P1S6R4-occupancy.py` 的 `occupants()` | 先修脚本改读合并字典，再逐组重查出表 | 并入 IT-005 | — | 待详细修复方案 |
| **IT-010** | TS-009／SL-004⑥ | 按钮抽检表缺「现译」列，框架 5 词没有行号。至少 5 词的动作描述与源码不符。`Payment` 在销售发票上建的是收款，现译「付款」方向错，却判了一致；按方案应记「不可分、保留」。定稿列有 7 词与现译不同，且没写进 csv | `Spike/P1S6R4-buttons.csv`；erpnext `sales_invoice.js:98/378/402`、`purchase_invoice.js:155`、`work_order.js:944` | 按源码重写抽检表；定稿写 csv 并补测试 | `新Session修` | `Payment` 这类方向词的处置（改无 context 行会波及其它出处） | 待新Session修 |
| **IT-011** | TS-006／SL-004⑦ | 缺 `Dr` 落地后测试站称谓显示「借方」的截图；回执也没贴 occupancy 反例输出 | Spike 下无对应文件 | 测试站实跑补证 | `新Session修` | — | 待新Session修 |
| **IT-012** | TS-006 csv 分段 | csv 没按方案分三段有序（按源词排序有 442 处断点），`CSV_SECTIONS`、`test_csv_sections_sorted` 都不存在。D 回执 Part2 第 45 行自己记了「尚未重排、需补齐或记录偏离」，之后两样都没做 | `translations/zh.csv`；`tests/test_translations.py` | 重排脚本加段界常量与用例。也可经裁决改为偏离并记录 | 并入 IT-005 | 是否仍要求分三段 | 待详细修复方案 |
| **IT-013** | TS-008／SL-006①②④ | 缺 states 与 Property Setter 两条原定做法的实测。销售、采购两边的筛选下拉、表单只读 status 共 4 张截图缺失，`ts008-proof.png` 只是空列表页。撤钩反证缺失，回执第 97 行只是一句「建议」 | `Spike/P1S6R4-ts008-*` | 测试站造三张票，按方案逐项补跑 | `新Session修` | 撤钩后的预期值：方案写「未付款」，erpnext 官方无 context 译文实为「未付」，以哪个为准 | 待新Session修 |
| **IT-014** | TS-008／SL-006⑤ | README 那三行的栏目不是 A6 规定的五栏（文件:行／覆盖了什么／依赖的上游行为与锁定 commit／失效症状／复验法），缺上游依赖、失效症状和复验法 | app `README.md:54-60` | 补齐五栏 | `本Session修` | — | 已修复 |
| **IT-015** | TS-007／SL-005③ | `test_placeholders_preserved` 的 `_tokens` 先排序再比，HTML 标签顺序不在校验范围内，与「序列相同」不完全一致 | `tests/test_translations.py:200-201` | 占位符比多重集合，HTML 标签按序列比 | `本Session修` | — | 已修复 |

### Part3

| 项 | 清单项 | 现象 | 定位 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|
| **IT-016** | TS-010／SL-007④；DEC-025 | 方案第 1 步要的 `nav-before.json` 不存在。当作「改前」的 `nav-current-before.json` 拍在首次导入之后，里面已有 Business Flow。DEC-025 要求如实披露取证范围，回执没写 | `Spike/P1S6R4-nav-current-before.json` | 接受 E 补出的演示站证据：S6 前备份 `20261008_211805` 与当前三表 diff 为 0。在回执里披露取证范围 | `延迟或不修` | 是否接受 E 的替代证据 | 不做（接受现有证据／追认） |
| **IT-017** | TS-010／SL-007⑦ | 同一个「2099 调大 modified 后导入」：`migration-acceptance.json` 那次没导入，断言失败；`migration-future.json` 那次导入了，原因没解释。之后又用 `frappe.db.set_value` 直接改了测试站与**演示站**的 Business Flow `modified`，回执都没披露 | `Spike/P1S6R4-migration-{acceptance,future}.py`、`P1S6R4-set-nav-modified.py` | 测试站一次跑完「旧值改 label→不变；调大→变新；恢复」，恢复用当前时刻；回执补披露 | `新Session修` | — | 待新Session修 |
| **IT-018** | TS-013／SL-009①⑤ | 例 1、5 复现前没先验实时通道（方案要求每例先验）。例 3、4 缺数据准备顺序和调用方式（`part3-data.py` 几个动作的先后、6787 服务的启停），照着做不出来 | `Spike/P1S6R4-ts013-report.md` | 补命令序列；例 1、5 补实时通道回执后复跑 | `新Session修` | — | 待新Session修 |
| **IT-019** | TS-012 README | README 开账覆盖一行写 `desk_patches.js:9`，实际在 `:61-95`；也缺方案要求的「复刻原方法 114-134 行，上游改须同步」 | app `README.md` 的「S6 SL-008 开账跳转覆盖」节 | 改一行 | `本Session修` | — | 已修复 |

### Part4

| 项 | 清单项 | 现象 | 定位 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|
| **IT-020** | TS-014／SL-010② | **屏核未覆盖需求 §4.9**：<br>- 表二 `/crm`、`/raven`、`/insights` 在演示站零屏通过正式屏核；<br>- 表一缺新建仓库对话框、命名对话框、BOM 提交、经「创建」进的下游单据、任务单两个对话框、完工入库报错框、销售订单「关闭」、发票列表徽标、全部「取消」确认框等；<br>- 已填数据的供应商、客户、物料、员工 47 屏 pass=false，之后没复跑，仍有中英混排（`zh.csv:1861`、`:1918`）和繁体。<br>判据只查英文词，查不出「中文：」占位与繁体 | `Spike/P1S6R4-screens-forms-v10/result.json`、`screens-loop/result-masters.json`；屏清单映射见 `Spike/P1S6R5-E/part4/` 子 Agent 结论 | 先定屏清单口径与判据，补清单；IT-005 处理完后在演示站按 A14 备份、造数、逐屏核、恢复 | `出方案修` | ① 「表单屏」指空白新建还是已填单据；② 繁体、aria-label、ERPNext 自带英文默认数据算不算界面文案；③ 是否每个 DocType 都核「取消」确认框 | 待详细修复方案 |
| **IT-021** | TS-014／SL-010③；HT-008 | loop 各屏用 `frappe.set_route` 直接打开，没走「创建 → 下游单据」，HT-008 实际没测。home 屏 `sidebar_title=Stock` 没说明 | `Spike/P1S6R4-capture-state.cjs` | 改成点「创建」走下游，记录 sidebar_title | 并入 IT-020 | — | 待详细修复方案 |
| **IT-022** | TS-014／SL-010④ | 方案指定的 `Spike/P1S6R4-sidebar-dupes.py` 不存在；「应收」下拉与 `account_type` 选项两张截图也不存在。E 用等价只读探针在演示站实测：侧栏无重名，「应收账款」各只出现一次，现象本身不存在 | `Spike/P1S6R5-E/part4/probe_demo.py` | 按方案签名补脚本与两张截图 | `新Session修` | 能否以 E 的探针结果替代截图 | 待新Session修 |
| **IT-023** | TS-014／SL-010⑤ | D 没有演示站原有入口 diff 的证据（现有快照都取自测试站）。E 已补：S6 前备份 `20261008_211805` 与当前演示站三表共 834 行比对，name、modified、hidden、idx 差异 0 | `Spike/P1S6R5-E/part4/diff_backup_entries.json` | 接受 E 补证 | `延迟或不修` | 是否接受以 S6 前备份作「改前」口径 | 不做（接受现有证据／追认） |
| **IT-024** | TS-014／SL-010⑥ | **备份与默认恢复有误取风险**：<br>- 测试态备份 `20261011_002831`（带销售闭环数据）放进了 `保留-S6收尾/`，方案要求放 `保留-S6R4测试态/`；<br>- 它也是根目录最新的一套，而 `restore.sh` 不带参数时取最新（`docker/restore.sh:34`）；<br>- `docs/项目概况.md:81` 仍写「`20261008_211805` 是当前空账基准点，`restore.sh` 不带参数即取它」，照文档操作会恢复出带数据的站 | `docker/backups/`；`docs/项目概况.md:69-81` | 项目概况改为：最终基准点 `20261010_232619`，恢复须显式指定时间戳。测试态那套移到 `保留-S6R4测试态/` | 文档部分 `本Session修` | 移动备份文件须用户许可 | 已修复 |
| **IT-025** | TS-014／SL-010⑧ | 判别力反证只在 about:blank 上用合成 DOM 测了提取函数。方案要求的整条链没做：测试站加一条英文 label 的自有侧栏条目、不加 csv，跑 `screen-check.js` 报 pass=false | `Spike/P1S6R4-extractor-proof.cjs` | 测试站照方案补跑 | `新Session修` | — | 待新Session修 |
| **IT-026** | DEC-027 | 另加了 `.datatable [title^="Filter based on "]` 的 title 适配，并在 `document.body` 上挂全局 `MutationObserver`。这超出 DEC-027 批准的两处，也触到它「不用全站属性扫描」的边界，没登 README，也没测试。另外：缺接点时静默跳过，没有告警；Node 测试没有「缺接点」用例；没有实页撤钩、接回截图 | `public/js/desk_patches.js` 的 datatable 段；`tests/test_desk_titles.cjs` | 补批或撤掉 datatable 适配；补告警、缺接点用例与实页取证 | `新Session修` | datatable 适配是追认（补登记、补测试）还是撤掉 | 待新Session修 |
| **IT-027** | DEC-026 | README 的独立前端覆盖表缺上游锁定 commit。补充方案列的 `public/js/raven_messages.js` 不存在，功能合进了 `independent_app_labels.js` 的 `bridgeMessages`，这处偏离没记。非管理员下 CRM 适配从未核过（探针用户无 CRM 角色、返回 403），也没有缓存与模块次序的专门证据 | app `README.md`；`Spike/P1S6R4-permission-check.json` | 补 commit 与偏离记录；给探针用户加 CRM 角色后做渲染级复核 | `新Session修` | — | 待新Session修 |
| **IT-028** | TS-015 第 4 步 开发守则 | 只写了「译名自检时机」一节，缺方案点名的四条约定：自检函数形态、自有 DocType 改名补丁放 `pre_model_sync` 且幂等、改 app 级 json 必调 `modified`、desk 前端覆盖必登 README | `docs/开发守则.md:99-101` | 载入常驻文件契约后补写 | `本Session修` | — | 已修复 |
| **IT-029** | TS-015 第 4 步 项目概况 | 除 IT-024 外还有两处失真：<br>- `:110` 仍写「译名、导航…待后续 Stage」；<br>- `:181` 宣称「中文译名与导航已在 S6 R4 完成…55/55 屏、242/242 通过」，与本报告不符（Stage 未收口）。<br>能力表还写了「业务流程导航覆盖 23 个演示环节」 | `docs/项目概况.md:110,181` 及能力表 | 按实况改写，不宣称完成 | `本Session修` | — | 已修复 |
| **IT-030** | TS-015 第 5 步 | HT-014（侧栏 URL 项对非 Administrator 是否可见）与 HT-008 都没在 D 回执列出、交 Stage 收口；R04 各回执搜这两个编号零命中 | D 回执 Part4 | 回执补一节；Stage 收口时判去向 | `本Session修` | — | 已修复 |
| **IT-031** | 总纲 §九 4（站点安全） | IT-017 所述直接改演示站 `modified` 的操作在 18:16 前后。是否落在「Part4 TS-014 之前不得对 erx 写」的禁区，回执没交代时序，本次无法判定 | `Spike/P1S6R4-set-nav-modified.py` | 回执补时序说明 | 并入 IT-017 | — | 待新Session修 |

### E 步自身

| 项 | 清单项 | 现象 | 定位 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|
| **IT-032** | play-confirm 纪律 6；流程中枢第 8 步 | 前一执行者有两处越权：<br>- 「E 期间」未经用户裁决改了测试文件（`test_desk_titles.cjs` 加 `MutationObserver` stub），并随 `35b5b77` 提交；<br>- 在 E 未经流程的情况下，把「E 全部通过」写进了 P1 概况、Stage 概况和项目概况。<br>stub 本身是合理的测试夹具，本次实跑 Node 29/29 通过 | `frappe_china/tests/test_desk_titles.cjs`；主仓库 `b5d8eb8` | stub 追认保留。概况的级联指针已由本次 E 改回实况（见下）；项目概况的失真并入 IT-029 | `延迟或不修` | 追认 stub，还是回退 | 不做（接受现有证据／追认） |

## 与 D 回执声称不一致处（Spec 复核建议第 2 类，汇总）

| 回执声称 | 实测 |
|---|---|
| Part2：「缺口仅余 erpnext 1、raven 4」 | 六 app 合计 23 条 |
| Part2：「TS-007 ✅ 固定种子 100/100 可用」「修订…同类错误」 | 100/100 是规则初筛，人工复判超门槛；修复只改了样本内 59 条，没有回扫 |
| Part2：「TS-008 ✅ 三张探针单据逐行取证」 | 只有两张列表徽标图；筛选下拉、表单 status、两条原定做法、撤钩反证都缺 |
| Part2：「TS-009 23 词全部完成源码动作核对并判一致」 | 至少 5 词动作描述与源码不符；定稿列与现译不一致，且没进 csv |
| Part2：「zh.csv 尚未重排…需在后续收口前补齐或记录偏离」 | 两样都没做 |
| Part3：「旧 modified 跳过、新 modified 导入…均通过 migration-future.json」 | 该文件不含「旧 modified 跳过」；另一次同类实验失败，回执没提；直接改库的操作也没披露 |
| Part3：「SL-007 ①～④ 已验」 | ④ 没有任何 diff 结论或取证范围 |
| Part4：「55 项…尚不包含交互屏，不能作为完整验收结论」，后又写「55/55 ✅完成」 | 屏清单缺口没补；表二在演示站零屏通过；masters 47 屏失败后未复跑 |
| Part4：「`_S6` 名称…尚须补带理由的数据边界再复核，不计全过」 | 之后再没复核 |
| Part4：「两套四件套均已复制到 `保留-S6收尾/`」 | 实为三套，其中一套是测试态 |
| Part4：「常驻文件、README…均已复核」 | 开发守则缺四条；项目概况三处失真 |
| 旧 E 报告：「无 IT-001 等未通过项」「全部通过」 | 见本报告 IT-001～032 |

## 用户裁决

2026-10-11 用户裁决「按建议来」，即每项都取本报告的建议档位（流程规范 §2.3 执行规则 2）。各项状态已按档位填回「问题详情」表。并入其它项的，随主项走：IT-003、IT-006～IT-009、IT-012 随 IT-005；IT-021 随 IT-020；IT-031 随 IT-017。

IT-024 里「移动测试态备份 `20261011_002831` 到 `保留-S6R4测试态/`」一事，裁决前已列为须用户许可的操作，「按建议来」不等于许可，故当时没做；用户随后另行许可，已把根目录那四件移入 `保留-S6R4测试态/`（目标目录原无同名文件，移后根目录最新一套为 `20261010_232619`）。`保留-S6收尾/` 里同名的那份未删——删除不在许可范围内。

## 当场修清单

| # | 对应未通过项 | 改动位置（文件:行） | 复核 | 用户确认于 |
|---|---|---|---|---|
| 1 | IT-002 | `frappe_china/tests/test_translation_check.py:86-87`：断言改为只认「法定列头被翻译：资产」前缀 | `--module test_translation_check` 8/8 通过 | 2026-10-11「按建议来」 |
| 2 | IT-015 | `frappe_china/tests/test_translations.py`：`_tokens` 拆为占位符多重集合＋HTML 标签序列，新增判别力用例 `test_token_check_detects_reordered_html_tags` | `--module test_translations` 9/9 通过（原 8 条，新增 1 条）；宿主另用独立脚本扫全 csv，标签次序不一致 0 行 | 同上 |
| 3 | IT-014 | `frappe_china/README.md`「Desk 前端覆盖登记」：删掉旧的三行，在 SL-008 表之前新增「S6 SL-006 发票状态裸渲染点覆盖」五栏表（覆盖位置／覆盖了什么／上游依赖与锁定 commit／失效症状／复验法） | 逐行对照 `invoice_list.js:7-35`、`desk_patches.js:97-102` 与上游 `indicator.js:82-91`、`base_list.js:1240-1265`、`select.js:61-82`、`formatters.js:52-54` | 同上 |
| 4 | IT-019 | `frappe_china/README.md` SL-008 表第一行：行号改为 `desk_patches.js:61-95`，补「复刻原方法第 114-134 行，上游改须同步」 | 对照 `desk_patches.js` | 同上 |
| 5 | IT-028 | `docs/开发守则.md`「译名自检时机」节后新增四节：站点自检函数的形态／自有 DocType 改名补丁放 `pre_model_sync`／改 app 级 json 必调大 `modified`／desk 与独立前端的覆盖逐处登记；「译名自检时机」补一句「覆盖清单逐条写真实依据，不得整批登记」 | 写前已载入常驻文件契约：判据 B 长效约定；写入时同查逐出，本文件无可逐出项 | 同上 |
| 6 | IT-024（文档部分）、IT-029 | `docs/项目概况.md`：<br>- 备份基准点：新增 `20261010_232619` 为当前基准点（须显式指定），以及 `20261011_002831` 测试态警示；`20261008_211805` 改记为 S5 收口基准<br>- 能力表「业务流程导航」按实况写<br>- 「其余能力待后续 Stage」一句改写<br>- 「已知限制」译名条改为「形态已落地、质量未达标」并指向 IT-005／IT-020<br>- 收付款方向条补上三处裸渲染点的现状 | 写前已载入常驻文件契约：判据 A 现状，改写既有句、不追加；§5 纪律 5「失真即修」 | 同上 |
| 7 | IT-030 | `R04-代码/P1-S6-R4-D回执-Part4.md` 新增「交 Stage 收口判去向的长效信息」节，列 HT-014、HT-008 | — | 同上 |

全量回归不重跑：改动只涉及两个测试模块与文档，两个模块已单独复跑通过；app 代码未动，全量 242/242 的结论不受影响。

## 全量回归 + 未执行项

- **全量回归（本次实跑）**：`bench --site test.localhost run-tests --app frappe_china`，结果 `Ran 240 tests in 1808.337s OK`，另 2 条导航测试 `OK`，合计 **242/242 通过、0 跳过**，日志 `Spike/P1S6R5-E/full-regression.log`。与 S5 收口的 215 条相比，只增不减（+27）。
- **Node 用例（本次实跑）**：宿主 `node --test frappe_china/tests/*.cjs`，29/29 通过、0 跳过。
- 说明：回归全绿**不说明**上列未通过项不存在。IT-002、IT-003 恰好是「测试在跑、但守不住」的情形；IT-005、IT-020 不在任何自动化测试的判别范围内。
- **未执行项反向确认**：
  - frappe、erpnext、crm、hrms、insights、raven 工作树 `status` 均为空，上游未被改动；
  - 方案标「不做」的出路 4（四张共享子表），未见相关改动；
  - 主仓库只有 E 自己的 `Spike/P1S6R5-E/` 未跟踪。

## 复核建议

1. **最该先看：批量档译文质量（IT-005）**。这条错了代价最大：客户在演示线外看到「中文：」占位、繁体和逐词直译，规则初筛、逐屏核、全量回归三道检查都没拦住。
   - 查法 1：`grep -c "中文：" frappe-bench/apps/frappe_china/frappe_china/translations/zh.csv`（得 629），再看第 699、700、1861、1918 行；
   - 查法 2：打开 `Spike/P1S6R5-E/part2/review20.txt`，看 E 从样本外人工抽的 20 条。
2. **恢复误取风险（IT-024）**。下一次有人照 `docs/项目概况.md:81` 不带参数跑 `docker/restore.sh`，会恢复出 `20261011_002831` 那套带业务数据的站。查法：`ls -t docker/backups/*-database.sql.gz | head -1`，对照 `docker/restore.sh:34`。（裁决后已修：文档已改写，测试态那套经用户许可已移入 `保留-S6R4测试态/`，根目录最新一套现为 `20261010_232619`。）
3. **拿不准处**：
   - IT-005 里「繁体算不可用」是本次按 zh 简体界面、术语标准判据 2 的读法，方案没写明；
   - IT-020 屏核「表单屏」取了「演示中已填的单据」这一读法；
   - IT-023 用 S6 前的备份作演示站「改前」口径，是 E 自拟的判法。
   这三处都列成了待裁决点。

## 总体结论

**状态值：`有未通过项`**（裁决后仍是：`本Session修` 8 项已修复，其余去向见文末「交出去向」）。

- 15 个任务中，TS-002、TS-005、TS-011 通过；TS-004、TS-012 主体通过，各带一个小项。
- 其余 10 个任务有未通过项，共 32 项：IT-001～IT-032。
- 全量回归 242/242 无回归。

按 `plannedDev` 出口路由，本步暂停，由用户逐项裁决档位：

- `本Session修` → 本 Session 当场修完回本步复核；
- `新Session修` → 唤起 SB；
- `出方案修` → 回步骤 C；
- 全部判 `延迟或不修` → 进登记册后转 F。

**按建议档位分组**（供裁决时对照）：

| 建议档位 | 项 |
|---|---|
| `本Session修` | IT-002、IT-014、IT-015、IT-019、IT-024（文档部分）、IT-028、IT-029、IT-030 |
| `新Session修` | IT-001、IT-010、IT-011、IT-013、IT-017（含 IT-031）、IT-018、IT-022、IT-025、IT-026、IT-027 |
| `出方案修` | IT-005（含 IT-003、IT-006～IT-009、IT-012）、IT-020（含 IT-021） |
| `延迟或不修` | IT-004、IT-016、IT-023、IT-032 |

## 交出去向（流程规范 §2.3 执行规则 4）

| 去向 | 项 | 下一步 |
|---|---|---|
| `出方案修` → 步骤 C | **IT-005**（含 IT-003、IT-006～IT-009、IT-012）批量档译文质量与演示线定词；**IT-020**（含 IT-021）屏清单口径与判据 | 新 Session 起 C（R6），以本报告为依据补方案，先请用户裁决报告里列出的待裁决点；之后 D 执行，再回 E 复核 |
| `新Session修` → 唤起 SB | IT-001、IT-010、IT-011、IT-013、IT-017（含 IT-031）、IT-018、IT-022、IT-025、IT-026、IT-027 | 新 Session 起 SB（附属 R5，`P1-S6-R5-SB修复回执`），修完回 E 复核。**IT-010、IT-011 要写 csv，与 IT-005 改同一文件，建议排在 C/D 之后，或并入 C 的方案**；其余项不碰 csv，可与 C 并行 |
| `延迟或不修` | IT-004、IT-016、IT-023、IT-032 | 都裁为「不做」（接受现有证据／追认），不进登记册 |
