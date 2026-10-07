# F 审核分片报告 · 片 5（对象：R6 开发方案 SL-011～012／TS-017～020 的代码落地 / 审核标准：R5 E 报告 IT-001～003 ＋ B 需求文档 §4.2.2、AC-006 ＋ R6 C 讨论记录 DEC-023～028）

**轮次**：P1-S5-R9｜**步骤**：F 分片 5｜**日期**：2026-10-07｜**执行者**：Claude 子 Agent（只读）
**依据**：[R6 C开发方案](../R06-开发方案/P1-S5-R6-C开发方案.md)（全文）；[R6 C讨论记录](../R06-开发方案/P1-S5-R6-C讨论记录.md)（DEC-023～028、F1～F11、LG-014／015）；[R5 E确认报告](../R05-确认报告/P1-S5-R5-E确认报告.md) IT-001／002／003；[B需求文档](../R02-需求文档/P1-S5-R2-B需求文档.md) §4.2.2、§4.10、§八 AC-006、§十 LG-011／012；`docs/开发守则.md`（「删公司要清的子表行」「认科目看科目号」「依赖可选 app」「判据必须能区分」）；`docs/业务规则.md`
**被审范围**：`frappe_china` `03fde72..4b21aae` 中属 R6 的部分——`accounting/company.py`、`accounting/hr.py`（全文）、`hooks.py` `doc_events`、`cn_tax/data/company_defaults.json`、`README.md`「已知限制」两条、`tests/test_company_hr_lifecycle.py`、`tests/test_hr.py`、`tests/test_scaffold.py` ⑦、`tests/test_expense_claim.py`、`tests/utils.py`；回执 [R7 D回执](../R07-D代码/P1-S5-R7-D回执.md)

## 覆盖自证

- **读全的依据**：F Spec、`bricks/audit.md`、`bricks/sharding.md`、R6 开发方案全文（§一～§九逐条建要求清单）、R6 C 讨论记录全文、R7 D 回执全文、`开发守则.md` 全文、`业务规则.md` 全文。R5 E 报告只读了 IT-001～004 一节；R8 E 报告与 S5 概况只按关键词读了 R6／TS-017～020／IT-030／延迟登记册相关段（当索引用）。B 需求文档只读了 §4.2.2、§4.10、AC-006、LG-011／012 与目录。**未读**：R3 总纲全文（只沿用 R6 方案对它的替换表）、流程规范 §2.2／§2.3 原文（档位与状态取值按 audit 积木与任务说明填）。
- **逐行读的代码**：`company.py` 全文（1-221）、`hr.py` 全文（1-137）、`hooks.py` 155-162、`company_defaults.json` 全文、`test_company_hr_lifecycle.py` 全文（1-336）、`test_expense_claim.py` 全文、`test_hr.py`／`test_scaffold.py` 的 S5 diff、`tests/utils.py` 全文；`git diff 8433978..a82499f`（Codex 版 → Claude 续做）逐段核了回执「偏离」1～5 条；`git show 65f3b78:company.py`（删行旧逻辑原貌）。
- **对照的上游**：`hrms/hooks.py` Company 钩子与 `company_data_to_be_ignored`；`hrms/overrides/company.py` 全文；`hrms/setup.py` 报销类型夹具（`_` 为 `install_fixtures` 的假翻译）；`Expense Claim Type`／`Expense Claim Account` 结构与 `validate_accounts`；`hrms` 全部引用 Company／Account 的子表；`erpnext` `company.py` 的 `validate`／`validate_coa_input`／`on_update`／`on_trash`、`create_charts`／`get_chart`（复制建账）；`erpnext` `Account.on_trash`；`frappe` `delete_doc.py`（先 `on_trash` 后链接检查）、`Document.run_method`、`database.set_value`／`delete`、`clear_document_cache`、`nestedset`。
- **只读查询**（容器 `erx001-frappe-1`，`bench --site X mariadb -e "SELECT…"` 与 `bench execute frappe.get_doc_hooks`）：两站公司、报销类型、`Expense Claim Account` 全行及其科目号、悬空行（按公司、按科目）、`Tax Rule` 按公司计数、各公司科目数与无号明细科目数、`installed_apps`、Company 实际钩子顺序；测试站全库凡有 `company` 列的 194 张表逐表查「指向不存在公司的行」；`tabDeleted Document` 里的 Company 删除记录。
- **跳过**：没有跑任何测试与变异（任务限定只读、主会话在跑全量回归），故 R7 回执与 R8 报告里的「专项 15/15」「变异各有失败」只核了日志与代码结构，没有亲自复现；没跑 ruff（容器 `env/bin` 无 ruff），只做了 `ast.parse` 语法检查；演示站只做了只读查询，没有构造删公司／复制建账场景。

