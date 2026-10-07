# F 审核分片报告·片 2（对象：方案 Part2 SL-003～004／TS-006～008 的站点状态与支撑代码 / 审核标准：B 需求文档 §4.3、§4.4、AC-002、AC-006，RS-001／002）

**轮次**：P1-S5-R9｜**步骤**：F 分片 2｜**日期**：2026-10-07｜**执行者**：Claude 子 Agent（只读）
**依据**：[R3 开发方案 Part2](../R03-开发方案/P1-S5-R3-C开发方案-Part2.md)（全文逐条）＋[总纲](../R03-开发方案/P1-S5-R3-C开发方案-总纲.md)；[B 需求文档](../R02-需求文档/P1-S5-R2-B需求文档.md) §一～二、§4.1～4.4、§4.10～4.11、§五～六、§八、§十；`docs/开发守则.md`、`docs/业务规则.md`
**被审范围**：`frappe_china` `03fde72..4b21aae` 中与本片相关的 `install.py`、`hooks.py`、`translations/zh.csv`、`company_defaults.json`、`tests/test_install.py`；主仓库 `c372a94..2fb2641 -- docker/` 中 `apps.json`、`scripts/setup.sh` 第 6／6.2 段；两站 `test.localhost`／`erx.localhost` 的站点状态；`docker/backups/` 三个基准点；回执 [D 回执 Part2](../R04-代码/P1-S5-R4-D回执-Part2.md)、[SB 修复回执](../R05-确认报告/P1-S5-R5-SB修复回执.md) IT-005／018／026 行

## 覆盖自证

- **读全的依据**：F Spec、`bricks/audit.md`、`bricks/sharding.md`、流程规范 §2.2～2.3、开发守则全文、业务规则全文、方案总纲全文、Part2 全文、需求文档（§一、§二、§四 4.1～4.4、4.10～4.11、§五、§六、§八 AC 全表、§九、§十）、Stage 概况（含延迟登记册 SH-P1S5001～008）、D 回执 Part2 全文、SB 回执全文；R5 E 报告与 R8 E 报告只当索引读（R5 §问题详情 IT-001～012、IT-024～028、当场修清单与反证表；R8 全文前 60 行）。
- **逐行读的代码**：`frappe_china/install.py` 全文（157 行）；`accounting/selfcheck.py` 全文；`accounting/hr.py` 全文；`accounting/company.py` 的 S5 diff；`hooks.py`／`zh.csv`／`company_defaults.json`／`README.md` 的 S5 diff；`tests/test_install.py:170-240`；`docker/apps.json` 全文；`docker/scripts/setup.sh` 的 S5 diff；Spike `P1-S5-R5-IT005-demo-site-verify.py:100-175`。
- **对照的上游**：frappe `installed_applications.py:20-200`、`__init__.py:924-1010`（`get_installed_apps`／`get_hooks`／`_site_cached_load_app_hooks`）、`cache_manager.py:110-125、281-313`、`utils/caching.py`（`site_cache`）、`utils/redis_wrapper.py:233-258、596-650`、`installer.py:370-376`、`translate.py:132-236`、`gettext/translate.py:41-62、345-360`、`commands/site.py:550-575`、`commands/utils.py:137-151`、`utils/change_log.py:105-130`；hrms `hooks.py`（全部键名；`override_doctype_class`、`doc_events`、`get_matching_queries`、`period_closing_doctypes`）、`overrides/employee_payment_entry.py` 全文、`overrides/company.py:12-135、171-196`、`hr/doctype/expense_claim/expense_claim.py:911-955`、`hr/utils.py:846-886`、`setup.py:34-41`、`locale/zh.po:4218-4226`；erpnext `payment_entry.py:585-630、743-749、2807-2820`、`bank_reconciliation_tool.py:964-1000、1190-1270`；crm `hooks.py` 覆盖段、`overrides/contact.py`、`erpnext_crm_settings.py:606-626`；四个业务 app 的 `override_whitelisted_methods`（grep）。
- **跑过的只读查询**：两站 `site_config.json` 的 `installed_apps`；两站 `tabInstalled Application`、全局 `installed_apps`、`tabCompany`、科目数、`tabExpense Claim Account`、`tabExpense Claim Type`、`Expense Claims` 科目；两站 `frappe_china.install.check_app_order`（先读码确认只读：只读库、读 hooks、读译文文件，`get_all_translations` 缺键时会回填 redis 合并译名缓存，属缓存、不写库）；两站 `get_hooks("doc_events")`（Company／Payment Entry／Sales Order／Journal Entry／`*`）、`get_hooks("override_doctype_class")`、`get_controller("Payment Entry")`（独立 python 进程 `frappe.init/connect` 只读）；演示站业务与痕迹计数 22 类（GL、SLE、客户、供应商、物料、各类发票、JE、PE、SO、报价、CRM Lead／Deal／Product、联系人、地址、Translation、Insights 四表）、`tabDeleted Document`（10-05 起）、`tabVersion`（DefaultValue；10-07 起；基准点后）、`tabSeries`、`tabActivity Log`、`tabError Log`、System Settings、`tabProperty Setter`（Employee）、HR Settings；测试站 `tabVersion`（DefaultValue 调序五条）、`tabDeleted Document`（Company）、`tabModule Def` 装 app 时刻；四个官方 App 与 `frappe_china` 的 HEAD／remote／`core.fileMode`／`status`；`sites/apps.txt`；`docker/backups/` 目录、三个基准点 `site_config_backup.json`、根目录与 `保留-*` 副本的 md5；`20261004_005331` 与 `20261007_003913` 数据库转储的逐表逐行比对（时间戳与 10 位随机 id 归一后）；回归日志 `s5-r8-regression.log`、`s5-sb-final-regression.log` 结尾；`s5-sb-it005-up.log` 关键行；Spike `IT005-demo-site-verify.log`。
- **跳过的及原因**：未跑 `run-tests`（本片只读，主会话在跑全量回归；验证门数字取日志，见自证复核）；未重做 TS-008 第 4 步反证（写操作）；未在运行中的 `bench start` web 进程里取钩子（须发请求或注入，属干扰）——P2-01 的「进程层」结论是读码推断；SL-003 ②⑤（`_FCT 入口二` 装 HRMS 前后状态）已不可复现，只核了时间线；未核 `setup.sh` 第 3／4 段与 `lock-apps.sh`（Part1 范围，片 1）；Part3／Part4 的 CRM、Raven、Insights 配置值只记集成点，不判。

