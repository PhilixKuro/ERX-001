# P1-S8-R6 D 待验表

**日期**：2026-10-22｜**唤起方**：R6 D｜**依据**：R5开发方案总纲§六、§十。

| 编号 | 待验命题 | 阻塞否 | 判定 | 实际观察 | 探针代码 |
|---|---|---|---|---|---|
| HT-014 | 草稿工序卡仅写scheduled_time_logs可重叠保存，仍为Open，expected_start_date和time_required由排程得出 | 不阻塞 | go | test_targets.py::test_ht014_scheduled_only_cards_allow_overlap_and_remain_open真实提交订单/工单后给两张草稿卡相同起点，无实际时间行；s8-ts016-targets-final2.log 5/5含此项。第三段实际复产尚待验证。 | 开发方案指定测试；s8-ts016-targets-final2.log |
| HT-015／LG-002 | 换库后worker/scheduler缓存站点配置的行为与规避是否成立 | 阻塞TS-021 | 待验 | 尚未启动，不以单测代替换库实机证据；沿用R5总纲要求。 | 新Session的SA探针，尚未执行 |
| HT-023 | 原生制造入库mapper及Stock Entry浮点比较，是否会拒绝累计工序损耗后的合法数量 | 阻塞TS-016第7幕验收及TS-017 | go | 整链日志观察值：fg_completed_qty=2061.86、成品行1993.86、process_loss_qty=68.00000000000023。test.localhost无写库探针调用原生`validate_fg_completed_qty`：库存精度2；原生重算仍得68.00000000000023，舍入后相加在Python float中为2061.8599999999997，与2061.86不等，原生校验拒绝。确认根因是精确浮点相等检查。整链失败日志`frappe-bench/logs/s8-ts016-targets-boundary-green.log`；探针输出`frappe-bench/logs/s8-ht023-probe.log`。 | `frappe_debug/spike/ht023_stock_entry_loss.py`（bench execute；test.localhost；rollback） |

## 复核建议

HT-014证据只证明原生草稿排程行为，实际工序报工仍须按SlotAllocator避免重叠。HT-023已确认原生精确浮点比较会拒绝该两位数量组合；探针只隔离确认原生校验，没有验证可接受的业务落地处理。HT-015须在TS-021开写前由SA新Session填回，不能把本表的存在当作已验证。
