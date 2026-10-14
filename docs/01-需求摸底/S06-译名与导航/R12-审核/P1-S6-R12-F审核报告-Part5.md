# F 审核分片报告 · 片 5（对象：`zh.csv` 全表与四道质量守卫、覆盖清单、白名单、基线／占用／清场脚本 / 审核标准：B 需求文档 §4.2～§4.4、§4.9、AC-006／007／009 ＋ R6 C 讨论记录 DEC-028～038 ＋ R6 开发方案 SL-011～015）

**轮次**：P1-S6-R12｜**步骤**：F 分片 5｜**日期**：2026-10-13｜**执行者**：Claude 子 Agent（只读）
**依据**：[R6 C开发方案](../R06-开发方案/P1-S6-R6-C开发方案.md)（全文）；[R6 C讨论记录](../R06-开发方案/P1-S6-R6-C讨论记录.md)（DEC-028～038）；[B需求文档](../R02-需求文档/P1-S6-R2-B需求文档.md) §4.2、§4.3、§4.4、§4.9、§八；`docs/开发守则.md`「译名自检时机」；`docs/业务规则.md`；S3 [术语标准草案](../../S03-演示前置/R01-前置讨论/P1-S3-R1-A术语标准草案.md) §1、§2.3（核覆盖依据用）
**线索（不采信，只作索引）**：[R7 D回执](../R07-代码/P1-S6-R7-D回执.md) 与三份附表、[R7 D讨论记录](../R07-代码/P1-S6-R7-D讨论记录.md)、[R8 E确认报告](../R08-确认/P1-S6-R8-E确认报告.md)；R9 C 讨论记录 DEC-039（只为追 `Master` 一条）
**被审范围**：`frappe_china` HEAD `d441e9f`（S6 改动面 `474cd1c..d441e9f`）中——`translations/zh.csv`（5751 行）、`tests/test_translation_quality.py`、`tests/translation_whitelist.py`、`tests/translation_overrides.py`、`tests/test_translations.py`、`tests/test_named_terms.py`；主仓库 `Spike/P1S6R4-baseline.py`、`Spike/P1S6R4-occupancy.py`、`Spike/P1S6R6-csv-prune.py`、`Spike/P1S6R4-sample.py`、`Spike/P1S6R6-trad-chars.py`、`Spike/P1S6R6-batch|demo/`、`Spike/P1S6R7/`（只读）。R8（`3f9511a`）与 R11（`d441e9f`）E 当场修按已裁决处理，未重提。

## 覆盖自证

- **读全的依据**：F Spec、`bricks/audit.md`、`bricks/sharding.md`、R6 开发方案全文（§一～§八建要求清单）、R6 C 讨论记录全文、B 需求 §4.2～§4.4、§4.9、§4.10～§4.12、§八全文、`开发守则.md`「译名自检时机」节、`业务规则.md` 全文、S5 Part5 参考格式。R7 回执、讨论记录、覆盖清单判定附表读全；按钮抽检附表、演示线定词附表只按键查（定词表、撞名判定表）；R8 E 报告读了逐项确认、问题详情、清单外发现、裁决与当场修四节。**未读**：R3 方案总纲与 Part1～4 全文（只用 R6 §六替换表）、R9／R10 方案与回执全文（只追了 DEC-039 一条）、流程规范 §2.2／§2.3 原文。
- **逐行读的代码**：`test_translation_quality.py`（1-227）、`test_translations.py`（1-338）、`translation_overrides.py`（1-126）、`test_named_terms.py`（1-144）、`translation_whitelist.py` 头尾与条数；`P1S6R4-baseline.py`（1-312）、`P1S6R4-occupancy.py`、`P1S6R6-csv-prune.py`、`P1S6R4-sample.py` 全文；`P1S6R6-trad-chars.py` 前 60 行、`P1S6R6-visible-text.cjs`／`P1S6R6-screen-check.js` 的判定段；上游 `frappe/translate.py:198-212`、`frappe/public/js/frappe/translate.js:5-20`、`form/templates/form_links.html`、`workstation_dashboard.py`、`standard_chart_of_accounts.py:75-90`、`accounts_receivable.py:1250-1262`、`sales_and_purchase_return.py:474-484`。
- **亲自跑的**（宿主 `python -I -X utf8`，脚本与输出都在 `Spike/P1S6R12-F/p5/`）：基线 `--allow-unlocked` 重跑（`baseline.json`）；独立抽检 `sample_f.py`（种子 20261013）；全表扫描 `scan_csv.py`；三表一致性与覆盖键源码出处 `audit_tables.py`、`hidden_refs.py`；守卫反例 `guard_probe.py`；占用脚本三例；清场脚本 `prune()` 内存重算（未写盘）。演示站 `erx.localhost` 只读：两条 SELECT（`q1.sql`、`q2.sql`），一次 `bench console` 只读取值（`get_dashboard_data`、`get_all_translations`、标准科目表根节点 `_()` 后的值）。
- **跳过**：没跑 `bench run-tests`（约束）；四道守卫只按复制逻辑在独立脚本里测，没有在测试框架内变异；没有截屏、没有开演示站界面；165 行 context 行只做了来源归类与守卫复跑，没有逐条判译文质量；R9／R10 新增的 csv 行只核了 `Master` 一条的波及面。

