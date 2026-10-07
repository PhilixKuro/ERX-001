# F 复核分片报告 · 片 1（对象：R9 已修项 FD-005／006／007①／008／010／011／012 与本片延迟项 / 审核标准：R3 开发方案 Part1（SL-001～002、TS-001～005）＋ Part2（SL-003～004、TS-006～008）；R9 F 审核报告与 SB 回执）

**轮次**：P1-S5-R10｜**步骤**：F 复核分片 1｜**日期**：2026-10-07｜**执行者**：Claude 子 Agent（只读）
**依据**：[R3 开发方案 Part1](../R03-开发方案/P1-S5-R3-C开发方案-Part1.md)、[Part2](../R03-开发方案/P1-S5-R3-C开发方案-Part2.md)（TS-002、TS-004、TS-005、接口契约 `check_app_order`）；[R9 F 审核报告](../R09-F审核/P1-S5-R9-F审核报告.md)（FD-005～012、FD-021、023～027、035 行与当场修清单）、[R9 Part1](../R09-F审核/P1-S5-R9-F审核报告-Part1.md)、[SB 回执](../R09-F审核/P1-S5-R9-SB修复回执.md)；`docs/开发守则.md`「装完任何新 app 后」节；Stage 概况登记册与长效信息；`docs/01-需求摸底/P1-概况.md` PH-P1016 行
**被审范围**：`frappe_china` `4b21aae..9d53d39` 中 `install.py`、`accounting/hr.py`（回填部分）、`tests/test_install.py`、`tests/test_hr.py`、`tests/test_expense_claim.py`（`test_2b`）；主仓库 `2fb2641..d7b89d6` 中 `docker/lock-apps.sh`、`docs/开发守则.md`、Stage 概况、P1 概况

## 覆盖自证

**读了的依据**：本片共用说明；R9 收口报告全文；R9 Part1 全文；SB 回执全文；R3 Part1 TS-002／TS-004 伪代码段；Part2 接口契约与 TS-008 段（按关键词读）；开发守则第 76～85 行；Stage 概况本轮 diff（长效信息 #3／#4、SH-P1S5005～010）；P1 概况 PH-P1016 行。B 需求文档只按 AC-006 关键词查了一处，没有重读全文（本轮改动不改意图层）。

**逐行读的代码**：两仓本轮完整 diff（本片相关文件）；`install.py` 全文（工作区与 `HEAD` 一致后读；主会话变异期间改用 `git show HEAD:`）；`hr.py` 第 1～80 行（`HEAD`）；`company.py` 第 1～80 行与 `_throw_missing_accounts`；`selfcheck.check_all_cn_companies`；`lock-apps.sh` 全文；`setup.sh` 第 101～180、254～300、342～375 行；`test_install.py` 中新旧两例与 `check_app_order` 系列用例。

**对照的上游**（只读）：frappe `installer.py:330-392`（`install_app` 末尾 `clear_cache` → `erase_persistent_caches`；`add_to_installed_apps` 先 `commit` 再 `update_versions`）；`redis_wrapper.py:478-516、601-640`（`ClientCache` 订阅 `clear_persistent_cache`，处理函数清 controller 缓存，`doctype` 为空时清 `_SITE_CACHE`）；`__init__.py:923-1012`（`get_installed_apps` 的 `request_cache`、`get_hooks` 开发模式走 `site_cache`）；`cache_manager.py:281-320`；`defaults.py:149-191、235-273`（`set_global` → `_clear_cache` → `frappe.clear_cache`）；`installed_applications.py` 全文（`update_versions`、`update_installed_apps_order` 不 commit）；`change_log.get_versions`、`utils.get_installed_apps_info`；`commands/utils.py:263-322`（`bench execute` 函数返回后才 `commit`）；`commands/site.py:543-573`（`list-apps` 读 `Installed Applications` 子表）；`migrate.py:198`；`utils/boilerplate.py:204-210`（`bench new-app` 建 git 仓库、不加 remote）；ERPNext `company.py:535-545、597-601`；HRMS `overrides/company.py:101-126`；四个官方 app 的 `hooks.py`（覆盖键 grep）。

