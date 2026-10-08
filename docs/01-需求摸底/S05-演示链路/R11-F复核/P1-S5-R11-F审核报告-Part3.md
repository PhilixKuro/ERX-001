# F 复核分片报告 · 片 3（对象：应用配置脚本的 Raven 推送预检、约定措辞与「配置四个 App」改名 / 审核标准：R3 开发方案 Part3 TS-009、SL-007 ①；R10 F 复核报告 FD-037／045／050 的问题描述、建议与当场修清单 #1、#9、#12）

**轮次**：P1-S5-R11｜**步骤**：F 复核分片 3｜**日期**：2026-10-08｜**执行者**：Claude 子 Agent（只读）
**依据**：[R3 开发方案 Part3](../R03-开发方案/P1-S5-R3-C开发方案-Part3.md)（TS-009、SL-007 ①）；[R10 F 复核报告](../R10-F复核/P1-S5-R10-F审核报告.md)（问题清单 FD-037／045／050 行、当场修清单、修后验证）；[R10 Part3](../R10-F复核/P1-S5-R10-F审核报告-Part3.md)（全文）；[Stage 概况](../P1-S5-概况.md) 长效信息 #1（:106）、登记册 SH-P1S5006 ⑦（:122）
**被审范围**：主仓库 `git diff d7b89d6..288470b` 中 `docker/scripts/configure_apps.py`、`docker/configure-apps.sh`、`docker/README.md`（:94「结构」、:232-263「配置四个 App」）、Stage 概况 #1 与 SH-P1S5006 行、探针 `docs/01-需求摸底/Spike/P1-S5-R10-FD037-probe.py`。三个受变异影响的脚本一律经 `git show HEAD:` 读取，没读工作区

> 问题编号 `P3-xx` 是片内编号，主会话收口时转成 `FD-`。

## 覆盖自证

**读全了的**：R10 收口报告（全文）；R10 Part3（全文）；`HEAD:docker/scripts/configure_apps.py` 的 1-30、120-359 行（30-119 为 `TOOLS` 表与 `_apply`／`_norm`，本轮未动，`git diff` 为证）；`HEAD:docker/configure-apps.sh`（全文）；`HEAD:docker/README.md` 228-263；FD-037 探针（全文）；本片四个文件的 `git diff d7b89d6..288470b`；Stage 概况的 diff。

**对照的上游代码**（只读）：
- raven `e890308`：`raven/raven/doctype/raven_settings/raven_settings.py` 全文（87 行，`validate` 在 58-87）；`raven_settings.json` 中推送四字段、AI 相关字段的 `fieldtype`／`default`／`mandatory_depends_on`、`issingle`、有无 `reqd`；`hooks.py` 的 `"*"` doc_events；`api/notification.py`、`notification.py`、`boot.py` 中读 `push_notification_service` 的位置。
- frappe：`database/database.py` 的 `get_single_value`（878-927，取值后按字段类型 `cast`）、`get_singles_dict`、`sql_ddl`（451-458）、`close`；`utils/data.py` 的 `cast`（Select／Data 的 `None` 转成 `""`）；`model/document.py` 的 `_save` 调用顺序（555-610）、`_validate`（827-851，`_save_passwords` 在 `update_single` 之前）、`_set_defaults`、`_validate_mandatory`、`update_single`、`load_from_db`；`model/base_document.py` 的 `_save_passwords`（掩码写回）、`get_password`、`is_dummy_password`、`init_valid_columns`、`_get_missing_mandatory_fields`、`_validate_selects`；`frappe/__init__.py` 的 `destroy`。
- crm：`erpnext_crm_settings.py` 54-67（`validate` 的写入链）；erpnext `hooks.py` 的 `"*"` validate 钩子。

**只读查询**（两站各一遍，`bench mariadb`）：`tabSingles` 中 `Raven Settings` 全部字段（密钥类只取长度）；测试站 `tabCompany`、`ERPNext CRM Settings` 的 `enabled`／`sync_products`／`erpnext_company`／`modified`。

**只读实验**（测试站，各一次，`rollback` 收尾，没有 save、没有 commit）：
- `.claude/r11-tmp/p3/p3_validate.py`：取 `Raven Settings`，按 `configure_raven` 的目标值在内存设好连接字段，再按 8 种推送状态各调一次上游 `validate()`；同一状态下钩住 `frappe.db.get_single_value` 喂入相同值，调 `HEAD` 版 `preflight`，逐例对照「上游拒不拒」与「预检拦不拦」。另查 `tabSingles` 与 `__Auth` 中 Single 类密码字段的存放形态。
- `.claude/r11-tmp/p3/p3_before.py`：`d7b89d6`（改前）与 `HEAD` 两版 `preflight` 在测试站现状下各调一次。