## 逐项落地核查

| 意图层依据 | 要求层要求（方案任务／验收条款） | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| IT-001／SL-011 ④ | 基线 `commits(allow_unlocked)`：不带开关遇未锁即抛，带开关告警后照跑 | `P1S6R4-baseline.py:257-272`、`:277` | ✅ | ✅ | 本片重跑时 `unlocked` 为 `{}`（R5 SB IT-001 已改锁），故只读码核了拒跑分支 |
| IT-006／A19 | 白名单拆成数据模块，不 import frappe；测试与基线共读 | `translation_whitelist.py:1-7`；`test_translations.py:18`、`:199`；`P1S6R4-baseline.py:101-108`、`:110-131` | ✅ | ✅ | 213 条，每条都在某 app 的 `main.pot` 或本 app 源词里（`audit_tables.json`），无死条目 |
| IT-009／SL-011 ⑤ | 占用脚本改读 `merged_dict()`；`Stock Ledger`／「物料凭证」报不可用、占用者 `Stock Ledger Entry` | `P1S6R4-occupancy.py:15-29` | ✅ | ✅ | 本片实跑输出 `usable: False, occupants: ['Stock Ledger Entry']`。判占用只看合并字典的目标词，看不到「同一源词在别的 app 里另有用处」，见 P5-03 |
| A17／SL-011 ① | 四个守卫函数、`STOPWORDS`／`ALLOW`／`QUALITY_EXCEPTIONS` | `test_translation_quality.py:17-188` | ✅ | ✅ | 函数签名与方案一致。四道守卫都先要求译文含汉字（`:153`、`:162`），QE 对一行豁免全部四道（`:134`），见 P5-04 |
| A18 | 繁体判据：GB2312 外汉字 | `test_translation_quality.py:142-149` | ✅ | ✅ | 照方案实现。GB2312 收录的「於／乾／著／後／麽」不会判中；台湾用词（简体字形）不在本守卫范围，见 P5-04 |
| SL-011 ① 全表 | 四道守卫对 csv 全表返回 `[]` | `:198-208` | ✅ | ✅ | 复制逻辑对当前 5751 行重跑，扣除 QE 后命中 0 |
| SL-011 ① 判别力 | 四条构造坏行（帳戶／登录 带 密码／中文：A0／上传 Photo）各被报出，报出内容含源词 | `:210-223` | ✅ | ✅ | 复制逻辑复现四例全中（`guard_probe.py` 第一段）；R8 已做恒假变异 |
| SL-011 ② | `QUALITY_EXCEPTIONS`／`UNTRANSLATED`／`ALLOW` 每项理由非空 | `:225-227` | ✅ | ✅ | QE 39 条都在 csv 里，且每条仍命中至少一道守卫（无死豁免）；`ALLOW` 44 个词都在某行译文里出现 |
| SL-011 ③ | 交集断言两差集；`basis` 形态正则；`ours` 过守卫 | `test_translations.py:210-213`、`:230-237`、`:330` | ✅ | ✅ | 基线 `official_overrides` 114 键与 `OVERRIDES` 114 键完全相等（两差集都空）。第五种形态「本 app 自有源词」（R7 偏离 1）由 R8 IT-045 补了误用断言 `:243-246`、`:326-327` |
| IT-003／TS-017 第 2 步 | 覆盖清单每条 `basis` 写真实依据 | `translation_overrides.py:12-125` | ✅ | ⚠️ | 本片抽 30 条依据回原文全部找得到（见「自证复核」）。但「依据真」不等于「这一行覆盖没有误伤」：无 context 行会作用到上游所有同源词出处，D 步判波及面看的是 `main.pot` 的 `#:` 出处，跨 app 重复的源词出处不全，见 P5-01～03 |
| A15／SL-012 ① | 清场只留四类；输出各类行数；删除数 = 原 − 留 | `P1S6R6-csv-prune.py:59-83`、`:96-109` | ✅ | ✅ | 取法用 AST 执行 `test_translations` 里同名两函数，与测试同一取法（`:41-56`）。脚本默认就写盘，现在重跑会删掉 5433 行，见 P5-06 |
| A16 | 覆盖官方的批量行一律删除回落官方 | `translation_overrides.py` 全部 `basis` | ✅ | ✅ | 114 条依据里没有「批量档」；R7 TS-021 的 15 个「官方即原样」键进了白名单 |
| A20／SL-012 ⑥ | 全表按（源词 casefold，context）排序；`test_csv_sorted` 含对调判别力 | `test_translations.py:270-278`、`:318-323` | ✅ | ✅ | 宿主重算逆序对 0；排序键与清场脚本 `sort_rows`（`prune.py:86-87`）一致 |
| R7 新增约定「判重按 Frappe 读法」 | csv 判重前把源词里字面 `\n` 换成换行 | `test_translations.py:179-181`；对照 `prune.py:66-67`、`P1S6R4-baseline.py:66` | ⚠️ | ⚠️ | 两个 Spike 脚本按 Frappe 读法归一，测试 `_duplicate_keys` 没有归一。当前 csv 按归一键查重 0，没出事，见 P5-05 |
| SL-012 ③／AC-006 | 基线重跑六 app 缺口合计 0，例外只在白名单 | `Spike/P1S6R12-F/p5/baseline.json` | ✅ | ✅ | 本片实跑：`gap_counts` 六个 0，`identity_gap_counts` 六个 0，`whitelisted` 合计 228 |
| SL-012 ④／AC-007 | 分层抽检 100 条、不可用 ≤ 10 | `Spike/P1S6R6-sample.out.csv`、`-review.json` | ✅ | ✅ | 本片另抽 80 条（批量档 60、演示线档 20），80 条全部可用，与 R7 的 97/100、R8 的 0/40 方向一致 |
| SL-013 ①～③ | 演示面无中文键逐条有译；撞名每组定词或同义保留；收付款方向落 csv 进 `NAMED_TERMS` | `test_named_terms.py:12-89`；`baseline.json` `demo_collisions` | ✅ | ✅ | 75 个 `NAMED_TERMS` 与宿主合并字典逐键相等。当前 188 组演示撞名的目标词都能在 R7 附表或 R7／R8 的判定 json 里找到记录 |
| TS-019 DJ-001／IT-048 | 无 context 改词的已知代价逐条列出 | R7 讨论记录第 1 步 | ⚠️ | — | 列了 `Available`／`Operations`／`Finish` 三处。同类代价还有 `Expenses`（科目根）、`Ledger`（纸张规格）、`Item Type`（导航栏条目）、`Debit Note`／`Credit Note`（日记账凭证类型）没列，原因相同，见 P5-02、P5-03 |
| DEC-039（R9，csv 全表范围内） | 称呼 `Master`→少爷 只作用于称呼下拉 | `zh.csv:2887`；`translation_overrides.py:60` | ❌ | — | 同一源词在 `workstation_dashboard.py:8` 是工位表单「关联」页签的分组标题（意为主数据）。演示站实取：`DASH ['少爷', '交易']`，见 P5-01 |
| 守则「译名自检时机」第 2 段（TS-024 ③） | 批量写 csv 前后跑守卫；不取材 zh_TW；例外登记理由 | `开发守则.md:103` | ✅ | — | 措辞与 R7 新增约定一致 |
| 方案外夹带 | — | `git diff 474cd1c..d441e9f` 本片文件 | ✅ 无功能夹带 | — | 本片文件里方案外的改动都对得上 R8／R9／R10／R11 的已裁项（`LITERAL_KEYS`、`R9_OWN_KEYS`、`_source_strings_from_text`、`_misused_own_basis`、`_PLACEHOLDER` 闭合）。`JAN` 同时在 `UNTRANSLATED` 与 `OVERRIDES`／`NAMED_TERMS`，属重复登记，见 P5-07 |

