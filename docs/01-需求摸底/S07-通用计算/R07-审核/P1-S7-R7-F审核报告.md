# 审核报告（对象：P1-S7 通用计算的代码，`frappe_china` `68233b9..acf97e6` / 审核标准：R03 B 需求文档＋R04 C 开发方案总纲与 Part1～3＋业务规则）

**轮次**：P1-S7-R7｜**日期**：2026-10-16～17｜**步骤**：`plannedDev` F（audit），收口报告｜**执行者**：Claude（Opus 5.5）｜`打tag=否`
**Spec**：[F-codeAudit-plannedDev-audit.md](../../../流程体系/workflows/plannedDev/F-codeAudit-plannedDev-audit.md)＋`bricks/audit.md`＋`bricks/sharding.md`
**意图层**：[B 需求文档](../R03-需求文档/P1-S7-R3-B需求文档.md)｜**要求层**：[C 方案总纲](../R04-开发方案/P1-S7-R4-C开发方案-总纲.md)与 Part1～3 的 TS-001～017｜**合规基线**：[业务规则](../../../业务规则.md) v1（未经专家确认）
**被审对象**：`frappe_china` `68233b9..acf97e6`（Ruff 基线 `39b2cec`＋功能 6 个提交＋E 修复 `acf97e6`；功能面 87 文件 +5841／-21）；HEAD＝`origin/main`＝`docker/apps.json` 锁＝`acf97e6`；主仓库 S7 期间提交（`bd4f91e..02771f5`）
**分片报告**：[Part1](P1-S7-R7-F审核报告-Part1.md)（方案 Part1：TS-001～009）／[Part2](P1-S7-R7-F审核报告-Part2.md)（方案 Part2：TS-010～013）／[Part3](P1-S7-R7-F审核报告-Part3.md)（方案 Part3：TS-014～017＋横切）。片内 `P{n}-xx` 号只在片内有效，跨文件引用用本报告的 `FD-` 号。

**独立性**：D 步主体由 Codex 执行，TS-012 补完与 E 由另两个 Session 的 Claude 做；本步主会话与三个子 Agent 均未参与 D、E。

## 覆盖自证（分片）

依据拆成总纲＋3 Part，按 `sharding.md` 按 Part 分 3 片，每片一个独立只读子 Agent，干净上下文；验证门、跨片合并与对关键发现的抽查复核由主会话做。

| 片 | 范围 | 实际查了 | 跳过及原因 |
|---|---|---|---|
| 1 | TS-001～009：Ruff 基线、骨架、覆盖自检、补货参数、安全库存与再订货点、选 BOM、建议单与每日计算；E 修复 IT-001～006 是否修对 | 方案逐条要求列行；`39b2cec` 64 文件 AST 比对；上游 `production_plan.py`、`bin.py`、`bom.py` 对照；test.localhost 回滚探针（MR 类型、按订单仓库、工作中心调价、杂项）；Ruff、Node 自跑 | 三个 js 只读码，没上浏览器；Python 全量不由本片跑 |
| 2 | TS-010～013：批次系数、拆单 L4 补丁、工序数量传递（含方案外 `sync_operation_loss`）、计件工资 | 逐条要求列行；上游 `work_order.py`、`job_card.py`、`stock_entry.py`、HRMS `additional_salary.py` 对照；拆单原函数哈希复算 `a1ef469c…`；回滚探针 A～F（`bench execute` 补丁、级联、取消、0 数量卡、表单并发、取消待重做） | `sync_operation_loss` 与 `track_semi_finished_goods`、超产、纠正卡的交互只读码；前端并发没上浏览器 |
| 3 | TS-014～017：负荷报表、SPC 与控制图、收尾；横切：版本锁、主仓库 S7 提交、常驻文件、演示站状态、Spike 卫生 | SPC 自造不等子组单侧算例逐式手算；负荷报表口径读码＋只读探针；echarts 许可证；11 个主仓库提交逐个看；演示站只读快照与长跑进程重载时刻；两站译名自检 | SPC 工作中心筛选只验了 SQL 可跑、未造命中数据；worker 是否加载 E 修复只读码推断 |
| 主 | 验证门、跨片合并、抽查 | 全量 Python 自跑；抽读 `operation_flow.py:40-69、:123-163`、`bom_selection.py:64-79`、`custom_field.json` 的 `cn_service_level`、`hooks.py:116`、`piece_rate.ensure_component`；fixtures 清单与 `custom_field.json` 逐名比对 | 浏览器实点；会计与生产领域专家 |

**一句话边界**：本轮对照方案与需求查代码，没有交叉核对 S4～S6 已交付功能的历史行为（只靠全量回归兜底），前端只读码。

**审核自身留下的痕迹**：只写了本目录 4 份报告和 `Spike/P1S7R7-F/`（全量日志 `python-full.log`、`p1/`～`p3/` 探针与输出）。test.localhost 探针全部事务内回滚，未触发 Error Log；演示站只做 SELECT；`frappe_china` 与主仓库受管文件未改。

## 验证门实跑结果