## 逐项落地核查

| 意图层依据 | 要求层要求（方案任务／验收条款逐条） | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| IT-002／DEC-023 | 接口契约：`on_trash` 调 `clear_company_expense_claim_accounts(doc.name)`（所有公司） | `company.py:109-111` | ✅ | ✅ 实际钩子表 `on_trash` 末位为本函数 | — |
| DEC-025 | `is_cn_company(doc)` 时 `frappe.db.delete("Tax Rule", {"company": doc.name})` | `company.py:112-113` | ✅ | ✅ | 只按 `company` 过滤，不会误删别家；复制建账的公司本来就没有本 app 建的 `Tax Rule`（`setup_cn_taxes` 只在建账分支 `company.py:132`），故判 `is_cn_company` 与否不影响结果 |
| DEC-024 | 只删 `company == doc.name` 的行 | `hr.py:135-136` | ✅ | ✅ | — |
| HT-018 | 框架先跑 `on_trash` 再查链接 | 上游 `delete_doc.py:173-183` | ✅ | ✅ | 已读码确认：`run_method("on_trash")`（控制器在前、doc_events 在后）→ `check_if_doc_is_linked` |
| HT-021 | 无 DocType 链接 `Tax Rule` | 全 bench `*.json` 搜 `"options": "Tax Rule"` | ✅ | — | 本片复查零命中 |
| HT-022 | 有交易时删除仍被拦、`on_trash` 删除随事务回滚 | `test_company_hr_lifecycle.py:174-189` | ✅ | ✅ | 用 savepoint 回滚核条数不变 |
| TS-017 | 新增 `is_cn_company`：沿 `existing_company` 链，环或超 10 层判否 | `company.py:33-49` | ✅ | ✅ 被 `before_insert`／`validate`／`on_update`／`on_trash` 四处调用 | 链上公司不存在时返回假（`:40-41`）；源公司被复制后因 `existing_company` 是 Link 不能不带 `force` 删，故实际不会断链 |
| TS-017 | `before_insert`／`on_update` 改调 `is_cn_company`；`_takes_cn_path` 不变 | `company.py:61`、`:84`；`:52-57` | ✅ | ✅ | `_takes_cn_path` 在 R4 已改为 `_company_chart`，非本轮改动 |
| TS-017 | `hr.py` 新增 `clear_company_expense_claim_accounts`（`frappe.db.delete`，不 import hrms） | `hr.py:132-137` | ⚠️ | ✅ | 守卫查的是 `DocType "Expense Claim Account"`，同文件另两处查 `"Expense Claim Type"`（`:31`、`:85`）；真实站点两者同存同亡，功能等价，但使对应测试失去判别力，见 P5-02 |
| TS-017 | `hooks.py` `doc_events["Company"]["on_trash"]` | `hooks.py:160` | ✅ | ✅ | 制表符缩进，已核 |
| TS-017 测试 | 新文件，继承 `FrappeChinaTestCase`，HRMS 不在则 `skipTest` | `test_company_hr_lifecycle.py:107-112` | ✅ | ✅ | — |
| SL-011 ① | 中式公司不带 `force` 删成功；报销行 0、`Tax Rule` 0 | `test_…:123-132` | ✅ | ✅ | 先断言删前 13 条 `Tax Rule`、行数 >0，有判别力 |
| SL-011 ② | `Standard` 公司同法删除成功、报销行 0 | `test_…:134-141` | ✅ | ✅ | — |
| SL-011 ③ | 删后同名重建：266 科目、报销行与映射一致；再建 `Standard` 不报错 | `test_…:143-152` | ✅ | ✅ | — |
| SL-011 ④ | 另一家公司的报销行与 `Tax Rule` 删前删后相同 | `test_…:154-161` | ✅ | ✅ | — |
| SL-011 ⑤① | 无 `Expense Claim Type`（patch `exists`）→ 删公司不报错，`clear…` 返回 0 | `test_…:163-172` | ⚠️ | ❌ 判别力不足 | patch 只让 `Expense Claim Type` 答否，而 `clear…` 查的是 `Expense Claim Account`，仍走 count＋delete；测试先手删了该公司全部行，返回 0 来自「本来就没行」而非守卫。见 P5-02 |
| SL-011 ⑤② | 有一张已提交凭证 → 删除报错，报销行与 `Tax Rule` 条数不变 | `test_…:174-189` | ✅ | ✅ | 按方案用 `1001`／`5602250` 各 1 元的 JE |
| SL-011 ⑤③ | `Standard` 公司删除不动任何 `Tax Rule` | `test_…:191-202` | ✅ | ✅ | 既 spy `db.delete` 调用又核全站总数 |
| TS-017 验证 | 判别力变异：注释 `on_trash` 两行，①②③ 失败 | R7 回执、R8 报告 | ⚠️ 未亲自复现 | — | 只读约束下未跑；回执写 14 例、R8 写 13 例，R8 已解释 |
| DEC-028 | `company_defaults.json` 新键 `expense_claim_type_fallback = "5602250"`，`_comment` 补「待领域专家确认」 | `company_defaults.json:2`、`:27` | ✅ | ✅ `hr.py:26` 消费 | `5602250 管理费用_其他` 在本表为明细（`is_group: 0`），两站实测存在 |
| TS-018 | `FALLBACK_KEY` 常量 | `hr.py:16` | ✅ | ✅ | — |
| TS-018 | `expense_claim_account_number`：名称本身 → 译文 → 兜底 | `hr.py:19-26` | ✅ | ✅ | 译文比对依赖当前会话语言，见 P5-04（观察） |
| §二／TS-018 | `set_cn_expense_claim_accounts` 遍历站上全部类型；映射有、站上无照旧告警；只配缺的、不覆盖；缺科目一次报全、不写任何行；无 DocType 返回 [] | `hr.py:29-69` | ✅ | ✅ | 「不覆盖」靠 `:47-50` 按 `parent`＋`company` 判存在；`test_expense_claim.py:72-83` 验证已有行不被改 |
| DEC-026／TS-018 | 新增 `validate`：已有中式公司保存前预配；`is_new()` 不动作 | `company.py:76-79` | ✅ | ✅ 实际钩子表 `validate` 为 HRMS→本 app | 每次保存的代价：1 次 `get_all`＋每类型 1 次 `exists`（站上 5 类），可忽略；只补缺、不改已有行 |
| HT-017 | `validate` 先于 HRMS `on_update`，补齐后 HRMS 全部跳过 | `test_…:206-233` ①「`repointed` 为空」 | ✅ | ✅ | 与 app 安装顺序无关（validate 恒在 on_update 前） |
| HT-020 | 在 Company `validate` 里保存 `Expense Claim Type` 不影响公司保存 | `test_…:206-233` 间接 | ⚠️ | ✅ | 回执已如实申报为间接覆盖 |
| TS-018 | `hooks.py` `validate` 项 | `hooks.py:158` | ✅ | ✅ | — |
| TS-018 测试 | `test_hr.py` 的缺科目用例改为同时 patch `get_all` | `test_hr.py:29` | ✅ | ✅ | — |
| SL-012 ① | 新增 `_FCT 新类型` 后保存：6 行、新类型挂 `5602250`、原 5 行不变、266 科目、无无号明细；`repointed` 为空；zh／en 各一次 | `test_…:206-228` | ✅ | ✅ | 用 `patch(..., side_effect=spy)` 取返回值，等效于方案的 `wraps` |
| SL-012 ② | 连续保存两次结果相同 | `test_…:230-233` | ✅ | ✅ | — |
| SL-012 ④ | 已指向别的有号科目的行保存后不变 | `test_…:255-264` | ✅ | ✅ | — |
| SL-012 ⑤ | 类型名为 `_("Travel")` 的 zh 译文时命中 `5602130` | `test_…:266-274` | ✅ | ✅ | 先断言译文≠原文，有判别力 |
| SL-012 ⑥② | 映射科目号查不到 → 报错列全缺项、不写任何行 | `test_…:296-308` | ✅ | ✅ | 连兜底科目缺失也列出（`Travel=9999903`） |
| SL-012 ⑥③ | 无 `Expense Claim Type` → `validate`／`on_update`／`repoint` 零写入 | `test_…:310-324` | ✅ | ✅ | 这例有判别力：去掉守卫会补回 5 行，断言即红 |
| SL-012 ⑥④ | `Standard` 公司保存行为不变 | `test_…:326-336` | ✅ | ✅ | — |
| DEC-027／TS-019 | 新增 `repoint_generic_expense_claim_accounts`：join 查指向无号科目的行 → 改挂映射科目 → 逐个删通用科目（有 GL／`LinkExistsError` 则保留＋warning＋记 `kept`）→ 清 ECT 文档缓存；返回三键 | `hr.py:82-129` | ✅ | ✅ | 判「无号」用 `ifnull(account_number,'')=''`，不用 `_()`；删除不带 `force`。改挂对象是**任何**无号科目，删除成功时无日志，见 P5-03 |
| TS-019 | `on_update` 非建账分支 `is_cn_company` 时调 `repoint`；删除 `_remove_hrms_expense_claim_account` | `company.py:82-90` | ✅ | ✅ | 已核 Codex 版仍调已删函数（`git diff 8433978 a82499f`），续做已改 |
| HT-019／SL-012 ③ | 复制建账 zh／en：报销行齐全且带号、与映射一致；无「费用报销记录」／`Expense Claims`；267 科目；复制的复制成立；先断言 `frappe_china` 在 `hrms` 之后、不跳过 | `test_…:235-253` | ✅ | ✅ | 复制的复制只在 zh 下测，方案未要求双语，可接受 |
| SL-012 ⑥① | 通用科目有 GL → 行照改、科目保留、`kept` 列出、warning 日志 | `test_…:276-294`；`hr.py:115-117` | ✅ | ✅ | — |
| SL-012 ⑦ | 源码无 `_remove_hrms_expense_claim_account`、无 `_("Expense Claims")` | `test_scaffold.py` `test_no_language_dependent_expense_claim_cleanup` | ✅ | ✅ | 本片 grep 复查：只在该测试文件自身出现 |
| TS-019 | S4 `test_company` 复制建账用例不改、照旧过 | `test_company.py` | ✅（未改） | ⚠️ 未亲自跑 | 日志 `s5-r7-regression.log` 含 `test_company`，结尾 `Ran 196 … OK`、`EXIT=0` |
| TS-020 ① | 全量回归：报收集／通过／跳过，≥180 | `frappe-bench/logs/s5-r7-regression.log` | ✅ | — | 日志结尾 `Ran 196 tests in 767.106s`、`OK`、`EXIT=0`，与回执一致 |
| TS-020 ② | 残留核对：无 `_FCT` 公司；`Expense Claim Account` 无悬空行 | 两站只读查询 | ⚠️ | — | 报销悬空行两站均 0 ✅。但测试站仍有 **26 条 `Tax Rule` 指向已删公司 `FCT_TEMP`／`_FCT 入口二`**，其模板也已不存在；方案的核对口径只覆盖报销行，见 P5-01。`_FCT CRM 验证` 是 SB 后建的，已由 R8 IT-030 裁决保留 |
| TS-020 ③ | README「已知限制」补两条 | `README.md` +2 行 | ✅ | — | 措辞与 DEC-023～028 一致，标了「待领域专家确认」 |
| TS-020 ④ | D 回执「新增约定」记删公司约定 | R7 回执「新增约定」 | ✅ | — | 并已沉淀进 `开发守则.md`「删公司要清的子表行」「认科目看科目号」两节 |
| §九-2 | 删公司一律不带 `force` | 全 `frappe_china` 与 `docker/` grep | ✅ | — | `delete_doc("Company"…)` 只出现在生命周期测试，均不带 `force`；`raven_dataset.py:36` 的 `force=True` 删的是 CRM Deal／Item 等，不是公司 |
| §九-3 | 不碰演示站；IT-006 测试写在 `test_expense_claim.py`，不与生命周期测试混写 | 两个测试文件 | ✅ | — | 分开写了；演示站报销行 5 条、全带号、与映射一致，科目 266、无无号明细 |
| 方案外夹带 | — | `git diff 03fde72..4b21aae` 本片文件 | ✅ 无功能夹带 | — | `hr.py:128` `clear_document_cache` 是方案伪代码自带的。`company_defaults.json:33-34` 有 `},  "item_group_expense"` 排版瑕疵（R4 `1193f94` 引入，R6 改了同文件没顺手修，见 P5-05） |
| LG-139 | Company 钩子与 HRMS 钩子的先后 | `bench execute frappe.get_doc_hooks`（测试站） | ✅ | ✅ | `validate`：HRMS→本 app；`on_update`：HRMS 三个→本 app 末位；`on_trash`：HRMS→本 app。两站 `installed_apps` 均以 `frappe_china` 结尾。`repoint` 依赖此顺序，由 SL-012 ③ 首行断言与 `check_app_order` 兜住 |

