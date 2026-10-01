# SB修复回执（对象：代码 / 依据：P1-S4-R9-E确认报告 ＋ P1-S4-R7 开发方案 Part2／Part4）

**轮次**：P1-S4-R11｜**日期**：2026-10-01｜**步骤**：`plannedDev` SB（build）｜**执行者**：Claude（Opus 5.5）
**Round 归属**：`附属=否`。R9 SB 与 R10 SB 已各交一份回执，本次在新 Session 里承接两者「未做项」中剩下的五项，是另一个工作项，**占 Round**，记为 R11。
**依据**：[E确认报告](../R09-确认报告/P1-S4-R9-E确认报告.md) IT-017／020／021／028／031（用户裁决均为「立即修」）＋[R9 SB修复回执](../R09-确认报告/P1-S4-R9-SB修复回执.md)与[R10 SB修复回执](../R10-修复/P1-S4-R10-SB修复回执.md)的「未做项」＋[开发方案 Part2](../R07-开发方案/P1-S4-R7-C开发方案-Part2.md) SL-005 与 TS-009／010＋[Part4](../R07-开发方案/P1-S4-R7-C开发方案-Part4.md) SL-008／SL-009 与 TS-017／019
**用户指令**（2026-10-01，R10 收尾）：「剩下要修的内容留到下一个Session修。孤儿数据先不清，等本步收口再说。」
**用户指令**（2026-10-01，本轮交付后）：「1、你帮我改。2、如果影响截图的话，孤儿数据可以清。3、做完以上两项后Push当前项目。」——1 指 `git config user.email` 双 `@`，2 解除了上一条的「孤儿数据先不清」

## 本轮范围

| 项 | 范围 |
|---|---|
| IT-017 | 结转测试补强（SL-005 ①②③⑥⑧⑫、HT-004 红冲分录、造数改用销售／采购发票） |
| IT-020 | 打印与导出测试（SL-008 ①～③⑤、HT-007）＋TS-017 界面证据 |
| IT-021 | 银行导入测试补强（SL-009 ①③④、log 文案、方案点名的 `test_bank_reconcile.py`） |
| IT-028 | D 回执追加更正段（不改历史结论） |
| IT-031 剩余 | 年报隐藏「月份」、`unmapped.py` 静默跳过、结转状态提示的子串匹配、结转凭证 remark、`app_email` |

不在本轮：IT-025（出方案修复）。测试站孤儿数据原定等 S4 收口再说，本轮交付后用户许可清理（见上方第二条用户指令），已在本轮清掉。

## 逐项执行结果

