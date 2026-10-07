# SB回执（对象：代码 / 依据：[R9 F审核报告](P1-S5-R9-F审核报告.md) 裁为 `新Session修` 的 3 项 ＋ [R3 开发方案](../R03-开发方案/P1-S5-R3-C开发方案-总纲.md)／[R6 开发方案](../R06-开发方案/P1-S5-R6-C开发方案.md)）

**轮次**：P1-S5-R9（附属，不占 Round）｜**日期**：2026-10-07｜**执行者**：Claude（Opus 5.5；用户指定，不用 Workflow 预设的 CodeX）
**状态值**：`修复已落地`（FD-008／009／017 全部完成并复验通过；全量 209/209）

**开工前裁决**（2026-10-07，用户按建议）：FD-009 只补日志与 README，接受 DEC-027 的边界，不收窄判定。FD-008 先答「自检同口径一并改」；探针（见「偏离与暂停」第 1 条）实测复制建账公司按现自检报不过，暂停反馈后用户改判：**自检不改，口径不一致并入 Phase 登记册 PH-P1016**，本项只改回填。

## 逐项执行结果

| 任务 | 报告项号 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| 回填改用 `is_cn_company` | FD-008 | `frappe_china/accounting/hr.py:72-80`（`backfill_cn_expense_claim_accounts`；`:6-11` 改为从 `company` 导入 `is_cn_company`、去掉不再用的 `CN_CHART_NAME`）；`tests/test_expense_claim.py:72-92` 新增 `test_2b_after_hrms_install_backfills_existing_company_copy`；`tests/test_hr.py:40-57` 原 `test_backfill_only_visits_chinese_chart_companies` 改为 `…_chinese_companies` | ✅完成 | 2026-10-07 | 按改判只改回填；自检 `check_all_cn_companies` 未动，口径不一致补进 [P1 概况](../../P1-概况.md) 登记册 PH-P1016 行。`test_hr` 原用例断言的正是旧筛法（`get_all(filters={"chart_of_accounts": …})`），随修法改为断言「判中式公司交给 `is_cn_company`」 |
| `repoint` 删通用科目打日志，README 补已知限制 | FD-009 | `frappe_china/accounting/hr.py:125-128`（删除成功分支加 `logger.warning`）；`tests/test_company_hr_lifecycle.py:304-322` 新增 `test_sl012_6_1b_deleted_generic_account_is_logged`；`frappe_china/README.md:144`「已知限制」报销那条 | ✅完成 | 2026-10-07 | 按裁决接受 DEC-027 边界，判定不收窄。README 补的是：删掉与保留都记 warning；判「通用」只看科目号为空，报销类型不要指向无号科目，否则保存公司时被改挂、无凭证无链接时科目被删 |
| 配置脚本先做只读预检 | FD-017 | `docker/scripts/configure_apps.py:8-9`（模块说明）、`:145-157`（`configure_crm` 改收已解析的公司）、`:192-193`（`configure_raven` 去掉只设一个的报错）、`:215-241`（`ensure_bot_and_functions` 去掉写类工具检查）、`:271-286` 新增 `preflight`、`:309-315` `main` 先调 `preflight` 再写 | ✅完成 | 2026-10-07 | 取报告第一种做法「写类工具检查挪到最前面做只读预检」，并把同类的两项一并前移：公司解析（零家／多家／不存在）与 `URL`／`KEY` 只设一个。三项报错文字、退出码不变。改动前的副本留证 `docs/01-需求摸底/Spike/P1-S5-R9-SB-FD017-configure_apps.before.py` |

## 复验结果

| 报告项号 | 报告的判定标准 | 怎么复验的 | 实测结果 |
|---|---|---|---|
| FD-008 | 回填改用 `is_cn_company` 判；补一例「复制建账公司 + 装 HRMS」 | 测试站跑 `test_expense_claim`、`test_hr`；变异：把回填的判据换回 `chart_of_accounts == "小企业会计准则(2024)"`，跑 `test_expense_claim` 后还原 | 8/8、3/3 通过。变异下只有新例 `test_2b` 失败（复制公司 `eca_rows` 为空），其余 7 例照过，即旧用例确实区分不出、新例能区分；还原后 `grep` 核回 `is_cn_company` |
| FD-009 | 删除时打 warning；README「已知限制」补一句 | 测试站跑 `test_company_hr_lifecycle`；变异：删掉新加的 `logger.warning` 一行，只跑 `test_sl012_6_1b` 后还原；读 README 第 144 行 | 16/16 通过。变异下 `test_sl012_6_1b` 失败（`warning` 调用列表为 `[]`），还原后通过；README 已写明「判通用只看无号」「不要指向无号科目」「会被删」「记 warning」四点 |
| FD-017 | 把写类工具检查挪到最前面做只读预检（或每段写完立即打印）；开发守则「不静默」 | 探针 `Spike/P1-S5-R9-SB-FD017-probe.py`：测试站先建一条 `Delete Document` 类工具、把 `ERPNext CRM Settings.sync_products` 置 0（让 CRM 段有待写字段），再分别对改前副本和现脚本调 `main()`，钩住 `Document.save` 与 `sql_ddl` 计数，之后恢复两处。另跑常规与两条异常路径：`configure-apps.sh --site test.localhost`、`--company 不存在的公司`、只设 `RAVEN_LLM_URL` | 改前：rc=1，报「已有写数据类…」，但 `ERPNext CRM Settings` 已 save 1 次，**报错前已写**（站上无须建字段，所以这次没触发 DDL、rollback 撤得回；首跑建字段时就撤不回，与报告读码一致）。改后：rc=1，同一报错，`save` 0 次、`sql_ddl` 0 次。常规路径「无改动」rc=0；两条异常路径分别报「公司 不存在的公司 不存在」「RAVEN_LLM_URL 与 RAVEN_LLM_KEY 须同时设置」。探针结束后写类工具已删、`sync_products` 恢复 1 |

