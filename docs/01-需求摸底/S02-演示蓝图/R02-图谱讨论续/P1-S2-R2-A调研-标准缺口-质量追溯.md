# P1-S2-R2-A 调研：标准体系缺口 — 质量管理与追溯

调研对象：ERPNext v16.35.0 / Frappe v16.34.0 本地源码。日期 2026-09-23。
方法：读 DocType JSON 字段定义 + 控制器源码 + 关键词 grep；GitHub API 核实开源候选。
**本报告区分「读码所得」（给路径/行号）与「推断」（标注）。**

## 一、ERPNext v16 质量能力实有清单

### 1. `erpnext/quality_management/doctype/` — ISO 9001 体系文档层（非车间检验层）

| DocType | 职责 | 读码所得 |
|---|---|---|
| `Quality Procedure` / `Quality Procedure Process` | 质量程序文件树（父子结构），纯文档 | 目录存在 |
| `Non Conformance` | 不合格记录单 | 字段仅 7 个：`subject` / `procedure` / `status`(Open-Resolved-Cancelled) / `details` / `process_owner` / `corrective_action` / `preventive_action`（non_conformance.json:22-77） |
| `Quality Action` / `Quality Action Resolution` | CAPA 动作 | `corrective_preventive`(Corrective/Preventive)、`resolutions` 子表(problem/resolution/responsible/completion_by)（quality_action.json:56-76） |
| `Quality Goal` / `Quality Goal Objective` | 质量目标与指标 | 目录存在 |
| `Quality Review` / `Quality Review Objective` | 管理评审 | 目录存在 |
| `Quality Meeting` / `Agenda` / `Minutes` | 质量会议记录 | 目录存在 |
| `Quality Feedback` / `Parameter` / `Template` / `Template Parameter` | 客户质量反馈 | 目录存在 |

**关键判断：这一模块整体是「ISO 9001 文档留痕」，不是检验执行系统。** 依据：`Non Conformance` 无数量、无物料、无批次、无仓库、无 Quality Inspection 链接字段——它记不住「哪批多少件不合格」，只是一段文字描述。

### 2. `erpnext/stock/doctype/quality_inspection*/` — 实际检验层

- `Quality Inspection`（主表）、`Quality Inspection Reading`（读数子表）、`Quality Inspection Template`、`Quality Inspection Parameter`、`Quality Inspection Parameter Group`。

## 二、标准体系逐项判定

