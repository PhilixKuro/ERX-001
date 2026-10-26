# 审核报告·Part2（对象：`frappe_debug` `d8614a5` 的 `scenario/`、`builders/`、`data/scenario.yaml` / 审核标准：R05 方案总纲＋Part2，R04 需求 §4.3、§4.9、§4.11、§4.14、§4.17、§八 AC-018／019）

**轮次**：P1-S8-R8 F 片2｜**日期**：2026-10-26｜**审核者**：Claude（Opus 5.5，独立 Session，未参与 C／D／E）
**被审代码**：`frappe-bench/apps/frappe_debug` HEAD `d8614a5`（工作区无未提交改动）；调用的 `frappe_china` `75ceb04`、ERPNext fork `a729571`（只核调用契约）
**探针**：`Spike/P1S8R8-F/p2/`。`probe_rejected_billing.py` 在 `s8verify.localhost` 事务内跑、`rollback`，残留核 0、`Error Log` 增量 0；`gate_params.py` 只读解析（临时 yaml 用后即删）；`lock_9p.py` 只在本目录建锁文件、用后删除。只读 SELECT 对 `s8eoqformal.localhost`、`s8verify.localhost`。未碰 `erx.localhost`、`test.localhost`。

## 覆盖自证

- **读全的依据**：总纲全文（A1～A20、§四偏离 1～19、§五契约、§六 HT-001～022、§十纪律）；Part2 全文（SL-011 ①～⑫、TS-013～017 具体改动与验证方式）；需求 §4.3、§4.9 全节、§4.11、§4.14、§4.17、§八 AC-017～019；开发守则全文；业务规则全表。
- **读全的代码**：`scenario/` 的 `params.py`、`day.py`、`slots.py`、`monthly.py`、`opening.py`、`masters.py`、`runner.py`、`targets.py`、`support.py`、`rehearsal.py`；`builders/` 全部 7 个文件；`data/scenario.yaml`；`hooks.py`；`demo/scene_date.py`、`demo/operation.py`、`demo/workspace.py`（与生成器共享状态的部分）；`quality.py` 1～300 行（计划加载、指纹、导出）、`verify.py` 1～110、300～360 行。
- **只读到调用面的**：`frappe_china` 的 `replenishment/daily.py`、`rules.py` 定期复核段、`replenishment_suggestion.py` 的 `adopt`／`ignore`、`piece_rate.py` 的 `make_piece_rate_summaries`、`closing.py` 函数表；ERPNext `job_card.py` 的 `validate_time_logs`／`get_overlap_for`／`validate_sequence_id`、`purchase_receipt.py` 的 `make_purchase_invoice`、`supplier_scorecard.py` 默认等级。
- **跳过及原因**：`quality.py` 的筛选算法 `screen_quality_samples` 只扫了入口（用户已批准的方案，E 已核）；`verify.py` 其余检查只看了判据形状；测试文件只抽看了 `test_day.py` 的工位/员工断言；全量测试不跑（主会话在跑）；`erx.localhost` 上的终版数据不碰。
- **数据站的局限**：`s8eoqformal` 是 10-22 用 `e5a9e6c` 生成的数据，早于 R7 的 IT-012／013／018 修复；`s8verify` 更旧且没迁移出 `Demo Progress`（探针因此须像生成器那样置 `in_scenario_generator`）。凡用这两站数据下的结论，都另核了 `d8614a5` 里对应代码行未变（`git diff e5a9e6c d8614a5 -- scenario/day.py` 里员工、分配器、商机金额、客户名几处没有改动）。

## 验证门实跑结果（本片只自跑小门）

| 门 | 声称值 | 实测值 | 与基线对比 | 一致否 |
|---|---|---|---|---|
| Ruff check／format（`scenario/`＋`builders/`） | 通过（D／E） | `All checks passed!`、`21 files already formatted` | — | ✅ |
| SL-011 ① 参数校验 | 六类各一例报错（D 11/11） | `gate_params.py`：缺键、规则次序颠倒、损耗率越界、异常段落在场景外、E 晚于今天，五类都在建单前报错且带键名；起止颠倒在 `runner._validate_range:177` | — | ✅ |
| E＝2026-10-20 的日期推导 | S＝2025-10-01 | S 2025-10-01、D1 2026-01-07、D2 2026-04-01；三段 [10-01,01-06]／[01-08,03-31]／[04-02,10-19] | 与方案写死值一致 | ✅ |
| 9p 挂载上 `filelock` 跨进程互斥 | 未声称 | `lock_9p.py`：`/workspace` 与 `/tmp` 两处子进程都 `TIMEOUT`（互斥生效） | — | ✅（高风险点自核） |
| `s8eoqformal` 全账借贷 | 平衡 | `sum(debit)-sum(credit)=0.00` | — | ✅ |
| 全量 Python／Node | 175/175 等（E） | 未跑（主会话在跑） | — | — |

