# P1-S6-R4 D回执-Part1（对象：代码）

日期：2026-10-09｜执行者：Codex｜Spec：D-code-plannedDev-build.md，打tag=否
依据：R3 开发方案总纲与 Part1。

## 逐项执行结果

| 任务 | 对应切片 | 落地位置（相对 frappe_china app，Spike 为项目根） | 结果 | 完成日期 | 说明 |
|---|---|---|---|---|---|
| TS-001 基线脚本 | SL-001 | Spike/P1S6R4-baseline.py:1 | ✅完成 | 2026-10-09 | 七 app HEAD 匹配；缺口 5513，撞名 905，演示面 3042、演示撞名 185、官方覆盖 2；明细见输出 JSON |
| TS-002 自检函数与 labels.py 收窄 | SL-001 | frappe_china/translation_check.py:1; frappe_china/accounting/statements/labels.py:1 | ✅完成 | 2026-10-09 | 全部语言、50 行上限和提示已覆盖；测试站及演示站只读自检均通过 |
| TS-003 测试改造与覆盖清单 | SL-001 | frappe_china/tests/translation_overrides.py:1; frappe_china/tests/test_translation_check.py:1; frappe_china/tests/test_translations.py:1 | ✅完成 | 2026-10-09 | 自检 8/8、译名 7/7；六 app、assets、清理断言和重复键反证已覆盖 |
| TS-004 底稿改名与补丁 | SL-002 | frappe_china/cn_tax/doctype/cash_flow_worksheet/cash_flow_worksheet.py:1; frappe_china/patches/s6_rename_cash_flow_worksheet.py:1 | ✅完成 | 2026-10-09 | migrate、旧记录与子表迁移、controller 与幂等均通过；现金流 20/20、数据集 15/15、补丁 2/2、译名 7/7；新名称表单打开与三种搜索名称已截图 |
| TS-005 S4 四处小缺陷与分隔符 | SL-003 | frappe_china/cn_tax/doctype/cash_flow_worksheet/cash_flow_worksheet.js:1; frappe_china/accounting/statements/unmapped.py:1; frappe_china/accounting/closing.py:1 | ⚠️部分 | — | 四处修改与 context 分隔符已落地，相关模块全过，修改后截图已补；修改前有效对照仍缺，用户裁决保留 Part1 未完成并先修测试站货币配置 |

## 方案要求的验证

| 任务 | 验证方式 | 实测结果 |
|---|---|---|
| TS-001 | python Spike/P1S6R4-baseline.py | 七 app HEAD 匹配；缺口 422/1843/775/164/483/1826，合计 5513；撞名 905；演示面 3042，演示撞名 185，官方覆盖 Formula/Yearly Amount 两条 |
| TS-002 | 两站 execute 自检 | test.localhost 与 erx.localhost 均打印「译名自检通过」、返回 []；演示站仅查询 |
| TS-003 | 两个测试模块 | test_translation_check 8/8，test_translations 7/7，均无跳过；自检日志 Spike/P1S6R4-translation-check.log |
| TS-004 | SL-002 ①～⑤ | migrate 成功；旧表不存在，新表含原记录及一行 Cash Flow Item，parenttype=Cash Flow Worksheet，controller=CashFlowWorksheet，重跑不报错；补丁 2/2、现金流 20/20、数据集 15/15、译名 7/7；迁移及清理见 Spike/P1S6R4-rename-probe.json，搜索见 Spike/P1S6R4-worksheet-search.png；浏览器打开的三张底稿为另造的 UI 数据，原迁移探针已清理 |
| TS-005 | SL-003 ①～⑥及四模块测试 | test_cash_flow 20/20、test_closing 24/24、test_unmapped 4/4、test_translations 7/7、test_s6_closing_separator 2/2，均无跳过；取消确认框、已提交/已取消按钮隐藏、草稿取明细标脏与保存可点、公司/月份为空按钮隐藏均有修改后截图；漏科目报表已实显 ¥ 25.00；有效前态对照待补 |

## 全量验证

| 门 | 结果 |
|---|---|
| Python py_compile | 前序已通过（TS-002、TS-004 实现文件） |
| Part1 相关模块 | 合计 82 条通过，0 跳过：自检 8、译名 7、改名 2、分隔符 2、漏科目 4、现金流 20、结转 24、两年数据集 15 |
| 回归日志 | Spike/P1S6R4-closing.log（24/24）；Spike/P1S6R4-statement-dataset-rerun.log（15/15） |
| git diff --check | 主仓库与 frappe_china 均通过；七处文件尾空行已清理 |
| 全量 app | 未跑；S5 基线 215 条，最终全量与只增不减比较按 Part4 TS-015 执行，本轮 82 条不能替代全量 |
| JS 语法 | node --check：测试站 CDP 取证脚本与 cash_flow_worksheet.js 均通过 |

