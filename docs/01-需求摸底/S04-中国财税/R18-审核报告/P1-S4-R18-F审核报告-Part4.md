# 审核报告·Part4（对象：frappe_china Part4 范围＋`docker/` / 审核标准：R7 开发方案 Part4 ＋ R17 F 报告各项建议与判定标准）

**轮次**：P1-S4-R18｜**日期**：2026-10-03｜**步骤**：`plannedDev` F（audit，复核轮），第 4 片｜**执行者**：Claude 子 Agent（Opus 5.5，只读）
**依据**：[R7 Part4](../R07-开发方案/P1-S4-R7-C开发方案-Part4.md)（全读）、[R17 收口](../R17-审核报告/P1-S4-R17-F审核报告.md)（问题清单、当场修清单）、[R17 Part4](../R17-审核报告/P1-S4-R17-F审核报告-Part4.md)、[R17 SB 回执](../R17-审核报告/P1-S4-R17-SB修复回执.md)、`docs/开发守则.md`「各 app 用 shallow clone」「版本锁定」「git 需显式配代理」、`docker/README.md`
**被审范围**：`frappe_china` `21faeb9..cd5d565` 中的 `README.md`、`accounting/statements/cash_flow_statement.py`、`cn_tax/doctype/bank_statement_preprocess/bank_statement_preprocess.js`、`tests/test_cash_flow.py`；主仓库 `5a96ad3..5ade13c -- docker`（`apps.json`、`scripts/setup.sh`），以及 `setup.sh`、`lock-apps.sh`、`apps.json` 当前全文
**方法与边界**：只读。没跑测试、没 migrate、没写站点、没跑 `up.sh`／`restore.sh`。站点只做了 SELECT。宿主临时目录里做了纯 git／bash 实验（含一次真实 GitHub 浅克隆），做完已删。

## 覆盖自证

**读全的**：
- 代码：上述四个 frappe_china 文件的 diff；`cash_flow_statement.py:100-200`；`bank_import.py:289-405`（预处理与导入的落库、`_mark_failed`）；`cash_flow.py` 的 `_validate_items`、`before_cancel`、`_assign_default_codes`、`_direction_fits`；`patches/fd004_default_accounts.py`；`company_defaults.json`；科目表 JSON 里 400103／1606／1901／5711010 的 `root_type`、`account_type`。
- docker：`setup.sh` 全文（343 行）、`lock-apps.sh`、`apps.json`、`up.sh`、`docker/README.md` 第 117-140 行；`5a96ad3..5ade13c` 的 docker diff。
- 上游：frappe `public/js/frappe/request.js`（`frappe.call`、`frappe.request.call` 的 done／always／fail、`statusCode` 各分支、`prepare`、`cleanup`）、`form/form.js:reload_doc`、`model/model.js`（`with_doc`、`doc_update` 实时监听）、`model/document.py:notify_update`、`form/toolbar.js:700-845`（Amend 按钮）、`locale/zh.po` 的 `Amend`；`esbuild/esbuild.js`、`build-cleanup.js`。erpnext `stock_entry.py:811-945、2664-2750、3377-3405`、`stock_entry_utils.py:120-191`、`item.py:292-335`、`bom.py:1490-1620`、`stock_entry_type.py:291-350`、`subcontracting_receipt.py:935-950`、`stock_reconciliation.py:66-71、975-990、1424-1432`、`item_group.py:get_item_group_defaults`、`controllers/stock_controller.py:get_gl_entries`；`locale/zh.po` 的 `Material Issue`。bench（容器内 `/home/frappe/.bench/bench`）`app.py:188-205、659-760`、`bench.py:shallow_clone`、`config/common_site_config.py:12`。
- zelin：`cash_flow.js:1-40`（`set_query`）、`default_accounts.csv` 第 21、22、30 行。

