# SB修复回执（对象：代码 / 依据：P1-S4-R12-E确认报告 ＋ P1-S4-R7 开发方案）

**轮次**：P1-S4-R12｜**日期**：2026-10-01｜**步骤**：`plannedDev` SB（build）｜**执行者**：Claude（Opus 5.5）
**Round 归属**：`附属=原Session做`——本次修复是 R12 E 步那个工作项的一部分（同 Session、只改 E 报告裁为「立即修」的项），**不占 Round**，沿用 R12。
**依据**：[E确认报告](P1-S4-R12-E确认报告.md)＋[开发方案总纲](../R07-开发方案/P1-S4-R7-C开发方案-总纲.md)／Part1–4
**用户裁决**（2026-10-01）：「IT-036恢复兜底，其它按你的建议来。」
**用户许可**（2026-10-01）：写演示站（IT-034 migrate、IT-014 删 `ts019.csv`）——「同意」，先备份；SB 完成后 `frappe_china` 与 docs 各 commit＋push 一次。

## 逐项执行结果

| 任务 | 报告项号 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| 演示站 migrate | IT-034 | 演示站 `erx.localhost`（先备份到 `docker/backups/保留-R12迁移前/20261001_235432-*`，`gzip -t`／`tar -tf` 通过） | ✅完成 | 10-02 | `bench --site erx.localhost migrate` 跑了两次：第一次修 IT-007／010／013 三处；IT-036 改了 fixture 后再跑一次，把 `party_type` 带上演示站。复查见「复验结果」。第一次迁移时上游 `delete_duplicate_icons`（`frappe/model/sync.py:313-326`）删了一个改名残留的 App 图标「Frappe Framework」，见「偏离与暂停」 |
| 演示站 `ts019.csv` 清理、测试站 TS-019 界面取证 | IT-014 剩余 | 演示站 File `cc29a46be6` 及磁盘文件；`docs/01-需求摸底/Spike/P1-S4-R12-TS019-ui-*.png`（4 张） | ✅完成 | 10-02 | 删前断言：文件名、路径吻合，未挂任何单据，无其它 File 共用该路径；删后记录与磁盘文件都不在。界面取证见「TS-019 界面取证」节 |
| 科目表 JSON 按原字节入库 | IT-035 | `.gitattributes`（新建，该文件 `-text`）；`git add --renormalize` | ✅完成（随本轮提交落地） | 10-02 | 暂存区 sha256 为 `539d12f5…867972`，与 zelin 原件、工作区相同；`git ls-files --eol` 为 `i/crlf w/crlf attr/-text`。提交后在容器内复查 `git status` 不再报它被修改 |
| 行名行次与勾稽式钉住 | IT-032 | `tests/statutory_layout.py`（新建，按方案表逐字写死）；`tests/test_mapping.py:45-57`；`tests/test_balance_sheet.py:44-60`；`tests/test_cash_flow.py:223-` | ✅完成 | 10-02 | 资产负债表左右栏 32×2 位、利润表 32 行、现金流量表 25 行、10＋9 条勾稽式，测试同时比 `mapping.py` 与报表 `run()` 的输出。不从被测模块读期望值（R11 约定） |
| SL-006 ⑧⑩⑦ 测试 | IT-033 | `tests/test_balance_sheet.py:62-100`；`tests/test_statement_dataset.py:228-237` | ✅完成（⑦ 末句见「偏离与暂停」） | 10-02 | ⑩ patch `BS_LEFT` 让货币资金不取数 → `text-danger`、「差额 -1000.00」、`report_summary` 三项全红；⑧ patch 映射为两个不存在的号 → 报错一次列出两个号；利润表同理；营业税、开办费 0.00 且说明行原因逐字断言 |
| `test_mapping` 判别力 | IT-018 剩余 | `tests/test_mapping.py:76-139` | ✅完成 | 10-02 | 重复覆盖改为按解析后的明细逐个科目号展开比较、两张表都查，排除「其中」子行（从独立基准的 ≥ 式取，不读被测常量）；覆盖改为两张表各自判，利润表排除 `UNCLOSED_PL_ROOTS`，子行不计入上级覆盖。删掉了与事实不符的旧注释 |
| 现金流测试缺口 | IT-019 剩余 | `cn_tax/doctype/cash_flow/cash_flow.py:41-97`；`tests/test_cash_flow.py:161-248`；`tests/test_statement_dataset.py:278-` | ✅完成 | 10-02 | 代码三处：⑤① 一次列出全部缺代码的**行号**；同凭证内部转账行借贷合计须为 0（TS-015，validate 校验）；⑤② 的「有现金流水的月份未交」检查移到单纯顺序检查之前，两条报错可区分。测试：⑦ 与月末余额不符的正向用例；第 6 条年报逐行；④ 行名对独立基准；现金流量表「上年无数据」 |
| 建账与自检测试 | IT-022 剩余 | `tests/test_company.py:155-192`；`tests/test_selfcheck.py:43-58` | ✅完成 | 10-02 | 补公司已回滚断言；新增让 `Company.validate` 抛错的用例（回滚前标志仍为真、回滚后为假，只有 `after_rollback` 能复位）；「缺科目」改删叶子 `1622` 并精确断言 `missing_from_chart`；`test_company` 补税模板／规则／类别计数 |
| 译名补齐 | IT-024 剩余 | `translations/zh.csv`（＋76 行）；`tests/test_translations.py:74-116` | ✅完成 | 10-02 | 新测试扫全 app 的 `_()`／`__()` 源词与 DocType、字段 label、Select 选项，要求 `zh` 下都有译文（编码名 `UTF-8`／`GB18030` 除外）。判别力：临时删掉 `Closing Type` 一行 → 失败并列出它，已还原。连带把 4 个按英文报错原文断言的测试改为中文 |
| 恢复按往来类型兜底预填 | IT-036 | `fixtures/cash_flow_code.json`（第 1、3、4 项 `party_type`）；`cn_tax/doctype/cash_flow/cash_flow.py:161-180`；`README.md:102-106`；`tests/test_cash_flow.py:62-107` | ✅完成 | 10-02 | 预填顺序同 zelin：科目 → 对方科目 → 往来单位 → 项目默认往来类型。往来单位一级只查 Customer／Supplier（只有它们带该字段）。README 补登记 fixture 另外三处改动与本处 |
| 文档小瑕疵 | IT-037 | `R08-代码/P1-S4-R8-D回执-Part4.md:119`；`docs/项目概况.md:67-72` | ✅完成 | 10-02 | D 回执更正段那句改为指向本回执；项目概况备份清单的缩进归位、标题改为「备份基准点」，补上本轮迁移前备份。改常驻文件前已载入常驻文件契约，同文件写入即查逐出：无触发项 |
| 全量回归 | — | `bench --site test.localhost run-tests --app frappe_china` | ✅完成 | 10-02 | 112/112，见「全量验证」 |
| 锁定 `docker/apps.json` | — | `docker/apps.json`（`docker/lock-apps.sh`） | ✅完成 | 10-02 | 用户指令「更新apps.json」。`frappe_china` 由 R9 前的 `57286df` 更新为本轮提交；`frappe`／`erpnext` 未变 |