| 门 | 声称值（E 修后） | 实测值 | 与基线对比 | 一致否 |
|---|---|---|---|---|
| `bench --site test.localhost run-tests --app frappe_china`（先 `clear-cache`） | 349/349 | **341 integration（1823.5s）＋5 旧式类＋3 未分类＝349/349**，均 OK，`EXIT=0`（主会话自跑，`Spike/P1S7R7-F/python-full.log`） | TS-001 基线 283 → 349，只增不减 | ✅ |
| `node --test frappe_china/tests/*.cjs`（宿主 Node 24.13.1） | 89/89 | **89/89**，0 fail、0 skip（片 1、片 3 各跑一次） | 86 → 89 | ✅ |
| `node --check`（本 Stage 新增 js） | — | 全部通过（片 1） | — | ✅ |
| Ruff 0.14.10（容器） | `check` 0、`format` 161 | `check` All checks passed!；`format --check` 161 files already formatted（片 1、片 3） | 基线 0 告警保持 | ✅ |
| Ruff 基线提交只含格式与 lint（TS-001） | 只含 | `39b2cec` 64 文件，AST 比对有差异的 7 个都是等价修正（片 1） | — | ✅ |
| 拆单上游原函数哈希 | 与登记一致 | 复算 `a1ef469c…`，一致（片 2） | — | ✅ |
| 两站 `translation_check.run` | 通过 | 两站均通过（片 3） | — | ✅ |
| 版本锁 | `apps.json` 锁 `acf97e6` | `frappe_china` HEAD＝`origin/main`＝锁＝`acf97e6`；工作区干净 | — | ✅ |
| 演示站只读快照 | 业务数据 0、`check_app_order` 真 | `check_app_order` 五项全真；业务数据、Translation、物料、批次 0；D 最终快照后 Error Log 新增 0（片 3） | 与 S6 收口基线一致 | ✅ |
| 类型检查／构建 | — | 不适用（工具链索引「待确立」）；`acf97e6` 无 json／js 改动，不需 build | — | — |

验证门与声称值全部一致。全量全绿不代表无缺陷：本报告的中级发现大多落在测试没覆盖的情形里（见 FD-012、FD-024）。

## 逐项落地核查（汇总；逐条要求行在各片报告）

| 方案任务 | 落地 | 生效否 | 本轮发现 | 查于 |
|---|---|---|---|---|
| TS-001 Ruff 基线 | ✅ | ✅ | — | 片 1 |
| TS-002 模块骨架与字段 | ✅ | ✅ | FD-010（Company 节位置）、FD-016（fixtures 清单）、FD-014（新模块首次 migrate 不同步） | 片 1、片 3 |
| TS-003 覆盖自检与顺序比对 | ✅ | ⚠️ | FD-015（`ensure_component` 绕过自吞）、FD-021（判据夹带）、FD-020、FD-028 | 片 1、片 3 |
| TS-004 补货参数、`auto_indent`、提前期同步 | ✅ | ⚠️ | FD-009（服务水平默认值压住公司默认） | 片 1 |
| TS-005 选 BOM 共用函数 | ✅ | ⚠️ | FD-006（工作中心调价无效） | 片 1 |
| TS-006 选 BOM 三处接入 | ✅ | ✅ | FD-022（已保存工单不出提示） | 片 1 |
| TS-007 需求取样、安全库存、再订货点 | ✅ | ✅ | FD-018（E 修复的展示副作用） | 片 1 |
| TS-008 建议单与三种规则 | ✅ | ⚠️ | FD-007（MR 类型）、FD-008（按订单仓库）、FD-017 | 片 1 |
| TS-009 每日计算入口与采纳 | ✅ | ⚠️ | FD-011（「立即计算」吞掉 problems）、FD-019、FD-023 | 片 1 |
| TS-010 批次系数 | ✅ | ✅ | FD-025、FD-026、FD-031 | 片 2 |
| TS-011 拆单 L4 补丁 | ✅ | ✅ | FD-034（`bench execute` 进程不打补丁） | 片 2 |
| TS-012 工序间数量传递（含已裁决的 `sync_operation_loss`） | ✅ | ⚠️ | FD-001～005、FD-027、FD-036 | 片 2 |
| TS-013 计件汇总与 Additional Salary | ✅ | ✅ | FD-015、FD-035 | 片 2 |
| TS-014 产能负荷报表 | ✅ | ✅ | FD-039（口径记录） | 片 3 |
| TS-015 SPC 计算与报表 | ✅ | ✅ | FD-030（测试判别力）、FD-037 | 片 3 |
| TS-016 控制图页面 | ✅ | ✅ | FD-029（许可证文件）、FD-038 | 片 3 |
| TS-017 收尾、全量回归、演示站 | ✅ | ✅ | FD-013（D 步探针曾写演示站）、FD-032、FD-033、FD-040、FD-041 | 片 3 |
| 横切：告警与 problems 的语言 | — | — | FD-023 | 片 1、片 3 |

17 个任务都有行，没有整片跳过。需求 AC-001～023 的覆盖由各片按总纲 §三末表逐条核过。

## 跨片一致性（收口交叉比对）

| 比对点 | 发出方 | 消费方 | 结果 |
|---|---|---|---|
| Job Card `for_quantity`／`time_required`／排程末行 | 片 2 拆单与级联写入 | 片 3 负荷报表 `capacity_load.py:55-75` | 字段对得上；0 数量卡按 0 计。**但 FD-003 会让旧表单把 `time_required` 写回整卡值，负荷报表随之回到整卡工时**——两片单看都对，合起来负荷失真 |
| 选 BOM 后重建的 `operations.bom` | 片 1 `work_order_before_insert` | 片 2 拆单与计件按「同 BOM 第 k 次出现」对应 | 一致：片 1 重调 `set_work_order_operations()`，片 2 读到的是新 BOM 的工序 |
| `hooks.after_migrate` 顺序 | 片 2 `ensure_component` 在首位 | 片 1 `install.after_migrate` 自吞异常 | **拼装不上**：三片独立指出同一处（片 1 交接、P2-11、P3-11），合为 FD-015 |
| fixtures 过滤清单 ⇔ `custom_field.json` | 片 1、片 2 共 27 条 | `hooks.py` fixtures 过滤 | 主会话逐名比对：只缺 `Material Request-cn_replenishment_suggestion` 一条（FD-016），片 2 的字段都在 |
| `zh.csv` 共享 | 三片各约 45／20／40 行 | 译名守卫与两站自检 | 守卫与自检通过；9 行删了再原样加回，只是重排。语言问题三处同源，合为 FD-023 |
| `test_translations.py:204-206` 跳过 `public/js/vendor/` | 片 3 | 全 app | 现只有 echarts；他片若在该目录放自有文件会被一并跳过，记入 FD-041 观察 |
| `make_piece_rate_summaries`／`run_daily` 接口约定 | 片 2／片 1 | S8 生成器 | 签名与 §5.2 一致；实现比契约多 `is_default`、`note` 两键、`default_boms` 返回 list，现有调用方拼得上。FD-034：S8 若用 `bench execute` 调 `make_job_card` 不经补丁 |