**只读查询**（两站，SELECT／读文件）：全局 `installed_apps`；`site_config.json` 的 `installed_apps`、`developer_mode`；`tabInstalled Application`（idx、app_name、modified、`is_setup_complete`、`git_branch`）；`System Settings.setup_complete`；`tabCompany`（name、chart_of_accounts、existing_company、parent_company、`default_expense_claim_payable_account`）；`tabVersion`（DefaultValue/installed_apps 计数）；演示站 `tabDeleted Document`（10-06 起按类型计数）；`bench --site erx.localhost list-apps`；主 bench `lock-apps.sh --show`（只显示，不写）。

**实验**：在仓库外 `mktemp -d` 临时目录复制 `lock-apps.sh`，造一份 `apps.json` 与 9 个假 app 仓库（声明的 5 个：在分支上、在 tag 上、tag 条目但 HEAD 在分支上、游离、tag 不存在；未声明的 4 个：有 origin 在分支上、只有 upstream 停在轻量 tag、无任何 remote 游离、只有 upstream 停在附注 tag），另 1 条未克隆；先跑 `--show`，再跑写入，看输出与写出的 `apps.json`。做完已 `rm -rf`，确认目录不存在。另在临时目录验证 `git remote add upstream ""` 返回 0。

**跳过的及原因**：没跑测试、没做变异（硬约束；变异由主会话做）；没写任何站点；没开 `bench start` 验广播生效（R9 已试过、探针不可信，本片不重复）；`setup.sh` 端到端未跑（SH-P1S5008）。

## R9 已修项复核

