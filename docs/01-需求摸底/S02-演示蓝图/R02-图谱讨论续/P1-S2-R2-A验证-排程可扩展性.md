# P1-S2-R2 A验证：排程可扩展性

结论先行：**排程结果不是"直接写在 `expected_*` 字段上"的，而是从子表 `scheduled_time_logs` 派生出来的**。因此钩子要改写的对象是子表，不是那三个字段。改子表能走纯 `doc_events`；`has_overlap` 这一层不能。

---

## ① 排程调用链（读码所得）

| 步 | 位置 | 做什么 |
|---|---|---|
| 1 | `work_order.py:985` `on_submit` → `:998` | 提交工单，调 `self.create_job_card()` |
| 2 | `work_order.py:1219` `create_job_card` | 按 `self.operations` 顺序、按批量拆分循环 |
| 3 | `work_order.py:1236` `prepare_data_for_job_card` | 每行调下面两步 |
| 4 | `work_order.py:1262` `set_operation_start_end_time(row, idx)` | 算 **WO Operation 行**的 `planned_start_time/planned_end_time`：首序=`planned_start_date`，同 `sequence_id` 并行，否则接上一序末 + `get_mins_between_operations()` |
| 5 | `work_order.py:2968` 模块级 `create_job_card(...)` | `frappe.new_doc("Job Card")` + `doc.update({...})`，其中 `time_required` 先按 `time_in_mins/qty*qty` 预填（`:2987`） |
| 6 | **`work_order.py:3012` `doc.schedule_time_logs(row)`** | **在 `doc.insert()`（`:3014`）之前调用** |
| 7 | `job_card.py:544` `schedule_time_logs(row)` | while 剩余工时>0：`validate_overlap_for_workstation`(`:556`) + `check_workstation_time`(`:580`) |
| 8 | `job_card.py:556` → `:364 get_overlap_for` → **`:400 has_overlap`** | 找冲突；冲突则把 `args.from_time` 顺延到 `data.to_time + 工序间隔`，**递归重试**(`:573`) |
| 9 | `job_card.py:580` `check_workstation_time` | 套 Workstation 工作时段/节假日，跨时段就切片 |
| 10 | `job_card.py:730` `update_time_logs(row)` | `self.append("scheduled_time_logs", {from_time,to_time,time_in_mins,...})`——**纯内存 append** |
| 11 | `job_card.py:779` `before_save` → `:926` `set_expected_and_actual_time` | 由子表**派生** `expected_start_date/expected_end_date/time_required` |
| 12 | `work_order.py:1244-1245` | 回读 `job_card_doc.scheduled_time_logs[-1].from_time/to_time` 写回 WO Operation 行，`:1247` 校验 `plan_days`，`:1259` `row.db_update()` |

只有 `work_order.py:3012` 一处调 `schedule_time_logs`（全仓 grep，排除测试）。

## ② 排程结果的赋值方式（★核心）

`job_card.py:926-950` `set_expected_and_actual_time`：

```
("scheduled_time_logs", "expected_start_date", "expected_end_date", "time_required")
→ self.set(start_field, min(time_list)); self.set(end_field, max(time_list)); self.set(time_required, time_in_mins)
```

读码所得三点：

1. **是 `self.set(...)` 后随 save 落库，不是 `db_set`。**
2. **这三个字段是派生量**，来源是子表各行 `from_time/to_time/time_in_mins` 的 min/max/sum。**全仓没有任何 `db_set("expected_start_date"...)`**（grep 确认赋值点仅 `:926` 一处，调用点仅 `before_save` 一处）。
3. 推论（标注：**推断**，未实跑）：**在 `before_save` 之后的钩子里单改 `expected_*` 会在下一次 save 时被 `before_save` 按子表重算回去。** 要让改写稳定，必须改 `scheduled_time_logs` 子表；改完 `expected_*` 会自动随之而来。

**对换型矩阵的直接后果**：换型分钟数**不能**加在 `time_required` 上（会被 `:950` 的 sum 覆盖），必须体现为 `scheduled_time_logs` 的行时长/额外行。这条是本次验证里最吃紧的一点。

## ③ 可用钩子点与执行顺序

`document.py:1391-1419`（before）/`1445-1474`（post）+ `1245-1260 run_method` + `1614-1663 Document.hook`：

- 走 composer 的方法：`before_validate`、`validate`、`before_save`、`before_submit`、`before_cancel`、`on_update`、`on_submit`、`on_cancel`、`on_change`。
- **同一事件内顺序：`document.py:1636` `compose` 的 runner 先执行类自己的 `fn(self,...)`，再依次跑 hooks**；hooks 列表由 `:1653-1655` 拼成 `doc_events[DocType][method] + doc_events["*"][method]`。即 **erpnext 自己的方法体永远先跑，app 的 handler 后跑**；具体 DocType 先于 `"*"`，同 DocType 内按 hooks.py 列表顺序（多 app 时按 app 加载序，累加不覆盖）。