## 业务规则合规核

| 规则条款 | 本 Round 改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则科目表 | 间接涉及（`Expenses` 无 context 覆盖） | 合规（未经专家确认） | 演示公司用 `小企业会计准则(2024)`，科目名不经这个 `_()`，不受影响。但 ERPNext 标准科目表的根节点 `_("Expenses")` 在 zh 会话下建公司会叫「报销管理」（演示站 console 实取根节点 `['资金(资产)使用', '报销管理', '收入', …]`），这是会计语义错，不违反 BR-001（不是本项目准则的科目表），记为 P5-02 |
| BR-002 法定报表列头 | 涉及（csv 不得译成法定列头） | 合规（未经专家确认） | csv 译文与 `labels.py:20-24` 字面列头同名 0 行；测试 `test_translations.py:214-221` 守住，豁免只给 `NAMED_TERMS` |
| BR-003～BR-007（税率、价税分离、增值税结转、附加税、恒等式） | 不涉及 | — | 本片只改译名，不改计税与报表计算 |
| 收付款方向（S3 术语标准 §1.1／§1.3、DEC-035／036） | 涉及（术语，不是 BR 不变量） | 草案·待领域专家确认 | 23 行落 csv、进 `NAMED_TERMS`，宿主合并字典逐键相等；`Unpaid` 无 context 显示官方「未付」。这些是用词决定，不是领域不变量，不进 `业务规则.md`，是对的 |
| `Dr`→借方（DEC-003）、`Cr` 官方「贷方」 | 涉及 | 合规 | 会计方向用词正确；`Dr` 作称呼的代价已由 LG-011 登记 |
| 本片总体 | — | 无新增或变更的领域不变量 | 无需触发规则送审 |