| 任务 | 报告项号 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| 年报隐藏「月份」 | IT-031 | `cn_tax/report/小企业利润表/小企业利润表.js:12`、`cn_tax/report/小企业现金流量表/小企业现金流量表.js:12`（`depends_on: eval:doc.period_type !== 'Annual'`）；`accounting/statements/printing.py:50`（`_month`） | ✅完成 | 10-01 | 方案 Part3 TS-013「选 `Annual` 时 `month` 固定为 12，并在界面上隐藏」。现金流量表的 `month` 原本没有默认值，隐藏后会卡在必填，故补了默认当月。PDF 的期间文字与文件名原先直接读 `filters.month`，年报时会印成隐藏筛选里的默认月，改为与 `execute` 一致按 12 月 |
| `unmapped.py` 在 `1000` 缺失时不静默 | IT-031 | `accounting/statements/unmapped.py:95`（R9 已去掉 `try/except`）；`tests/test_unmapped.py:80` | ✅完成 | 10-01 | 代码在 R9 SB 的 `dde0a4c` 里已改（R9 回执未记）；本轮补测试：把 `1000` 改号后出表报错并带出 `1000` |
| 结转状态提示不靠英文子串 | IT-031 | `accounting/statements/balance_sheet.py:66`（R9 已改为与 `_()` 源词整句比较）；`translations/zh.csv:50-53`；`tests/test_closing.py:332` | ✅完成 | 10-01 | 代码在 `dde0a4c` 已改。本轮发现 4 条 issue 原文没有中文词条，补进 csv；测试在 `zh` 会话下确认 issue 已被翻译、报表说明行仍认得出 |
| 结转凭证 remark 写明计算依据 | IT-031 | `accounting/closing.py:160-166`（增值税）、`:184-193`（附加税）、`:226-231`（损益）、`:233-249`（本年利润）；`translations/zh.csv:55-60` | ✅完成 | 10-01 | 按方案 Part2 字段表示例：增值税写「应纳增值税 X ＝ 已交 ＋ 转出未交 − 转出多交；组余额」，附加税逐项写「基数 × 税率 ＝ 金额」与合计，损益与本年利润写净利润（亏损）金额与去向。`_pl_transfer_rows`／`_year_end_rows` 改为同时返回金额，只有 `closing.py` 内部调用 |
| `app_email` | IT-031 | `hooks.py:5`（无改动）；`C:/Users/Philix/.gitconfig` 的 `user.email` | ✅完成 | 10-01 | `hooks.py:5` 已是 `PhilixKuro@users.noreply.github.com`（D 步已改正）。报告指出的另一半是 git 配置：`git config --show-origin` 查明双 `@` 写在**全局** `~/.gitconfig`，主仓、`frappe_china`、`frappe`、`erpnext`、SPS 五个仓库都继承它，各仓库本地没有覆盖。经用户许可（「你帮我改」）改为 `PhilixKuro@users.noreply.github.com`，五个仓库读回都是新值。**已推送的历史提交作者邮箱不改**（要改只能改写已推送的历史），本轮之后的提交用新邮箱 |
| 结转测试补强 | IT-017 | `tests/test_closing.py`（新增 `invoice`／`gl_snapshot`／`pl_by_account_and_cost_center`／`second_cost_center`，重写 `seed_normal_month` 与两个测试）；`tests/test_closing_voucher.py:72-86, 150-158` | ✅完成 | 10-01 | 逐条见「复验结果」IT-017 行 |
| 银行导入测试补强 | IT-021 | `tests/test_bank_reconcile.py`（新建，方案 TS-019 点名的文件）；`tests/test_bank_preprocess.py`（移走集成测试，只留 7 个解析测试）；`translations/zh.csv:61` | ✅完成 | 10-01 | 逐条见「复验结果」IT-021 行 |
| 打印与导出测试 | IT-020 | `tests/test_statement_export.py`（新建，3 个测试，跑在两年数据集上）；`tests/test_prepared_report.py`（新建，方案 TS-017 点名的文件） | ✅完成 | 10-01 | 逐条见「复验结果」IT-020 行 |
| TS-017 界面证据 | IT-020 | `docs/01-需求摸底/Spike/P1-S4-R11-TS017-ui-balance-sheet.png`／`-ui-profit-and-loss.png`／`-ui-cash-flow.png`／`-ui-profit-and-loss-annual.png`（浏览器界面）；`-pdf-balance-sheet.png`／`-pdf-profit-and-loss.png`／`-pdf-cash-flow.png`（法定格式 PDF 首页渲染） | ✅完成 | 10-01 | 见「TS-017 界面取证」节 |
| D 回执更正段 | IT-028 | `R08-代码/P1-S4-R8-D回执-Part4.md` 末尾「更正段」；Part1～3 末尾各一行指针 | ✅完成 | 10-01 | 只追加，不改上文。TS-021 的确认原话与逐条命令取自 Codex 会话记录（D 步是在 Codex 里执行的），见「复验结果」IT-028 行 |
| 测试站孤儿数据清理 | — | 测试站 `test.localhost` | ✅完成 | 10-01 | 用户许可后清理，见「测试站孤儿数据清理」节 |
| 全量回归 | — | `bench --site test.localhost run-tests --app frappe_china` | ✅完成 | 10-01 | 清理前后各跑一次，见「全量验证」 |

## 复验结果

