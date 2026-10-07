# F 审核分片报告 · 片 1（对象：方案 Part1 SL-001～002／TS-001～005 的落地 / 审核标准：B 需求文档 §4.2）

**轮次**：P1-S5-R9｜**步骤**：F 分片 1｜**日期**：2026-10-07｜**执行者**：Claude 子 Agent（只读）
**依据**：[开发方案 Part1](../R03-开发方案/P1-S5-R3-C开发方案-Part1.md)（要求层，全文逐条）、[总纲](../R03-开发方案/P1-S5-R3-C开发方案-总纲.md)（A1～A5、§六第 1／2 行、§九）、[B 需求文档](../R02-需求文档/P1-S5-R2-B需求文档.md) §4.2.1／§4.2.2／§4.10／§八（意图层）、`docs/开发守则.md`、`docs/业务规则.md`
**被审范围**：`docker/apps.json`、`docker/scripts/setup.sh`、`docker/lock-apps.sh`、`docker/README.md`「版本记录」段（主仓库 `c372a94..2fb2641`）；`frappe_china`（`03fde72..4b21aae`）的 `install.py`、`accounting/hr.py`（Part1 部分）、`accounting/company.py` 的入口 1、`hooks.py` 相关行、`cn_tax/data/company_defaults.json`、`tests/test_install.py`／`test_expense_claim.py`／`test_scaffold.py`／`test_hr.py`

## 覆盖自证

**读全的依据**：F Spec、`bricks/audit.md`、`bricks/sharding.md`、流程规范 §2.2／§2.3、开发守则、业务规则、总纲、Part1、D 回执 Part1、Stage 概况（含延迟需求登记册 SH-P1S5001～008）；需求文档 §一～§四.4、§4.10～§十 全读（§4.5～§4.9 只略读，与本片无关）。R5／R8 E 报告只按关键词查了 Part1 相关行（IT-006～009、IT-011、TS-001～005 行），当作「已核过什么」的索引，结论都自己重核过。另读了 R6 C 方案中改动 Part1 函数的段落（§接口契约、对 Part1 TS-005 的更正行），用来区分「R6 有意改的」和「被 R6 改坏的」。

**逐行读的代码**：`setup.sh` 第 1～420 行（0～9 段全读，重点第 3、4、6、6.2 段）；`lock-apps.sh` 全文；`apps.json` 全文；`install.py` 全文；`hr.py` 全文；`company.py` 全文；`hooks.py` 全文；`company_defaults.json` 全文；`test_install.py`、`test_expense_claim.py`、`test_hr.py`、`test_scaffold.py` 全文；`tests/utils.py` 的 S5 diff；两仓 S5 区间的完整 diff（docker 三个脚本与 README；frappe_china 的 `company.py`／`hooks.py`／`company_defaults.json`／`README.md`／`zh.csv`／`utils.py`）。

**对照的上游**（只读）：frappe `installed_applications.py:108-145`（`update_installed_apps_order`）、`installer.py:340-392`、`:655-680`（`install_app` 钩子次序、`_sync_installed_apps_to_site_config`、`update_site_config`）、`__init__.py:924-942`（`get_installed_apps`）与 `:990-1012`（`get_hooks` 的两层缓存）、`cache_manager.py:20-40`、`:281-320`、`utils/caching.py`、`redis_wrapper.py:600-666`（`erase_persistent_caches` 与进程内缓存）、`translate.py:135-190`、`commands/utils.py:263-320`（`bench execute` 自动 commit 并打印返回值）；HRMS（锁定 commit `6f5ac249`）`overrides/company.py:100-140`、`hooks.py:173-181`、`setup.py:1-40`、`:338-342`；ERPNext `company.py:535-545`（`validate_coa_input`）；容器内 bench `app.py:122-194`（`--branch` 取 tag）、`utils/app.py:176-227`。