## 集成检查

| 集成点类型 | 具体落点 | 两端一致否 | 说明 |
|---|---|---|---|
| 事件／消息 | realtime | 不涉及 | 本 Stage 不发不收 realtime 事件；只 `msgprint` 与 Notification Log |
| 接口契约（§13 跨 Phase） | 演示操控事件协议 `erx_demo_step` | 不涉及 | 推送侧、消费侧都没改 |
| 接口契约 | `run_daily`／`run_now`／`scheduled_daily` ⇔ 总纲 §5.2、需求 §4.13 | ⚠ | 签名与四条约定一致；`run_now` 的返回在列表回调里被丢弃（FD-011）；`scheduled_daily` 写 Error Log 参数位次反（FD-019） |
| 接口契约 | `select_bom`／`recommend_bom` ⇔ §5.3 | ⚠ | 形态一致；成本口径与 A10 不符（FD-006） |
| 接口契约 | 按订单规则 ⇔ 上游 `get_items_for_material_requests` | ❌ | 上游返回的请购类型超出建议单取值域（FD-007）；`for_warehouse=None` 时仓库粘连（FD-008）。偏离 14 的前提在上游实现下不成立 |
| 接口契约 | `after_migrate` ⇔ §5.4「不 raise」 | ⚠ | 自检本身自吞；同列表首位的 `ensure_component` 不吞（FD-015） |
| 接口契约 | 拆单补丁 ⇔ 上游 `split_qty_based_on_batch_size` | ✅ | 哈希一致；web、后台任务、WO `before_submit` 三处生效，`bench execute` 不生效（FD-034，方案 HT-004 已知） |
| 接口契约 | `docker/apps.json` 锁 ⇔ `frappe_china` HEAD | ✅ | 均 `acf97e6`；历史上 `fea1737` 锁滞后一次（FD-040） |
| 共享状态 | `Work Order Operation.process_loss_qty` ⇔ 原生 `stock_entry.py:1165`、`:3343` | ❌ | 不与 `Work Order.process_loss_qty` 双算；但上道损耗的算法把未建卡、取消待重做的数量也计入（FD-001），0 数量卡又让同步永不触发（FD-002） |
| 共享状态 | Job Card `modified` ⇔ 原生「已被修改」检查 | ❌ | `update_modified=False` 让检查失效（FD-003） |
| 共享状态 | `Item.cn_service_level` ⇔ `Company` 默认服务水平 | ❌ | 字段默认 95 让回落永不发生（FD-009） |
| 共享状态 | `frappe.local.lang` ⇔ 告警标题与 problems | ⚠ | migrate 进程为 `en`，problems 全英文（FD-023） |
| 跨模块数据流 | 安全库存 → 再订货点 → EOQ／定期复核 → 建议单 → 采纳出 MR | ✅ | 365 天回放与 E 修后集成测试走通；本轮复跑全量在内 |
| 跨模块数据流 | 前道卡提交 → 后道级联 → 工序损耗 → Manufacture → 工单 Completed | ⚠ | 主路径成立；五种情形偏离（FD-001～005） |
| 跨模块数据流 | 计件汇总 → Additional Salary → 工资单 | ✅ | 片 2 读码与单测核过 |
| 跨模块数据流 | 质检读数 → SPC 报表与控制图 | ✅ | 手算例对上；工作中心筛选未造命中数据 |

## 业务规则合规核

需求 §4.17 已判本 Stage 不新增、不变更领域不变量。三片逐条核过 BR-001～BR-007（基线未经专家确认）：

| 规则条款 | 本 Round 改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 否 | 合规 | 不碰科目表与报表 |
| BR-002 报表构成 | 否 | 合规 | — |
| BR-003 增值税税率 | 否 | 合规 | — |
| BR-004 增值税月末转出 | 否 | 合规 | — |
| BR-005 城建税与附加 | 否 | 合规 | — |
| BR-006 资产＝负债＋权益 | 间接 | 合规 | 计件经 Additional Salary 走 HRMS 原生分录；工序损耗改的是 Work Order Operation，不直接产 GL。FD-001 会让成品入库数量偏少（工单以错误损耗 Completed），影响的是库存数量与成本，不破恒等式 |
| BR-007 价税分离 | 否 | 合规 | — |

**规则新增／变更检出**：本轮未检出新的领域不变量。FD-037（Nelson 规则 8 取需求字面「两侧均可」）属算法口径选择，不是领域规则，不进业务规则送审。

## 问题清单

证据、复现探针与完整建议在「来源」列所指的片报告该行；本表只给裁决所需的摘要。严重程度：高＝阻断／根因偏离 · 中＝需修 · 低＝技术债 · 观察＝可容许偏差记录。三片之间的重复项已合并（FD-015、FD-023）。

### 中（14 条）