### TS-004 消息改名判定

| 原源词 | 判定 |
|---|---|
| No submitted Cash Flow for this month | 指底稿，改为 Cash Flow Worksheet |
| Cash Flow row {0} is missing | 指报表行，保留 Cash Flow；调用处 cash_flow_statement.py 的 _value |
| Cash Flow for {0}, month {1} already exists | 指底稿，改为 Cash Flow Worksheet |
| Submit the Cash Flow for month {0} before month {1} | 指底稿，改为 Cash Flow Worksheet |
| Submit Cash Flow month(s) {0} before month {1} | 指底稿，改为 Cash Flow Worksheet |
| Cancel later Cash Flow months before cancelling month {0} | 指底稿，改为 Cash Flow Worksheet |
| Cash Flow ending balance does not match cash accounts: {0} vs {1} | 指底稿，改为 Cash Flow Worksheet |
| Cash Flow year-to-date ending balance does not match cash accounts: {0} vs {1} | 指底稿，改为 Cash Flow Worksheet |

Cash Flow Items、Cash Flow Name、Cash Flow Type 等子表字段名保持原样。改名补丁与补丁测试中的旧名仅用于识别旧站迁移路径。

## 偏离与暂停

- 本轮前序曾批量误写 BOM 和文件尾空行并破坏 closing.py；已通过 apply_patch 恢复原始结转逻辑，结转 24/24 与数据集 15/15 回归通过。仍有无业务语义的文件尾换行差异，未以 reset/restore 清理。
- 已有实现未按先红后绿执行；后续补齐验收反证，不把通过结果当作测试先行证据。
- 基线脚本的四部分演示线面与官方覆盖清单已补齐，demo_surface=3042；LG-009 的机械差集仍需区分实际操作与文字提及，详见下节。
- 旧名底稿造数、迁移及清理已执行，HT-006 探针 go，详见 D待验表与 Spike/P1S6R4-rename-probe.json。新装路径以补丁测试覆盖，未做全新装站实测。
- 数据集与结转曾并行运行，Company 嵌套集写锁导致数据集 setUpClass 超时、运行 0 条；顺序重跑数据集后 15/15 通过。失败日志 Spike/P1S6R4-statement-dataset.log 保留，不把失败算成跳过。
- 修改前截图没有留存。closing-before-reconstructed.png 仅以旧源词重建确认框，当前字典已删旧译文，所以该图露出英文；unmapped-before-reconstructed.png 与修改后金额相同，未区分两种情形。两图都不作修改前验收证据。
- 首次漏科目截图显示 CNY 25.00；只读核实 Currency/CNY.symbol 为 null。临时补符号的对照截图可显示 ¥，已恢复原配置并核验。用户随后裁决「保留 Part1 未完成，先修测试站的货币配置」，据此持久修复 test.localhost 的 Currency/CNY.symbol=¥，并重新取真实界面截图；演示站没有写入。

## 界面证据与清理

| 核验项 | 正向证据 | 实测结果与限制 |
|---|---|---|
| 取消确认框 | Spike/P1S6R4-S4fix-closing-after.png | 公司 _FCT S6 界面验证、2025 财年、第 3 月均出现；没有点击确认执行冲销 |
| 已提交/已取消底稿 | Spike/P1S6R4-S4fix-submitted-after.png；Spike/P1S6R4-S4fix-cancelled-after.png | docstatus 分别为 1/2，取明细按钮均不可见 |
| 草稿取明细 | Spike/P1S6R4-S4fix-draft-before-fetch.png；Spike/P1S6R4-S4fix-draft-after-fetch.png | 点击真实按钮后 dirty=true，明细 1 行，主按钮「保存」且 disabled=false；随后真实保存成功。这是操作前后证据，不能替代修改前截图 |
| 未填公司/月份 | Spike/P1S6R4-S4fix-company-empty.png；Spike/P1S6R4-S4fix-month-empty.png | 公司空或月份 0 时按钮不可见；仅改表单内存，未保存，随后 reload_doc |
| 搜索现金流量 | Spike/P1S6R4-worksheet-search.png | 同时出现现金流量表、现金流量底稿、小企业现金流量表 |
| 漏科目币种 | Spike/P1S6R4-ui-currency.log；Spike/P1S6R4-S4fix-unmapped-after.png | 在持久修复的测试配置下，行 currency=CNY、列 options=currency、实际界面 ¥ 25.00；临时配置图另留 currency-fixture 后缀，不混作本次最终证据 |
| 测试站货币修复 | Spike/P1S6R4-test-currency.py；Spike/P1S6R4-test-currency.json | 固定只作用 test.localhost；首次 null→¥，第二次 ¥→¥、changed=false；按用户裁决保留新符号 |
| UI 数据清理 | Spike/P1S6R4-ui-data.py；Spike/P1S6R4-final-state.log | 公司、底稿、日记账及其 GL 与子表均清理；全部带 company 列的表对该公司计数无残留；GL 先按真实取消流程标记 is_cancelled，再按本探针公司和凭证精确删除，以解除链接保护；不带 force |
| 本地服务与自检 | 6787 服务使用后停止；测试站 execute 自检 | 译名自检通过，Translation 0 行；旧 Cash Flow DocType/表不存在，新底稿表空；未重启 8000 演示服务 |