**跳过的部分及原因**：没跑 `configure-apps.sh`，也没跑 FD-037 探针（两者都会写站）；没跑测试与变异。

## R10 已修项复核

| R10 项 | 修于 | 定位（文件:行） | 落地 | 生效 | 原问题消失 | 说明 |
|---|---|---|---|---|---|---|
| FD-037（取 (b)） | 当场修 #1 | `configure_apps.py:280-300`（`preflight` 推送预检）、`:335`（`main` 先调 `preflight`）；README :248、:262；Stage 概况 :122 SH-P1S5006 ⑦；探针 | ✅ | ✅ | ✅ | 逐条核见表后「FD-037 逐条核」。两站现状下预检必拦；上游会拒的状态预检一律拦下，没有漏；只在推送服务为空这一种罕见状态下比上游严（P3-04）。探针能区分改前改后，但没有前置断言、也不兜异常（P3-03） |
| FD-045 | 当场修 #9 | `configure_apps.py:8-11`（模块说明）；Stage 概况 :106 长效信息 #1；README :262 | ✅ | ✅ | ⚠ 部分 | 三处的核心说法一致，也与代码相符：`main`（:350）只捕获 `ConfigureError`，其余异常照常上抛，进程打 traceback，退出码 1。但同文件 `preflight` 的 docstring（:274）仍是「把会报错退出的检查**全**做在写之前」（P3-01）；README「已写的部分要按输出核对」做不到，因为写后抛错时脚本什么改动都不打印（P3-02） |
| FD-050 | 当场修 #12 | README :94；`configure-apps.sh:2`；`configure_apps.py:1`、`:324` | ✅ | — | ✅ | 四处都已改成「配置 CRM 集成与 Raven」。全仓 grep「配置四个」（不含 `frappe-bench/`）：现行文件里只剩 README :232 节标题（有意保留），其余都是历史报告、R3 方案原文与 R9 SB 改前副本，不应改。README :236「站点装完四个 App 之后」说的是装 app，不是配 app，说法正确。保留标题的理由「别处引用的锚」站不太住（P3-05） |

**FD-037 逐条核**：

1. **预检条件与上游拒绝条件是否一致。** 上游 `raven_settings.py:68-74`：只有 `push_notification_service == "Raven"` 时才依次要求 `server_url`、`api_key`、`api_secret`，缺一即 `throw`。没有别的前置开关：它不看 `enable_ai_integration`／`enable_local_llm`，四个推送字段也都不是 `reqd`。字段上的 `mandatory_depends_on` 只在前端生效，frappe `model/` 下没有任何服务端代码读它。服务的取值域是 `Frappe Cloud\nRaven`，缺省 `Raven`。空值判定用的是 Python 真值，空串和 `None` 都算未填，一个空格算已填。预检写的是 `service in (None, "", "Raven") and not all(三项)`，三项也按真值判，与上游相同。内存实验逐例对照如下：

   | 状态（连接字段都按目标值设好） | 上游 `validate()` | `HEAD` 版 `preflight` | 一致否 |
   |---|---|---|---|
   | A 现状：`Raven`，三项空 | 拒绝（`Please enter the Push Notification Server URL`） | 拦下 | ✅ |
   | B `Frappe Cloud`，三项空 | 通过 | 放行 | ✅ |
   | C `Raven`，三项齐 | 通过 | 放行 | ✅ |
   | F `Raven`，只缺 secret | 拒绝（`…API Secret`） | 拦下 | ✅ |
   | G `Raven`，secret 为掩码 `*****` | 通过 | 放行 | ✅ |
   | H `Raven`，地址只填一个空格 | 通过 | 放行 | ✅ |
   | D 服务为 `""`，三项空 | **通过** | **拦下** | ❌ 预检偏严（P3-04） |
   | E 服务为 `None`，三项空 | **通过** | **拦下** | ❌ 同上 |

   **没有漏拦**：上游会拒的状态（A、F），预检都拦下了。`validate` 的另两个 `throw` 分支，即 `auto_create_department_channel` 与 `enable_google_apis`，两站都是 0，按 FD-045 的口径归入「其余上游 validate」，不预检。