| R9 项 | 修于（当场／SB） | 定位（文件:行） | 落地 | 生效 | 原问题消失 | 说明 |
|---|---|---|---|---|---|---|
| FD-005 (a) | 当场 | `docs/开发守则.md:81,83` | ✅ | ✅ | ✅ | 补段的三点与代码、上游一致：① 检查在新进程里跑，证明不了重启；② 归位函数广播 `erase_persistent_caches`（`install.py:149`），按读码会清各进程 `_SITE_CACHE`（`redis_wrapper.py:631-640`），开发模式钩子表正存在那里（`__init__.py:1003-1004`），实测未确认，所以「重启不可省」；③ 四个官方 app 的 `hooks.py` 都没有注册那三个覆盖键（crm／hrms 的 `override_whitelisted_methods` 是注释，insights／raven grep 无命中），`overrides_ok` 无竞争者时恒真。说法与代码对得上 |
| FD-005 (b) | 当场 | `install.py:146-149` | ✅ | ✅（读码） | ⚠️ 部分 | 调用本身对：与 `installer.py:374-375` 同序（先 `clear_cache` 再广播），订阅方是每个进程 `ClientCache` 的后台线程，`doctype=None` 时清整个 `_SITE_CACHE`。**但广播发在提交之前**：`update_installed_apps_order` 不 commit，`bench execute` 在函数返回后才 commit（`commands/utils.py:315-316`）；上游 `add_to_installed_apps` 是先 commit 再广播。窗口内别的进程重读会把旧顺序重新缓存（见 P1-03）。R9 已注明生效未能实测 |
| FD-006 | 当场 | `install.py:47-50,77-81`；`test_install.py:224-238`；`开发守则.md:81` | ✅ | ✅ | ✅ | 判据改为「`frappe_china` 之后只许 `TAIL_APPS`」，与 `target_app_order` 的目标（`other` 排在 `tail` 前）一致。`TAIL_APPS = ("frappe_china", "frappe_debug")`（`install.py:6`），首项是 `frappe_china`，`TAIL_APPS[1:]` 得 `('frappe_debug',)`，文案正确（耦合见 P1-04）。`frappe_china` 不在列表时 `after_china=[]`、`order_ok=False`，判定对，文案不点明「未装」（P1-04）。新测试 patch `frappe.get_installed_apps`，`check_app_order` 在调用时按模块属性取它，patch 生效；带 `print_designer` 判假、带 `frappe_debug` 判真，两向都测了。R9 修后 M3 变异已证有判别力 |
| FD-007① | 当场 | `test_install.py:85-111` | ✅ | ✅ | ✅ | patch 位置与 `install.py` 的引入方式匹配：`reorder_installed_apps` 在函数体内 `from frappe.core.doctype.installed_applications.installed_applications import update_installed_apps_order`、`from frappe.installer import update_site_config`，每次调用才去源模块取名，patch 源模块属性能截住；`frappe.get_installed_apps`／`get_single`／`clear_cache` 都经 `frappe.` 取；`frappe.client_cache` 是同一个实例，`patch.object` 截得住。断言调序、镜像以目标顺序各调一次，子表、清缓存、广播各一次，能区分「调序做了」与「没做」（R9 M1 复测已失败）。全部写操作都被 mock，不改测试站 |
| FD-008 | SB | `hr.py:72-80`；`test_expense_claim.py:72-93`；`test_hr.py:40-56`；`P1-概况.md:150` | ✅ | ✅ | ✅ | `is_cn_company`（`company.py:33-50`）对非 str 入参直接用 `.get("chart_of_accounts")`／`.get("existing_company")`，`frappe._dict` 支持；沿链时每级 `get_value(..., as_dict=True)` 取同样三列，最多 10 级、带防环。`get_all` 取的三列够用：设上级公司的子公司在 ERPNext 里也被写成 `existing_company`（`company.py:597-601`），不需要 `parent_company`。`get_all` 缺省 `limit_page_length=0`，不截断。性能：本表公司零次额外查询，复制公司每级一次，演示规模可忽略。`test_hr` 对 `hr.is_cn_company` 的 patch 打在 `hr` 模块名字空间，`backfill` 按全局名取，生效。用户改判「自检不改、并入 PH-P1016」已写进 PH-P1016 行，描述与 `selfcheck.py:132-143` 一致 |
| FD-010 | 当场 | `lock-apps.sh:103-123` | ✅ | ✅ | ⚠️ 部分 | 临时目录实测：有 origin 的新 app 写 `branch`、不标 official；只有 upstream 的标 `official: true` 并警告；停在 tag 上写 `tag`（轻量、附注都认）；游离且无 tag 不写 branch／tag 并警告。**但判据是「没有 origin」，不是 R9 建议的「无 origin、只有 upstream」**：一个 remote 都没有的仓库也被标 `official: true`、`url: ""`。`bench new-app` 建的仓库正是这样（S7 要建 `frappe_debug`），见 P1-01 |
| FD-011 | 当场 | `lock-apps.sh:36-43,88-93` | ✅ | ✅ | ✅ | 实测 `--show`：在分支上显示 `branch=main（实际 main）`；tag 条目而 HEAD 在分支上显示 `tag=v1（实际 main）`；游离显示「实际 游离」。`describe --tags --exact-match` 不在 tag 上时非零退出，但 `--show` 段用的是 `subprocess.run(capture_output=True)` 且不带 `check`，不抛异常，stderr 被吞掉、不出噪音，回落到「游离」；写入段的 `git()` 帮助函数 `check=False`，同样不中止。保留 tag 时核 `refs/tags/<tag>^{commit}`：tag 不在 HEAD 上打警告并给出 tag 指向，tag 不存在打「不存在」。主 bench `--show` 七条记录值与实际一致 |
| FD-012 | 当场 | `install.py:143-145` | ✅ | ✅（测试站） | ⚠️ 部分 | `update_versions` 按 `get_installed_apps_info()` → `get_versions()` → `get_installed_apps(_ensure_on_bench=True)` 的顺序 `delete_key` 后重新 append、`save()`；`set_global` 已清掉 `request_cache`，读到的是新顺序。它会 save（单表 DocType，无 `track_changes`，不写 Version），并 `set_single_value("System Settings", "setup_complete", is_setup_complete())`；`frappe`／`erpnext` 两行的 `is_setup_complete` 从现表保留，所以不改配置完成标记（两站现为 1／1，`setup_complete=1`）。自身不 commit，由 `bench execute` 统一提交。在 `setup.sh` 6.2 段调用时，每次 `install-app` 已各调过一次 `update_versions`，再调一次结果相同，无额外副作用。测试站子表已是目标顺序（16:09:03 重写）。**演示站没变**：它早已是目标顺序，归位走提前返回，`list-apps` 仍把 `frappe_china` 列在第 3 位（见 P1-02） |

## 延迟／不做项登记核对