## 逐项落地核查

| 意图层依据 | 要求层要求（方案任务） | 定位 | 落地 | 生效否 | 偏差说明 |
|---|---|---|---|---|---|
| §4.9.1 参数文件 | TS-013 `Scenario`／`load_scenario`／`dates`，整份校验 | `params.py:15-23, 308-480` | ✅ | ✅ `runner.generate:267`、`demo/config.py:199-209` 都在用 | 结构与方案键名一致；多出 `purchase`、`qty_phases`、`product_weights`、`seed`（后两者 D 已登记，`qty_phases` 由 IT-014 补登）。**定期复核起算日没校验**，见 P2-06 |
| §4.3.1 时间线 | D1／D2／三段推导，E 不晚于今天 | `params.py:350-439` | ✅ | ✅ | 实测见验证门 |
| ADR-0010 共用建单辅助 | TS-014 `builders.dates.dated` | `builders/dates.py:6-20` | ✅ | ✅ 经 `insert_and_submit` 走全部建单 | — |
| §4.9.3-1 全部经提交 | TS-014 builders 走原生 mapper→dated→insert→submit | `builders/*.py` | ✅ | ✅ | grep `docstatus: 1` insert／裸写 GL、SLE：0 处（只有 `support.py:79` 写 `__UserSettings`，是方案 TS-016-7 要求的）。`selling.py:19-28` 两个函数无调用方，见 P2-10 |
| §4.9.2 主数据 | TS-014 `build_masters` 幂等 | `masters.py:592-645` | ✅ | ✅ | 只用「支」「千克」（`:594-596` 不存在即报错）；产能计划关（`:614`）。客户池 30 个只被第 6／7 幕目标单用，见 P2-04 |
| §4.9.2 期初 | TS-014-3 借 1002＋1601、贷 3001 | `opening.py:411-458` | ✅ | ✅ | `is_opening=Yes` 为 D 登记偏离 |
| §4.9.2 每日全链 | TS-015 `run_day` 固定顺序 0～6 | `day.py:575-605` | ⚠️ | ✅ | 步骤 0、2、3、6 符合；步骤 1 商机金额、概率、状态没按要求造（P2-04）；步骤 4 拒收接上了，但拒收数量照开票付款（P2-01）；步骤 5 报工全挂一名员工（P2-02）、后道工序报工时间早于前道（P2-03） |
| §4.9.3-4／5 不跨天、不重叠 | `SlotAllocator.take` | `slots.py:8-89` | ✅ | ✅ `day.py:394` | 同工位不重叠 E 已核；**同员工跨工位重叠 2130 对**（P2-02） |
| §4.9.3-3 按 BOM 工时报 | 报工分钟＝`time_required` | `day.py:417` | ✅ | ✅ | — |
| §4.9.3-6 拆单补丁 | `_patch_production_hooks` | `runner.py:243-248, 309` | ✅ | ✅ | E IT-016 已核卡数 |
| §4.9.3-7 SPC | 读数分布＋异常段 | `day.py:436-498`、`quality.py` | ✅ | ✅ | 用户批准的「候选＋筛选」；计划与 E 绑定，换预跑日要先重做计划（P2-07） |
| §4.11 三规则依次 | 步骤 0 按启用日打勾 | `day.py:593-598` | ✅ | ⚠️ | `s8eoqformal` 实测：按订单 2025-10-02 起、EOQ 2026-02-02 起、定期复核 2026-06-10 起，三段都有采纳。但定期复核只在 S＋14k 天那天出，S 落在周日时永不出（P2-06） |
| §4.9.2 采购、供应商 | 步骤 3 选当月最低价（IT-012） | `day.py:200-222` | ✅ | ✅ | 逻辑对；**供应商价格走势参数让 6 家全年拿不到单**，评分 0、原生自动禁采（P2-05） |
| §4.9.2 拒收 | 步骤 4 按比例填拒收（IT-013） | `day.py:225-271`、`buying.py:44-67` | ⚠️ | ✅ | 入库对；发票、付款含拒收数量，暂估应付留借方余额（P2-01） |
| §4.9.2 缺料 | TS-016-2 判料够、记推迟、窗口内压到货 | `day.py:287-350` | ✅ | ✅ | 事件分布 2025-10～2026-09 均有 |
| §4.9.2 每月 | TS-016-1 计件、折旧、结转、底稿；D2 上月跳过、第三段补结 | `monthly.py:318-350, 382-396` | ✅ | ✅ | 折旧借 5602070 贷 1602020（Depreciation Entry）；补结在 D2＋1 开头；IT-018 制造费用借 4101 贷 1002（`:192-233`），先于结转生成、按 marker＋日期幂等 |
| §4.9.3-9 第 6 幕 | TS-016-3 超载排程 | `targets.py:118-196` | ✅ | ✅ | 挂在一张 66,240 支的合成订单上，不是方案写的「真实订单」（P2-08） |
| 偏离 16 第 7 幕 | TS-016-4 交货 D2 已入库订单 | `targets.py:199-205`、`monthly.py:367-368` | ✅ | ✅ | D2−28 建单，`find_act7_order` 按 `po_no=S8-ACT7` 取 |
| §4.9.3-10 第 9 幕 | TS-016-5 提前期内留置 EOQ、E−1 忽略 | `targets.py:208-240`、`day.py:184` | ✅ | ✅ | 另在 E−1 段末直接 `run_daily(sc.E)`，方案没写（P2-09） |
| 偏离 12 评分 | TS-016-6 E−1 后建按月记分卡 | `support.py:250-294`、`monthly.py:373` | ✅ | ✅ | 评分标准是 AI 自拟两条（P2-05、业务规则核） |
| §4.9.3-11 列表设置 | TS-016-7 每段末清 | `support.py:297-324`、`monthly.py:365-366` | ✅ | ✅ | 只在 D1−1、D2−1、E−1 清；幕间快照前清不清归片 3 |
| §4.9.4 调用方式 | TS-017 `start_generate`／`generate_status`／`generate` | `runner.py:107-365` | ✅ | ✅ 彩排页 `rehearsal.js:129-147` 消费 | 签名比 §5.3 多 `job_id`、`preview_quality_schedule`，兼容；每日 savepoint＋commit，失败回滚当日并整段停 |
| §4.9.3-2 不乱序补单 | `from_date` 不早于最后生成日次日 | `runner.py:175-225` | ✅ | ✅ | — |
| §4.9.3-12 E 不晚于今天 | `load_scenario`／`_validate_range` | `params.py:356`、`runner.py:179` | ✅ | ✅ | — |
| HT-019 耗时 | 整年计时 | D 回执 1793.8 秒 | ✅ | — | 采信 D 与 E 的计时，没复跑 |

