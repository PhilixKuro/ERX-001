# F 复核分片报告 · 片 1（对象：R10 已修项 FD-040、不做项 FD-044 的注明、延迟项 FD-047（SH-P1S5011）、不做项 FD-048／052 与版本锁定 / 审核标准：R3 开发方案 Part1（SL-001～002、TS-001～005）＋ Part2（SL-003～004、TS-006～008）；R10 F 复核收口报告与片 1 报告）

**轮次**：P1-S5-R11｜**步骤**：F 复核分片 1｜**日期**：2026-10-08｜**执行者**：Claude 子 Agent（只读）
**依据**：[R3 开发方案 Part1](../R03-开发方案/P1-S5-R3-C开发方案-Part1.md)、[Part2](../R03-开发方案/P1-S5-R3-C开发方案-Part2.md)；[R10 F 复核报告](../R10-F复核/P1-S5-R10-F审核报告.md)（「问题清单」FD-040／044／047／048／052 行、「当场修清单」#4／#8／#10／#14、「修后验证」FD-040 条）、[R10 Part1](../R10-F复核/P1-S5-R10-F审核报告-Part1.md)；`docs/开发守则.md`「官方业务 App」「装完任何新 app 后」两节；Stage 概况登记册 SH-P1S5011 行与 R10 行
**被审范围**：主仓库 `d7b89d6..288470b` 中 `docker/lock-apps.sh`、`docker/apps.json`、`docs/项目概况.md`（演示站状态一句）、Stage 概况（R10 行、SH-P1S5011）；`frappe_china` `9d53d39..052e4c3`（只有 `README.md` 与 `tests/test_realtime_check.py`，都不在本片依据内，只核了它不碰 `install.py`）

## 覆盖自证

**读了的依据**：R10 收口报告全文；R10 Part1 全文；两仓本轮 `git diff --stat`，以及主仓库中 `lock-apps.sh`、`apps.json`、`setup.sh`、`项目概况.md`、`开发守则.md`、Stage 概况、P1 概况的完整 diff。R3 Part1／Part2 正文这一轮没有重读：本片涉及的改动只落在 TS-002（锁定与 remote 归位）与 TS-004（归位）的已有实现上，判定标准沿用 R9／R10 片 1 的读法。

**逐行读的代码**（三个被主会话变异的文件一律用 `git show HEAD:`）：`docker/lock-apps.sh` 全文（HEAD）；`docker/scripts/setup.sh` 第 115～320 行（HEAD，第 3、4 段与未声明仓库的循环）及本轮 diff（第 2 段）；`docker/up.sh` 第 35～47 行（HEAD）；`frappe_china/install.py` 第 1～160 行（HEAD）；`test_install.py:85-113` 的用例名与断言（grep）；`test_company_hr_lifecycle.py:170-180`（HEAD）。

**对照的上游**（只读）：frappe `installer.py:370-392`（`install_app` 末尾 `clear_cache`→`erase_persistent_caches`；`add_to_installed_apps` 先 `commit` 再 `update_versions`、再 `commit`）；`commands/utils.py:312-317`（`bench execute` 返回后才 `commit`）；`migrate.py:198`（migrate 会 `update_versions`）；`utils/boilerplate.py:204-210`（`bench new-app` 只 `git init`＋首次提交，不加 remote）；容器内 bench `app.py:194`（`get-app` 用 `--origin upstream` 克隆）；`docker/restore.sh:59`（恢复后跑 `migrate`）。

**只读查询**（两站）：`tabInstalled Application`（idx、app_name、modified）；`tabDefaultValue` 的 `installed_apps`（`__global`）；`System Settings.setup_complete`；`bench --site <站> list-apps`；`sites/<站>/site_config.json` 的 `installed_apps`。另核两仓 HEAD：`frappe_china` HEAD＝`origin/main`＝`052e4c3`，七个 app 的 HEAD 与 `apps.json` 锁定值逐一比对。

