# 审核报告·Part4a（对象：主仓库 `5ade13c..3a7854c -- docker/scripts/setup.sh docker/up.sh` / 审核标准：R18 F 报告 FD-080、081、082 的建议与判定标准 ＋ R14 FD-009「重跑 `up.sh` 不失败」＋ R17 FD-045「锁不上就响亮失败」＋ 开发守则「静默失败」「版本锁定」）

**轮次**：P1-S4-R19｜**日期**：2026-10-04｜**步骤**：`plannedDev` F（audit，复核轮），第 4 片 4a 子片｜**执行者**：Claude 子 Agent（Opus 5.5，只读）
**依据**：[R18 收口](../R18-审核报告/P1-S4-R18-F审核报告.md) FD-080／081／082 三行与「当场修清单」#1、[R18 SB 回执](../R18-审核报告/P1-S4-R18-SB修复回执.md)（全读）、[R18 Part4](../R18-审核报告/P1-S4-R18-F审核报告-Part4.md) P4-01～03、[Stage 概况](../P1-S4-概况.md) `SH-P1S4040`～`048`
**方法与边界**：只读。没跑 `up.sh`／`setup.sh`／`bench build`，没有网络 clone，没写站点，没改三个真实 app 仓库的状态与 `.git/config`。宿主 `mktemp -d` 临时目录里做了纯 bash／git 小实验（实验用 `GIT_CONFIG_NOSYSTEM=1 GIT_CONFIG_GLOBAL=/dev/null` 模拟容器内无全局设置），做完已删。容器内只跑了 `git status --porcelain`／`git config --get`（加 `GIT_OPTIONAL_LOCKS=0`）。

## 覆盖自证

**读全的**：
- 改动：`git diff 5ade13c..3a7854c -- docker` 全部（`setup.sh` +21／-8 两处、`up.sh` +5、`apps.json` 1 行）。
- `docker/scripts/setup.sh` 全文（374 行）、`docker/up.sh` 全文、`docker/lock-apps.sh` 全文；`shell.sh`、`start.sh`、`restore.sh`、`backup.sh` 用 grep 查了 `git`／`status`／`< <(`／`read`。
- 上游：`frappe/esbuild/esbuild.js:195-335、380-470`（入口收集、输出目录规则、`assets.json` 写入）、`build-cleanup.js`；`frappe/build.py:222-244`（`bench build` → `yarn run build` → `node esbuild`）。
- `docker/README.md:121`、`:212`，`docs/开发守则.md:164`（换行相关）；主仓库 `.gitattributes`、`frappe_china/.gitattributes`。

**做过的实验与只读查询**：
1. find 的 prune 与 `//`：`apps/x//x/public` 下放 `dist/css/a.bundle.css`、`node_modules/p/n.bundle.js`、`sub/dist/s.bundle.scss`，按 `assets_missing` 原样的 find 跑。
2. `assets_missing` 原函数（从 `setup.sh` 截取后 `eval`）对真实 bench 三个 app 的判定；frappe／erpnext 各类 `*.bundle.*` 源文件计数与 `dist/css`、`dist/js` 文件数。
3. `set -euo pipefail` 下 `find | grep -q .` 的 SIGPIPE：30／60／120／3000 个 bundle 各跑多次。
4. 换行：LF 工作区写 `autocrlf=true` 后 status、`touch` 后 status、`reset --hard` 后写出的字节；CRLF 工作区在 unset／false／input／true 四值下的 status。
5. 第 3 段锁定逻辑在「工作区干净、HEAD 比锁定值新」时的行为（`autocrlf=true` 下）。
6. FD-082：`app_entries=$(python …) || {…; exit 1;}` 喂 `[]`、正常两条、第二条缺 `url` 三种 JSON。
7. 宿主 `git config --show-origin --get-all core.autocrlf`（在 `docker/` 下）、主仓库 `--local`；三个 app 的仓库级 `core.autocrlf`／`core.fileMode`、是否浅克隆、HEAD 与 `apps.json` 对照。
8. 容器内只读：三个 app 的 `status --porcelain` 行数（默认／`-c core.autocrlf=false`／`-c core.fileMode=true`）。
9. `bash -n` 两个脚本。