## 集成检查

| 集成点类型 | 具体落点 | 两端一致否 | 说明 |
|---|---|---|---|
| 事件/消息 | 本片不发不收实时事件；进度走状态文件 `private/frappe_debug/generate.json` | ✅ | 写端 `_write_status`（tmp＋`os.replace`），读端 `_read_status` 带 9p 重试（IT-017）→ `generate_status` 返回 `state/day/error` → `rehearsal.js:129-147` 只读这三个键 |
| 接口契约 | 开发守则跨 Phase 契约「演示操控的事件协议 `erx_demo_step`」 | 不涉及 | `frappe_debug` 全仓 grep `erx_demo_step` 0 处；ADR-0014 配置驱动已取代，生成器不发不收 |
| 接口契约 | 总纲 §5.3 `start_generate`／`generate_status`／`generate` | ✅ | 返回值与方案一致；`start_generate` 只限 Administrator、限 POST |
| 接口契约 | `frappe_china.replenishment.daily.run_daily(as_of_date, company)` | ✅ | 生成器按日期先后、只在工作日调；不 commit，由生成器每日提交；`ok=False` 即抛（`day.py:173-175`） |
| 接口契约 | `replenishment_suggestion.adopt(name)`／`ignore(name)` | ✅ | `adopt` 建的物料需求日期＝`calculation_date`，即场景日；生成器以 Administrator 跑，过 `only_for` |
| 接口契约 | `piece_rate.make_piece_rate_summaries(company, as_of_date)` | ✅ | 月末调、按员工×期间幂等；`problems` 非空即抛（`monthly.py:236-242`） |
| 接口契约 | `closing.generate_month_end_closing`／`month_closing_state` | ✅ | 按月顺序；D2 上月推迟、D2＋1 补结 |
| 接口契约 | `job_card_split.ensure_patched`／`overproduction.ensure_patched` | ✅ | 同步与后台两条路径都显式调 |
| 接口契约 | `stock_entry_accounts.normalize_fallback_operating_cost`（IT-018） | ✅ | 生成器 `insert_and_submit` 两次触发 `before_validate`，靠该函数幂等；`_absorbed_overhead` 依赖 410199 贷方＝实际工序成本 |
| 共享状态 | 场景终点 E：登记表 `scenario_end` → `load_scenario` 缺省 | ✅ | `workspace.py:59-66` 写，`params.py:309-314` 读；有 `work_db` 才生效 |
| 共享状态 | `frappe.flags.in_scenario_generator` → `scene_date.apply_scene_date` 跳过 | ✅ | `runner.py:284`、`scene_date.py:10`；`finally` 复原 |
| 共享状态 | 站点操作锁 `frappe_debug_demo_operation.lock` | ✅ | 生成全程持有，快照、换库期间不能生成，反之亦然；`_run_generate` 等 10 秒 |
| 共享状态 | `quality-plan.json` | ⚠️ | 生成器要求有计划才能跑过 SPC 窗口，计划绑 E（P2-07） |
| 跨模块数据流 | `Scenario Event` 缺料推迟 → 策略对比报表缺料次数 | ✅（采信 D／E） | 报表自有判据，D／E 逐段对上 37／3／1；片 1 应复核报表侧 |
| 跨模块数据流 | 场景日期 → 演示配置 `dates`／`segments`／`rule_dates` | ✅ | 唯一来源 `params.dates` |
| 跨模块数据流 | 段末前置 → 演示各幕（`S8-ACT7`、未转换线索、默认 BOM、超载卡、EOQ 建议） | ✅ | 见交接摘要 |