## 集成点登记（交接摘要）

**本片暴露**

| 接口／状态 | 定义处 | 消费方（实测 grep） | 契约 |
|---|---|---|---|
| `_app_source_strings()`／`_source_strings_from_text(name, text)` | `test_translations.py:87-160` | 同文件 `test_every_app_source_string_has_chinese`（`:199`）、`test_override_basis_forms`（`:236`）、`test_literal_keys_are_app_sources`、`test_r9_own_keys_are_app_sources`；`Spike/P1S6R6-csv-prune.py:41-56` 用 AST 摘出两函数源码执行（不 import frappe）；`Spike/P1S6R12-F/p7`、`Spike/P1S6R9/own-keys.py` 等核查脚本 | 只认 `_()`／`__()`／JS `translate(` 字面量、名字以 `SOURCE(S)` 结尾的常量、DocType／Report／Workspace Sidebar／Desktop Icon json；跳过 `tests/` 与非 `custom_field` 的 fixtures。写法约定在 `开发守则.md:105`。改名或拆函数会让清场脚本 `KeyError`（`prune.py:50-51` 显式检查） |
| `REQUIRED_TRANSLATIONS`、`LITERAL_KEYS`、`R9_OWN_KEYS` | `test_translations.py:20-84`、`:164-176` | 清场 `keep_keys()` 只读 `REQUIRED_TRANSLATIONS`（`prune.py:62`）；后两者只被测试断言为本 app 源词 | — |
| `NAMED_TERMS`（75 键） | `test_named_terms.py:12-89` | `test_named_terms`；`test_translations.py:15`、`:218`（法定列头豁免）；`prune.py:63`（保留类 ②） | 键形 `源词` 或 `源词:context`。**另有一份手抄副本** `P1S6R4-baseline.py:14-24` `NAMED_SOURCES`（36 个，不带 context），只决定哪些键算演示面；R9 以后新增的点名词（称呼、`JAN`、`CN Tax` 等）没同步进去 |
| `OVERRIDES`（114 条，`Override(official, ours, basis)`） | `translation_overrides.py:4-125` | `test_translations.py:17`、`:212`、`:234-237`、`:248-256`；`prune.py:64`（保留类 ③） | 键集合须恒等于「csv 键 ∩ 六 app 官方 zh.po 键」（基线 `official_overrides` 实测 114 = 114）；`basis` 五种形态（`:330`） |
| `UNTRANSLATED`（213 条） | `translation_whitelist.py` | `test_translations.py:199`；`test_translation_quality.py:14`、`:226`；`P1S6R4-baseline.py:101-131`（按路径载入）；`P1S6R4-sample.py:22`；`Spike/P1S6R7/merge_check.py:18` | 不得 import frappe（基线按路径载入）；键可带字面 `\n`，读取方自行归一 |
| `guard_problems(rows)`、`find_*`、`ALLOW`、`QUALITY_EXCEPTIONS` | `test_translation_quality.py:22-188` | `test_translations.py:232-237`（`ours` 过守卫）；`Spike/P1S6R7/merge_check.py:16`、`:59`（合并前检查，须在容器里 import frappe_china） | 返回 `"键 => 译文"` 列表，已扣 QE |
| 繁体字表 `Spike/P1S6R6-trad-chars.json`（373 字） | `P1S6R6-trad-chars.py` | `P1S6R6-visible-text.cjs:111`、`P1S6R6-screen-check.js:278` | 与测试守卫同一 GB2312 判据，但只取「zh_TW 用字 − zh 用字」，比测试守卫窄：测试能判中的 GB2312 外字，逐屏核不一定判中 |

