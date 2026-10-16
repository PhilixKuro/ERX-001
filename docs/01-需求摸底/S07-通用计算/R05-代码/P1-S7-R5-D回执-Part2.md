# P1-S7-R5 D回执·Part2

**日期**：2026-10-15 开工，2026-10-16 续跑｜**执行者**：Codex｜**打tag**：否
**依据**：[R04 开发方案总纲](../R04-开发方案/P1-S7-R4-C开发方案-总纲.md)及 [Part2](../R04-开发方案/P1-S7-R4-C开发方案-Part2.md)
**Spec**：`D-code-plannedDev-build.md`；回执按 `bricks/receipt.md`。

## 逐项执行结果

| 任务 | 对应切片 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-010 批次系数 | SL-006 | `frappe_china/production/batch_uom.py:8`、`frappe_china/public/js/batch_uom.js:1`、`frappe_china/hooks.py`、`frappe_china/fixtures/custom_field.json`、`frappe_china/translations/zh.csv`、`frappe_china/README.md` | ✅完成 | 2026-10-16 | Python 3/3、Node 定向 1/1；采购收货表单同单两批次与交换批次均正确，截图见验证表。续跑全量 Python 328/328、Node 87/87 及译名检查通过。 |
| TS-011 拆单覆盖 | SL-007 | `frappe_china/production/job_card_split.py:15`、`frappe_china/tests/test_job_card_split.py:12`、`frappe_china/hooks.py`、`frappe_china/README.md`「后端覆盖登记」 | ✅完成 | 2026-10-16 | 拆分数量、工时保留、两条建卡路径、重复工序按同一 BOM 映射及 hooks 已实现；初版定向 8/8，全量内含续跑补测后 9/9；日志修复、上游哈希守卫及译名检查通过。 |
| TS-012 工序间数量传递 | SL-008 | `production/operation_flow.py::realign`、`::sync_operation_loss`、`tests/test_operation_flow.py::TestOperationFlow`、`hooks.py`、`translations/zh.csv`、`README.md`「已知限制」 | ✅完成（用户裁决 A 路线） | 2026-10-16 | 级联、取消恢复、已开工卡保护与差异提示沿用原代码。新增 `sync_operation_loss`：某道工序的卡全部提交后，把「工单数量 − 本道卡数量合计」作为上道累计损耗，并入该道 `Work Order Operation.process_loss_qty`。Manufacture 按工单数量入库：950 场景下 1000／50 → 成品 950、Completed；多道损耗场景 1000／70 → 成品 930、Completed。定向 6/6 通过。 |
| TS-013 计件汇总单与 Additional Salary | SL-009 | `production/piece_rate.py`、`production_plus/doctype/piece_rate_summary/`、`piece_rate_summary_item/`、`tests/test_piece_rate.py`、安装及迁移 hooks | ✅完成 | 2026-10-16 | 真实工单与报工行汇总 1190；生成、幂等、取消附加薪资及员工失败隔离通过；最终全量 342/342、Node 89/89，详见 Part3。 |

## 全量验证

**TS-012 完成后的全量（2026-10-16）**：Python **344/344**，其中 336 integration（1801.927s）、5 old category（0.250s）、3 math（0.005s），均 OK、退出 0，日志 `frappe-bench/logs/s7-r5-ts012-full.log`。比 Part3 的 342 少 1 条旧用例 `test_manufacture_native_loss_semantics_remains_pending`、多 3 条新用例。Ruff check 通过、format --check 160 文件通过。本次只改 Python 与 README，未改 JS／csv，故未重跑 Node 与 `translation_check.run`，沿用 Part3 的 89/89 与两站自检结果；全量内的译名质量与翻译测试照常通过。