| 报告项号 | 报告的判定标准 | 怎么复验的 | 实测结果 |
|---|---|---|---|
| IT-017 ① | 附加税各自舍入可区分；按科目＋成本中心逐一为 0；每张凭证 `voucher_subtype`；编号 -001～003；三个附加税科目各自金额 | 造数改用 `P13专票未税` 的销售发票 10,050 与采购发票 6,000，应纳 526.50：各自舍入 36.86＋15.80＋10.53＝63.19，按 12% 一次舍入是 63.18。管理费用记在另建的第二个成本中心。断言三个附加税科目各自金额、5403 借方 63.19、全部损益 (科目, 成本中心) 年内余额为 0 且第二成本中心确有发生额、每张凭证 GL 的 `voucher_subtype` 等于其类别、编号 `JZ-FCN-202603-001～003` | ✅通过 |
| IT-017 ② | 重复生成后条数不变 | 报错前后数结转凭证条数 | ✅通过 |
| IT-017 ③ | 取消前后逐科目快照；编号 -004～006 | 结转前取全部有效 GL 按 (科目, 成本中心) 的快照（直接 SQL，不经 `gl_sums`），整月取消后与之逐项相等；重做后编号为 -004、-005、-006 | ✅通过 |
| IT-017 ⑥⑧ | 用销售发票造草稿与「结转后变动」 | 草稿改为一张未提交的销售发票，断言草稿清单里有它、且一张结转凭证都没建；结转后再提交一张该月销售发票 → `complete=False` 且 issues 含该条；取消并重新生成后 `issues=[]`、`complete=True` | ✅通过 |
| IT-017 ⑫ | 权限测生成入口 | `Accounts User` 调 `generate_month_end_closing` 与 `cancel_month_end_closing` 都抛 `PermissionError`（另保留内部 `_make` 那一条） | ✅通过 |
| IT-017／HT-004 | 红冲分录 | 取消后该凭证共 4 条 GL、全部 `is_cancelled=1`；其中 2 条 remarks 为 `On cancellation of …`，借贷与原分录对调 | ✅通过 |
| IT-017 判别力 | 测试能区分两种舍入写法 | **临时**把附加税改成「合计按 12% 一次舍入、差额挤进城建税」：`test_normal_month…` 报 `-36.85 != -36.86`、`test_year_end…` 报 `-2986.82 != -2986.81`，2 项失败。还原后 `grep -c MUTATION` 为 0 | ✅通过（临时改动已还原，未入库） |
| IT-020 ① | 屏幕列头逐字合规 | `test_screen_columns_are_legal`：`zh` 下三张表 `run()` 的列头与法定列头相同，数据非空 | ✅通过 |
| IT-020 ②／HT-007 | `export_query` 导出、`openpyxl` 读首行；资产负债表 8 列两个「行次」各占一列；行名行次同屏幕 | `test_xlsx_header_and_rows_match_screen`：设 `form_dict` 调 `export_query`，读 `frappe.response.filecontent`；首行逐字相同；其后每行按屏幕列序取（行名, 行次），与屏幕逐行相同 | ✅通过 |
| IT-020 ③ | PDF 标题、表号、编制单位、列头行名、`NotoSansCJK` 嵌入、方向 | `test_pdf_text_fonts_and_orientation`：`pdftotext` 取出标题、表号、`编制单位：{公司名}`、`单位：元`、全部列头与行名；`pdffonts` 有 `NotoSansCJK…` 且 `emb=yes`；`pdfinfo` 页面尺寸资产负债表 842×595（横）、另两张 595×842（竖）。期望的标题、表号、方向写死在测试里，不读被测的 `printing.STATEMENTS` | ✅通过 |
| IT-020 ③ 判别力 | — | **临时**删掉资产负债表模板里的表号 → 失败；**临时**把资产负债表方向改成 `Portrait` → 失败（`595.0 not greater than 842.0`）。两处都已还原，`git diff --stat -- templates` 为空 | ✅通过 |
| IT-020 ⑤ | `disable_prepared_report_automation=1`、`prepared_report=0`；睡 16 秒后仍为 0 | `test_prepared_report.py`：四个 Report 记录逐个读；把利润表 `execute` 包一层 `sleep(16)` 后经 `run()` 执行，再用**第二条数据库连接**读 `prepared_report`（本事务看不到另一连接的提交，同连接读回没有判别力） | ✅通过（25.8 秒） |
| IT-021 ① | 6 条逐行相符（日期、金额、摘要、对方户名） | 6 行期望值写成常量，CSV 由它生成；导入后按日期取 6 条 `Bank Transaction` 的（日期, 存入, 支取, 摘要, 流水号, 对方户名）与常量逐行相等 | ✅通过 |
| IT-021 ③ | 重复导入新增 0，log「6 行已存在，跳过」 | 同一 GB18030 文件再导一次：`rows=0, skipped=6`，条数仍 6；预处理单 `skipped_count=6`，`log` 含「6 行已存在，跳过」（补了 `{0} existing rows were skipped` 的中文词条，原先 zh 下显示英文） | ✅通过 |
| IT-021 ④ | xlsx 版本结果与 csv 相同 | 原测试给 xlsx 的流水号加了 `X-` 前缀再只比条数。改为同一内容（不改流水号）导入**另一个户头**（挂 `1012`），6 条记录与 csv 户头逐行相同 | ✅通过 |
| IT-021 其它 | ②⑥ 原有断言保留；方案点名的文件 | 自动核销与映射子表为空两组断言照旧；集成测试移到 `test_bank_reconcile.py`，`test_bank_preprocess.py` 只留解析测试 | ✅通过 |
| IT-028 | 补 TS-021 确认原话与逐条命令、P-3 判据、HT-007、数据集耗时；申报偏离；更正不符处 | 原话与命令从 Codex 会话 `C:\Users\Philix\.codex\sessions\2026\10\01\rollout-2026-10-01T10-57-25-…jsonl` 逐行取（只读）；其余逐条对照 E 报告 IT-028 的清单写进更正段 | ✅完成。另查出一处 D 回执未报的事实：清站前对备份的 `gzip -t` 在执行时**没跑起来**（宿主无 `gzip`，每个文件都输出 FAIL），真正跑通在 E 步，已写进更正段 |
| IT-031 | 四个小项 | 见上表各行；`test_closing` 9/9、`test_unmapped` 4/4、`test_translations` 1/1 | ✅通过 |