**只读查询与实跑**：
- 两站 `tabDefaultValue.installed_apps`、`site_config.json` 的 `installed_apps`、`developer_mode`；`tabCompany`；`tabExpense Claim Account` 连 `tabAccount`（科目号、`is_group`、建立时间）；`tabExpense Claim Type`；各公司科目数；名为 `Expense Claims`／`费用报销记录` 的科目；`tabVersion` 中 `installed_apps` 的调序记录；`tabModule Def` 各 app 的最早建立时间（用来推装 app 的时间线）。
- 宿主跑 `git ls-remote --exit-code --heads --tags`：四个有效 ref 各一次、坏 tag `v3.99.9` 一次。
- 七个 app 仓库的 HEAD、分支或游离状态、精确 tag、remote 与 push 地址、tracking 配置。
- `bash -n` 两个脚本；`company_defaults.json` 解析；`lock-apps.sh --show`；`lock-apps.sh` 写入模式在**仓库外临时副本**上跑两次（原样一次、删掉 raven 条目一次），跑完已删副本，`git status` 干净。
- 在本机 bash 里模拟 `setup.sh` 第 4／6 段的循环守卫与 awk 判「未声明」的逻辑。
- 用 `git show` 数了 `03fde72`／`1193f94`／`4b21aae` 三个点上各测试文件的用例数。

**跳过的及原因**：
- **`run-tests` 未跑**（任务禁止，主会话正在跑全量回归）。Spec 的「验证门亲自实跑」本片做不到。测试是否通过只能读码判断，没有实测数字。
- **Ruff 未跑**：容器与宿主都没装 ruff，回执说的「未执行」至今仍是这样。
- **`setup.sh` 端到端未跑**（写操作；已登记延迟 SH-P1S5008）。
- 容器内 `ls-remote` 失败（rc=128，连 `127.0.0.1:7897`）：cwd 在 `/workspace` 下时会继承主仓库 `.git/config` 的宿主代理。`setup.sh` 用 `GIT_CONFIG_*` 注入代理绕开了这一点（`setup.sh:52-54`），所以改在宿主上跑预检。
- `configure_apps.py` 是否读 `apps.json` 没查，归片 3。

## 逐项落地核查