**实验**（目录 `D:\ERX-001\.claude\r11-tmp\p1\`，结束前已 `rm -rf`，确认不存在）：
1. 用 `git show HEAD:docker/lock-apps.sh` 取出脚本，造假 bench：已声明的 `frappe_china`（有 origin）＋未声明的三个——`frappe_debug`（无任何 remote，模拟 `bench new-app`）、`offapp`（只有 upstream）、`ownapp`（只有 origin）。跑写入，看输出与 `apps.json`。
2. 用 `setup.sh:141-153` 原样的 python 片段解析写出的 `apps.json`，再按 `setup.sh:156` 的 `IFS=$'\t' read -r` 读，宿主 bash 5.2.15（msys）与 frappe 容器内 bash 5.2.15（linux）各验一遍；接着按 `setup.sh:157-178` 的逻辑走一遍 `frappe_debug` 那一行；另用 `setup.sh:314` 的 awk 判它算不算「已声明」。
3. 给 `frappe_debug` 加 origin、给 `offapp` 也加一个 origin，先跑 `--show` 再跑写入，看已存在条目的 url 与 `official` 怎么变。
4. 把 `frappe_debug` 的 origin 去掉、url 改回 `""` 再跑，看已存在的空 url 条目会不会再警告；另造一个只有 `github` 这个 remote 的 `xapp`，看判据。

**跳过的及原因**：没跑测试、没做变异（硬约束，由主会话做）；没写任何站点；`setup.sh` 没在容器里真跑（会改真 bench 的 remote 并起站），第 3 段只在临时目录用同一段解析与读取逻辑模拟；`frappe_china` 本轮两处改动（`README.md`、`test_realtime_check.py`）归片 3／片 4 的依据，本片只确认它们没碰 `install.py`。

## R10 已修项复核

| R10 项 | 修于（当场／SB） | 定位（文件:行） | 落地 | 生效 | 原问题消失 | 说明 |
|---|---|---|---|---|---|---|
| FD-040 | 当场 #4 | `docker/lock-apps.sh:107-117`（HEAD） | ✅ | ✅ | ⚠️ 部分 | **判据对了**：实验 1 中，无 remote 的 `frappe_debug` 写成 `url: ""`、不带 `official`，并打「没有任何 remote，url 为空，须手工补上（否则重建时不会克隆它）」；只有 upstream 的 `offapp` 标 `official: true`；只有 origin 的 `ownapp` 不标。R10 列的后果①②已经消失：条目不是 official，`lock-apps.sh:84-85` 下次会重读 remote（实验 3：加上 origin 后再跑，url 更新为 origin、仍不带 official）；`setup.sh` 第 4 段也不会再把它当官方仓库删 origin。**但后果③的前提不成立，警告文案说错了后果**：`url` 为空时，`setup.sh:156` 的 `IFS=$'\t' read` 会把行首的空字段吞掉，整行左移（tab 是 IFS 空白字符，`setup.sh:139-140` 的注释写过这个坑，只给 commit 和 app_name 补了 `-` 占位，url 没有补），于是 `:157` 的 `[ -z "$app_url" ] && continue` 永远不会触发。实验 2 读出 `url=[main] ref=[<commit>] commit=[frappe_debug] name=[0]`，接着走到 `:173-177`，报「容器内访问不了 main，或分支/tag <commit> 不存在」并 `exit 1`，**整个 `up.sh` 中止**，而不是警告说的「不会克隆它」（见 P1-01）。`--show` 段与已声明条目的分支都不受影响（实验 1、3 中 `frappe_china` 的输出、`apps.json` 写回值都正常） |

FD-040 的后果③（「`url` 为空时第 3 段跳过它」）是 R10 片 1 原报告（本人前一轮）写的，没有实测，本轮实测推翻了它。修复照这个前提写了警告文案，「修后验证」也只跑了 `lock-apps.sh`，没有把写出的 `apps.json` 喂给 `setup.sh` 的解析。

## 延迟／不做项登记核对

| R10 项 | 裁决去向 | 登记位置 | 描述与实情一致否 | 说明 |
|---|---|---|---|---|
| FD-044 | 不做（只注明） | `docs/项目概况.md:68`（「演示站当前状态」括注）；R10 收口报告当场修 #8 | 一致 | 两站只读查询：演示站 `tabInstalled Application` idx 1～7 依次为 `frappe, erpnext, frappe_china, crm, hrms, insights, raven`（modified 均 `2026-10-07 00:43:29`），`list-apps` 同序，`frappe_china` 第 3，与注明相符；`__global installed_apps` 与 `site_config.json` 都是目标顺序，「`check_app_order` 为真」也成立。测试站子表是目标顺序（16:09:03 重写）。「下次 migrate 或 `restore.sh` 自愈」：`migrate.py:198` 调 `update_versions()`、`restore.sh:59` 跑 `migrate`，说法成立。两站 `setup_complete` 均为 1 |
| FD-047 | 延迟 → SH-P1S5011 | Stage 概况登记册 `P1-S5-概况.md:127` | 一致（日期一处待核） | 逐句对代码：`install.py:140-149` 依次是 `update_installed_apps_order`、`update_site_config`、`update_versions`、`clear_cache`、`erase_persistent_caches`，函数内无 commit；`bench execute` 返回后才 `commit`（`commands/utils.py:316-317`）；上游 `add_to_installed_apps` 先 `commit`（`installer.py:383`），广播在 `install_app` 末尾（`:374-375`），说「上游先提交再广播」成立。「`test_install` 的 `changed` 分支用例」即 `test_install.py:85` `test_reorder_installed_apps_rewrites_order_mirror_and_caches`，它断言 `erase.assert_called_once_with()`（`:111`），改挂 `after_commit` 后确须改断言，说法成立。唯一不符：「登记日期」写 `2026-10-07`，而裁决与登记都发生在 2026-10-08（R10 收口报告第 182、195 行），见 P1-02 |
| FD-048 | 不做（下次改到时顺手修） | R10 收口报告第 174、202 行；Stage 概况 R10 行 | 一致 | 留档在；代码未变：`install.py:79` 仍是 `list(TAIL_APPS[1:])`，`TAIL_APPS` 首项仍是 `frappe_china`（`:6`），现文案正确 |
| FD-052 | 不做（下次改到时顺手统一） | R10 收口报告第 178、202 行；Stage 概况 R10 行 | 一致 | 留档在；`test_company_hr_lifecycle.py:176` 仍是 `c.args[:1] == (EXPENSE_CLAIM_ACCOUNT,)`，本轮未改 |

**版本锁定**：`docker/apps.json`（HEAD）的 `frappe_china.commit` 为 `052e4c3751a715df7ef0a8a7481e0df0da2a60ed`，等于 `frappe_china` 的 HEAD 与 `origin/main`，工作区干净。与 `d7b89d6` 版逐条逐键比对：7 条、顺序不变，差异只有这一键；其余六个 app 的锁定值都等于各自仓库的 HEAD，`official` 标记（crm、hrms、insights、raven）不变。✅

## 业务规则合规核

| 规则条款 | 本轮改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 执行《小企业会计准则》 | 不涉及（本片改动只有锁定脚本、文档注明与登记） | 合规 | — |
| BR-002 三张报表 | 不涉及 | 合规 | — |
| BR-003 增值税税率 | 不涉及 | 合规 | — |
| BR-004 增值税月末转出 | 不涉及 | 合规 | — |
| BR-005 附加税 | 不涉及 | 合规 | — |
| BR-006 资产负债表平衡 | 不涉及 | 合规 | — |
| BR-007 价税分离 | 不涉及 | 合规 | — |

## 集成点登记（交接摘要）

- **本片依赖**：
  - 片 4（R3 Part4 归属 `setup.sh`／`up.sh`）：P1-01 的后果落在 `setup.sh` 第 3 段的解析与读取（`:141-178`），修法可能要改 `setup.sh`。本片只读 HEAD、在临时目录模拟，没在容器里真跑。本轮 `setup.sh` 只改了第 2 段（`SOCKETIO_PORT`），第 3、4 段字节未变，所以 P1-01 不是本轮 `setup.sh` 改动带出来的。
  - 主会话：P1-01 若要实证 `up.sh` 中止，须在可丢弃环境里真跑一次（见「需主会话补跑」）。
- **本片暴露**：
  - `lock-apps.sh` 现在会往 `apps.json` 写 `url: ""` 的非 official 条目（新 app 无 remote 时）；之后再跑，若仍无 remote 则**静默**保留空 url，不再警告（实验 4：第二次运行只打一行常规输出）。`setup.sh` 第 3 段对这种条目会中止，而不是跳过（P1-01）。
  - `--show` 与已声明条目的写回逻辑不变；已存在的非 official 条目，加了 origin 后再跑会更新 url（实验 3）。官方条目的 url 不重读（`lock-apps.sh:82-83`），本轮未变。
  - remote 名不是 `origin`／`upstream`（如 `gh` 以外的工具起名 `github`）时同样按「无任何 remote」处理（实验 4 的 `xapp`），后果同 P1-01。

## 自证复核

| 被审产物声称（R10 报告／代码注释／文档） | 实际复核 | 一致否 |
|---|---|---|
| 当场修 #4：「无 origin 且有 upstream」才标 `official`；一个 remote 都没有时不标，警告 url 为空须手工补 | `lock-apps.sh:113-117` 照此实现，实验 1 输出与写出值相符 | ✅ |
| `lock-apps.sh:117` 警告：「否则重建时不会克隆它」 | 实验 2：`setup.sh` 读取时整行左移，第 3 段 `exit 1`，`up.sh` 中止 | ❌ P1-01 |
| R10 FD-040 问题描述后果③：「`url` 为空时第 3 段跳过它」 | 同上，跳过分支 `setup.sh:157` 对空 url 不可达 | ❌ P1-01（前一轮本片读码误判） |
| 修后验证 FD-040：三个假仓库跑 `lock-apps.sh`，三种结果 | 本片重做得同样三种结果；但修后验证没有覆盖 `setup.sh` 对写出值的消费 | ⚠️ 覆盖面窄 |
| 当场修 #8／项目概况：演示站子表仍是安装顺序、`frappe_china` 列第 3，下次 migrate／restore 自愈 | 两站查询与上游代码都相符 | ✅ |
| 当场修 #10：SH-P1S5011 已登记 | 在，描述与代码一致；登记日期写 10-07 | ⚠️ P1-02 |
| 当场修 #14：`apps.json` 只改 frappe_china commit，其余条目无差异 | 逐键比对属实 | ✅ |
| R10「FD-048、FD-052 不做，下次改到时顺手修」 | 留档在，代码未动 | ✅ |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准／意图 | 建议 | 建议档位 | 待裁决点 | 状态 |
|---|---|---|---|---|---|---|---|---|
| P1-01 | 低（低／中边界） | `docker/lock-apps.sh:109,116-117`（HEAD）；后果在 `docker/scripts/setup.sh:139-160、173-177`（HEAD） | FD-040 修好后，无 remote 的新 app（`bench new-app` 建的 `frappe_debug` 正是这样）会以 `url: ""` 写进 `apps.json`。警告说「否则重建时不会克隆它」，实际是**下次 `up.sh` 在第 3 段中止**：`setup.sh:141-153` 把空 url 原样输出成行首空字段，`:156` 的 `IFS=$'\t' read -r` 把它吞掉、整行左移（宿主与容器 bash 5.2.15 实测都是 `url=[main] ref=[<commit>] commit=[frappe_debug] name=[0]`），`:157` 的空 url 跳过不会触发，`apps/0` 不存在，于是去 `ls-remote main`，报「容器内访问不了 main，或分支/tag <commit> 不存在」并 `exit 1`，报错还指向私有仓库凭据，很误导。`setup.sh:139-140` 的注释写过同一个 IFS 坑，只给 commit 与 app_name 补了 `-` 占位。另外，条目一旦写进去，之后再跑 `lock-apps.sh` 若仍无 remote，空 url 会**静默**保留、不再警告（实验 4）；`setup.sh:314` 的 awk 不吞空字段，会把它算作「已声明」。这个问题不是 R10 引入的（R10 前同样写 `url: ""`，只多了 `official`），但 R10 的修复照错误前提写了警告文案 | FD-040 的判定标准（「url 为空，须手工补」须如实说明后果）；开发守则「不静默」；`setup.sh:139-140` 自己定下的「空字段写 `-`」约定 | (a) 新 app 无 remote 时**不写入**条目，只警告「{app} 没有任何 remote，未写进 apps.json；先加 origin 并推送，再跑一次」——没 url 的条目本来也重建不出来，同时在 `setup.sh` 的解析里把空 url 也输出成 `-`、读到 `-` 时警告并 `continue`，兜住手工写空的情形；(b) 只改 `setup.sh` 的解析（空 url → `-` → 跳过并警告），`lock-apps.sh` 照旧写空 url，警告文案改成与之相符；(c) 只改 `lock-apps.sh` 的警告文案为「url 为空时 up.sh 会在第 3 段中止，须先补 url」。**建议 (a)** | 本Session修 | 取 (a)／(b)／(c)；(a)、(b) 要改 `setup.sh`，属片 4 的依据范围 | 待裁决 |
| P1-02 | 观察 | `docs/01-需求摸底/S05-演示链路/P1-S5-概况.md:127`（SH-P1S5011「登记日期」列） | SH-P1S5011 的登记日期写 `2026-10-07`。FD-047 是 R10 发现的，用户裁决原话与当场修清单都记在 2026-10-08（R10 收口报告第 173、182、195 行），登记也是那天做的 | 登记册「登记日期」列的含义 | 改为 `2026-10-08` | 本Session修 | — | 待裁决 |

## 本片盲区自述

- 没跑测试、没做变异。FD-040 是 shell 脚本，没有自动测试守着，本片的结论全部来自临时目录实验。
- P1-01 的「`up.sh` 中止」是用 `setup.sh` 第 3 段的同一段解析代码、同一种 `read` 在临时目录与容器 bash 里模拟出来的，没在容器里真跑 `setup.sh`（会改真 bench 的 remote、起站）。`ls-remote main` 那一步在宿主跑，没走容器网络；即使网络不同，它对「main」这个非 URL 的结果也只会是失败。
- `lock-apps.sh` 的判据靠 remote 名（`origin`／`upstream`）。用 `bench get-app` 克隆的**自有** fork 也只有 upstream，会被标成 official——这是 R9 FD-010 定下的取舍，有「请确认」警告，本片没再立项。
- 本片没有复核 R10 其余当场修项（FD-037～039、041～043、045、049～051），它们归片 3／4／5。`frappe_china` 本轮两处改动只确认不碰 `install.py`。
- SH-P1S5011 的技术判断（窗口内旧顺序被重新缓存）沿用 R10 片 1 的读码推断，本轮没有复现。

## 需主会话补跑的实测

1. **P1-01 实证（可选）**：在可丢弃的 bench 副本或临时目录，往 `apps.json` 末尾加一条 `{"url": "", "branch": "main", "commit": "<任一 sha>", "app_name": "frappe_debug"}`，只跑 `setup.sh` 第 3 段的解析与循环。预期报「容器内访问不了 main」并以 1 退出。不要在主 bench 上跑完整 `up.sh`。
2. **跨片确认（片 4）**：P1-01 若取 (a)／(b)，改动落在 `setup.sh:141-160`，请片 4 确认与第 2 段（`SOCKETIO_PORT`）及 `up.sh` 传参无交叉。
