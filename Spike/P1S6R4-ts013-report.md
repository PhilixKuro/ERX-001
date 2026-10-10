# P1-S6-R4 TS-013：不刷新六例复现记录

日期：2026-10-10。Chrome 154.0.8037.98，界面语言 `zh`。测试站为 `test.localhost:6787`；例6在 `erx.localhost:8000` 只读。例3、4 前各由实际桌面页面收到 `realtime_check.run` 回执（测试站约584.1ms、590.8ms；演示站约597.4ms），没有把“通道不通”混成界面缺陷。

| 例 | 操作与环境 | 实测 | 结论与处置 |
|---|---|---|---|
| 1 仓库列表空白 | 由 Business Flow 侧栏点 Warehouse | URL 路由为 `Tree/Warehouse`，树节点1个 | 未复现；见 TS-011 的两轮树视图证据 |
| 2 采购工作区卡片不显示 | 检查 v16 侧栏实现与调用路径 | Workspace Sidebar 取代旧卡片入口，`add_card()` 无调用者；刷新不改变这一点 | 不属于不刷新问题；按 `LG-073` 不修 |
| 3 BOM 保存后提交按钮不出现 | 测试站建两个 `_FCT S6P3` 物料、一条原料行、一道工序，实际点击保存，不刷新 | 保存后 `__unsaved=0`、`is_dirty=false`、`set_value` 调用已记录；主按钮“提交”存在且未禁用 | 未复现，不改上游；结构化证据 `P1S6R4-refresh-bom.json`，界面 `P1S6R4-refresh-bom-saved.png` |
| 4 Job Card 时间行残留空记录 | 测试站真实执行开始（选员工）→暂停→继续→完成，每步查询数据库并读取 UI | 开始/暂停/继续/完成四态各有截图；两条时间行 name 均为真实记录，idx 1/2，无空/new 行；最终完成量1、计时按钮消失 | 未复现，不加 `doc_events` 兜底，不改上游；`P1S6R4-refresh-job.json` |
| 5 树形 DocType 从侧栏点进空白 | 由 Business Flow 点 Account | `Tree/Account`，6个可见节点 | 未复现；并在干净状态和已访问列表状态下，各测 Account/Warehouse/Cost Center/Company/Employee，十项全通过，见 `P1S6R4-tree-rounds.json` 与 `P1S6R4-tree-{clean,after-list}-*.png` |
| 6 新会话首进销售税模板列表空白 | 演示站新浏览器会话首次打开 `/desk/sales-taxes-and-charges-template`，只读观察 | 页面5条记录；Network 实际出现 `reportview.get`、`get_count`、`get_list` 三条取数请求 | 未复现，不改演示站；`P1S6R4-refresh-tax.json` 与 `P1S6R4-refresh-tax-demo.png` |

可复跑：先按 `docs/.../P1-S6-R3-C开发方案-Part3.md` 建立专用数据，再真实启动测试站 6787 服务并保持 realtime 页面开启，执行 `node Spike/P1S6R4-refresh-check.js bom` 和 `job`；`tax` 只读连接演示站。树视图的两种状态执行 `node Spike/P1S6R4-tree-rounds.js`。本报告与结构化结果均排除在本地 git 状态之外。

本轮为六例补造的 `_FCT S6 Part3` 公司及其关联数据必须按 `Spike/P1S6R4-part3-data.py cleanup` 精确清理并验证无残留。若重复继续测试，可先运行 `reset-job` 重置自己的草稿任务卡。
