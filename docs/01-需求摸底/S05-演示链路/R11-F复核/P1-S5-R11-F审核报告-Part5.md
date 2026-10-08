# F 复核分片报告 · 片 5（对象：R6 开发方案 SL-011～012／TS-017～020 范围内的 R10 当场修 / 审核标准：R10 F 复核报告 FD-039、FD-046、FD-051 的问题描述与建议 ＋ R6 C开发方案 ＋ R6 C讨论记录 DEC-023～028 ＋ 常驻文件契约）

**轮次**：P1-S5-R11｜**步骤**：F 复核分片 5｜**日期**：2026-10-08｜**执行者**：Claude 子 Agent（只读）
**依据**：[R10 F复核报告](../R10-F复核/P1-S5-R10-F审核报告.md)（FD-039、046、051 行，当场修清单 #3／#13，修后验证，状态值裁决去向表，复核建议 4）；[R10 Part5](../R10-F复核/P1-S5-R10-F审核报告-Part5.md)（全文）；[R9 F审核报告](../R09-F审核/P1-S5-R9-F审核报告.md)（FD-013 行、当场修 #2）；[R6 C开发方案](../R06-开发方案/P1-S5-R6-C开发方案.md)（SL-011／012、TS-017～020）；`docs/流程体系/常驻文件契约.md`；`docs/流程体系/流程规范.md` §12；`plannedDev` Workflow 长效信息表；`docs/业务规则.md`
**被审范围**：`frappe_china` `git diff 9d53d39..052e4c3 -- README.md`（第 144 行一处）；主仓库 `git diff d7b89d6..288470b -- docs/开发守则.md`（「删公司要清的子表行」一节，第 91、93 行）；[Stage 概况](../P1-S5-概况.md) 的当前进度区与长效信息区；两站只读查询

## 覆盖自证

- **读全的**：两段 diff；R10 Part5 全文；R10 收口报告的当场修清单、修后验证、总体判断、状态值、复核建议各节及 FD-039／046／051 三行；`hr.py`（HEAD `052e4c3` 全文 1-141，`git status` 为空）；`company.py` 19-116（`is_cn_company`、`on_trash` 等）；`常驻文件契约.md` 全文；`开发守则.md` 85-96、163-185。
- **对照的上游**：`frappe/utils/logger.py` 全文（`default_log_level`、`create_handler`、`get_logger`、`set_log_level`）；`frappe/__init__.py` 第 85 行 `_dev_server`、第 1475-1491 行 `log_level`／`logger()`；全仓库 grep `frappe.log_level`／`set_log_level`／`_dev_server`（命中 `commands/utils.py:640` 的 `store_logs`）；容器内 bench CLI `bench/utils/system.py:149-158`（`bench start` 写 `DEV_SERVER`）与 `bench/config/templates/supervisor.conf`（生产模板，无 `DEV_SERVER`）；`frappe/model/delete_doc.py` 150-247；`deleted_document.py` 全文；`frappe/utils/nestedset.py` 41-165、168-231、264-320；`erpnext` `account.py` 85-163、242-250、495-500，`account.json` 的 `lft`／`rgt`／`old_parent`；`chart_of_accounts.py` 60-76；`erpnext` `company.py` 770-836；`hrms/hooks.py` 392-402；`treeview.js` 522-533。
- **只读查询**（容器 `frappe`，均为 SELECT；时间为 UTC 2026-10-07 17:33～18:34，即北京时间 10-08 01:33～02:34）：两站公司列表（测试站全程只有 `_Test Company`、`_Test Company 1`、`_FCT CRM 验证`，无测试中途的临时公司；演示站只有华东弹簧有限公司）；`information_schema` 带 `company` 列的表及其类型；`company` 列非 Link→Company 的字段；带 `company` 字段的 Single；194 表泛查悬空；补充泛查（`company` 为空串、名字不叫 `company` 的 Company 链接字段 19 个、`tabSingles`、`tabDefaultValue`）；链接到 Account 的 183 个字段查悬空；全部子表（492 对父子）查父记录不存在的行；`tabDeleted Document` 按 DocType 计数；`tabAccount` 行数与最大 `rgt`；容器内各进程的 `DEV_SERVER`；两份 `frappe_china.log` 的大小与时间。SQL 都从标准输入送入，首尾加 `BEGIN`／`END` 哨兵行，确认全部语句执行完。
- **模拟**：按 `nestedset.py` 的 `update_move_node`／`update_add_node`／`rebuild_tree` 写了一个纯内存模拟（不连库），复现「删科目 → 树变动 → 从 Deleted Document 恢复」的 lft/rgt 变化，在容器的 python 里跑，用于 P5-01。
- **跳过**：不跑测试、不写站，所以没有在站上真恢复一次被删科目（P5-01 是读码＋模拟）；没有在 `bench start` 的 web 进程里实际触发一次删除去看日志（R10 已记为盲区，本片同）。临时文件放 `.claude/r11-tmp/p5/`，结束前已删。

