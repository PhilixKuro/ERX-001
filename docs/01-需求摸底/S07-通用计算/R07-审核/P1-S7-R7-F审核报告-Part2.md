# 审核报告·Part2（对象：`frappe_china` `68233b9..acf97e6` 中批次换算、拆单、工序数量传递、计件工资 / 审核标准：R04 方案总纲＋Part2，R03 需求 §4.7～4.9、§4.11.3、§4.13、§4.18）

**轮次**：P1-S7-R7 F 片2｜**日期**：2026-10-16｜**审核者**：Claude（Opus 5.5，独立 Session，未参与 C／D／E）
**被审代码**：`frappe-bench/apps/frappe_china`，HEAD `acf97e6`（工作区无未提交改动）；上游 erpnext `12cd563f`、hrms `6f5ac249`（`docker/apps.json`）
**探针**：`Spike/P1S7R7-F/p2/`（`probe_flow.py`／`probe_cancel.py`／`probe_zero_card.py` 及同名 `.log`），只在 `test.localhost` 跑，均 `try/finally: frappe.db.rollback()`，未触发 `frappe.log_error`（`tabError Log` 无须清理）

## 覆盖自证

- **读全的依据**：总纲全文（§二 A1～A17、§四偏离 1～21、§五、§六、§七、§十）；Part2 全文（SL-006～009 验收 ①～⑦、TS-010～013 具体改动与验证方式）；需求 §4.7、§4.8、§4.9、§4.11.3、§4.13、§4.17、§4.18 与 §八 AC-016～019；开发守则「侵入度分级」「覆盖登记」「写入端与读取端」「静默失败」「探针三条纪律」「跨 Phase 接口契约表」；业务规则全表。
- **读全的代码**：`production/batch_uom.py`、`job_card_split.py`、`operation_flow.py`、`piece_rate.py`；`production_plus/doctype/piece_rate_summary*`（py／json／list.js）；`public/js/batch_uom.js`；`hooks.py` 全文；`install.py` 的 `after_install`／`after_app_install`／`after_migrate`；fixtures 中 `Item-cn_unit_length_m`、`Batch-cn_linear_density`、`BOM Operation-cn_job_card_split_qty`、`BOM Operation-cn_piece_rate`、`Operation-cn_piece_rate` 五条；`zh.csv` 本片新增行；README「后端覆盖登记」与「已知限制」本片两行；测试 `test_batch_uom.py`／`.cjs`、`test_job_card_split.py`、`test_operation_flow.py`、`test_piece_rate.py`。
- **对照的上游**：`work_order.py:1219-1230, 2838-2853, 2902-2915, 2968-2995, 700-740, 920-951, 1577-1595`、`work_order.js:400-437`、`job_card.py:165-200, 755-785, 870-923, 950-990, 1052-1089, 1536-1595`、`stock_entry.py:1165-1200, 3343-3360`、`transaction.js:1669-1715, 2027-2045`、`stock_entry.js:1091-1110, 1182-1195`、`stock_controller.py:415-465`、`frappe/app.py:244-245`、`background_jobs.py:269-270`、`frappe/__init__.py:1140-1190`、`document.py:1089-1113`、hrms `additional_salary.py:27-39, 111-131, 159-190` 与 json 权限。
- **跳过及原因**：① 未跑 `run-tests`（主会话正在 test.localhost 跑全量，派单禁止），测试数取自 `frappe-bench/logs/s7-r6-e-after-fix-full.log` 只读核对，非本片实跑；② 未开浏览器复验 SL-006 ⑤（只核了截图文件存在与前端代码、Node 单测）；③ 未核 `erx.localhost`（本片无须读演示站数据）；④ `Piece Rate Summary` 已提交后取消来源 Job Card 是否被原生回链检查拦住，只读码推断、未探针。

## 逐项落地核查

