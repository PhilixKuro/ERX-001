# SB修复回执（对象：代码 / 依据：P1-S4-R18-F审核报告 ＋ P1-S4-R7 开发方案 Part3、Part4）

**轮次**：P1-S4-R18｜**日期**：2026-10-03｜**步骤**：`plannedDev` SB（build）｜**执行者**：Claude（Opus 5.5）｜`打tag=否`
**Round 归属**：`附属=新Session做`（步骤表 SB 行原值）——只做 R18 F 报告裁为 `新Session修` 的 3 项（FD-081、082、085），**不占 Round**，沿用 R18。
**依据**：[F审核报告](P1-S4-R18-F审核报告.md) FD-081／082／085（原条目 [Part4](P1-S4-R18-F审核报告-Part4.md) P4-02／P4-03、[Part3](P1-S4-R18-F审核报告-Part3.md) P3-02）＋[开发方案 Part3](../R07-开发方案/P1-S4-R7-C开发方案-Part3.md) SL-006 ⑩（BR-006）＋R17 FD-045 的意图（锁不上就响亮失败）
**用户裁决**（2026-10-03，见 F 报告「用户裁决」）：「其它的按建议来」——三项取建议档位 `新Session修`；FD-081 的待裁决点「有未提交改动时继续警告还是中止」交 SB 按建议定。
**范围外不动**：`本Session修` 5 项（F 步已修）、延迟 12 项（`SH-P1S4037`～`048`）。

## 逐项执行结果

| 任务 | 报告项号 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| 容器内 git 与宿主换行判断对齐 | FD-081 | `docker/up.sh:29-34`（读宿主 `core.autocrlf`，经 `-e HOST_GIT_AUTOCRLF` 传进容器）；`docker/scripts/setup.sh:166-172`（第 3 段循环内、锁定判断之前写仓库级 `core.autocrlf`） | ✅完成 | 10-04 | **两处偏离报告字面建议，均为达成同一意图**：① 报告写「第 4 段写」，但第 4 段在第 3 段之后跑，**新机器上**锁定判断那一刻仍没有该设置，故挪到第 3 段循环内、判断之前；② 报告写「写 `true`」（「宿主本来就是 true」），改为**照抄宿主的值**——硬写 true 会让 Linux 宿主的工作区检出成 CRLF（容器与宿主共用同一份工作区），宿主没设则不写。待裁决点「有改动时继续警告还是中止」按建议**保持警告**：此时中止会挡住真有本地改动的人重跑 `up.sh`，而换行假改动消除后这条分支只在真有改动时走到 |
| `apps.json` 解析失败时中止 | FD-082 | `docker/scripts/setup.sh:126-136`（`app_entries=$(python …) \|\| exit 1`）、`:202`（`done <<<"$app_entries"`） | ✅完成 | 10-04 | 取报告建议原样。原 R17 FD-049 那段关于「-」占位的注释随 python 一起上移，未改字 |
| 资产负债表年初列不平也标红 | FD-085 | `frappe_china/accounting/statements/balance_sheet.py:92-104`（`_render_notes_html` 加 `opening_difference`）、`:133-152`（年初差额、summary）；`translations/zh.csv` 末行 `Opening Difference,年初差额`；`tests/test_balance_sheet.py` 新增 `test_opening_imbalance_is_reported_in_red` | ✅完成 | 10-04 | 取报告建议：年初差额与期末差额并列计算，任一列不平即红块、前两项 summary 标红；年初不平时 summary 追加第四项「年初差额」（报告待裁决点提到的「可加第四项」）。平时仍是方案 SL-006 的三项，第三项「差额」仍只看期末。新源词按总纲 A9 走 `_()`＋csv（官方 po 无 `Opening Difference`） |
| 全量回归 | — | `bench --site test.localhost run-tests --app frappe_china`（日志 `frappe-bench/logs/r18-sb-full.log`） | ✅完成 | 10-04 | 157/157，见「全量验证」 |

## 复验结果