**做过的只读实验与查询**：
1. 宿主临时目录，本地仓库：① 完整克隆后按 SHA `fetch --depth 1` 一个本地没有的新提交；② 完整仓库上 `--unshallow`；③ `clone --depth 1 --origin upstream` 后按第 3 段原样取 remote、fetch、reset 到旧提交；④ protocol v0 按 SHA fetch。
2. 宿主临时目录，**真实 GitHub**（经宿主代理 7897）：照 bench 参数 `git clone --depth 1 --branch main --origin upstream PhilixKuro/FrappeChina`，按第 3 段命令锁到旧提交 `48e7933`；protocol v0 再取 `21faeb9`；取不存在的 SHA；`--unshallow`；`remote remove upstream` 对分支跟踪配置的影响。
3. 宿主临时目录：第 3 段 python 段对空串、`-`、缺 `url` 的输出与 `read` 的解析；第 4 段在新克隆上的 remote 结果；`set -euo pipefail` 下进程替换里 python 失败、循环体内 `exit 1` 两种情况。
4. 容器内只读：三个 app 的 `git status --porcelain` 行数（默认与 `-c core.autocrlf=true` 各一次）、分支跟踪配置、`sites/common_site_config.json` 的 `shallow_clone`；第 9 段判据对三个 app 的实际取值（`public/` 在否、`dist/css` 文件数）。
5. 两站 SELECT：`tabTranslation` 里有没有覆盖 `Amend`／`Cancel` 或译文含「修订」的记录（两站都是 0 条）。
6. `bash -n docker/scripts/setup.sh` 通过；`git ls-files --eol` 看 `setup.sh` 是 LF。

**跳过及原因**：
- 没实跑 `setup.sh` 任何一段，也没跑真 `bench get-app`（硬约束）。第 3 段的结论来自 git 实验（含真实 GitHub），没在容器经 `host.docker.internal` 代理复做，要实跑的步骤列在文末。
- FD-055 没在浏览器复验（硬约束）。结论来自读 `request.js`，并与 SB 回执的浏览器取证对照。
- 没重跑测试与变异（硬约束）。`test_cash_flow.py` 的改动只核了断言字串。
- R7 Part4 的 TS-015～022 本轮没有改动，各任务的其余要求沿用 R17 Part4 的核查结论，本片只核与 R17 修复相关的条目。

## 逐项复核表

三层：落地（代码在）→ 生效（真被调用、没被绕过）→ 原问题消失。