## 逐项落地核查

| 意图层依据 | 要求层要求（方案任务／验收条款逐条） | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| §4.3 测试站先行 | TS-006 ① 取四个 App、锁 commit、只读 `upstream`、`core.fileMode false`、`apps.txt` 含四个 | `apps/{crm,hrms,insights,raven}` HEAD；`sites/apps.txt` | ✅ | ✅ | 四个 HEAD 与 `apps.json` 一致；remote 只有 `upstream`、push=`DISABLED_use_origin_instead`；`fileMode=false`；工作区空 |
| §4.3 第 4 条 | TS-006 ② 装 HRMS 前建 `_FCT 入口二` | 测试站 `tabDeleted Document`：`_FCT 入口二` 原 `creation` 19:20:38，`Module Def` HR 19:21:04 | ✅ | — | 只核时间线（建于装 HRMS 前 26 秒）；装后 5 行、266 已不可复测（R5 同判） |
| §4.3 第 1 条、A11 | TS-006 ③ 次序 crm→hrms→raven→insights | 测试站 `Module Def`：FCRM 19:16、HR 19:21、Raven 19:23:05、Insights 19:23:48；`tabInstalled Application` idx raven 6／insights 7 | ✅ | — | 与 A11 一致 |
| §4.2.1 归位 | TS-006 ④ 归位、清缓存、重启 `bench start` | 测试站 `tabVersion` 19:24:47 调序一条 | ⚠️ | ⚠️ | 调序有留痕；D 回执写「重启容器」而非重启 `bench start`（R5 IT-028 已处理容器重建后果）。进程层是否刷新见 P2-01 |
| AC-006、LG-003 | TS-006 ⑤ `zh`／`en` 各保存一次，266、无 `Expense Claims`、`check_company_chart` ok | 测试站已不可复现；`tests/test_expense_claim.py:118-130` `test_7_saving_in_zh_and_en_keeps_chart` | ✅ | ✅ | 由单测覆盖（R5 SB IT-006 补的），日志 `s5-r8-regression.log` 205 条全过 |
| LG-139 | TS-006 ⑥ 打出 `Company.on_update` 实际次序 | 两站实测 `get_hooks("doc_events")["Company"]` | ✅ | ✅ | `on_update`：hrms 三个 → `frappe_china.on_update`，与 D 回执一致；另实测 `validate`：hrms → frappe_china；`on_trash`：hrms `handle_linked_docs` → frappe_china |
| AC-005、RS-002、HT-011 | TS-006 ⑦ 全量回归全过、不过即停 | `logs/s5-r8-regression.log`：Ran 205、OK、EXIT=0 | ✅ | ✅ | 未亲跑（见覆盖自证）；`Payment Entry` 控制器已是 `hrms…EmployeePaymentEntry`（两站实测），S4 用例确在该类上跑。HRMS 新开的员工付款路径未覆盖，见 P2-03 |
| SL-003 ⑥ | TS-006 ⑧ 删测试公司、无 `_FCT` 公司 | 测试站 `tabCompany` | ⚠️ | — | 现存 `_FCT CRM 验证`（R8 IT-030 已裁「保留、不做」，不重报）；`_Test Company`／`_Test Company 1` 是 HRMS `before_tests` 所建（R5 IT-027 已记） |
| RS-010 | TS-007 ① 核 `20261004_005331` 4 个文件在根目录 | `docker/backups/` | ✅ | ✅ | 4 个文件在根目录 |
| RS-010 | TS-007 ② `backup.sh` 并另存 `保留-S5装App前/` | `backups/保留-S5装App前/20261007_003913-*` | ✅ | ✅ | 4 个文件，数据库包 md5 与根目录同名文件一致（`5d0345af…`）；内容与 `005331` 逐行比对仅多 3 条登录 `Activity Log` 与 3 条 `Sessions`（归一时间戳与随机 id 后），与项目概况「内容同 005331」相符 |
| §4.3 演示站第 2 条 | TS-007 ③ `up.sh`：HRMS 补配打印、6.2 段 `changed: True` 与目标顺序 | `frappe-bench/logs/s5-sb-it005-up.log:77、104、131` | ✅ | ✅ | `backfill: {'华东弹簧有限公司': [5 类]}`；`changed: true`，`after` 为目标顺序；`EXIT=0` |
| §4.3 演示站第 2 条 | TS-007 ④ 重启 `bench start` | 容器内 honcho／`frappe serve` 进程起于容器时间 01:17:07 | ✅ | — | 在 SB 之后又重起过一次（R8 或之后）；本片不追溯 |
| AC-006、§4.3 演示站第 3 条 | TS-007 ⑤ HDTH 5 行与映射一致；`zh` 下保存一次；266；`extra_accounts` 空；无 `Expense Claims` | 演示站 `tabExpense Claim Account`、`tabAccount`；`check_app_order` 内 `check_all_cn_companies`；`IT005-demo-site-verify.log:11-51` | ✅ | ✅ | 现状：5 行科目号 5602090／5602040／5602010／5602250／5602130 与 `company_defaults.json` 一致；266；无 `Expense Claims`；HDTH `modified` 00:51:27（那次 `zh` 保存）。**`en` 下未保存**，见 P2-05 |
| AC-010、SL-004 ⑥ | TS-007 ⑥ 空账核对 8 类为 0 | 演示站计数 | ✅ | ✅ | 8 类均 0；另扩查 PE、SO、报价、CRM 三表、联系人、地址、Translation、Insights 三表均 0 |
| AC-002 | TS-008 ① 接口契约 `PROBE_SOURCE`／`WHITELIST_TARGETS`／`AppOrderCheck` 九键 | `install.py:7-24` | ✅ | ✅ | 字段与类型与契约一致；`WHITELIST_TARGETS` 与 `hooks.py:205-209` 三个键相同 |
| AC-002 第 1 项 | `order_ok`：`frappe_china` 在全部已装业务 app 之后 | `install.py:45-49` | ✅ | ✅ | 与方案伪码一致 |
| AC-002 第 2 项 | `overrides`／`overrides_ok`：三个键 `[-1]` 以 `frappe_china.` 开头 | `install.py:51-56` | ✅ | ⚠️ | 代码对；但站上无任何业务 app 注册这三个键（grep 四个 app 与 erpnext），故真调序时它恒为真、无判别力，见 P2-01 |
| AC-002 第 3 项 | 撞源词：expected 读 csv、competitors 读各业务 app csv｜mo、actual 读 `get_all_translations`；无竞争者／无 expected 判探针失效 | `install.py:27-38、58-68、80-88` | ✅ | ✅ | 写入端：`frappe_china/translations/zh.csv:129` `Formula,计算方式`（S4 `ee5fe6a` 加，非本轮）；竞争端：`hrms/locale/zh.po:4225-4226` `公式`，`sites/assets/locale/zh/LC_MESSAGES/hrms.mo` 在；crm／insights／raven 无该条；读取端合并顺序 `translate.py:172-187`。两站实测 expected＝actual＝「计算方式」、competitors `{hrms: 公式}` |
| AC-002 第 4 项 | `company_checks_ok`＝`check_all_cn_companies()` 全 ok；无中式公司注明 | `install.py:70-73、89-92`；`selfcheck.py:132-143` | ✅ | ✅ | 两站 `company_checks_ok` 真 |
| 开发守则「不静默」 | `problems` 每项一句话；读译文出错写进 problems | `install.py:36-37、75-92` | ✅ | ✅ | R5 IT-011 修后形态 |
| §2 边界 | `check_app_order` 只读、不 import 业务 app | `install.py:41-109` | ✅ | ✅ | 无业务 app import；无写库 |
| — | TS-008 ② 测试三条：当前站 ok（HRMS 不在 skip）；patch 顺序 → `order_ok` 假；patch hooks 末项被盖 → `overrides_ok` 假 | `tests/test_install.py:173-215` | ✅ | ✅ | 另有两条探针失效用例（`:217-240`）；`s5-r8-regression.log:151-155` 五条全 ✔ |
| AC-002、SL-004 ④ | TS-008 ③ 演示站 `check_app_order` `ok` 真 | 本片实跑 | ✅ | ✅ | `ok`／四项全真、`problems` 空 |
| AC-002「不调序时失败」、HT-004、RS-003 | TS-008 ④ 测试站真调序 a～e，含重启 `bench start` | 测试站 `tabVersion` 2026-10-06 14:18:37（→ `crm, frappe_china, hrms…`）、14:19:03（→ 目标顺序）；R5 E 报告反证表 | ⚠️ | ⚠️ | 调序与回调都有留痕，c 步 `ok／order_ok／translation_ok` 假、actual「公式」，e 步复真——**翻译层反证可信**。但 b、d 步没重启 `bench start`（R5 已申明「当时未运行」），用的是每次新起的 `bench execute` 进程：HT-004 的「进程内缓存」一半没被验到；`overrides_ok` 在 c 步仍为真。见 P2-01 |
| A5、LG-010 | `reorder_installed_apps` 同步 `site_config.json` 镜像 | `install.py:124-140` | ✅ | ⚠️ | 两站 `site_config.json` 已同步；**`tabInstalled Application` 未同步**，`bench list-apps` 读它，见 P2-02 |
| §4.11「不用 `override_doctype_class`」 | `frappe_china/hooks.py` 无 `override_doctype_class` | `hooks.py` | ✅ | ✅ | 无；站上类覆盖来自 hrms（4 个）与 crm（Contact、Email Template），见 P2-06 |
| 方案 TS-008 验证方式 | 约定「装完新 app 后 reorder＋check_app_order」进 D 回执「新增约定」 | D 回执 Part2「新增约定」；`docs/开发守则.md`「装完任何新 app 后让 `frappe_china` 归位并验」 | ✅ | ⚠️ | 已入开发守则；其中「以 `check_app_order` 验……顺序对而缓存或进程没刷新时，覆盖仍不生效」一句对进程层过度声称，见 P2-01 |
| 夹带检查 | 本片代码范围内方案外改动 | `install.py` 全文；`zh.csv` 新增行 | ✅ | — | 无方案外改动。`zh.csv` 本轮唯一新增 `Realtime check received: {0}` 属 Part4 TS-013（`public/js/realtime_check.js:3` 使用），他 app `zh.po` 无同源词、无竞争 |

