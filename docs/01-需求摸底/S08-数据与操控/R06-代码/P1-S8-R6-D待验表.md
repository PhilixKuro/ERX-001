# P1-S8-R6 D 待验表

**日期**：2026-10-22｜**唤起方**：R6 D｜**依据**：R5开发方案总纲§六、§十。

| 编号 | 待验命题 | 阻塞否 | 判定 | 实际观察 | 探针代码 |
|---|---|---|---|---|---|
| HT-014 | 草稿工序卡仅写scheduled_time_logs可重叠保存，仍为Open，expected_start_date和time_required由排程得出 | 不阻塞 | go | test_targets.py::test_ht014_scheduled_only_cards_allow_overlap_and_remain_open真实提交订单/工单后给两张草稿卡相同起点，无实际时间行；s8-ts016-targets-final2.log 5/5含此项。第三段实际复产尚待验证。 | 开发方案指定测试；s8-ts016-targets-final2.log |
| HT-015／LG-002 | 换库后60秒内新任务、排队任务及在途任务读写哪个库；scheduler关闭、A6分离克隆、A7生成期间不换库及删除Redis目标库前缀键的规避是否成立 | 阻塞TS-021 | go | 2026-10-23新Session在独立站s8ht015.localhost、两份s8dev克隆库A/B实测：换库后5.54秒新RQ任务读写B；换前排队、换后执行的fork任务在12.58秒读写B；换前已开始任务在6.44秒仍读写A；62秒后fork/nofork新任务均读写B。同一scheduler进程在换后5.58秒、67.68秒的tick及其原生Scheduled Job均读写B。当前版本后台init不启用Web请求60秒配置缓存。在途任务仍用旧连接。Redis目标库原始值7，不删目标前缀时独立进程get_cached_doc仍得旧值4；删18个目标键后即剩0键，新进程读7。A6分离子进程启动后0.010秒切到B，32.96秒后仍从显式源A克隆完成、目标标记A。A7基线两种worker不换库均读写A。 | Spike/P1S8R6-SA/run_ht015.py、ht015_probe.py、redis_ht015.py、detached_ht015.py；定长证据Spike/P1S8R6-SA/evidence/；原日志frappe-bench/logs/ht015-*.log |
| HT-023 | 原生制造入库mapper及Stock Entry浮点比较，是否会拒绝累计工序损耗后的合法数量 | 阻塞TS-016第7幕验收及TS-017 | go | 整链日志观察值：fg_completed_qty=2061.86、成品行1993.86、process_loss_qty=68.00000000000023。test.localhost无写库探针调用原生`validate_fg_completed_qty`：库存精度2；原生重算仍得68.00000000000023，舍入后相加在Python float中为2061.8599999999997，与2061.86不等，原生校验拒绝。确认根因是精确浮点相等检查。整链失败日志`frappe-bench/logs/s8-ts016-targets-boundary-green.log`；探针输出`frappe-bench/logs/s8-ht023-probe.log`。 | `frappe_debug/spike/ht023_stock_entry_loss.py`（bench execute；test.localhost；rollback） |

## 复核建议

HT-014证据只证明原生草稿排程行为，实际工序报工仍须按SlotAllocator避免重叠。HT-023已确认原生精确浮点比较会拒绝该两位数量组合；探针只隔离确认原生校验，没有验证可接受的业务落地处理。

HT-015最需复核的是在途任务边界：go依赖方案的演示期scheduler关闭、A6克隆不经RQ、A7生成期间不换库；本探针明确观察到已开始作业继续写A，未证明任意在途业务任务都能安全跨库。复核可在新建隔离站重跑run_ht015.py的inflight阶段；Redis复核跑redis_ht015.py，4与7取不同值以区分缓存和数据库。scheduler探针只将队列传输重定向到专属队列、将tick限定到本探针站点，原生单站初始化、调度筛选、ScheduledJobType.enqueue及run_scheduled_job执行链均实跑；未启动遍历所有站点的全局scheduler。没有无法判定项。