### 基线差额与 LG-009

A 步缺口 347/1796/758/132/479/1826 与本轮差额分别为 75/47/17/32/4/0，恰为译文等于源词的条目数，合计 175。冻结 Part1 算法将这些条目计为缺口，故 5338 + 175 = 5513；不是版本变化。先前 896 撞名来自按冒号排除源词，误排了带冒号但无 context 的键；改为按解析所得 context 判别后与 A 步 905 一致。

Raven 冻结方案路径 settings/ai 实际为 settings/panels/ai，按当前锁定源码取后者。只追 CRM 的一层 component import，并解析无后缀路径。

LG-009 按操作稿反引号 DocType 机械求差得 14 项：Item Attribute、Lead、Master Production Schedule、Period Closing Voucher、Pick List、Prepared Report、Report、Repost Item Valuation、Sales Forecast、Translation、User Permission、Warehouse Type、Workstation Operating Component、Workstation Type。含说明和不采用项的文字提及，不能把 14 项全部当成“实际打开”。原 38 项与文字的 39 项差额未被唯一定位；原始候选及完整展开清单留在 baseline.out.json，供 Part2 判断演示边界时核对。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| 自检函数放 app 包顶层，run() 打印并返回问题清单 | 位置/调用 | TS-002 |
| 自有 DocType 改名补丁放 pre_model_sync 并做表存在与新 DocType 幂等判断 | 位置/错误处理 | TS-004 |

## 未做项

| 项 | 原因 |
|---|---|
| TS-005 有效修改前对照 | 修改前截图未留存，当前两张 reconstructed 图片不能作为有效证据；用户裁决保留 Part1 未完成 |

## 2026-10-09 续跑记录

测试站现有唯一数据库备份是在新 DocType 迁移后生成，且旧演示站基准备份不能覆盖测试站；因此本次没有伪造修改前状态，也没有对 `erx.localhost` 写入。当前实现的聚焦回归重新执行如下：

| 模块 | 结果 |
|---|---|
| `test_s6_closing_separator` | 2/2 通过，0 跳过 |
| `test_unmapped` | 4/4 通过，0 跳过 |
| `test_cash_flow` | 20/20 通过，0 跳过 |

本次未新增有效修改前截图，TS-005 仍保持部分完成；续跑锚点仍是拿到真实前态对照后再验收，不进入 Part2。
| Part2～4 | 用户裁决先修测试站货币配置，当前继续 Part1，不进入 Part2；全部 D 任务尚未完成，不进入 E |
| tag | 本步打tag=否，未执行 |

## 提交与推送

用户已明确授权「提交并推送」。frappe_china 已提交并推送至 origin/main：`db9541aec0ea925f9376cf927dcc87447a7a175b`；主仓库同步更新 docker/apps.json 的 frappe_china 锁定版本，并提交本轮证据与进度文档。提交前暂存区 git diff --check 通过；仅清理新增文件的尾部空行及自检文件 BOM，未重跑已有 82 条通过的行为测试。三处无关换行差异（hr.py、test_hr.py、原始科目表 JSON）未纳入提交，保留本地。提交不改变 Part1 未完成状态。

## 状态值

执行中，尚无出口状态。TS-001～004 完成，TS-005 部分完成；用户裁决保留 Part1 未完成、先修测试站货币配置，该配置修复及幂等验证已完成。续跑锚点为 TS-005 的有效修改前对照与验收；不进入 Part2，不进入 E。全量 app 回归留 Part4。

## 复核建议

- 重点核对 s6_rename_cash_flow_worksheet.py 在已有旧 DocType 与新装站两条路径下的幂等行为。
- 重点核对 translation_check.find_problems() 对 sites/assets/locale/*/LC_MESSAGES/frappe_china.mo 的路径枚举及空库导入阶段。
- 最薄的是 SL-003 的修改前对照。现有两张 reconstructed 图未满足判别力，不作为验收依据；按用户裁决保留未完成状态。
- 复核漏科目金额时同时看 currency 字段、列 options 与 Currency/CNY.symbol；测试站现已持久修复为 ¥，真实界面取证见 ui-currency.log 与 unmapped-after.png，演示站符号配置未改。
