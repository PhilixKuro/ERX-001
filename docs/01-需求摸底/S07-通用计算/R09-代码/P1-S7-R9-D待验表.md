# P1-S7-R9-D待验表

日期：2026-10-17。依据：D Spec、R8 TS-020 及用户批准的原料展开后分仓方案。

| 编号 | 待验命题 | 阻塞否 | 判定 | 实际观察 | 探针代码 |
|---|---|---|---|---|---|
| V-01 | 原生 `get_exploded_items` 可取得公司原料默认仓与库存单位需求量；将原料作为无BOM输入按仓分别调用原生请购计算，可保留不同默认仓、数量和采购单位换算 | 阻塞 | go | 未分组时A/B/C均落Stores；分组后A=Stores、5箱×2=10件，B=Work In Progress、15件；C无默认仓可识别并排除。回滚后物料0。另真实销售订单集成5/5通过 | `Spike/P1S7R9-D/native_warehouse.py` |

执行说明：前段实现已先于探针，违反先验后写，详见D回执。本次由当前执行者在独立进程补做探针，未新开SA Session；不声称满足SA独立Session要求。探针不调用自有 `order_proposals`，只检验原生API假设，执行完回D继续。

复跑：`docker compose -f docker/compose.yaml exec -T -w /workspace/frappe-bench/sites frappe /workspace/frappe-bench/env/bin/python /workspace/Spike/P1S7R9-D/native_warehouse.py`。初次在错误工作目录启动时因`/workspace/logs/cssutils.log`不存在而退出，未连接数据库；改用sites工作目录后通过。该目录是Frappe logger的相对路径约定，不涉及更改上游。

## 复核建议

探针只覆盖一个真实BOM、两仓及采购单位换算；不代表100种原料、10仓时的性能。复跑 `Spike/P1S7R9-D/native_warehouse.py`，核对原生未分组与分组结果的仓库差异、quantity×conversion_factor及回滚后物料数。
