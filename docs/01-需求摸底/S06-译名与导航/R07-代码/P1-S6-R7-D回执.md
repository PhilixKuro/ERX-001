# D回执（对象：代码 / 依据：P1-S6-R6-C开发方案）

**轮次**：P1-S6-R7｜**开工**：2026-10-11｜**执行者**：Claude（Opus 5.5；S6 概况偏离：D 步执行者由 CodeX 改为 Claude）
**Spec**：[D-code-plannedDev-build.md](../../../流程体系/workflows/plannedDev/D-code-plannedDev-build.md)｜`打tag=否`
**依据**：[R6 开发方案](../R06-开发方案/P1-S6-R6-C开发方案.md)（TS-016～024）；未被替换部分照 R3 方案（[总纲](../R03-开发方案/P1-S6-R3-C开发方案-总纲.md)＋Part1～4）
**执行前基线**：`frappe_china` HEAD `af015fa`（`docker/apps.json` 锁 `1d51db2`，不一致——IT-001 属 SB）；其余六 app HEAD 与锁一致；`zh.csv` 5966 行；全量 242/242（R5 E 实跑）、Node 29；演示站清洁基准 `20261010_232619`

## 逐项执行结果

| 任务 | 对应切片 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-016 基线脚本可跑、占用脚本改读合并字典、白名单拆模块 | SL-011 | `Spike/P1S6R4-baseline.py:101`（`untranslated()`）、`:110`（`gaps()` 读白名单、出 `whitelisted`）、`:257`（`commits(allow_unlocked)`）、`:277`（参数）；`Spike/P1S6R4-occupancy.py:18`（`occupants()` 读 `merged_dict()`）；`frappe_china/tests/translation_whitelist.py`（新）；`frappe_china/tests/test_translations.py:17,142` | ✅完成 | 2026-10-11 | 基线带开关跑完，`commits.unlocked` 列出 `frappe_china`（`af015fa` ≠ 锁 `1d51db2`）；不带时 `ValueError` 退出码 1（`Spike/P1S6R7-baseline-refuse.txt`）。占用脚本反例：`Stock Ledger`→「物料凭证」报不可用、占用者 `Stock Ledger Entry`（`Spike/P1S6R7-occupancy-proof.txt`）。`test_translations` 9/9 |
| TS-017 质量守卫测试与覆盖清单重建 | SL-011 | `frappe_china/tests/test_translation_quality.py`（新，四守卫 `find_*`、`guard_problems()`、9 用例）；`frappe_china/tests/translation_overrides.py`（重建，218 → 57 条）；`frappe_china/tests/test_translations.py` 交集断言改两差集、`test_override_basis_forms`、`test_basis_form_rejects_garbled_basis`、`_BASIS_FORM:217` | ✅完成 | 2026-10-11 | **未做到先红后绿**：守卫实现与判别力用例在同一次写入里写成，没有先单独跑红（见「偏离与暂停」第 3 条）；判别力用例的预期值取自方案 SL-011 ① 原文给的四个构造坏行，不是照实现反推。首跑时逐词判别力用例里我自加的一条 `是 paid` 断言失败（守卫判它为混排，不判逐词），删去该自加断言，方案原文那条照留。四条判别力＋理由用例 5/5 绿；依据形态与 `ours` 过守卫 2/2 绿。**时序（方案原文）**：此时 csv 批量行仍在，四条全表守卫用例与交集断言预期红——实跑红：全表守卫命中 placeholder 696／traditional 1603／word_by_word 2182／mixed 3095，合计 5370 行；交集断言列出「覆盖了官方但未登记」161 键、「登记了但未覆盖」0。全表通过放 TS-018 验。判定附表 [P1-S6-R7-D附表-覆盖清单判定.md](P1-S6-R7-D附表-覆盖清单判定.md)（留 57／删 161，删的全部因 `ours` 命中守卫或指不出决策） |
| TS-018 csv 清场与排序 | SL-012 | `Spike/P1S6R6-csv-prune.py`（新，`keep_keys()`／`prune()`／`sort_rows()`）；`frappe_china/translations/zh.csv`（5852 → 224 行，全表排序）；`Spike/P1S6R6-pruned.csv`（删除的 5628 行留档）；`frappe_china/tests/test_translations.py` `test_csv_sorted`、`_sort_key`／`_unsorted_pairs` | ✅完成 | 2026-10-11 | 先红后绿：`test_csv_sorted` 先写、对旧 csv 跑红（大量相邻对逆序），清场排序后绿。清场输出 `{"original": 5852, "kept": 224, "own": 154, "named": 30, "override": 40, "dropped": 5628}`（`Spike/P1S6R7/ts018-prune.json`），5628 = 5852 − 224。HT-019 验：删掉的 161 个覆盖键全量核（比方案抽 5 个更严，因随机 5 个全是官方＝源词的符号键、分不出回落与无译文），`clear-cache` 后 `get_all_translations("zh")` 全部等于官方，其中官方为中文的 3 个（`Are you sure you want to log out?`→您确定要退出登录吗？等）也回落正确（`Spike/P1S6R7/ts018-fallback.json`）。测试站 `clear-cache` 后 `test_translations` 12/12、`test_named_terms` 2/2、`test_translation_quality` 9/9 全绿（四道守卫全表通过，SL-011 ① 全表部分在此验过）。基线重跑缺口：frappe 422／erpnext 1841／crm 775／hrms 163／insights 483／raven 1826，**合计 5510**（预期约 5500）；演示面 3052 键、演示撞名 184 组（`Spike/P1S6R7-baseline-ts018.json`） |
| TS-019 演示线定词补齐 | SL-013 | 进行中：`Spike/P1S6R7/s3_write.py`→`s3_rows.csv`（202 行）经 `Spike/P1S6R7/apply_rows.py` 并入 `zh.csv`（224 → 425 行）；`translation_overrides.py` 57 → 100 条；`test_named_terms.py` `NAMED_TERMS` 加 21 条收付款方向＋3 条保留官方（`Settings`／`Paid`／`Unpaid`） | ✅完成 | 2026-10-11 | 附表 [P1-S6-R7-D附表-演示线定词.md](P1-S6-R7-D附表-演示线定词.md)（定词表／占用重查表／撞名判定表）。**第 1～2 步**：465 键分 7 块由子 Agent 译（in-04～07 的子 Agent 与 in-03 曾因 API 额度中断，恢复后续完），每块过 `Spike/P1S6R7/merge_check.py`（占位符／HTML／四守卫／法定列头／重复／缺译）全过后并入；合并时改回 1 条（`Convert to Ledger` 译者改「转换为明细」，偏离官方，改回官方「转换为分类账」）；Excel／WhatsApp／ERPNext 官方即原样，移出 csv 进白名单；`ALLOW` 加 9 个品牌名（WhatsApp、Google、Raven、Jinja、Excel、Frappe、ERPNext、OpenAI、Insights，各写理由）。演示面无中文键重跑剩 40 个，全是编号规则、条码制式等代码值，进白名单。**第 3 步**：见讨论记录第 2 步 DJ-002——200 组中 42 组由 context 行解开，80 组机械同义，59 组逐组判同义，19 组异义写 19 行定词；E 点名的 `Stock Ledger`→库存台账，其余三组已由 S3 改词解开。**第 6 步**：HT-017 成立——测试站 `Accounts Settings` 的 `Role Allowed to over bill `（带尾空格）显示「可超额开票的角色」（`Spike/P1S6R7/ht017-it011/ht017-accounts-settings.png`）；残余缺口里的代码值 120 个进白名单（逐条理由，`Spike/P1S6R7/whitelist_report.json`）。**第 7 步**：IT-011——测试站联系人称谓下拉空查询列出「借方」，搜「借」命中「借方」（`it011-salutation-empty.png`、`it011-salutation-jie.png`）；占用脚本反例见 TS-016。**第 8 步**：`clear-cache` 后三个译名测试模块全过，`translation_check.run` 通过。csv 904 行，覆盖清单 115 条，缺口 4929（全在演示面外，交 TS-021）。**原第 4、5 步记录**：——S3 收付款方向全表与 §2.3 改词组按 DJ-001 落法写入（讨论记录 [P1-S6-R7-D讨论记录.md](P1-S6-R7-D讨论记录.md) 第 1 步），占用重查 7 处命中均判同义或随本轮改词消解（`Spike/P1S6R7/s3_recheck.json`），不写 12 条（原因逐条见 `Spike/P1S6R7/s3_rows.json`）；`Receivable` 由「应收账款」改「应收类」（S3 §2.3.3）。`clear-cache` 后 `test_translations` 12/12、`test_named_terms` 2/2、`test_translation_quality` 9/9。S3 改词实数 75 组（草案记 73，差在 §2.3.4，见 `Spike/P1S6R7/s3_terms.json` `counts.discrepancy`）。**进行中**：第 1～2 步演示面无中文键重跑为 500 个（C 步 527，以 D 重跑为准），其中 35 个是编号规则、条码类型等代码值不译、465 个分 7 块交子 Agent 译（`Spike/P1S6R6-demo/in-01～07.json`）；第 3、6、7 步未开始 |
| TS-020 按钮抽检重做 | SL-013 | 附表 [P1-S6-R7-D附表-按钮抽检.md](P1-S6-R7-D附表-按钮抽检.md)；`Spike/P1S6R7/buttons/`（`build.py`、`buttons.json`）；`Spike/P1S6R7/buttons_apply.py`、`buttons_compare.py`；csv＋8 行、`OVERRIDES`＋4、`NAMED_TERMS`＋9 | ✅完成 | 2026-10-11 | 读码由子 Agent 做（曾因 API 额度中断，恢复后续完）。89 源词入表，每词记全部调用行并追到后端方法定义；「点了即写库」34 个落在 20–40 区间（口径说明见附表头）。E 点名四行重核：`sales_invoice.js:378`／`:402`、`purchase_invoice.js:155` 实为「取物料来源」带入当前单、不建新单，筛出；`work_order.js:944` 是为工单原材料建库存预留，上轮写成「为销售订单预留」对象错，译词「预留」本身对。不一致 11 词：8 词定稿写 csv（`Update Items`→变更明细、`Update Rate as per Last Purchase`→按最近采购价更新单价、`Return / Credit Note`→退货/红字发票、`Return / Debit Note`→退货/采购红字发票、内部／公司间采购发票与采购入库 4 词补译）；`Start`、`Material Transfer` 判「不可分、保留」；`Inter Company Invoice` 源码未包 `__()`，进未做项。`Payment`→收付款依据改记 DEC-035、进 `NAMED_TERMS`。比对脚本在测试站 `clear-cache` 后取合并字典：89 词中 88 词一致，余 1 即 `Inter Company Invoice`。三个译名测试模块全过 |
| TS-021 批量档整批重译与抽检 | SL-012 | `Spike/P1S6R7/batch_export.py`→`Spike/P1S6R6-batch/in-*.json`（19 块）；指令原文 `Spike/P1S6R6-batch/README.md`；合并 `Spike/P1S6R7/merge_check.py`＋`apply_rows.py`，逐块记录 `Spike/P1S6R7/merged/log.txt`；抽检 `Spike/P1S6R4-sample.py`（改种子 20261011、总体读批量档）→`Spike/P1S6R6-sample.out.csv`、`Spike/P1S6R6-sample-review.json`；回扫 `Spike/P1S6R7/sample_fix.py`→`Spike/P1S6R7/sample_backscan.json`；残余清理 `Spike/P1S6R7/gap_cleanup.py`、`drop_batch_overrides.py`；`zh.csv` 最终 5726 行 | ✅完成 | 2026-10-11 | **分块与翻译**：基线取剩余缺口 4898 条，同一源词跨 app 只交一次，代码值不交；按 app 分 19 块（每块 ≤300），12 个子 Agent 分批译（每批 ≤7 个，免再触 API 额度）。各 app 块数与并入条数：frappe 2 块 351、erpnext 5 块 1493、crm 3 块 657、hrms 1 块 129、insights 2 块 473、raven 6 块 1736。**合并**：每块过 `merge_check`（占位符／HTML／四守卫／法定列头／重复／缺译），不过的由主 Session 逐条处置，没有整块退回重译。处置分四类：① 译者为躲守卫删改原文信息的（路径、请求头名、参数名、示例值、品牌名改成泛称），全部恢复原文，逐条进 `QUALITY_EXCEPTIONS` 写理由（该表连同须保留代码／示例值的句子共 39 条）；② 品牌名、产品名进 `ALLOW`（共 44 个，各写理由）；③ 整条源词即品牌名、标识符、示例值的不写 csv，进 `UNTRANSLATED`；④ 个别改词（「节假日表」→官方「假期列表」，`Short-term Investments` 与法定列头同名→「短期投资类」）。**A16 复查**：批量档覆盖官方、且官方值就是源词原样的 15 个键（`Active Directory`、`Slug`、`Sazhen`、数字单位 B／T 等），删行回落官方并进白名单，覆盖清单不再含任何批量档依据的条目。**换行键**：main.pot 从 TSX 抽出的串把 JS 转义换行记成字面 `
`，Frappe 读 csv 时又把源词的 `
` 换成换行，造成两行撞键；csv 留一行，字面键 4 个进白名单写理由，合并脚本按 Frappe 读法判重。**抽检**（SL-012 ④）：总体 4809 条（扣除白名单），按 app 分层 100 条（crm 13／erpnext 30／frappe 7／hrms 5／insights 9／raven 36），由未参与翻译的子 Agent 逐条打开出处、按需求 §4.2.3 三条加 DEC-029 判，每条写理由：**可用 97、不可用 3**（意思错 2、术语 1），≤10，接受。3 条当场改：`Reposting Item and Warehouse`→追溯调整的物料与仓库、`Grand Total must match sum of Payment References`→「…各付款凭据行金额之和」、`Vote Selection`→所选选项。按错误类型回扫：物料成本价追溯调整一族（出处在 `repost_item_valuation`／`stock_reposting_settings`）官方用「追溯调整」，批量档写成「重过账」，同类 15 条改；会计凭证重过账一族官方即「重过账」，不动；「付款参考」「投票选项」同类回扫 0 条。**SL-012 ③**：重跑基线，六 app 缺口合计 **0**，例外只在 `UNTRANSLATED`（228 条）。`clear-cache` 后三个译名测试模块全过，`translation_check.run` 通过 |
| TS-022 逐屏核 v2 脚本与测试站反证 | SL-014 | `Spike/P1S6R6-trad-chars.py`→`.json`（373 字）；`Spike/P1S6R6-visible-text.cjs`＋`.selftest.cjs`（11/11）；`Spike/P1S6R6-screen-check.js`；`Spike/P1S6R6-screens-build.py`→`Spike/P1S6R6-screens.json`（137 屏）＋`Spike/P1S6R6-screens-map.md`；`Spike/P1S6R6-closed-loop.py`（由 R4 造数脚本参数化，站点作参数，状态文件即 values.json）；反证 `Spike/P1S6R6-proof-build.py`→`Spike/P1S6R6-screens-proof.json`、`Spike/P1S6R6-proof-plant.py`，结果 `Spike/P1S6R6-proof/`；侧栏重名 `Spike/P1S6R6-sidebar-dupes.py` | ✅完成 | 2026-10-12 | **脚本**：子 Agent 写出取词、判词与主脚本后过慢，主 Session 停掉它、复核后沿用；屏清单与生成脚本由主 Session 在 R4 的 85 屏上改写，未从零写。**屏清单**（SL-014 ①）：137 屏，按状态 blank 33／saved 36／prefilled 7／dialog 34／list 17／report 10；§4.9 表一 25 行、表二 3 行与确认框 1 行全部有映射，无空行。「由上游创建」7 屏经「创建」菜单点击进入、不用 `set_route`；确认框 29 屏（15 个单据类型提交＋取消，结转凭证只有取消）。**测试站造数**：另建测试公司 `_S6R6 测试公司`，跑通 14 步闭环，另造各单据草稿、已提交且无下游的上游单据、结转凭证与现金流量底稿、CRM 线索与商机（`Spike/P1S6R6-closed-loop-test.json`）。**测试站全屏跑通**（只作脚本可用证据，不作验收）：首跑 137 屏中 104 通过、28 判不通过、5 屏脚本报错；修脚本与清单自身问题（采购单复制带入已收货比例致「创建」菜单不出现，改新建；单号剥离正则写成 Python 普通字符串，`\b` 变退格符，改原始字符串；现有公司屏路由写死演示公司；新建 BOM 无「成本核算」页签；开账跳转菜单项名）后 5 屏报错全部消除。另补 2 行 csv（`Book Advance Payments In Separate Party Account`、`Call Logs`）。**判不通过的分三类**，留待 TS-023 在演示站逐屏处置：① 测试站独有——美国区域自定义字段 `Is customer exempted from sales tax?`（演示站无此字段，已查）、测试站系统语言为英文致 CRM 前端未载入中文词典；② 上游未包 `__()`、csv 不能改的——`filter_list.js:145` 筛选按钮悬停「1 Filter Applied」、`list_view.js:763` 首列排序提示用未译 label、CRM `crm_fields_layout.py:180` 服务端拼的「Add {label}...」占位、frappe-ui `ListFooter.vue:20` 的「of」；③ 用户数据误判（造数前缀、单号、物料价格自动名）。**整链反证**（SL-014 ⑥）：三种失败分开造、分开跑——自有侧栏加英文条目 `Zzproof Entry` → 报 `english: [Entry, Zzproof]`；csv 把「业务流程」临时改繁体「業務流程」→ 报 `traditional: [務, 業]`；表单标题 `title` 设英文 → 报 `title_issues` 1 条（`Save this document`）。每次随即恢复：csv 哈希与造前一致（`2af3a896…`），`git status` 与造前一致，`business_flow.json` 不含 `Zzproof`（造侧栏条目时置 `frappe.flags.in_import`，免得 developer_mode 写回 app json）。**侧栏重名**：测试站返回 `{}`（演示站在 TS-023 跑） |
| TS-023 演示站逐屏核与新基准点 | SL-014 | | ⬜未开始 | | |
| TS-024 全量回归、常驻文件、工作量 | SL-015 | | ⬜未开始 | | |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-016 | SL-011 ④⑤；`run-tests --module frappe_china.tests.test_translations` 全过 | 宿主 `python -I` 跑基线带／不带 `--allow-unlocked`；跑方案原文的占用反例；测试站跑模块 | 带开关跑完、`commits.unlocked` 列出 `frappe_china`；不带时 `ValueError`、退出码 1；占用反例报不可用、占用者 `Stock Ledger Entry`；模块 9/9 |
| TS-017 | SL-011 ①～③（全表守卫放 TS-018 验） | 测试站跑 `test_translation_quality` 与 `test_translations` | 判别力 4 条＋理由 1 条 5/5；依据形态与 ours 过守卫 2/2；全表守卫对旧 csv 红（5370 行命中）；交集断言列出两个差集（161／0） |
| TS-018 | SL-012 ①②⑥；四道守卫对全表通过 | 清场脚本输出各类行数；161 个被删覆盖键全量核回落官方（比方案抽 5 个更严）；测试站 `clear-cache` 后跑三个模块 | 5852 → 224 行，删 5628 = 5852 − 224；161 键全部回落官方；`test_csv_sorted` 先红后绿，并含对调两行的判别力断言；三个模块 12／2／9 全过 |
| TS-019 | SL-013 ①～④、⑥ | 演示面无中文键逐条定词；撞名按渲染点重算后逐组判；S3 收付款方向表落 csv；占用重查；测试站实看 HT-017、IT-011 | 演示面余 40 个代码值进白名单，其余全有译文；撞名 200 组全判（42 组由 context 行解开／139 组同义／19 组异义写定词）；S3 实数 75 组、141 键重查，7 处占用全部消解；HT-017 成立；`Dr` 下拉显示「借方」 |
| TS-020 | SL-013 ⑤ | 读码成表；定稿写 csv；比对脚本在测试站 `clear-cache` 后取合并字典 | 89 词入表（点了即写库 34 个）；88/89 一致，余 1 为 `Inter Company Invoice`（源码未包 `__()`） |
| TS-021 | SL-012 ③～⑤ | 19 块分批译、逐块机检后并入；`SEED=20261011` 分层抽 100 条；独立子 Agent 逐条判；回扫；重跑基线 | 抽检 97 可用、3 不可用（≤10），回扫 15 条；六 app 缺口 **0**，例外只在 `UNTRANSLATED`（228） |