## 业务规则合规核（规则未经专家确认）

| 规则条款 | 本 Round 改动是否涉及 | 结论 | 备注 |
|---|---|---|---|
| BR-001 小企业会计准则 | 是：场景公司建账 | 合规 | `masters.py:44-55` 用 `CN_CHART_NAME` |
| BR-002 报表种类 | 间接：月结与现金流量底稿 | 合规 | 生成器每月提交底稿、结转；报表本身归片 1 |
| BR-003 增值税税率 | 是：销售／采购发票 | 合规 | 货物 13%（`s8eoqformal` 发票税行 13%） |
| BR-004 应交增值税转出 | 间接：月结 | 合规（调用原生月结） | 实现归片 1 |
| BR-005 附加税 | 间接：月结 | 合规（调用原生月结） | 同上 |
| BR-006 资产负债表平衡 | 是 | 合规 | 全账借贷差 0.00；终版第 7／8 幕平衡采信 E 回读。P2-01 的暂估应付借方余额不破坏平衡，但会让应付类科目出现反向余额 |
| BR-007 价税分离按分四舍五入 | 是：含税价模板倒算 | **草案·待专家确认**（P2-11） | 36/326 张销售发票、20/155 张采购发票的税额与 round(不含税×13%,2) 差 0.01（例 `ACC-SINV-2026-00009`：不含税 10,088.50，税 1,311.50，按规则应 1,311.51）。原因是含税价按「含税−不含税」倒算税额 |
| BR-008 完工入库不产生损益 | 是 | 合规 | `s8eoqformal` 制造入库 GL 662 行全在资产类；IT-018 制造费用凭证借 4101（资产类）贷 1002 |
| 新规则（AI 推断）① 实际制造费用＝当月吸收额 | 是（IT-018） | 草案·待领域专家确认 | 已登记 `SH-P1S8010` |
| 新规则 ② 生产设备折旧计入管理费用 | 是（偏离 13） | 草案·待领域专家确认 | 已登记 `SH-P1S8005` |
| 新规则 ③ 拒收数量照开票照付款 | 是（IT-013 修复引入） | 草案·待领域专家确认 | 见 P2-01，未登记，未经裁决 |
| 新规则 ④ 供应商评分＝准时率 50%＋合格率 50%，分母加 1 | 是（`support.py:255-270`） | 草案·待领域专家确认 | 无单据的供应商得 0 分并被原生自动禁采，见 P2-05 |