| 意图层依据 | 要求层要求（方案任务／验收条款逐条） | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| §4.2.1 表、DEC-001／002／015 | TS-001：共 7 条，顺序 `frappe, erpnext, crm, hrms, insights, raven, frappe_china` | `docker/apps.json:1-49` | ✅ | ✅ | `lock-apps.sh --show` 按此顺序列出 |
| 同上 | 四个新条目 `official: true` | `apps.json:19,26,33,40` | ✅ | ✅ | — |
| 同上 | commit 40 位，前缀分别为 `deedce73`／`6f5ac249`／`5447f162`／`e890308e` | `apps.json:17,24,31,38` | ✅ | ✅ | 宿主 `ls-remote`：crm `main`、raven `main` 分支头与锁定值相同；insights tag 指向 `5447f162`；hrms `version-16` 分支头已前进到 `7c037698`，锁定 commit 在本地仓库存在（HEAD 即它），符合 TS-001「只核 commit 存在」的退路 |
| DEC-015 | Insights 用 `tag: v3.14.2`、不写 `branch` | `apps.json:30` | ✅ | ✅ | — |
| A1～A3 | README「版本记录」补两句：顺序即装载顺序；`official`／`tag` 的含义 | `docker/README.md:121,123` | ✅ | — | R5 IT-008 修过的「tag 条目是 detached HEAD」说法已在 |
| §4.2.1 | `frappe_china` 条目锁到 HEAD | `apps.json:46` | ✅ | ✅ | `4b21aae`，就是 HEAD（R5 IT-009 已修） |
| DEC-003、A4 | TS-002：`BUSINESS_APP_ORDER`／`TAIL_APPS` 常量 | `frappe_china/install.py:5-6` | ✅ | ✅ | 与 `apps.json` 的业务 app 段顺序一致（两处各写一份，见集成点） |
| 同上 | `target_app_order`：纯函数；frappe、erpnext 居首；业务 app 按常量序；未知 app 保持相对顺序；尾部 app；不增不减 | `install.py:112-121` | ✅ | ✅ | 与伪代码逐行一致 |
| 同上 | `reorder_installed_apps`：已是目标顺序则不写、不留 Version | `install.py:131-134` | ✅ | ✅ | 两站当前顺序就是目标顺序：测试站有 5 条、演示站有 1 条 `installed_apps` 的 Version，都是调序时写的 |
| 同上 | 经 `update_installed_apps_order` 写（框架校验增删、frappe 居首、写 Version、限 System Manager） | `install.py:126-136`；上游 `installed_applications.py:108-136` | ✅ | ✅ | `bench execute` 以 Administrator 连接，结束时自动 commit 并打印返回值（`commands/utils.py:315-322`） |
| A5／LG-010 | 同步 `site_config.json` 的 `installed_apps` 镜像 | `install.py:137-138` | ✅ | ✅ | 实测两站镜像与库一致，都是目标顺序 |
| HT-004 | 归位后清缓存 | `install.py:139` | ✅ | ⚠️ | 只清本进程与 Redis；开发模式下别的进程里的 `@site_cache` 钩子表要靠重启才失效（P1-05，方案已接受重启） |
| 同上 | 返回 `{changed, before, after}` | `install.py:134,140` | ✅ | ✅ | — |
| SL-001 ⑦ | 六个单测：常规七个、缺某业务 app、有未知 app、`frappe_debug` 在场、已是目标顺序、无 `frappe_china` | `tests/test_install.py:31-83` | ✅ | ✅ | 六类逐一对上 |
| TS-002 | 在当前站点上调两次 `reorder_installed_apps`，第二次 `changed` 为假 | `test_install.py:85-90` | ✅ | ⚠️ | 站点已是目标顺序时两次都走提前返回，`changed=True` 分支（写库、同步镜像、清缓存）从未被测到（P1-06） |
| §4.2.1 第 1 条，总纲 §六第 1 行 | TS-003-1：第 3 段解析多输出 `ref`（tag → branch → `version-16`）与 `official`；空字段写 `-` | `setup.sh:133-146` | ✅ | ✅ | — |
| 同上 | TS-003-2：预检用 `ls-remote --exit-code --heads --tags`，同时查 `refs/heads/` 与 `refs/tags/`；非零即报错退出；`get-app --branch "$ref"` | `setup.sh:165-172` | ✅ | ⚠️ | 宿主实测：`v3.14.2`／`main`／`version-16` 返回 rc=0，坏 tag 返回 rc=2。bench 把 `--branch` 拼成 `git clone --branch`（容器 `bench/app.py:189-194`）。**只在目录还不存在时才预检**，且「不存在」与「访问不了」报同一句话（P1-07） |
| 同上 | 原注释里「`--heads`」的说法改正；tag 条目的日志说「停在 tag $ref」 | `setup.sh:163-164,231-239` | ✅ | ✅ | R5 IT-008 已修。本地 insights 有 `refs/tags/v3.14.2`，`show-ref` 分支可达 |
| §4.2.1 第 4 条，DEC-001 | TS-003-3：`official=1` 的 app：`upstream` 设为官方 url、push 地址设 `DISABLED_use_origin_instead`、删 `origin` | `setup.sh:261-266` | ✅ | ✅ | 实测 crm／hrms／insights／raven 只有 `upstream`，push 地址为 `DISABLED_use_origin_instead` |
| 同上 | 其余 app 维持现逻辑；`apps/` 下未声明的目录只设 `core.fileMode false` | `setup.sh:267-291,301-310` | ✅ | ✅ | frappe／erpnext 为 origin=fork、upstream=官方只读；frappe_china 只有 origin。未声明目录那段是 R5 IT-007 补的 |
| §4.2.1 第 2 条 | TS-003-4：第 6 段按 `apps.json` 顺序 `install-app`（跳过 frappe）；未声明的打警告、不装 | `setup.sh:339-360` | ✅ | ❔ | 本机模拟了循环守卫与 awk 判别，行为正确。端到端未跑（SH-P1S5008） |
| §4.2.1 第 3 条 | TS-003-5：第 6.2 段：已装 `frappe_china` 就调归位并打出返回值；未装就打说明；段末提示重启 | `setup.sh:362-370` | ✅ | ❔ | 返回值由 `bench execute` 打印。演示站的调序 Version 时间 00:44:09 在 raven 装完（00:43:15）之后，与 6.2 段被执行一致，但这是旁证 |
| 方案 TS-003 末句 | 每处改动注明原因与需求编号 | `setup.sh:133-146,165,261,362` | ⚠️ | — | 只有 `:302`、`:353` 写了编号；解析、预检、official 分支、6.2 段都没写（并入 P1-08） |
| §4.2.1 第 5 条，总纲 §六第 2 行 | TS-004：按 `apps.json` 原顺序遍历；未克隆的原样保留并警告 | `lock-apps.sh:66-73` | ✅ | ✅ | 临时副本写入：与仓库内文件零 diff |
| 同上 | official 条目不读 remote，沿用 `e.url`；非 official 依次取 origin → upstream → 原值 | `lock-apps.sh:75-78` | ✅ | ✅ | — |
| 同上 | 有 tag 时保留 tag、不写 branch；HEAD 游离时沿用 branch 并警告 | `lock-apps.sh:81-89` | ✅ | ⚠️ | 保留 tag 时不核对 HEAD 是否还在该 tag 上（P1-02） |
| 同上 | 新 app 追加到末尾并警告 | `lock-apps.sh:92-98` | ✅ | ⚠️ | 实测删掉 raven 条目后再写，raven 被追加到末尾并警告，但不带 `official`；下次 `setup.sh` 第 4 段会把它当 fork 处理（P1-01） |
| 同上 | `--show` 多显示 tag／branch 与 official | `lock-apps.sh:19-44` | ✅ | ⚠️ | ref 列显示的是 `apps.json` 里记的值，不是仓库现状（P1-02） |
| DEC-005、§4.2.2 映射表 | TS-005-1：`expense_claim_type` 五条映射；`_comment` 补「待领域专家确认」 | `company_defaults.json:2,28-34` | ✅ | ✅ | 两站的行都指向 `is_group=0` 的对应科目号。`:34` 两个键挤在一行（P1-08） |
| §4.2.2 | TS-005-2：`set_cn_expense_claim_accounts` 在站点无该 DocType 时返回 `[]` | `accounting/hr.py:31-32` | ✅ | ✅ | `test_hr.py:9-14` 断言只查了一次 `exists` |
| 同上 | 只配缺的，已有行不覆盖 | `hr.py:44-51` | ✅ | ✅ | R6 DEC-028 把遍历对象改成站上全部类型、未映射的落兜底科目，「只配缺的」仍成立。R6 DEC-027 的 `repoint` 会改挂指向**无号**科目的行，是 R6 有意收窄的，不算被破坏 |
| 同上 | 映射里有、站上没有的类型告警跳过 | `hr.py:36-41` | ✅ | ✅ | — |
| 同上 | 科目号查不到时先收齐、一次报错，不写空值 | `hr.py:53-59` | ✅ | ✅ | `test_expense_claim.py:90-105` 断言零行 |
| 同上 | `backfill_cn_expense_claim_accounts`：全部中式公司，筛法与 `check_all_cn_companies` 相同 | `hr.py:72-79` | ✅ | ⚠️ | 筛法照方案字面写成 `chart_of_accounts == CN_CHART_NAME`。R6 起「中式公司」还包括复制建账的公司（`is_cn_company`），回填会漏掉它们（P1-04） |
| §4.2.2 入口 1 要求 | 不 import `hrms`；`required_apps` 不含 `hrms` | `hr.py:1-11`；`hooks.py:11` | ✅ | ✅ | grep 全 app 无 `import hrms`／`from hrms` |
| §4.2.2 入口 1 | TS-005-3：`build_cn_company` 末尾、`setup_cn_taxes` 之后调预配 | `accounting/company.py:132-133` | ✅ | ✅ | 测试站 `_FCT CRM 验证` 有 5 行、科目 266、无 `Expense Claims`。HT-003：`ignore_chart_of_accounts` 在 `before_insert` 置真、`finally` 里复位（`company.py:70,101-102`），HRMS 的两个钩子（`hrms/overrides/company.py:101,120`）在入口处检查它 |
| §4.2.2 入口 2 | TS-005-4：`hooks.after_app_install` 指向 `install.after_app_install`，只对 `hrms` 回填 | `hooks.py:104`；`install.py:149-157` | ✅ | ✅ | **原问题已消失**：演示站 HDTH 的 5 行建于 00:41:38，在 HR 模块（00:41:10）之后、Insights（00:42:24）之前，即装 HRMS 时由钩子写入；科目 266，无 `Expense Claims`／`费用报销记录`。HT-002 的次序（`installer.py:360-364`）成立 |
| TS-005-5 | `test_expense_claim.py`：HRMS 不在时 `skipTest`；①～⑦ | `tests/test_expense_claim.py:37-130` | ✅ | ✅ | 七例逐条对上。⑥ patch `exists`；⑤ patch `_account_name`；⑦ 显式设 `lang`。R5 IT-006 补的；R8 做过变异测试 |
| SL-002 ⑧ | `test_scaffold.py`：`required_apps == ["erpnext"]`；模块顶层不 import hrms | `tests/test_scaffold.py:35-53` | ✅ | ✅ | 只扫 `tree.body` 的顶层语句，与要求的「顶层」一致 |
| TS-005 验证方式 | 「依赖可选 app 只在 DocType 存在时生效、顶层不 import」写进约定 | `docs/开发守则.md:83-85` | ✅ | — | 已从回执进了常驻文件 |
| §4.2.1 末段 | 锁定后在被锁 commit 上重读 HRMS 的跳过条件 | `hrms@6f5ac249 overrides/company.py:119-135` | ✅ | — | 本片重读：「已有 `Expense Claim Account` 即 continue」与入口处的 `ignore_chart_of_accounts` 门控都在 |
| SL-001 ②③⑤、AC-008 | 端到端重建、坏 tag 用临时 `apps.json` 实测 | — | ❔ | — | 已登记延迟 SH-P1S5008，描述与实情一致（预检命令本片在宿主重测通过） |

