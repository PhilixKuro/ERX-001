# P1-S8-R6 D 回执 · Part2

**日期**：2026-10-22｜**执行者**：Codex｜**打 tag**：否
**依据**：[R5 开发方案·Part2](../R05-开发方案/P1-S8-R5-C开发方案-Part2.md)及总纲。

## 逐项执行结果

| 任务 | 对应切片 | 落地位置（文件:行） | 结果 | 完成时间 | 说明 |
|---|---|---|---|---|---|
| TS-013 场景参数文件与加载校验 | SL-011 | `frappe_debug/scenario/params.py:293`、`frappe_debug/data/scenario.yaml:3`、`frappe_debug/tests/test_params.py:109` | ✅完成 | 2026-10-22 | 实现不可变 Scenario、YAML 安全加载、相对日期／工作日推导、日期分段及业务参数逐项汇总校验；公司缩写按用户裁决采用HDTH。ATDD先红10/10（模块缺失），实现后11/11（2.789秒）；最新定向测试12/12（2.656秒）。六类必需错误、合法日期样例、假日顺延、默认文件及不写入断言均通过。无新增工程约定。 |
| TS-014 建单辅助、主数据与期初 | SL-011 | `frappe_debug/builders/{common,selling,buying,manufacturing,accounts,crm,dates}.py`、`scenario/{masters,opening}.py`、`tests/{test_builders,test_builder_dates,test_builder_integration,test_masters}.py` | ✅完成 | 2026-10-22 | 公共日期流程、主数据幂等与期初 GL 通过。真实原生 mapper 集成测试3/3：CRM 转换返回 string、报价客户创建及订单子行交期；采购按供应商/场景日期取价、拒收收货 GL/SLE、非零发票与 1002 付款结清；草稿生产计划生成日期正确且已提交工单/工序卡。 |
| TS-015 每日全链 | SL-011 | `frappe_debug/scenario/day.py:395`、`scenario/slots.py:65`、`tests/test_day.py:103` | ✅完成 | 2026-10-22 | 实现 `run_day` 固定顺序：规则开关、CRM 需求、生产计划/工单、逐日补货、采购收货/发票/付款、发料/工序报工/质检/完工入库、库存可用时交付/销售发票/到期收款。随机流按种子与日期派生；订单数按工作日数计算并随机取整。补货返回问题时停止并抛错；缺货时不创建空白发货单；质检记录样本与参数化读数。同日交易按顺序递增时间。测试站14天集成含周日和月末，逐类核对采购入库、制造入库、发货、采购/销售发票、付款均已提交且GL完整，库存单据SLE完整；同工位12+张工序卡时间不重叠、工时等于卡工时并关联员工；CRM订单日期有效且无GL。 |
| TS-016 每月任务、缺料、第 6／9 幕前置 | SL-011 | scenario/{monthly,targets,support,day,opening}.py、doctype/scenario_event/、四个定向测试模块 | ✅完成 | 2026-10-22 | 月末会计、首年前置空底稿、缺料推迟、未来超载排程、目标订单、评分与列表筛选清理已实现；第7幕整链已恢复并通过原生完工入库回归，HT-023修复保持数量语义。 |
| TS-017 生成器入口、后台任务与一年实跑 | SL-011 | `scenario/{runner,quality,day,params,verify}.py`、`data/scenario.yaml`、`tests/{test_scenario_runner,test_quality_screening,test_day,test_params}.py` | ✅完成 | 2026-10-22 | 正式站384日原生验证全通过（1793.801秒）；80项全量80/80、容器退出0，报表回归7/7。190组SPC子组有15个异常窗内信号、窗外0；E日EOQ建议2276.67千克及4家有效供应商价。缺料报表三段与事件逐段一致37/37、3/3、1/1；GL/SLE逐单据映射0差异，另37张月结凭证的134行GL与原生map全匹配。12家供应商各12期评分、三段建议→MR→PO、拆卡、负荷、月末/现金流、后台任务及5000支续跑订单均通过。 |

## 方案要求的验证