## R10 已修项复核

| R10 项 | 修于 | 定位（文件:行） | 落地 | 生效 | 原问题消失 | 说明 |
|---|---|---|---|---|---|---|
| FD-039 ①「只在 `bench start` 拉起的开发服务进程里写进 `logs/frappe_china.log`」 | 当场 #3 | `README.md:144`；`logger.py:12、24-33、80` | ✅ | ✅ | ✅ | `create_handler` 写 bench 级 `../logs/frappe_china.log`（相对 `sites/`，即 `frappe-bench/logs/`）；有站点上下文时**另写**站点级 `sites/<site>/logs/frappe_china.log`（`:29-33`）。README 只写了前者，说法不错，只是没写全，不单列问题。容器实测：`bench start` 起的 `honcho`、`bench serve`、`schedule`、`worker`、`socketio`、`watch` 进程都带 `DEV_SERVER=true`，`docker compose exec` 的 shell 不带。两份 `frappe_china.log` 仍是 0 字节、时间 10-06 13:07（UTC） |
| FD-039 ②「命令行、装 app 钩子、测试与生产进程的缺省级别是 ERROR」 | 当场 #3 | `logger.py:12、80、109-112`；`__init__.py:85、1476`；`commands/utils.py:640`；bench `system.py:154-156`；`supervisor.conf` | ✅ | ✅ | ✅ | 级别取 `frappe.log_level or default_log_level`，`default_log_level` 只看环境变量 `DEV_SERVER`。`frappe.log_level` 的来源只有两个：`set_log_level()`（全部 app 无调用方）和 `bench console` 退出时的 `store_logs`（置 20，只为写 ipython 历史）。**没有站点配置项能改它**——`site_config` 里的 `logging` 是数据库查询日志（`database.py:393`），与此无关。生产：bench 的 supervisor 模板里 gunicorn／worker／schedule 都不设 `DEV_SERVER`，`bench start --no-dev` 也不设，所以缺省 ERROR 成立。同文件第 38 行的 warning 走同一 logger，README 没说它会落盘，不构成说法不符 |
| FD-039 ③「被删的科目留有 `Deleted Document` 记录，可从那里恢复」 | 当场 #3 | `hr.py:121`；`delete_doc.py:176、225-226、237-246`；`deleted_document.py:48、65`；`nestedset.py:54-57、117-119、287-312` | ✅ | ⚠️ | ⚠️ | **留痕成立**：`hr.py:121` 只传了 `ignore_permissions=True`，没传 `force`／`delete_permanently`；`add_to_deleted_document` 只在 `in_install == "frappe"` 时跳过，HRMS 装入触发的 `after_app_install` 时 `in_install` 是 `hrms`，照样写；`Deleted Document` 不在 `default_log_clearing_doctypes`，不会被自动清。**恢复有坑**：快照里的 `lft`／`rgt` 是删除时 `NestedSet.on_trash` 把节点挪到树尾后的值，`parent_account` 是原值、`old_parent` 是空串。`restore` 用 `insert` 把快照原样写回，`on_update` → `update_nsm` 判 `old_parent != parent`，按快照的 `lft`／`rgt` 走 `update_move_node`。若此后别的节点已经占了那段区间，它们会被一起挪走，科目树就乱了。见 P5-01 |
| FD-051 ①「现在清两类：所有公司的报销类型科目行，以及本表建账公司的 `Tax Rule`」 | 当场 #13 | `开发守则.md:91`；`company.py:110-114`；`hr.py:135-141` | ✅ | ✅ | ✅ | 与代码相符：`on_trash` 无条件调 `clear_company_expense_claim_accounts(doc.name)`（HRMS 在时删 `company = 被删公司` 的报销行），`is_cn_company(doc)` 为真时再删该公司的 `Tax Rule`；`is_cn_company` 沿 `existing_company` 链判，复制建账的中式公司也算。措辞「所有公司的报销类型科目行」可能被读成「删所有公司的行」，README:145 的写法「该公司的报销类型科目行（所有公司）」更准；另外这句是代码现状，与 README:145 重复，见 P5-02 |
| FD-051 ②「只查报销行曾漏掉 26 条悬空 `Tax Rule`」 | 当场 #13 | `开发守则.md:93`；R9 报告 FD-013 行（第 157 行）、当场修 #2（第 199 行） | ✅ | ✅ | ✅ | 与 R9 记载相符：26 条，`FCT_TEMP`、`_FCT 入口二` 各 13 条；R5／TS-020 的残留核对只查了报销行 |
| FD-051 ③ 泛查法可执行 | 当场 #13 | `开发守则.md:93`；两站查询 | ✅ | ⚠️ | ✅（Tax Rule 一类）／⚠️（方法覆盖面） | **可执行**：两站各 194 张带 `company` 列的表，全是 `BASE TABLE`，逐表泛查都是 **0 行悬空**。**误报**：Single 不建自己的表、值在 `tabSingles`，泛查碰不到，不会误报（也就查不到，补查 `tabSingles` 0 条悬空）；`company` 列不是 Company 链接的只有 `Employee Benefit Ledger`、`Raven HR Company Workspace` 两张（Data 型），两站这两张表都是 0 行，目前不会误报。**漏报**：① 名字不叫 `company` 的 Company 链接字段有 19 个（`represents_company`、`parent_company`、`asset_owner_company` 等），补查 0 条悬空；② **子表的父记录被上游裸 SQL 删掉、子表本身没有 `company` 列**，泛查查不到。测试站实有 132 行（见 P5-03） |
| FD-051 ④ 写进开发守则是否合适 | 当场 #13 | `开发守则.md:89-93`；常驻文件契约 §1、§2、§5 | ✅ | ⚠️ | — | 「核残留查全部带 `company` 列的表」是跨 Phase 的长效工程约定，归开发守则，合适。引事件作理由（R9 FD-013）在本守则有先例（「判据必须能区分」一节的反例表），不算装过程。「现在清两类……」是代码现状描述，判据 A 下属现状，家在 README:145（已有同义句），守则里重复一份，见 P5-02。**同节没有该逐出的失效内容**：`Expense Claim Account` 确实不在 `hrms/hooks.py:392-402` 的 `company_data_to_be_ignored` 里；全 app 与 `docker/` 没有带 `force` 删 Company 的调用 |