## 业务规则合规核

| 规则条款 | 是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 涉及（报销映射目标科目） | 合规（规则本身未经专家确认） | 两站 HDTH／`_FCT CRM 验证` 5 行全指向 266 科目表内的明细科目（科目号与 `company_defaults.json` 一致）；映射表本身仍「待领域专家确认」（需求 §4.2.2、LG-011） |
| BR-002 报表含现金流量表 | 涉及（HRMS 打开员工付款路径后的现金流量预填） | **草案·待领域专家确认** | 员工报销款按 `party_type=Employee` 预填「4 支付的职工薪酬」，按准则应归「支付其他与经营活动有关的现金」——AI 推断，见 P2-03 |
| BR-003 增值税税率 | 不涉及 | — | 本片无税率改动 |
| BR-004 增值税月末结转 | 间接涉及（月结草稿检查） | 合规（S4 行为未变） | `closing.py` 未改；HRMS 新增过账单据不在草稿检查表，见 P2-03（工程覆盖，非规则违背） |
| BR-005 附加税 | 不涉及 | — | — |
| BR-006 资产负债表恒等 | 不涉及 | — | 本片无过账 |
| BR-007 价税分离 | 不涉及 | — | 测试站 `rounding_method` 现为 Commercial（R5 IT-027 已修）；演示站 System Settings `Commercial Rounding`、`Asia/Shanghai`，未被 HRMS 改写 |
| 规则新增／变更 | 本轮无新增 | — | 需求 §4.10 声明不新增；本片检出一条 AI 推断的候选（P2-03，草案） |