| # | 来源 | 定位 | 问题 | 建议 | 建议档位 | 待裁决点 | 状态 | 用户裁决 |
|---|---|---|---|---|---|---|---|---|
| FD-001 | P2-04 | `production/operation_flow.py:58` | **中（边界：高）**。`sync_operation_loss` 把「工单数量 − 本道卡数量合计」当上道损耗，未建卡、取消待重做的数量也被计成损耗。探针 C：首道只建 600 的卡，工序行记 600＋400 损耗；探针 E：取消一张待重做，工单以损耗 250、成品 750 被置 Completed | 上道损耗改按上一道的累计损耗（或预计产出差）计，不按本道卡数量差 | `出方案修` | 是否改 D 讨论第 7 步已裁决的 A 路线公式 | 待详细修复方案 | 2026-10-17「按建议来」：`出方案修`；待裁决点随该出口处理时答 |
| FD-002 | P2-05 | `operation_flow.py:56` 与总纲偏离 4 | 偏离 4 保留的 0 数量草稿卡原生提交不了，「本道卡全部已提交」永不成立，不补写损耗，Manufacture 报 `OperationsNotCompleteError`（探针 F） | 判「全部已提交」时排除 `for_quantity`＝0 的草稿卡 | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-003 | P2-03 | `operation_flow.py` 各 `set_value(..., update_modified=False)` | 原生「已被修改」检查失效：前道提交前打开的后道表单再保存，把 950 静默改回 1000、`time_required` 回 40000（探针 D）。负荷报表随之失真 | A 更新 `modified` 让原生拦截／B 后道卡保存时按级联结果重算 | `本Session修` | 选 A 还是 B | 已修复 | 2026-10-17「按建议来」：`本Session修`；待裁决点 2026-10-17「按推荐」：A（级联改卡时更新 `modified`） |
| FD-004 | P2-01 | `operation_flow.py:158-163` | 卡从 0 加回数量时，原料需求量按 `0 × 比例` 仍为 0，未按方案 Part2 :179 用工单原料口径重取（探针 B2：末张回到 300，原料 0.0） | `old_qty` 为 0 时按工单 `required_items` 的单位用量重算 | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-005 | P2-02 | `operation_flow.py:123-127` | 拆单扣过多张后取消前道，回不到取消前：`[250,250,200,0]` → `[250,250,200,300]`，末张超过拆分数量 | A 逆序回填至拆分数量上限（改偏离 4）／B 维持「加在最后一张」并接受超拆分数量 | `出方案修` | 选 A 还是 B | 待详细修复方案 | 2026-10-17「按建议来」：`出方案修`；待裁决点随该出口处理时答 |
| FD-006 | P1-03 | `production/bom_selection.py:68-74` | 方案 A10 要求工序费率**预置为工作中心价**；代码只在行费率为 0 时才取。提交过的 BOM 行费率都非零，工作中心调价对选 BOM 无效（探针：0→600，单位成本 12.25 不变） | 有 workstation 取其价，否则取 Workstation Type 价，都无才留行值；补「只调工作中心费率、选择改变」的真 BOM 测试 | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-007 | P1-01 | `replenishment/rules.py:253` | 按订单规则把上游返回的 `Material Transfer`／`Customer Provided` 原样写进建议单，取值域里没有，`upsert` 报校验错，该物料出不了建议 | `Material Transfer`→`Transfer`；`Customer Provided` 另定 | `本Session修` | `Customer Provided` 回落 `Purchase`，还是给建议单加该选项 | 已修复 | 2026-10-17「按建议来」：`本Session修`；待裁决点 2026-10-17「按推荐」：A（建议单加 `Customer Provided` 选项） |
| FD-008 | P1-02 | `rules.py:219-230`；上游 `production_plan.py:1806,1903` | `for_warehouse=None` 时上游改写外层变量，第一种原料的默认仓粘给其后所有原料，净缺料也按那个仓扣（探针：原料 B 默认在制仓，建议单写成原料仓）。偏离 14 的前提不成立 | ① 按物料默认仓分组分别调原生函数／② 只取展开量，仓库与 Bin 自己重取 | `出方案修` | ①、② 还是接受原生行为并写进 README 已知限制 | 待详细修复方案 | 2026-10-17「按建议来」：`出方案修`；待裁决点随该出口处理时答 |
| FD-009 | P1-04 | `fixtures/custom_field.json:219` | Item `cn_service_level` 带 default 95，方案写无默认。新物料一律 95，公司默认服务水平永不生效 | 去掉 default，调大 `modified` | `本Session修` | 是否清空测试站已有物料上的 95 | 已修复 | 2026-10-17「按建议来」：`本Session修`；待裁决点 2026-10-17「按推荐」：A（不清测试站已有值） |
| FD-010 | P1-05 | `custom_field.json:61` | Company 的补货节插在 `default_currency` 之后，把国家、税号、城建税率、母公司等原生字段划进「补货参数」节 | 改 `insert_after` 到原生节末尾 | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-011 | P1-14 | `public/js/replenishment_suggestion_list.js:70-75` | 「立即计算」回调只刷新列表，丢掉返回结果，problems 界面上一条都看不到，属静默失败；表单上也没这个按钮 | 回调里弹出各步 processed／problems | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-012 | P1-12 | `frappe_china/tests/` | 方案点名的 `test_s7_scaffold.py`、`test_bom_selection_hooks.py` 不存在；`test_bom_selection` 全是桩；`run_now` 权限无用例 | 补真 DocType 用例 | `新Session修` | — | 待新Session修 | 2026-10-17「按建议来」：`新Session修` |
| FD-013 | P3-01 | `Spike/P1S7R5-D/ts010-ui.cjs`；D 回执 Part2 | D 步 TS-010 浏览器探针首版连 8000 端口（只服务演示站），在 `erx.localhost` 建了 `_FCT_` 物料、两个批次和 45 条 Error Log；Part2 回执写「已清」未提写过演示站，Part3 才清。现演示站干净，但脚本仍无站点名断言 | 开发守则补「浏览器探针写之前先断言 `frappe.boot.sitename`」；脚本加断言；Part2 回执补更正 | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-014 | P3-02 | `modules.txt` 与首次 migrate | 改 `modules.txt` 后第一次 migrate 退出 0，但 `app_modules` 旧缓存让新模块的 DocType／Report／Page 不同步；D 靠先 clear-cache 再 migrate 解决，没进守则 | 写进开发守则 | `本Session修` | 只写守则，还是另改 `setup.sh`／在自检里加「模块都在 `Module Def`」（后者应走 `出方案修`） | 已修复 | 2026-10-17「按建议来」：`本Session修`；待裁决点 2026-10-17「按推荐」：A（只写守则） |

### 低（19 条）