**一句话**：FD-039 的 ①② 三层都成立；③ 的留痕成立，但「可恢复」漏了树形科目恢复后要重建树。FD-051 的 ①② 成立；③ 的方法能跑、对现有 194 张表给出 0，可它看不见子表孤行，测试站有 132 行；④ 的约定部分写对了地方，附带的那句现状说明与 README 重复。

## 延迟／不做项登记核对

| R10 项 | 裁决去向 | 登记位置 | 描述与实情一致否 | 说明 |
|---|---|---|---|---|
| FD-046 | 延迟（Stage 收口移交长效信息时同步路线文档） | Stage 概况第 80 行（R10 进度表行末「FD-046 收口时做」）、第 82 行（⭐ 进度条目「FD-046 留到 Stage 收口移交长效信息时同步路线文档」） | 基本一致 | 记下了，收口时读当前进度能看到。但有两处不足：① 两处都只写了「同步路线文档」，没写同步什么（#3 的 FD-027、FD-032，#4 的 FD-002 `debug_mode` 置 0），收口者得回 R10 报告查；② 收口做长效信息移交时，读的是长效信息表 #3、#4，那里没有任何标注，而路线文档 v1.7 修订行写着「#2～#4」已落进清单——这正是 FD-046 说的漏法。没进延迟登记册：按规范 §12 与 Workflow 长效信息表，「经用户裁决为延迟的审核发现」应进登记册；本项在本 Stage 内就会做完，记作收口待办也说得通。见 P5-04 |
| FD-047 | 延迟 | 登记册 `SH-P1S5011`（第 127 行） | 一致 | 不属本片，只核了在册 |
| FD-044／048／052 | 不做 | R10 报告状态值表 | — | 不属本片 |