| 方案任务 | 要求层要求 | 定位（文件:行） | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| TS-010 | 换算方向表：库存＝`weight_uom`、行≠→`w`；反之 `1/w`；其余回落 | `batch_uom.py:33-41` | ✅ | ✅ | 与方案表字面一致；「行≠weight_uom」把任何非重量单位都当「支」，见 P2-07 |
| TS-010 | 精度 `flt(x, 9)`，与字段 precision 一致 | `batch_uom.py:43`；上游三类子表 `conversion_factor` precision＝9 | ✅ | ✅ | — |
| TS-010 | `BATCH_UOM_DOCTYPES` 常量 | `batch_uom.py:8-12` | ⚠️ | ❌ 死代码 | 无任何读取方（全仓 grep 仅定义处）；`apply_batch_factor` 直接取 `items`，见 P2-08 |
| TS-010 | `get_batch_conversion_factor` 回落原生、`source`、Item read 权限 | `batch_uom.py:46-60` | ✅ | ✅ | — |
| TS-010 | `apply_batch_factor`：有 batch_no 才算，非 None 且不同才改 | `batch_uom.py:63-71` | ✅ | ✅ | 三类单据 `before_validate` 已挂（`hooks.py:192-194`），测试 ⑥ 篡改修复为真单据 |
| TS-010 | 前端 `batch_no`／`uom` handler、只追加；三个 `doctype_js` 键 | `batch_uom.js:1-40`；`hooks.py:49-51` | ✅ | ⚠️ | 与原生 `uom` handler 并发、谁后回谁生效，见 P2-09；服务端保存时纠正 |
| TS-010 | 字段 label「kg/m」、description、`weight_uom` 为空不处理、README 已知限制 | fixtures `Batch-cn_linear_density`；README:196 | ✅ | ✅ | — |
| TS-010 验证 | 单测 ①～④⑥、⑤截图 | `test_batch_uom.py` 3 例；`Spike/P1S7R5-D/ts010-purchase-receipt-batch-factors.png` 存在 | ✅ | ✅ | ③ 的「回落原生」只以 mock 验 API；表单级回落未在真单据断言（低，不另立项） |
| TS-011 | `split_qty` 签名与语义：未勾走 `_original`；勾了按拆分数量、空→整单；不改 `batch_size`；调 `get_serial_nos_for_job_card` | `job_card_split.py:65-76` | ✅ | ✅ | 对照上游 `work_order.py:2902-2915`：未勾分支完全委托；勾选分支与方案伪码一致 |
| TS-011 | `_bom_operation_split_qty` 同 BOM 内第 k 次出现对应、对不上返回 0 并 `log_error` | `job_card_split.py:14-62` | ✅ | ✅ | — |
| TS-011 | `ensure_patched` 幂等、记 `_original` | `job_card_split.py:79-85` | ✅ | ⚠️ | web 请求（`before_request`，`app.py:244-245`）、后台任务（`before_job`，`background_jobs.py:269-270`，`frappe.call` 按签名过滤 kwargs 不会报错）、WO `before_submit` 三处生效；**`bench execute` 进程实测未打补丁**（探针 A：模块属性仍是 erpnext 原函数），直接调 `make_job_card` 的脚本路径不生效，见 P2-10 |
| TS-011 | hooks 三处登记 | `hooks.py:186, 316, 321` | ✅ | ✅ | — |
| TS-011 | 守卫哈希测试、打印新旧哈希 | `test_job_card_split.py:20-30` | ✅ | ✅ | 本片在容器里复算 `inspect.getsource` sha256＝`a1ef469c…870b`，与 `UPSTREAM_SHA256` 一致 |
| TS-011 | README「后端覆盖登记」一行，六列齐 | README:114-118 | ✅ | ✅ | 依赖 commit、`:2902-2915`、`:1228`、`:2853`、失效症状、复验法齐全 |
| TS-011 验证 | ①② 提交路径、③ `make_job_card`、④ 未勾、⑤ 哈希 | `test_job_card_split.py` 9 例 | ✅ | ✅ | ① 4000 分、② 2500×4／3000×3＋1000 均有常量期望 |
| TS-012 | `realign` 签名、for_update 锁工单、按 idx 排序、非纠正卡、只改本道之后、目标量公式、预计产出级联（A17） | `operation_flow.py:8-38`、`87-109` | ✅ | ✅ | 公式与方案逐项一致 |
| TS-012 | `_is_started`（偏离 5） | `operation_flow.py:112-120` | ✅ | ✅ | — |
| TS-012 | `_shift`：差额落最后一张、扣到 0 依次往前；加回加在最后一张（偏离 4） | `operation_flow.py:123-136` | ✅ | ⚠️ | 照方案字面；多张扣过后再取消，回不到取消前（探针 B2：`[250,250,200,300]`），见 P2-02 |
| TS-012 | `_set_card_qty`：`for_quantity`、`time_required`（同 `work_order.py:2987` 式）、排程末行、`items.required_qty` 按比例 | `operation_flow.py:139-183` | ⚠️ | ⚠️ | 比例分支对；**原为 0 的卡加回时 `items` 未按方案 :179 用工单原料需求重取**，仍是 0（探针 B2），见 P2-01；`update_modified=False` 使陈旧表单保存静默覆盖级联（探针 D），见 P2-03 |
| TS-012 | `on_job_card_submit`／`on_job_card_cancel`、跳过纠正卡、msgprint | `operation_flow.py:73-84`；`hooks.py:188-191` | ✅ | ✅ | 处理器在原生 `on_submit`／`on_cancel` 之后、同一事务（读码） |
| TS-012 | 提示文案源词进 csv | `operation_flow.py:29-31`；zh.csv | ⚠️ | ✅ | 方案文案末句「Please adjust manually.」被删，见 P2-12 |
| TS-012（方案外，已裁决） | `sync_operation_loss`：全部卡已提交的工序，把「本道自身损耗＋(工单数量−本道卡数量合计)」写进 `Work Order Operation.process_loss_qty` 与 `status`；`track_semi_finished_goods` 跳过 | `operation_flow.py:41-70` | ✅ | ⚠️ | 不改已提交 Job Card、不改 `Work Order.process_loss_qty`（非半成品模式下后者取 Manufacture 入库单之和，`work_order.py:938-951`），**不与原生汇总双算**；Process Loss Report 读工单字段，也不双算。但「工单数量−卡数量合计」把**未建卡／已取消待重做**的数量也记成损耗（探针 C、E），零数量草稿卡又让「全部已提交」永不成立（探针 F），见 P2-04、P2-05 |
| TS-012 验证 | ① 两种 `disable_capacity_planning` 各跑一遍；④ 拆单；⑤ 入库与工单状态；⑥ 原料量 | `test_operation_flow.py` 6 例 | ⚠️ | — | 只跑了 `disable_capacity_planning=1`（以手插排程行代替）；⑥ 只覆盖比例分支；⑤ 拆单下的入库没测，见 P2-06 |
| TS-013 | DocType 字段、可提交、命名 `PRS-.YYYY.-.#####`、模块 Production Plus | `piece_rate_summary.json` | ✅ | ✅ | 字段与方案表一致；权限 HR Manager／System Manager |
| TS-013 | 子表 8 字段、`rate_source` 三选项 | `piece_rate_summary_item.json` | ✅ | ✅ | `No Piece Rate` 进 csv，另两项沿用官方词 |
| TS-013 | `PIECE_RATE_COMPONENT`／`ABBR`、`ensure_component` 幂等、挂 `after_install`／`after_app_install("hrms")`／`after_migrate` | `piece_rate.py:7-35`；`install.py:219-238`；`hooks.py:116` | ✅ | ✅ | `after_migrate` 里未包异常、排在自检之前，见 P2-11 |
| TS-013 | `collect_rows`：已提交、公司、非纠正卡、行 employee、`from_time` 日期或 `posting_date`（偏离 7）、单价 BOM 工序＞工序＞无单价、只用 `completed_qty` | `piece_rate.py:38-100` | ✅ | ✅ | 无员工的时间行不进任何人（需求即按行 employee 归人，记观察不立项）；每行 `get_doc("Work Order")`，见 P2-13 |
| TS-013 | `validate` 重算、同月首尾、同员工同期间已提交拒绝 | `piece_rate_summary.py:10-35` | ✅ | ✅ | 另加「员工须属该公司」，属合理加固 |
| TS-013 | `on_submit` 零额 throw、建并提交 AS（7 个指定字段）、回填；`on_cancel` 取消 AS | `piece_rate_summary.py:37-62` | ✅ | ✅ | 与 HT-014 与需求 §4.9 一致；未加 `ignore_links` |
| TS-013 | `make_piece_rate_summaries`（§5.2 契约）：自然月、未来 throw、HRMS 缺失 problems、已提交跳过、savepoint 隔离、不 commit；`SummaryResult` 四键 | `piece_rate.py:12-16, 103-143` | ✅ | ✅ | docstring 写了接口约定要点 |
| TS-013 | `make_for_period` 权限＋commit；列表按钮弹框 | `piece_rate.py:146-151`；`piece_rate_summary_list.js` | ✅ | ✅ | 输出经 `escape_html` |
| TS-013 验证 | ①～⑦ | `test_piece_rate.py` 4 例 | ✅ | ✅ | 1190＝950×0.2＋10000×0.1 为常量期望 |
| 总纲 §七 | 拆单 L4 登记；`doc_events` L3；`doctype_js` 追加不登记但回执写明 | README:118；D 回执 Part2「偏离与暂停」第 3 条 | ✅ | — | — |
| 总纲 §十.7 | json／fixtures `modified` 调大 | fixtures 五条、DocType json | ✅ | — | 未核历史版本差值，只核了字段存在 |