| R17 项 | 定位（文件:行） | 落地 | 生效 | 原问题消失 | 说明 |
|---|---|---|---|---|---|
| **FD-045** 新机器锁定不生效 | `setup.sh:155-181`（`:165` 选 remote，`:166-169` cat-file→按 SHA fetch→unshallow，`:172-179` reset 失败时 `exit 1`） | ✅ | ✅ | ✅（git 层实证）／⚠ 有新边角 | **按 SHA fetch 能用**：真实 GitHub 上 `fetch --depth 1 upstream 48e7933` 退出码 0，protocol v0 也是 0（GitHub 允许 want 可达提交）。之后 `reset --hard` 到 `48e7933`，仍在 `main`。不存在的 SHA 报 `not our ref` 退出 128，`--unshallow` 之后 reset 仍失败 → 走 `exit 1`。**unshallow 兜得住**：浅克隆上 `--unshallow` 成功，拿到全部 21 个提交；对完整仓库 `--unshallow` 报 `does not make sense`，被 `|| true` 吞掉，接着 reset 失败退出，不会误判成功。**报错退出真生效**：循环用 `< <(…)` 喂数据，循环体跑在主 shell 里，实验中 `exit 1` 让外层退出码为 1。**与第 4 段不冲突**：第 3 段运行时只有 `upstream`，取它；重跑时第 4 段已加过 `origin`，取 `origin`，两者都指自有 fork。按 SHA fetch 只写 `FETCH_HEAD`，不留远端跟踪引用，第 4 段删、加 remote 不受影响。**代理**：`GIT_CONFIG_*` 已 `export`（`:52-54`），fetch 子进程继承。**已有 bench 重跑**：只有 `current ≠ 锁定值` 才进入，现在 HEAD＝锁定值，直接走 `:158`；新加的 `cat-file -e` 让本地已有该提交时不再联网，比改前好。新边角见 P4-02、P4-06、P4-07 |
| **FD-046** `apps.json` 未重锁 | `docker/apps.json:17` | ✅ | ✅ | ✅ | `cd5d565dc…` ＝ frappe_china `HEAD` ＝ `origin/main`（`rev-parse` 与 `ls-remote` 都是这个值），工作区（宿主）干净。erpnext `12cd563`、frappe `c1f1e8e` 各等于 fork 的 `version-16` 最新。主仓库 `HEAD`＝`origin/main`＝`5ade13c`，锁定已推送。R17 P4-02 建议的第 ② 项（`setup.sh` 不往回退的保护）在合并成 FD-046 时丢了，既没裁决也没登记，见 P4-05 |
| **FD-049** 空字段被 `read` 合并 | `setup.sh:187`（输出 `-`）、`:128-129`（还原） | ✅ | ✅ | ✅ | 实验结果：缺 `commit` → `commit=[]`、`name=[frappe_china]`，不再错位；`branch`／`commit`／`app_name` 为空串时，`or` 把它们当成缺省（改前 `a.get("branch","version-16")` 遇到空串会输出空，照样错位，这次一并修好）。**字段真值就是 `-`**：commit 不可能是 `-`（不是 SHA）；app_name 为 `-` 不是合法的 Python 包名；branch 的 `-` 不做还原，按原样传给 `ls-remote`／`get-app`，同样不是合法分支名。三种都不构成实际风险。**`url` 为空**：行首是 tab，被当作 IFS 空白吃掉，各字段左移一位（`url=[main]`），随后 `ls-remote main` 失败、`exit 1`——会响亮失败，只是报错文字看不出原因（属于配置写错，不另立条目）。python 本身出错时不报错，见 P4-03 |
| **FD-050** 1901 的上游兜底来源 | app `README.md:129` | ✅ | — | ⚠ 部分 | 委外分摊损失（`subcontracting_receipt.py:942-944`）、服务端建的期初盘点（`stock_reconciliation.py:68-71`；Opening Stock 只拒收损益类科目，`:981-987`，1901 能通过）两条与源码一致。**但有三处与源码不符**：①「物料发出以外的用途」把 Material Issue 排除在外了，可 `stock_entry.py:2737-2743` 中 Material Issue 同样在物料、物料组都没有费用科目时取 `stock_adjustment_account`；② 补救办法「给每个物料组设好费用科目可避免前两种」，对 BOM 与生产作业卡这两条路不成立——`bom.py:1513、1606-1613` 只读物料级 `Item Default`，`stock_entry_type.py:291-326` 根本不取费用科目，一律兜底；③ 漏了物料主数据「期初库存」字段：`item.py:292-330` → `stock_entry_utils.py:133-134`，无条件取 1901。见 P4-04 |
| **FD-054** README zelin 修改表三行 | app `README.md:74、98、110、112`；删空行 | ✅ | — | ✅ | 逐行对照：`:74` zelin 原值是 `生产成本-库存调整`（科目表 `400103`，`root_type` Asset，`account_type` Stock Adjustment）和 `固定资产清理`（`1606`，Asset），与 zelin `default_accounts.csv:21、30` 一致；「原值都是资产类」成立；patch 只改仍是旧值、且是本科目表的公司（`fd004_default_accounts.py:15-22`）成立。`:98` zelin `cash_flow.js:6-14` 用 `set_query` 过滤 `formula` 为空且方向与借贷相符，本 app 在 `cash_flow.py:95-107` 改成 validate 拒收，成立。`:110、112` 预填跳过方向不符或公式行、都不符留空（`cash_flow.py:220-228`），成立。原来断开列表的空行已被新条目取代 |
| **FD-055** 预处理失败后不刷新 | `bank_statement_preprocess.js:7-15` | ✅ | ✅（读码） | ✅（SB 浏览器取证，本片读码复核一致） | `frappe.call` 把 `always` 原样传下去（`request.js:114`）。`$.ajax` 链上回调的登记顺序是 done → always（`:315-332`）→ fail，jQuery 按登记顺序执行。**成功（200）**：done 走 `success_callback`（本调用没给 `callback`，什么也不做）→ always：先 `cleanup`（解冻、弹服务端消息）再 `reload_doc`。**417**：always（cleanup 弹报错 → 刷新）→ fail 的 417 分支调 `error_callback`（未给）。**5xx**：always（刷新）→ fail 的 500 分支 `report_error` 弹错误窗。**网络失败**：always 里 `data` 是 xhr，`responseText` 为空，跳过解析；`cleanup` 没有消息可弹 → `reload_doc`，它的 GET 也会失败，表单不变，不损坏数据。刷新都在 cleanup 之后，报错窗不会被刷新冲掉。**刷新两次／回调冲突**：原来的 `.then` 已删，没有别的 callback。成功路径上 `doc.save()` 会发 `doc_update` 实时消息（`document.py:1503-1509`），`model.js:154-170` 在 `modified` 不同时也会 `debounced_reload_doc`，所以**可能多一次 GET**——改前用 `.then` 时也是这样，两次都只是重读，没有副作用。失败路径用 `db.set_value` 补写，不发实时消息，只刷新一次 |
| **FD-059** 说明行不指向「修订」 | `cash_flow_statement.py:143`；`test_cash_flow.py:375` | ✅ | ✅ | ✅ | 文案是中文硬写，没经 `_()`，和同函数里另外三条说明写法相同（R17 Part4 已登记），所以不需要 csv 条目，`test_translations.py` 也不涉及。测试断言同步改成了新字串。**「修订」就是界面上的按钮名**：已取消单据的主按钮是 `__(status)`，`status="Amend"`（`toolbar.js:782-783、826-844`），frappe `locale/zh.po:2366-2367` `msgid "Amend"` → `msgstr "修订"`；erpnext 的 zh.po 没有这一条；两站 `tabTranslation` 没有覆盖。两个会计角色有 `amend`（R14 FD-006），按钮会出现。R7 方案 SL-007 ⑦ 的原句没改（属于 R7 产物），措辞的偏离已经用户裁决（FD-059） |