| R9 项 | 裁决去向 | 登记位置 | 描述与实情一致否 | 说明 |
|---|---|---|---|---|
| FD-021 | 延迟 → SH-P1S5009 | Stage 概况登记册 SH-P1S5009 行 | 一致 | ① `fixtures/cash_flow_code.json` 代码 4「支付的职工薪酬」`party_type=Employee`；② `closing.py:21-30` `DRAFT_CHECK_DOCTYPES` 不含 HRMS 单据；③ HDTH `default_expense_claim_payable_account` 为 NULL（演示站查询）。三条都对 |
| FD-035 | 延迟 → SH-P1S5010 | Stage 概况登记册 SH-P1S5010 行 | 一致 | `apps.json` 业务段 crm、hrms、insights、raven 与 `BUSINESS_APP_ORDER`（`install.py:5`）现仍一致，仍无比对 |
| FD-023 | 不做（接受宽读） | R9 报告留档 | 一致 | `setup.sh:165-172` 预检仍只在目录不存在时跑，报错仍不分 rc。本轮 `setup.sh` 只改了第 2 段 |
| FD-024 | 不做（下次改到时顺手修） | R9 报告留档 | 一致 | `company_defaults.json:34` 仍是 `},  "item_group_expense": {`；本轮没改这个文件，`setup.sh` 改的第 2 段不涉及那几处注释 |
| FD-025 | 不做（留档） | R9 报告留档 | 一致 | 演示站 10-07 的 `Deleted Document`：Property Setter 4、Insights Query v3 2、Insights Workbook 2，共 8 条，与 R9 复核值一致 |
| FD-026 | 不做（接受单测代替） | R9 报告留档 | 一致 | `test_expense_claim.py:145-147` 在 `zh`、`en` 两种语言下各跑一遍 |
| FD-027 | 不做／长效信息 #3 | Stage 概况长效信息 #3 | 一致 | `crm/hooks.py:228-231` 确实整类覆盖 `Contact`、`Email Template`；#3 写了「走 `doc_events`」 |

## 业务规则合规核

| 规则条款 | 本轮改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 执行《小企业会计准则》 | 涉及：FD-008 让复制建账的公司也在装 HRMS 时拿到报销科目映射 | 合规（映射本身是草案·待领域专家确认） | 映射与兜底科目号未改；复制公司的科目由源公司复制，科目号相同 |
| BR-002 三张报表 | 不涉及 | 合规 | 员工付款现金流量项目的疑点已登记 SH-P1S5009，本轮未改 |
| BR-003 增值税税率 | 不涉及 | 合规 | — |
| BR-004 增值税月末转出 | 不涉及 | 合规 | — |
| BR-005 附加税 | 不涉及 | 合规 | — |
| BR-006 资产负债表平衡 | 不涉及 | 合规 | — |
| BR-007 价税分离 | 不涉及 | 合规 | — |

## 集成点登记（交接摘要）

- **本片依赖**：
  - 片 5：FD-036 把 `is_cn_company` 的循环变量改名为 `_attempt`。本片在 FD-008 里用到它，读码确认行为未变（`company.py:40`）。`is_cn_company` 本身的其余正确性归片 5。
  - 主会话：FD-005 (b)、FD-012 的变异（见「需主会话补跑」）。
- **本片暴露**：
  - `check_app_order()` 的 `order_ok` 新判据与问题文案「frappe_china 之后只能是 ['frappe_debug']，实际 …（排在它后面的：…）」。`setup.sh` 6.2 段只调 `reorder_installed_apps`、不调 `check_app_order`，不受文案变化影响。
  - `reorder_installed_apps()` 返回值形态不变（`{changed, before, after}`），`setup.sh:369` 由 `bench execute` 原样打印，对得上。`setup.sh` 6.2 段用 `list-apps` 第一列判 `frappe_china` 装没装，`list-apps` 读的正是 FD-012 重写的子表，只是顺序会变，判定不受影响。
  - `backfill_cn_expense_claim_accounts` 现在也回填复制建账的公司；`check_all_cn_companies` 仍按 `chart_of_accounts` 筛（PH-P1016 已登记两种判法的不一致）。
  - `lock-apps.sh` 追加新 app 时会自动标 `official`（P1-01 指出的误判对片 4／S7 建 `frappe_debug` 有影响）。

## 自证复核