## 测试站孤儿数据清理

R10 记下的孤儿数据来自 R9 IT-015 删掉的 9 家 `_FCT 银行导入 BI*` 公司：公司记录删了，挂在它们名下的科目、凭证等还在。本轮用户许可清理（「如果影响截图的话，孤儿数据可以清」——要在测试站落数据截图，先把旧的清干净，截完整站恢复时才不会混在一起）。

| 步 | 做了什么 | 结果 |
|---|---|---|
| 1 备份 | `bench --site test.localhost backup --with-files` | `20261001_213507-test_localhost-*` 四个文件；`gzip -t` 与 `tar -tf` 都通过 |
| 2 圈定 | 只读查询：全库带 `company` 字段的表里，`company` 不是现存公司的行全部属于这 9 家；另按名字查以 `_FCT` 开头、带这 9 个缩写之一的主数据 | 无现存公司（Company 0）；孤儿只在这 9 家名下 |
| 3 演练 | 删除脚本先以 `DRY=1` 只计数。删除范围正向限定（开发守则「探针三条纪律」第 1 条）：`company` 恰为这 9 个名字之一的行；名字以 `_FCT` 开头且带其缩写的主数据；上述单据的子表行、Version 与附件 | GL Entry 18／Payment Ledger Entry 9／Bank Transaction 102（子表 Bank Transaction Payments 8）／Bank Statement Import 17／Bank Statement Preprocess 25／Payment Entry 9／Bank Account 9／Tax Rule 117／Cost Center 18／Account 2,394；Customer、Bank、Customer Group、Territory、Bank Statement Format 各 9；File 67；Version 102 |
| 4 实删 | 同一脚本 `DRY=0`，删完提交；对 Customer Group、Territory、Account、Cost Center 重建树 | 这 9 家名下各表都是 0；Account、GL Entry、Payment Entry 全站都是 0；`_FCT` 主数据都是 0 |
| 5 复核 | 只读查询 | System Settings 未变（zh／Asia/Shanghai／yyyy-mm-dd／CNY／Commercial Rounding）；已装 app 仍是 frappe／erpnext／frappe_china |
| 6 新基线备份 | 清理后再备份一次 | `20261001_214437-test_localhost-*`，`gzip -t` 通过。第 7 节截图后的恢复用这一份 |

两份备份都留在测试站 `sites/test.localhost/private/backups/`，没有复制到 `docker/backups/`（测试站不在 `backup.sh`／`restore.sh` 的范围内）。

