# SB修复回执（对象：代码 / 依据：P1-S4-R14-F审核报告 ＋ P1-S4-R7 开发方案）

**轮次**：P1-S4-R14｜**日期**：2026-10-02｜**步骤**：`plannedDev` SB（build）｜**执行者**：Claude（Opus 5.5）｜`打tag=否`
**Round 归属**：`附属=新Session做`（步骤表 SB 行原值）——本次只做 R14 F 报告裁为 `新Session修` 的 11 项，是 R14 F 那个工作项的一部分，**不占 Round**，沿用 R14。与 R10／R11（承接前一份 SB 回执的未做项、另起工作项）不同。
**依据**：[F审核报告](P1-S4-R14-F审核报告.md)（含 Part1～4 分片报告的原条目）＋[开发方案总纲](../R07-开发方案/P1-S4-R7-C开发方案-总纲.md)／Part1–4
**用户裁决**（2026-10-02，见 F 报告「用户裁决」）：「1、按建议来。…」——各项取报告的建议档位与建议修法；待裁决点未逐项答复的，取报告建议。
**范围外不动**：`本Session修` 15 项（F 步已修）、`出方案修` FD-004／FD-007（等 C 步）、延迟 15 项。

## 逐项执行结果

| 任务 | 报告项号 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| 按实际目录名取 app 名、锁定判断用实际目录、私有仓库凭据说明 | FD-009 | `docker/scripts/setup.sh` 第 3 段；`docker/apps.json`（三条都加 `app_name`）；`docker/lock-apps.sh`（写入 `app_name`＝目录名）；`docker/README.md`「源码在哪、怎么管版本」节＋新增「私有仓库」小节 | ✅完成 | 10-02 | 取报告建议「在 apps.json 加 `app_name` 字段」：存在判断与锁定判断都用它，缺省退回仓库名。**另去掉 `--resolve-deps`**：报告「把握最低处」点到的第三条失败路径已读码证实——bench `install_resolved_deps` 遇到已装的 erpnext 会 `click.confirm`，容器内实测无输入时 `Abort`，答 y 则 `rmtree` 整个 erpnext 目录；`apps.json` 本就按装载顺序列全，不需要依赖解析。克隆前先 `ls-remote` 探一次，访问不了就响亮失败并指向 README。待裁决点「仓库是否本就打算私有」：未改仓库可见性（属用户决定），按现状（未登录 API 返回 404、`ls-remote` 要用户名，故判为私有）写凭据办法。**未跑 `up.sh`**（会碰演示站），改为抽出第 3 段在临时目录实跑，见「复验结果」 |
| 带账簿的损益分录挡住 | FD-013 | `accounting/closing.py` `_assert_no_finance_book_pl`（生成入口、在「上月未结」检查之前调用）；`translations/zh.csv` +1；`tests/test_closing.py` `test_finance_book_pl_entries_block_closing` | ✅完成 | 10-02 | 取待裁决点的建议「本 Stage 不支持账簿、报错挡住」。范围取本年初至本月末的损益类 GL（与损益结转取数范围相同），报错列出账簿名。只有资产负债类科目带账簿时不拦（测试有判别用例）。`gl_sums` 的空账簿口径未改 |
| 不可变总账开启时挡住生成与取消 | FD-014 | `accounting/closing.py` `assert_mutable_ledger`（`generate_month_end_closing`／`cancel_month_end_closing` 开头）；`month_end_closing_voucher.py` `before_cancel`；`translations/zh.csv` +1；`tests/test_closing.py` `test_immutable_ledger_blocks_generate_and_cancel` | ✅完成 | 10-02 | 按报告建议「入口检查该开关，开启时明确报错」。另把单张取消（表单「取消」按钮走 `before_cancel`）也算一个入口，否则绕得过去。开关判据用上游 `is_immutable_ledger_enabled()`。报错引用官方译名「启用不可篡改账本」「会计设置」 |
| ≥ 式误报与说明行列名 | FD-017 | `statements/engine.py` `check()`（新增可选参数 `column`）；`balance_sheet.py`（期末余额／年初余额）、`profit_and_loss.py`（本年累计金额／本月金额或上年金额）；`tests/test_mapping.py` `test_check_notes_name_the_column_and_soften_signed_rows`；`tests/test_statement_dataset.py` `assertChecksPass` | ✅完成 | 10-02 | 取报告建议的第二种：≥ 式**只在涉及的各行都不为负时**判「勾稽不符」，有负数行时降为「勾稽提示」（不说是错）。原文勾稽式本身不动（`BS_CHECKS`／`PL_CHECKS` 与 R12 钉住的集合相同）。说明行改中文并带列名，如「本月金额：勾稽提示：第 18 行 -400.00 小于其中项第 19 行之和 100.00；…」。`assertChecksPass` 原来靠 `!=` 判，改为判「勾稽」两字，否则新措辞会让它恒过 |
| 附加税分摊按借减贷净额 | FD-018 | `statements/engine.py` `allocate_surtax`；`tests/test_profit_and_loss.py` `test_surtax_reversal_reduces_detail_rows` | ✅完成 | 10-02 | 按报告建议：每张凭证取 `5403` 借减贷净额；净额为正按同凭证税种明细的贷方分摊，为负按借方反向冲减。未分摊说明行带符号。测试：计提 100（70／30）后冲回 20（14／6）→ 第 3／6／10 行 80／56／24，无勾稽说明 |
| 组科目无明细、`exclude` 号不校验 | FD-019 | `statements/engine.py` `resolve()`、`_source_value()`；`statements/unmapped.py` `_covered_accounts`；`tests/test_mapping.py` `test_resolve_rejects_empty_group_and_bad_exclude`、`_covered` | ✅完成 | 10-02 | `resolve` 同时解析 `numbers` 与 `exclude`；号不存在、组下无明细两类一次收齐报出（新词条「以下科目号下没有任何明细科目」）。**连带**：`resolve` 的返回值现在含 exclude 号，两处「把 resolved 全部值当覆盖」的调用（漏科目检查、覆盖测试）改为只取 `numbers`，否则 `2221000` 等被排除的明细会被当成已覆盖 |
| 现金流明细方向与公式行校验 | FD-021 | `cn_tax/doctype/cash_flow/cash_flow.py` `_validate_items`、`_assign_default_codes`、新增模块函数 `_direction_fits`；`translations/zh.csv` +2；`tests/test_cash_flow.py` `test_item_code_direction_and_formula_rows_are_validated`、`test_party_type_fallback_prefills_code` | ✅完成 | 10-02 | 取报告建议「validate 里加两条」，校验放后端（界面与脚本都挡得住）：① 明细行不得选公式行（小计、期初、期末），一次列出行号；② 借方行只能选流入项目、贷方行只能选流出项目（**草案·待专家确认**）。**连带**：预填（科目 → 对方科目 → 往来单位 → 默认往来类型）改为跳过方向不符或是公式行的候选，否则预填出来的代码会被新校验拒绝；都不符就留空。原 prefill 测试里供应商、员工两行用借方，与它们的流出项目方向相反，改为贷方，另加「收回供应商退款不预填」一行 |
| 合计行判据与金额格式 | FD-023 | `accounting/bank_import.py` `DEFAULT_SUMMARY_KEYWORDS`、`_PLAIN_DECIMAL`、`_parse_amount`、`_parse_statement_rows`；`bank_statement_format.json`（`summary_keywords` 默认值，`modified` 后移）；`tests/test_bank_preprocess.py` `test_summary_row_rule_does_not_swallow_real_rows`、`test_amount_accepts_only_finite_plain_decimals`、`statement_format()` 默认值 | ✅完成 | 10-02 | 取报告建议：① 只有**日期格**含关键字、且该行**没有流水号**时才当合计行跳过；默认关键字去掉单字「共」（待裁决点「是否保留共」取建议：不保留）。② 金额文本只收普通十进制数（拒 `NaN`、`Infinity`、科学计数法），落到原有的「金额无效」报错；xlsx 的数字格另走一支，浮点经 `repr` 转、非有限值拒收。已建的格式记录不改（两站 `Bank Statement Format` 都是 0 条）。测试站已 migrate |
| 预处理失败留痕 | FD-024 | `accounting/bank_import.py` `_mark_failed`、`_persist_failure`（两处 Failed 分支共用）；`tests/test_bank_reconcile.py` `test_failed_preprocess_survives_request_rollback` | ✅完成 | 10-02 | 取报告建议的第一种「失败分支独立提交留痕」（待裁决点「要不要留痕」取建议：留）。做法：事务内照旧 save，另登记 `frappe.db.after_rollback` 回调，请求回滚后单独 `set_value` 并提交；调用方若吞掉异常再提交，commit 会清掉这个回调。没在抛错前直接 commit，因为那会把本请求里此前的写入一并提交。测试用 savepoint 模拟一次请求：回滚后断言回到 Draft，跑回调后为 Failed 且 log 含行号 |
| `restore.sh` 可选时间戳（项目概况那半随 S4 收口） | FD-027 | `docker/restore.sh`（可选参数 `<时间戳>`）；`docker/README.md`「日常用法」表、结构树、「重装站点」节 | ⚠️部分（按裁决） | 10-02 | 只做 `restore.sh` 这一半。带时间戳时在 `backups/` 根目录与各子目录（`保留-*`）里找，找不到就列出全部可用时间戳；不带参数时行为不变。子目录名含中文，传进容器的路径用单引号包住。项目概况三节（`frappe_china`「待创建」、「能力」「数据模型」）按待裁决点建议**留到 S4 收口时的常驻文件全量逐出再改**，本步不动常驻文件。项目概况第 67 行「须显式指定」现在与脚本对得上了 |
| 仓库科目与物料组科目缺项报错 | FD-028 | `accounting/company.py:93-170`（新增 `_throw_missing_accounts`，三段共用）；`tests/test_company.py` `test_missing_warehouse_or_item_group_account_is_reported` | ✅完成 | 10-02 | 两段都改为先查全部科目号、收齐缺项一次报错，**通过后才写**；报错句与默认科目那段相同。缺的物料组本身仍按原方案只记 warning（不是本项范围）。`test_company` 9/9 |
| 全量回归 | — | `bench --site test.localhost run-tests --app frappe_china`（日志 `frappe-bench/logs/r14-sb2-full.log`） | ✅完成 | 10-02 | 137/137，见「全量验证」 |