## 全量验证

| 门 | 结果 |
|---|---|
| `frappe_china` 全量（中途，TS-021 后、TS-022 前） | 第一次 253 条中 1 红（`test_website_translation.test_known_entry_uses_wrapper_and_csv`，原因见「偏离与暂停」第 0 条）；恢复 15 行后复跑：integration **253/253 通过**＋导航 **2/2**，合计 **255/255、0 跳过**，耗时 1816 秒（`Spike/P1S6R7/full-regression-mid.log`）。比 R5 E 基线 242 条只增不减（+13，其中 `test_translation_quality` 新增 9、`test_translations` 新增 3；余 1 条未逐条对出来源） |
| Node 用例 | `node --test` 四个 `.cjs`：**29/29**（基线 29） |
| 译名自检 | 测试站 `translation_check.run`：通过 |
| 最终全量（TS-024） | 待跑 |

## 偏离与暂停

0. **TS-018 清场误删 15 行，TS-021 后的中途全量回归查出**（`Spike/P1S6R7/full-regression-pre.log`：253 条中 1 条红，`test_website_translation.test_known_entry_uses_wrapper_and_csv`）。A15 ① 的「本 app 自有源词」按 `_app_source_strings()` 取，只认 `_()`／`__()` 调用、DocType label 与 Select 选项；而 `website_translation.SOURCES` 元组、`independent_app_labels.js` 的 `Set`、`desk_patches.js` 的 `translate('Filter based on {0}', …)` 都按字面量键取用，不经 `_()`，故被判为批量行删掉。它们是 R4 TS-014（DEC-026／027）独立前端与悬停提示适配所需的键，清场前已有译文。处置：`Spike/P1S6R7/prune_regression.py` 扫删除留档里以引号字面量出现在本 app 代码中的键，得 15 个（另 7 个是 Python 运算符与纸张规格名、非译名键，不恢复），从 `Spike/P1S6R6-pruned.csv` 原样恢复（依据 DEC-026），复跑 `test_website_translation` 3/3 与三个译名模块全过。**方案层面的缺口**：A15 ① 的取法漏了「本 app 以字面量按键取用」这一类，`_app_source_strings()` 未改（改它属改既有测试判据），供 E 判是否补进取法。