## 业务规则合规核

| 规则条款 | 本 Round 改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则科目表 | 涉及（报销映射与兜底科目） | 合规（未经专家确认） | `5602250 管理费用_其他` 是本表明细科目；改挂目标一律按 `account_number` 取本表科目；B 需求 §4.10 已定映射是配置、不是不变量 |
| DEC-028「未映射的报销类型挂 `5602250`」 | 新增口径 | **草案·待领域专家确认** | AI 推荐、用户采纳的口径，不是已生效不变量；`company_defaults.json` `_comment` 与 README 均已标「待领域专家确认」；不进 `业务规则.md` 是对的 |
| BR-002～BR-007（报表、增值税、附加税、价税分离） | 不涉及 | — | 删 `Tax Rule` 只发生在删公司时，不改税率与计税逻辑 |
| 本片总体 | — | 无新增或变更的领域不变量 | 删公司清理、报销映射预配都是实现层；无需触发规则送审 |

## 集成点登记（交接摘要）

**本片暴露**
- 接口：`company.is_cn_company(doc_or_name)`（沿 `existing_company` 链，≤10 层）；`hr.expense_claim_account_number(type)`；`hr.set_cn_expense_claim_accounts(company) -> list[str]`；`hr.repoint_generic_expense_claim_accounts(company) -> {"repointed","deleted","kept"}`；`hr.clear_company_expense_claim_accounts(company) -> int`；`hr.backfill_cn_expense_claim_accounts()`（R3 已有，被 `install.after_app_install("hrms")` 消费，只按 `chart_of_accounts == 小企业会计准则(2024)` 选公司，不含复制建账的公司，LG-015 已接受）。
- 钩子：`doc_events["Company"]` 现为 `before_insert`／`validate`／`on_update`／`on_trash` 四项（`hooks.py:155-162`）。

