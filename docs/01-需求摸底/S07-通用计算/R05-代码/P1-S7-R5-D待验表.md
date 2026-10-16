# P1-S7-R5 D待验表

| 编号 | 对应任务 | 技术假设 | 验证方式 | 判定 | 证据 |
|---|---|---|---|---|---|
| HT-001 | TS-001 | Ruff 0.14.10 可装入 bench 环境，bench setup requirements --python 后仍可运行 | 实装、重装依赖、复查版本 | go | pip 实装成功；`bench setup requirements --python` 退出 0；重装后 `env/bin/ruff --version` 输出 `ruff 0.14.10`。完整输出在 `frappe-bench/logs/s7-r5-requirements.log` |

该事实验证在本轮容器中执行；不依赖此结果的工作先记录现有测试基线。

## TS-012 → SA 交接（2026-10-16）

**唤起方**：P1-S7-R5 D，`需要事实验证`；D 未结束。按 `play-spike.md` 在独立 Session 执行，完成后填回下表，再回 D 续 TS-012。

| 编号 | 待验命题 | 阻塞否 | 判定 | 实际观察 | 探针代码 |
|---|---|---|---|---|---|
| V-01（HT-011） | 三工序 1000 支工单，首道卡按 950 完工＋50 损耗提交后，经 `frappe.db.set_value` 将第二道卡 `for_quantity` 从 1000 改为 950，重新读取后按 950 完工、零损耗提交，是否同时通过原生数量校验和前后序校验 | 阻塞 TS-012 | go | 实跑三张原生 Job Card，sequence_id 为 1/2/3，初始 `for_quantity` 均 1000。未完成首道时提交第二道，原生抛 `OperationSequenceError`；首道提交后 `total_completed_qty=950`、`process_loss_qty=50`、docstatus=1。对第二道执行 `frappe.db.set_value` 将数量从 1000 改为 950，重新读取为 950；提交后 `total_completed_qty=950`、`process_loss_qty=0`、docstatus=1，Job Card status 为 Completed。工单 status=`In Process`；三工序行状态依序 Completed / Work in Progress / Pending。 | `Spike/P1S7R5-D/ht011-probe.py`；实际输出 `Spike/P1S7R5-D/ht011-probe.log` |
| V-02（HT-012） | 三工序 1000 支工单，首道 950 完工＋50 损耗、第二与第三道改量后各 950 完工且零损耗，Manufacture 库存凭证以 `fg_completed_qty=950`、`process_loss_qty=50` 提交，是否成功且工单 `status=Completed`；同时记录三道工序状态 | 阻塞 TS-012 | no-go | 三张卡均原生提交成功：首道 950 完工＋50 损耗，第二、三道各 950 完工＋0 损耗。Manufacture 凭证以 `fg_completed_qty=950`、`process_loss_qty=50` 提交成功（docstatus=1）；原生生成 finished-good 行 qty=900。提交后工单 `produced_qty=900`、`process_loss_qty=50`、qty=1000、status=`In Process`；三工序行状态为 Completed / Work in Progress / Work in Progress。工单未到 Completed，命题不成立。 | `Spike/P1S7R5-D/ht012-probe.py`；实际输出 `Spike/P1S7R5-D/ht012-probe.log` |

### 前次用户裁决（2026-10-16，后续验证已否证其验收假设）

用户当时选择改验收输入、保持 ERPNext 原生生产语义：TS-012 的 Manufacture 验收改为 `fg_completed_qty=1000`、`process_loss_qty=50`。当时预期原生生成 finished-good 数量 950，并以 `produced_qty + process_loss_qty >= qty` 将工单置为 `Completed`；但后续实跑在原生工序校验处先被拒绝，该预期未成立，以后续暂停裁决为准。HT-012 的原始 `950/50` no-go 作为事实证据保留。

### 后续裁决（2026-10-16）