| 被审产物声称（R9 报告／SB 回执／文档） | 实际复核 | 一致否 |
|---|---|---|
| R9 当场修 #7：归位末尾补 `erase_persistent_caches()` | `install.py:149` 在；与 `installer.py:375` 同序；但上游在广播前已 commit，这里没有 | ⚠️ 落地一致，时机有差（P1-03） |
| R9 当场修 #8：`order_ok` 改判、新增测试、开发守则同步一句 | 三处都在，`开发守则.md:81` 加了「`frappe_china` 之后只许有 `frappe_debug` 这类尾部 app」 | ✅ |
| R9 当场修 #9①：新测试断言调序、镜像、子表、清缓存、广播各一次 | 断言逐条在；patch 位置正确 | ✅ |
| R9 当场修 #10：「无 `origin` 即标 `official: true`」 | 照字面实现；与 R9 问题表 FD-010 建议「无 origin、只有 upstream」不同，无 remote 的仓库也被标 official | ⚠️（P1-01） |
| R9 当场修 #11：`--show` 显示实际 ref、保留 tag 前核 HEAD | 临时目录实测五种状态都对 | ✅ |
| R9 当场修 #12、修后验证：「归位后 `tabInstalled Application` 子表是目标顺序」 | 测试站是；演示站仍是安装先后顺序（`frappe_china` 第 3），`list-apps` 同样 | ⚠️ 只在测试站成立（P1-02） |
| R9 修后验证：`lock-apps.sh` 追加出的条目带 `official: true`，insights 带 tag | 实测相同；另测出无 remote 情形 | ✅（覆盖面窄） |
| SB 回执：`CN_CHART_NAME` 不再从 `hr` 导出，只有 `test_hr` 用到 | grep：`hr.py` 已不引入；其余模块都从 `chart` 直接引入 | ✅ |
| SB 回执：PH-P1016 行已补口径不一致 | `P1-概况.md:150` 已补，内容与 `selfcheck.py:132-143`、`hr.py:72-80` 一致 | ✅ |
| 开发守则：「四个官方 app 都不注册那三个覆盖键」 | 四个 `hooks.py` grep 无注册 | ✅ |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准／意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P1-01 | 低 | `docker/lock-apps.sh:107-113`；后果在 `setup.sh:261-266` | 追加新 app 时只看「没有 origin」就标 `official: true`，一个 remote 都没有的仓库也会被标上，`url` 写成 `""`。临时目录复现：无 remote、游离的假 app 写出 `{"url": "", "official": true, "commit": …, "app_name": …}`，并打「没有 origin，按官方仓库标 official=true」。`bench new-app` 建的仓库正是没有 remote（`boilerplate.py:204-210`），S7 要建的 `frappe_debug` 会走到这里。后果：① official 条目以后 `lock-apps.sh` 不再读 remote（`:82-83`），`url` 永远是空；② 用户之后给它加了自己的 origin，`setup.sh` 第 4 段对 official 条目会 `remote remove origin`、`remote add upstream ""`（实测空 url 能加上）、禁推，把自有仓库配置成只读；③ `url` 为空时第 3 段直接跳过它，新机器上不会被克隆 | R9 FD-010 建议「按无 origin、只有 upstream 推断」；开发守则「官方 App 只配只读 upstream」的反面：自有 app 不该被当官方 | 判据改为 `not origin and upstream` 才标 official；两个 remote 都没有时不标 official，警告「无 remote，url 为空，须手工补」 | 本Session修 | — | 待裁决 |
| P1-02 | 低 | 演示站 `tabInstalled Application`；`install.py:137-145` | FD-012 的同步只在 `changed=True` 分支里做。演示站早已是目标顺序，归位走提前返回，子表从没被重写：查询得 idx 3 是 `frappe_china`（modified 00:43:29），`bench --site erx.localhost list-apps` 仍列在第 3 位。R9 FD-012 定位写的是「两站」，现在只有测试站好了。下次 `migrate`（`migrate.py:198`，`restore.sh:59` 会跑）会自愈 | R9 FD-012「镜像不一致会误导排查」 | (a) 不改代码，接受「下次 migrate／restore 自愈」，在 R10 收口报告注明演示站现状；或 (b) 经用户许可在演示站执行一次 `frappe.get_single("Installed Applications").update_versions()` 并提交（写演示站，在空账基准点之后多一次单表改动） | 延迟或不修 | 取 (a) 还是 (b)；(b) 要写演示站 | 待裁决 |
| P1-03 | 观察 | `install.py:140-150`；`commands/utils.py:315-316`；对照 `installer.py:377-387` | 归位在**提交前**清缓存并广播：`update_installed_apps_order` 只 `set_global` 不 commit，`clear_cache()` 与 `erase_persistent_caches()` 之后函数返回，`bench execute` 才 commit。窗口内若有运行中的 web／worker 处理请求，会读到已提交的旧 `installed_apps`，重新写进 Redis 的 `defaults::__global` 和本进程 `_SITE_CACHE`，之后没人再清。上游 `add_to_installed_apps` 是先 `commit` 再广播。窗口只有毫秒级；出了事 `check_app_order` 会报 `order_ok` 假、重跑归位能修好，所以定观察。读码推断，没复现 | 开发守则「判据必须能区分」之外：广播要在新状态可见之后才有意义 | 把末尾的 `clear_cache()`／`erase_persistent_caches()` 改挂 `frappe.db.after_commit.add(...)`。不要直接加 `frappe.db.commit()`：FD-007① 那个 mock 用例虽不受影响，但在真站上跑归位的测试会把测试事务提交掉 | 延迟或不修 | 改不改；改的话 FD-007① 用例要相应改成断言回调已登记 | 待裁决 |
| P1-04 | 观察 | `install.py:6,49-50,78-81` | ① 文案用 `TAIL_APPS[1:]` 表示「`frappe_china` 之外的尾部 app」，靠的是 `frappe_china` 排第一这一隐含约定，以后调整元组顺序文案就错；② 站上没装 `frappe_china` 时报「frappe_china 之后只能是 ['frappe_debug']…（排在它后面的：[]）」，不点明是没装 | 开发守则「不静默」（较弱） | 改为 `[a for a in TAIL_APPS if a != "frappe_china"]`；`frappe_china` 不在列表时单独报「未安装」 | 延迟或不修 | — | 待裁决 |