**本片依赖**
- 共享状态 ①：`installed_apps` 顺序决定合并字典叠加（`frappe/translate.py:172-187`），`frappe_china` 末位。基线与占用脚本按 `APPS` 元组（`baseline.py:13`）硬编码同一顺序，不读站点。
- 共享状态 ②：翻译缓存。改 csv 后须 `clear-cache`，测试里 `clear_cache()`（`test_translations.py:197`、`test_named_terms.py:95`）。
- 上游契约 ①：Frappe 读 csv 时源词与译文都把字面 `\n` 换成换行、只 strip 译文（`translate.py:203-211`）。
- 上游契约 ②：前端 `__(txt, null, ctx)` 先查 `txt:ctx`，查不到退回无 context 键（`translate.js:12-18`）。所以无 context 覆盖行会作用到所有没写 context 行的同源词渲染点。P5-01～03 都从这里来。
- 上游事实 ③：六个 app 的 `main.pot` 不重复收录前面 app 已有的 msgid（实测 `Master`／`Transaction`／`Save` 在 erpnext 的 `main.pot` 都是 0 条，`Expenses` 在 hrms 的 `main.pot` 是 0 条，但源码里都有 `_()` 调用）。凡是靠 `#:` 出处判「这个源词在哪里用」的脚本与附表（基线 `demo_surface`、D 附表「出处」列、R9 讨论记录「只有一处出处」），对跨 app 重复的源词都看不全。
- 法定列头：`accounting/statements/labels.py` `LEGAL_LABELS`（别的片）。

**事件**：本片不发出、也不消费 SSE／realtime 事件。

## 自证复核

| 被审产物声称 | 实际复核 | 一致否 |
|---|---|---|
| R7：TS-018 后四道守卫对全表通过；R8：5745 行守卫全 `[]` | 现 5751 行（R9／R10 加行），复制逻辑重跑扣 QE 后 0 命中 | 一致 |
| R7：重跑基线六 app 缺口 0，例外只在白名单（228） | 本片实跑缺口 0，`whitelisted` 合计 228 | 一致 |
| R7：抽检 97 可用／3 不可用 | 本片独立抽 80 条（种子 20261013；批量档每 app 10 条＝60，演示线档简单随机 20），80 条可用，不可用 0（明细见下表） | 一致（方向） |
| R7：覆盖清单 115→119 条（R7 终），R8 后去 10 条 | 现 114 条，与基线交集 114 完全相等 | 一致 |
| R7 附表／R8：依据「抽 10 组都能回到原文」 | 本片抽 30 条：S3 §1.1／§1.3 五条（`Payment Amount`、`Received Amount`、`Outstanding Amount`、`Is Paid`、`Type of Payment`）、S3 §2.3.x 十二条（`Accounting Ledger`、`Adjustment Against`、`Finished Good`、`Payments`、`Warehouses`、`Available`、`Stock Projected Qty`、`Additional Material Transfer`、`Sales Partner`、`Hold Invoice`、`Credit Note`、`Note`）、「演示线撞名」六条（`Expenses`、`Debit Note`、`Due Date`、`Item Type`、`Leaves`、`Stock Ledger`，R7 演示线定词附表 :624-639）、DEC-039 四条、DEC-035、DEC-041、本 app 自有源词两条。条目与节号都找得到 | 一致 |
| R7 演示线定词附表：`Expenses` 判「HRMS 报销模块，与科目根类型 Expense（费用）异义」 | 被覆盖的官方条目 `Expenses`→「费用」来自 erpnext `zh.po:20267`，它在 `main.pot` 里的出处只有两张标准科目表的根节点（`main.pot:20223-20224`）。也就是说，这次覆盖改掉的正是科目根这个用处 | **不一致**（P5-02） |
| R9 讨论记录：称呼五个源词「在 `frappe/locale/main.pot` 中都只有 `install_fixtures.py` 一处出处」 | 字面属实，但 `Master` 在 erpnext 源码里另有 `workstation_dashboard.py:8` 一处，erpnext 的 `main.pot` 因去重没收录 | **不一致**（P5-01） |
| R7 新增约定：判重按 Frappe 读法归一 | Spike 合并与清场脚本做了，测试 `_duplicate_keys` 没做 | 部分（P5-05） |
| R6 方案 SL-011 ⑤ 占用反例 | 实跑复现 | 一致 |