## 复验结果

| 报告项号 | 报告的判定标准 | 怎么复验的 | 实测结果 |
|---|---|---|---|
| FD-009 | 按 `apps.json` 重建能锁到指定 commit；重跑 `up.sh` 不失败；私有仓库有凭据办法 | 未跑 `up.sh`（会碰演示站）。把 `setup.sh` 第 3 段**原样抽出**，在容器临时目录 `/tmp/fd009` 里执行：仓库用本地裸仓库 `FrappeChina.git`（仓库名与 app 名不同，同真实情形），`bench get-app` 换成一个按 pyproject 改目录名的假函数（同 bench `utils/app.py:get_app_name`），并断言它不再收到 `--resolve-deps`。四种情形：① 新机器；② 重跑；③ 旧写法（无 `app_name`）；④ 访问不了的仓库 | ✅ ① 克隆、改名为 `frappe_china` 后锁到指定的 `40200dc`；② 重跑 get-app 调用次数仍为 1，不中止；③ get-app 后报「找不到 apps/FrappeChina…app_name 与 pyproject name 不一致？」并退出；④ 报「容器内访问不了…见 README『私有仓库』节」并退出。临时目录与脚本已删。私有性：未登录 `api.github.com/repos/PhilixKuro/FrappeChina` 返回 404，无凭据 `ls-remote` 要用户名 |
| FD-013 | 带账簿的损益 GL 不再被静默漏结 | `test_finance_book_pl_entries_block_closing`；变异 M1 | ✅ 报错并列出账簿名、不生成凭证；只有资产负债类科目带账簿时照常结转。M1（去掉检查）测试失败 |
| FD-014 | 不可变总账开启时入口明确报错 | `test_immutable_ledger_blocks_generate_and_cancel`（patch 开关为 1）；变异 M2 | ✅ 批量生成、批量取消、单张取消三处都报「不支持不可篡改账本」，凭证仍为已提交；关掉后照常取消。M2 失败 |
| FD-017 | 汇兑收益较大时 `18>=19` 不误报为错误；说明行写清列名 | `test_check_notes_name_the_column_and_soften_signed_rows`（推演 D 原数）；变异 M3；两年数据集 15 项 | ✅ 推演 D 得「本月金额：勾稽提示：…涉及以「-」号填列的行，不一定是错误」；各行非负时仍为「勾稽不符」；等式也带列名。M3（不分负数行）失败。数据集上无任何勾稽说明 |
| FD-018 | 红字冲回附加税时明细同步减少、`3>=4+…+10` 不误报 | `test_surtax_reversal_reduces_detail_rows`；变异 M4 | ✅ 计提 100 冲回 20 → 80／56／24，无勾稽说明。M4（只看借方）失败 |
| FD-019 | 组科目无明细、`exclude` 错号都报错 | `test_resolve_rejects_empty_group_and_bad_exclude`；变异 M5；`test_mapping` 覆盖与重复覆盖测试、`test_unmapped` 4 项 | ✅ 空组报「下没有任何明细科目：1199」；错号 `777777` 列进缺号，正确的 `2221000` 不列。M5 失败。覆盖与漏科目检查结果不变 |
| FD-021 | 方向不符、选公式行都被拒 | `test_item_code_direction_and_formula_rows_are_validated`、`test_party_type_fallback_prefills_code`；变异 M6、M7；数据集 15 项 | ✅ 贷方行选 1、借方行选 16、明细选 7 各报对应行号；改正后提交通过、期末 70。预填跳过方向不符的候选。M6、M7 都失败。数据集逐月底稿照常提交 |
| FD-023 | 日期写错且摘要含关键字的真实明细不被吞；`NaN`／`Infinity`／`1e5` 按金额无效报出 | `test_summary_row_rule_does_not_swallow_real_rows`、`test_amount_accepts_only_finite_plain_decimals`；变异 M8、M9；原有 7 项预处理测试 | ✅ 三条坏明细都报日期错误，真正的合计行仍跳过；9 种非法金额文本都返回 None，原有带 ¥／千分位的写法照常解析。M8、M9 失败 |
| FD-024 | 经界面调用时 Failed 与 log 落库 | `test_failed_preprocess_survives_request_rollback`；变异 M10 | ✅ savepoint 回滚后为 Draft、log 空（即改前症状），跑 after_rollback 后为 Failed、log 含「第 2 行：日期」。M10（不登记回调）失败。**未经真实 HTTP 请求验证**，见复核建议 1 |
| FD-027（脚本那半） | 子目录里的基准备份用脚本恢复得到 | `bash -n`；`echo n \| restore.sh <时间戳>` 三种：子目录里的、不存在的、不带参数 | ✅ `20261001_110222` 解析到 `保留-S4清站前/` 下的三件套；不存在的列出 14 个可用时间戳；不带参数仍取根目录最新。拼好的含中文路径在容器内 `ls` 到同一文件。**未真跑恢复**（会覆盖演示站） |
| FD-028 | 查不到科目号时报错，不写 NULL | `test_missing_warehouse_or_item_group_account_is_reported`；变异 M11 | ✅ 仓库、物料组两种缺号各报出「仓库=号」「物料组=号」，公司回滚不存在。M11 失败 |