## TS-017 界面取证

方案 Part4 TS-017：「在测试站界面上以 `zh` 用户打开三张报表，各导出一次 XLSX、下载一次法定格式 PDF，目视核对后截图存 `Spike/`」。

| 步 | 做了什么 | 结果 |
|---|---|---|
| 7.1 落数据 | 在测试站造一份两年数据集（缩写 `FDV`）并**提交**——测试里的数据集随事务回滚，界面上看不到 | 公司 `_FCT 报表数据集 FDV`，造数 16.6 秒 |
| 7.2 起服务 | 容器内另起一个只服务 `test.localhost` 的 `frappe --site test.localhost serve --port 6787`。**原因**：8000 端口上的 `bench serve` 是按 `default_site` 只服务演示站的单站点模式，`Host: test.localhost` 也会落到演示站（实测：以测试站的会话访问 8000 一律未登录，演示站 Activity Log 记了一条失败登录）。6787 是 compose 已映射、当前无人监听的 watch 端口 | `ping` 200；登录后 `Company` 列表只有 `FDV` 一家，确认连的是测试站 |
| 7.3 登录 | 给测试站 Administrator 设一个临时随机密码，`/api/method/login` 登录取 `sid` | `Logged In`。密码只存在随后删掉的临时文件里；第 8 步整站恢复后回到原密码 |
| 7.4 截图 | 无头 Chrome 带该 `sid`，依次打开三张报表（2026-03 月报），再在同一页面会话里调界面「导出」用的 `export_query`（Excel）与「打印法定格式」按钮的 `download_statement_pdf`；最后把利润表切到年报 | 三张表 `frappe.boot.lang = zh`、用户 Administrator；列头：资产负债表 8 列 `资产｜行次｜期末余额｜年初余额｜负债和所有者权益｜行次｜期末余额｜年初余额`，利润表与现金流量表 `项目｜行次｜本年累计金额｜本月金额`；行数 32／32／25；三张表都有「打印法定格式」按钮。**年报**：「月份」筛选已隐藏（IT-031），第四列变为 `上年金额` |
| 7.5 核下载文件 | 用 `openpyxl` 读三份 XLSX 首行，用 `pdfinfo`／`pdffonts`／`pdftotext` 查三份 PDF | XLSX 首行与上面的列头逐字相同，资产负债表 8 列；PDF 资产负债表 842×595（横），另两张 595×842（竖），字体 `NotoSansCJKsc-Bold` 嵌入，首行为法定标题与「会小企 0N 表」 |
| 7.6 存图 | 4 张界面截图＋3 张 PDF 渲染图存 `Spike/`（文件名见上表） | 已目视核对 |
| 8 恢复 | 停掉 6787 的服务；`bench --site test.localhost restore --force` 恢复第 6 步那份备份（含公私文件） | Company、Account、GL Entry、Payment Entry、Bank Transaction 都是 0，System Settings 与已装 app 同清理后；临时目录 `frappe-bench/tmp_r11_ui/` 已删 |

**说明**：界面截图里金额列显示为 `CNY 1,234.00`（Currency 字段的原生格式），PDF 与 XLSX 是纯数字；列头与行名三处一致。

## 全量验证

| 门 | 结果 |
|---|---|
| 执行前基线 | R10 回执：92/92。本轮新增测试方法：`test_unmapped` 1、`test_bank_reconcile` 1（由 `test_bank_preprocess` 移入，不算新增）、`test_statement_export` 3、`test_prepared_report` 2，预计 98 |
| 本轮全量回归（清理前） | **98/98 通过**（427 秒）＝ R10 的 92 ＋ 本轮新增 6，没有减少。日志 `frappe-bench/logs/r11-full.log` |
| 本轮全量回归（清理并恢复后） | **98/98 通过**（261 秒），日志 `frappe-bench/logs/r11-full-2.log`。清掉孤儿数据后没有测试依赖它 |
| 回归前后站点 | 清理前那次：前后一致，Company 0、Account 2,394、GL 18、Payment Entry 9（孤儿数据没有增加）。清理后那次：前后都是 Company 0、Account 0、GL 0、Payment Entry 0。System Settings 两次都是 zh／Asia/Shanghai／yyyy-mm-dd／CNY／Commercial Rounding |
| 临时文件 | `frappe-bench/tmp_r11_*`（舍入试算、字形探针、方向探针、PDF 渲染、孤儿清理、界面取证）均已删除；`ls frappe-bench | grep tmp` 为空 |