## 业务规则合规核

| 规则条款 | 本轮改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 间接（被删科目恢复后科目树的 lft/rgt） | 合规（规则未经专家确认） | 本轮只改说明文字。P5-01 是树结构的完整性问题：分组科目余额按 lft/rgt 汇总，树乱时报表汇总会错。这条不改变科目口径 |
| BR-002 报表构成 | 否 | 不涉及 | — |
| BR-003 增值税税率 | 间接（P5-03 孤行是税费模板子表） | 不涉及现行口径 | 孤行属于已删公司，现存模板没有重复行（查询 `dup-idx` 为空） |
| BR-004～BR-007 | 否 | 不涉及 | — |
| DEC-028 兜底 `5602250` | 否 | 仍为草案·待领域专家确认 | README:144 原句保留 |

## 集成点登记（交接摘要）

- **本片依赖**
  - 主会话：P5-01 只做了读码和内存模拟。要实证，得在测试站开事务、删一个无号叶子科目，新建两个科目（或建一家公司），然后 `restore`，查 `tabAccount` 的 lft/rgt 一致性，再 rollback。这要写站，本片没做。
  - 片 1：`is_cn_company` 接 dict 的分支归片 1；本片只确认 `on_trash` 传的是 Document，走的是 `else` 分支。
- **本片暴露**
  - **本轮基线**（UTC 2026-10-07 17:33～18:34）：两站 194 张带 `company` 列的表 0 悬空；19 个其它名字的 Company 链接字段、`tabSingles`、`tabDefaultValue` 0 悬空；演示站全部 492 对子表 0 孤行、Account 链接 0 悬空。**测试站**：`Purchase Taxes and Charges` 77 行、`Sales Taxes and Charges` 55 行，父模板已不存在，`account_head` 指向已不存在的科目，来自 11 家已删公司（9 家 `_FCT 银行导入 BI*` 删于 10-01，`FCT_TEMP`／`_FCT 入口二` 删于 10-05，见 `tabDeleted Document`）。
  - 两站 `tabDeleted Document` 里没有 Account 记录（测试回滚了），目前没有可恢复的被删科目。两站科目树现在是一致的：测试站 459 行、最大 `rgt` 918；演示站 266 行、最大 `rgt` 532。
  - 别片若引用「泛查 0 悬空」做结论，口径只覆盖带 `company` 列的表，不含子表孤行。

## 自证复核