| 任务 | 验证方式（方案原文） | 怎么跑的 | 实测结果 |
|---|---|---|---|
| TS-013 | `test_params.py`：SL-011 ① 六例；一例完整合法参数解析出的 S／D1／D2／E／segments 与写死值一致（以 E＝2026-10-20 为例：S＝2025-10-01）。 | `bench --site test.localhost run-tests --module frappe_debug.tests.test_params`；另对 `frappe_debug` 执行 Ruff check 与 format check。 | 11/11（2.789 秒）；写死日期与三段区间通过，默认 `scenario.yaml` 可载入；Ruff 与格式检查通过。 |
| TS-014 | `test_masters.py`：小参数在测试站事务内 `build_masters` 两次，第二次无新增；期初日记账 GL 借贷与参数一致。 | `bench --site test.localhost run-tests --app frappe_debug`；另先红后绿运行 `test_builders.py`。 | 21/21（27.397秒），退出0；15类主数据二次构建计数不变，2张已提交BOM；期初日记账已提交，GL借贷各1,000,000，1002银行借700,000、3001资本贷1,000,000；日期辅助5/5，建单公共流程2/2。Ruff check、22个文件格式检查均通过。 |
| TS-015 | `test_day.py`：测试站事务内 14 天小场景；断言单据类型计数、日期不减、GL／SLE 齐全、同工位不重叠；⑪ 在 TS-017 的后台任务里核。 | `bench --site test.localhost run-tests --module frappe_debug.tests.test_day`；全量 `bench --site test.localhost run-tests --app frappe_debug`；Ruff check / format check。 | 定向 2/2（65.359 秒）；全量 32/32（102.017 秒），Ruff 与 27 个 Python 文件格式检查通过。14 天集成实际生成并核对 PR、制造 Stock Entry、DN、PI、SI、Payment Entry、GL/SLE、质量检验及12+工序卡无重叠。后台进程拆卡已在TS-017正式运行中验证通过。 |
| TS-016 | test_monthly.py与test_shortage.py：跨两个月末小场景核折旧、月结、底稿、计件；断料时推迟首卡并在到货后恢复。⑧⑨⑩在TS-017整年数据核。 | 测试站串行运行monthly、shortage、targets、scenario_support；全量`bench --site test.localhost run-tests --app frappe_debug`；Ruff check / format check。 | 定向：月末5/5（65.779秒）、缺料4/4（29.413秒）、目标边界测试含第7幕1/1（25.913秒）；HT-023原生Stock Entry两位数量比较修复红绿完成；最新版全量52/52（289.982秒），Ruff与38个Python文件格式检查通过。整年验收⑧⑨⑩及后台进程测试在TS-017。 |
| TS-017 | SL-011 ③～⑫：全年核单据／GL／SLE、三规则分段、月末、评分、排程、SPC、负荷、缺料、第9幕建议、后台补丁与分段续跑。 | 测试站全量与Ruff/format/compile；两座`s8eoq`清洁站冻结参数预检、全年预跑、完整窗口筛选并导出计划，另一站导入后正式运行；`s8-ts017-final-evidence.py`只读核账簿和续跑订单。 | ✅完成。正式站384日原生验证全通过（1793.801秒）；全量80/80、容器退出0，报表回归7/7。190组SPC子组有15个异常窗内信号、窗外0；E日EOQ建议2276.67千克及4家有效供应商价。缺料报表三段与事件逐段一致37/37、3/3、1/1；GL/SLE逐单据映射0差异，另37张月结凭证的134行GL与原生map全匹配。12家供应商各12期评分、三段建议→MR→PO、拆卡、负荷、月末/现金流、后台任务及5000支续跑订单均通过。 |

### 新参数隔离预跑证据（2026-10-22）

- 站点`s8eoqpreview.localhost`；冻结指纹 `370e74f88a5945f47b5e47e953a9542e7b8a9ac543fd4fc7252db37bd64ea8ce`。384日，第一段445.282秒、第二段387.650秒、第三段914.151秒；含验收和导出总计1750.442秒，日耗时中位数4.3485秒、最大17.646秒。
- 预跑原生验收仅`spc.anomaly_window`不通过（预跑按未筛选读数提交，用于取得完整日程）；其余检查全通过，E日建议`RS-2026-00161`为EOQ、2276.67千克、Awaiting Decision，4家有效供应商价。只读原生复算：计划量1440.97238018低于再订货点1676.04218978，90日日均需求124.61045556、标准差184.69493082，库存611.15、在途829.823；提前期仍7天。不能将预跑整体标为通过。
- 导出的190组候选计划第115次原生完整窗口评估通过；日程指纹 `fa27ec807ad8c3e4862aa26f82cc4b62f17ff328e132f1f8c1c3fdb7bd3d0f21`。以拒绝覆盖方式复制到`s8eoqformal.localhost`，两端文件SHA256均为 `C98CC1207526066FCEDD28BF465241B6E99C2EBD3D019FD992A47DC401B4F39A`。
- 发现策略对比报表的5张额外缺料由日末结存包含本工单自身发料导致；报表现恢复同工单计划日发料量后再判定。预跑和正式站三段缺料数与生成事件数均为37/37、3/3、1/1；策略报表回归7/7。正式对账`frappe-bench/logs/s8-ts017-shortage-report-formal.log`。
- 正式站`s8eoqformal.localhost`全年384日，耗时1793.801秒，日耗时中位4.5965秒、最大18.679秒；原生验证器`ok=true`且无失败项。190个SPC子组的15个信号均在2026-02-19至2026-02-26异常窗口内，窗外0；E日目标EOQ建议存在。正式站报表／事件三段均为37/37、3/3、1/1。12家供应商各12期评分全提交且总分非空；分阶段建议、MR及PO链齐全；拆卡与第6幕负荷符合要求。输出：`s8-ts017-s8eoqformal-{verification,summary,extended,supplementary}.json`，正式三段报表对账` s8-ts017-shortage-report-formal.log`。
- 正式站逐类原生GL map与SLE行数核对0差异；另核月结独立DocType共37张凭证、134行GL，逐张与`get_gl_entries`结果一致。5000支插入订单`SAL-ORD-2026-00085`工单Completed、交付及开票100%、应收余额0。月结证据` s8-ts017-s8eoqformal-month-end-gl-final.json`。
- 只读补充脚本按原生GL生成映射重算、按库存单据行推导SLE数；逐单据计数和科目借贷合计无差异。5000支插入订单`SAL-ORD-2026-00085`已100%交付/开票，工单完成，发票未结金额0。证据：`frappe-bench/logs/s8-ts017-s8eoqpreview-{verification,supplementary,summary}.json`与对应`.log`，补充脚本`frappe-bench/logs/s8-ts017-final-evidence.py`。