## 新发现清单

| 片内编号 | 严重程度 | 定位 | 问题 | 证据 | 建议 | 建议档位 | 待裁决点 |
|---|---|---|---|---|---|---|---|
| P4-01 | 中 | `docker/scripts/setup.sh:306-326`（第 9 段） | **在已装 `frappe_china` 的 bench 上重跑 `up.sh`，会在最后一段中止**；新机器上搭建也一样，退出码非 0。第 9 段的判据：凡有 `<app>/public/` 的 app，都要求 `public/dist/css` 非空，否则 `bench build`，build 后仍空就 `exit 1`。`frappe_china` 提交了 `public/.gitkeep`、`css/`、`js/`，但没有任何 `*.bundle.*` 源文件，`bench build`（esbuild 只收 `public/**/*.bundle.*`，`esbuild.js:255-268`）不会给它生成 `dist`，于是走到 `:324-325`「bench build 后 frappe_china 仍无 dist/css，中止」。这一段在 `frappe_china` 加入前就写好了（`ae901bd`，2026-09-18），之后各轮都没跑过 `up.sh`。R14 FD-009「重跑 `up.sh` 不失败」与 R17 的「重跑不再二次克隆 ✅」都只核了第 3 段 | 容器内只读：`erpnext dist/css=6`、`frappe=16`、`frappe_china public 在、dist/css=0`；`frappe_china/public` 只有 `.gitkeep`、`css/`、`js/`（均空）；`assets.json` 里没有 `frappe_china` 条目 | 判据改为「该 app 有 `*.bundle.*` 源文件（排除 `dist`、`node_modules`）才要求有 `dist`」；或改用 `sites/assets/assets.json` 里有没有该 app 的条目来判断 | 新Session修 | 是否同时把第 6～9 段纳入「重跑 `up.sh`」的验收（现在只验过第 3 段） |
| P4-02 | 低 | `setup.sh:159-160`；宿主 `C:/Program Files/Git/etc/gitconfig` 里 `core.autocrlf=true` | **在本机，锁定这一步对 frappe_china 实际不会执行，只打警告**。宿主 Git for Windows 用 `autocrlf=true` 检出，工作区是 CRLF；容器里的 git 没有这项设置，把这些文件都当作已修改。所以只要锁定值 ≠ HEAD，就走 `:160`「有未提交改动，跳过」，然后继续往下跑。FD-045 才确立的「锁不上就响亮失败」在这条分支上不成立。（副作用：本机暂时碰不到 R17 P4-02 说的「往回退」，但到 Linux 新机器上就会退。） | 容器内 `git status --porcelain`：frappe_china 27 行、erpnext 2 行；加 `-c core.autocrlf=true` 后都是 0。宿主上两者都干净 | 第 4 段给各 app 写仓库级 `core.autocrlf true`（宿主本来就是 true，只是让容器的判断与宿主一致，做法同已有的 `core.fileMode false`）。另外，「有改动跳过」要不要也 `exit 1` 由用户定 | 新Session修 | 有未提交改动时：继续警告，还是中止 |
| P4-03 | 低 | `setup.sh:182-189`（`done < <(python …)`） | **`apps.json` 写坏时，脚本静默跳过整个第 3 段**。进程替换里的退出码不受 `set -e`／`pipefail` 约束：JSON 语法错时一个 app 都不装，脚本照样往下跑；某条缺 `url` 时，python 在那条抛 `KeyError`，后面各条都被静默丢掉。FD-049 改的就是这一行，但没顾到这一点 | 实验：JSON 截断、第二条缺 `url` 两种情况，循环都正常结束，外层退出码 0 | 先 `entries=$(python …)`（命令替换的失败会被 `set -e` 捕到），再 `<<<"$entries"` 喂给循环；或循环结束后 `wait $!` 检查退出码 | 新Session修 | — |
| P4-04 | 低 | app `README.md:129` | **FD-050 补的这条「已知限制」有三处与上游源码不符**（详见逐项表 FD-050 行）：① Material Issue（界面译名「其他出库」，README 写的「物料发出」不是界面词）也会兜底到 1901，不该排除；② 「给物料组设费用科目」挡不住 BOM 带出与生产作业卡这两条路：BOM 只读物料级默认，作业卡这条路完全不取，都要在物料的 Item Default 上设；③ 漏了物料主数据「期初库存」：保存物料时自动建入库凭证，贷方无条件记 1901——S7 造演示数据最可能先走这条路。（BOM 生产时原料与成品两边都落 1901，按读码通常相互抵消，没做实测。） | `stock_entry.py:2726、2737-2743`；`bom.py:1513、1606-1613`；`stock_entry_type.py:291-326`；`item.py:292-330`；`stock_entry_utils.py:133-134`；erpnext `zh.po:30693-30694` | 把这条改成：其他出库／其他入库等手工库存凭证（物料、物料组都没有费用科目时）；按 BOM 或作业卡带出的行（只看物料级默认）；物料「期初库存」；委外分摊损失；服务端期初盘点。补救写成「物料组与物料都设费用科目；期初库存改用库存盘点录入」 | 本Session修 | — |
| P4-05 | 观察 | R17 收口 FD-046 行；R17 Part4 P4-02 建议 ②；S4 延迟登记册 `SH-P1S4021`～`036` | **R17 P4-02 的第 ② 项（`setup.sh` 不把分支往回退的保护）在收口合并时丢了**。FD-046 只保留了「重锁」，那项建议档位是 `新Session修`、带待裁决点，收口里既没裁决也没登记。现在 HEAD＝锁定值，暂时没有风险；但只要某轮提交了 frappe_china 而没重锁，又有人跑 `up.sh`，P4-02 的情形就会重现（在 Linux 或干净克隆上；本机被 P4-02 的假改动挡住了） | `grep` R17 收口与 S4 概况，没有「不回退」「is-ancestor」的裁决或登记 | 收口时补裁：或者补登记一条延迟项，或者随 P4-01／P4-02 一起修（`merge-base --is-ancestor 锁定值 HEAD` 成立时只警告、不 reset） | 延迟或不修（补登记） | 补登记，还是一起修 |
| P4-06 | 观察 | `setup.sh:167` | **锁定时按 SHA `--depth 1` fetch，会把完整克隆变成浅克隆**。已有的完整仓库（本机 frappe_china 现在 `is-shallow=false`）遇到「锁定值本地没有」时，fetch 写入 `.git/shallow`，reset 之后 `git log` 只看得到 1 个提交。改前的写法也有这个问题，不是 FD-045 引入的；开发守则本来就主张浅克隆，提交与推送不受影响 | 实验 ①：fetch 前 `shallow=false`，fetch 后 `true`；reset 后 `log` 只有 1 行 | 可以只在 `is-shallow-repository` 为 true 时才带 `--depth 1`；也可以不改，在 README 里写一句 | 延迟或不修 | — |
| P4-07 | 观察 | `setup.sh:166-169、176-177` | **fetch 的 stderr 被丢掉了，报错原因可能指错方向**。代理不通、容器重建后凭据丢失（README「私有仓库」节说过 `down.sh` 会丢凭据）、网络超时，最终都报「取不到锁定的 commit…检查该 commit 是否已推送」。另外这步 fetch 没设 `GIT_TERMINAL_PROMPT=0` 和 `timeout`，与 `:140` 的探测写法不一致。`docker/README.md:121` 也没写「锁不上现在会中止 `up.sh`」 | 读码；实验中失败时 git 真正的报错是 `not our ref`，被 `2>/dev/null` 吞了 | 不丢 stderr，或者把它留到报错时一起打出来；fetch 前加 `GIT_TERMINAL_PROMPT=0 timeout 60`；README 版本记录那段补一句 | 延迟或不修 | — |
| P4-08 | 观察 | `setup.sh:197-224`（第 4 段） | **第 4 段在新机器上的结果与注释不符**（在 FD-045 之前就这样）。① `frappe_china`（`official` 为空）：加上 `origin`＝fork，但 bench 建的 `upstream`（同样是 fork、push 没禁用）没删，`main` 仍跟踪 `upstream`；本机 frappe_china 只有 `origin`，是后来手工整理过的。② frappe／erpnext：`remote remove upstream` 会连带删掉 `branch.version-16.remote`，归位后分支没有跟踪，直接 `git push`／`pull` 不带参数会报 no upstream（本机 frappe 正是这样）。开发守则写的是带参数的 `git push origin version-16`，按文档操作不受影响 | 实验：新克隆按第 4 段处理后 `origin`、`upstream` 都是 fork，`branch.main.remote upstream`；`remote remove` 后分支配置消失；本机 `git -C frappe branch -vv` 没有跟踪信息 | 自有 app 也删掉 `upstream`；归位后 `git branch --set-upstream-to origin/<branch>` | 延迟或不修 | 归 Part1（remote 归位）一起判断 |

