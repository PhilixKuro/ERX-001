# P1-S6-R4 D回执-Part4（对象：代码）

**日期**：2026-10-11
**执行者**：Codex
**依据**：P1-S6-R3-C开发方案-Part4.md

## 逐项执行结果

| 任务 | 对应切片 | 落地位置 | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-014 | SL-010 | `Spike/P1S6R4-screen-check.js`; `Spike/P1S6R4-screens-forms.json`; `Spike/P1S6R4-screens-forms-v10/result.json`; `Spike/P1S6R4-sales-chain-proof.json`; `Spike/P1S6R4-screens-loop/result-sales-chain.json`; `Spike/P1S6R4-clean-check.json` | ✅完成 | 2026-10-11 | 演示站 55/55 屏通过；销售订单→生产→销售出库→销售发票→收款均为 docstatus=1，销售链真实 Desk 表单 3/3 通过。销售闭环留档 `20261011_002831` 后已显式恢复清洁 C `20261010_232619`；恢复后的清洁检查、译名自检、装序检查均通过。两套四件套均已复制到 `保留-S6收尾/` |
| TS-015 | SL-010 | `README.md`; `docs/开发守则.md`; `docs/项目概况.md` | ✅完成 | 2026-10-11 | 最终全量：240 integration + 2 导航，242/242 通过、0 跳过；Desk 6/6、独立前端 10/10、提取器反证与模板 3/3 通过。常驻文件、README、译名自检与装序均已复核 |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-014 | 方案对应切片验收条件 | 既有 smoke/备份/恢复；提取器正反证、只读模板探针、测试站独立前端撤钩/接回取证；HDTH 销售闭环脚本与 Desk 三屏复核 | 55/55 屏、销售链 3/3 屏通过；`sales-chain-proof` 显示销售订单、制造入库、销售出库、销售发票、收款已提交并有对应 SLE/GL。已恢复清洁基准 `20261010_232619`，清洁检查 pass=true、译名自检通过、装序 ok=true |
| TS-015 | 方案对应切片验收条件 | `bench --site test.localhost run-tests --app frappe_china`；常驻文件与 README 改写 | 240 integration + 2 导航，242/242 通过、0 跳过；译名自检、装序检查与 focused 用例均通过 |

## 全量验证

| 门 | 结果 |
|---|---|
| 最终 240 integration + 2导航 | ✅242通过、0跳过 |
| DEC-026／027 focused | ✅3 Python、Desk Node 6/6、独立前端 Node 10/10、模板 3/3；测试站撤钩/接回8项 |

### 2026-10-10 续跑证据

- 恢复后的清洁检查 `Spike/P1S6R4-clean-check.json` 通过：`Translation`、`Cash Flow Worksheet`、GL/SLE 与业务单据均为 0；无 `_FCT`/`_S6` 临时记录；HDTH 科目 266；`Cash Flow Worksheet` 表存在。清洁备份为 `20261010_232619`，四件套已复制到 `docker/backups/保留-S6收尾/`。
- 续跑闭环：采购订单、采购收货、采购发票、采购付款、销售订单、生产计划、工单、领料单、任务单、完工入库，以及销售出库、销售发票、销售收款均已提交。`Spike/P1S6R4-sales-chain-proof.json` 显示销售出库 2 GL/1 SLE、销售发票 3 GL、收款 2 GL；`Spike/P1S6R4-screens-loop/result-sales-chain.json` 的 Desk 三屏 3/3 通过。首次销售出库失败的根因是制造 helper 生成的辅助成本行缺 `expense_account`；在演示数据脚本中补入公司默认成本科目与成本中心后由原生校验成功，未修改 frappe/erpnext 上游源码。
- 修正逐屏等待条件，避免首页列表未完成时触发上游面包屑空引用；修正提取器保留输入框 `title`/`placeholder` 后反证通过。报表 `Filter based on …` 是 frappe-datatable 裸模板，CSV 不消费；在已批准的 Desk 限定适配中增加仅针对 `.datatable` 该前缀的 title 适配，实机复核为「按…筛选」。