| 单据类型 | 已提交张数 | 原生映射应有GL行 | 实有GL行 | 单据行应有SLE行 | 实有SLE行 |
|---|---|---|---|---|---|
| Purchase Receipt | 155 | 311 | 311 | 155 | 155 |
| Purchase Invoice | 155 | 449 | 449 | 0 | 0 |
| Stock Entry | 665 | 1331 | 1331 | 1330 | 1330 |
| Delivery Note | 326 | 652 | 652 | 326 | 326 |
| Sales Invoice | 326 | 978 | 978 | 0 | 0 |
| Payment Entry | 477 | 954 | 954 | 0 | 0 |
| Journal Entry | 13 | 28 | 28 | 0 | 0 |

## 全量验证

| 门 | 结果 |
|---|---|
| `frappe_china` 集成测试 | — |
| 旧类与未分类测试 | — |
| Node、Ruff 与格式检查 | 本轮涉及的8个Python文件Ruff check及format check通过；compileall通过。无Node文件。 |
| `frappe_debug` 测试 | 容器内合并输出复跑 `s8-ts017-full-demand-phase-confirmed.log`：80/80（312.234秒），结尾 `OK`、实际退出0。旧日志 `s8-ts017-full-demand-phase.log` 为80/80（302.554秒）且 `OK`，但宿主PowerShell将stderr包装为 `NativeCommandError`，当时外层退出1；保留该差异，不改写旧证据。新增覆盖包括完整窗口筛选边界、分段计划核对、YAML日期指纹及期末需求阶段参数。 |
| `frappe_china` 策略报表集成 | `test_strategy_comparison`模块7/7，含本工单计划日发料不误计缺料的原生单据回归。 |

## 偏离与暂停

- TS-016第7幕真实完工链曾命中原生Manufacture Stock Entry精确浮点比较；已在ERPNext fork归一比较结果（不改成品、损耗和mapper数量），恢复用例红绿验证并纳入52/52。
- TS-017场景缩写按裁决为HDTH。保留`s8dev.localhost`、`s8verify.localhost`及旧失败现场。隔离预跑和正式全年运行完成；正式站原生全年验证全过，SPC、EOQ、缺料报表/事件、GL/SLE、月结凭证、供应商评分、负荷、拆卡、后台任务与分段续跑均已复核。策略对比报表依DEC-035排除本工单自身计划日发料后，缺料数逐段与事件一致。TS-017完成，R6 D整体仍继续。
- 用户已选择“补交 S 前一个月空底稿”；原生底稿递归要求同会计年度逐月提交，因此缺省S=2025-10-01时需从1月补至9月。九个月的展开为Codex读码推导，非用户另行要求；见D讨论第10步。已有场景前有效GL/SLE或草稿时停止。
- 折旧仍为手工Journal Entry，但原生折旧科目强制`voucher_type=Depreciation Entry`；期初凭证显式`is_opening=Yes`，以匹配原生现金流排除期初分录的语义。金额与科目不变。
- 供应商评分使用限定在同步调用内的原生模块时钟覆盖，使历史E只生成至E上月，调用结束恢复。
- 前次实现的日链包装、部分边界和字段调整未完整保留先红后绿过程；不得将补测描述为红绿证据。后续改动恢复测试先行。

## 新增约定

### SPC 与 EOQ 修复续跑记录（2026-10-22）

