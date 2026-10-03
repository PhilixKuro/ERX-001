# SB修复回执（对象：代码 / 依据：P1-S4-R17-F审核报告 ＋ P1-S4-R7 开发方案 Part4）

**轮次**：P1-S4-R17｜**日期**：2026-10-03｜**步骤**：`plannedDev` SB（build）｜**执行者**：Claude（Opus 5.5）｜`打tag=否`
**Round 归属**：`附属=新Session做`（步骤表 SB 行原值）——本次只做 R17 F 报告裁为 `新Session修` 的 1 项（FD-055），是 R17 F 那个工作项的一部分，**不占 Round**，沿用 R17。
**依据**：[F审核报告](P1-S4-R17-F审核报告.md) FD-055（原条目 [Part4](P1-S4-R17-F审核报告-Part4.md) P4-05）＋[开发方案 Part4](../R07-开发方案/P1-S4-R7-C开发方案-Part4.md) TS-018＋R14 FD-024 判定标准
**用户裁决**（2026-10-03，见 F 报告「用户裁决」）：「按建议来」——FD-055 取建议档位 `新Session修`、建议修法「失败回调里也 `reload_doc`；须浏览器验」。
**范围外不动**：`本Session修` 14 项（F 步已修）、延迟 16 项（`SH-P1S4021`～`036`）、FD-065（并入 `SH-P1S4006`）、不做 2 项。

## 逐项执行结果

| 任务 | 报告项号 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| 预处理按钮成功、失败都刷新表单 | FD-055 | `frappe_china/cn_tax/doctype/bank_statement_preprocess/bank_statement_preprocess.js:7-15` | ✅完成 | 10-03 | 取报告建议的第二种写法：`.then(() => frm.reload_doc())` 改为 `frappe.call` 的 `always` 选项。读码依据：上游 `request.js:315-331` 在 `$.ajax(...).always` 里先 `frappe.request.cleanup`（解冻、弹报错）再调 `opts.always`，成功、失败、5xx 都走这一支；`.then` 只在 done 链上。服务端未动 |
| 浏览器复验 | FD-055 | 测试站 6787；`Spike/P1-S4-R17-SB-FD055-*.png` 4 张 | ✅完成 | 10-03 | 见「复验结果」与「浏览器取证」 |
| 全量回归 | — | `bench --site test.localhost run-tests --app frappe_china`（日志 `frappe-bench/logs/r17-sb-full.log`） | ✅完成 | 10-03 | 154/154，见「全量验证」 |

## 复验结果

| 报告项号 | 报告的判定标准 | 怎么复验的 | 实测结果 |
|---|---|---|---|
| FD-055 | 失败后界面看得到 Failed 与 log（方案 TS-018「Failed 时写 log」的意图；R14 FD-024 判定标准），且不再撞时间戳冲突；须浏览器验 | 无头 Chrome（DevTools 协议）以 Administrator 打开测试站一张日期写错（`2026-01-3x`）的预处理单，真实 DOM 点击「预处理并导入」，读表单状态；关掉弹窗后标脏并保存一次。同一张单在**改前代码**下再跑一遍作对照（变异）。另用一张正常流水的单验成功路径 | ✅ **改后**：弹窗「第 2 行：日期「2026-01-3x」无法识别」，背后表单已刷新为「失败」、log 同句、`modified` 与服务端一致；接着保存「已保存」。**改前（变异）**：服务端同样落了 Failed，但表单仍是「草稿」、log 空、`modified` 停在旧值；接着保存报「has been modified after you have opened it…请刷新获取最新数据」——即报告所述症状，变异判别力成立。**成功路径**：无弹窗，表单刷新为「已导入」，保存正常 |

## 浏览器取证