| # | 来源 | 定位 | 问题 | 建议 | 建议档位 | 待裁决点 | 状态 | 用户裁决 |
|---|---|---|---|---|---|---|---|---|
| FD-015 | P2-11＋P3-11＋片 1 交接 | `hooks.py:116`；`production/piece_rate.py:23-35` | `ensure_component` 排在 `after_migrate` 首位且不吞异常，抛错即中断 migrate、自检也不跑，绕过 §5.4「不 raise」；建出的薪资项没有科目行 | 包 try 并走自检同款告警，或挪到自检之后；科目行另判 | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-016 | P1-06 | `hooks.py:257-293` fixtures 过滤 | 缺 `Material Request-cn_replenishment_suggestion`，下次 export-fixtures 会丢该字段（主会话逐名比对确认只缺这一条） | 补进清单 | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-017 | P1-07 | `replenishment_suggestion.json` | 状态源词用 `Pending`，官方已译「待处理」，正是 A16 的反例；规则 `Against Sales Order` 显示「销售订单」 | 按 A16 换源词 | `新Session修` | 接受「待处理」「销售订单」，还是改源词 | 待新Session修 | 2026-10-17「按建议来」：`新Session修`；待裁决点随该出口处理时答 |
| FD-018 | P1-08 | `rules.py:44-47` | IT-001 修法把三项预留都映射成 `Reserved Qty`（官方译「销售预留数量」），触发依据里四行同名 | 三项各给一个选项 | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-019 | P1-09 | `replenishment/daily.py:80` | `log_error` 参数位次反，Error Log 标题成了截断的结果字典 | 对调参数 | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-020 | P1-10 | `install.py:31-32` | 方案要求取代的 `WHITELIST_TARGETS` 没删，留成导入时求值的别名，测试仍在用 | 删别名，测试改调 `override_targets()` | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-021 | P1-11 | `install.py:58` | 方案外夹带：`order_ok` 改成整序必须等于 `target_app_order`，失败提示文字仍是旧判据 | 保留则改提示文字；或回退 | `本Session修` | 保留新判据还是回退 | 已修复 | 2026-10-17「按建议来」：`本Session修`；待裁决点 2026-10-17「按推荐」：A（保留新判据、改提示文字） |
| FD-022 | P1-13 | `public/js/work_order.js` | 已保存的工单打开（refresh）时不出推荐提示 | 补 refresh 分支 | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-023 | P1-15＋P3-03 | 多处 problems；`install.ALERT_TITLE` 与每日告警标题 | problems 全是英文（总纲 §5.1 要求中文）；两个告警标题不在 csv、不在官方词典。单补 csv 也不生效：常量名不以 `SOURCE` 结尾、守卫查不到，且 migrate 进程语言为 `en`（E 留给 F 判的那条） | 统一用 `_()` 加 `lang="zh"`，补 csv 与守卫 | `本Session修` | 告警标题译还是进白名单（只给管理员看、不在演示屏单内） | 已修复 | 2026-10-17「按建议来」：`本Session修`；待裁决点 2026-10-17「按推荐」：A（译成中文） |
| FD-024 | P2-06 | `tests/test_operation_flow.py` | `disable_capacity_planning` 只跑一种取值；⑥ 只测比例分支；拆单下入库等情形没测 | 补用例（与 FD-001～005 修复一并） | `新Session修` | — | 待新Session修 | 2026-10-17「按建议来」：`新Session修` |
| FD-025 | P2-07 | `production/batch_uom.py:33` | 库存单位为 kg 时，任何非 kg 行单位（如「箱」）都取单支系数；方案换算表本身的缺口 | A 物料加「单支单位」字段／B 约定演示物料只配 kg 与支、记已知限制 | `出方案修` | 选 A 还是 B | 待详细修复方案 | 2026-10-17「按建议来」：`出方案修`；待裁决点随该出口处理时答 |
| FD-026 | P2-08 | `batch_uom.py:8` | `BATCH_UOM_DOCTYPES` 无读取方，死代码 | 删或接到 hooks 生成 | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-027 | P2-12 | `operation_flow.py` 已开工提示 | 方案文案里的「Please adjust manually.」被删 | 补回并补 csv | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-028 | P3-04 | `install.py` `after_migrate` | 无中式公司时只打印 passed，「无对象」那条提示不打印，违反总纲偏离 17 | 通过时连同无对象提示一并打印 | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-029 | P3-05 | `public/js/vendor/` | 只带 echarts 的 LICENSE，缺 `NOTICE`（Apache-2.0 §4(d)）与 `LICENSE-d3`；缺口在方案 | 补两份文件 | `本Session修` | 是否在方案外补（不补则对外交付前法务复核须覆盖） | 已修复 | 2026-10-17「按建议来」：`本Session修`；待裁决点 2026-10-17「按推荐」：A（补 NOTICE 与 LICENSE-d3） |
| FD-030 | P3-06 | `tests/test_spc.py`、`tests/spc_data.py` | 数据对称，分不出 X̿ 定义与单侧限处理；实现对，测试判别力不足 | 把片 3 手算例（不等子组、只有上限）写成常量用例 | `本Session修` | — | 已修复 | 2026-10-17「按建议来」：`本Session修` |
| FD-031 | P2-09 | `public/js/batch_uom.js` | `uom` 变更时与原生 handler 并发请求，谁后返回谁生效，保存时服务端纠正（读码判断） | — | `延迟或不修` | — | 延迟 | 2026-10-17「按建议来」：`延迟或不修`；登记 `SH-P1S7008` |
| FD-032 | P3-07 | 主仓库 `a3e39f2` `docker/scripts/configure_apps.py` | feat 提交里顺手整份改缩进（660 行，`-w` 后 102 行），方案外夹带，不改行为 | — | `延迟或不修` | — | 延迟 | 2026-10-17「按建议来」：`延迟或不修`；登记 `SH-P1S7009` |
| FD-033 | P3-08 | `docs/项目概况.md`「演示站当前状态」 | 仍停在 S6；按流程属 Stage 收口时更新 | 收口时更新 | `延迟或不修` | — | 延迟 | 2026-10-17「按建议来」：`延迟或不修`；登记 `SH-P1S7010` |