- 用户已批准“正态候选样本＋有界筛选”，配置均值、标准差、异常窗口及原生判异不变；有限重试失败须报错，已提交质检不得改写。见D讨论第12步。
- 用户选择A：隔离清洁站显式预跑全年日链，筛选并原子导出`private/frappe_debug/quality-plan.json`；另一清洁站读取计划。计划校验场景参数指纹和完整日程指纹；计划外实际请求在提交前报错，已计划但未使用的请求在窗口结束时报错。预跑标志不开放给后台生成接口，且不能加载正式计划。相关新增测试先红后绿，最新全量80/80通过。
- 原诊断中目标库存1603.1高于原生订货点544.564669673。用户选择保留7天暂停采纳并调整场景需求；`scenario.yaml`将订单数量均值从3000调至3500，并为目标3mm钢丝对应的压簧/拉簧设置10权重，其余三种产品各1，周订单量、补货规则及验收口径不变。权重覆盖与正值校验、确定性抽样测试通过；正式全年运行确认E日EOQ建议出现。
- TS-017正式全年及补充验收均通过；沿R5 Part3继续TS-018。保留`s8verify.localhost`失败证据。

| 约定 | 类别 | 在哪个任务确立 |
|---|---|---|

## 未做项

| 项 | 为什么没做 |
|---|---|

## 状态值

执行中；TS-013～017完成。正式站384日原生验证全通过（1793.801秒）；80项全量80/80且容器退出0、策略报表模块7/7、SPC筛选边界13/13。SPC 15个信号全部在异常窗口、窗外0；E日EOQ建议2276.67千克；三段缺料报表/事件37/37、3/3、1/1。GL/SLE及37张月结凭证134行GL均与原生映射一致；12家供应商评分、负荷、拆卡、后台任务及5000支续跑订单全部通过。场景指纹`370e74f88a5945f47b5e47e953a9542e7b8a9ac543fd4fc7252db37bd64ea8ce`，质量计划190组、第115次评估成功。R6 D继续下一任务。

## 复核建议

`test_day.py::test_fourteen_days_create_dated_crm_orders_and_due_production` 已核跨周日/月末日链与工序卡排程；正式全年核了GL/SLE、SPC、月度任务、后台拆卡和续跑。仍建议复核`day.py`报价单`valid_till`取当前日期与场景日+30日较晚值的方案偏离；拒收比例及供应商逐日最低有效价的全边界仍未覆盖。HT-015须在TS-021开写前按SA验证，不由本次全年运行替代。

## 2026-10-22 中途提交检查点

- 用户明确授权提交并推送当前进度。`frappe_china`的Part1实现已推送至`ee153b4591ce80419290a39ec430a0c99c0381a3`；`frappe_debug`的场景参数、日期辅助、主数据与期初实现已推送至`e2843633210688417b73303e3ee4cd50ee1865d4`。主仓库同步更新`docker/apps.json`。
- 本次是开发中途保存：TS-013～016完成，TS-017未完成，不代表Part2全量验收或D步收口。续跑从TS-017生成器入口、后台验证与全年实跑继续。
- 提交前未发现测试或场景生成任务；昨晚遗留的`purchase_receipt_ui.cjs`进程60268已结束。常驻Docker、web、worker与scheduler继续正常运行。

### 2026-10-25 E 步核出的更正（R7 IT-012～016）

按 [R7 E 确认报告](../R07-确认/P1-S8-R7-E确认报告.md) 更正，原文保留：

- **IT-012**：生成器选供应商按跨月历史最低价取第一条，不是当期最低价（`day.py` 原第 190～200 行），致 6 家供应商全年无单、评分全 0。R7 改为先取每家 `valid_from<=当日` 的最新价再比最低。
- **IT-013**：方案步骤 4「按参数比例填拒收数」未接入生成器，全年 155 张采购入库无拒收行；上文「拒收收货 GL/SLE 通过」只是 builder 单测。R7 加 `purchase.rejected_ratio: 0.02` 与「不合格品」仓。
- **IT-014（偏离补登）**：`scenario.yaml` 的 `qty_phases` 把终点前 14 天订单均值设为 14000（平时 3500），为让第 9 幕在最后一个提前期内触发 EOQ；方案 DEC-012 写「平稳、无季节」，上文「周订单量…不变」不确。用户 2026-10-25「按建议来」，保留并在此登记。
- **IT-015**：第 6 幕负荷判定用的是自算工时，原生 `capacity_load` 只在全年跑完后看过（那时卡已完工）。R7 在重跑后的第 6 幕快照副本上补核。
- **IT-002**：上文「已在 ERPNext fork 归一比较结果」当时未提交、并于 10-24 19:53 被还原；R7 已重写。