| 步 | 做了什么 | 结果 |
|---|---|---|
| 1 备份 | `bench --site test.localhost backup --with-files` | `20261003_191422-test_localhost-*` 四件 |
| 2 落数据 | 一次性脚本建本表公司 `_FCT 预处理界面取证 FUI`、银行、户头（挂 `1002`）、流水格式，一张坏日期 csv 的预处理单（`BANK-PRE-00026`）；之后另建一张 GB18030 两行正常流水的单（`BANK-PRE-00027`）；给 Administrator 设临时随机密码（只存在随后删掉的临时文件里） | 两张单均为 Draft |
| 3 起服务 | 容器内另起只服务测试站的 6787（见记忆） | `ping` 200；`frappe.boot.lang=zh`、用户 Administrator |
| 4 浏览器 | 宿主 Chrome 无头启动，`--remote-debugging-port=0` 自选端口（固定的 9333 落在 Windows 保留段、bind 失败，同 9000 那个坑） | 见「复验结果」。改前代码的对照：工作区临时换回 `HEAD` 版本 → 把单据复位为 Draft → 跑同一脚本 → 拷回改后版本，`sha256sum -c` 一致 |
| 5 存图 | `Spike/P1-S4-R17-SB-FD055-fixed-after-click.png`／`-fixed-after-save.png`／`-before-fix-after-click.png`／`-before-fix-after-save.png` | 已目视核对：改后点击图中弹窗背后表单的状态栏为「失败」、日志栏有原因；改前保存图为时间戳冲突弹窗 |
| 6 恢复 | 先单独停 6787（R12 的教训：不与 restore 写在同一条命令里），再 `bench --site test.localhost restore --force` 恢复第 1 步备份（含公私文件） | Company／Account／Bank／Bank Account／Bank Statement Format／预处理单／Bank Statement Import／Bank Transaction／GL 全为 0；System Settings 与 Global Defaults 的 country 仍为 China；Administrator 密码随恢复回到原值 |

## 全量验证

| 门 | 结果 |
|---|---|
| 执行前基线 | R17 F 步 154/154 |
| `run-tests --app frappe_china` | **Ran 154 tests in 490.571s, OK**（与基线同数：本项是前端 js，无 Python 可测面，判别力靠浏览器变异对照）。跑后测试站 Company／Account／Bank／预处理单／Bank Transaction／GL 均为 0，country 不变 |
| 临时文件 | `frappe-bench/tmp_r17_sb/`（落数脚本、浏览器脚本、临时密码文件、Chrome 配置目录）已删；`ls frappe-bench \| grep tmp` 为空 |
| `node --check` | 通过 |
| 改动面 | `git diff --stat`：1 file，4+／1-；app 内 `reload_doc` 只此一处调用 |

## 偏离与暂停

- **无暂停项**：报告建议与方案 TS-018 不冲突。报告给了两种写法（`callback`＋`error` 两个回调，或 `.always(...)`），取后者的等价形式 `always` 选项——`error` 回调在 417 之外的若干状态码分支里不一定被调到（`request.js` 各 `statusCode` 分支各自决定），`always` 不受影响。
- **演示站未动**：只改了一个前端 js，演示站同一份 bench 代码即时生效，无元数据改动，不需要 migrate。

## 新增约定

| 约定 | 类别（命名/位置/错误处理/依赖/跨层调用） | 在哪个任务确立 |
|---|---|---|
| 调用服务端方法、失败时服务端会补写单据（R14 FD-024 的 after_rollback 约定）的表单按钮，用 `frappe.call` 的 `always` 刷新表单，不用 `.then` | 跨层调用 | FD-055 |

（R14 SB 回执「新增约定」第 1 条 after_rollback 补写的前端配套。是否移交 `开发守则.md` 由收尾时定，本步不改常驻文件。）

## 未做项

无。

## 状态值

**`修复已落地`**——裁为 `新Session修` 的唯一一项 FD-055 已改完，并按报告的判定标准（须浏览器验）在测试站真实浏览器里复验通过，变异对照证实改前症状可复现、改后消失；全量回归 154/154。按出口路由「SB · `修复已落地` → 回唤起方（F）复核」。

## 复核建议

1. **修得最勉强的那项**：无勉强处——这是报告指出的根因本身（按钮只在成功时刷新）。可抽看 `bank_statement_preprocess.js:7-15` 与上游 `frappe/public/js/frappe/request.js:315-331`，确认 `always` 在 `cleanup` 之后执行（故先弹报错、再刷新，报错弹窗不会被刷新冲掉——截图 `fixed-after-click` 可见两者同时在）。
2. **修复引入的连带影响**：改动只此一个文件 4 行；成功路径已在浏览器复验（「已导入」、保存正常）。网络中断这类无响应的失败也会触发刷新，刷新本身若也失败只多一次报错，不影响数据。
3. **拿不准处**：浏览器取证用的是 Administrator；Accounts User 角色下没有另跑一遍（按钮与刷新是同一段前端代码，服务端权限判断未改）。