| 被审产物声称（R10 报告／README／开发守则／Stage 概况） | 实际复核 | 一致否 |
|---|---|---|
| 当场修 #3：README 写明 warning 只在开发服务进程落盘、其余进程缺省 ERROR 不落盘、被删科目可从 `Deleted Document` 恢复 | 三点都在 `README.md:144`；①② 与上游一致；③ 留痕成立，恢复要补「重建树」 | 部分一致（P5-01） |
| R10 复核建议 4：「被删科目能从 `Deleted Document` 恢复，审计痕迹并没有缺」 | 痕迹确实在（`delete_doc.py:225-226`）；「能恢复」对树形 DocType 有前提 | 部分一致（P5-01） |
| 当场修 #13：补现清的两类与泛查核法；写入前按常驻文件契约判为长效工程约定、同节无失效内容 | 两类与代码相符；核法能跑；同节确实没有失效内容；「现在清两类」那句属现状、与 README 重复 | 基本一致（P5-02） |
| 开发守则：「只查报销行曾漏掉 26 条悬空 `Tax Rule`（P1-S5-R9 FD-013）」 | 与 R9 报告第 157、199 行一致 | 一致 |
| R10 Part5：「两站 194 张带 `company` 列的表无悬空行，可作为本轮之后的基线」 | 本轮复查仍是 194 张、0 行；但测试站有 132 行子表孤行，不在这个口径里 | 一致（口径内）；口径外另有发现（P5-03） |
| Stage 概况：「FD-046 收口时做」 | 第 80、82 行都在 | 一致（细节不足，P5-04） |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准／意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P5-01 | 低 | `README.md:144`「可从那里恢复」；frappe `nestedset.py:54-57`、`:117-119`、`:287-312`；`deleted_document.py:48、65`；`delete_doc.py:225-226` | 「被删的科目可从 `Deleted Document` 恢复」在树形 DocType 上不完全成立。删除时 `NestedSet.on_trash` 先把节点挪到树尾、再 `reload`，快照里存的是树尾的 `lft`／`rgt`、原 `parent_account` 和空的 `old_parent`。`restore` 把快照原样 `insert`，`on_update` → `update_nsm` 看到 `old_parent("") != parent_account`，就按快照的 `lft`／`rgt` 跑 `update_move_node`；它的第一步把 `lft >= 快照.lft 且 rgt <= 快照.rgt` 的行全部取负（挪到暗区）。删除后树只要长了两个以上节点，那段区间就会被别的科目占住，这些科目会被一起挪进被恢复科目的父节点下，lft/rgt 失真（`parent_account` 不变）。新建任何公司都会建几百个科目，并对整张 `tabAccount` 跑 `rebuild_tree`（`chart_of_accounts.py:71-74`），之后一定会撞上。**证据**：按上游三个函数写的内存模拟，随机 40 节点的树各跑 300 次：删后新增 0／1 个节点再恢复，树坏 0 次；新增 2、3 个节点，300 次全坏；新增 3 个节点并 `rebuild_tree` 后再恢复，300 次全坏。一个具体例子：快照 `[9,10]`，删后 G2 下新增 A1～A3 并重建，A3 恰好占 `[9,10]`；恢复后 A3 被挪到 `[3,4]`，落在 G1 区间内，却仍挂在 G2 下。修复办法：在科目表树视图点「Rebuild Tree」（`treeview.js:522-533`，限 System Manager）即可，因为 `parent_account` 没坏。没有在站上实测 | README 说法要与实情一致；FD-039 (a)「写明可从 `Deleted Document` 恢复」的意图；开发守则「判据必须能区分」（「有记录」不等于「能无损恢复」） | README:144 那句改为「被删的科目留有 `Deleted Document` 记录，可从那里恢复；科目是树形，恢复后须在科目表树视图执行一次 Rebuild Tree（重建树）」。只改文档 | 本Session修 | 只补 README 这半句，还是先由主会话在测试站开事务实测一次再改 | 待裁决 |
| P5-02 | 观察 | `docs/开发守则.md:91`「现在清两类：所有公司的报销类型科目行，以及本表建账公司的 `Tax Rule`」；`frappe_china/README.md:145` | 两处小问题。① 措辞：「清所有公司的报销类型科目行」可能被读成删公司时把所有公司的报销行都清掉；实际是「不论哪种公司，删时都清它自己的报销行」，README:145「该公司的报销类型科目行（所有公司）」说得更准。② 归属：这句描述的是 `on_trash` 当前的行为（「现在」），按常驻文件契约判据 A 属现状，`on_trash` 一改就会错。README:145 已有同义句，守则里又写一份，违背「同一条内容只在一个文件里有家」。本节真正的长效约定是「删公司由 `on_trash` 兜住」「不带 `force`」「泛查核残留」，不需要列现清对象 | 常驻文件契约 §1 判据 A、§2「同一条内容只在一个文件里有家」、§5.1 | 守则这句改为指向：「现清对象见 `frappe_china/README.md`『已知限制』删公司一条」；或者保留但改成「删公司时清该公司自己的报销行，中式公司另清 `Tax Rule`」，消掉歧义 | 本Session修 | 改成指针，还是只改措辞 | 待裁决 |
| P5-03 | 低 | `docs/开发守则.md:93` 的泛查法；测试站 `tabPurchase Taxes and Charges`、`tabSales Taxes and Charges`；erpnext `company.py:830-832` | 泛查法只看带 `company` 列的表，看不见子表孤行。ERPNext `Company.on_trash` 用裸 SQL 删税费模板（`delete from tabSales/Purchase Taxes and Charges Template where company=%s`），不删子表，子表又没有 `company` 列。**测试站实有 132 行**（采购 77 行、销售 55 行）：父模板已不存在，`account_head` 指向已不存在的科目，涉及 11 个缩写（`BI48186` 等 9 个、`FCT2`、`FCT3`），对应 `tabDeleted Document` 里 10-01、10-05 删掉的 11 家公司。演示站 0 行。全部 492 对子表只有这两张有孤行。危害：目前没有父记录会加载它们。但以后新建一家缩写相同的公司、重建同名模板（如 `P0无税 - FCT2`）时，`_load_child_table_from_db` 只按 `parent`／`parenttype`／`parentfield` 取行，旧孤行会混进新模板，税行重复。随机缩写 `BI*` 撞名概率很低，`FCT2`／`FCT3` 这类固定缩写有可能撞上（当前测试代码里没再用这两个） | 开发守则「判据必须能区分」（泛查为空 ≠ 无残留）；IT-002「不留悬空行」的意图 | ① 守则那句补半句：「子表另查 `parent` 不在父表的行（上游 `Company.on_trash` 裸删税费模板会留下这种行）；Single 与不叫 `company` 的 Company 链接字段不在此法内」。② 测试站这 132 行，删前整行导出备份，再按 `parenttype` 删父模板已不存在的行。要写站，须用户许可 | 本Session修 | 守则补不补；测试站 132 行删不删（R9 FD-013 同类处置的先例是「允许、删前备份」） | 待裁决 |
| P5-04 | 观察 | [Stage 概况](../P1-S5-概况.md) 第 80、82 行；长效信息表 #3、#4（第 108-109 行） | FD-046 的收口待办只记在当前进度区的两句里，内容只有「同步路线文档」，没写同步哪几条。收口时做长效信息移交，按的是长效信息表，而 #3、#4 格内没有「R9 增补的 FD-027、FD-032、FD-002 未进路线文档 v1.7」的标注；路线文档 v1.7 修订行又写着「#2～#4」已落进清单。收口者只看长效信息表和路线文档，仍可能判为已移交，也就是 FD-046 原本说的那种漏法。另外，按规范 §12 与 Workflow 长效信息表，「经用户裁决为延迟的审核发现」应进延迟登记册，本项没有 `SH-` 号 | FD-046 的裁决意图（收口时不漏）；规范 §12.2 第 1 条 | 在长效信息 #3、#4 格末各加一句「（R9 增补 FD-027／FD-032／FD-002 尚未进路线文档 v1.7 §四 S7，收口移交时同步，R10 FD-046）」；登不登 `SH-` 号由用户定 | 本Session修 | 只在长效信息格内标注，还是另登 `SH-P1S5012` | 待裁决 |