## 自证复核

| 被审产物声称 | 实际复核结果 | 一致否 |
|---|---|---|
| D Part2 TS-015「同工位工序卡不重叠、工时等于卡工时并关联员工」 | 同工位不重叠属实；「关联员工」是全部 4208 条时间行都挂 `HR-EMP-00001` 一人，同一员工跨工位重叠 2130 对 | ⚠️ 字面真，实质不符（P2-02） |
| E IT-013 修复「14 天集成实测拒收行全部落不合格品仓」 | 入库侧属实；没核发票侧：拒收 5／100 时发票按 100 开、付 800（应 760），暂估应付余借 35.39 | ⚠️ 修复不完整（P2-01） |
| E IT-012 修复（选当期最低价），其「连带：6 家评分全 0」随修复消除 | E 终版回读表本身只列 6 家有单（01／02／05／06／09／10），03／04／07／08／11／12 仍全年无单，评分仍为 0 | ❌（P2-05） |
| D「12 家供应商各 12 期评分全提交且总分非空」 | 字面真；`s8eoqformal` 6 家 12 期全 0，9 家被原生置 `prevent_pos=1` | ⚠️ |
| D「三段建议→物料需求→采购订单」 | 实测采纳：按订单 117、EOQ 26（2026-02-02 起）、定期复核 14（2026-06-10 起） | ✅ |
| D「GL／SLE 逐单据 0 差异」 | 全账借贷差 0.00；没逐单据复算 | ✅（部分复核） |
| D「CRM 商机带金额、概率、预计成交日」（TS-015 步骤 1 完成） | 335 张商机全部 `Qualification`，`deal_value` 0、`expected_deal_value` 全为 1000、概率全为 60 | ❌（P2-04） |

## 问题清单