## 复验结果

| 报告项号 | 报告的判定标准 | 怎么复验的 | 实测结果 |
|---|---|---|---|
| IT-034 | 演示站三处与测试站一致；自检仍通过 | 两站只读 SQL：`tabCash Flow Code` 第 1、3、4、5、11、12 条行名；`Cash Flow Item` debit／credit 的 `read_only_depends_on`；四个 Report 的 `disable_prepared_report_automation`。`check_all_cn_companies()` | ✅ 行名与测试站相同（1「销售产成品、商品、提供劳务收到的现金」、11／12 已对调回来）；两字段 `eval:doc.manual_split === 0`；四个 Report 均为 0/1；自检 `checked=True, ok=True`、266/266；第二次迁移后第 1、3、4 项 `party_type` 为 Customer／Supplier／Employee。公司仅 HDTH，GL／BT／Cash Flow 仍 0；System Settings 六项不变 |
| IT-014 剩余 | `ts019.csv` 不在；测试站有 TS-019 界面证据 | 演示站 `tabFile` 与磁盘计数；见「TS-019 界面取证」 | ✅ 记录 0、磁盘 0；4 张截图 |
| IT-035 | git 里存的字节与 zelin 原件 sha256 相同 | `git show :<file> \| sha256sum` | ✅ `539d12f5…867972` |
| IT-032 | IT-004 原排法、IT-005 原缺陷植回时有测试失败 | **变异实跑**（临时改 `mapping.py`，跑完还原，`git diff` 为空）：① 右栏 6 个空位挪回末尾；② 去掉 `22>=23`、`24>=…` | ✅ ① `test_mapping` 1 项、`test_balance_sheet` 1 项失败；② `test_mapping` 1 项失败。E 步同样两次变异全过 |
| IT-018 剩余 | 重复覆盖、利润表覆盖两项有判别力 | **变异实跑**：③ 第 51 行改回 `3102,3103,3104`（IT-001 原式）；④ 存货只删 `400101／400102／400199`（IT-003 只删一半）；⑤ 删掉利润表第 22 行取数源 | ✅ 三次各有 `test_mapping` 1 项失败。E 步 Part3 片推演三次都测不出 |
| IT-022 剩余 | `after_rollback` 被测到 | **变异实跑**：⑥ 删掉 `company.py` 的 `frappe.db.after_rollback.add(_reset_flag)` | ✅ `test_company` 1 项失败 |
| IT-033 | ⑧⑩ 各有用例；⑦ 末句有断言 | `test_balance_sheet` 5 项、`test_statement_dataset` 15 项 | ✅（⑦ 按 Part2 定义断言，见「偏离与暂停」） |
| IT-019 剩余 | ⑦、年报第 6 条、④ 行名、「上年无数据」；⑤① 行号；⑤② 可区分；内部转账借贷为 0 | `test_cash_flow` 12 项；`test_statement_dataset` 的年报用例在 savepoint 内建 4–12 月空底稿后回滚 | ✅ |
| IT-024 剩余 | 全 app 源词在 `zh` 下都有译文 | `test_translations` 2 项；判别力：删 `Closing Type` 一行 → 失败 | ✅ |
| IT-036 | 往来单位与科目都没设代码时按默认往来类型预填 | `test_party_type_fallback_prefills_code`：Customer→1、Supplier→3、Employee→4，Shareholder 与无往来类型为空 | ✅ |
| IT-037 | 两处文档改正 | 复读改后段落 | ✅ |