**本片抽检明细**（判据：需求 §4.2.3 三条加 DEC-029；术语对照宿主合并字典，`lookup.py` 输出；全部可用，下面只列有说明的几条）

| # | 档 | 源词 → 译文 | 判定 | 说明 |
|---|---|---|---|---|
| 10 | 批量 crm | `You can get your access key from ` → 访问密钥可从以下位置获取： | 可用 | 后接链接，句式通顺；源词尾空格没保住，不影响显示 |
| 19 | 批量 erpnext | `Excess Material Transfer` → 调拨数量超出 | 可用 | 出处是报错框标题（`stock_entry.py:1371`），意思对 |
| 20 | 批量 erpnext | `{0} {1} is blocked.` → 已冻结 | 可用 | 与 `Block Invoice`→冻结发票同一套 |
| 26 | 批量 frappe | `Doctype To Sync` → 待同步单据类型 | 可用 | 官方 `Doctype` 就是「单据类型」 |
| 29 | 批量 frappe | `The user can create a new Item…` → 用户可新建物料… | 可用 | 权限帮助页里的 Item 是示例单据类型，「物料」对 |
| 55 | 批量 raven | `points` → 分 | 可用 | 链接预览「123 points」→「123 分」 |
| 70 | 演示 erpnext | `Optional. Select a specific manufacture entry to reverse.` → 选填。可指定要拆解冲回的完工入库单。 | 可用 | 工单拆解对话框；与 `Source Manufacture Entry`→源完工入库单一致 |
| 72 | 演示 erpnext | `Item Wise Consumption` → 物料耗用表 | 可用 | 侧栏报表项，「表」合需求 §4.2.4 用词规则 |
| 80 | 演示 erpnext | `Consume Components` → 原材料耗用 | 可用 | BOM 分节，与 `Raw Materials Consumption` 同义共用（撞名表已判同义） |