## 本片盲区自述

- **P5-01 没有实跑**：结论来自读上游代码和内存模拟，模拟只复刻了 `update_move_node`／`update_add_node`／`rebuild_tree` 三个函数的 lft/rgt 运算。没有在站上真跑一次 `restore`。`Account.validate` 在恢复时是否另有拦截（例如父科目已改成非组、公司已删），只读了 `validate_parent`，判断是会报错而不是损坏树，没有逐条核。
- **FD-039 ①② 的证据**：级别结论来自读码，加上容器进程环境变量、日志文件为空作旁证；没有在 web 进程里触发删除，看那行日志是否写进两份文件。生产部署（supervisor）只读了 bench 自带的模板，项目自己没有生产部署，无从实测。
- **P5-03 的来源**：只确认了「父模板被裸 SQL 删、子表不删」这一条路径，以及孤行与已删公司的对应关系；没有去追 `FCT_TEMP`、`_FCT 入口二` 当初由哪个探针或旧测试建出。孤行混进新模板的危害是读 `_load_child_table_from_db` 推出的，没实测。
- **泛查的时间点**：查询窗口内测试站一直只有 3 家公司；主会话在跑全量回归，窗口外新建又删掉的公司不在本片结果里。`Raven AI Function` 的 Deleted Document 在窗口内有新增（10-07 18:50 UTC 前后），说明回归正在跑，但没看到临时公司留下。
- **没往这些方向找**：开发守则其它各节的逐出检查（只查了本节）；`hr.py:38` 那条 warning 的触发频率；P5-03 之外其它上游 `on_trash` 裸删路径（只做了全子表孤行泛查，结果只有这两张）。