## TS-019 界面取证

开发方案 Part4 TS-019：「在测试站界面上走一次『银行流水预处理 → 对账工具 → 自动对账』，截图存 `Spike/`」。做法沿用 R11 TS-017。

| 步 | 做了什么 | 结果 |
|---|---|---|
| 1 备份 | `bench --site test.localhost backup --with-files` | `20261002_014347-test_localhost-*`；`gzip -t`、`tar -tf` 通过 |
| 2 落数据 | 一次性脚本走与 `test_bank_reconcile` 同一条路并**提交**：建本表公司 `_FCT 银行对账取证 FUI`、银行、户头（挂 `1002`）、银行流水格式、一张收款（`reference_no=FCT20260105001`）；GB18030 仿网银 csv（3 行抬头、1 行表头、6 行明细、1 行合计）→ `run_preprocess_and_import` → `auto_reconcile_vouchers` | 预处理单 `BANK-PRE-00026` 状态 `Imported`、6 行、跳过 0；6 条 Bank Transaction；`FCT20260105001` 一条为 `Reconciled`，收款 `clearance_date=2026-01-05` |
| 3 起服务、登录 | 容器内另起只服务测试站的 6787；给测试站 Administrator 设临时随机密码（只存在随后删掉的临时文件里），`/api/method/login` 取 `sid` | `ping` 200；`Company` 列表只有 `FUI` 一家，确认连的是测试站 |
| 4 截图 | 无头 Chrome（DevTools 协议）带 `sid` 依次打开：预处理单、银行对账单导入列表、该户头的银行交易流水列表、银行对账工具（填公司、户头、1 月起止后点「选未核销凭证」） | 4 张，每张 `frappe.boot.lang=zh`、用户 Administrator；对账工具按钮为「上传银行对账单｜自动核销｜选未核销凭证」 |
| 5 存图 | `Spike/P1-S4-R12-TS019-ui-preprocess.png`／`-bank-statement-import.png`／`-bank-transactions.png`／`-reconciliation-tool.png` | 已目视核对：流水列表 6 行、1 行「已核销」；对账工具期末余额 0、已核 100、差额 −100，列出其余 5 笔未核销 |
| 6 恢复 | 停掉 6787；`bench --site test.localhost restore --force` 恢复第 1 步备份（含公私文件） | Company／Account／GL／PE／BT／预处理单都是 0，System Settings 不变；Administrator 密码随恢复回到原值；临时目录 `frappe-bench/tmp_r12_ui/` 已删 |