## 业务规则合规核

| 规则条款 | 是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 执行《小企业会计准则》，映射目标只取该科目表的明细科目（需求 §4.10） | 涉及 | 合规（未经专家确认） | 五个映射科目号与兜底 `5602250` 在两站都指向 `is_group=0` 的明细科目；演示站与测试站中式公司科目数都是 266，无多余的 `Expense Claims` 科目 |
| 报销类型 → 科目映射五行（`Calls→5602090` 等） | 涉及 | **草案·待领域专家确认** | AI 按费用性质推定（需求 §4.2.2、LG-011）；它是配置，不是不变量，不进 `业务规则.md`。JSON `_comment` 与 frappe_china `README.md` 已标「待确认」 |
| BR-002 报表构成、BR-006 资产负债平衡 | 不涉及 | — | 本片不改报表 |
| BR-003／BR-007 税率与价税分离 | 不涉及 | — | `tests/utils.py` 的 `_use_cn_rounding` 引用了 BR-007，但那是 R5 IT-027 的测试前置，不属本片 |
| BR-004／BR-005 增值税结转与附加税 | 不涉及 | — | — |
| 本片是否新增或变更领域不变量 | 否 | — | 归位、版本锁定都是工程约定，不进业务规则 |

## 集成点登记（交接摘要）