## 集成点登记（交接摘要）

- **跨片共享状态·装序**：两站全局 `installed_apps` 与 `site_config.json` 均为 `frappe, erpnext, crm, hrms, insights, raven, frappe_china`；两站 `tabInstalled Application` 的 idx 仍是装的先后（`frappe_china` 第 3；测试站 raven 6／insights 7，演示站 insights 6／raven 7）——`bench list-apps` 读后者（P2-02）。两站 `developer_mode=1`（钩子走进程内 `site_cache`，影响 P2-01）。
- **跨片共享状态·apps.json**（依赖片 1）：四条 `official: true`；Insights `tag: v3.14.2`、commit `5447f162`；crm `deedce73`、hrms `6f5ac249`、raven `e890308e`、`frappe_china` `4b21aae`——本片核到磁盘 HEAD 一致。
- **暴露的接口契约**：`frappe_china.install.check_app_order() -> AppOrderCheck`（九键；`PROBE_SOURCE="Formula"`，唯一竞争者 `hrms`）；`reorder_installed_apps() -> {changed, before, after}`（片 1 的 `setup.sh` 6.2 段与人工修复共用；只同步 `site_config`，不同步 `tabInstalled Application`、不发 `erase_persistent_caches`）；`target_app_order(installed)`。S8G-S1 IM-007 将接 `after_migrate`。
- **依赖的接口契约**（片 1）：`after_app_install = frappe_china.install.after_app_install` → `hr.backfill_cn_expense_claim_accounts()`；`Company` 的 `before_insert／validate／on_update／on_trash` 四钩子；`check_all_cn_companies()`（S4）。
- **共享状态·company_defaults.json 键**：`expense_claim_type`（Calls／Food／Medical／Others／Travel → 5602090／5602040／5602010／5602250／5602130）、`expense_claim_type_fallback`=5602250。
- **钩子实测次序**（LG-139）：`Company.on_update` hrms×3 → frappe_china；`validate` hrms → frappe_china；`on_trash` hrms → frappe_china。`Payment Entry` 控制器＝`hrms.overrides.employee_payment_entry.EmployeePaymentEntry`；`Sales Order.before_validate`＝crm 建客户；`*` 五个写事件挂 raven 文档通知。类覆盖另有 crm 的 Contact、Email Template。
- **站点数据**：演示站 HDTH 5 行 `Expense Claim Account`、266 科目、`default_payroll_payable_account`／`default_expense_claim_payable_account` 均空；HR Settings `emp_created_by=Naming Series`（HRMS 装时改的 Employee 命名 Property Setter 4 条）；演示站 `Raven Bot` `ERX 分析助手`、`Raven AI Function` 15 条、`CRM Settings` 版本记录 00:52（片 3 范围）；测试站留 `_FCT CRM 验证`（片 3 的 IT-017 脚本依赖它）。
- **备份基准点**：根目录 `20261004_005331`（S4 基准）、`20261007_003913`（＝005331＋3 次登录）、`20261007_011313`（当前空账基准、`restore.sh` 默认取它；`site_config_backup` 已含七 app）；后两者在 `保留-S5装App前／后/` 有 md5 一致的副本。基准点之后演示站无 `Version`／`Deleted Document`／公司修改。
- **译名**：`zh.csv` 本轮新增 1 行（Part4 `realtime_check.js` 用，无竞争）；`Formula` 探针行是 S4 的，S6 改译名时若动这行须同步换探针。