**说明**：R8 那三张截图（`P1-S4-R8-TS019-*`，实为演示站）不删，作为 IT-014 的原始证据保留。

## 全量验证

| 门 | 结果 |
|---|---|
| 执行前基线 | R12 E 步实跑 98/98 |
| 各模块单跑 | 改动涉及的 14 个模块逐个单跑全过（`test_mapping` 8、`test_balance_sheet` 5、`test_cash_flow` 12、`test_company` 8、`test_selfcheck` 7、`test_statement_dataset` 15、`test_translations` 2、`test_bank_preprocess` 7、`test_closing` 9 等） |
| 本轮全量回归 | **112/112 通过**（unittest 报 304.7 秒）＝ 98 ＋ 14，没有减少。日志 `frappe-bench/logs/r12-sb-full.log`。外层 `time` 报的墙钟 555 分钟不可信（期间宿主侧后台任务到时被收回、容器内进程继续跑），以 unittest 自报为准 |
| 测试方法的增删 | `test_mapping` 删 4 个、增 6 个：被删的 `test_statement_shapes_and_formulas`／`test_every_balance_sheet_number_covers_exactly_one_leaf_set`／`test_chart_leaf_accounts_are_covered_by_some_statement`／`test_resolve_all_statement_accounts`，其断言分别被逐字版式、按明细比的重复覆盖、分表覆盖三组新测试包含且更严（后者对全部行跑 `resolve`）。其余模块只增不删 |
| 回归后站点 | 测试站 Company／Account／GL 都是 0，System Settings 不变 |
| 临时文件 | `frappe-bench/tmp_r12_mut/`、`tmp_r12_sb/`、`tmp_r12_ui/`、容器内临时 `tmp_r12_*.py` 均已删；`ls frappe-bench \| grep tmp` 为空 |

## 偏离与暂停