### 观察（8 条）

| # | 来源 | 定位 | 记录 | 建议档位 | 待裁决点 | 状态 | 用户裁决 |
|---|---|---|---|---|---|---|---|
| FD-034 | P2-10 | `production/job_card_split.py` | `bench execute` 进程实测不打补丁（方案 HT-004 已知）；S8 若用脚本直调 `make_job_card` 会按 `batch_size` 拆 | `延迟或不修` | — | 延迟 | 2026-10-17「按建议来」：`延迟或不修`；登记 `SH-P1S7011` |
| FD-035 | P2-13 | `piece_rate._rate` | 每条时间行整单读一次工单（N＋1） | `延迟或不修` | — | 延迟 | 2026-10-17「按建议来」：`延迟或不修`；登记 `SH-P1S7012` |
| FD-036 | P2-14 | `operation_flow._update_scheduled_time` | 改量后 `expected_end_date` 不缩短 | `延迟或不修` | — | 延迟 | 2026-10-17「按建议来」：`延迟或不修`；登记 `SH-P1S7013` |
| FD-037 | P3-09 | `production/spc.py` Nelson 规则 8 | 照需求字面「两侧均可」，同侧 8 点也命中；经典定义要求两侧都有 | `延迟或不修` | 保留字面还是改回经典（改则同步需求与测试） | 延迟 | 2026-10-17「按建议来」：`延迟或不修`；待裁决点随该出口处理时答；登记 `SH-P1S7014` |
| FD-038 | P3-10 | TS-016 取证数据 | 28 点里 21 点判异，不是方案说的「两处」；⑥ 已满足，S8 造数时注意 | `延迟或不修` | — | 延迟 | 2026-10-17「按建议来」：`延迟或不修`；登记 `SH-P1S7015` |
| FD-039 | P3-12 | `capacity_load.py` | 四处口径：截断桶标签取自然周一／月一；「未排期」键导出为英文；关产能排程的站点所有卡进「未排期」（测试站 `disable_capacity_planning`＝1，演示站 0）；产能侧不读 `allow_production_on_holidays`（两站均 0） | `延迟或不修` | — | 延迟 | 2026-10-17「按建议来」：`延迟或不修`；登记 `SH-P1S7016` |
| FD-040 | P3-13 | 主仓库 `fea1737` | 没更新 `apps.json`，锁滞后一次，`e1b5621` 从未被锁；现锁正确 | `延迟或不修` | — | 延迟 | 2026-10-17「按建议来」：`延迟或不修`；登记 `SH-P1S7017` |
| FD-041 | P3-14 | `Spike/P1S7R5-D`、`Spike/P1S7R6-E`；`test_translations.py:204-206` | 卫生合格；两个 ht01x 日志为 UTF-16、git 当二进制；两个 check 脚本会跑 `ruff --fix`／`format` 改 app 文件；vendor 目录整体被译名测试跳过 | `延迟或不修` | — | 延迟 | 2026-10-17「按建议来」：`延迟或不修`；登记 `SH-P1S7018` |

**合计 41 条**：中 14、低 19、观察 8，无高。三片原报 43 条，合并两处重复（FD-015＝P2-11＋P3-11，FD-023＝P1-15＋P3-03）。按建议档位：`本Session修` 23 条，`新Session修` 3 条（FD-012、017、024），`出方案修` 4 条（FD-001、005、008、025），`延迟或不修` 11 条（FD-031～041）。

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| E：修后全量 349/349、Node 89/89、Ruff 0 | 本轮自跑 349/349、89/89、Ruff 0 | ✅ |
| E：IT-001～006 已修复 | 片 1 逐条复核修得对；IT-002 修法带出展示副作用 FD-018 | ✅（附 FD-018） |
| E：TS-005／006「选中最低者、调价后改选」 | 只调了原料价；只调工作中心费率时选择不变（FD-006） | ❌ |
| E：TS-012 `_set_card_qty`「与方案一致」 | 从 0 加回时原料量不重取（FD-004） | ❌ |
| E：TS-003 自检「告警、不中断、归位后不再告警」 | 自检本身成立；同列表首位的 `ensure_component` 能中断 migrate（FD-015） | ⚠️ |
| D 回执 Part2：TS-010 浏览器探针数据「已清」 | 曾写过演示站，Part3 才清；回执未提（FD-013） | ❌ |
| D 回执：方案点名的测试文件已建 | 两份不存在（FD-012） | ❌ |
| D 回执 Part3：演示站业务数据仍为 0 | 片 3 只读快照确认为 0 | ✅ |
| E：演示站未上线 E 修复，需重启 `bench start` | web 进程 11:57:38 UTC 自动重载，晚于最后一次改源码；`acf97e6` 无 json／js，不需 migrate／build。worker 读码推断已随任务 fork 加载 | ⚠️（worker 未实证） |

## 当场修清单

用户 2026-10-17 裁决「按建议来」，待裁决点「按推荐」（各项均取 A）。只修裁为 `本Session修` 的 23 项；文件位置在 `frappe-bench/apps/frappe_china/` 下，行号为修后。