| 标准/能力 | 判定 | 依据 |
|---|---|---|
| **IQC/IPQC/OQC 三段检验** | **有，能表达** | `quality_inspection.json:67-74` `inspection_type` = Select，取值 `Incoming` / `Outgoing` / `In Process`。`reference_type`(:81) 可挂 Purchase Receipt / Purchase Invoice / Subcontracting Receipt / Delivery Note / Sales Invoice / Stock Entry / **Job Card**。三段齐全，IPQC 可挂工序卡。 |
| **检验计划与抽样方案（AQL / GB-T 2828.1）** | **几乎无** | 仅有 `sample_size` 一个 Float 字段（:130），人工填数字。grep `sampling_plan` / `AQL` / `Sampling` **全部 0 命中**（已排除 chart_of_accounts 与 node_modules 噪声）。无抽样水平、无 AQL 值、无接收/拒收数（Ac/Re）、无抽样标准表。Item 上的 `sample_quantity`/`retain_sample`(item.json:505) 是**留样**，不是抽样方案，勿混。 |
| **⭐ SPC 控制图 + 判异准则** | **完全无** | grep `control_chart`=0、`spc`、`x-bar`=0、`nelson`=0、`western_electric`=0、`std_dev`=0、`standard_deviation`=0。`Quality Inspection Reading` 只有 `reading_1`..`reading_10` 十个离散读数格 + `min_value`/`max_value`/`acceptance_formula`（reading json:59-190），是单次判合格，**无跨批次的时序统计**。无控制图，无判异规则。 |
| **⭐ 过程能力指数 Cp/Cpk/Pp/Ppk** | **完全无** | grep `cpk` / `Cpk` / `process_capability` 全 0。无标准差计算入口。弹簧厂客户要的 CPK≥1.33 **无处生成**。 |
| **MSA / GR&R** | **完全无** | grep `gage_r` / `GR&R` = 0。无量具、无重复性/再现性概念。 |
| **APQP / PPAP** | **完全无** | grep `ppap` / `apqp` = 0。无 PSW、无控制计划(Control Plan)、无 FMEA、无过程流程图。汽车配套弹簧厂的量产件批准全缺。 |
| **不合格品管理（让步/返工/报废/隔离）** | **弱，仅拒收拦截** | 有拦截：`Stock Settings.action_if_quality_inspection_is_rejected` = Stop/Warn（stock_settings.json:286-289），另有 `action_if_quality_inspection_is_not_submitted`(:148)。拦截逻辑在 `controllers/stock_controller.py:1676-1695`。**但拒收之后没有流程**：无隔离仓自动转移、无让步接收(concession)审批、无 MRB(物料评审委员会)。返工只有 `Job Card.is_corrective_job_card`(job_card.json:384) 这一个纠正工单钩子。报废靠 Stock Entry 手工。 |
| **CAPA / 8D** | **有壳无骨** | `Quality Action` + `Non Conformance` 提供 corrective/preventive 两段文本（见上表）。**8D 无**：无 D1-D8 阶段、无根因分析工具(5Why/鱼骨)、无临时措施与永久措施区分、无有效性验证关闸。 |
| **⭐ 批次/序列正反向追溯** | **有，且 v16 是现成报表——此处应修正预期** | `erpnext/stock/report/serial_no_and_batch_traceability/`（.py 共 559 行，2025 版权头）。有 `traceability_direction` 过滤器，取值 **Backward / Forward / Both**（py:56,66）：Backward 走 Stock Entry 反查原料，Forward 正查流向。**不需自己刨 SLE。** 另有 `serial_and_batch_summary`、`batch_wise_balance_history`、`serial_no_ledger` 等报表。检验单本身带 `batch_no` / `item_serial_no` 字段（qi.json:114-127），QI 结果可回写批次（quality_inspection.py:251）。**断裂索赔追责这条链是通的。** |
| **ISA-95 / MES 分层** | **Job Card 只是 L3 的薄壳** | `Job Card` 有 workstation / operation / time_logs / employee / barcode / wip_warehouse / quality_inspection_template / sub_operations（job_card.json:109-445），够做工时与工序流转。**缺**：grep `poka_yoke`=0、`wip_kanban`=0、`andon`=0（39 个命中经核实全是西班牙语科目表里 "abandono" 的子串噪声，非功能）。无在制品电子看板、无 Andon 呼叫、无防错校验、无设备数采(OPC-UA/SCADA)、无 SPC 在线采集。 |
| **图纸文件版本与变更通知** | 未查实（本报告未复查，沿用起点结论） | 起点已确认 `drive` 补不上 |
| **模具工装管理** | **无** | grep `tooling`=0、`Mold`=1（经核实为无关命中）、`Die `=0。无模具台账、无寿命计数、无保养周期、无模具与工序绑定。 |

## 三、开源候选核实

| 候选 | 真实性 | 许可证 | 最后提交 | v16 兼容 | 结论 |
|---|---|---|---|---|---|
| `Siddardth7/quality-platform` | 存在，Python，描述为 FMEA/SPC/Control Plan（AIAG/IATF-16949） | **无**。`license` 字段 = `None`，`/LICENSE` 直连返回 **404** | 2026-09-11（活跃） | **否**——`requirements.txt` 依赖 `streamlit`（altair/blinker/cachetools 均标注 `via streamlit`），根目录 `app.py`，**无 frappe 依赖、无 hooks.py** | **用户说法成立，不可复用。** 无许可证=法律上不授权任何使用；且是独立 Streamlit 应用，不是 Frappe app。需求参照可以，代码不能拿。 |
| `Neev-Chovatiya/SmartBMR` | 存在，自述 Frappe 上的 MES | MIT（`license.txt` 在根目录） | 2026-07-19 | **未查实**（未读其 hooks.py / pyproject 的 frappe 版本约束） | star 0、单人项目、名为 BMR（批记录，偏制药）。**不建议依赖**，可参考。 |
| `iniself/dataq` | 存在 | MIT | 2025-05-16 | 未查实 | 是**数据质量**（data quality）工具，与制造质量无关。**排除。** |
| `priyankongit/edu_quality` | 存在 | AGPL-3.0 | 2026-09-04 | — | 学校管理，名称误导。**排除。** |
| `carlosqsilva/pyspc` | 存在，SPC 控制图库，243 star | **GPL-3.0** | 2023-01-12（**三年无更新**） | 库级可 import | GPL 传染性对 ERPNext(GPLv3) 本身兼容，但对闭源交付不利。已停更。**备选。** |
| `suanto/pycontrolcharts` | 存在，SPC 控制图库 | **MIT** | 2026-03-06 | 库级可 import | star 1，很新很小，需自行评估质量。**许可证最友好的 SPC 计算内核候选。** |
| `DamnitDavid/CronQMS` / `nanowind/qms-ic-packaging` | 存在，MIT | MIT | 2026-07/08 | 独立系统，非 Frappe app | 集成形态是外挂系统+接口，成本高于自研 DocType。**不推荐。** |
| ECOSIRE（SPC / Tooling-Mold） | — | 闭源收费无源码 | — | — | 按指示**仅作需求参照，不推荐**。 |