**变异实跑 11 组**（`tmp_r14_sb_mut/mut.py`：逐组植回原缺陷 → 只跑对应测试 → 按原字节还原并校验 sha256；摘要 `frappe-bench/logs/r14-sb2-mut-summary.json`）：**11/11 按预期失败**。跑完 app 工作区仍是同样的 19 个改动文件，临时目录已删。FD-009、FD-027 是脚本，不在变异范围，判别力靠上面的情形实跑。

## 全量验证

| 门 | 结果 |
|---|---|
| `run-tests --app frappe_china` | **Ran 137 tests in 402.267s, OK**（＝F 步后 127＋本步新增 10：`test_company` 1、`test_closing` 2、`test_mapping` 2、`test_profit_and_loss` 1、`test_cash_flow` 1、`test_bank_preprocess` 2、`test_bank_reconcile` 1）。只增不减。跑后测试站残留同 F 步口径 |
| ⚠ 第一次全量 | **135/137，2 项失败**（`test_cash_flow` 两项）。原因是我自己：全量回归在后台跑时，我为了拿 Ruff 基线做了 `git stash`／`stash pop`，那几秒里工作区退回了改前代码，恰好落在这两项上。stash 已完整还原（19 个文件、diff 不变）；之后什么都不碰、重跑一次即 137/137。日志被重跑覆盖 |
| Ruff（F823／F821／F841／E9，同 F 步口径） | `All checks passed!` |
| Ruff 全规则 | 873 条（改前 699）。增加的 174 条全是 RUF001～003 全角标点（新写的中文注释与报错），I001、B905、RUF059 条数不变。FD-029 已判延迟（忽略 RUF001～003 的配置在那项里做）。另 F401 未用导入 7 条均为改前已有，本步新加的导入都有使用 |
| 测试站 migrate | 已跑（`Bank Statement Format` 默认值改动需要）。**演示站未 migrate**：本步唯一的元数据改动是该默认值，演示站该 DocType 0 条记录；Python 改动对演示站即时生效（同一份 bench 代码） |