| # | 对应问题 | 改动位置（文件:行） | 用户确认于 |
|---|---|---|---|
| 1 | FD-002 | `frappe_china/production/operation_flow.py:56-57`：判「本道卡全部已提交」时排除 `for_quantity`＝0 的草稿卡 | 2026-10-17 |
| 2 | FD-003（A） | `operation_flow.py:147-151`：改卡数量不再 `update_modified=False`，旧表单再保存被原生 `TimestampMismatchError` 拦下 | 同上 |
| 3 | FD-004 | `operation_flow.py:158-163` 与新增 `_required_per_unit`（`:168` 起）：从 0 加回时按工单原料每件用量重取，口径同原生 `job_card.py:742-777` | 同上 |
| 4 | FD-006 | `frappe_china/production/bom_selection.py:66-76`：工价先取工作中心（无则类型）现价，同原生 `bom.py:1037-1050` 的 `update_hour_rate=True` 分支；两者都无才留行值 | 同上 |
| 5 | FD-007（A） | `frappe_china/replenishment/rules.py:250-253` 把 `Material Transfer` 映射为 `Transfer`；`replenishment_suggestion.json` 的请购类型加 `Customer Provided`（`adopt` 原样透传），`modified` 调大 | 同上 |
| 6 | FD-009（A） | `fixtures/custom_field.json` `Item-cn_service_level`：`default` 置空、`modified` 调大；测试站已有值不清 | 同上 |
| 7 | FD-010 | `custom_field.json` `Company-cn_replenishment_section`：`insert_after` 改为 `default_scrap_warehouse`（「库存与生产」页签的生产节末尾），`modified` 调大 | 同上 |
| 8 | FD-011 | `public/js/replenishment_suggestion_list.js`：「立即计算」回调弹框逐公司逐步列 processed／skipped／problems；批量结果逐条列；`frappe_china.replenishment.calculate` 供表单复用；`public/js/replenishment_suggestion.js` 表头加「立即计算」 | 同上 |
| 9 | FD-013 | `docs/开发守则.md` 新节「浏览器探针写之前先断言站点名」；`Spike/P1S7R5-D/ts010-ui.cjs` 写前断言 `frappe.boot.sitename`；D 回执 Part2 末尾补「更正」节 | 同上 |
| 10 | FD-014（A） | `docs/开发守则.md` 新节「改 `modules.txt` 后先清缓存再 migrate」 | 同上 |
| 11 | FD-015 | `frappe_china/hooks.py:116-117`：`after_migrate` 只留 `install.after_migrate`；`install.py:139-157` 在其中 try 调 `ensure_component`，失败回滚并并入 problems 走告警。薪资项无科目行一事不改，交 S8（见下「交接」） | 同上 |
| 12 | FD-016 | `hooks.py` fixtures 过滤补 `Material Request-cn_replenishment_suggestion` | 同上 |
| 13 | FD-018 | `rules.py:38-61` 三项预留各映射到自己的选项（官方译「生产预留数量」「委外预留数量」「生产计划预留数量」）；`replenishment_basis_item.json` 加三个选项，`modified` 调大；`_basis` 不再写备注 | 同上 |
| 14 | FD-019 | `replenishment/daily.py:14、:80`：`log_error(title=…, message=as_json(result))` | 同上 |
| 15 | FD-020 | `install.py` 删 `WHITELIST_TARGETS`；`tests/test_install.py` 改调 `override_targets()` | 同上 |
| 16 | FD-021（A） | `install.py:80-83`：失败提示改写为「应为 {目标顺序}，实际 …」 | 同上 |
| 17 | FD-022 | `public/js/work_order.js`：抽出 `show_bom_recommendation`，已保存草稿 `refresh` 时也提示 | 同上 |
| 18 | FD-023（A） | `safety_stock.py`、`reorder_level.py`、`rules.py`、`daily.py` 的 problems 改为中文「物料 X／仓库 Y：原因」；`install.py:8` 常量改名 `ALERT_TITLE_SOURCE`（守卫可取到），标题 `_(…, lang="zh")`；`daily.py` 新增 `DAILY_ALERT_SOURCE`；`zh.csv` 补两条标题 | 同上 |
| 19 | FD-026 | `production/batch_uom.py` 删死常量 `BATCH_UOM_DOCTYPES` | 同上 |
| 20 | FD-027 | `operation_flow.py:30` 提示补回「Please adjust manually.」，`zh.csv` 同步改为「…，请手动调整。」 | 同上 |
| 21 | FD-028 | `install.py:158-162`：通过时在 passed 之后逐行打印信息性提示（如无中式公司），不告警 | 同上 |
| 22 | FD-029（A） | `public/js/vendor/` 补 `ECHARTS-NOTICE`、`ECHARTS-LICENSE-d3`（取自 Insights 包内同版 echarts 5.6.0，LICENSE 与已有文件 `cmp` 相同）；README 第三方节同步 | 同上 |
| 23 | FD-030 | `tests/test_spc.py` 新增非对称、不等子组、只有上限的常量用例 | 同上 |
| 测试 | — | 新增 `tests/test_s7_audit_fixes.py`：10 条直测（FD-006 真 BOM 只调工作中心价改选、FD-007 调拨映射可写入与 `Customer Provided` 选项、FD-009、FD-010、FD-015、FD-018、FD-028）＋继承 `TestOperationFlow` 的 13 条（含新增 FD-002 走到 Manufacture Completed、FD-003 旧表单被拦、FD-004 加回后原料量） | 同上 |
| 站点 | — | 测试站 `reload_doc` 两个 Stock Plus DocType＋`sync_fixtures`＋`clear-cache`（只动 `test.localhost`）；演示站未动 | 同上 |

**交接给 S8**（FD-015 余项）：计件薪资项「计件工资」由本 app 建时没有公司科目行，S8 跑 Payroll Entry 前须给演示公司补一行（未实测）。

### 复核（本步当场）

拿暴露问题的原探针重跑，输出在 `Spike/P1S7R7-F/p1/`、`p2/` 下的 `*-after.log`：

| 项 | 修前 | 修后 |
|---|---|---|
| FD-002 | 探针 F：Manufacture 报 `OperationsNotCompleteError` | 第二道 `(700, 300, Completed)`，Manufacture 入库 700、损耗 300，工单 `Completed`；0 数量卡仍提交不了（原生要求时间行），不再挡路 |
| FD-003 | 探针 D：旧表单保存成功，库内回到 `1000／40000` | `TimestampMismatchError`，库内保持 `950／38000` |
| FD-004 | 探针 B2：末张回到 300，原料 0.0 | 新用例：末张回到 300，原料 600（每件 2） |
| FD-006 | 工作中心 0→600，单位成本 12.25 不变 | 12.25 → 39.25；新用例只调工作中心价即改选 |
| FD-007 | `upsert` 报「物料需求类型不能为 Material Transfer」 | `order_props [('Transfer', 6.0)]`、`upsert_ok` |