1. **TS-017 依据形态补一种「本 app 自有源词」**。方案 SL-011 ③ 只列四种形态（`DEC-0xx`／`S3 术语标准 §x.x`／`演示线撞名`／`按钮抽检 IT-010`），但 A15 ① 本 app 自有源词里有 2 条覆盖官方：`Formula`（cn_tax 字段 label，又是 S5 装序检查的探针源词 `install.PROBE_SOURCE`）、`Yearly Amount`（为避开法定列头「本年累计金额」，S4 LG-134）。二者都无 S6 决策号，按四种形态只能删，删了 `Formula` 会打掉 S5 的装序检查。判为方案漏列一类、不属重做决定：`_BASIS_FORM` 加第五种 `本 app 自有源词`，二者保留（`test_translations.py:217`）。供 E 复核时判是否可接受。
2. **TS-017 「留」的依据映射**：方案第 2 步表的「能指出决策」四类，D 步按以下写进 `basis`——`Timesheet` 全族 → `DEC-016`；`NAMED_TERMS` 的键 → 各自决策号（`Dr` DEC-003／022、`Setup` DEC-019、`Payment References`／`Payment Entry Reference` DEC-014、`Cash Flow` DEC-015、`Closed Date`／`Create Chart Of Accounts Based On` DEC-021、`Accounts Receivable`／`Debtors`／`Receivable` S3 术语标准 §2.3、`Agents`／`Bot`／`Create Quotation`／`Add Row`／`Opening & Closing` DEC-001（需求 §4.2.2 必改条目））；R4 TS-014 的 11 条 → `DEC-026`。C 回执「拿不准处」第 2 行已指出 DEC-026 没有逐条过目，照方案保留。删去的 161 条中，154 条因 `ours` 命中守卫；7 条过守卫但指不出决策（`21:00`、`Frappe CRM`、`Lft`、`Outlook.com`、`Sazhen`、`Sendgrid`、`Verdana`），csv 该行在 TS-018 删掉、回落官方。
3. **TS-017 未守 atdd 先红后绿次序**：`test_translation_quality.py` 的守卫函数与判别力用例一次写成。补救：判别力用例的预期值全部取自方案 SL-011 ① 原文；全表守卫用例对当前 csv 实跑为红（5370 行命中）、TS-018 清场后转绿，这一段是真实的红到绿。此后各任务先写测试、跑红，再写实现。

