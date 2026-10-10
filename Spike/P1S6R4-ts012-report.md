# P1-S6-R4 TS-012：开账凭证跳转复核

测试站 `test.localhost` 上用 `Spike/P1S6R4-ts012-data.py` 创建并提交一张 `is_opening=Yes` 日记账凭证和一张普通日记账凭证，浏览器确认两张表单均出现「会计凭证」入口，且期初凭证的表单数据为 `is_opening=Yes`、分录借贷各 100 元。脚本随后取消凭证、清理本次 GL 行、删除单据和公司，`cleanup_verified=true`。

当前证据边界：按钮存在已取证；浏览器脚本尚未稳定点击 Frappe 的「查看」下拉菜单并读取最终 `frappe.route_options`，因此不能声称 TS-012 的开账／普通凭证跳转条件已经通过。库存调账路径因测试站没有库存调账数据，本轮未伪造实测。

可重跑数据准备与清理：

```powershell
@(Get-Content Spike\P1S6R4-ts012-data.py; 'main("prepare")') | docker exec -i erx001-frappe-1 bash -lc 'cd /workspace/frappe-bench && env/bin/python -'
@(Get-Content Spike\P1S6R4-ts012-data.py; 'main("cleanup")') | docker exec -i erx001-frappe-1 bash -lc 'cd /workspace/frappe-bench && env/bin/python -'
```