## 本片盲区自述

- 没跑测试、没做变异。新测试「能区分」的结论来自读码与 R9／SB 记的变异结果（M1、M3、SB 的 FD-008 变异），FD-005 (b)、FD-012 两行没有对应变异记录。
- P1-03 纯读码，没开 `bench start` 制造并发请求复现。广播在运行进程里到底生效没有，R9 已说明测不出，本片没再试。
- `lock-apps.sh` 实验用的是假仓库，没有真实 remote 网络行为；declared 条目的附注 tag 走 `^{commit}` 只读码确认，实验只在新 app 路径上试了附注 tag。Windows 下不设 `PYTHONIOENCODING=utf-8` 时中文输出乱码，这是本轮之前就有的现象，没立项。
- `update_versions` 的 `save()` 会触发 `"*"` 类 `doc_events`，没去逐个查各 app 对单表 DocType 的通配钩子。
- FD-008 扩大了回填范围：复制公司若缺映射科目号，`after_app_install` 会抛错中断装 HRMS。复制公司科目由源公司复制，按读码不会缺；R6 的 `validate` 同样会对它抛同一错误，所以没立项。

## 需主会话补跑的实测

1. **变异 M4（FD-005 b）**：删掉 `install.py:149` 的 `frappe.client_cache.erase_persistent_caches()`，跑 `--module frappe_china.tests.test_install`。预期 `test_reorder_installed_apps_rewrites_order_mirror_and_caches` 失败（`erase.assert_called_once_with()`）。跑完按原字节还原。
2. **变异 M5（FD-012）**：删掉 `install.py:145` 的 `update_versions()` 一行，同上。预期同一用例失败（`single.assert_called_once_with` 或 `update_versions.assert_called_once_with`）。
3. **P1-01 复现（可选）**：仓库外临时目录 `git init` 一个无 remote 的仓库放进假 `apps/`，跑 `lock-apps.sh` 写入。预期出现 `"url": "", "official": true`。本片已做过一次，结果见问题表。
4. **P1-02 若用户取 (b)**：`bench --site erx.localhost execute 'frappe.get_single("Installed Applications").update_versions'`（`bench execute` 取不到属性时会 eval 表达式，结果可调用就再调一次，见 `commands/utils.py:298-305`；结束时提交）。预期之后 `list-apps` 顺序为 `frappe, erpnext, crm, hrms, insights, raven, frappe_china`，`setup_complete` 仍为 1。