**本片暴露的接口**：
- `frappe_china.install.reorder_installed_apps() -> {"changed": bool, "before": list, "after": list}`。消费方：`setup.sh:365`、`开发守则.md:79`、Part2 TS-008 反证（片 2）、SB IT-005。
- `frappe_china.install.target_app_order(list) -> list`（纯函数）。
- `frappe_china.install.after_app_install(app_name)`，经 `hooks.py:104` 注册；只对 `"hrms"` 调 `backfill_cn_expense_claim_accounts()`。
- `frappe_china.accounting.hr.set_cn_expense_claim_accounts(company) -> list[str]`。片内的调用方是 `company.build_cn_company`；R6 起 `company.validate`（`company.py:76-79`）也调它（归片 5）。
- `frappe_china.accounting.hr.backfill_cn_expense_claim_accounts() -> dict[str, list[str]]`。

**本片依赖的接口**：
- 框架：`update_installed_apps_order`（`only_for System Manager`、强制 frappe 居首）、`frappe.installer.update_site_config`、`bench execute`（自动 commit）、`installer.install_app` 的次序（HRMS `after_install` → 各 app 的 `after_app_install`）。
- HRMS `set_expense_claim_type_accounts` 的跳过条件（已有行即 continue）与 `ignore_chart_of_accounts` 门控。
- 片内对 `company.py` 的依赖：`_load_defaults`、`_account_name`、`_throw_missing_accounts`（签名未改）。