## 自证复核

| 被审产物声称 | 实际复核 | 一致否 |
|---|---|---|
| D Part2：测试站 `installed_apps` 为目标顺序 | 全局值与 `site_config` 均为目标顺序 | ✅ |
| D Part2：`Company.on_update` 次序（hrms×3 → frappe_china） | 两站实测相同 | ✅ |
| D Part2：测试站 `check_app_order` 四项真、`Formula` 期望／实际「计算方式」、竞争「公式」 | 本片实跑相同 | ✅ |
| D Part2：反向 `ok／order_ok／translation_ok` 假、实际「公式」 | `tabVersion` 两次调序留痕（10-05 20:27／20:29、10-06 14:18／14:19）；R5 反证表；未列 `overrides_ok`——读码与反证表均表明它当时仍真 | ✅（但见 P2-01） |
| D Part2：TS-006 第 4 步「重启容器」 | 方案要求重启 `bench start`；R5 已处置后果（IT-028） | 已报，不重报 |
| SB IT-005 ①：`005331` 在根目录；`003913` 已另存 | 文件在；副本 md5 一致 | ✅ |
| SB IT-005 ②：`up.sh` EXIT=0、HRMS 补配打印 5 类、6.2 段 `changed: true` | `s5-sb-it005-up.log:77、104、131` | ✅ |
| SB IT-005 ③：HDTH 5 行映射一致、保存前后 266、`extra_accounts` 空、无 `Expense Claims` | 现状一致；HDTH `modified` 00:51:27 | ✅ |
| SB IT-005 ④：演示站 `check_app_order` 全真、`problems` 空 | 本片实跑一致 | ✅ |
| SB IT-005 ⑥：GL、SLE、客户、供应商、物料、发票、JE 均 0；无 `_FCT` 公司 | 一致，扩查 14 类亦 0 | ✅ |
| SB：七个 app 均在锁定 commit、工作区空 | 四个官方 App＋`frappe_china` HEAD 与 `apps.json` 一致、`status` 空 | ✅ |
| SB IT-018／复核建议 2：演示站 `Deleted Document` 新增「两个工作簿、两个查询共 4 条」，给的查询为 `creation > '2026-10-07'` | 该查询实得 **8 条**：另 4 条是 00:41:51 HRMS 装时删的 Employee 命名 Property Setter | ⚠️ 不一致（P2-04） |
| SB IT-018：`tabSeries` `Insights Workbook`=2；现余 1 条执行日志 `sig4mp22ku`（00:42） | 一致 | ✅ |
| SB IT-026：新基准点 `011313` 另存、`restore.sh` 取它为最新 | 根目录最新一套即 011313，副本 md5 一致；其 `site_config_backup` 含七 app | ✅ |
| 项目概况：`003913` 内容同 `005331` | 逐表逐行比对（归一时间戳与随机 id）仅差 3 条登录 `Activity Log`／`Sessions` | ✅ |
| R8：全量 205/205 | `s5-r8-regression.log`：Ran 205、OK、EXIT=0（读日志，未亲跑） | ✅（未亲跑） |
| 开发守则：「以 `check_app_order` 验……顺序对而缓存或进程没刷新时，覆盖仍不生效」 | `check_app_order` 总在新进程里跑，测不到运行中 web／worker 的进程内钩子缓存；覆盖项无竞争者恒真 | ⚠️ 过度声称（P2-01） |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P2-01 | 低（边界：中） | `frappe_china/install.py:51-56、124-140`；`docs/开发守则.md`「装完任何新 app 后让 `frappe_china` 归位并验」第 3 条；上游 `frappe/__init__.py:1003-1004`、`cache_manager.py:311-313`、`installer.py:375`、`redis_wrapper.py:615-650` | **`check_app_order` 的判别力比开发守则写的窄。** ① 覆盖项：四个业务 app 与 erpnext 都不注册那三个 whitelisted 键，`overrides_ok` 在真调序时恒真（R5 反证 c 步只有 order、translation 两项报错）；只有单测的 patch 能让它为假。② 进程层：两站 `developer_mode=1`，钩子缓存在各进程的 `site_cache` 里；`reorder_installed_apps` 调的 `frappe.clear_cache()` 只清本进程的 `_SITE_CACHE`，不像装 app 那样发 `erase_persistent_caches()`。所以不重启时，运行中的 web／worker 仍按旧顺序取钩子，而 `bench execute check_app_order` 新起一个进程，照样报 `ok`。TS-008 第 4 步反证没重启 `bench start`（R5 申明），HT-004 的「重启进程」一半实际没验到。现在不出错，是因为开发守则第 2 步要求重启 | 开发守则「判据必须能区分它要区分的两种情形」；HT-004／RS-003；AC-002「同一检查在不调序时失败」（翻译项满足，覆盖项与进程层不满足） | (a) 改开发守则那句：写明 `check_app_order` 只证库、redis 缓存与新进程的状态，运行中进程靠第 2 步重启；`overrides_ok` 在没有竞争注册者时恒真。(b) 可选：`reorder_installed_apps` 末尾补 `frappe.client_cache.erase_persistent_caches()`，让运行中进程丢掉钩子缓存（读码，须带着 `bench start` 实测） | 本Session修 | 只改文字 (a)，还是 (a)＋(b)（(b) 动代码，要在测试站起着 `bench start` 验） | 待裁决 |
| P2-02 | 低 | `frappe_china/install.py:136-138`；上游 `commands/site.py:562`、`installed_applications.py:29-60`；两站 `tabInstalled Application` | 归位只改全局 `installed_apps` 和 `site_config` 镜像，没改 `Installed Applications` 子表。`bench list-apps` 按这张表显示，两站都列成 `frappe, erpnext, frappe_china, crm, hrms, …`，和真实装序不一样。下次 `migrate` 时 `update_versions()` 会按 `get_installed_apps()` 重写，这时才自愈 | A5 自己的理由：「镜像与数据库不一致会误导排查」，这张表同理；开发守则「判据必须能区分」（看 `list-apps` 判装序会得出错结论） | 归位后调 `frappe.get_single("Installed Applications").update_versions()`；或在开发守则／README 注一句「`list-apps` 不反映装序，看 `check_app_order` 的 `order`」 | 本Session修 | 改代码，还是只加注明 | 待裁决 |
| P2-03 | 低 | `hrms/hooks.py:155-160`；`hrms/overrides/employee_payment_entry.py:22-30、45-51`；`frappe_china/fixtures/cash_flow_code.json:34-39`；`cn_tax/doctype/cash_flow/cash_flow.py`（`_assign_default_codes`）；`accounting/closing.py:21-30、220-230` | RS-002 只靠 S4 全量测试验证。读码对照：`EmployeePaymentEntry` 对 Customer／Supplier 的语义没变（`get_valid_reference_doctypes` 两支相同；`set_missing_ref_details` 非员工单据仍走原 `get_reference_details`），PE／JE 新增的 hrms 钩子遇到非报销引用时直接返回，银行对账多出的匹配查询只在勾 `expense_claim` 时生效——**S4 路径无语义变化**。新打开的员工路径 S4 没覆盖：① 付给员工的报销款／借支（`party_type=Employee`）按 fixture 兜底预填现金流量「4 支付的职工薪酬」；按小企业准则，差旅等报销应是「6 支付其他与经营活动有关的现金」（**草案·待领域专家确认**）。② 月结草稿检查 `DRAFT_CHECK_DOCTYPES` 不含 HRMS 的过账单据（Expense Claim、Employee Advance、Payroll Entry、Leave Encashment、Gratuity），草稿报销单不拦月结（月结后提交会被 `_changed_after_closing` 发现）。另：HDTH 的 `default_expense_claim_payable_account` 为空，用户可能选 `2202 应付账款`（准则口径应是其他应付款） | 需求 §4.2.2 末段「`Payment Entry` 整类覆盖……只靠 TS-005 跑 S4 全量测试来验」；BR-002 | 本 Stage 不配人事数据（项目概况已知限制），建议登延迟，在 HRMS 报销真正启用前处理：员工往来的现金流量默认项目、月结草稿检查表、报销应付科目映射，三件一起交会计确认 | 延迟或不修 | 登记延迟（唤醒：IM-016 开工或演示要报销时），还是不做 | 待裁决 |
| P2-04 | 观察 | SB 回执「偏离与暂停」末条、「复核建议」2；演示站 `tabDeleted Document` 2026-10-07 00:41:51 四条 | SB 回执说演示站多出的非业务痕迹是 4 条 `Deleted Document`（Insights）。按它给的查询实得 8 条，另 4 条是装 HRMS 时 HR Settings 删掉并重建的 Employee 命名 Property Setter（`naming_series`／`employee_number` 的 hidden／reqd；现 `emp_created_by=Naming Series`）。不是测试数据，也已在新基准点里；但「装 HRMS 改了 Employee 命名方式」没写进回执，也没进项目概况 | audit 纪律 6「被审产物的声称一律复核」 | 本报告留档即可；S8G 建员工（IM-016）时知道命名方式已被 HRMS 改成按序列 | 延迟或不修 | — | 待裁决 |
| P2-05 | 观察 | 方案 Part2 TS-007 第 5 步；需求 AC-006 | AC-006 写「测试站新建中式公司与演示站保存 HDTH 后……`zh` 与 `en` 会话下各保存一次后科目数不变」。方案对 HDTH 只要求 `zh` 下保存一次，总纲 §六偏离表没列这处收窄。`en` 路径由测试站单测 `test_7_saving_in_zh_and_en_keeps_chart` 覆盖，演示站 HDTH 没在 `en` 下保存过 | 需求 AC-006；总纲 §六「相对需求的偏离」应列全 | 接受现状（单测已覆盖 LG-003，演示站少写一次），本报告留档 | 延迟或不修 | 是否接受单测代替演示站 `en` 保存 | 待裁决 |
| P2-06 | 观察 | `crm/hooks.py`（`override_doctype_class`：Contact、Email Template）；需求 §5.1；ADR-0004 | 需求 §5.1 和 ADR-0004 只记了 HRMS 的类覆盖。站上 CRM 还整类覆盖了 `Contact`、`Email Template`，目前只加了 `default_list_data` 静态方法，没有语义影响。但 ADR-0004「不用 `override_doctype_class`，否则会静默绕过别人的类覆盖」这条理由对 Contact 同样成立 | 需求 §5.1「直接影响」应列全 | S6／S7 要改 Contact 行为时走 `doc_events`；在 ADR-0004 或项目概况的覆盖清单里补一行 | 延迟或不修 | — | 待裁决 |