下表为 TS-010／TS-011 完成时、TS-012 实现前的验证基线，不能视为包含当前 TS-012 代码的全量回归。

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
| TS-012 | `tests/test_operation_flow.py`：SL-008 ①～⑥；⑤ 三道走完后建 `Manufacture` 提交、断言工单 `status`；HT-012 结论写进 D 回执。 | 先跑 SA 探针 `Spike/P1S7R5-D/ht012b-probe.py`（测试站，回滚后残留 0），再改测试：去掉原生失败证据用例，新增三条——单道损耗入库、多道累计损耗入库、后道卡取消后工序行复原。不带 `sync_operation_loss` 时新增三条均红（工序行停在 950＋0／Work in Progress），带上后 6/6 绿。不绕过原生校验。 | 探针两例 go，输出 `ht012b-probe.log`。定向 6/6（11.976s）：①②④ 级联沿用；⑤ 三道各 950，工序行均为 950＋50／Completed，入库 1000／50，成品 950，工单 produced 950、loss 50、Completed；多道场景卷簧 950＋50、热处理 930＋20、磨端 930，工序行 50／70／70，入库 1000／70，成品 930、Completed；后道卡取消后该工序行回到 0＋0／Pending。HT-012：原命题（950／50 入库）no-go，改按工单数量入库并补写工序行损耗后成立。 |
| TS-013 | SL-009 ①～⑦：真实员工、薪资结构分配、两张工单与报工行；无分配员工独立失败。 | `bench --site test.localhost run-tests --module frappe_china.tests.test_piece_rate`；首次缺模块为红，落地后定向复验。 | 4/4、12.861s，日志 `frappe-bench/logs/s7-r5-ts013-green.log`。950×0.2＋10000×0.1＝1190；BOM 优先、Operation 回退、草稿不计、无单价拒绝零额提交、重复跳过、取消联动及 Guest 权限通过。后补同期间草稿不阻生成／重复提交拒绝断言，纳入最终全量。 |

## TS-012 暂停时验证

- 定向测试命令：`docker compose -f docker/compose.yaml exec -T -w /workspace/frappe-bench frappe bench --site test.localhost run-tests --module frappe_china.tests.test_operation_flow`。
- Manufacture 事实：`1000/50` 抛 `OperationsNotCompleteError`；`950/0` 被原生带入损耗 50，成品 900，工单 `produced_qty=900`、`process_loss_qty=50`、`In Process`，工序行状态为 Completed / Work in Progress / Work in Progress。
- 定向测试 4/4 通过（10.877s，退出 0），日志：`frappe-bench/logs/s7-r5-ts012-native-evidence.log`；固定证据说明：`Spike/P1S7R5-D/ts012-native-evidence.md`。本次修改的 Python 三文件 Ruff check／format --check 均通过。当时尚未跑包含 TS-012 的全量；后续 TS-017 全量 342/342 已包含这些事实断言（见 Part3），仍不宣称 TS-012 功能验收完成。
- CSV 修改后清缓存，测试站 `translation_check.run` 通过。翻译模块首跑 19/20，新增提示词追加在表尾导致 `test_csv_sorted` 失败；已将该行移到全表正确排序位置，复跑 **20/20 通过**（10.793s，退出 0）。原失败日志保留在 `frappe-bench/logs/s7-r5-ts012-translations.log`，复跑日志为 `s7-r5-ts012-translations-recheck.log`。

## 偏离与暂停

- **TS-012 恢复（2026-10-16，执行者 Claude）**：用户在 [D 讨论记录第 7 步](P1-S7-R5-D讨论记录.md)选 A，即补写工单工序行的累计上道损耗。与方案的差异有两处：① SL-008 ⑤ 原文是「生产入库 950（带损耗 50）」，实际入库填工单数量 1000、损耗 50，成品 950，达到原文要的成品数与 Completed；② 新增 `sync_operation_loss`，方案无此函数，经用户裁决加入。开了 `track_semi_finished_goods` 的工单不补写。以下两段为恢复前的历史记录，保留不删。
- TS-012 的独立 SA 已完成：HT-011 go；原始 HT-012 的 `950/50` 得到成品 900、工单 `In Process`。随后选择的 `1000/50` 在级联后的第二、三道工序处被原生校验拒绝（完工 950＋损耗 0＜1000），该验收假设被否证。用户最新裁决：保留原生语义，暂停 Manufacture 验收，保留级联代码与失败证据，重新确定验收口径。详见 [D 讨论记录第 2 步](P1-S7-R5-D讨论记录.md)。
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
| （无）| TS-012 已于 2026-10-16 按 A 路线完成；损耗率按工序算是新需求，不属方案任务，登记 `SH-P1S7007` 并入 S8 |