**跨片共享状态**：
- **`installed_apps` 顺序**：两站的库与 `site_config.json` 镜像都是 `["frappe","erpnext","crm","hrms","insights","raven","frappe_china"]`。片 2 的 `check_app_order` 以此为判据；片 4 的重建演练以它为目标。
- **业务 app 顺序写在两处**：`apps.json` 的条目顺序与 `install.py:5` 的 `BUSINESS_APP_ORDER`，当前一致。加 app 时两处要一起改，没有任何检查保证它们一致。
- **`apps.json` 字段**：`url`、`branch`|`tag`（二选一，tag 优先）、`commit`、`app_name`、`official`。消费方：`setup.sh` 第 3／4／6 段、`lock-apps.sh`。`configure_apps.py` 是否读它本片未查（请片 3 补）。
- **`company_defaults.json` 键**：`expense_claim_type`（本片）、`expense_claim_type_fallback`（R6，片 5）。两者都由 `hr.expense_claim_account_number` 读。
- **「中式公司」的两种判法**：`backfill_cn_expense_claim_accounts` 与 `selfcheck.check_all_cn_companies` 按 `chart_of_accounts == CN_CHART_NAME` 筛；R6 的 `company.is_cn_company` 会沿 `existing_company` 链判。复制建账的公司 `chart_of_accounts` 为空（ERPNext `company.py:535-537`），所以前者看不到它们（P1-04）。**请收口时与片 2（自检、`check_app_order.company_checks_ok`）、片 5（R6）比对。**
- **测试站残留**：`test.localhost` 上有中式公司 `_FCT CRM 验证`（报销行建于 2026-10-05 19:21），SL-003 ⑥ 要求测试站上不留 `_FCT` 公司。是否属片 3 有意保留的 CRM 集成公司，交片 2／3 确认。
- **调序痕迹**：测试站有 5 条 `tabVersion(DefaultValue/installed_apps)`（10-05、10-06），演示站 1 条（10-07 00:44:09）。
- **事件**：本片不发出也不消费任何实时事件。

## 自证复核