## 本片盲区自述

- **没往哪个方向找**：没进运行中的 web／worker 进程取钩子，P2-01 的进程层结论只有读码依据（`__init__.py:1003`、`cache_manager.py:311-313`、`installer.py:375`）；没亲跑全量回归，也没做变异，`check_app_order` 单测的有效性取 R5／R8 的记录；HRMS 的 `regional_overrides`（只对 India）、`accounting_dimension_doctypes`、`audit_trail_doctypes` 对 S4 的影响没逐个读；CRM 的 `Sales Order.before_validate` 对 S4 销售订单测试的影响只看到「订单已有客户就直接返回」，没跑。
- **把握最低处**：P2-03 的现金流量归类是 AI 依准则推断的（报销款进「其他经营活动」而非「职工薪酬」），没有原文依据，须会计确认；月结草稿检查要不要纳入 HRMS 单据，也取决于 S8G 怎么用 HRMS。
- **拿不准处**：① P2-01 定「低」还是「中」——开发守则第 2 步已要求重启，按守则做就不出错，所以定低；但守则第 3 步的措辞会让后来者以为「`check_app_order` 为真就够了」，若按「常驻文件里的错误判据」算可升中。② P2-02 是否算问题：上游本身就这样（`update_installed_apps_order` 也不改这张表），`migrate` 后自愈；按 A5 的同一理由列为低。③ SL-003 ⑥ 测试站留 `_FCT CRM 验证`、`_Test Company*`，已由 R8 IT-030 与 R5 IT-027 处置，本片未重报。