## 全量验证

| 门 | 结果 |
|---|---|
| 全量 `bench --site test.localhost run-tests --app frappe_china`（`frappe-bench/logs/s5-r9-sb-regression.log`，2026-10-07） | **Ran 209、OK、`EXIT=0`**，耗时 985 秒，209 条全 ✔、0 ✖。对比 R9 F 审核修后基线 207：只增不减（+1 `test_expense_claim.test_2b`、+1 `test_company_hr_lifecycle.test_sl012_6_1b`） |
| 专项 | `test_hr` 3/3、`test_expense_claim` 8/8、`test_company_hr_lifecycle` 16/16 |
| Lint（Ruff 0.14.10 `--select F,E9 --ignore F401`，临时装进 `.claude/tmp-ruff`、用完删，同 R9 F 审核的做法） | 本次改动的 4 个 app 文件＋`configure_apps.py`＋探针：`All checks passed!` |

## 偏离与暂停

1. **FD-008 改判**：用户开工前先答「自检同口径一并改」。改之前我先跑了探针 `Spike/P1-S5-R9-SB-FD008-probe.py`（测试站，事务内建源公司＋复制公司，整体 rollback）：复制公司 `chart_of_accounts` 为空、`is_cn_company` 为真；若让 `check_company_chart` 按本表核它，`ok=false`——多出无号 `VAT`，缺 `round_off_account`／`write_off_account`／`unrealized_exchange_gain_loss_account`／`default_discount_account` 四个 DEC-097 默认科目。这正是 S4 FD-008（Phase 登记册 PH-P1016）已登记延迟的缺口，同口径改自检等于提前做 PH-P1016 的一部分，而且以后一建复制公司 `check_app_order` 就会变红。暂停反馈后用户改判：**自检不改，并入 PH-P1016**。已回填审核报告 FD-008 行的裁决列与 PH-P1016 行。
2. FD-017 把三项会报错的检查都放进了 `preflight`，比报告点名的「写类工具检查」多前移了两项（公司解析、`URL`／`KEY` 只设一个）。理由：它们在原脚本里同样排在 CRM 段写入之后或中间（公司解析在 `FCRM Settings.save` 之后），不前移的话报告指出的缺口还在。报错文字和退出码都没变。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| 配置类脚本：会报错退出的检查全部放在第一次写之前，统一做只读预检（`preflight`）；不要写到一半再报错，因为 Frappe 的 DDL 会隐式提交，rollback 撤不回 | 错误处理 | FD-017 |

## 未做项

| 项 | 为什么没做 |
|---|---|
| FD-008 自检 `check_all_cn_companies` 同口径 | 用户改判并入 PH-P1016（见「偏离与暂停」第 1 条） |

## 状态值

**`修复已落地`**——裁为 `新Session修` 的 FD-008／009／017 全部改完，并按报告判定标准复验通过（FD-008 按用户改判只改回填）；全量 209/209。交回 F 复核（新 Round R10）。

## 复核建议

1. **修得最勉强的一项：FD-009。** 只补了日志和文档，误删用户无号科目的根因（判定口径宽）按裁决保留。查法：读 `hr.py:89-98` 的 join 条件，对照 README 第 144 行。
2. **连带影响**：
   - FD-008 改了 `hr.py` 的导入，`CN_CHART_NAME` 不再从 `hr` 导出。全 app `grep` 过，只有 `test_hr` 用到它，已一并改。
   - FD-017 改了 `configure_crm`／`configure_raven` 的入参语义：`configure_crm` 现在收已解析的公司，不再自己解析。这两个函数只有 `main` 调用，`grep` 过 `docker/`、`frappe_china`、`Spike/`。
   - 实际改动的文件：`hr.py`、3 个测试文件、`frappe_china/README.md`、`docker/scripts/configure_apps.py`；文档另有审核报告 FD-008／009 行、P1 概况 PH-P1016 行、本回执，以及 Spike 下 3 个新文件。都在三项的涉及范围内。
3. **拿不准处**：FD-017 的探针在测试站上触发不了 DDL，因为三个自定义字段已经存在。所以「首跑建字段后 rollback 撤不回」这条仍是读码结论。改后的判据是报错前 `save` 次数为 0，它比只看 DDL 更严，DDL 的情形也被它覆盖了。