| 报告项号 | 报告的判定标准 | 怎么复验的 | 实测结果 |
|---|---|---|---|
| FD-081 | 本机容器里锁定值 ≠ HEAD 时真的 reset 到锁定值，不再走「有未提交改动，跳过」（R18 Part4 实跑清单第 3 条：「加上仓库级 `core.autocrlf true` 再跑一次，确认真的 reset」） | 容器内把 `frappe_china` 拷到 `/tmp` 临时目录，按宿主视角（`autocrlf=true`）把工作区检出成 CRLF；`apps.json` 锁到 `HEAD~1`（`cd5d565`）；**原样执行第 3 段**（从 `setup.sh` 截取，`BENCH_DIR` 指真 bench 只为取 python，`cd` 到临时目录）。改前、改后各一次；改后另以 `HOST_GIT_AUTOCRLF` 为空（模拟 Linux 宿主）跑一次 | ✅ **改前**：「有未提交改动，跳过 checkout 到 cd5d565」，exit 0，HEAD 仍 `49e76c4`（症状复现）。**改后**：「对齐到锁定的 cd5d565…已对齐（仍在 main 分支）」，exit 0，HEAD＝`cd5d565`、`main`、仓库级 `autocrlf=true`、`status` 0 行。**宿主未设**：不写配置、行为同改前（Linux 宿主本无 CRLF 工作区，不受影响）。本机容器现状：`frappe_china` 27 行、`erpnext` 2 行假改动，加 `-c core.autocrlf=true` 后均 0 |
| FD-082 | `apps.json` 写坏（截断、某条缺 `url`）时第 3 段不再静默跳过／截断，外层退出码非 0（Part4 实跑清单第 1 条 E） | 同上的临时目录，喂两份坏 `apps.json`：① 截断（少一个 `]`）；② 第二条缺 `url`。改前、改后各一次 | ✅ **改前**：两种都打出 python 回溯后继续往下跑，**exit 0**（② 还先处理了第一条，即截断）。**改后**：两种都打出 python 回溯＋「错误：解析 … 失败（见上方 python 报错）：JSON 语法错，或某条缺 url？」，**exit 1**，且一个 app 都没动（缺 `url` 那份第一条也不处理——先整份解析再进循环） |
| FD-085 | 年初一列不平时与期末不平同样醒目：红块、summary 标红（报告建议；BR-006「不等时明确报出」；R14 Part3「期末与年初两列都校验；不等时出红色说明并标红」） | 新用例 `test_opening_imbalance_is_reported_in_red`：2025-01-01 开账凭证 `1002` 借 1000／`9999` 贷 1000（`is_opening=Yes`），1 月 20 日 `9999` 转入 `3001`——年初资产多 1000、期末平衡，即报告所述可达情形。经 `query_report.run` 出 1 月表。**变异**：把 `balance_sheet.py` 换回 `HEAD` 版本跑同一模块，再拷回（SHA-256 前后一致 `7434fb89…`） | ✅ **改后**：说明块 `text-danger`，首条「年初余额：资产总计与负债和所有者权益总计不等，差额 1000.00」，不出期末那条；summary 四项 `Red／Red／Green／Red`，第三项「差额」仍为期末 0，第四项「年初差额」1000。**改前（变异）**：该用例失败——说明块是 `text-muted`，只有一行「年初余额：勾稽不符：第 53 行为 0.00，按第 30 行计算应为 1000.00」，即报告所述症状；其余 6 条照过 |

## 全量验证

| 门 | 结果 |
|---|---|
| 执行前基线 | R18 F 步当场修后 156/156 |
| `run-tests --app frappe_china` | **Ran 157 tests in 538.604s, OK**，EXIT=0；156 → 157（新增 FD-085 一条）。FD-081／082 是环境脚本，无 Python 测试面，判别力靠上面的改前／改后对照 |
| `test_translations` | 含在全量内通过：新源词 `Opening Difference` 有 csv 译文、不与官方 po 重键、不撞法定行名 |
| `bash -n` | `up.sh`、`setup.sh` 均通过；两文件仍为 LF（`.gitattributes` `*.sh eol=lf`） |
| 跑后测试站 | Company／Account／GL Entry 均 0（测试事务回滚，未用备份恢复） |
| 临时文件 | 主仓库 `.claude/r18sb/`（第 3 段截取、实验脚本、三份 `apps.json`）与容器 `/tmp/r18sb` 已删 |
| 版本控制（用户许可「提交并推送」） | `frappe_china` 提交 `6cb779c` 已推送（本地＝`origin/main`）；`docker/apps.json` 用 `lock-apps.sh` 锁到 `6cb779c`，随主仓库提交推送 |
| 改动面 | 主仓库 `git diff --stat`：`docker/scripts/setup.sh` 29（+21／-8）、`docker/up.sh` +5；`frappe_china`：`balance_sheet.py`、`test_balance_sheet.py`、`zh.csv` 3 files，+45／-12 |