**本片依赖**
- 跨片共享状态 ①：`installed_apps` 中 `frappe_china` 在 `hrms` 之后（两站实测 `["frappe","erpnext","crm","hrms","insights","raven","frappe_china"]`）。复制建账的事后改挂靠这个顺序；由别的片（R3 Part1／`check_app_order`／`reorder_installed_apps`）保证。
- 跨片共享状态 ②：`cn_tax/data/company_defaults.json` 的键 `expense_claim_type`（5 个英文键）与 `expense_claim_type_fallback`（`5602250`），消费方只有 `hr.py`。`docker/scripts/configure_apps.py:621` 也按 `chart_of_accounts` 选中式公司，与 backfill 口径相同、同样漏复制建账的公司。
- 跨片共享状态 ③：HRMS 夹具建的报销类型名为英文（`hrms/setup.py:338-342` 用的是假翻译 `_`）；两站实测为 `Calls/Food/Medical/Others/Travel`。
- 上游契约：HRMS `set_expense_claim_type_accounts` 的「已有行即跳过」（`hrms/overrides/company.py:125-126`），以及 `company_data_to_be_ignored` 不含 `Expense Claim Account`（`hrms/hooks.py:392-402`）。HRMS 锁在 `6f5ac249`（`docker/apps.json`）。
- 测试基类：`FrappeChinaTestCase`（`tests/utils.py`，lang=zh、舍入固定为 Commercial Rounding）与 `make_cn_company`／`make_std_company`。