另外 71 条照抄出处一读即对，不逐行列出。全表扫描：繁体 0、占位 0、空译 0；台湾用词表 34 个词全表命中只有「设定」5 行、「预设」2 行（大陆同样通用），「数位」2 行是「小数位数」被误切，都不算错。

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P5-01 | 中 | `zh.csv:2887` `Master,少爷`；`translation_overrides.py:60`；上游 `erpnext/manufacturing/doctype/workstation/workstation_dashboard.py:8`、`frappe/public/js/frappe/form/templates/form_links.html:8` | DEC-039 把无 context 的 `Master` 改成「少爷」，本意只给称呼下拉用。但 erpnext 的工位看板数据用 `_("Master")` 做「关联」页签的分组标题（下列 BOM、工艺路线、工序，意为主数据），模板再调 `__(label)`，没有 context，csv 也加不了 context 行。演示站只读复现：`bench console` 中 `frappe.local.lang="zh"` 后 `get_meta("Workstation").get_dashboard_data().transactions` 的 label 为 `['少爷', '交易']`。工位表单是演示线环节 5（需求 §4.9 表一第 5 行）。逐屏核 `05-workstation-saved` 停在 `#dashboard_tab`，没点开「关联」页签，所以没抓到。根因是 R9 查出处时只看了 frappe 的 `main.pot`，erpnext 的 `main.pot` 去重不收 `Master`（`grep -c '^msgid "Master"$' erpnext/erpnext/locale/main.pot` → 0） | 需求 §4.2.2 定词规则 1「逐条看源码里的用处」；§4.9 判据（界面文案不得误导）；DEC-039 失效条件 | 两条路选一：① 用 `hooks.py` `override_doctype_dashboards` 给 `Workstation` 换一个本 app 源词做分组标题（如复用 `Master Data`→基础资料），`Master` 继续给称呼用；② 改 DEC-039，给 `Master` 选一个两处都说得通的词（候选需重新占用核查）。两条都要补一屏「工位表单·关联页签」进逐屏核 | 出方案修 | 走前端／钩子改分组标题，还是回头改 DEC-039 的称呼用词 | 待裁决 |
| P5-02 | 低 | `zh.csv:1922` `Expenses,报销管理`；`translation_overrides.py:34`；上游 `erpnext/accounts/doctype/account/chart_of_accounts/verified/standard_chart_of_accounts.py:81`、`…_with_account_number.py:140`；`hrms/hr/doctype/expense_claim/expense_claim.json:170`、`hr_settings.json:335` | `Expenses` 覆盖官方「费用」，依据「演示线撞名」，附表理由写「HRMS 报销模块，与科目根类型 Expense 异义」。但官方这条译文在 `main.pot` 里的出处**只有**两张标准科目表的根节点（`main.pot:20223-20224`），HRMS 的用处反而因去重不在 `main.pot` 里。结果：zh 会话下按 `Standard` 科目表建公司，费用类根科目会叫「报销管理」（演示站 console 实取根节点列表含「报销管理」），科目名写进库后不会随 csv 回改；报销单的费用明细子表标题、HR 设置的页签也变成「报销管理」。演示公司走小企业会计准则科目表，不受影响；测试站的 `make_std_company` 会建出这样的根科目 | DJ-001「已知代价」要逐条列出；需求 §4.2.2 规则 3（异义的给每个源词一个唯一用词）；会计用语 | 把无 context 行收回到只改首页图标那一处：首页图标 `desktop_icon/expenses.json` 不能带 context，可考虑给 `Desktop Icon` 记录改 label 或走侧栏自有 label；`Expense Claim.expenses` 写 context 行（如「费用明细」）；无 context 行删掉、回落官方「费用」。先跑占用 | 新Session修 | 首页「Expenses」图标是否必须显示「报销管理」（若是，要换一种不经无 context 行的做法） | 待裁决 |
| P5-03 | 低 | `Spike/P1S6R4-baseline.py:194-226`（`demo_surface`）与 `parse_po` 的 `refs`；`Spike/P1S6R4-occupancy.py:18-21`；R7 演示线定词附表「出处」列；涉及行 `zh.csv:2779` `Ledger`、`:2680` `Item Type`、`:1330`／`:1411` `Credit Note`／`Debit Note` | 判一个无 context 覆盖行「会改到哪些渲染点」，D／C 步用的都是 `main.pot` 的 `#:` 出处，但后面的 app 不重复收录前面 app 已有的 msgid，出处天然不全。本片按源码扫 `_()`／`label`／`options` 字面量，对 114 条覆盖键逐个比对（`hidden_refs.py`），`main.pot` 漏记的出处有 27 个键，其中意思对不上的：`Ledger`→会计账簿，在 `main.pot` 里**唯一**的出处是打印设置的纸张规格选项（`print_settings.json:62`，11×17 英寸 Ledger 纸），现在纸张下拉显示「会计账簿」；`Item Type`→物料类别，`main.pot` 唯一出处是导航栏条目类型（`navbar_item.json:31`，选项 Route／Action／Separator）；`Credit Note`／`Debit Note`→红字发票／采购红字发票，同时改到日记账凭证的「凭证类型」选项（`journal_entry.json:109`，演示线环节 13 期初凭证的必填下拉），日记账的贷项／借项通知被叫成「发票」 | DJ-001「已知代价」须列全；需求 §4.2.2 规则 5（占用核查法）；守则「判据必须能区分它要区分的两种情形」 | ① 基线脚本另加「源码出处」索引（扫六 app 源码的 `_()`／json label／Select 选项），供占用核查与撞名判定用，不只靠 `main.pot`；② 按 `hidden_refs.py` 的 27 个键逐条判，意思不对的写 context 行或收回；`Ledger`、`Item Type` 两处不在演示线上，可登记接受 | 新Session修 | 不在演示线上的误伤（纸张规格、导航栏条目）是修还是登记接受 | 待裁决 |
| P5-04 | 低 | `test_translation_quality.py:130-135`、`:152-164` | 守卫判别力的盲区（复制逻辑在 `python -I` 独立脚本测，`guard_probe.py`）：① 四道守卫都先要求译文含汉字，**整句没译**（`Upload Photo`→`Upload Photo`）或英文改写（→`Upload picture`）全部放过；基线的「译文等于源词」只在 Spike 脚本里，不在测试里，改写也查不出。② 台湾用词（简体字形）`伺服器设定`、`请检查网路连线`、`资料库档案` 全部放过，而 DEC-029 把台湾用词算不可用。③ 无空格、无停用词的逐词拼接（`登录带密码`）放过。④ 全大写英文词（`上传 PHOTO`）一律豁免，不只缩写。⑤ `QUALITY_EXCEPTIONS` 按行豁免**全部四道**守卫，不只登记时命中的混排：任一 QE 行的译文里混进「帳戶」，守卫照样放过。当前 csv 没有这几类坏行（本片抽检 80/80、台湾用词表扫描未发现实例），所以是防再犯能力的缺口 | A17「再次批量写入时当场失败」；DEC-029 | ⑤ 最便宜：QE 改成「键 → (守卫名, 理由)」，只豁免登记的那道；② 加一张台湾用词表（「伺服器、网路、资料库、档案、讯息、预设值…」，排除大陆通用词）作第五道守卫；① 在测试里加「本 app 键以外、有汉字源词档之外的译文不得等于源词」，或把基线 identity 判断搬进测试 | 新Session修 | 第五道守卫（台湾用词）要不要加 | 待裁决 |
| P5-05 | 观察 | `test_translations.py:179-181`、`:258-262` | R7 回执「新增约定」：判 csv 键重复时按 Frappe 读法把源词里的字面 `\n` 换成换行再比（`translate.py:203-204`）。Spike 合并与清场脚本做了（`prune.py:66-67`、`baseline.py:66`），测试 `_duplicate_keys` 没做：构造 `[["a\\nb","甲"],["a\nb","乙"]]` 返回 `[]`，而 Frappe 读后两行同键、后者覆盖前者。当前 csv 按归一键查重为 0 | R7 新增约定 | `_duplicate_keys` 的键先 `.replace("\\n", "\n")`，并补一条判别力断言 | 延迟或不修 | — | 待裁决 |
| P5-06 | 观察 | `Spike/P1S6R6-csv-prune.py:96-109`；csv 行来源 | 清场脚本只认 A15 ①②③，第 ④ 类「本轮 TS-019～021 新写的行」在 csv 里没有可机读的来源记号。宿主内存重算：现在重跑会留 318 行、删 5433 行（`own 187／named 59／override 72`）。脚本默认就写盘（`--dry-run` 才不写），注释虽写「只在 TS-018 跑一次」，但没有防重跑。另有 165 行既不在 A15 ①②③ 里，也不在任何 `in-*.json` 分块里（160 行 DJ-001 的 S3 context 行，加 `Book Advance Payments In Separate Party Account`、`CN¥`、`Call Logs`、`Forecasted Sales`、`Options:` 五行），来源只能靠 `git log -S` 追 | A15 可复核性 | 脚本加防重跑（例如检测到 csv 已排序且行数远少于原始即拒跑，或改为默认 dry-run）；以后要再清场，先给第 ④ 类建来源清单 | 延迟或不修 | — | 待裁决 |
| P5-07 | 观察 | `translation_whitelist.py:112`；`translation_overrides.py:54`；`test_named_terms.py:83` | `JAN` 同时登记在 `UNTRANSLATED`（不译）与 `OVERRIDES`／`NAMED_TERMS`（csv 写回原样覆盖官方「01」），三处说法一致、没有冲突，但白名单那条已经多余：键在 csv 里，本来就不算缺口 | 单一来源 | 下次动白名单时删掉这条 | 延迟或不修 | — | 待裁决 |