2. **Password 字段取到的是什么。** `push_notification_api_key` 在 json 里是 `Data`，不是 Password。只有 `push_notification_api_secret` 是 `Password`。frappe 保存时，`_save_passwords`（`base_document.py:1349-1369`）先把明文加密写进 `__Auth`，再把字段值替换成等长的 `*`；它在 `_validate` 里被调用，排在 `update_single` 之前，所以 `tabSingles` 存的是掩码。`get_single_value` 取回的就是这串 `*`，非空即为真。`get_doc` 载入时也是同一串 `*`，上游 `validate` 同样判为已填（实验 G 例两边都放行）。未填时 `tabSingles` 存的是 `NULL`，`get_single_value` 经 `cast` 后得到 `""`，两边都判未填（A 例）。所以不会出现「已填被判成未填」或反之。两站目前都没有任何 Single 类密码字段有值（`tabSingles` 与 `__Auth` 均 0 行），G 例的掩码是在内存里构造的。
3. **预检是否真在任何写入之前。** `main` :333-340 的顺序是 `preflight` → `configure_crm` → `configure_raven` → `ensure_bot_and_functions`。`preflight` 全程只读：`frappe.db.exists`、`get_single_value`、`get_all`，没有 `save`、`set_value` 或 DDL。实验后 `Raven Settings.modified` 仍是 `2026-10-05 19:23:21`。对照实验：现状下改前版 `preflight` 放行（于是先写 CRM 段，再在 Raven 段被上游拒），`HEAD` 版直接拦下。
4. **三处说法是否一致。** 报错文案（:296-299）、README :248、SH-P1S5006 ⑦ 说的是同一件事：缺省推送服务是 `Raven`，此时三项缺一即拒绝保存；两站三项都空；脚本在写入之前报错退出；处置办法是改为 `Frappe Cloud` 或填齐三项，留到 SH-P1S5006 唤醒时定。两站 `tabSingles` 的实际值与这些描述一致：`push_notification_service=Raven`，三项都是 `NULL`。只有一处行号小偏差：⑦ 写 `raven_settings.py:68-73`，第三个 `throw`（API Secret）实际在 :74，不影响定位，不单列为问题。
5. **探针能否区分改前改后。** 能，但靠的是「崩溃 vs 判定行」，不是探针自己的判定逻辑。`HEAD` 版：`preflight` 抛 `ConfigureError`，`main` 返回 1，`save` 0 次，`sync_products` 仍为 0，判「通过」。改前版：上游 `ValidationError` 不是 `ConfigureError`，`main` 不捕获，探针 :33-36 的 `try/finally` 只还原了 `Document.save`，异常继续往外抛。于是 :37 起的计数打印、teardown（把 `sync_products` 改回 1）和判定行都不执行，探针以 traceback 结束。这与 R10「改前：抛 traceback」的记述对得上。弱点见 P3-03。

## 延迟／不做项登记核对

本片范围内，R10 没有裁决延迟或不做的项（FD-044／046／047／048／052 分属别片）。SH-P1S5006 ⑦ 是这一轮新补的登记，已在上面「FD-037 逐条核」第 4 条核过，与实情一致。

## 业务规则合规核

| 规则条款 | 本轮改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001～BR-007 | 否 | 合规（不涉及） | 本片改动只涉及配置脚本的预检、注释与文档措辞，不碰科目、报表、税率与价税 |
| 是否新增或变更规则 | 否 | — | 长效信息 #1 新增的「配置类脚本先预检再写」是工程约定，归开发守则，不进 `业务规则.md` |

## 集成点登记（交接摘要）

**本片依赖**：
- raven `e890308` 的 `RavenSettings.validate` 推送分支（:68-74）。预检把这段上游条件复制了一份，raven 升级后若改了条件，两边会不同步，而且没有测试守着这处对应关系。锁定版本不变时没有影响。
- `apps.json` 中 raven 的锁定值：本片假定未变，请片 1 或主会话确认（本轮 `apps.json` 只改了 `frappe_china` 一行）。

**本片暴露**：
- `configure-apps.sh` 退出码 1 现在多了一种原因：设了 `URL`／`KEY`，而推送服务为 `Raven`（或空）且三项不齐。两站现状下，只要设了这两个值，就一定走到这里。
- 两站 `Raven Settings` 的推送四字段：服务为 `Raven`，其余三项为 `NULL`。S7 或任何经 `doc.save()` 写这张表的操作都会被上游拦下，这个结论与 R10 相同。

## 自证复核