## 偏离与暂停

- **无暂停项**：三项的报告建议与方案（R7 Part3 SL-006 ⑩、R17 FD-045 的意图）都不冲突。
- **FD-081 两处偏离报告字面**（位置挪到第 3 段、值照抄宿主而非写死 true），理由见逐项表；判定标准未降低，复验按报告给的「确认真的 reset」做。
- **演示站未动**：`balance_sheet.py` 改动随同一份 bench 代码即时生效，无元数据改动、无需 migrate。`zh.csv` 新增一条译文，演示站要等下次 `clear-cache`（或重启）才显示「年初差额」，在此之前那一项只在年初不平时出现、显示英文源词；本步未对演示站执行 `clear-cache`。

## 新增约定

| 约定 | 类别（命名/位置/错误处理/依赖/跨层调用） | 在哪个任务确立 |
|---|---|---|
| `setup.sh` 里凡用子进程产出数据喂给 `while read` 循环的，先用命令替换存进变量并 `\|\| exit 1`，再 `<<<` 喂循环，不用 `< <(…)` 进程替换（后者的失败不受 `set -e` 约束） | 错误处理 | FD-082 |
| 容器里要与宿主一致的 git 行为设置（`core.autocrlf`），由 `up.sh` 从宿主读出、经环境变量传进容器照抄，不在容器里写死值 | 跨层调用 | FD-081 |

（是否移交 `开发守则.md` 由收尾时定，本步不改常驻文件。）

## 未做项

无。

## 状态值

**`修复已落地`**——裁为 `新Session修` 的 3 项（FD-081、082、085）全部改完，各按报告的判定标准复验通过，且改前对照都复现了报告所述症状；全量回归 157/157。按出口路由「SB · `修复已落地` → 回唤起方（F）复核」。

## 复核建议

1. **修得最勉强的那项**：FD-081。它解决的是「容器里 git 的换行视角与宿主不一致」这一根因，但做法是**把宿主的一项全局设置复制进各 app 的仓库级配置**——宿主日后改了 `core.autocrlf`，要重跑 `up.sh` 才同步。查法：`docker/up.sh:29-34` 与 `docker/scripts/setup.sh:166-172` 对照报告 FD-081 与 Part4 P4-02 读；另看位置为何不在第 4 段（新机器上第 4 段晚于锁定判断）。
2. **修复引入的连带影响**：
   - FD-081 写的仓库级 `core.autocrlf` 也会被**宿主 git** 读到（同一个 `.git/config`）。宿主值本来就是这个，故宿主行为不变；但从此「宿主改全局设置」对这三个 app 不再生效。
   - 本机 `frappe`／`erpnext`／`frappe_china` 三个仓库下次跑 `up.sh` 时都会被写入该项；本步实验只在 `/tmp` 的拷贝上做，**本机三个真实仓库的配置未改**。
   - FD-085 让 `report_summary` 在年初不平时变成 4 项；`printing.py` 只取 `execute` 的前三个返回值、不读 summary，PDF 不受影响。S7 演示脚本或日后自检若按「summary 恰好 3 项」判断会受影响（现无此类代码，已 grep）。
3. **拿不准处**：
   - FD-085 的「年初差额」第四项是报告待裁决点里「可加第四项」的那种读法；若只要标红、不要第四项，删 `balance_sheet.py:144-145` 与 csv 末行、改测试断言即可。
   - `setup.sh` 全文仍没真跑过（与 R18 F「查得最浅」那条相同）：第 3 段是截取后原样执行，第 4 段以后未跑。