- 改本次 CSV 前已完整执行 `bench --site test.localhost run-tests --app frappe_china`：237 条 integration tests 全通过，另2条导航测试通过，合计239通过、0跳过；integration 耗时1636.172秒。这是修改前回归，不替代 TS-015 最终回归。
- 粗核输出 `Spike/P1S6R4-screens-demo5/result.json` 为25/30；修正了 `/crm`、`/raven`、`/insights` 被错误当作 Desk 路由的取证问题。当前提取器漏 placeholder/title，等待条件与数据排除也需收窄，粗核数字不作为 AC-001 证据。
- `Spike/P1S6R4-translation-runtime.json` 记录三个独立前端实际正文、脚本 URL 和词典。CRM 入门组件与 Insights 演示横幅有未调用翻译函数的文字；Raven 源码已调用 `_()`，仍须核运行 bundle/运行时消息对象，不能先认定只需补 CSV。
- CSV 整句修正与新增键已同步6项官方覆盖（含保留官方同译名），译名 focused 8/8；`general` 与固定 `0/10 steps` 已移除，改成参数化步数；`example`、`com`、`China`、admin 不作全局白名单。Insights 菜单「数据源／数据存储／设置演示数据」已实机确认。
- DEC-026 用户已选择 A。自有 `update_website_context` 仅替换 zh 的三张已知模板，prefix include 保留上游入口；翻译脚本限定入门/图表/横幅。`Spike/P1S6R4-independent-app-check.json` 与8张截图证明撤钩英文、接回中文、SPA 导航与 input 用户值不变；其中首次发现 `stage (0%)` 残留，另补先红后绿用例与修复，再复跑成功。
- 提取器改为直接 text node、可见属性、当前 Select 选项；祖先隐藏与数据字段分别排除，保留子表按钮。`Spike/P1S6R4-extractor-proof.json` 正反证通过。旧粗核清单未改为完整清单前拒绝 `!!document.body` 等空条件，不能重用25/30作为正式结论。
- 演示站 DEC-026 部署后的 `migrate` 已成功结束（孤儿文件扫描阶段约456秒）；重复 `clear-cache` 并停止旧 honcho、重新启动 `bench start`（日志 `Spike/P1S6R4-bench-start.log`）。新增55项表单/页签/报表清单 `Spike/P1S6R4-screens-forms.json`，逐屏执行中；它是完整清单的一部分，尚不包含已填业务单据、创建/提交/取消等交互屏，不能作为完整验收结论。
- 新增正式表单屏核修复19个整句（`Spike/P1S6R4-form-translations.json`），官方重叠5项已登记，译名测试8/8通过（4.592秒）。55屏v7中已修复按钮/title、首页与原有侧栏；公司/库存与总账残留的 `_S6` 名称及凭证号是本轮造数后的数据项，尚须补带理由的数据边界再复核，不计全过。
- DEC-027 用户批准 Desk 限定 title 适配；Node 用例先2失败/4通过，实施后6/6。与已有 Node 合跑29/29、0跳过；`bench build --app frappe_china` 成功。CRM 入门 aria-label 正反证先失败，随后在既有区域补属性翻译，浏览器语言门/动态渲染/用户值验证通过。
- `Spike/P1S6R4-screens-loop/result-purchase_receipt.json` 的采购收货 3/3 与制造链表单证据保留；采购发票早先的前端加载异常是旧造数阶段的失败记录，后续恢复后由原生脚本完成提交并不覆盖该失败记录。
- 销售闭环留档备份为 `20261011_002831`（四件套，根目录及 `保留-S6收尾/`）；随后已显式恢复 `20261010_232619`（数据库、文件与迁移成功），重跑清洁查询 pass=true；译名自检通过，装序检查 ok=true。最终演示站为无业务数据的清洁基准。

## 改动清单（常驻文件）

| 文件 | 改动 | 依据 |
|---|---|---|
| `docs/开发守则.md` | 译名唯一来源、自动自检时机与官方覆盖登记 | 常驻文件契约判据B、§2长效工程约定；Part4 TS-015 |
| `docs/项目概况.md` | 已落地业务流程入口、自检能力与底稿 DocType 新名；未宣称整体验收完成 | 判据A、§2系统现状与§5失真即修 |
| app `README.md` | 官方覆盖说明、独立前端覆盖登记与复验法 | TS-015第3项、DEC-026 |

## 偏离与暂停

- 本 Part 开工时没有既有回执；按方案先建立本文件并逐项续写。
- 原清单仅30个粗核入口且提取器过度排除，未满足完整屏核；已纠正声称与脚本。TS-015部分文档/回归在 TS-014 未完成时提前准备，不据此跳过顺序或宣称整个 Part 完成。
- 独立前端追加按 DEC-026 执行，不改 R3 原方案；Node 用例先缺模块报红再实现，百分比用例先断言失败再修正。3条 Python 模板用例实现后才执行，不称其先红后绿。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| 每个 Part 使用独立 D 回执，开工即预填任务并在任务完成时回写 | 流程/位置 | Part 开工 |

## 未做项

| 项 | 为什么没做 |
|---|---|
| 无 | 方案要求的 TS-014／015 均已落地并验证 |

## 交 Stage 收口判去向的长效信息（TS-015 第 5 步）

> 本节由 R5 E 步按 IT-030（`本Session修`）补写，原回执缺此节。

| 编号 | 内容 | 现状 | 建议去向 |
|---|---|---|---|
| HT-014 | 侧栏 URL 项（`/crm/…`、`/raven`）对非 Administrator 用户是否可见 | 未验证：`desk_views.py` 对 URL 类型的判定未读完；本 Stage 只以 Administrator 验过 | 路线文档 §四 S7 执行清单（演示用户归 S7） |
| HT-008 | 从自有侧栏进入的单据，经「创建 → 下游单据」或报表跳转时侧栏是否保持 | 未实测：屏核各屏以 `frappe.set_route` 直接打开，未走「创建」路径（见 E 报告 IT-021） | 随 IT-020 整改实测；若有换走侧栏的屏，结论交 S7 演示脚本 |

## 状态值

`代码已落地`。TS-014 的 55 屏、销售闭环、清洁基准与最终恢复核均通过；TS-015 最终全量与常驻文件收尾完成。下一步按 `plannedDev` 进入 E 确认。

## 复核建议

- 对照方案 Part 的每个任务和本回执落地位置，确认没有把 Part2 结果混入 Part1。
- 重点复核所有标记为 ✅ 的任务是否有可复现命令或正向界面证据。