| 被审产物声称 | 实际复核 | 一致否 |
|---|---|---|
| D 回执：TS-001 七条按方案顺序、四个 official、Insights 用 tag | 读文件，宿主 `ls-remote` 核 commit | 一致 |
| D 回执：TS-002「11 个安装测试通过」 | 未跑测试。用例数：S4 时 4 例，加 Part1 的 7 例正好 11；`1193f94` 里有 14 例，多出的 3 例是 Part2 的 `check_app_order` 用例 | 用例数对得上；通过与否无法复核 |
| D 回执：TS-004「`--show` 保留 7 条顺序」 | 本片重跑 `--show`，顺序与 tag／official 标记都对；写入模式在临时副本上零 diff | 一致 |
| D 回执：「方案未偏离」「当前没有方案外代码偏离」 | 当时缺 `test_expense_claim.py` 与 ⑧ 静态检查，第 4 段漏掉未声明目录，tag 日志与 README 说法不对 | **不一致**。R5 E 已立为 IT-006／007／008 并修复，本片复核修复都在（见逐项表），不重复立项 |
| D 回执：TS-005「3 个定向测试通过」 | `test_hr.py` 有 3 例 | 用例数一致；通过与否无法复核 |
| R5 E：TS-002 两站镜像与库一致（A5） | 本片重查两站都一致 | 一致 |
| R5 E：「SL-001 ② 预检只在目录不存在时走，按宽读算通过」 | 读码确认（`setup.sh:156-170`） | 一致；本片另列为观察项 P1-07，供用户改判 |
| R8 E：IT-006 测试已补，变异后 ①③ 失败 | 七例在、内容逐条对上；变异未重做 | 内容一致；变异未复核 |
| 登记册 SH-P1S5008：「SL-010 ② 预检已在 R5 补测通过」 | 本片在宿主重测：有效 ref 返回 rc=0，坏 tag 返回 rc=2 | 一致 |
| 开发守则：「装完任何新 app 后……以 `check_app_order` 验，`ok` 为真才算完」 | 第五个 app（不在 `BUSINESS_APP_ORDER` 里）排在 `frappe_china` 之后时，`order_ok` 仍为真 | **不一致**（P1-03） |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P1-01 | 低 | `docker/lock-apps.sh:92-98`；后果在 `setup.sh:267-284` | 追加新 app 时只写 `url/branch/commit/app_name`，不带 `official`。用 `bench get-app` 取来的官方 App（只有 `upstream`）被追加后，下次 `setup.sh` 第 4 段把它当作自有 fork：`fork=upstream 的 url` → 建一个指向**官方仓库、可推送**的 `origin`，`upstream` 的 push 地址也不禁用。游离 HEAD（tag 检出）的新 app 会写成 `"branch": ""`，`setup.sh:136` 随之退到 `version-16`。复现：在临时副本里删掉 raven 条目后跑写入，得到 `('raven','main',None,None)`，无 `official` | 开发守则「官方业务 App 只配只读 `upstream`、不设 `origin`」；需求 §4.2.1 第 4 条 | 追加时按「无 `origin`、只有 `upstream`」推断并写 `official: true`，或至少在警告里写明「须手工确认 official／tag」；HEAD 游离时不写空 `branch`，改为警告 | 本Session修 | 自动推断 `official`，还是只警告、由人补字段 | 待裁决 |
| P1-02 | 低 | `lock-apps.sh:81-82`、`:35-37` | 判据区分不了两种情形：① tag 条目原样保留 tag，不核 HEAD 是否仍等于该 tag 指向的 commit。仓库挪到别的 commit 后再锁，会写出「`tag: v3.14.2` + 新 commit」这样自相矛盾的条目，重建时先按旧 tag 克隆、再按 SHA 拉新 commit。② `--show` 标着「各 app 当前版本」，ref 列却显示 `apps.json` 里的记录值；仓库已切到别的分支时照样显示 `branch=main` | 开发守则「判据必须能区分它要区分的两种情形」；需求 §4.2.1 第 5 条（不把 tag 写坏） | 保留 tag 前用 `git rev-parse "refs/tags/<tag>^{commit}"` 比对 HEAD，不等就警告；`--show` 同时显示仓库实际的 `symbolic-ref`／`describe --exact-match` 与记录值 | 本Session修 | — | 待裁决 |
| P1-03 | 低（中／低边界） | `frappe_china/install.py:46-49`；`docs/开发守则.md:81` | `order_ok` 只要求 `frappe_china` 排在 `BUSINESS_APP_ORDER` 四个之后。不在常量里的第五个 app 装上后追加在末尾、排在 `frappe_china` 之后，会占走 `[-1]` 位，但 `order_ok` 仍为真；译名比对的 `competitors` 也只取那四个 app，所以 `ok` 可以为真。开发守则写的是「装完**任何**新 app 后」以它验 | 开发守则「判据必须能区分」；ADR-0003（`frappe_china` 在全部业务 app 之后） | `order_ok` 改判「`frappe_china` 之后只有 `TAIL_APPS`」，与 `target_app_order` 的目标一致，并补一个带未知 app 的单测；或者把开发守则的措辞收窄为「四个业务 app」 | 本Session修 | 改判据，还是改开发守则措辞（后者须先载入常驻文件契约） | 待裁决 |
| P1-04 | 低 | `accounting/hr.py:72-79`（同一筛法另见 `selfcheck.check_all_cn_companies`） | 回填按 `chart_of_accounts == CN_CHART_NAME` 筛公司。R6 起「中式公司」还包括复制建账的公司（`is_cn_company` 沿 `existing_company` 链判），而复制建账的公司 `chart_of_accounts` 被 ERPNext 的 `validate_coa_input` 置空（`erpnext/setup/doctype/company/company.py:535-537`），所以装 HRMS 时回填漏掉它们。下一次保存时 R6 的 `validate` 会补上，漏的只是「装完到第一次保存之间」这一段。属拼装不上：Part1 契约的筛法与 R6 的定义不一致 | 需求 §4.2.2 入口 2「装完 HRMS 后对**全部**中式公司补配」 | 回填改为遍历公司、以 `is_cn_company` 判；补一个「复制建账公司 + `after_app_install("hrms")`」用例 | 新Session修 | 自检 `check_all_cn_companies` 是否同口径一并改（牵动片 2／片 5） | 待裁决 |
| P1-05 | 观察 | `install.py:139` | 归位后只调 `frappe.clear_cache()`：它清本进程的 `_SITE_CACHE` 和 Redis 键，但不调 `frappe.client_cache.erase_persistent_caches()`（`install_app` 在 `installer.py:375` 会调）。两站都开着 `developer_mode=1`，钩子表走 `@site_cache`（`__init__.py:1003-1004`），正在跑的 web／worker 进程要重启才会按新顺序取钩子。方案 HT-004 已接受重启，`setup.sh:370` 也打了提示 | — （方案已接受） | 可加一行 `erase_persistent_caches()`，减少对重启的依赖；或者不修 | 延迟或不修 | — | 待裁决 |
| P1-06 | 低 | `tests/test_install.py:85-90` | 判别力不足：在已是目标顺序的站上，两次调用都走 `install.py:133-134` 的提前返回，`changed=True` 分支（`update_installed_apps_order`、A5 的镜像同步、`clear_cache`）没有任何单测；把 `:136-139` 全删掉，此用例照样通过。另外，若在非目标顺序的站上跑，`update_site_config` 写文件不随测试事务回滚，会留下镜像与库不一致 | 方案 TS-002（幂等）、总纲 A5；开发守则「判据必须能区分」 | 加一例：patch `frappe.get_installed_apps` 返回乱序、patch 掉 `update_installed_apps_order`／`update_site_config`，断言它们以目标顺序被调用、`changed` 为真；原用例保留作冒烟 | 本Session修 | — | 待裁决 |
| P1-07 | 观察 | `setup.sh:156-170` | 预检只在 `apps/<name>` 还不存在时跑。目录已在时改了 `apps.json` 的 tag／branch，既不预检也不切 ref，只按 commit 对齐。SL-001 ② 的字面要求只在首次克隆时成立（R5 E 按宽读判了通过）。另外预检把 rc=2（ref 不存在）与 rc=128（访问不了）合成一句报错，看不出是哪一种 | 方案 SL-001 ② 字面；开发守则「判据必须能区分」（较弱） | 接受宽读、不修；或在报错里打出 rc 以区分两种原因 | 延迟或不修 | 是否接受「已克隆的条目不预检」的宽读 | 待裁决 |
| P1-08 | 观察 | `cn_tax/data/company_defaults.json:34`；`setup.sh:133-146,165,261,362` | 文档性小偏差：JSON 的 `},  "item_group_expense": {` 把两个键挤在一行（S5 改动带进来的，JSON 仍合法）；`setup.sh` 的解析、预检、official 分支、6.2 段注释没写需求编号，方案 TS-003 要求「每处改动注明原因与需求编号」 | 方案 TS-003 末句 | 下次改到这两处时顺手修 | 延迟或不修 | — | 待裁决 |

