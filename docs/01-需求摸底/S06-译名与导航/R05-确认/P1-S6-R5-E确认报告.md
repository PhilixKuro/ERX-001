# P1-S6-R5-E 确认报告（对象：D 代码 Part1～Part4）

日期：2026-10-11。依据 `plannedDev` E-verify-plannedDev-confirm、confirm brick、play-confirm，按 Part1～Part4 的 TS-001～TS-015 逐项复核。

## 逐项确认

| # | 任务 | 复核依据与实测 | 结论 |
|---:|---|---|---|
| 1 | TS-001 基线脚本 | `Spike/P1S6R4-baseline.py` 与输出；七 app HEAD、缺口、撞名、演示面统计与 D 回执一致 | ✅通过 |
| 2 | TS-002 自检与 labels | 演示站 `translation_check.run` 输出“译名自检通过”；清洁检查 Translation=0 | ✅通过 |
| 3 | TS-003 测试与覆盖清单 | 自检 8/8、译名 7/7；覆盖断言与官方覆盖登记存在 | ✅通过 |
| 4 | TS-004 底稿改名 | `rename-probe.json`：旧表消失，新表、子表 parenttype、controller 正确，重复执行成功 | ✅通过 |
| 5 | TS-005 S4 缺陷与分隔符 | D 回执模块结果 20/20、24/24、4/4、2/2，前后态证据齐全 | ✅通过 |
| 6 | TS-006 演示线档 | 点名术语和发票 context 2/2；Timesheet 族已核对 | ✅通过 |
| 7 | TS-007 批量档 | 固定种子抽检 usable=100、unusable=0；译名测试 8/8 | ✅通过 |
| 8 | TS-008 裸渲染点 | Sales/Purchase 状态、上下文回退、撤钩反证及构建证据齐全 | ✅通过 |
| 9 | TS-009 按钮抽检 | `P1S6R4-buttons.csv` 共 23 个词，源码动作定位均一致 | ✅通过 |
| 10 | TS-010 业务流程导航 | 51/51 点击；SVG 两 variant；迁移守卫、/undefined 请求 0 | ✅通过 |
| 11 | TS-011 树形点检 | Account、Warehouse、Cost Center 两轮树视图有节点；Company、Employee 列表有记录 | ✅通过 |
| 12 | TS-012 开账跳转 | 浏览器 4/4、Node 8/8；期初参数带 `show_opening_entries=1`，普通凭证不带；缺失类仅告警 | ✅通过 |
| 13 | TS-013 不刷新六例 | 六例均有专用报告和 JSON/截图；例 2 按方案引用 LG-073 不修 | ✅通过 |
| 14 | TS-014 逐屏与基准 | 55/55 屏通过；销售 Desk 3/3；清洁检查 pass=true、Translation/GL/SLE=0、科目 266、底稿表存在；基准 `20261010_232619` 已保留 | ✅通过 |
| 15 | TS-015 全量与常驻文件 | E 复跑 `bench --site test.localhost run-tests --app frappe_china`：240 integration + 2 导航=242/242、0 跳过；上游六 app 工作树 clean | ✅通过 |

## 验收条件复核

SL-001～009 的任务证据均正向；SL-010 的逐屏、清洁、销售闭环、独立前端、模板探针及全量回归均有证据。`screens-forms-v10/result.json` 为 55/55 `pass=true`。首页与三个原有侧栏屏的 `sidebar_title` 分别是 `Stock`、`Accounts Setup`、`Stock`、`CRM`，属于方案要求保留的原有入口；其余屏为 `Business Flow`。

## 复核中发现并修清

首次直接运行 `test_desk_titles.cjs` 时，6 个用例因测试 VM 未提供浏览器原生 `MutationObserver` 在初始化阶段失败。该问题是测试夹具缺失；已在 `frappe_china/tests/test_desk_titles.cjs` 增加最小 `observe()` stub，随后同一命令 6/6 通过。其他 Node focused 结果：独立前端 10/10、开账 8/8、导航守卫 5/5。

## 复核建议与边界

1. 销售闭环的制造辅助成本行由演示数据脚本补入公司默认成本科目和成本中心，未改 frappe/erpnext；这证明本轮演示数据可提交，不等于上游 helper 默认行为已改变。
2. TS-013 例 2 按方案明确引用 LG-073；例 6 为演示站只读验证。
3. 独立前端撤钩记录是判别力反证；后续官方 bundle 升级后应重新跑模板与撤钩反证。
4. 清洁检查只证明当前演示站基准为空及结构完整；销售闭环备份 `20261011_002831` 供回溯。
5. 译名、装序与清洁复核结果分别为“译名自检通过”、`order_ok=true`、`clean-check.pass=true`。

## 全量回归

E 期间独立重跑：`Ran 240 tests in 1895.178s ... OK`，随后 2 个导航测试 `OK`；合计 242/242 通过、0 跳过。

## 总体结论

**状态值：全部通过**。15 个任务均逐项落地，方案验收条件均有证据，无 IT-001 等未通过项；下一步按 Workflow 出口进入 F 审核，不在本 E 步直接执行 F。