## 偏离与暂停

- **无暂停项**：11 项的报告建议与原方案没有冲突。几处待裁决点用户未逐项答复，按 F 报告「用户裁决」那条（「按建议来」、未答复的取报告建议）取了建议，各行「说明」列已写明取的是哪一种。
- **FD-009 多做了一处**：去掉 `--resolve-deps`。报告建议里没写，但报告 Part4「把握最低处」明说那是第三条失败路径、未验证；本步读 bench 源码并在容器里实测 `click.confirm` 无输入即 `Abort`，确认它成立。不去掉，重跑 `up.sh` 照样中止，等于这项没修好。
- **FD-021 连带改了预填**：加了方向校验后，原预填会预填出方向相反的代码再被自己拒绝，故预填改为跳过方向不符的候选。原 prefill 测试的两行数据随之改了借贷方向。
- **FD-019 连带改了覆盖口径**：`resolve` 的返回值现在也含 `exclude` 号，两处把它整体当覆盖的地方改为只取取数号。
- **执行中出的一处差错**：见「全量验证」第二行。

## 新增约定

| 约定 | 类别（命名/位置/错误处理/依赖/跨层调用） | 在哪个任务确立 |
|---|---|---|
| 经界面调用、抛错后整个请求会回滚的写操作，要留失败痕迹时：事务内照常写，另登记 `frappe.db.after_rollback` 回调在回滚后单独补写并提交（`bank_import._mark_failed`）。不在抛错前 commit | 错误处理 | FD-024 |
| `docker/apps.json` 每条带 `app_name`＝`frappe-bench/apps/` 下的目录名，顺序即安装顺序；`setup.sh` 不让 bench 解析依赖。`lock-apps.sh` 自动写入 | 依赖 | FD-009 |
| 本 app 不支持的站点级开关（不可篡改账本、账簿）在**每个入口**明确报错挡住，包括表单上的单张取消，不在取数里静默忽略 | 错误处理 | FD-013、FD-014 |