| 被审产物声称 | 实际复核 | 一致否 |
|---|---|---|
| 当场修 #1：「Raven 已装、`URL`／`KEY` 都设了、推送服务为 `Raven`（或空）且三项未填齐时报 `ConfigureError`，写在任何写入之前；不改推送服务」 | 代码照此实现，只读，排在第一次写之前，没有改推送服务。「（或空）」比上游严（P3-04） | 一致（附观察） |
| 修后验证：探针「改后 rc=1、save 0 次、`sync_products` 仍为 0」「改前抛 traceback」 | 读码与只读实验都支持；探针本身没复跑 | 一致 |
| 修后验证：探针跑完测试站已恢复（`sync_products=1`） | 测试站 `sync_products=1`，`Raven Settings.modified` 停在 10-05，没有被写过的痕迹 | 一致 |
| 模块说明 :8-11「本脚本自己的检查……都在写任何东西之前做完；已知会拒绝保存的上游校验也在这里预先查；其余上游 validate 仍可能在写入之后抛错，那时以 traceback 退出、退出码非 0」 | `main` 只捕获 `ConfigureError`，其余异常上抛，退出码 1；`configure-apps.sh` 的 `set -e` 与 `docker compose exec` 会把退出码原样传出 | 一致 |
| `preflight` docstring :274「把会报错退出的检查全做在写之前」 | 收窄没有改到这一行 | 不一致（P3-01） |
| README :262「……报错时站点没有任何改动。别的上游校验仍可能在写入之后抛错……已写的部分要按输出核对」 | 前半句对 `ConfigureError` 成立；后半句做不到，写后抛错时没有任何改动输出 | 部分一致（P3-02） |
| Stage 概况 #1 收窄后的约定措辞 | 与模块说明同一口径 | 一致 |
| 当场修 #12「四处改齐；节标题保留，它是别处引用的锚」 | 四处改齐；全仓没有任何 markdown 锚链接指向该节，引用都是文字，而且绝大多数在历史报告里 | 一致（理由偏弱，P3-05） |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准／意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P3-01 | 观察 | `docker/scripts/configure_apps.py:274`（`preflight` docstring） | FD-045 收窄了模块说明与 Stage 概况 #1 的措辞，但同文件 `preflight` 的 docstring 仍写「只读：把会报错退出的检查**全**做在写之前」。证据：`git show HEAD:docker/scripts/configure_apps.py \| sed -n 274p`。这正是 FD-045 要消除的「全部」口径，同一文件里出现了两种说法 | FD-045 的建议（约定措辞收窄，不能说「全部」） | 改为「只读：本脚本自己的检查与已知会拒绝保存的上游校验，都在写之前做完；返回……」 | 本Session修 | — | 待裁决 |
| P3-02 | 低 | `docker/README.md:262` 末句；`configure_apps.py:336-348` | README 写「别的上游校验仍可能在写入之后抛错，那时以 traceback 退出、退出码非 0，**已写的部分要按输出核对**」。但 `main` 只在三段配置**全部返回之后**才打印说明与「改动 旧→新」（:341-346）；中途抛错时，这些都不会打印，输出只有 traceback（CLI 下 `msgprint` 也不落到 stdout）。用户手里没有「输出」可核。实际留下的是：最后一次 DDL 之前的写入（`sql_ddl` 先 commit，`database.py:451-458`）；之后未提交的写入随 `destroy()` 关闭连接被丢弃 | FD-045 的意图（说法与实情相符）；开发守则「不静默」 | (a) 只改 README：「此时脚本不列出已写字段；CRM 段若建过自定义字段，那一步及其之前的写入已提交，其余未提交的写入被丢弃，须到站上核对 `ERPNext CRM Settings` 等单例」；或 (b) 每次 `save` 后立即打印该段改动，让输出真能核对（改了输出时机，测试与 README 都要跟着改） | 本Session修 | 取 (a) 只改说法，还是 (b) 改打印时机。建议 (a)：写后抛错现在只是理论路径，改代码不划算 | 待裁决 |
| P3-03 | 低 | `docs/01-需求摸底/Spike/P1-S5-R10-FD037-probe.py:13-48` | 探针作为留证会被复跑，但它没有前置断言，也不兜异常。① **不先核推送状态**：若测试站以后已把推送服务改成 `Frappe Cloud`（SH-P1S5006 ⑦ 的处置之一），`HEAD` 版 `preflight` 会放行，`main` 会把假地址 `http://example.invalid/v1` 和假密钥 `dummy` 写进测试站的 `Raven Settings`，置 `enable_ai_integration=1`，并 **commit**。探针只还原 `sync_products`，不还原 Raven Settings，测试站就留下一套假的 LLM 连接。② **不兜非 `ConfigureError` 异常**：:33-36 的 `try/finally` 只还原 `save` 钩子；`main` 一旦抛上游异常（改前版正是如此），:39-48 的 teardown 不执行，`sync_products` 停在 0（若异常发生在 CRM 段写回之前），也不打判定行。R10 能区分改前改后，靠的是人看 traceback | 开发守则「不静默」；测试站状态可恢复 | ① 开头加断言：`push_notification_service == "Raven"` 且三项为空，否则拒跑并说明；② 把 `main` 调用包进 `try/except Exception`，记为「抛异常（改前形态）」，并让 teardown 放进 `finally`；③ 文件头注明「推送状态改变后此探针失效」 | 本Session修 | — | 待裁决 |
| P3-04 | 观察 | `configure_apps.py:292`（`in (None, "", "Raven")`）；上游 `raven_settings.py:68` | 预检把空服务也当作 `Raven`，上游只认 `== "Raven"`。内存实验 D（`""`）、E（`None`）两例：上游 `validate()` 通过，预检拦下，报错文案还写「推送服务是 Raven」，与实情不符。两种状态怎么来：① `tabSingles` 一行 `Raven Settings` 都没有时，`get_doc` 走 `new_doc` 取缺省 `Raven`，上游会拒，而 `get_single_value` 经 `cast` 返回 `""`；这种情形下预检把空当 `Raven` 是**对的**；② 有其它字段的行、唯独缺这一字段的行，或该行值为空串（只能经 API／`db.set_single_value` 造出）时，`get_doc` 得到 `None`／`""`，上游放行，预检误拦。两站都有完整的行、值为 `Raven`，现状下碰不到；`None` 那一项在 `cast` 之后永远取不到，是死值（后两点为读码） | FD-037 的判定标准（预检与上游拒绝条件一致） | 不改判据（①的情形要它）；注释补一句「空值按缺省 Raven 处理，覆盖单例从未保存的情形，可能误拦单个字段缺行的罕见状态」；文案改为「推送服务是 Raven（或未设）」 | 延迟或不修 | 改不改文案 | 待裁决 |
| P3-05 | 观察 | `docker/README.md:232`（节标题「## 配置四个 App」）；R10 当场修 #12 括注 | 正文、头注释与 argparse 都改成了「CRM 集成与 Raven」，节标题仍是「配置四个 App」，FD-050 指出的「四个」说多了，在标题上依旧存在。保留理由「它是别处引用的锚」：全仓 grep `#配置四个`、`配置四个-app`，没有任何 markdown 锚链接；以「配置四个 App」节名引用它的，都是 R5～R10 的历史报告和 R3 方案原文，现行常驻文件（`项目概况.md`、`开发守则.md`、Stage 概况）都没有按此节名引用 | FD-050 的意图（结构说法与实情一致） | 维持现状也可（历史报告靠节名定位，改名会让它们失去对应）；或改名，并在新标题下加一行「原『配置四个 App』」作为检索锚 | 延迟或不修 | 改不改节标题 | 待裁决 |

## 本片盲区自述

- **FD-037 只验到 `validate()` 与 `preflight` 这一层**，没有真跑 `configure-apps.sh`。`save()` 链上 `validate` 之前的环节，如 `_set_defaults`（单例非新建时不补缺省）、`_restore_masked_fields_from_db`（Administrator 直接跳过）、erpnext 的 `"*"` validate 钩子，都是读码判断，没有实测。
- **P3-04 的两种来源**（单例从未保存、单个字段缺行）都是读码推断。为了不写站，没有在测试站删行去复现，只用内存赋值模拟了取值结果。
- **P3-02 的「哪些写入已提交」**按 `sql_ddl` 先 commit 推断。首跑建自定义字段的 DDL 路径，R9、R10、本轮都没有实测过。
- **探针没有复跑**（会写站）。P3-03 ① 的后果按读码推断：放行后 `configure_raven` 会 save，`main` 随后 commit。
- 没有核 raven 推送服务改成 `Frappe Cloud` 后的运行时行为。这是 SH-P1S5006 ⑦ 留给唤醒时定的事，不在本片范围。
- 没看 `setup.sh`、`lock-apps.sh`、compose、端口相关改动（分属别片），也没看 `frappe_china` 仓库的改动。