## 本片盲区自述

- **没跑任何测试**（受任务约束）。「测试会过」全凭读码，用例数是数出来的。Spec 要求的验证门实测值本片给不出，须由收口或主会话的全量回归补上。
- **没往这些方向找**：`setup.sh` 第 0～2、5、7～9 段 S5 前就有的行为（如 `GIT_PROXY` 为空时容器内 git 仍继承主仓库 `.git/config` 的宿主代理，本片实测到这一现象，但不属 S5 改动，未立项）；`bench update`／`bench get-app` 与「官方 App 只有 `upstream`」的长期交互（只读了 `get_remote` 优先取 `upstream`，看着无害）；`frappe` 条目在 `apps.json` 里的 branch 不被 `bench init` 使用（用的是 `FRAPPE_BRANCH` 环境变量，S5 前就这样）。
- **把握最低的一处**：P1-04 的后果只是读码推断。站上现在没有复制建账的中式公司，没能在实物上看到漏配；R6 的 `validate` 能兜住，这一点也是读码判断（`test_company_hr_lifecycle.py` 是片 5 的范围，未细读）。
- **拿不准处**：P1-03 判「低」还是「中」——在 S8G 之前没有第五个 app 要装，所以定低；若用户把开发守则那条看作对外承诺，应升为中。P1-01 是否算「方案外缺口」——方案伪代码本身就写了不带 `official` 地追加，所以这是标准没写到的缺口，不是落地偏差。
- 测试站残留的 `_FCT CRM 验证` 公司不属本片要求，只登记在集成点，没有立项。