实现并复跑后发现，`1000/50` 在 Manufacture 提交前即被原生 `check_if_operations_completed()` 拒绝：数量级联后的第二、三道工序均为完工 950、损耗 0，不能满足每道工序的 1000 校验。为保留原生语义，用户裁决暂停 TS-012 的 Manufacture 验收，保留级联代码与失败证据，重新确定验收口径。定向测试 4/4 通过（10.877s，退出 0），Manufacture 用例断言 `1000/50` 抛 `OperationsNotCompleteError`，以及原生 `950/0 → 成品900、produced_qty=900、process_loss_qty=50、status=In Process`；这不是成品 950／工单 Completed 的验收通过。固定说明见 `Spike/P1S7R5-D/ts012-native-evidence.md`，运行日志见 `frappe-bench/logs/s7-r5-ts012-native-evidence.log`，原始探针证据仍见 `Spike/P1S7R5-D/ht012-probe.log`。

### 执行入口与边界

- 先读 `CLAUDE.md`、`docs/流程体系/workflows/plannedDev/SA-probe-plannedDev-spike.md`、`plays/play-spike.md`、`bricks/spike.md`、`交接契约.md`、`docs/开发守则.md`。
- 依据：`R04-开发方案/P1-S7-R4-C开发方案-Part2.md` 的 TS-012 与总纲 HT-011／HT-012；不改方案、不改生产码；一个探针一个命题，留在 `Spike/P1S7R5-D/`。
- 只写 `test.localhost`，不写 `erx.localhost`。不得 import `erpnext.tests.utils`。现有 `TestJobCardSplit._make_work_order` 仅单道，不足以直接回答这两条命题。
- 探针必须用 `try/finally: frappe.db.rollback()`，以防 bench execute 成功路径自动 commit；子表用 `doc.append`，不可直接赋 dict 列表。Error Log 非事务，若产生记录只能正向限定自己的记录清理。
- 输出须包含卡的原／改后数量、完工与损耗、docstatus、工序 sequence_id、工单及各工序状态；须证明前后序校验启用，不用 mock 或 flags 绕过。
- 命令入口（工作目录 `docker/`）：`docker compose exec -T frappe bench --site test.localhost execute "exec(open('/workspace/Spike/P1S7R5-D/ht011-probe.py', encoding='utf-8').read(), globals())"`；HT-012 独立运行 `ht012-probe.py`，两次实跑输出分别保存在对应 `.log` 文件。公共造数/快照函数在 `Spike/P1S7R5-D/ts012-probe-common.py`。
- 填回判定后 D 继续：两个 go → TS-012 先红后绿；任一 no-go → 按方案「不成立时」暂停反馈；探针构造错误仅属待验，修正后重跑。

### 补验（2026-10-16，A 路线，执行者 Claude）

| 编号 | 待验命题 | 阻塞否 | 判定 | 实际观察 | 探针代码 |
|---|---|---|---|---|---|
| V-03（HT-012b） | 后道卡级联、全部提交后，把工单工序行损耗补写为「工单数量 − 本道完工」（即本道损耗＋上道累计损耗），Manufacture 按工单数量入库，能否通过原生工序校验、成品为实际末道完工数、工单 Completed | 阻塞 TS-012 | go | 例 1：三道 950，工序行补写 50／50／50，入库 `1000/50`，原生生成成品行 950，工单 Completed。例 2：950＋50、930＋20、930，工序行 50／70／70，入库 `1000/70`，成品 930，Completed。原生 `get_pending_process_loss_qty` 取各行最大值，所以补写的必须是累计值。回滚后残留 0 | `Spike/P1S7R5-D/ht012b-probe.py`；输出 `ht012b-probe.log` |

## 复核建议

HT-011 的第二道提交被原生前后序校验负向控制阻止，首道完成后再按数据库改量并重读则提交通过，验证过程没有 mock 或绕过校验。HT-012 的 `1000/50` 口径已在原生校验处确认冲突，当前暂停 Manufacture 验收；重新确定口径后再恢复 finished-good 数量、工单状态与三条 Work Order Operation 状态的联合验收。原始 `950/50` 的 no-go 证据以及当前定向测试的 `950/0` 观察均保留。