**定级说明**：P4-01 定「中」：它让文档里唯一的一键重建命令在最后一步报错退出，而且 R14／R17 都判「重跑不失败」已解决，却没跑到这一段。在第 9 段之前，站点和各 app 都已装好，所以按「环境实际可用」看也可以降为「低」。P4-02 在「低／观察」之间：它会打警告、不静默，但正好让 FD-045 的修复在本机失效。P4-04 定「低」：只是文档，但它给的补救办法会误导 S7 造数据。

## 业务规则合规核

| 规则条款 | 本片改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001～007 | 不涉及 | — | 本片改动只有 README 文字、说明行文案、前端刷新和环境脚本，没有产品语义改动 |
| DEC-122（库存调整默认科目 1901） | 涉及（README 描述其后果） | 规则本身没变；README 对后果描述不准（P4-04） | 不新增、不改写规则 |

本片没检出新增或改写的业务规则。

## 交接摘要

**本片依赖别片**：
- Part1：第 1 段 `bench init`（frappe 同样是 `--depth 1 --origin upstream`，`common_site_config.shallow_clone=true`）、第 4 段 remote 归位（P4-08）。
- Part5／R15：DEC-122 的口径。P4-04 改的是 README 对 1901 来源的描述，口径本身不归本片判断。

**本片暴露给别片／收口**：
- `docker/apps.json` 三条锁定值＝各仓库远端最新；主仓库已推送。
- **`up.sh` 重跑会在第 9 段中止**（P4-01）：在修好之前，任何「跑一次 `up.sh` 验证」的计划都会在这里失败。
- **本机容器里 git 把 frappe_china 看成有 27 处改动**（CRLF，P4-02）：凡在容器里用 `git status` 判断「工作区干净」的脚本或探针（不只是 setup.sh），在本机都会误判。
- 物料「期初库存」会贷记 1901（P4-04）：S7 造数据时，若在物料上填期初库存，12 月会触发「年末待处理财产损溢尚有余额」。
- FD-055 确立的约定（服务端失败会补写单据的按钮，用 `always` 刷新）读码成立。成功路径可能因实时消息再刷新一次，没有副作用。
- R17 P4-02 ② 那项保护的去向要收口补裁（P4-05）。