## 验证门实跑结果

| 门 | 声称值 | 实测值 | 与基线对比 | 一致否 |
|---|---|---|---|---|
| 本片 Python 测试（全量内） | D 回执：3／9／6／4 | **未实跑**（派单禁止）；只读 `s7-r6-e-after-fix-full.log`：`test_batch_uom` 3 ✔、`test_job_card_split` 9 ✔、`test_operation_flow` 6 ✔、`test_piece_rate` 4 ✔，全量 341＋5＋3 OK、无 ✖ | — | 与日志一致（非独立复跑） |
| Node `test_batch_uom.cjs` | 1/1 | 容器内 `node --test` **1/1 pass** | — | 一致 |
| Ruff check（本片 17 文件） | 0 | **All checks passed** | — | 一致 |
| Ruff format --check（同上） | 通过 | **17 files already formatted** | — | 一致 |
| 上游哈希守卫 | `a1ef469c…870b` | 容器内复算 **相同** | — | 一致 |

## 集成检查

| 集成点类型 | 具体落点 | 两端一致否 | 说明 |
|---|---|---|---|
| 事件／消息 | Job Card `on_submit`／`on_cancel` → `realign`＋`sync_operation_loss` | ✅ | 原生 `update_work_order` 先写工序行，本处理器后写；同一事务 |
| 事件／消息 | Work Order `before_submit` → `ensure_patched` → `create_job_card`（`work_order.py:1219-1228`） | ✅ | `before_submit` 早于 `on_submit` |
| 接口契约 | `make_piece_rate_summaries(company, as_of_date) -> SummaryResult`（总纲 §5.2，S8 消费） | ✅ | 签名、四键、期间、幂等口径与契约一致；`period` 为 tuple（JSON 化后成 list，S8 按序取即可） |
| 接口契约 | 拆单后 Job Card `for_quantity`／`time_required` → 片3 `capacity_load.py:55-75`（按 `time_required×(1−完工/for_quantity)` 计） | ⚠️ | 字段名对得上；`for_quantity`＝0 的卡负荷按 0 计（与偏离 4 一致）；但陈旧表单保存会把级联改回原值（P2-03），负荷报表随之回到整卡工时；`expected_end_date` 不随时长缩短（P2-14） |
| 接口契约 | `Work Order Operation.process_loss_qty`（本片写）→ 原生 `stock_entry.py:1165-1200`、`:3343-3360`、`work_order.py:716-719` 读 | ⚠️ | 正常路径对上（测试 950／930 两例）；未建卡、取消待重做、零数量卡三种情形写入值与读取方语义不符（P2-04、P2-05） |
| 接口契约 | 跨 Phase 契约表（开发守则 §跨 Phase 接口契约表）：演示操控事件协议 `erx_demo_step` | — | 本片不涉及该协议，核过无交集 |
| 共享状态 | `hooks.py`：本片条目 `doctype_js` 3 键、`doc_events` Work Order `before_submit`／Job Card／三类单据、`before_request`、`before_job`、`after_migrate` 首项、fixtures 五条名 | ✅ | 与片1的 Work Order `before_insert`／`after_insert` 同一 dict 并存，无键覆盖 |
| 共享状态 | `fixtures/custom_field.json` 五条（`insert_after` 链：`batch_size`→`cn_job_card_split_qty`→`cn_piece_rate`） | ✅ | — |
| 共享状态 | `zh.csv` 本片新增约 20 行 | ✅ | 文案缺句见 P2-12 |
| 跨模块数据流 | 级联后卡量 → 计件取 `time_logs.completed_qty`（不读 `for_quantity`） | ✅ | 计件不受级联影响 |
| 跨模块数据流 | 拆单对应规则（同 BOM 第 k 次出现）被计件单价复用 | ✅ | `piece_rate._rate` 与 `job_card_split._bom_operation_split_qty` 同口径 |

