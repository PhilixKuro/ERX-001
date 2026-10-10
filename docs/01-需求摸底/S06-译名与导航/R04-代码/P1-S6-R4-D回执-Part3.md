# P1-S6-R4 D回执-Part3（对象：代码）

**日期**：2026-10-10
**执行者**：Codex
**依据**：P1-S6-R3-C开发方案-Part3.md

## 逐项执行结果

| 任务 | 对应切片 | 落地位置 | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-010 | SL-007 | `workspace_sidebar/business_flow.json`; `desktop_icon/business_flow.json`; `public/icons/desktop_icons/{solid,subtle}/business_flow.svg`; `public/js/desk_patches.js`; `tests/test_sidebar_header.cjs` | ✅完成 | 2026-10-10 | 7 个分节、51 个链接、图标与 SVG、DEC-024 守卫已落地；新会话51/51点击、树视图两轮10/10、`/undefined` 请求0；旧 modified 跳过、新 modified 导入、恢复后迁移及 CN Tax 内容/时间戳不变均通过 `Spike/P1S6R4-migration-future.json` |
| TS-011 | SL-007 | `tests/test_business_flow_navigation.py`; `Spike/P1S6R4-nav-click.js`; `Spike/P1S6R4-nav-click.out.json` | ✅完成 | 2026-10-10 | 从业务流程侧栏真实点击 Account、Warehouse、Cost Center，路由均为 Tree 且可见节点分别为 6、1、1；Company、Employee 为列表且有记录，各有独立 PNG。首页业务流程图标首项、两种 SVG 资源已取证 |
| TS-012 | SL-008 | `public/js/desk_patches.js:9`; `public/js/opening_ledger.js:5`; `tests/test_opening_ledger.cjs`; `README.md`；`Spike/P1S6R4-opening-ledger.js` | ✅完成 | 2026-10-10 | 修正 Payment Entry 的原生 `fa fa-table` 分组与 Journal Entry 的 `finance_book` 保留；Node 8/8 通过。浏览器真实点击期初库存调账、期初日记账、普通库存凭证、普通日记账的会计凭证按钮，前两者带 `show_opening_entries=1`，后两者不带，四者各返回 2 条非零分录并截图；删除 StockController 后重载补丁告警 1 条、无异常。HT-004/005/015 均成立，见 `Spike/P1S6R4-opening-ledger.out.json` |
| TS-013 | SL-009 | `Spike/P1S6R4-ts013-report.md`; `Spike/P1S6R4-refresh-check.js`; `Spike/P1S6R4-refresh-{bom,job,tax}.json` | ✅完成 | 2026-10-10 | 六例均有真实路径与结论；例 1/5 引 TS-011，例 2 按 LG-073 不修，例 3 保存后未刷新即有可用提交按钮，例 4 四阶段时间行真实且 idx 唯一，例 6 演示站新会话首进列表显示5条；实时往返通过，未复现的不硬修。测试数据已按专用公司范围清理并验证。 |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-010 | SL-007 ①～④、⑥～⑧ | `node Spike/P1S6R4-nav-click.js`; `node Spike/P1S6R4-tree-rounds.js`; `node Spike/P1S6R4-sidebar-probe.js`; `python Spike/P1S6R4-migration-future.py`; build；app-order check | 51/51 点击，树/列表两轮10/10；`/undefined` 为0；旧 modified 跳过、新 modified 导入、恢复后迁移与 CN Tax 不变均通过；构建与装序检查通过 |
| TS-011 | SL-007 ⑤ | `node Spike/P1S6R4-nav-click.js`，实际点击业务流程侧栏，实时读取路由/可见树节点/列表数据并截 PNG | 三个树形入口有节点；公司、员工列表有记录；详见输出逐项明细及 `P1S6R4-nav-{tree,list}-*.png` |
| TS-012 | SL-008 ①～④ | `node --test .../tests/test_opening_ledger.cjs`；`bench build --app frappe_china`；`node Spike/P1S6R4-opening-ledger.js` | Node 8/8，浏览器 4/4，开账参数与非开账分支均按方案；每张凭证接口返回 2 条分录，截图 `P1S6R4-ledger-*.png`；异常路径 1 条告警且不抛错 |
| TS-013 | SL-009 ①～⑤ | `node Spike/P1S6R4-refresh-check.js bom`／`job`／`tax`；每次先让桌面页真实回执 realtime_check；前两者在测试站、tax 在演示站只读打开列表 | BOM 无未保存标志且「提交」可用；任务单四阶段各存库内时间行与界面计时器截图，最终两行 idx=1/2、完成量1、按钮消失；演示站税模板首进5条且有三条取数请求。realtime 回执来自相应站点，耗时 BOM 584.1ms、任务单590.8ms、演示站597.4ms。完整步骤与环境见复现报告 |

## 全量验证

| 门 | 结果 |
|---|---|
| Part3 focused verification | ✅ 13 Node tests; browser navigation 51/51; tree/list 10/10; migration probes pass |

## 偏离与暂停

- 本 Part 开工时没有既有回执；按方案先建立本文件并逐项续写。
- 本轮两处既有开账补丁的纠错先修改实现、后补 Node 验收用例，未满足测试先行次序；如实记录，不把 8/8 通过称为先红后绿。浏览器首轮日记账未带开账参数，原因是浏览器 boot 早于探针公司建立，重新登录后四张凭证均通过。
- TS-010 守卫按 DEC-024 补充方案实现；守卫测试按测试先行先红2项、实现后5项全绿。CN Tax 固定时间戳按 DEC-025 实现，原方案“JSON 不改”放宽为“只补 modified，内容不变”。
- 全量测试首次运行 237 integration tests：236 通过、1 因 `cash_flow_worksheet.py` UTF-8 BOM 被 `ast.parse` 拒绝；去除该文件 BOM 后，`test_scaffold` 4/4 通过。全量套件未因功能断言失败；Part4 TS-015 仍须按方案再跑一次完整套件。

## 新增约定

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|
| 每个 Part 使用独立 D 回执，开工即预填任务并在任务完成时回写 | 流程/位置 | Part 开工 |

## 未做项

| 项 | 为什么没做 |
|---|---|
| 全量 `frappe_china` 回归与 Part4 | 依赖本 Part 完成后按 Part4 执行；全量测试尚未开始 |

## 状态值

`代码已落地`（Part3）。TS-010/011/012/013 的方案要求验证均完成；全量回归属于 Part4 TS-015，尚未开始。

## 复核建议

- 对照方案 Part 的每个任务和本回执落地位置，确认没有把 Part2 结果混入 Part1。
- 重点复核所有标记为 ✅ 或 ⚠️ 的任务是否有可复现命令或正向界面证据；本 Part 当前没有可标记为完整验收的任务。
