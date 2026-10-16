# TS-012 原生 Manufacture 失败证据

日期：2026-10-16。站点：仅 `test.localhost`。

用户最新裁决：保留原生语义，暂停 TS-012 Manufacture 验收，保留级联代码与失败证据，重新确定验收口径。

## 可复现输入与结果

工单数量 1000，三道工序。首道 Job Card 完工 950、损耗 50；提交后由 `operation_flow.py` 将第二、三道未开工卡的数量级联到 950。后两道各完工 950、损耗 0。

| Manufacture 输入 | 原生实际结果 |
|---|---|
| `fg_completed_qty=1000`、`process_loss_qty=50` | 插入／提交路径抛 `OperationsNotCompleteError`，未形成已提交入库；后两道的 950＋0 小于原生要求的 1000 |
| `fg_completed_qty=950`、`process_loss_qty=0` | 原生带入待计损耗 50；提交后成品行数量 900，工单 produced_qty=900、process_loss_qty=50、status=In Process |

第二行提交后，Work Order Operation 状态依序为 `Completed / Work in Progress / Work in Progress`。原始独立 SA 的 `950/50` 同样得到成品 900、工单 In Process，见 `ht012-probe.py` 与 `ht012-probe.log`。

## 自动化证据

测试：`frappe_china/tests/test_operation_flow.py::TestOperationFlow.test_manufacture_native_loss_semantics_remains_pending`。

该用例通过真实工单／任务单／库存凭证调用原生接口，断言上述异常、成品数量、损耗、工单及工序状态；拒绝路径使用 savepoint 回滚，未 mock 或跳过原生校验。

在项目根运行：

```powershell
docker compose -f docker/compose.yaml exec -T -w /workspace/frappe-bench frappe bench --site test.localhost run-tests --module frappe_china.tests.test_operation_flow
```

本次实跑 4/4，10.877s，退出 0。另三项覆盖未开工卡数量／工时／物料／排程调整、已开工卡保留与差异提示、拆单末卡调整和取消恢复。运行日志：`frappe-bench/logs/s7-r5-ts012-native-evidence.log`。

测试通过表示当前事实可复现，不表示“成品 950、工单 Completed”验收通过。TS-012 尚未完成，未跑包含该实现的全量回归；TS-013～017 等待验收口径重定。

## 原生读取端

- `erpnext/stock/doctype/stock_entry/stock_entry.py::check_if_operations_completed`：按每道工序完工量＋损耗校验 Manufacture 请求数量。
- 同文件 `set_process_loss_qty`、`get_pending_process_loss_qty`：带入原生待计损耗。
- `erpnext/manufacturing/doctype/work_order/work_order.py::get_status`、`update_operation_status`：原生工单与工序完成状态判定。