## 状态值

- `代码已落地`（2026-10-16 更新）——TS-012 已按用户裁决的 A 路线完成，SL-008 ①～⑥ 均有断言；TS-010～013 已完成；全量 344/344。此前的 `无法实现` 仅针对旧验收口径，已由 D 讨论记录第 7 步取代。

## 复核建议

- TS-011 对应规则：对照方案 `_bom_operation_split_qty`，重点复核同一 BOM 内同 operation 第 k 次出现，跨 BOM 不共享计数。测试位置 `tests/test_job_card_split.py::test_repeated_operation_mapping_is_scoped_to_the_same_bom`。
- 两条建卡路径中 make_job_card 当前测试直接调用后端入口，未做工单表单点击验收；HTTP／后台补丁的 hooks 注册有断言，实际重装由 Work Order before_submit 测试覆盖。
- **TS-012 的判断空间最大处**是 `sync_operation_loss` 的损耗口径：工序行损耗＝本道卡损耗＋（工单数量 − 本道卡数量合计）。原生入库取各行损耗的最大值，所以必须写累计值；只补上一道的话，多道损耗场景会多记成品。查法：读 `operation_flow.py::sync_operation_loss`，对照 `stock_entry.py:3343 get_pending_process_loss_qty` 与 `:1165 check_if_operations_completed`，再用测试 `test_manufacture_books_cumulative_loss_of_several_operations` 的 950＋50／930＋20 走一遍。
- **测试最薄处**：
  - 拆单场景（第二道 4 张卡）下的补写只有级联断言，没有入库断言；补写要等该工序所有卡都提交，逻辑相同但没专测。
  - 已开工卡不改数量时，补写的上道损耗为 0、原生仍要工人手填，这条路径没测。
  - 原生在 job card 提交时重算工序行，我们紧随其后补写，依赖 `doc_events` 晚于原生 `on_submit` 执行，测试间接覆盖了这一点。
- **与方案的偏离**：SL-008 ⑤ 的入库输入由 `950/50` 改为工单数量 `1000/50`；`sync_operation_loss` 是方案外新增，均经用户裁决（D 讨论记录第 4～7 步）。
- **演示站**：改动只涉及 Python，没有 schema 变化，不需要 migrate。演示站运行中的 worker 要重启 `bench start` 才会加载新代码，本次没有重启。
- TS-013 的单价映射沿用 TS-011 同 BOM、同工序第 k 次出现的对应规则；重点对照 `piece_rate._rate`。员工失败按 savepoint 回滚，批量入口核心不 commit；列表白名单入口检查角色后提交。取消实测经原生回链检查通过，未加 `ignore_links`。

## 更正（P1-S7-R7 F 审核 FD-013，2026-10-17 补记）

上方验证表 TS-010 行「浏览器临时数据、6787 服务及 hosts 标记已清」不完整：`ts010-ui.cjs` 的首版连的是 `test.localhost:8000`，而 8000 只服务演示站，故在 `erx.localhost` 建过物料 `_FCT_TS010_UI_1792088513074` 与两个批次，并留下 45 条请求失败的 Error Log。这些在 [Part3 回执](P1-S7-R5-D回执-Part3.md) TS-017 收尾时才清掉。演示站现已干净（R7 F 片 3 只读核实）。`ts010-ui.cjs` 已补「写之前断言 `frappe.boot.sitename`」。