**定向测试**：`test_s7_audit_fixes` 23/23；`test_operation_flow` 6/6、`test_install` 18/18、`test_after_migrate` 3/3、`test_spc` 5/5、`test_bom_selection` 8/8、补货各模块（rules 4、levels 9、integration 4、daily 2、suggestion 4）、`test_translations` 20/20、`test_translation_quality` 13/13 全过。首轮跑出三处修正：集成用例因测试站 DocType 未 reload 报「依据不能为 Reserved Qty for Production」（reload 后过）；混排守卫拦下译文「frappe_china 覆盖自检未通过」（改为「中国本地化覆盖自检未通过」）；新用例本身两处造数错（工作中心 `hour_rate` 被 validate 重算、拆单下第三道卡取错下标），已改。Node 89/89，Ruff `check` 全过、`format` 通过。

**修后全量**：Python **373/373**：364 integration（1845.2s）＋5 旧式类＋4 未分类，均 OK，`EXIT=0`（`Spike/P1S7R7-F/python-full-after-fix.log`），比修前 349 多 24 条新增、一条未少；Node 89/89；Ruff `check` 全过、`format --check` 通过。

**未上演示站**：本轮改了两个 DocType json 与 fixtures，演示站要 migrate（先 `clear-cache`）才生效；按 S7 纪律，演示站写操作留到修复全部走完、Stage 收口前统一做，本步只动测试站。修复尚未提交（`frappe_china` 工作区 19 改 3 新）。

## 总体判断

**部分满足**。十七个任务都已落地，主链都生效：补货三规则与采纳、安全库存与再订货点、选 BOM、批次系数、拆单、计件、负荷报表、SPC 与控制图。全量 349/349。关键缺口有三处：

1. **工序数量传递（TS-012）在常见操作下会算错**。首道少建卡或取消一张待重做，工单会以错误损耗 Completed（FD-001）；保留的 0 数量卡会让 Manufacture 报错（FD-002）；旧表单保存会把级联结果写回原值（FD-003）。FD-001 要改 D 讨论已裁决的公式，须先出方案。
2. **按订单补货对上游的假设不成立**：原料默认仓不同时仓库会粘连（FD-008），默认请购类型为调拨或客户提供时出不了建议（FD-007）。
3. **选 BOM 不看工作中心调价**（FD-006），与 A10 相反。

其余以配置默认值、界面静默与留档为主。

## 状态值

`有发现`——41 条（中 14、低 19、观察 8，无高）。用户 2026-10-17 裁决「按建议来」，待裁决点「按推荐」。

**按去向分组**（规范 §2.3 执行规则 4）：

| 去向 | 项 | 下一步 |
|---|---|---|
| `本Session修` → `已修复` | FD-002～004、006、007、009～011、013～016、018～023、026～030（23 项） | 已在本步修完，见「当场修清单」 |
| `新Session修` → `待新Session修` | FD-012（补方案点名的测试文件与 `run_now` 权限用例）、FD-017（建议单状态与规则的源词按 A16 换，待裁决点到时答）、FD-024（`test_operation_flow` 补用例） | 唤起 SB（附属本 R7），修完回 F 复核 |
| `出方案修` → `待详细修复方案` | FD-001（上道损耗公式，改 D 讨论已裁决的 A 路线）、FD-005（加回规则：逆序回填还是加在最后一张）、FD-008（按订单规则的仓库取法）、FD-025（批次系数的单支单位识别） | 回 C 出补充方案 → D 执行；各项待裁决点在 C 步定 |
| `延迟或不修` → `延迟` | FD-031～041（11 项） | 进本 Stage 延迟需求登记册 |

FD-024 与 FD-001、FD-005 改同一文件同一路径，宜在 C 步方案里一并排进，SB 只做 FD-012、017。是否这样合并由用户在起下一步时定。

## 复核建议

1. **FD-001 的定级在「中／高」之间**。它能让工单以错误损耗完工、成品少入库，但要靠「首道少建卡」或「取消待重做」触发。若 S8 的演示脚本有取消重报的步骤，应改判高，并在 S8 造数前修掉。查法：`Spike/P1S7R7-F/p2/probe_cancel.py` 的探针 E，看工单 `status` 与 `process_loss_qty`。同理，FD-013、FD-014 定「中」也有反方理由：前者演示站已清干净，后者 D 已绕过；可降「低」。
2. **查得最浅的是前端三个 js 与 `batch_uom.js` 并发**（FD-011、FD-022、FD-031）。都只读了码，没上浏览器。查法：在测试站补货建议单列表点「立即计算」，造一个会进 problems 的物料，看界面是否有提示。
3. **开放找漏的盲区**：只对照了方案与需求，没交叉核对 S4～S6 已交付功能的历史行为（只靠全量回归兜底）。`sync_operation_loss` 与 `track_semi_finished_goods`、超产比例、纠正卡的交互，以及汇总单提交后取消来源 Job Card 是否被拦，都只读了码。没有生产与财务领域专家看过口径。
4. **拿不准处**：FD-008 的问题根在上游，偏离 14 写的仓库取法算不算对用户的承诺，两种读法都通。FD-021 和 FD-032 算不算方案外夹带：前者与 TS-003 同提交、方向与 `PH-P1073` 一致，后者只改格式、不改行为。

## 版本交付

用户 2026-10-17 指示「提交并推送」。当场修提交 `a091cd7ce6045abdd92da60f269f52f28f2c9d33`，已推送 `FrappeChina/main`；主仓库 `docker/apps.json` 的 `frappe_china` commit 同步更新，与本报告及 Part1～3、两份概况、开发守则、D 回执 Part2 更正、`Spike/P1S7R5-D/ts010-ui.cjs` 与 `Spike/P1S7R7-F/` 一起提交。`Spike/P1S7R7-F/` 为探针、修复脚本与两次全量日志，均依赖当时站点状态，无可重生成产物，全部保留。