**Frappe 生态结论：没有可用的质量/SPC/MES/模具 app。** 搜了 frappe+quality+management、erpnext+SPC、frappe+MES、erpnext+tooling+mold、erpnext+quality+spc+cpk 五组关键词，四组零结果，命中的四个仓库全部经上表排除。

## 四、只能自研的部分

按弹簧厂优先级排序（自研判定依据：既无原生、又无可复用开源 app）：

1. **SPC 控制图 + CPK 计算**（最高优先，客户直接要）。自研形态：新增 `Control Chart` / `Process Capability Study` DocType，数据源直接读 `Quality Inspection Reading`（现成读数已在库里，这是有利条件）。计算内核可考虑内嵌 `pycontrolcharts`(MIT) 或自己写公式——公式本身是公开标准，不到 200 行。判异准则（Nelson 8 条）需自写。
2. **抽样方案（GB/T 2828.1）**。自研形态：`Sampling Plan` DocType + AQL 抽样表数据（一次性录入标准表），在 Quality Inspection 上按批量+检验水平+AQL 自动算 `sample_size` 与 Ac/Re。现有 `sample_size` 字段可作落点。
3. **模具工装管理**。自研形态：`Tool`/`Mold` DocType（台账、冲次计数、寿命预警、保养计划），与 `Job Card.workstation`/`operation` 绑定。可参考 `Asset` + `Asset Maintenance` 模块复用其保养排程（**推断**，未逐字段核实 Asset Maintenance 是否够用）。
4. **不合格品闭环**（隔离仓、让步接收审批、MRB、报废工作流）。可在现有 `Non Conformance` 上扩字段挂物料/数量/批次/QI 链接，比新建划算。
5. **8D 报告**。在 `Quality Action` 上扩 D1-D8 阶段字段 + 有效性验证关闸。
6. **APQP/PPAP 与 Control Plan / FMEA**（若真做汽车配套才投入，工作量最大）。
7. **MES 车间层**（在制品看板、Andon、防错、数采）。范围大，建议与另一路的生产计划调研合并裁剪。

**不需自研**：批次/序列正反向追溯（v16 已有现成报表，见二表）；三段检验类型表达（`inspection_type` 已够）。

## 五、拿不准 / 未查实

- **SmartBMR 的 v16 兼容性未查实**：未读其 `hooks.py`、未看 `pyproject.toml` 的 frappe 版本约束，也未看 `smart_bmr/` 内实际 DocType。若要作参考需再查一轮。
- **`serial_no_and_batch_traceability` 报表的实际穿透深度未实测**：读码确认有 Backward/Forward 双向且走 Stock Entry 递归，但**未实测多级 BOM（原料→半成品→成品）能否连续穿透**。断言「链是通的」基于读码，不是跑数据。弹簧多为单级或两级，风险不高，但索赔场景建议实测一次。
- **`Asset Maintenance` 能否承载模具保养属推断**，未逐字段核实。
- **图纸版本管理这条本报告未复查**，沿用起点结论。
- **`Quality Inspection Template` 与 `Parameter Group` 的具体能力未细读**（只确认存在），若做抽样方案落点需再看一眼其结构。
- grep 类否定结论的口径：均在 `erpnext/` 下按 `*.py` `*.json` `*.js` 全量搜，排除 `node_modules` 与 `chart_of_accounts`。**若某能力藏在 Frappe 框架层而非 erpnext 层，本次未覆盖**（SPC/CPK 属业务能力，框架层不太可能有，但这是推断）。