| # | 严重程度 | 定位 | 问题描述 | 违背的标准/意图 | 建议 | 建议档位 | 待裁决点 | 状态 | 用户裁决 |
|---|---|---|---|---|---|---|---|---|---|
| P2-01 | 中 | `day.py:260-283`、`builders/buying.py:44-73`；站点 `Buying Settings.bill_for_rejected_quantity_in_purchase_invoice=1`（原生缺省） | IT-013 接上拒收后，原生采购发票映射在该开关为 1 时按「实收＋拒收」开票，生成器随即全额付款。探针（`probe_rejected_billing.py`）：订 100、拒 5，入库 95（672.57），发票 100（800），付款 800，`220202 应付账款-暂估库存` 余借 35.39。整年约 2% 的采购额会这样处理：拒收品照付款、暂估应付挂借方余额，拒收品又以 0 成本留在「不合格品」仓 | 需求 §4.9.2「收货（填拒收数）→ 采购发票 → 付款」的会计正确性；BR-006 精神（科目余额方向） | 生成器前置把该开关置 0（或发票映射后按合格数开票），补一条用例核 220202 归零；随后重跑隔离预跑与整场预跑 | `新Session修` | 拒收品是否开票付款（原生缺省「开票」是为了后续退货、扣款流程；演示里没有退货环节） | 待裁决 | |
| P2-02 | 中 | `day.py:409-411` | 每张工序卡的报工员工都取「公司第一个在职员工」，12 名员工只有 `HR-EMP-00001` 有时间行（4208 条）。结果：计件汇总每月只有 1 张（第 6 幕计件列表只见一人）；同一员工同时段在不同工位报工 2130 对（原生只在同工位内查重叠，拦不住） | 需求 §4.9.1「员工与计件单价」、方案 TS-014「员工（带性别）」及参数 `staff.employees: 12` 的意图；§4.9.3-5 不重叠的业务含义 | 按工位或工序给员工分组轮派（参数里加工位→员工映射，或按 rng 选当日空闲员工），并在 `verify` 加同员工不重叠检查 | `新Session修` | — | 待裁决 | |
| P2-03 | 中 | `day.py:394`（`allocator.take` 未传 `not_before`）、`day.py:423`（`patch.object(JobCard, "validate_sequence_id", …)`）、`day.py:432` | ① 同一工单的工序报工时间不按工序顺序：332 个工单里 89 个，后道卡开工早于前道卡（例 `MFG-WO-2026-00006`：回火 09:04、磨端 10:06，卷簧却在 13:00）；② 完工入库的过账时间（09:xx）早于当天报工结束，1493 行；③ 提交工序卡时把原生 `validate_sequence_id` 换成空函数，方案没写，回执与 README 均未登记。演示命名函数 `demo/functions.py:185-221` 已用 `not_before` 处理，生成器没用 | 方案 TS-015 步骤 5「按工序顺序报工」；开发守则「静默失败」与覆盖登记的精神（绕过原生校验无登记） | 生成器给 `take` 传上一道卡的止时作 `not_before`；完工入库时间取末道卡止时之后；说明并登记绕过 `validate_sequence_id` 的理由，能去掉就去掉 | `新Session修` | 是否保留对 `validate_sequence_id` 的绕过 | 待裁决 | |
| P2-04 | 中 | `day.py:91-137` | ① 商机金额写死 `expected_deal_value: 1000`、概率写死 60、预计成交日恒为当天＋7；`deal_value` 0；转成订单后状态不推进，335 张商机全停在 `Qualification`；② 每张订单新建一个「场景客户 日期-序号」客户，全年 334 个一次性客户，`parties.customers: 30` 建出的客户池只被第 6／7 幕目标单用了 1 个 | 需求 §4.9.2「CRM 线索与商机（带金额、概率、预计成交日，状态不来回切）」、方案 TS-015 步骤 1「金额、概率、预计成交日；状态单向推进」；需求 §4.9.1「客户与供应商数量（数十个）」 | 金额取报价单金额、概率按阶段、成交后推进到成交状态；订单从客户池抽客户（CRM 线索挂已有组织） | `新Session修` | 商机要推进到哪一步（成交即 Won，还是保留部分在途）；客户是否必须复用 30 个池 | 待裁决 | |
| P2-05 | 中 | `data/scenario.yaml:158-170`、`support.py:255-292`；原生 `supplier_scorecard.py:380-392` | 价格走势让每种线材始终只有两家能成为当月最低价，03／04／07／08／11／12 六家全年无单（E 终版回读的订单分布同样只有 6 家）。自拟评分公式对无单据者给 0 分，原生默认等级把 0～30 分判为 Very Poor 并自动给供应商置 `prevent_pos=1`：`s8eoqformal` 12 家里 9 家被禁止下采购单。第 9 幕要看评分并「确认供应商」时，一半供应商 0 分且无法下单 | 需求 §4.9.3-10、AC-019「无空分」的意图（区分度）；E IT-012 连带问题未消除 | 调价格走势让各家轮流有单，或评分改用原生默认标准与变量；无单据的期不判 Very Poor，或在场景里关掉等级的禁采动作 | `新Session修` | 选调参数还是改评分公式；第 9 幕是否需要能对任一家下单 | 待裁决 | |
| P2-06 | 中 | `masters.py:610`（`cn_review_start_date = S`）、`day.py:590-591`（非工作日直接返回，不调 `run_daily`）、`frappe_china` `rules.py:151-153` | 定期复核只在 S＋14k 天当天出建议，这些天都和 S 同一星期几。S 落在周日时，复核日全是周日，生成器周日不调 `run_daily`，覆盖 N 天规则全年一条建议都不出，参数校验也不拦。探针：E＝2026-06-15 → S＝2025-06-01（周日），复核日全为 Sunday。按「E＝预跑当天」，2027 年 2、3 月预跑时 S 为 2026-02-01／03-01，都是周日 | AC-018「三种规则按启用日依次出建议、各段都有采纳单据」；§4.9.3「参数文件加载时校验」 | `cn_review_start_date` 取 `rule_periodic_from` 当天或之后的第一个工作日；`load_scenario` 校验复核日至少有一天落在工作日；补一条 S 为周日的用例 | `本Session修` | — | 待裁决 | |
| P2-07 | 中 | `runner.py:286-299`、`quality.py:56-67, 104-114, 241-258`；`README.md` 第 17～46 行 | SPC 候选计划的指纹含 S／D1／D2／E 与整份参数，SPC 窗口 [D2−90, D2] 横跨第一、二段。换一天预跑或改任何参数，旧计划即失效，第一段一开跑就报「缺少完整候选计划」或指纹不符。重做计划要先在另一座隔离清洁站跑完整年（约 30 分钟），再 `bench execute … export_quality_sample_plan` 并手工拷到演示站。README 的部署与「整场预跑」步骤都没提这一前置，彩排页开播前也不检查 | 需求 §4.4.9 彩排即预跑、DEC-038「E＝预跑当天」与生成器之间拼装不上；需求 §4.9.4「重置：从清洁基准起新工作库重跑」 | README 补「换预跑日或改参数前先重做 SPC 计划」的完整步骤；彩排页开播前校验计划与当前 E 的指纹 | `本Session修` | 是否把计划生成并入彩排流程（改动面大，可另出方案） | 待裁决 | |
| P2-08 | 低 | `targets.py:155-162` | 第 6 幕超载的排程卡挂在一张专门生成的 66,240 支订单（`S8-ACT6`，平时订单均值约 3,800、最大 14,500）上，不是方案写的「挂在交货日在第三段的真实订单的工单上」 | 方案 TS-016-3 字面；§4.9.3-8「不靠调参凑结果」精神 | 记为偏离补登回执；或拆成几张常规量订单 | `延迟或不修` | — | 待裁决 | |
| P2-09 | 低 | `monthly.py:371-378` | 生成器在第三段最后一天（E−1）段末直接 `run_daily(sc.E)`，提前写出 E 日的补货建议，并改写物料的安全库存与再订货点；方案只要求 E−1 忽略留置的建议。与 §4.3.2-1「该幕当天的单据只由彩排产生」字面冲突；第 9 幕现场再调一次是幂等重算，演示不受影响 | 方案外夹带；§4.3.2-1 | 补登偏离并说明理由（让 `verify` 在生成后即可核第 9 幕前置），或移到 `verify` 里在事务内跑后回滚 | `延迟或不修` | 是否保留 | 待裁决 | |
| P2-10 | 低 | `builders/selling.py:19-28` | `make_and_submit_delivery_note`、`make_and_submit_sales_invoice` 无调用方；生成器另写了 `day.py:501-526` 的发货单（为插质检）与发货单→发票映射 | 方案 TS-014「builders 生成器与命名函数共用」；死代码 | 删除或改由生成器调用 | `延迟或不修` | — | 待裁决 | |
| P2-11 | 观察 | 场景销售／采购发票（含税价模板 `13% 专票 含税价`） | 36/326 张销售发票、20/155 张采购发票的税额比 round(不含税×13%,2) 少或多 0.01，原因是含税价倒算 | BR-007（舍入方式本身待专家确认） | 并入 `SH-P1S8005` 交会计确认：含税价倒算是否适用 BR-007 | `延迟或不修` | BR-007 是否覆盖含税价倒算 | 待裁决 | |
| P2-12 | 观察 | `masters.py:616`、`day.py:127`、`rehearsal.py:97` | 生成器改了全局 `Selling Settings.allow_sales_order_creation_for_expired_quotation=1`；历史报价单 `valid_till` 取 max(场景日＋30, 今天)。D 回执复核建议已自陈 `valid_till`，全局开关未登记 | 方案外夹带（影响演示站全局设置） | 回执补登 | `延迟或不修` | — | 待裁决 | |