## 建议主会话做的实跑清单

1. **第 3 段容器实跑**（照 R17 harness：原样执行第 3 段，把 `bench get-app` 换成同参数的 `git clone --depth 1 --branch <b> --origin upstream`，克隆到容器临时目录，并经 `GIT_PROXY` 代理）：
   - A：锁到非最新提交 → 断言 `HEAD`＝锁定值、仍在分支上；
   - B：删掉 `commit` → 不错位；
   - C：不存在的 SHA → 退出码 1，看报错文字（P4-07）；
   - D：先完整克隆，再锁到本地没有的新提交 → 记录前后的 `is-shallow-repository`（P4-06）；
   - E：`apps.json` 写坏（截断、缺 `url`）→ 确认脚本没有中止（P4-03）。
2. **第 9 段干跑**：容器里只执行第 9 段的两个循环，把 `bench build` 换成 `echo build`，预期 `missing=frappe_china`，第二个循环报「仍无 dist/css，中止」（P4-01）。修好后再用真 `bench build` 跑一次。
3. **本机锁定分支**：把 frappe_china 拷到容器临时目录（保留 CRLF 工作区），让 `apps.json` 锁到 `HEAD~1`，执行第 3 段，预期走「有未提交改动，跳过」（P4-02）；加上仓库级 `core.autocrlf true` 再跑一次，确认真的 reset。
4. **可选**：FD-055 用 Accounts User 角色在浏览器再点一次（SB 回执拿不准处 3），顺便在 DevTools 网络面板看成功路径是否有两次 `getdoc`。