（`plannedDev` 长效信息表只规定 D 步的约定移交 `开发守则.md`。这三条是否移交，由收尾时定，本步不改常驻文件。）

## 未做项

| 项 | 为什么没做 |
|---|---|
| FD-027 项目概况三节 | 按待裁决点的建议，随 S4 收口时的常驻文件全量逐出再改（中枢第 8 步⑤） |
| FD-009／FD-027 的真机实跑（`up.sh`、真恢复） | 两者都会写演示站；已用抽出脚本段与 dry run 代替，见复验结果 |

## 状态值

**`修复已落地`**。F 报告裁为 `新Session修` 的 11 项全部改完并按报告判定标准复验通过（FD-027 按裁决只做脚本那半），全量回归 137/137，变异 11/11。按出口路由「SB · 修复已落地 → 回唤起方（F）复核」。

**但 F 复核还不能马上起**：F 报告的另一路 `出方案修`（FD-004、FD-007）还没走——要先回 C 步改方案、D 执行，两路都完成后再一并回 F 复核（S4 概况「下一步两路」）。

## 复核建议

1. **修得最勉强的是 FD-024**：`after_rollback` 补写是靠「frappe 在请求异常后调 `db.rollback()`、rollback 会跑这个回调」这条路径（`frappe/app.py` 的 except 分支、`database.py:rollback`）。测试用 savepoint 加手动跑回调来模拟，**没有经过真实 HTTP 请求**。查法：在测试站另起 6787 服务（同 R11 做法），上传一份日期写错的 csv，点「预处理并导入」，弹窗报错后刷新单据，看状态是不是「Failed」、log 是否有内容。
2. **修复的连带影响**（报告项之外动到的调用点）：
   - FD-017 改了两张报表全部勾稽说明的措辞（`!=` 式改为中文带列名）。S6 译名若引用旧措辞会受影响；`test_statement_dataset.assertChecksPass` 已同步改判据。
   - FD-019 让 `resolve` 也解析 `exclude` 号，`unmapped._covered_accounts` 与覆盖测试跟着改。
   - FD-021 改了现金流底稿的预填顺序（跳过方向不符的候选）。会计如果习惯「先预填、再改」，现在部分行会留空。
   - FD-009 改了 `setup.sh`、`lock-apps.sh` 与 `apps.json` 的格式。旧格式的 `apps.json`（没有 `app_name`）在 `frappe_china` 这一条上会响亮失败，而不是像以前那样静默跳过。
3. **拿不准处**：
   - FD-021 的方向约束是草案、待专家确认。F 报告 Part4 提到可能有合法的反向情形（如退款冲减流入）。现在这种情形会被拒；若专家确认要支持，需要改成按项目放行，而不是取消校验。
   - FD-017 的「≥ 式涉及负数行只出提示」是会计口径推断。原文第 19 行明写「收入以“-”号填列」，据此判断上级行小于其中项可以是合法的；但其它 ≥ 式（如 `9>=10+…+13` 存货）出现负数时是否同样只该提示，没有依据，现按同一规则处理。
   - FD-009：仓库可见性按「未登录访问 404」判为私有。若其实是想设为公开，README 那节可以删掉，`ls-remote` 探测照样有用。
