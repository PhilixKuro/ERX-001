# P1-S7-R5 D回执·Part2

**日期**：2026-10-15 开工，2026-10-16 续跑｜**执行者**：Codex｜**打tag**：否
**依据**：[R04 开发方案总纲](../R04-开发方案/P1-S7-R4-C开发方案-总纲.md)及 [Part2](../R04-开发方案/P1-S7-R4-C开发方案-Part2.md)
**Spec**：`D-code-plannedDev-build.md`；回执按 `bricks/receipt.md`。

## 逐项执行结果

| 任务 | 对应切片 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-010 批次系数 | SL-006 | `frappe_china/production/batch_uom.py:8`、`frappe_china/public/js/batch_uom.js:1`、`frappe_china/hooks.py`、`frappe_china/fixtures/custom_field.json`、`frappe_china/translations/zh.csv`、`frappe_china/README.md` | ✅完成 | 2026-10-16 | Python 3/3、Node 定向 1/1；采购收货表单同单两批次与交换批次均正确，截图见验证表。续跑全量 Python 328/328、Node 87/87 及译名检查通过。 |
| TS-011 拆单覆盖 | SL-007 | `frappe_china/production/job_card_split.py:15`、`frappe_china/tests/test_job_card_split.py:12`、`frappe_china/hooks.py`、`frappe_china/README.md`「后端覆盖登记」 | ✅完成 | 2026-10-16 | 拆分数量、工时保留、两条建卡路径、重复工序按同一 BOM 映射及 hooks 已实现；初版定向 8/8，全量内含续跑补测后 9/9；日志修复、上游哈希守卫及译名检查通过。 |
| TS-012 工序间数量传递 | SL-008 | — | ⏸暂停待裁决 | 2026-10-16 | SA 验证 HT-011 为 go、HT-012 为有效 no-go；指定 Manufacture 输入下工单仍 In Process。按 D 纪律暂停反馈，不先写测试或生产代码。 |
| TS-013 计件汇总单与 Additional Salary | SL-009 | — | ⬜未开始 | — | — |

## 全量验证

| 门 | 结果 |
|---|---|
| TS-010 定向测试 | Python 3/3、Node 1/1 通过；表单同单两批次系数 0.005 / 0.006，库存数量 0.05 / 0.06，交换批次仍正确 |
| TS-011 定向测试 | 初版 8/8；续跑新增日志分支测试先红（两种场景失败），修正 `log_error` 的 title/message 后，全量内 9/9 通过 |
| Python 全量 | 328/328：323 integration（1787.009s）＋5 old-frappe-test-class-category（0.251s），均 OK、退出 0。TS-001 基线 283 项按类名＋用例名逐项比对，缺失 0、新增 45。日志 `frappe-bench/logs/s7-r5-part2-python-full.log` |
| 译名 | 本轮全量含质量 13/13、翻译 20/20；全量结束后测试站 `translation_check.run` 再验通过。TS-010 已留两站只读自检通过结果 |
| Ruff / Node / 差异检查 | app 全量 Ruff check 0、format --check 143 文件通过；Node 87/87（基线86）；根与 app diff --check 通过 |

Part1 的旧测试在中文上下文断言英文 `Manually specified`，首轮全量发现后中断；仅将测试期望修为已定译名「手动指定」，定向复验 8/8，再从头完整跑出上述 328/328。首轮输出保留在 `frappe-bench/logs/s7-r5-part2-python-initial-red.log`，定向复验见 `s7-r5-part2-bom-selection-recheck.log`。Node 输出见 `s7-r5-part2-node-full.log`。

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-010 | `tests/test_batch_uom.py`：SL-006 ①～④、⑥；SL-006 ⑤：测试站采购收货表单选两个批次并截图。 | 三类单据草稿 insert/save；Node 模拟前端 handler；测试站真实采购收货表单选两批次并交换。 | Python 3/3、Node 1/1；系数 0.005 / 0.006、库存数量 0.05 / 0.06。证据：`Spike/P1S7R5-D/ts010-ui.cjs`、`ts010-ui-result.json`、`ts010-purchase-receipt-batch-factors.png`。浏览器临时数据、6787 服务及 hosts 标记已清。 |
| TS-011 | `tests/test_job_card_split.py`：SL-007 ①～⑤，工单提交与 make_job_card 两条路径；上游源码哈希守卫。 | 真实工单/BOM 提交；直接调用 make_job_card；模拟补丁被还原后经 before_submit 重装；跨 BOM 同名工序映射测试；日志兜底分支补测。 | 全量内 9/9。10000→1 张/4000 分；2500→4 张/各1000 分；3000→3000×3+1000/1200×3+400 分；未勾选为原生 1 张/400000 分。守卫 SHA256 `a1ef469cb702d0a2dc923f8911d0e3a17f4144af157b5035a466bb159ab4870b`。 |

## 偏离与暂停

- TS-012 的独立 SA 已完成：HT-011 go，HT-012 有效 no-go。以 `fg_completed_qty=950`、`process_loss_qty=50` 提交 Manufacture 后，原生生成成品数量 900，工单保持 `In Process`（工单数量 1000）。按 D 纪律暂停并反馈用户裁决；未写 TS-012 测试或生产代码。
- TS-010 前端采用追加子表字段 handler，调用 `frappe.model.set_value` 后交由原生 conversion_factor handler 重算；未替换原生 handler。
- 补跑前发现 `tests/translation_whitelist.py` 的既有新增行单引号不满足 Ruff 格式要求，已仅格式化该文件；全量发现 Part1 的 TS-005 测试按英文断言中文注释，已定向复现（注释实际含「手动指定」），修正测试期望文字，不改生产行为。
- 本次完整全量是在 TS-010／TS-011 均已实现后补跑，覆盖当前两个切片；未做到总纲 §十要求的「每个切片完成当场各跑一次全量」，不将本次补验记为历史上已逐切片执行。

## 新增约定

| 约定 | 类别（命名/位置/错误处理/依赖/跨层调用） | 在哪个任务确立 |
|---|---|---|
| 无新增工程约定；文件位置、BOM 工序映射、错误兜底及 hooks 均沿用方案 | — | TS-010／TS-011 完成前复查 |

## 未做项

| 项 | 为什么没做 |
|---|---|
| TS-012 | HT-012 no-go：指定 Manufacture 输入无法满足“工单 Completed”验收，等待用户裁决 |
| TS-013 | 按方案任务顺序，待 TS-012 后继续 |

## 状态值

- `无法实现`——TS-010／TS-011 实现及补验已完成；TS-012 的 HT-012 在原生口径下为 no-go，按 D 纪律暂停反馈用户，等待对方案受影响部分的裁决；TS-012～017 尚未落地。

## 复核建议

- TS-011 对应规则：对照方案 `_bom_operation_split_qty`，重点复核同一 BOM 内同 operation 第 k 次出现，跨 BOM 不共享计数。测试位置 `tests/test_job_card_split.py::test_repeated_operation_mapping_is_scoped_to_the_same_bom`。
- 两条建卡路径中 make_job_card 当前测试直接调用后端入口，未做工单表单点击验收；HTTP／后台补丁的 hooks 注册有断言，实际重装由 Work Order before_submit 测试覆盖。
- TS-012 尚未落地。独立 SA 已覆盖三道工序校验和 Manufacture 提交后的工单、工序状态；HT-012 的原生数量口径及 no-go 证据见 D 待验表，未裁决前不按原方案继续编码。