## 业务规则合规核

| 规则条款 | 本 Round 改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 否 | 合规（无交集） | 本片不出凭证 |
| BR-002 报表构成 | 否 | 合规（无交集） | — |
| BR-003 增值税税率 | 否 | 合规（无交集） | — |
| BR-004 月末转出未交增值税 | 否 | 合规（无交集） | — |
| BR-005 附加税 | 否 | 合规（无交集） | — |
| BR-006 资产＝负债＋权益 | 间接 | 合规 | 批次换算改 `stock_qty`，库存估值随之变；不破坏复式平衡 |
| BR-007 价税分离 | 否 | 合规（无交集） | — |
| 规则新增／变更检出 | `sync_operation_loss` 引入「工序行损耗＝本道损耗＋上道累计损耗」口径 | 非领域不变量，属实现约定 | 若要升进 `业务规则.md`，须标「草案·待领域专家确认」；需求 §4.17 判本 Stage 无新增，本片同意 |

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| D 回执：TS-010 3/3、TS-011 9/9、TS-012 6/6、TS-013 4/4 | E 后全量日志各数相符；未独立复跑 | 一致（日志层） |
| D 回执：守卫 SHA256 `a1ef469c…` | 容器复算相同 | 一致 |
| D 回执：「两条建卡路径都生效」「HTTP／后台补丁有断言」 | 两条路径在 `run-tests` 进程内经 `before_submit`／`setUp` 生效；`bench execute` 进程未打补丁（探针 A） | 部分一致（P2-10） |
| E 报告 TS-012 行：「`_set_card_qty` 同时改时长、排程末行与原料量，与方案一致」 | 原为 0 的卡加回时原料量未按方案 :179 重取，仍为 0（探针 B2） | **不一致**（P2-01） |
| E 报告：`sync_operation_loss` 方案外但经裁决、「不算违规」 | 裁决属实（D 讨论第 7 步）；实现对未建卡／取消待重做／零数量卡有副作用（探针 C、E、F），E 未提 | 部分一致（P2-04、P2-05） |
| D 回执复核建议：「已开工卡不改数量时补写为 0、原生仍要手填」 | 读码属实（已开工卡保持 1000，`upstream`＝0） | 一致 |
| D 回执：「SL-008 ①～⑥ 均有断言」 | ① 只跑一种 `disable_capacity_planning`；⑥ 只覆盖比例分支 | 部分一致（P2-06） |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 | 用户裁决 |
|---|---|---|---|---|---|---|---|---|---|
| P2-01 | 中 | `operation_flow.py:158-163` | 卡数量从 0 加回时，原料需求量取的是**该卡自己的** `required_qty`（已被比例 0 清成 0），乘新数量仍是 0。探针 B：第二道 4×250，前道 700 完工后末张扣到 0；取消前道后末张回到 300，原料行仍为 `0.0`（`probe_flow.log` B2） | Part2 :179「按原生 `get_required_items` 口径重取（工单原料 `required_qty × new_qty ÷ wo.qty`，`job_card.py:773`）」；SL-008 ⑥ | `old_qty`＝0 时按工单 `required_items` 中同物料（同 `operation`）的 `required_qty` 计算；补一条 0→加回的断言 | 本Session修 | — | 待裁决 | |
| P2-02 | 中 | `operation_flow.py:123-127` | 加回差额一次全加到最后一张：扣过多张的情形取消前道后回不到取消前。探针 B：`[250,250,250,250]` → 前道 700 → `[250,250,200,0]` → 取消前道 → **`[250,250,200,300]`**，末张超过拆分数量 250 | 需求 AC-018 第 3 问「前道取消后后道回到取消前的数量」；SL-007 拆分数量语义 | 加回时按扣减的逆序回填，每张至多回到拆分数量（或原数量），余数再落末张 | 出方案修 | 加回规则：A 逆序回填至拆分数量上限（偏离 4 改写）／B 维持方案字面「加在最后一张」并接受超拆分数量 | 待裁决 | |
| P2-03 | 中 | `operation_flow.py:146-151, 164, 183` | 级联用 `db.set_value(..., update_modified=False)`，原生「文档已被修改」检查（`document.py:1089-1113` 比 `modified`）失效。前道提交前已打开的后道卡表单，级联后再保存会把 `for_quantity`／`time_required` 静默改回原值。探针 D：库内 950 → 保存陈旧文档成功 → `(1000, 40000)` | 总纲 A14 意图（后道按实到数量）；开发守则「静默失败」 | 改为 `update_modified=True`（陈旧表单保存时原生报「已被修改」），或在 Job Card `validate` 里对未开工卡重算目标量 | 本Session修 | 选法：A 更新 `modified` 让原生拦截／B 保存时重算 | 待裁决 | |
| P2-04 | 中（边界：高） | `operation_flow.py:58` | 「上道累计损耗＝工单数量−本道卡数量合计」把非损耗的缺口也记成损耗：① 首道人手只建／改成 600 的卡完工后，首道工序行记 **600＋400 损耗**、状态 Completed，而第二道仍是 1000（探针 C）；② 拆单工序 4 张已提交、取消其一待重做，工序行记 **750＋250**，原生建卡对话框的待建量（`work_order.js:420-437`）算成 0，后道仍是 1000；第三道按 750 报完后 Manufacture 以损耗 250、成品 750 **把工单置 Completed**（探针 E） | 需求 §4.8「每次提交／取消都重算」、原生按每道 完工＋损耗 对账；D 讨论第 7 步裁决的口径是「上道损耗」，不含未建卡与待重做 | 上道损耗改按 `realign` 同一口径取「工单数量−本道计划量（上道预计产出）」，而非本道卡数量合计；补 C、E 两例测试 | 出方案修 | 是否修改已裁决的 A 路线公式（改为按上道预计产出计） | 待裁决 | |
| P2-05 | 中 | `operation_flow.py:56`；与总纲偏离 4 拼装 | 偏离 4 保留的 `for_quantity`＝0 草稿卡，原生无法提交（`job_card.py:890-899` 要求有时间行）；`sync_operation_loss` 又要求该道**全部**卡已提交才补写，于是该道永不补写，Manufacture 被 `OperationsNotCompleteError` 拒绝（探针 F：前道损耗 300、第二道末张 0）。删卡或补一行 0 完工时间行后才通过 | SL-008 ④⑤ 合起来不成立（拼装不上） | 「全部已提交」判定排除 `for_quantity`＝0 的未开工草稿卡 | 本Session修 | — | 待裁决 | |
| P2-06 | 低 | `test_operation_flow.py:8-36` | ① 方案要求 `disable_capacity_planning` 两种取值各跑一遍，测试只设 1 并手插排程行；⑥ 只测比例分支（漏了 P2-01）；拆单＋损耗＋入库、陈旧表单、未建卡／取消待重做均无测试 | Part2 TS-012 验证方式 | 随 P2-01～05 一并补测 | 新Session修 | — | 待裁决 | |
| P2-07 | 低 | `batch_uom.py:33-34`；Part2 TS-010 换算表 | 库存单位为 kg 时，**任何**非 kg 行单位（如「箱」）都取「每支重量」为系数，箱的系数会错成单支值 | 需求 §4.11.3「按 `UOM Conversion Detail` 的既有配置定方向」 | 只对「物料 UOM 表中被识别为单支的那个单位」生效，或限定行单位须在 `uoms` 中且原生系数与单支同量级；属方案缺口 | 出方案修 | 单支单位如何识别：A 加物料字段「单支单位」／B 约定演示物料只配 kg 与支两种单位、记已知限制 | 待裁决 | |
| P2-08 | 低 | `batch_uom.py:8-12` | `BATCH_UOM_DOCTYPES` 无读取方，属死代码；子表名写死在 `apply_batch_factor:65` | 方案把它列为接口常量 | 让 `apply_batch_factor` 按该表取子表字段，或删常量 | 本Session修 | — | 待裁决 | |
| P2-09 | 低 | `batch_uom.js:30-37` | `uom` 变更时与原生 handler（`transaction.js:1669-1686` 的 `get_conversion_factor`、`stock_entry.js:1091-1106` 的 `get_uom_details`）各发一次请求，谁后返回谁写 `conversion_factor`；原生后回时表单显示物料级系数，保存时服务端才纠正。未在浏览器复现，读码判断 | SL-006 ⑤「前端选批次后系数当场变化」（批次变更不受影响，单位变更受影响） | 在 `conversion_factor` 变更后若行有批次再校一次，或接受「保存后纠正」写进已知限制 | 延迟或不修 | — | 待裁决 | |
| P2-10 | 观察 | `job_card_split.py:79-89`；`hooks.py:316, 321` | `bench execute`／console 进程不经 `before_request`／`before_job`，补丁只在 WO `before_submit` 时装上；同进程未先提交工单就直接调 `make_job_card`，走的是上游按 `batch_size` 拆（探针 A：模块属性仍为 erpnext 原函数）。S8 生成器若经 `bench execute` 补建卡会命中 | 总纲 A13「两条建卡路径都生效」；HT-004 | 在 S8 入口或 `frappe_china` 某个必经 import 处调用 `ensure_patched()`，或在 README 登记行补「脚本路径须先调 `ensure_patched`」 | 延迟或不修 | — | 待裁决 | |
| P2-11 | 低 | `hooks.py:116`；`piece_rate.py:23-35` | `ensure_component` 在 `after_migrate` 列表首位且不吞异常，一旦抛错会中断 migrate 并跳过随后的覆盖自检（HT-002）。另：建出的薪资项无公司科目行，S8 跑 Payroll Entry 时会要求补科目（未实测） | 总纲 §5.4「自检抛异常也告警不中断」的同一意图 | 包 try 并走 `after_migrate` 同样的告警，或挪到自检之后；科目行记进 S8 交接 | 本Session修 | — | 待裁决 | |
| P2-12 | 低 | `operation_flow.py:29-31`；zh.csv 对应行 | 提示文案缺方案的「Please adjust manually.」，操作工只看到差额、看不到要怎么办 | Part2 TS-012 提示文案 | 补回源词与译文 | 本Session修 | — | 待裁决 | |
| P2-13 | 观察 | `piece_rate.py:56-68` | 每条时间行 `get_doc("Work Order")`，一月多卡时 N＋1 次整单读取 | — | 按工单缓存 | 延迟或不修 | — | 待裁决 | |
| P2-14 | 观察 | `operation_flow.py:168-183` | 改量后只改排程末行时长与止时，Job Card `expected_end_date` 与工序行 `planned_end_time` 不变；负荷报表按 `expected_start_date` 分桶，暂不受影响 | 总纲 A14 | 记已知限制即可 | 延迟或不修 | — | 待裁决 | |