## 盲区自述

- **没跑 `setup.sh` 和真 `bench get-app`**：第 3 段的结论来自 git 实验。真实 GitHub 那次走的是宿主代理，没在容器经 `host.docker.internal` 复做。被强推丢掉、不再可达的 SHA，GitHub 是否还给，没有测。
- **P4-01 是读码加目录实查**：我没执行 `bench build`，「build 后 frappe_china 仍没有 dist」的依据是 esbuild 的收集规则，加上 `frappe_china` 安装时那次构建确实没产出（`assets.json` 里没有它）。
- **P4-04 里 BOM 生产「原料与成品相互抵消」只是推演**（`stock_controller.get_gl_entries` 加 `merge_similar_entries`），没实测；成本中心不同时可能不抵消。
- **FD-055 的网络失败分支**：`reload_doc` 先 `remove_from_locals` 再 GET，GET 失败后表单仍指着已从 `locals` 移除的对象。我判断后续保存不受影响，但没验证。
- **没往这些方向找**：`lock-apps.sh` 在宿主跑时用的是 Windows `python`；`restore.sh`／`backup.sh` 本轮没改，没复核；frappe／erpnext 的锁定值与上游 `version-16` 配套与否，不属于本轮。
- **把握最低处**：P4-02 的严重程度。它取决于本机以后会不会出现「锁定值 ≠ HEAD」（只有别的机器推了新锁定、或手工改了 `apps.json` 才会），现在不触发。