**跳过及原因**：
- 没真跑第 9 段 `bench build` 分支、没在容器里跑第 3 段（硬约束；R18 当场修清单与 SB 回执各有一次截取后原样执行，主会话另有一次真跑 `up.sh` exit 0）。
- `.bundle.jsx`／`.tsx`／`.vue`／`.styl` 的推断来自读 `esbuild.js`，没真建这类 bundle 跑 esbuild。fast-glob 不收隐藏目录（默认 `dot:false`）是按库的默认值判断，没实测。
- 主会话已报的第 6 段 `list-apps | grep -qx` 永不匹配一条，按指示不再报。
- FD-085（`balance_sheet.py`）不属本子片。

## 已修项复核表

三层：落地（代码在）→ 生效（真被调用、没被绕过）→ 原问题消失。

| R18 项 | 定位（文件:行） | 落地 | 生效 | 原问题消失 | 说明 |
|---|---|---|---|---|---|
| **FD-080** 第 9 段误要求 `frappe_china` 有 `dist/css` | `setup.sh:325-339`（`assets_missing`）、`:342-346`（预检）、`:351-357`（build 后复检） | ✅ | ✅ | ✅（现有三个 app）／⚠ 边角见 P4a-02、P4a-03 | **prune 能匹配**：GNU find 4.9 输出路径原样保留起点字符串（`apps/x//x/public/dist/...`），`-path "$pub/dist"` 用的是同一个 `$pub`，实验中顶层 `dist` 与 `node_modules` 都被剪掉，`sub/dist` 下的 bundle 仍被计入——与 esbuild 只忽略 `public/dist`、`public/node_modules` 两个顶层目录一致（`esbuild.js:258-263`）。**css／js 归类**：esbuild 按入口扩展名分流，`.css/.scss/.less/.sass/.styl` → `<app>/dist/css/`，`.js/.ts` → `<app>/dist/js/`（`:214-219`），与两类判据一致；js 里 import 的 css 由 esbuild 输出在同一 `dist/js/` 下，不影响 css 判据（该判据只在有样式 bundle 时才查）。**frappe／erpnext 仍被查到**：frappe 28 个 `.bundle.js`＋8 个 `.bundle.scss`（`dist/css` 16、`dist/js` 56），erpnext 5＋3（6、10），两类都会查；`frappe_china` 无 bundle 源，两类都 `continue`，`return 1`。原函数对真实 bench：三者均「不缺」。主会话真跑第 9 段输出「前端资源齐备」 |
| **FD-081** 容器内 git 把 CRLF 当改动、锁定被绕过 | `up.sh:32-34`；`setup.sh:166-172`（写入），`:179`（status 判断） | ✅ | ✅ | ✅ | **读到的值**：`docker/` 在主仓库内，`git config --get` 会读 system＋global＋主仓库 local；现主仓库 local 无此项（`--local` rc=1），取到的是 `C:/Program Files/Git/etc/gitconfig` 的 `true`（潜在偏差见 P4a-04）。**时机**：写入在 `:170`，`status` 判断在 `:179`，同一循环轮次内先写后判，新机器 get-app 后也成立。**各值效果**（实验，CRLF 工作区）：unset／false → 2 行假改动，input／true → 0 行；宿主为 input 时工作区本就是 LF，写 input 无副作用。**新机器**：容器 get-app 出的 LF 工作区写 `true` 后 status 0，`touch` 后仍 0；之后 `reset --hard` 会把变动文件写成 CRLF（与宿主 checkout 行为一致，status 仍 0），三个 app 里被跟踪的 `.sh` 只有 frappe／erpnext 的 `.github/helper/*`（CI 用，容器不执行），`frappe_china` 无 `.sh`。**现状**：三个仓库仓库级 `autocrlf=true`、`fileMode=false`，容器内 status 默认 0 行（另以 `-c core.autocrlf=false` 查也是 0——主会话跑 `up.sh` 后 index 的 stat 信息已刷新）。**其它脚本**：`lock-apps.sh:25` 的 `status` 在宿主执行，不受影响；`shell.sh`／`start.sh`／`restore.sh`／`backup.sh` 不调用 git。**连带**：原先这台机器靠 CRLF 假改动「意外」挡住了锁定步往回退，修好后这道挡板没了，见 P4a-01 |
| **FD-082** `apps.json` 写坏时第 3 段静默跳过 | `setup.sh:131-136`、`:202` | ✅ | ✅ | ✅ | `var=$(cmd) \|\| {…}`：赋值语句的退出码即命令替换里最后一个命令（python）的退出码，`\|\|` 接住后 `exit 1`；`set -e` 对 `\|\|` 左侧不生效，不会抢先退出、也不会漏掉。实验：第二条缺 `url` → 打印「parse fail」并 `exit 1`，一条都不处理；正常两条 → 两行，字段正确（空字段为 `-`）。**空数组 `[]`**：`app_entries` 为空，`<<<""` 喂一行空串，`[ -z "$app_url" ] && continue` 跳过，0 行、整段退出码 0——与改前行为相同，且空清单是合法配置（frappe 由第 1 段装），不另立条目。**同类问题**：`docker/*.sh`、`docker/scripts/*.sh` 里 `< <(` 只剩 `setup.sh:127` 注释，无 `\| while`；其余 `read -r` 只在 `down.sh:11`、`restore.sh:45` 读终端确认 |