- **SL-006 ⑦ 末句与 Part2 的定义相互矛盾，已裁决（DEC-121）。** Part3 SL-006 ⑦ 括注：「2026 年 4–12 月没有结转，说明行会列出这几个月未结转」；Part2 TS-010 的状态定义：`closed = 有损益结转 或 本月根本没有损益发生额`。用户表示不懂会计、定不了，授权按 DEC-119「会计习惯为首要需求」定；取 Part2：账结法下损益科目无余额的月份没有结转对象，不做空凭证、不算漏结。过程见 [SB讨论记录](P1-S4-R12-SB讨论记录.md)。测试断言不变，注释改为引用 DEC-121；开发方案是 R7 产物，本步不改写。
- **演示站迁移时上游删了一个桌面图标。** 第一次 `migrate` 输出「Deleting icon Frappe Framework」：上游 `delete_duplicate_icons` 对同一 app 有多个 App 类图标时，删掉在 app 目录里没有对应 json 的那个（改名残留）。删后演示站剩 `Framework`（frappe）与 `ERPNext` 两个 App 图标、共 35 个 Desktop Icon，与测试站完全相同；备份 `保留-R12迁移前/` 里仍有原记录。判断为上游正常清理，未还原。
- **测试站恢复走了两次。** 第一次把「停 6787 服务」和「restore」写在同一个容器命令里，`pkill -f` 的匹配串同时命中了该命令自身，restore 没执行就被杀掉；第二次单独执行时 `restore` 又要求 MariaDB root 密码，从 `docker/.env` 的 `DB_ROOT_PASSWORD` 经环境变量传入（未回显）。最终恢复成功，结果见「TS-019 界面取证」第 6 步。
- **改了几处产品代码的行为**（不只测试），都是报告裁定的修法本身要求的：`cash_flow.py` 的缺代码报错从「遇到第一条就抛、报 GL Entry 名」改为「一次列出全部行号」；新增内部转账借贷合计校验；顺序检查与「有现金流水的月份」检查换了先后；`_assign_default_codes` 增加按往来类型兜底。
- 方案、报告其余各项无冲突，无暂停。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| 法定报表的行名、行次、勾稽式的期望值集中放 `tests/statutory_layout.py`，按方案表逐字写死；改报表行定义时这里同改，否则测试失败 | 测试纪律／位置 | IT-032 |
| 本 app 新增的 `_()`／`__()` 源词、DocType 名、字段 label、Select 选项都必须在 `translations/zh.csv` 有译文；由 `test_every_app_source_string_has_chinese` 扫描强制，不靠手列清单 | 位置／测试纪律 | IT-024 |
| 测试里断言报错文字时用 `zh` 译文（基类已设 `frappe.local.lang = "zh"`），不用英文源词 | 测试纪律 | IT-024 |

## 未做项

| 项 | 为什么没做 |
|---|---|
| IT-025 底稿与法定标题撞名 | R9 裁为出方案修复，不在本轮 |

## 状态值

**`修复已落地`**。R12 E 报告裁为「立即修」的 11 项（IT-014／018／019／022／024 剩余、IT-032～037）都已改完，并按报告的判定标准复验通过；其中 IT-032、IT-018、IT-022 用 6 组变异实跑验证了判别力（E 步时同样的变异测试全过，本轮每组都有测试失败）。全量回归 112/112。SL-006 ⑦ 末句的方案矛盾已按 DEC-121 定（以 Part2 为准）。按出口路由，下一步回 E 复核。

## 复核建议

1. **最该看的是 DEC-121**（`tests/test_statement_dataset.py:228-238`）。它是本轮唯一按「方案另一处定义」而不是按「验收条款字面」写的断言，且裁决依据是 Claude 推定的会计习惯、未经会计确认（LG-153）。查法：能联系上客户会计时问一句「某月没有任何收入费用，月末要不要做结转凭证」。
2. **修复带出的行为变化**：`cash_flow.py` 有四处产品行为改动（见「偏离与暂停」第 4 条），其中报错文字与顺序变了，界面上用户看到的提示会不同；`zh.csv` 一次加了 76 条译文，措辞都是本步拟的，没有对照任何外部词表。查法：在测试站中文界面上故意漏填一张现金流量底稿的代码、跳月提交各一次，看提示是否通顺。
3. **拿不准处**：
   - `Monthly Amount`／`Yearly Amount`（现金流量小计子表的字段）译为「当月金额」「年内累计金额」，刻意避开法定列头「本月金额」「本年累计金额」——后者在 `LEGAL_LABELS` 里，`test_translations` 不允许别的源词译成法定文字（LG-134）。
   - `test_mapping` 的「其中」子行是从原文 `≥` 勾稽式右边推出来的（如 `24>=25+…+29` 推出 25–29 都是 24 的子项），方案没有单列这张清单；按原文版式，26–29 确实是「营业外支出」的明细。
   - 重复覆盖检查把「同一科目只出现在 pos／neg 拆分行」视为合法，但没有逐对核验拆分是否互补（例如 `1122` pos 进行 4、neg 进行 34），互补性由数据集测试 `test_party_and_tax_reclassification` 兜。