**事件**：本片不发出、也不消费 SSE／realtime 事件。

## 自证复核

| 被审产物声称 | 实际复核 | 一致否 |
|---|---|---|
| R7 回执：TS-017 落地 `is_cn_company`:33-49、`before_insert`:60-61、`on_trash`:109-113、`clear…`:132-137、`hooks.py`:160 | 行号逐一对上 | 一致 |
| R7 回执：TS-018 `expense_claim_account_number`:19-26、`set…`:29-69、`validate`:76-79、`hooks.py`:158、`test_hr.py`:28 | 前四项一致；`test_hr.py` 的 `get_all` patch 在第 29 行（差 1 行） | 基本一致 |
| R7 回执：TS-019 `repoint`:82-129、`on_update`:82-90 | 一致 | 一致 |
| R7 回执：Codex 版 `on_update` 仍调已删函数、`set…` 只遍历映射、`before_insert` 未改、`repoint` 无 warning、注释乱码 | `git diff 8433978 a82499f` 逐条见到 | 一致 |
| R7 回执：专项 15/15 | 测试文件里正好 15 个 `test_` 方法；本片未亲自跑 | 结构一致，数字未复现 |
| R7 回执：全量收集 196、通过 196、跳过 0、`EXIT=0` | `frappe-bench/logs/s5-r7-regression.log` 结尾 `Ran 196 tests in 767.106s`／`OK`／`EXIT=0` | 一致 |
| R7 回执：残留核对「`Expense Claim Account` 指向不存在公司的行 0」 | 两站均 0 | 一致 |
| R7 回执／R6 方案隐含：删公司的残留只有报销行 | 测试站有 26 条 `Tax Rule` 指向已删公司（`FCT_TEMP`、`_FCT 入口二` 各 13 条，2026-10-05 强删留下），其销项／进项模板也已不存在 | **不一致**（核对口径漏项，P5-01） |
| R7 回执：SL-011、SL-012 验收条件「各有测试覆盖」 | SL-011 ⑤① 的测试在守卫失效时照样通过 | **部分不一致**（P5-02） |
| R7 回执：HT-020 由 SL-012 ①② 间接覆盖 | 读码与测试结构相符 | 一致（如实申报） |
| R7 回执：LG-014 要到 SB IT-005 才能实测 | 演示站已装 HRMS，报销类型名实测为英文；但 LG-014 在 R6 讨论记录里仍是「待验证」，后续文档没有关闭它 | 留档滞后（P5-04） |
| R8 E 报告：TS-017～019 三层全 ✅ | 本片三层核查结果相同，另外发现 P5-01～03 | 结论相近，R8 没覆盖到这三处 |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P5-01 | 低 | 测试站 `tabTax Rule`；R6 方案 TS-020 第 2 步 | 测试站有 26 条 `Tax Rule` 指向已删公司 `FCT_TEMP`／`_FCT 入口二`（各 13 条，`ACC-TAX-RULE-2026-00118` 起，modified 2026-10-05 19:20），它们引用的销项／进项模板也已不存在。这正是 F2 说的强删残留里与报销行同源的另一半；R5 IT-001 只删了报销行，TS-020 的残留核对 SQL 也只查报销行，所以没被发现。复现：`select count(*) from \`tabTax Rule\` x left join tabCompany c on c.name=x.company where c.name is null` → 26。全库 194 张带 `company` 列的表里只有这一处悬空。当前查询都按 `company` 过滤，不会命中它们，所以功能上没被触发 | IT-002「不留悬空行」；DEC-025；TS-020 残留核对的意图 | 主会话回归跑完后在测试站删这 26 条（只限这两家已删公司）；以后的残留核对加上 `Tax Rule`（以及「全库带 `company` 列的表」这一类泛查） | 本Session修 | 是否允许删测试站这 26 条（只动测试站，可回放） | 待裁决 |
| P5-02 | 低 | `hr.py:133`；`test_company_hr_lifecycle.py:163-172` | `clear_company_expense_claim_accounts` 的守卫查 `DocType "Expense Claim Account"`，同文件另两个入口查 `"Expense Claim Type"`。SL-011 ⑤① 的测试只让 `Expense Claim Type` 答否，并且先手删了该公司全部报销行：`clear…` 实际照常跑 count＋delete，返回 0 只因为本来就没有行。去掉守卫测试也照样绿，没有判别力。真实站点两张表同存同亡，所以产品行为没问题 | `开发守则`「判据必须能区分它要区分的两种情形」；SL-011 ⑤① | 守卫统一改查 `Expense Claim Type`（与 `:31`、`:85` 一致）；或测试同时 patch 两个 DocType，且不先删行、改为断言 `frappe.db.delete` 没被以 `Expense Claim Account` 调用 | 新Session修 | — | 待裁决 |
| P5-03 | 低 | `hr.py:89-98`、`:114-125` | `repoint` 判「通用科目」的口径是该公司**任何**无号明细科目，不只 HRMS 建的那个。只要用户在中式公司手建一个不填科目号的科目，并设成某报销类型的默认科目，下次保存公司就会把这一行改挂到映射科目，并在该科目无 GL、无链接时**不带日志地删掉它**（`deleted` 只进返回值，`on_update` 把返回值丢了；只有 `kept` 有 warning）。DEC-027 的失效条件已经预见到这种情形，但两点没写进 README：会删用户的科目，而且删了不留痕迹 | DEC-027 失效条件；方案「已有的不覆盖」（只覆盖到有号科目，SL-012 ④）；`开发守则`「静默失败自成一类」 | 至少给删除也打一条 warning，并在 README「已知限制」补一句「中式公司的报销类型不要指向无号科目，保存公司时会被改挂、该科目会被删」；收不收窄判定（例如只认这次请求里新建的科目）交用户定 | 新Session修 | 只补日志＋README（接受 DEC-027 的边界），还是收窄改挂判定 | 待裁决 |
| P5-04 | 观察 | `hr.py:23-25`；R6 C 讨论记录 LG-014 | `expense_claim_account_number` 的译名分支按**当前会话语言**比对 `_()`。如果站上的报销类型是中文名，而补配发生在 `en` 上下文（如 `bench install-app` 后的 `after_app_install`，F11 说那时 `lang` 是 `en`），译名就命中不了，会落到兜底 `5602250`；行写下后「不覆盖」，错映射会一直留着。实测两站的类型名都是英文，所以这个风险目前没有触发；LG-014 的问题其实已经有答案（演示站是英文名），但台账还标着「待验证」 | DEC-028；LG-014 | 关闭 LG-014（演示站实测英文名）；README 或 LG-011 补一句「报销类型改成中文名时，在 zh 会话下保存公司才能按译名命中」 | 延迟或不修 | — | 待裁决 |
| P5-05 | 观察 | `cn_tax/data/company_defaults.json:33-34` | 有 `},  "item_group_expense": {` 两个键挤在一行的排版瑕疵（R4 `1193f94` 引入）。R6 TS-018 改了这个文件、没顺手修。JSON 能正常解析，不影响功能 | 可读性 | 下次改这个文件时换行 | 延迟或不修 | — | 待裁决 |
| P5-06 | 观察 | 提交 `a82499f`；R7 D 回执头部 | R7 回执只写了 Codex 的提交 `8433978`，没写续做的提交号。续做的 `a82499f` 还把 SB 的 IT-006（`test_expense_claim.py`）和 IT-014（删 `run_report`）一起打进了同一个提交。改动本身都由各自的回执申报过，不算夹带，但按 Round 回溯时要拆开看 | 可追溯性 | 以后续做的回执写明提交号；跨 Round 的改动分开提交 | 延迟或不修 | — | 待裁决 |