## 交接摘要（供收口跨片比对）

**本片发出的事件／写入**
- Job Card `on_submit`／`on_cancel` 后：直接改写后道未开工 Job Card 的 `for_quantity`、`time_required`、`Job Card Item.required_qty`、`Job Card Scheduled Time` 末行（均 `update_modified=False`）；改写 `Work Order Operation.process_loss_qty` 与 `status`；`msgprint` 差额提示。
- Work Order `before_submit`、每个 web 请求、每个后台任务：替换 `erpnext…work_order.split_qty_based_on_batch_size` 模块属性（进程级全局状态）。
- 三类库存单据 `before_validate`：改行 `conversion_factor`。
- `Piece Rate Summary` 提交／取消：建并提交／取消 `Additional Salary`。
- `after_install`／`after_app_install("hrms")`／`after_migrate`：建 `Salary Component`「计件工资」。

**本片暴露的接口契约**
- `frappe_china.production.piece_rate.make_piece_rate_summaries(company, as_of_date) -> SummaryResult`（`period`／`created`／`skipped`／`problems`；不 commit；期间＝自然月；`payroll_date`＝月末）——S8 消费。
- `make_for_period`（whitelist，HR Manager／System Manager，会 commit）。
- `get_batch_conversion_factor(item_code, batch_no, uom)`（whitelist）、`batch_factor`。
- `realign(work_order, from_idx) -> list[str]`、`sync_operation_loss(work_order)`。
- Job Card `for_quantity`／`time_required`（拆单与级联后的值）——**片3 `capacity_load.py` 消费**；`for_quantity`＝0 的卡负荷为 0。
- `Work Order Operation.process_loss_qty` 的累计口径——原生 Manufacture 校验与入库损耗消费。