**方案外夹带**：`apps.json` 把 `frappe_china` 锁定值 `cd5d565` → `6cb779c`，是 SB 回执「版本控制」行写明的 FD-085 提交后重锁，`6cb779c` ＝ 宿主 `frappe_china` HEAD。除此之外 docker 改动只有上述三项，无夹带。`bash -n` 两脚本通过。

## 开放查漏新发现表

| 编号 | 严重程度 | 定位 | 问题 | 违背的标准 | 建议修法 | 建议档位 | 待裁决点 | 证据 |
|---|---|---|---|---|---|---|---|---|
| P4a-01 | 中 | `setup.sh:175-199`（锁定步）；`docker/README.md:121`；概况 `SH-P1S4045`～`047` | **FD-081 修好后，本机重跑 `up.sh` 会把「已提交、比锁定值新」的分支静默退回锁定值**。改前，本机容器把 CRLF 文件都看成改动，锁定值 ≠ HEAD 时总走「有未提交改动，跳过」，R18 Part4 P4-02 写明「本机暂时碰不到往回退」。现在 status 干净，于是只要 HEAD ≠ 锁定值就 `reset --hard` 到锁定值——常见情形是在 `frappe_china` 里 commit 了、还没跑 `lock-apps.sh` 就重跑 `up.sh`。分支指针被拨回，没推送的提交只剩 reflog 可找；输出只有一行「对齐到锁定的 …」，不提示丢了哪些提交。README 写的「有未提交改动时跳过，不会丢代码」不覆盖这种情形。**登记册**：`SH-P1S4045`（不往回退的保护）、`046`、`047` 的唤醒条件都是「下次改 `setup.sh` 第 3 段时」，本轮 FD-081、FD-082 都改了第 3 段，条件已满足，但 SB 回执把 037～048 列为「范围外不动」，没唤醒 | R17 P4-02 ②／R18 FD-094 的意图；开发守则「版本锁定」；登记册唤醒条件 | reset 前加 `git merge-base --is-ancestor "$app_commit" HEAD`：锁定值是 HEAD 的祖先（HEAD 更新）时不 reset，打警告「HEAD 比 apps.json 新，先跑 `docker/lock-apps.sh`」，或 `exit 1`；README:121 补这条。随之处理 `SH-P1S4046`／`047` | 新Session修 | ① HEAD 更新时：警告跳过，还是中止；② 是否把已唤醒的 `SH-P1S4046`／`047` 一并修 | 宿主实验：`autocrlf=true`、工作区干净、HEAD＝本地新提交、锁定值＝其父提交 → 走到 `reset --hard`，之后 `main` 不再包含该提交（`branch --contains` 0）；同一 CRLF 工作区去掉 `autocrlf` 时 status 1 行 → 改前会跳过。本机现状三个 app HEAD 均＝锁定值（主会话 `up.sh` 输出「已在锁定的 commit」），未发生实际回退 |
| P4a-02 | 观察 | `setup.sh:330`、`:333`；`esbuild.js:214-219、258` | **`assets_missing` 的扩展名集合与 esbuild 不完全一致**：① 脚本类收 `.bundle.tsx`、`.bundle.vue`，esbuild 的入口 glob 是 `{js,ts,css,sass,scss,less,styl,jsx}`，不收这两种 → 只有这类文件的 app 永远不会有 `dist/js`，第 9 段必 `exit 1`；② `.bundle.jsx` 被 esbuild 收进来，但只有 `.js`／`.ts` 加 `js/` 前缀，jsx 的产物落在 `<app>/dist/` 根下 → 只有 jsx bundle 的 app 被误判缺 `dist/js` 而中止；③ 样式类漏 `.bundle.styl`（漏判，不会中止）；④ find 会计入隐藏目录里的文件，fast-glob 默认不收。现有三个 app 只有 `.bundle.js`／`.bundle.scss`，均不受影响 | R18 FD-080 建议「判据与 esbuild 的收集规则一致」 | 两类扩展名改成与 `esbuild.js:258` 相同：样式 `css,sass,scss,less,styl`、脚本 `js,ts,jsx`；jsx 的去向若要严格，脚本类改查 `dist` 下有无 `*.js` | 延迟或不修 | 唤醒条件取「`frappe_china` 首次加前端 bundle 时」是否合适 | 读码：`esbuild.js:258` include glob；`:214-219` 只给 `.js/.ts` 加 `js/`；真实 bench 计数：frappe 28 js＋8 scss，erpnext 5＋3，`frappe_china` 0 |
| P4a-03 | 观察 | `setup.sh:329-330`、`:332-333`（`find … \| grep -q .`，`set -o pipefail`） | **输出很多时 find 吃 SIGPIPE，整条管道退出码 141，被 `\|\| continue` 当成「没有 bundle」而跳过检查**。方向是漏判（不中止），只在 find 输出超过管道缓冲时出现；现有 frappe 输出约 1.6 KB | 开发守则「静默失败」 | 改用 `find … -print -quit \| grep -q .`，或 `[ -n "$(find … -print -quit)" ]` | 延迟或不修（可随 P4a-02 一起改） | — | 实验：3000 个 bundle（约 260 KB 输出）→ 3／3 次未报缺失，`PIPESTATUS=141 0`；30／60／120 个（2～8.5 KB）各 5 次均正确 |
| P4a-04 | 观察 | `up.sh:12`、`:32` | **读到的不是纯宿主全局值**：`up.sh` 先 `cd docker/`，`git config --get` 会把主仓库 `.git/config` 的 local 设置也算进来；主仓库日后若单独设了 `core.autocrlf`，这个值会被照抄进三个 app。另外在 WSL 里跑 `up.sh` 时读到的是 WSL 的 git 配置（通常未设），不写入，CRLF 假改动会回来 | FD-081 意图「与宿主（检出 app 工作区的那个 git）一致」 | `(cd / && git config --get core.autocrlf)` 只读 system＋global；WSL 情形在 README 注一句即可 | 延迟或不修 | — | 宿主 `--show-origin`：唯一来源 `C:/Program Files/Git/etc/gitconfig true`；主仓库 `--local` rc=1。WSL 情形为推断，未实测 |