## 新增约定

| 约定 | 类别（命名/位置/错误处理/依赖/跨层调用） | 在哪个任务确立 |
|---|---|---|
| 原样显示、不译的源词一律进 `frappe_china/tests/translation_whitelist.py` 的 `UNTRANSLATED`（键 → 理由），测试与基线脚本共读这一份；该文件不得 import frappe | 位置 | TS-016 |
| 译文里允许保留的英文词（品牌、产品、格式名）进 `test_translation_quality.ALLOW`；必须保留源词中代码、路径、示例值的整句进 `QUALITY_EXCEPTIONS`；两表每项必须写理由，测试断言理由非空。**不得为了过守卫删改原文信息** | 错误处理 | TS-017／TS-021 |
| 覆盖官方的 csv 行，`translation_overrides.py` 的 `basis` 只取五种形态（`DEC-0xx`／`S3 术语标准 §x.x`／`演示线撞名`／`按钮抽检 IT-010`／`本 app 自有源词`），测试断言 | 命名 | TS-017 |
| csv 全表按（源词不区分大小写，context）排序，不分段；写回用 `csv.writer(lineterminator="
")` | 位置 | TS-018 |
| 判 csv 键是否重复时，按 Frappe 读 csv 的方式（`translate.py:203`，源词里的字面 `
` 换成换行）归一后再比 | 错误处理 | TS-021 |
| 批量档不覆盖官方（A16）；官方有意保留原文的键，csv 不写，进白名单 | 依赖 | TS-021 |

## 未做项

| 项 | 为什么没做 |
|---|---|
| erpnext 按钮 `Inter Company Invoice`（`purchase_invoice.js:228`）仍显示英文 | 源码 `add_custom_button("Inter Company Invoice", …)` 未包 `__()`，csv 写什么都不生效；改上游源码违反开发守则「扩展优先用 hook」，前端补丁方案未要求，不夹带。登记供 E 判（候选：`frappe_china` 前端按 ADR-0009 补丁包一层 `__()`） |
| erpnext 源词 `Naming series '{0}' for DocType '{1}' does not contain standard '.' or '{{' separator. Using fallback extraction.` 未译（暂进 `UNTRANSLATED` 并写明原因） | 源词含未闭合的 `{{`，`test_translations._PLACEHOLDER`（`\{\{?\s*[^{}]+\s*\}?`）把它到句末整段当成一个占位符，任何中文译文都过不了占位符一致检查。修正则属改既有测试判据，方案未要求，不夹带；登记供 E 判（建议：正则改为要求闭合括号） |

## 状态值

## 复核建议