**本片依赖的接口／状态**
- 片1：Work Order `before_insert` 选 BOM 后重建的 `operations`（含 `bom` 列，拆单与计件的「同 BOM 第 k 次出现」对应规则依赖它）。
- 上游：`work_order.py:1228, 2853` 按模块全局名调用；`job_card.py:773` 原料口径；`stock_entry.py:1165, 3343`；hrms `Additional Salary` 校验。
- 跨片共享文件：`hooks.py`（`doc_events` Work Order 与片1同 dict；`after_migrate` 列表与片1自检同列表、本片在前）、`fixtures/custom_field.json`（本片五条）、`translations/zh.csv`（本片约 20 行）、README「后端覆盖登记」（本 Stage 唯一一行）。

## 复核建议

1. **定级边界**：P2-04 在中／高之间——它能让工单以错误损耗 Completed（探针 E），但触发要「取消待重做」或「首道少建卡」；若演示脚本里有「取消后重报」一步，应改判高。P2-02、P2-03 在中／低之间：只在多张卡扣过或有人开着旧表单时出现。
2. **查得最浅处**：`sync_operation_loss` 与原生半成品追踪（`track_semi_finished_goods`）、超产比例（`overproduction_percentage_for_work_order`）、纠正卡（corrective job card）三者的交互只读了码、没探针；`piece_rate` 已提交后取消来源 Job Card 被原生回链拦截一事只是推断。
3. **没往哪找**：没对照 S4～S6 历史遗留行为（如 S5 对 Stock Entry 的其它 `before_validate` 处理是否与批次系数先后有关）；没复跑全量；没用浏览器验前端并发（P2-09 是读码结论）。
4. **拿不准**：P2-04 的「首道少建卡」是否算正常操作——原生允许经对话框补建剩余数量，所以判为问题；P2-07 的方案字面已写明「≠weight_uom 即取 w」，算方案缺口而非执行偏移。

## 总体判断

- 部分满足：TS-010、TS-011、TS-013 落地且生效，与方案和需求一致（另有低级与观察项）；TS-012 的级联主路径与已裁决的损耗补写在测试场景下成立，但在「拆单多张扣减后取消」「从 0 加回」「陈旧表单保存」「未建卡／取消待重做」「零数量草稿卡」五种情形下结果偏离需求 AC-018 与原生对账语义（P2-01～05）。
