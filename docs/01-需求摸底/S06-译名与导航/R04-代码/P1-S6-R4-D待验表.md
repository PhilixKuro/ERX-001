# P1-S6-R4 D待验表

依据：开发方案总纲 HT-006；Spec：SA-probe-plannedDev-spike.md。

| 编号 | 命题 | 判定标准 | 探针 | 结果 | 阻塞 |
|---|---|---|---|---|---|
| HT-006 | 补丁能改表名与子表 parenttype，并由新 controller 打开原记录；重复运行无改动 | 旧表消失、新表含原记录与一行子表；parenttype 新名；重复执行成功 | Spike/P1S6R4-rename-probe.py prepare → migrate → verify | go：原记录 1 行、新表 1 行、旧表不存在、child parenttype=Cash Flow Worksheet、controller=CashFlowWorksheet、重复执行成功；明细 Spike/P1S6R4-rename-probe.json | 已解除 |

## 复核建议

本探针只验证测试站的一条草稿底稿及一个 Cash Flow Item；新安装路径由补丁单元反证覆盖，不据此声称全新安装实测通过。