（严重程度：高＝阻断/根因偏离 · 中＝需修 · 低＝技术债 · 观察＝可容许偏差记录）

## 跨片一致性（交接摘要）

**本片依赖什么**

- 片 1（`frappe_china`）：`run_daily(as_of_date, company)` 的四条接口约定（按日先后、只算到当日、幂等、不晚于今天）；`adopt` 建的物料需求日期＝`calculation_date`；`make_piece_rate_summaries` 按员工×期间幂等；`generate_month_end_closing` 要求前月已结、`month_closing_state` 的 `vouchers/complete/issues` 三键；`normalize_fallback_operating_cost` 在 insert 与 submit 两次 `before_validate` 下幂等（IT-018 制造费用金额靠它）；Company 建账默认 `410199`／`400101`／`1002`；含税价税模板沿用；策略对比报表的缺料判定与 `Scenario Event`（`event_type=缺料推迟`）逐段一致；`spc.compute`／`load_subgroups`；`bom_selection.select_bom`。
- 片 3（演示框架）：登记表 `scenario_end` 冻结 E；`site_operation` 锁与快照、换库互斥；`Demo Progress` 存在（未迁移的站任何受 `scene_date_fields` 管的单据 insert 都会报 `DocType Demo Progress not found`，`s8verify` 即此状态）。