## 本片盲区自述

- **没有实跑**：只读约束加上主会话正在回归，本片没跑专项、没做变异，验证门数字只核了日志结尾与测试方法数。TS-017～019 的判别力变异全部采信 R7／R8 的描述，这是本片把握最低的一块。
- **没往这些方向找**：从界面（`company.js`）删公司、批量删除（`delete_bulk` 逐个 commit）这两条路径下 `on_trash` 的表现只读了码、没构造场景；`Transaction Deletion Record`（删公司交易）与本片清理的交互没查；`parent_company` 子公司路径只读了 `erpnext.set_chart_of_accounts`，没有测试覆盖。
- **拿不准处**：
  - P5-01 算产品缺陷的残留还是纯测试数据，取决于演示站有没有被强删过公司。演示站只读查询无悬空，所以定为低。
  - P5-03 定「低」还是「观察」在边界上：DEC-027 已明文接受这个失效条件，但「删用户科目且无日志」超出了讨论记录写到的程度，所以定为低。
  - `is_cn_company` 断链（源公司不存在）时判否：本片推断源公司因 Link 不能不带 `force` 删除，所以实际不会断链，这一点没有在站点上实测。
- **范围之外**：R3 Part1 TS-005 的原始实现（入口 1／2、`backfill`）只核了与本片的接口，没有逐条审，那是别的片的事；LG-015（backfill 漏复制建账的公司）已登记暂缓，没有重复报。