## 业务规则合规核

| 规则条款 | 本 Round 改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| — | 否 | — | 本子片只涉及 `docker/` 环境脚本，无产品语义改动，不涉及 BR 条款 |

## 交接摘要

- **本片暴露**：FD-080、081、082 三项三层均通过，现有三个 app 上原问题已消失。
- **主要新发现**：P4a-01（中）——FD-081 拿掉了本机「意外的挡板」，锁定步从此会把比锁定值新的已提交分支退回；登记册 `SH-P1S4045`～`047` 的唤醒条件「改第 3 段」本轮已触发、未被唤醒。建议收口合并成一条，`新Session修`。
- **其余**：P4a-02～04 均为观察，不影响现在的三个 app 与本机。
- **本片依赖**：主会话真跑 `up.sh` 的结论（exit 0、三个 app 已在锁定 commit、第 9 段齐备、三个仓库被写入 `autocrlf=true`）；本片没有重跑。
- **`SH-P1S4040`～`044`、`048`**：与本轮 docker 改动无关（040～044 是 app 代码，048 是第 4 段，本轮没改），未变糟、唤醒条件未触发。

## 盲区自述

- 没在容器里实跑 `bench build` 去验 jsx／tsx／vue／styl 的去向，P4a-02 只来自读 `esbuild.js`；fast-glob 的隐藏目录行为按默认值推断。
- 没查 `core.fileMode false` 的写入时机：它在第 4 段，晚于第 3 段的 status 判断，与 SB 给 autocrlf 挪位置的理由同构。本机已设好；新机器上容器 clone 出的文件模式与索引一致（9p 挂载带 `metadata`），推断不会触发，没实测。
- P4a-01 的定级在「中／低」之间：本机目前未发生回退、提交可从 reflog 找回、推送过的在 origin 还有；但它是本轮修复直接引出的行为变化，且 README 的承诺不覆盖。
- 没往 macOS 宿主、宿主 `autocrlf` 为非法值、`apps.json` 里 url 含 tab／换行这些方向找。