**本片暴露什么**

- **场景终点参数**：E 缺省为今天；登记表有 `work_db` 时取其 `scenario_end`；E 不得晚于今天；每段 `to_date` 须早于今天；S＝E 前 12 个月的当月 1 日。
- **场景进度与分段**：三段 [S, D1−1]、[D1+1, D2−1]、[D2+1, E−1]；每日 savepoint＋commit，失败只回滚当日、整段停；`from_date` 不得早于库内最后生成日的次日。
- **入口契约**：`start_generate(from_date, to_date)` → `{"job_id"}`（RQ `long`、10800 秒）；`generate_status(job_id)` → `{"state","day","error"}`；状态文件 `private/frappe_debug/generate.json`。
- **快照前置（演示框架拍快照前生成器已备好）**：D1−1 段末留一条未转换线索（第 1 幕）、把默认 BOM 设成非成本推荐（第 4 幕）、清 Administrator 列表筛选；D2−28 建 `S8-ACT7` 订单（交货 D2，第 7 幕）；D2−1 建 `S8-ACT6` 超载排程（第 6 幕）、清筛选；D2 上一个月**不结转、不计件、不建底稿**，留给第 6 幕（以 D2−1 计件）和第 7 幕现场结；第三段第一天先补结此前各月；E−1 段末忽略留置的 EOQ 建议、建供应商记分卡（只到 E 上月）、已跑过 `run_daily(E)`、清筛选。**列表筛选只在这三处清**，幕间（第 2～5 幕、第 7 幕、第 9 幕）快照前是否清归片 3 核（需求 §4.9.3-11）。
- **共享状态**：`frappe.flags.in_scenario_generator` 置位期间场景日期钩子跳过；生成全程持站点操作锁；`quality-plan.json` 必须与当前 E 和参数指纹匹配（P2-07）。
- **对片 1 的提醒**：P2-01 的暂估应付余额、P2-11 的税额尾差会进第 7／8 幕的资产负债表与对账，片 1 审报表时如看到应付类反向余额，根源在这里。

## 片内复核建议

1. **定级在边界上的**：P2-01 在「中／高」之间。它是会计口径错误，每张拒收入库都会留暂估借方余额，但资产负债表仍平衡、演示画面不一定看得出，所以定中。查法：在终版第 8 幕快照的只读副本上查 `220202` 余额方向，余额在借方就改判高。P2-02、P2-03 在「中／低」之间：数据不真实，但只有第 6 幕的计件列表一处看得出来。
2. **查得最浅的一块**：`monthly.py` 的月结、补结与 IT-018 制造费用这套组合，以及 `targets.py` 的第 6／7 幕前置，我只读了代码，数值采信 E 的终版回读（E 报告 §「演示站第二次整场预跑」表）。查法：拿第 7 幕原始快照的只读副本，逐月核 4101 借方＝410199 贷方、3 月未结、计件只缺 3 月。
3. **没往哪找**：没看终版 `erx.localhost` 数据（约束不许碰），SQL 结论都来自早于 R7 修复的 `s8eoqformal`，靠「代码行未变」推到现行代码；没核负库存、存货计价重算、应收账龄是否合理；没核 SPC 筛选算法本身；没逐单据复算 GL 映射。
4. **拿不准处**：P2-01 是否算问题，取决于「拒收照付」是不是用户想要的（ERPNext 缺省就这么做，是为了走退货、扣款流程）；P2-09 判为方案外夹带，但它服务于 `verify` 的第 9 幕核验，也可读成方案 SL-011 ⑨ 的实现手段；P2-03 绕过 `validate_sequence_id` 的原因没查到，可能是为了避开工序损耗下的数量比较，去掉前要先复现。

## 状态值

`有发现`