## 本片盲区自述

- **没有实跑测试**：只读约束加上主会话在跑回归，四道守卫的判别力用复制逻辑在独立脚本里测，测试文件里的用例没有在框架内跑红跑绿。复制时常量从源文件 AST 取（`guard_probe.py`），逻辑是手抄的，若手抄有偏差，P5-04 的个别反例结论会跟着偏。
- **抽检只有我一个人判**：80 条都是本片自己判的，没有第二个读者；术语一致性只对照了宿主合并字典里能查到的词，「意思对」主要看 `in-*.json` 附带的出处前后 3 行源码，没有逐条打开界面看。
- **误伤面只扫了字面量**：P5-01～03 的「隐藏出处」只扫了 `_("…")`／`__("…")` 字面量、json `label` 与 Select `options`。`__(变量)`、服务端拼串、`frappe.db` 取的记录名再译这些动态用法没扫，误伤面可能比 27 个键更大。
- **没往这些方向找**：165 行 context 行的译文质量；R9／R10 新增的 csv 行（只追了 `Master`）；`P1S6R6-screen-check.js` 的选择器与排除规则（属逐屏核片）；`Spike/P1S6R7/merge_check.py` 的合并检查逻辑（只看了它复用 `guard_problems`）。
- **拿不准处**：
  - P5-01 定「中」：工位表单在演示线上，但「关联」页签要演示者主动点开才看得到。如果演示稿不点这个页签，可降为低。
  - P5-02 定「低」还是「中」在边界上：科目名一旦建出就写进库、不会随 csv 回改，语义也确实错；但只发生在 `Standard` 科目表这条非产品路径上，演示公司不受影响，所以取低。
  - P5-03 里日记账「凭证类型」下拉的两项：贷项通知在会计上近似销售侧红字，「红字发票」勉强说得通；「采购红字发票」用来叫日记账类型则偏离较大。算不算误伤，要会计背景的人看。