对本课题的落点（前 / 后）：

| 钩子 | 相对排程 | 说明 |
|---|---|---|
| Job Card `validate` | **后** | 自动创建路径下 `schedule_time_logs` 已在 `insert()` 前跑完，子表已有行 |
| **Job Card `before_save`** | **后**，且在 `set_expected_and_actual_time` **之后** | 改子表后需自行重算 `expected_*`，或改完子表再调一次 `self.set_expected_and_actual_time()` |
| Job Card `on_update` / `on_submit` | 后，但已落库 | 改 `expected_*` 无用（见 ②-3）；`db_set` 不触发递归 save，但 `self.save()` 会 |
| Work Order `on_submit` | **`create_job_card` 之后**（`:998` 在 `on_submit` 体内，handler 在整个方法体之后） | 可在此对**整批** JC 重排——跨工单/跨工序全局优化唯一的纯钩子位置 |
| Work Order `validate`/`before_save` | 前 | 可改 `planned_start_date`、`operations` 行的 `time_in_mins`/`sequence_id`——**以"喂参数"的方式间接影响排程，不碰排程代码** |

`after_insert`：未在 `run_before/post_save_methods` 中出现，其触发位置**未查实**。

## ④ 三档做法判定

| 做法 | 能做到什么 | 升级要否跟 | 风险 |
|---|---|---|---|
| **(a) 纯 `doc_events` 追加** | ①WO `validate` 改 `operations` 行 `time_in_mins`（把换型矩阵查出的分钟数并入工序工时）、改 `sequence_id`、按优先级改 `planned_start_date`；②JC `before_save` 改写 `scheduled_time_logs` 子表并重算 `expected_*`；③WO `on_submit` 对本单已建 JC 整批重排。**优先级+换型矩阵的绝大部分需求落在这里。** | **要跟的只有字段名与子表结构**：`scheduled_time_logs` 的 `from_time/to_time/time_in_mins`、WO Operation 的 `time_in_mins/sequence_id/planned_*`。方法签名不用跟。 | 与 `work_order.py:1244` 的 `[-1]` 取末行约定耦合——重排后必须保证末行是最晚行，否则 WO Operation 的 `planned_end_time` 与 `plan_days` 校验（`:1247` `CapacityError`）会错。**推断，未实跑。** |
| **(b) 必须覆盖类** | 只有**改变冲突判定本身**才必须：`has_overlap`（`job_card.py:400`）是**实例方法**，由 `:390 self.has_overlap(...)` 内部调用，**不是模块级函数、未 whitelist**，`override_whitelisted_methods` 管不到（推断，其仅作用于 RPC 入口）。同理 `get_overlap_for`/`check_workstation_time`/`schedule_time_logs` 都是实例方法。若要"按换型矩阵判定两工序能否相邻/共站"，得覆盖。 | **每次升级都要跟方法体**。且 `override_doctype_class` 后者胜出、多 app 串联时前者被静默丢弃——占掉这个位置就等于锁死了别的 app。 | 最高。可行的替代是类属性 monkey patch（`JobCard.has_overlap = ...`，技术上可行，本项目倾向避免）。 |
| **(c) 第三条路** | ①**旁路排产**：自建 DocType 存优先级与换型矩阵 + 自己的排程结果，只在 WO `on_submit` 之后把结果**回写** JC 的 `scheduled_time_logs`——把算法完全放在自己表里，ERPNext 只当执行层；②禁用原生产能规划（`Manufacturing Settings.disable_capacity_planning`，`work_order.py:1221` 读它）后自己全权排，`schedule_time_logs` 根本不跑（`:3011` 条件），此时 `scheduled_time_logs` 是空白画布；③Server Script 可挂同样事件但难维护复杂矩阵，不推荐。 | 只跟字段名/子表结构，与 (a) 同级。②还要跟那个设置项的字段名。 | ② 放弃了原生工作站工时/节假日/产能切片逻辑，全部得自己实现，工作量大但可控且可测。 |

**建议**：主体走 (a)，并优先考虑 (c)② 作为"把算法收进自己家"的形态。(b) 留作最后手段。

## ⑤ 拿不准 / 未实跑的

1. 上表所有"推断"项均**未实跑验证**，特别是 `before_save` 钩子改子表后 `work_order.py:1244` 的回读行为。
2. `after_insert` 的实际触发位置未查实。
3. 手工新建 Job Card（不经 WO）时 `schedule_time_logs` 不被调用（`:3012` 是唯一调用点），此路径下 `expected_*` 的来源**未查**。
4. `override_whitelisted_methods` 对非 whitelist 内部调用无效——**推断，未读该实现代码**。
5. 未查：JC 取消/修改数量、`split_qty_based_on_batch_size` 二次拆分、以及 Production Plan 路径是否另有排程入口。
6. 未查：`workstation.py:259-274` 按 `expected_start_date` 排序的用途（看起来是产能看板/可用槽位查询），是否构成第二个"读取方"约定。