## 偏离与暂停

- **改了全局 git 配置**（经用户许可）。`user.email` 在 `~/.gitconfig`，改它影响本机所有仓库，不止本项目的五个。已推送的历史提交作者邮箱保留原样。
- **测试站做过一次整站恢复**（截图后）。恢复的是本轮第 6 步刚做的备份，此前已确认它与清理后状态一致；测试站上不存在需要保留的其它数据。
- **PDF 取字的两处容差写进了测试**，判据见「复核建议」第 2 条：① `pdftotext` 把与部首同形的字反查成部首码位（「小」「金」「行」「目」「一」「车」「长」等），测试先做 NFKC 归一并映射两个部首补充区字符；② 长行名在单元格里折行时，同一行的行次、金额会插在折行处，行名改为「按序出现在不超过行名长度＋40 字的窗口内」。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| 判断「另一连接是否提交了什么」时，用 `IntegrationTestCase.secondary_connection()` 读回；同一连接在 REPEATABLE READ 下看不到别的连接的提交，读回没有判别力 | 测试纪律 | IT-020 ⑤ |
| 校验 PDF 文字时先对 `pdftotext` 输出做 NFKC 归一（另映射部首补充区字符），再比较；不能直接拿原文子串比 | 测试纪律 | IT-020 ③ |
| 测试的期望值不从被测模块的常量读（如 `printing.STATEMENTS` 的方向、表号），按方案写死在测试里 | 测试纪律 | IT-020 ③ |

## 未做项

| 项 | 为什么没做 |
|---|---|
| TS-019 在测试站的界面重新取证（R9 IT-014 回执记的未做项） | 不在 E 报告本轮这五项内，用户本轮的许可只针对 TS-017 截图；留给 E 复核时判 |
| IT-025 底稿与法定标题撞名 | 用户裁为出方案修复 |
| 已推送提交的作者邮箱（双 `@`） | 改要改写已推送历史，未做 |

## 状态值

**`修复已落地`**。IT-017、IT-020（含 TS-017 界面截图）、IT-021、IT-028、IT-031（含 git 邮箱）都已改完，并按报告的判定标准复验通过；测试站孤儿数据已清，清理前后各跑一次全量回归，都通过。连同 R9、R10，E 报告裁为「立即修」的项都有了回执。R9 回执里记的「TS-019 测试站界面重新取证」不在本轮五项内，仍未做，见「未做项」。按出口路由，下一步回 E 复核。

## 复核建议

1. **最该看的是 IT-028 更正段里 TS-021 那两行**。原话只有「确认」两个字，而确认请求没逐项列出清站范围；备份完整性校验在清站当时没跑起来。这两条不改变演示站现状（E 步已复核为 HDTH 唯一公司、自检通过、备份三组 `gzip -t` 都 ok），但说明 DEC-101「执行前须当场确认范围与动作」那次执行得比方案要求宽。查法：读 `R08-代码/P1-S4-R8-D回执-Part4.md` 末尾「更正段」第一节。
2. **PDF 测试的两处容差是最可能藏问题的地方**（`tests/test_statement_export.py` 的 `_compact` 与 `_contains_wrapped`）。部首映射只列了报表里实际出现的 7 个字；折行窗口 40 字是按现有最长行名试出来的，行名变长或版式变窄时可能误报。它们只放宽了「字是否在」，没放宽标题、表号、编制单位与列头——那几项仍要求连续出现。
3. **拿不准处**：
   - 现金流量表的「月份」原本没有默认值，本步加了默认当月，否则隐藏后无法通过必填校验。这是界面行为的小改动，方案没写。
   - 低分辨率（110 dpi）的 PDF 渲染图里，利润表第 19 行「以“-”号填列」中的减号看不见；200 dpi 下可见，`pdftotext` 也取得出。判断为渲染图的分辨率问题，不是 PDF 缺字，但打印效果未实测。
