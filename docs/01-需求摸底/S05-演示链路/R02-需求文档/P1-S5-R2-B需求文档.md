# P1-S5 演示链路 —— 需求文档

**版本**：v1.0｜**日期**：2026-10-05
**参与者**：用户（裁决）、Claude（Opus 5.5，构建）
**产出步骤**：P1-S5-R2 · `plannedDev` B 步（`build`）
**依据**：[R1 A 需求讨论](../R01-需求讨论/P1-S5-R1-A需求讨论.md)（第 1–9 步，DEC-001～019）＋[本轮 B 讨论记录](P1-S5-R2-B讨论记录.md)（第 1 步，DEC-020）
**状态值与复核建议**：不在本文件——见 [P1-S5-R2-B回执](P1-S5-R2-B回执.md)

> **读法**：本文件只呈现最终结论，不含讨论过程；结论后的「来源」指向讨论记录的步号。**凡与 A 讨论记录字面不一致处，以本文件为准**（不一致处见回执「对依据的更正」节）。
> **编号**：任务 `TS-`、风险 `RS-`、验收 `AC-` 为本文件内编号；决策 `DEC-`、被否决方案 `NV-`、遗留问题 `LG-` 沿用本 Stage 序号（A 步 DEC-001～019、NV-001～002、LG-001～008；B 讨论 DEC-020、NV-003），本文件新增的遗留问题自 `LG-009` 起。
> **「读码」与「实测」**：本文件凡写「读码」的结论都未在站点上跑过，由 D／E 步实测确认。

---

## 一、任务总览

**一句话**：把 CRM、HRMS、Insights、Raven 四个官方 App 装进本项目，并确认异地终端能打开页面、能收到实时事件——让 S6 的译名与导航有完整的界面可做，让 S7 的演示数据与操控有 CRM 起点、AI 结论和可用的演示终端。使用者是本项目的演示者（用户本人），最终受众是弹簧厂客户。

| 序号 | 任务名 | 复杂度 | 依赖 | 对应需求 |
|---|---|---|---|---|
| **TS-001** | `apps.json` 加四个 App 条目并锁 commit | 低 | — | DEC-001／002／015 |
| **TS-002** | `setup.sh`／`lock-apps.sh` 认出官方 App（remote 归位、tag 检出） | 低 | TS-001 | DEC-001／015 |
| **TS-003** | 装完 App 后让 `frappe_china` 回到业务 app 末位（写进 `setup.sh`） | 低 | TS-001 | DEC-003 |
| **TS-004** | `frappe_china` 为中式公司预配 HRMS 报销类型的默认科目 | 中 | — | DEC-005 |
| **TS-005** | 测试站 `test.localhost` 装四个 App，跑 S4 全量回归与 HRMS 科目验证 | 中 | TS-001～004 | DEC-006 |
| **TS-006** | 演示站 `erx.localhost` 装四个 App（装前备份），装后出新的空账基准点 | 低 | TS-005 | DEC-006 |
| **TS-007** | 归位验收：顺序、三个覆盖、译名胜出、建账自检 | 低 | TS-003／TS-006 | DEC-004 |
| **TS-008** | CRM：集成设置、币种、Lead → 销售订单实点、漏斗看板 | 中 | TS-005 | CR-013／DEC-007／008 |
| **TS-009** | Insights：装成、打开、建数据源跑一次查询 | 低 | TS-005 | IM-006／DEC-016 |
| **TS-010** | Raven：连 LiteLLM、建 bot、建只读工具与报表通道 | 中 | TS-005 | EX-001／DEC-009／011 |
| **TS-011** | 三问：最小数据、标准答案、每问 3 次实测、结论记录 | 中 | TS-008／TS-010 | DEC-010／012～014／020 |
| **TS-012** | 演示终端连通性：定连通机制，局域网与外网各验三条 | 中高 | TS-006 | CR-015／DEC-017／018 |

**依赖说明**：TS-004 不依赖 HRMS 已装——它在 `frappe_china` 里写成「HRMS 在场才生效」，故可先写、在 TS-005 一并验。TS-005 必须在 TS-006 之前（RW-01 的缓解：先在一次性环境验，不直接动 `HDTH`）。TS-011 依赖 TS-008，因为问 1 的数据是 CRM 商机，要先确认 CRM 的字段在实装版本上与本文件一致。TS-012 只依赖演示站装完：连通性验证在演示站上做（§4.8）。

**工作量**：**6.5–12 人日**（DEC-019；Raven 取常规值时 6.5–10）。分项见 §4.9。

---

## 二、初始目的

**需求怎么来的**。P1 被重定向为「在客户面前跑通整个流程」后，S2 的需求图谱把四个 App 的接入与演示终端连通性放进同一个 Stage。四个 App 里，**CRM**（CR-013）把演示线的起点从报价单前移到线索与商机——客户自己是做销售的，看得懂漏斗；**HRMS**（IM-005）与 **Insights**（IM-006）是用户下令接入的（S2-R2 第 30 步），HRMS 还是将来计件工资（IM-016）的发放侧；**Raven**（EX-001）承载 AI 演示，用户要它答三类分析：分析销售漏斗找单子、哪个供应商货美价廉、哪个 BOM 在符合单子要求下利润最大化。**演示终端连通性**（CR-015）来自用户多次提出的要求：演示会在客户现场从另一台设备访问本机站点，页面能打开与实时通道能通是两件事，都要验到。

**这个 Stage 为什么必须排在 S6 之前**：每接入一个 App，S6 的译名范围与要折叠的导航入口就各多一份（需求图谱 §7.4）。先接入后做译名，译名只做一遍。

**要解决的核心问题**：

1. 四个 App 装进来之后，**S4 花 20 轮做对的中国账不被破坏**——HRMS 也在 `Company` 上挂了钩子，还整类覆盖了 `Payment Entry`。
2. **`frappe_china` 仍压得住四个 App**——新装的 app 一定排到末尾，不归位则 S6 写的译名会被四个 App 的同源词译文静默盖掉。
3. **AI 演示只演答得出的题**——按可信度优先，AI 在现场答错比不演示代价更大；三问的结论直接决定 S7 的数据怎么编。
4. **在异地终端上实时通道真的通**——读码发现，异地终端上页面正常而实时通道会被静默拒连，本机浏览器测不出来（LG-007）。

**本 Stage 不做的**（边界）：演示用的正式数据（S7 的 CR-011／CR-012）；四个 App 的译名与导航折叠（S6 的 CR-002／CR-010）；演示操控与心跳自检（S7 的 CR-008／CR-009）；`after_migrate` 接线自检（S8G-S1 的 IM-007）；计件工资（S8G 的 IM-016）；Insights 进演示（NV-022）；给 Raven 选模型（DEC-011，归用户）；三问的复杂口径（四条延迟需求，§4.6.6）。

---

## 三、关键设计决策

### 3.1 继承的决策（本 Stage 不重判，列此备查）

| 决策 | 内容 | 出处 |
|---|---|---|
| ADR-0003／ADR-0013 | 装载顺序 `frappe → erpnext → 四个业务 app → frappe_china → frappe_debug`；四处 `[-1]` 归 `frappe_china` | P1 架构文档 |
| ADR-0004 | 本项目不用 `override_doctype_class`（防绕过 HRMS 的 `EmployeePaymentEntry`） | P1 架构文档 |
| ADR-0006 | 译名走 `frappe_china/translations/zh.csv` 单一来源 | P1 架构文档 |
| ADR-0008 | 事件协议 `erx_demo_step`；推送侧 `publish_realtime(..., user=演示用户, after_commit=True)` | P1 概况「跨单位接口契约」 |
| NV-022 | Insights 不进演示；演示看板走 ERPNext 原生 Dashboard Chart／Number Card | 需求图谱 IM-006 |

### 3.2 本 Stage 的决策

**A. 接入与装载**

| 编号 | 决策内容 | 最终选择 | 选择理由 | 失效条件 |
|---|---|---|---|---|
| **DEC-001** | 四个 App 的来源（A 第 1 步） | **官方仓库，`apps.json` 锁 commit**；确须改其源码时再 fork | 修复已归 `frappe_china`（ADR-0013），改上游源码是 L5；fork 只带来同步负担 | 须改某个 App 的源码且无 hook 可走时，该 App 改为 fork |
| **DEC-002** | 分支（A 第 1 步） | **HRMS `version-16`；CRM、Raven `main`**；Insights 由 DEC-015 更正 | 均为发布分支、均声明兼容 v16；HRMS 的 `develop` 已要求 v17 | 某 App 日后出 `version-16` 分支时可改用；`main` 改为要求 v17 时须锁在兼容的 commit |
| **DEC-015** | Insights 版本（A 第 6／7 步，更正 DEC-002 的 Insights 部分） | **v3：tag `v3.14.2`，锁 commit `5447f162`** | Insights 的 `main` 是已停更的 v2 线；S2 的判断全部基于 v3；tag 是正式发布点 | 有更新的 v3 tag 时可改锁 |
| **DEC-003** | `frappe_china` 的归位手段（A 第 1／2 步） | **装完四个 App 后调 `update_installed_apps_order` 把 `frappe_china` 调到业务 app 末位**，写进 `setup.sh` | 不卸载、不碰数据，可在新机器上自动重现；取代 LG-151 的「重装」 | 调序入口被上游移除或改语义时 |
| **DEC-004** | 完成标志②的验收口径（A 第 1／2 步） | **三条**：① `installed_apps` 里 `frappe_china` 在四个 App 之后；② 三个 whitelisted 覆盖解析到 `frappe_china`；③ 一条与四个 App 撞源词的测试译名由 `frappe_china` 胜出。另直接调一次 `check_all_cn_companies()` 全过；`after_migrate` 接线仍归 S8G-S1 | 「覆盖生效」在 S5 当下不受顺序影响（四个 App 都不抢那三个覆盖位），顺序真正起作用的是译名合并 | 某个 App 日后开始覆盖那三个方法时，② 的意义随之改变 |

**B. HRMS 与中国账**

| 编号 | 决策内容 | 最终选择 | 选择理由 | 失效条件 |
|---|---|---|---|---|
| **DEC-005** | HRMS 报销类型自建科目的处理（A 第 2／3 步） | **`frappe_china` 为中式公司预配 HRMS 报销类型的默认科目**，映射到 `管理费用` 下的明细（映射表见 §4.2.2，待领域专家确认）。**`frappe_china` 不依赖 HRMS**：只在 `Expense Claim Type` 存在时才配 | 保住 S4 的科目表；HRMS 见已配即跳过 | HRMS 改了 `set_expense_claim_type_accounts` 的跳过条件；或新增报销类型 |
| **DEC-006** | RW-01 的验法（A 第 2／3 步） | ① 先在 `test.localhost` 装四个 App 并跑完 S4 全量测试，再装演示站，装前先备份；② 装完后 S4 的测试全过；③ `HDTH` 保存一次公司后科目数仍为 266、自检多余科目为空 | 把 RW-01「先在一次性测试公司上验」具体化；② 同时验 HRMS 对 `Payment Entry` 的整类覆盖 | — |

**C. CRM**

| 编号 | 决策内容 | 最终选择 | 选择理由 | 失效条件 |
|---|---|---|---|---|
| **DEC-007** | CRM 演示的起点与范围（A 第 3／4 步） | **从 Lead 开始**：Lead → Deal → 推进几档 → 报价 → 接单，**含漏斗看板**（加权预测收入、各档转化） | 与图谱 CR-013 的起点一致；看板是 CRM 对客户最有说服力的部分 | — |
| **DEC-008** | 由 Deal 建客户的时机（A 第 3／4 步） | **CRM 默认机制**：报价单报给 `CRM Deal`，保存销售订单时由 CRM 的 `before_validate` 钩子自动建客户；不勾「状态变更时建客户」 | 零配置、与先报价后成交一致；勾选那一项也省不掉「报价对象是商机」这句解释 | CRM 改了该钩子的行为；或客户要求赢单即建客户 |

**D. Raven 与三问**

| 编号 | 决策内容 | 最终选择 | 选择理由 | 失效条件 |
|---|---|---|---|---|
| **DEC-009** | bot 挂哪些工具（A 第 4／5 步） | **只读**：`Get List`＋`Get Document` 按三问要用的 DocType 各建记录，另加一个 `Custom Function` → `raven.ai.functions.get_report_result` 作报表通道；不建 `Update`／`Create`／`Delete` | `Create`／`Delete` 两个 handler 在 `main` 上不存在（LG-005）；AI 在现场不能改数据；报表通道可能省掉自写查询 | 报表通道实测不通（LG-006）时改为自写 `Custom Function`（§4.6.4） |
| **DEC-010** | 三问怎么测（A 第 4／5 步） | `test.localhost` 上造最小数据，每问事先算好标准答案；每问跑 3 次，**3 次都答对且说得出依据**才算「答得出」；测完清掉 | 「答得出」可判真假；不碰演示站的空账基准点；数据结构给 S7 当样板 | 最小数据下答得出、S7 的 100 条下答不出时，S7 须重测 |
| **DEC-011** | 模型（A 第 5 步） | **由用户在 LiteLLM 里配，不进本 Stage 范围**；S5 只负责 Raven → LiteLLM 的连接，bot 的模型填用户给的别名。测试报告记下别名；密钥不进文档与仓库 | 用户裁决 | **用户换模型时三问须重测** |
| **DEC-012** | 问 1「找单子」的口径（A 第 5／6 步） | 进行中的商机按**加权金额（金额 × 概率）**排序取前几名。⚠ 计算式由 DEC-020 更正 | 单表可答、标准答案唯一；演示稳定优先 | 进入四阶段战略第 ④ 阶段时按延迟需求重判 |
| **DEC-020** | 问 1 的加权金额由谁算（B 讨论第 1 步，更正 DEC-012 的计算式推断） | **bot 自取 `expected_deal_value` 与 `probability` 两字段自行计算排序**（`probability` 按百分数除以 100）；3 次未全对则改走自写 `Custom Function` | `expected_deal_value` 是「预计成交金额」、不含概率（读码）；`Get List` 只能按单字段排序；此法零开发且保住用户选的口径 | 实测 3 次未全对；或用户换模型 |
| **DEC-013** | 问 2「货美价廉」的口径（A 第 5／6 步） | 价＝同一物料各供应商的采购入库平均单价；美＝收货拒收率（`rejected_qty ÷ received_qty`），两项都取采购入库明细 | 两项同在一张明细表，S7 编数据简单 | 同 DEC-012 |
| **DEC-014** | 问 3「BOM 利润最大化」的口径（A 第 5／6 步） | 某张销售订单上的某个物料有几个有效 BOM，利润＝订单单价 − BOM 单位成本，取最高者；「符合要求」＝ BOM 产出的正是订单上那个物料 | 标准答案可精确算出；对 S7 的要求明确 | 同 DEC-012 |

**E. Insights**

| 编号 | 决策内容 | 最终选择 | 选择理由 | 失效条件 |
|---|---|---|---|---|
| **DEC-016** | Insights 的完成口径（A 第 6／7 步） | `install-app` 成功＋`/insights` 能打开＋对本站点建数据源、跑一次查询出结果；**装不上则当场记延迟需求，并把 331 条译名从 S6 范围扣掉** | 用最小代价实际验掉 RW-02；不进演示，不建看板 | — |

**F. 演示终端连通性**

| 编号 | 决策内容 | 最终选择 | 选择理由 | 失效条件 |
|---|---|---|---|---|
| **DEC-017** | CR-015 怎么算验到（A 第 7／8 步） | **三条**：① 异地终端登录并打开一张单据；② 本机发一条测试事件，异地终端界面上实收到；③ 反证：故意让实时通道不通，同一套检查须报失败 | 该失效在本机测不出（LG-007）；③ 证明检查分得清通与不通 | — |
| **DEC-018** | 「异地终端」的环境（A 第 8 步） | **局域网与外网两种都验**，各跑一遍 DEC-017 | 用户裁决 | 演示场景确定为其中一种时可减 |

**G. 工作量**

| 编号 | 决策内容 | 最终选择 | 选择理由 | 失效条件 |
|---|---|---|---|---|
| **DEC-019** | 本 Stage 工作量（A 第 8／9 步） | **6.5–12 人日**（原 5.5–9.5）。上限 12 含 Raven 最坏值；Raven 取常规值时为 6.5–10 | 按 A 步定下的范围逐项重估（RW-09） | 报表通道走通则上限按 10 算；外网连通机制在 C 步定后可再收窄 |

### 3.3 被否决方案记录

| 方案 | 否决理由 |
|---|---|
| **NV-001** 四个 App 先 fork 到 `PhilixKuro` | 本项目不预期改它们的源码，fork 只带来四个仓库的同步负担（A 第 1 步） |
| **NV-002** CRM／Insights／Raven 用 `develop` | 开发线不稳；唯一好处（与 S2 读码版本一致）可由复核读码替代。Insights 最终取 tag（DEC-015）（A 第 1 步） |
| **NV-003** 问 1 改为只按 `expected_deal_value` 排序 | 不是用户选的口径，漏斗概率不再参与（B 讨论第 1 步） |

A 步另有几个落选项未单独编号，列此防重复讨论：

| 落选项 | 否决理由（出处） |
|---|---|
| 卸载 `frappe_china` 再装以归位 | 删本 app 全部 DocType 表，S4 的数据要重建（A 第 1 步 ④ 选项 B） |
| 不调序、只验三个覆盖位 | S6 的译名 csv 会被同源词译文盖掉，问题推迟到 S6 才暴露（A 第 1 步 ④ 选项 C） |
| 本 Stage 顺手接 `after_migrate` 自检 | 把 S8G-S1 的 IM-007 提前做了一半（A 第 1 步 ④ 选项乙） |
| 接受 HRMS 建出的「Expense Claims」科目／规定演示前不保存公司 | 科目表在一次普通保存后就不合准则，后者很脆（A 第 2 步 ② 选项乙、丙） |
| CRM 从 Deal 开始演示 | 漏斗看板与 Lead 段到 S7 才第一次见（A 第 3 步选项 B） |
| 勾「状态变更时建客户」 | 省不掉报价对象是「商机」这句解释，多一处配置（A 第 3 步选项乙） |
| bot 按原完成标志建五类工具 | 两类不生效；`Update Document` 让 AI 在现场能改单据（A 第 4 步选项 B） |
| 等 S7 数据造好再测三问／在演示站造数据测 | 前者违反 RW-04 且成循环依赖；后者污染空账基准点（A 第 4 步选项乙、丙） |
| Insights 装 `main`（v2）或 `develop` 头 | 前者是停更旧线、S2 的判断不适用；后者是开发线（A 第 6 步选项 B、C） |
| Insights 只装不跑／加建看板 | 前者没验 RW-02；后者没有消费方（A 第 6 步选项乙、丙） |
| CR-015 只验连接是否建立 | 连接建立后鉴权仍可能被拒；没有反证，检查本身可能永远报「通」（A 第 7 步选项乙） |

---

## 四、最终需求描述

### 4.1 本 Stage 交付什么、不交付什么

| 交付 | 不交付（去向） |
|---|---|
| 四个官方 App 装在测试站与演示站，版本由 `apps.json` 锁定、新机器可重建 | 四个 App 的译名与导航折叠（S6 的 CR-002／CR-010） |
| `frappe_china` 归位到业务 app 末位，且新机器重建时自动归位 | `after_migrate` 接线自检（S8G-S1 的 IM-007） |
| `frappe_china` 为中式公司预配 HRMS 报销类型科目 | 计件工资（IM-016）；HRMS 的其它配置（考勤、薪资结构等） |
| CRM 的 Lead → 销售订单链路与漏斗看板实点通过 | 演示用的正式商机、客户、物料（S7 的 CR-011／CR-012） |
| Raven 连上 LiteLLM、只读 bot、三问实测结论 | 模型选择（DEC-011，归用户）；三问的复杂口径（§4.6.6 四条延迟需求） |
| Insights 装成并跑通一次查询 | Insights 进演示、建看板（NV-022） |
| 演示终端连通机制，局域网与外网各验三条 | 演示操控与心跳自检（S7 的 CR-008／CR-009） |
| 演示站装完四个 App 后的新空账基准点 | — |

### 4.2 接入与装载（TS-001～TS-004）

#### 4.2.1 版本锁定与重建脚本

**`apps.json` 的四个新条目**（DEC-001／002／015）：

| App | 仓库 | 分支或 tag | commit | 目录名 |
|---|---|---|---|---|
| HRMS | `https://github.com/frappe/hrms.git` | 分支 `version-16` | 开工时锁定（2026-10-05 分支头 `6f5ac249`） | `hrms` |
| CRM | `https://github.com/frappe/crm.git` | 分支 `main` | 开工时锁定（2026-10-05 分支头 `deedce73`） | `crm` |
| Insights | `https://github.com/frappe/insights.git` | **tag `v3.14.2`** | `5447f162`（tag 指向，A 步已核） | `insights` |
| Raven | `https://github.com/The-Commit-Company/Raven.git` | 分支 `main` | 开工时锁定（2026-09-25 分支头 `e890308e`） | `raven` |

目录名取自各仓库 `pyproject.toml` 的 `name`（已核 `crm`／`insights`／`raven`；HRMS 为 `hrms`）。**锁定时须在被锁的那个 commit 上重读 §4.2.2 引用的 HRMS 代码**——那里的跳过条件是 DEC-005 的前提。

**重建脚本须满足的五条**（读码查出，现脚本都不满足）：

| # | 要求 | 现状（读码） |
|---|---|---|
| 1 | **能按 tag 取 App**（Insights） | `setup.sh:157` 用 `git ls-remote --heads` 预检可访问性，tag 不在 heads 里，预检失败即中止；`bench get-app --branch` 接受 tag 与否未实测 |
| 2 | **按 `apps.json` 的顺序装 app** | `setup.sh:303` 第 6 段按 `apps/*/` 的字母序 `install-app`：会先装 `crm` 后装 `erpnext`，且 `frappe_china` 排在 `hrms`／`insights`／`raven` 之前。最终顺序由第 3 条兜住，但装的先后也决定各 app 安装钩子跑时看到什么（§4.2.2 入口 2），不应交给字母序 |
| 3 | **装完全部 app 后让 `frappe_china` 回到业务 app 末位**（DEC-003），幂等 | 无此段 |
| 4 | **官方 App 的 remote 归位**：不 fork（DEC-001），与 frappe／erpnext 的「`origin`＝自有 fork、`upstream`＝官方」区分开 | `setup.sh:243-247` 把 frappe／erpnext 之外一律当「自有 app 无上游」；具体怎么配留 C 步 |
| 5 | **`lock-apps.sh` 不破坏 `apps.json` 的顺序与 tag** | `lock-apps.sh` 按目录名排序重写整个文件，`branch` 取 `rev-parse --abbrev-ref HEAD`——Insights 按 tag 检出时得到 `HEAD`，写回后下次重建会去取一个叫 `HEAD` 的分支 |

**归位的落点与时机**：装 app 的流程结束时做一次（测试站、演示站、新机器重建都经过它）。用框架入口 `update_installed_apps_order`（`frappe/core/doctype/installed_applications/installed_applications.py:108-136`）：只改顺序、拒绝增删、强制 frappe 居首、写一条 `Version` 留痕、限 System Manager。**目标顺序**：`frappe → erpnext → crm → hrms → insights → raven → frappe_china`（四个业务 app 之间沿用 ADR-0003；`frappe_debug` 在 S7 建，届时排在 `frappe_china` 之后）。

**归位后的缓存**（LG-002，本步读码推进一半）：`update_installed_apps_order` **不清缓存**（只清 `request_cache`）。钩子表有两层缓存：开发模式下是进程内的 `site_cache`（`frappe/__init__.py:1003-1004`），否则是 `client_cache` 的 `app_hooks` 键（`:1006-1009`）；`installed_apps` 也在全局缓存键里（`cache_manager.py:25`）。⇒ **归位后须清缓存，且已在跑的 web／worker 进程要重启**，否则仍按旧顺序取钩子。是否足够由 TS-007 实测。

**`site_config.json` 里的 `installed_apps` 镜像**（新发现，LG-010）：v16 装卸 app 时把顺序镜像进 `site_config.json`（`installer.py:390`、`:658-663`），`update_installed_apps_order` 不同步它。读码在 frappe 的 python 侧没找到读这个键的地方（补丁注释说是给 bench 等外部工具读的），故镜像过期对站点本身预计无害；**是否顺手同步留 C 步定**。

#### 4.2.2 HRMS 报销类型的科目预配（TS-004，DEC-005）

**为什么要做**（读码，HRMS `version-16` 分支头）：HRMS 挂在 `Company.on_update` 上的 `set_expense_claim_type_accounts`（`hrms/overrides/company.py:119-135`）对每个报销类型检查「该公司是否已有 `Expense Claim Account`」，没有就按名找或新建一个无科目号的 `Expense Claims` 科目（父级依次取 `Indirect Expenses` 组、第一个 Expense 类组科目——在 `HDTH` 上是 `540 - 费用类`），并设为该类型的默认科目。入口有 `if frappe.local.flags.ignore_chart_of_accounts: return`。**已有 `Expense Claim Account` 即跳过**（`:125-126`）——DEC-005 就靠这一句。

**HRMS 装时建的 5 个报销类型**（`hrms/setup.py:338-342`）：`Calls`／`Food`／`Medical`／`Others`／`Travel`。**记录名恒为英文**：那里的 `_` 是 `install_fixtures.py:11-15` 的假翻译函数，原样返回（注释写明「建英文记录、靠 Translate Link Fields 显示译名」）。⇒ 按这 5 个英文名匹配即可，不受会话语言影响。

**映射表**（Claude 按费用性质推定，**全部待领域专家确认**）：

| 报销类型 | 默认科目 | 推定理由 |
|---|---|---|
| `Calls`（通讯费） | `5602090 管理费用_办公费` | 小企业准则科目表无单列通讯费，常并入办公费 |
| `Food`（餐费） | `5602040 管理费用_业务招待费` | 报销的餐费多为招待；⚠ 出差途中的餐费按惯例进差旅费，二者混在一个类型里 |
| `Medical`（医疗费） | `5602010 管理费用_职工薪酬` | 职工医疗报销属职工福利，福利费归入职工薪酬 |
| `Others`（其他） | `5602250 管理费用_其他` | 兜底 |
| `Travel`（差旅费） | `5602130 管理费用_差旅费` | 一一对应 |

五个科目号均已在 `frappe_china/cn_tax/chart_of_accounts/cn_smes_chart_of_accounts2024.json` 里核到。**已知限制**：一个报销类型对一家公司只能设一个默认科目（`expense_claim_type.py` 的 `validate_repeating_companies`），故销售人员的同类报销默认会进管理费用而非销售费用。报销单逐行可改科目，演示不受影响；实地考察时问客户会计（LG-011）。

**三个触发入口**（缺一个就有一条路径漏配）：

| # | 入口 | 场景 | 要求 |
|---|---|---|---|
| 1 | 建中式公司时（`frappe_china` 建账流程内） | S7 的数据生成器反复建公司；客户正式库建公司 | 只在报销类型 DocType 存在时配；**`frappe_china` 不得在 `required_apps` 里声明 HRMS，也不得在模块顶层 import `hrms`** |
| 2 | **HRMS 装到已有中式公司的站点上时** | 本 Stage 的演示站：`HDTH` 早于 HRMS 存在，装完时它没有任何 `Expense Claim Account`，下一次保存公司即触发 | 装完 HRMS 后对全部中式公司补配。可用机制之一：`frappe_china` 注册 `after_app_install`——框架每装一个 app 后对已装 app 的这个钩子逐个调用（`installer.py:363-364`）。具体手段留 C 步 |
| 3 | 以后新增报销类型 | 用户在 HRMS 里自己加类型 | **本 Stage 不做**（DEC-005 失效条件已接受）；登 LG-012 |

**只配缺的、不改已有的**：某类型对某公司已有默认科目时不覆盖。

**另两件交 C 步核的事**：① HRMS 的 `set_default_hr_accounts` 按名找 `Payroll Payable` 找不到、写入空值（A 第 2 步），读码判为无实害，不处理；② `Payment Entry` 被 HRMS 的 `EmployeePaymentEntry` 整类覆盖（`hrms/hooks.py:155-160`），读码看不出对 S4 收付款与银行对账的影响，**只靠 TS-005 跑 S4 全量测试来验**。

### 4.3 安装次序与两站（TS-005／TS-006，DEC-006）

**测试站先行**：

1. `test.localhost` 装四个 App（顺序 crm → hrms → insights → raven，**Insights 最后**，RW-02：装不上不阻塞其余三个）。
2. 归位并清缓存、重启进程（§4.2.1）。
3. 跑 `frappe_china` 全量测试，**全部通过**。基数以 `bench --site test.localhost run-tests --app frappe_china` 实际收集到的条数为准（S4 收口时是 160 条）。
4. 新建一家中式测试公司：自检通过、科目数 266、无 `Expense Claims` 科目、5 个报销类型各有指向 §4.2.2 映射的默认科目。
5. 在 `zh` 会话与 `en` 会话（或后台任务）下各保存一次该公司，科目数不变（验 LG-003：中英两个重复科目）。
6. 清掉测试公司与测试单据。

**演示站后行**（测试站 1–5 全过才装）：

1. **装前备份**（`docker/backup.sh`）。⚠ `backup.sh` 取「每类最新一份」（`:25-28`），`restore.sh` 不带参数取最新——执行前核空账基准点 `20261004_005331` 仍在、能被显式指定。
2. 装四个 App、归位、清缓存、重启进程。
3. 对 `HDTH` 补配报销类型科目（§4.2.2 入口 2），然后**保存一次 `HDTH`**：科目数仍 266，`check_all_cn_companies()` 的多余科目为空。
4. 再备份一次，作为**装完四个 App 后的新空账基准点**，写进项目概况「开发环境」节（D 步）。

### 4.4 归位验收（TS-007，DEC-004）

在演示站上验：

1. `frappe.get_installed_apps()` 里 `frappe_china` 位于 `crm`／`hrms`／`insights`／`raven` 全部之后。
2. 三个 whitelisted 覆盖（`frappe_china/hooks.py:202-206`）经 `frappe.get_hooks("override_whitelisted_methods")` 解析，末项是 `frappe_china` 的实现。
3. **一条撞源词的测试译名由 `frappe_china` 胜出**：取一个在四个 App 至少一个的 `zh` 译文里出现、译法与 `frappe_china` 测试行不同的源词，验 `zh` 会话下取到 `frappe_china` 的译法。合并逻辑：`frappe/translate.py:172-187` 按 `installed_apps` 顺序逐个 `update`，后者覆盖前者。源词取哪个、测试行用后撤不撤，留 C 步；**要求是这条验收在不调序时能失败**。
4. `check_all_cn_companies()` 直接调一次，`HDTH` 全部通过。

**交 S6 的约束**：同一 app 内 `.mo` 覆盖 `.csv`（`translate.py:181-182`），`frappe_china` 不得生成 `.mo`（Stage 概况长效信息 #2）。

### 4.5 CRM（TS-008，CR-013，DEC-007／008）

**配置**（读码 CRM `main`：`erpnext_crm_settings.json`、`fcrm_settings.json`、`crm_deal.py`）：

| 设置 | 值 | 说明 |
|---|---|---|
| `ERPNext CRM Settings.enabled` | 1 | 启用后 CRM 自动装报价单预填脚本 |
| `ERPNext CRM Settings.is_erpnext_in_different_site` | 0 | 同站部署 |
| `ERPNext CRM Settings.sync_products` | 1（默认） | CRM 产品映射到 ERPNext 物料，报价单明细才能预填 |
| `ERPNext CRM Settings.create_customer_on_status_change` | 0（默认） | DEC-008 |
| **`FCRM Settings.currency`** | **CNY** | ⚠ 默认为空，空时 CRM 按 `USD` 当系统币种算汇率（`crm_deal.py:275`）；看板金额乘的就是这个汇率（`dashboard.py:677-683`） |
| `CRM Deal.currency` | CNY | 字段无默认值；由 Deal 建出的客户取 `default_currency = deal.currency`（`erpnext_crm_settings.py:671`），空或非 CNY 会一路带进报价单与销售订单 |

后两行是 LG-004 的读码答案；**怎么保证 Deal 的币种恒为 CNY 留 C 步**，实点时核报价单与销售订单的币种。

**漏斗看板的前提**：「预测收入」按 `expected_closure_date` 的月份分组、`expected_deal_value × probability ÷ 100 × 汇率` 求和。`FCRM Settings.enable_forecasting`（默认 0）开启后 Deal 保存时强制要求金额与预计成交日（`crm_deal.py:255-259`）；它是否门控看板本步未读。**要求**：实点用的商机都填金额、概率、预计成交日；开不开 `enable_forecasting` 留 C 步按看板实际取数定。

**实点链路**（完成标志①，DEC-007）：

1. 在 `/crm` 建一条 Lead，转为 Deal（带一个临时测试物料对应的产品，金额、概率、预计成交日都填）。
2. 把 Deal 推进至少两档。
3. Deal 页「Create Quotation」在新标签页打开 ERPNext 报价单：公司、联系人、明细行已预填，报价对象为 `CRM Deal`。
4. 提交报价单 →「创建 → 销售订单」→ 保存：**站上自动出现一个由 Deal 建出的客户**，销售订单的客户即它（LG-085 的实测确认）。
5. 回 `/crm` 看板：该 Deal 计入预测收入与按阶段分布。
6. 清掉临时物料与链路上的单据（不留在空账基准点里）。

**交 S6／S7 的事实**：CRM 是独立前端 `/crm`，演示要在 `/crm` 与 `/app` 两套界面间切换（Stage 概况长效信息 #3）。

### 4.6 Raven 与三问（TS-010／TS-011，EX-001）

#### 4.6.1 Raven → LiteLLM 的连接（DEC-011）

- Raven Settings 启用本地模型，提供方 `OpenAI Compatible`，地址指向宿主上的 LiteLLM（宿主端口 7999）。**容器里访问宿主要用 `host.docker.internal`，不能用 `127.0.0.1`**。具体 URL 由 C 步定、D 步实测。
- 密钥由用户提供，存 Raven Settings 的密码字段，**不进任何文档、仓库与日志**。
- bot 的模型填用户在 LiteLLM 里配的别名；**本 Stage 不选模型**，测试报告记下别名。
- 走 LiteLLM 时无代码解释器——**AI 的算术全靠模型自己**，影响问 1 与问 3。

#### 4.6.2 bot 与只读工具（DEC-009）

- 一个演示 bot，只挂只读工具：按三问要用的 DocType 各建 `Get List` 与 `Get Document` 两条 `Raven AI Function`，外加一条报表通道（§4.6.3）。**不建** `Update`／`Create`／`Delete`（后两者的 handler 在 `main` 上不存在，LG-005）。
- 至少覆盖：`CRM Deal`、`CRM Deal Status`（问 1）；`Purchase Receipt`、`Supplier`、`Item`（问 2）；`Sales Order`、`BOM`、`Item`（问 3）。最终清单 C 步按 §4.6.5 的取数路径定。
- **⚠ 子表取不到父单信息**（本步读码，LG-009）：`handle_get_list` 只放行本表 `meta.fields` 里的字段与 `name`／`creation`／`modified`／`modified_by`／`owner`／`docstatus`，**`parent` 不在其中**，传了也被忽略。而供应商在 `Purchase Receipt` 主表、拒收数在 `Purchase Receipt Item` 子表；订单单价在 `Sales Order Item` 子表。⇒ 问 2、问 3 的现成工具路径只能是「主表 `Get List` 列单号 → 逐张 `Get Document` 取整单含明细」，或走报表通道。前者在最小数据下可行，S7 的 100 条下调用次数会多。
- **权限**：`Get List` 末端是 `frappe.get_all`，绕过权限（LG-091）；演示无妨，上生产前须处置（本 Stage 不处置）。

#### 4.6.3 报表通道（DEC-009，LG-006）

- 一条 `Custom Function`，函数路径 `raven.ai.functions.get_report_result`，让 AI 跑 ERPNext 现成报表、拿到列与行。读码：取 `Report` 记录后直接 `report.get_data(...)`（`functions.py:256-283`）；**调用路径上是否校验报表权限本步未查清**（`Report.is_permitted` 存在，`get_data` 路径上是否调用未读到）。
- 候选报表：问 2 → `purchase_analytics`、`item_wise_purchase_history`、`supplier_quotation_comparison`、`purchase_receipt_trends`；问 3 → BOM 与毛利类报表。**读码看到这几张采购报表都不含拒收数**（`buying/report/`、`stock/report/` 下 `rejected_qty` 零命中），故问 2 的「美」预计仍要靠单据路径。

#### 4.6.4 退路：自写查询函数

**触发**（任一）：报表通道实测不通；或某一问按 §4.6.5 跑 3 次未全对。**做法**：为该问写一个 `Custom Function`，直接返回该问口径下算好的结果；放 `frappe_china` 还是 `frappe_debug` 留 C 步（演示专用的查询按 ADR-0013 倾向 `frappe_debug`，但它在 S7 才建）。**改走退路后须重测该问并在测试报告注明**，并按 RW-04 重判该问是否进演示。工作量按 DEC-019 的最坏口径。

#### 4.6.5 三问的口径、数据与判据

**统一判据**（DEC-010）：每问在 `test.localhost` 上用最小数据事先算好标准答案；同一问法跑 3 次，**3 次都答对且说得出依据**（引了哪些单据或报表）才算「答得出」。测完清掉测试数据。测试报告逐问记：问法原文、模型别名、3 次各自的回答摘要与对错、用到的工具调用、结论（答得出／答不出／改走退路后答得出）。

**数据通则**：标准答案只计已提交单据（`docstatus = 1`）；草稿与已取消单据各放一条作干扰项。

| 问 | 口径 | 最小数据要求 | 标准答案 |
|---|---|---|---|
| **问 1「找单子」** | 进行中的商机（状态类型非 Won／Lost）按 **`expected_deal_value × probability ÷ 100`** 排序，取**前 3 名**（DEC-012／020） | 8–10 个商机，覆盖各档，含已赢、已输各至少 1 个（干扰项）；**「按加权金额排」与「只按金额排」的前 3 名须不同**（否则测不出 AI 有没有真的乘）；不出现并列 | 前 3 名及其加权金额 |
| **问 2「货美价廉」** | 指定一个物料比较各供应商：**价＝采购入库平均单价，美＝拒收率 `Σrejected_qty ÷ Σreceived_qty`**（DEC-013） | 1 个物料、3 个供应商、每家 2–4 张采购入库，单价与拒收数各不相同；**「最便宜」与「拒收率最低」须不是同一家**，问法里说明二者如何取舍（问法由 C 步定稿） | 各供应商的平均单价、拒收率与按问法规则选出的那一家 |
| **问 3「BOM 利润最大化」** | 指定一张销售订单上的一个物料：其有效 BOM 中，**单位利润＝订单单价 − BOM 单位成本**（单位成本＝`total_cost ÷ quantity`），取最高者（DEC-014） | 1 个物料、3 个有效 BOM（成本不同，至少一个 `quantity ≠ 1` 以验除法）、1 个无效 BOM（干扰项）、1 张含该物料的已提交销售订单 | 各 BOM 的单位成本与单位利润，及最高者 |

问 1「前 3 名」与问 3「单位成本＝`total_cost ÷ quantity`」是本文件补的细化（A 步未定数目、未写除法）。问 2 的「平均单价」取 `net_rate` 还是 `rate`、按数量加权还是按单据平均，C 步定一种；**要求是标准答案的算法与问法所说一致**。

**交 S7 的事实**（Stage 概况长效信息 #4）：采购入库要填拒收数；同一弹簧要有两三个成本不同的有效 BOM；商机要有金额、概率、预计成交日。

#### 4.6.6 未选口径（延迟需求，A 第 6 步）

四条进本 Stage 登记册，唤醒条件统一为「四阶段战略第 ④ 阶段开工时」：「卡住的单」；「货美」改用来料检验不合格率；「货美」加准时交货率；BOM 选择加交期约束。编号见 Stage 概况登记册（`SH-P1S5001`～`004`）。

### 4.7 Insights（TS-009，IM-006，DEC-015／016）

- 装 tag `v3.14.2`（§4.2.1），四个 App 里最后装。
- 完成口径：`install-app` 成功；`/insights` 能打开；对本站点建一个数据源、跑一次查询出结果（例如销售订单条数）。
- **装不上**（依赖装不上、或装上一跑就崩）：当场记延迟需求，**把 331 条译名从 S6 范围扣掉**；其余三个 App 照常推进。
- 环境风险比原判断低（`duckdb`、`pandas` 有 `cp314` 的 manylinux 预编译包），`ibis-framework 11.0.x` 是否纯 Python 未查，以实装为准。
- **不进演示**（NV-022）；直连 MariaDB 绕过权限层，演示站可接受，客户正式库装不装另议。

### 4.8 演示终端连通性（TS-012，CR-015，DEC-017／018）

**问题**（LG-007，本步重读代码，读法成立）：浏览器连实时服务时取页面的主机名、换成实时服务的端口（`socketio_client.js` 的 `get_host`）。实时服务按以下顺序认站点（`realtime/middlewares/authenticate.js:89-104`）：请求头 `x-frappe-site-name` → 主机名是 `localhost`／`127.0.0.1` 时取默认站点 → **否则取来源（`Origin`）的主机名** → 再否则取 `Host`。命名空间是站点本名 `erx.localhost`，二者不等即 `Invalid namespace`；另要求 `Host` 与 `Origin` 的主机名一致，否则 `Invalid origin`（`:17-23`）。页面那一侧有「任何主机名都服务默认站点」，照常打开。⇒ **异地终端用 IP 或别的主机名访问时，页面正常、实时通道被拒，界面不报错**；本机用 `localhost` 访问测不出来。仍是读码结论，本任务实测。

**连通机制留 C 步**，须满足：

1. 页面与实时两条通路都从异地可达，且实时通道过得了上述两项校验。
2. 局域网与外网两种环境都能用（DEC-018）；外网可达的方式由 C 步定。
3. 本机原有的 `localhost` 访问方式不受影响。
4. 不改上游源码（L5）。

**暴露面约束**（LG-008，本步补查现状）：

| 项 | 现状（读码） | 要求 |
|---|---|---|
| 管理员口令 | `docker/.env.example:5` 与 `docker/up.sh:40` 的缺省都是 `admin` | **外网暴露前改为非缺省值**，不写进仓库 |
| 对外端口 | `docker/compose.yaml:55-57` 发布 8000（页面）／9100（实时）／6787（资源监视），未写绑定地址；MariaDB 与 Redis 未发布 | **对外只放页面与实时两条**，6787 不对外 |
| 开发模式 | 站点开着 `developer_mode`（`setup.sh` 第 7 段） | 外网暴露期间是否关留 C 步判（开发模式下报错页带堆栈） |
| 访问控制 | 只有 Frappe 登录 | **外网暴露期间站点即公网可登录**。是否加一层访问控制、是否只在演示时段开放，留 C 步定，但须在方案里显式写出取舍 |

**验法**（DEC-017，每种环境各一遍）：

1. 异地终端登录、打开一张单据；
2. 本机发一条测试事件（`publish_realtime`，`user` 取异地终端登录的用户），**异地终端界面上实收到**（可见的界面反应，不只看连接建立）；
3. **反证**：故意让实时通道不通（如只断实时那一路），同一套检查须报失败。

测试事件的事件名与界面表现留 C 步；**不复用 `erx_demo_step`**（那是 S7 的契约，ADR-0008），用一个只供本验证的事件名。

### 4.9 工作量（DEC-019）

| 项 | 范围 | 人日 |
|---|---|---|
| 接入公共部分 | TS-001～003、TS-005～007 | 1–1.5 |
| IM-005 HRMS | TS-004（三个入口中的两个）＋ `HDTH` 保存验证 | 0.5–1 |
| IM-006 Insights | TS-009 | 0.5 |
| CR-013 CRM | TS-008 | 1–1.5 |
| EX-001 Raven | TS-010／011：连接 0.5＋工具与报表通道 0.5＋三问数据与标准答案 1–1.5＋实测 0.5 | 2.5–3（**最坏 3.5–5**） |
| CR-015 连通性 | TS-012 | 1–2.5 |
| **合计** | | **6.5–12**（Raven 取常规值 **6.5–10**） |

读码估算，未实做。本步新查出的两处（重建脚本五条、HRMS 装到已有公司时的补配入口）按原区间吸收、未上调；C 步拆任务后若超出，按 RW-09 回写路线文档。

### 4.10 业务规则

本 Stage **不新增也不变更**业务规则。§4.2.2 的报销类型映射是配置（客户会计可改），不是必须恒为真的领域不变量，不进 `docs/业务规则.md`；它受 BR-001 约束——映射目标只取《小企业会计准则》科目表里的明细科目。

### 4.11 接入点与侵入度

| 改动 | 落点 | 侵入度（开发守则 L0–L5） |
|---|---|---|
| 四个 App 的条目与重建脚本 | `docker/apps.json`、`docker/scripts/setup.sh`、`docker/lock-apps.sh` | 非 app 代码 |
| 归位 | 重建脚本调框架入口 | L0（只改 `installed_apps` 全局值） |
| 报销类型科目预配 | `frappe_china` 建账流程内 ＋ 一个安装期钩子（候选 `after_app_install`） | L2＋L3 |
| CRM／Raven／Insights 的配置 | 站点上的设置与 `Raven AI Function` 记录 | L0 |
| 自写查询函数（仅退路） | `Custom Function` 指向的自有 whitelisted 方法 | L2 |
| 连通机制 | 留 C 步；不得 L5 | 待定 |

**本 Stage 不用 `override_doctype_class`**（ADR-0004），也不新增 `override_whitelisted_methods`。

---

## 五、影响范围分析

### 5.1 直接影响

| 受影响对象 | 影响 | 范围 |
|---|---|---|
| 站点的 app 集合与顺序 | 新增四个 app；`frappe_china` 调回业务 app 末位 | 测试站、演示站 |
| `Company` 的 `on_update` | 新增 HRMS 的三个钩子与一个 `validate` 钩子；与 `frappe_china` 的两个钩子同挂一处 | 全站建公司与保存公司 |
| `Payment Entry` | 被 HRMS 的 `EmployeePaymentEntry` 整类替换 | 全站收付款、S4 的银行对账 |
| `Sales Order` | CRM 挂 `before_validate`，无客户时从 Deal 建客户 | 全站下销售订单 |
| 全部 DocType 的写事件 | Raven 对 `"*"` 挂五个写事件（`after_insert`／`on_update`／`on_trash`／`on_cancel`／`on_submit`，用于文档通知） | 全站写路径多一层 |
| 报销类型的默认科目 | 中式公司下 5 条 `Expense Claim Account` | 装 HRMS 的站点 |
| 重建脚本 | 装 app 顺序、tag 检出、归位、remote 归位 | 新机器重建 |
| 演示站数据 | 新空账基准点（四个 App 的安装记录与设置） | 演示站 |
| 网络暴露 | 外网验证期间站点对外可达 | 本机 |

### 5.2 间接影响

| 下游 | 影响 |
|---|---|
| **S6 译名与导航** | 四个 App 的未译条目进 CR-002 范围（Insights 装不上则扣 331 条）；四套入口进 CR-010 折叠范围；**`/crm` 是独立前端，译名要覆盖两套界面**；`frappe_china` 不得生成 `.mo` |
| **S7 数据与操控** | CR-012 按三问结论编数据（拒收数、多 BOM、商机三字段）；`Sales Order.before_validate` 建客户对生成器有利；**S7 改服务端钩子时 Raven 已在场**（路线文档 §四 S5 第 10 条）；连通机制是 CR-008／CR-009 在异地终端成立的前提；**生成器反复建公司时报销类型科目由 §4.2.2 入口 1 配好** |
| **S8G** | IM-016 计件工资用 HRMS 的 `Additional Salary`；IM-007 的自检断言对象是「`frappe_china` 在全部业务 app 之后」 |
| 项目文档 | 项目概况的模块结构表、技术栈表、「已知限制」（hrms 未安装那条）、开发环境节（新基准点）在 D 步装完后改写 |

---

## 六、风险与应对

| 编号 | 风险 | 严重程度 | 应对 | 当前状态 |
|---|---|---|---|---|
| **RS-001** | HRMS 与 `frappe_china` 同挂 `Company.on_update`，保存公司时 HRMS 往科目表里建一个无科目号的 `Expense Claims`（RW-01） | 高 | DEC-005 预配三入口中的两个（§4.2.2）；测试站先行（§4.3） | D 步处理 |
| **RS-002** | HRMS 整类覆盖 `Payment Entry`，S4 的收付款与银行对账行为可能变 | 高 | 测试站装完跑 S4 全量测试（DEC-006 ②）；不过则停在测试站，不装演示站 | E 步验 |
| **RS-003** | 归位后缓存未失效，钩子仍按旧顺序取（LG-002），覆盖与译名表面看对、实际未生效 | 中 | 归位后清缓存并重启进程；TS-007 第 3 条验收在不调序时能失败 | D 步实测 |
| **RS-004** | 重建脚本按字母序装 app、不认 tag、`lock-apps.sh` 写坏 tag（§4.2.1 五条），新机器重建得到不同的站 | 中 | 五条全部写进 D 步；E 步按 §4.2.1 表逐条核 | D 步处理 |
| **RS-005** | Insights 依赖在容器里装不上（RW-02） | 中 | 最后装；装不上当场记延迟需求、扣 S6 的 331 条 | D 步实测 |
| **RS-006** | Raven 后两问答不出（RW-04）；问 1 依赖模型算术（DEC-020） | 高 | 报表通道先试；不行走自写函数退路（§4.6.4）；答不出则重判是否演示 AI | D／E 步 |
| **RS-007** | 三问结论只对测试时的模型别名、只对最小数据成立 | 中 | 报告记别名；用户换模型须重测（DEC-011）；S7 的 100 条下须重测（DEC-010） | 长期 |
| **RS-008** | 异地终端实时通道被静默拒连（LG-007），且本机测不出 | 高 | DEC-017 三条含反证；两种环境各验一遍 | C 步定机制 |
| **RS-009** | 外网暴露期间站点公网可登录，管理员口令是缺省值 `admin` | **高** | 暴露前改口令；只放两条通路；访问控制与开放时段 C 步显式定（§4.8） | C 步定 |
| **RS-010** | 装演示站前的备份挤掉空账基准点 | 中 | 执行前核 `20261004_005331` 仍在、可显式指定（§4.3） | D 步执行前 |
| **RS-011** | CRM 币种默认为空，按 USD 算汇率，金额与客户币种错一路（LG-004） | 中 | `FCRM Settings.currency` 与 Deal 币种取 CNY（§4.5）；实点核报价单与销售订单币种 | D 步处理 |
| **RS-012** | 报表通道调用路径上的权限校验未查清（LG-006） | 低（演示） | 演示 bot 只给演示用户；上生产前同 LG-091 一并处置 | 待 D 步读码 |
| **RS-013** | 本文件对四个 App 的读码都在分支头上，锁定的 commit 尚未定（LG-001） | 中 | 锁定后在被锁 commit 上复核 §4.2.2 的跳过条件、HRMS 的 `Company` 钩子清单、Raven 的 `handle_get_list` | C 步写方案前 |

---

## 七、预期使用流程

**实施者（一次性）**

1. 在测试站装四个 App → 归位 → 跑 S4 全量测试 → 建测试公司验科目 → 清掉。
2. 备份演示站 → 装四个 App → 归位 → 为 `HDTH` 补配报销类型科目 → 保存一次 `HDTH` 验科目 → 再备份出新基准点。
3. 配 CRM（集成、币种），在测试站实点 Lead → 销售订单一遍。
4. 配 Raven（LiteLLM 地址、密钥由用户填），建只读 bot；在测试站造三问的最小数据，逐问跑 3 次，写测试报告。
5. 装 Insights，建数据源跑一次查询。
6. 按 C 步定的连通机制，在局域网与外网各验三条。

**演示者（演示当天，S7 之后）**

1. 异地终端打开站点、登录。
2. 演示从 `/crm` 的线索起，推商机、看漏斗看板，在 Deal 页生成报价单，转到 `/app` 接单。
3. 向 bot 提**测试报告里判为答得出的那几问**，问法用报告里的原文，不现场即兴。

---

## 八、验收标准

> 四条完成标志（路线文档 §三 S5 行，本轮按 A 步改写）逐条落到 AC；**凡验收都须有正向证据**（查得到的记录、界面可见的结果、返回值），不能以「没报错」代替。

| 编号 | 验收条件 | 对应 |
|---|---|---|
| **AC-001** | 在 `/crm` 由 Lead 转 Deal、推进至少两档，经 Deal 页按钮生成报价单（明细已预填、报价对象 `CRM Deal`），提交后生成销售订单并保存；**站上出现由该 Deal 建出的客户**，销售订单的客户即它；报价单与销售订单币种为 CNY；该 Deal 出现在漏斗看板的预测收入与按阶段分布里 | 完成标志①；DEC-007／008 |
| **AC-002** | 演示站 `installed_apps` 中 `frappe_china` 位于 `crm`／`hrms`／`insights`／`raven` 全部之后；三个 whitelisted 覆盖解析到 `frappe_china`；撞源词测试译名在 `zh` 会话下取到 `frappe_china` 的译法，且**同一检查在不调序时失败**（反证做一次）；`check_all_cn_companies()` 对 `HDTH` 全过 | 完成标志②；DEC-004 |
| **AC-003** | Raven 经 LiteLLM 答复一次（连接通）；演示 bot 只挂只读工具与报表通道，**无** `Update`／`Create`／`Delete` 类记录；三问各跑 3 次，测试报告逐问记下问法、模型别名、每次对错与依据、结论 | 完成标志③；DEC-009～014／020 |
| **AC-004** | 局域网与外网两种环境各自：① 异地终端登录并打开一张单据；② 本机发测试事件，异地终端界面可见地收到；③ 让实时通道不通时同一检查报失败 | 完成标志④；DEC-017／018 |
| **AC-005** | 测试站装完四个 App 后 `frappe_china` 全量测试全部通过（基数以实际收集条数为准，并在报告里写明） | DEC-006 ② |
| **AC-006** | 测试站新建中式公司与演示站保存 `HDTH` 后：科目数 266、自检多余科目为空、无 `Expense Claims` 科目；5 个报销类型对该公司的默认科目与 §4.2.2 映射一致；`zh` 与 `en` 会话下各保存一次后科目数不变 | DEC-005／006 ③；LG-003 |
| **AC-007** | Insights：`install-app` 成功、`/insights` 能打开、对本站点数据源跑一次查询有结果；**或**装不上时延迟需求已登记、S6 范围已注明扣除 331 条 | DEC-016 |
| **AC-008** | 在一个空目录按 `apps.json` 重建（或在测试站模拟其关键段）：Insights 按 tag 取到 `5447f162`；app 按 `apps.json` 的顺序安装；装完 `frappe_china` 已在业务 app 末位；跑一次 `lock-apps.sh --show` 与写入，`apps.json` 的顺序与 Insights 的 tag 不被改坏 | DEC-001／003／015；§4.2.1 |
| **AC-009** | 外网验证开始前：管理员口令非 `admin`；从外部探测只有页面与实时两条可达 | LG-008；RS-009 |
| **AC-010** | 演示站装完后有一份新的空账基准点备份，`20261004_005331` 仍在；站上无测试物料、测试单据、三问测试数据残留 | §4.3；DEC-010 |

---

## 九、术语定义

| 术语 | 定义 |
|---|---|
| 归位 | 装完新 app 后，把 `frappe_china` 在 `installed_apps` 里的位置调回全部业务 app 之后（DEC-003） |
| 业务 app | 本 Stage 接入的四个官方 App：CRM、HRMS、Insights、Raven |
| 覆盖位 `[-1]` | 见 S4 需求文档 §九：多个覆盖机制取最后安装的 app 注册的那一项 |
| 空账基准点 | 演示站只有设置与演示公司、无业务单据的备份，供 S7 造数从它起步 |
| 测试站／演示站 | `test.localhost`／`erx.localhost`。前者一次性、随时可清；后者是演示用站，变更前须备份 |
| 报表通道 | 一条 `Custom Function` 指向 `raven.ai.functions.get_report_result`，让 AI 调 ERPNext 现成报表 |
| 答得出 | 同一问法跑 3 次，3 次都与事先算好的标准答案一致，且说得出依据（DEC-010） |
| 加权金额 | 商机的 `expected_deal_value × probability ÷ 100`（DEC-020）。`expected_deal_value` 本身是「预计成交金额」，不含概率 |
| 拒收率 | 采购入库明细的 `Σrejected_qty ÷ Σreceived_qty`（DEC-013） |
| 异地终端 | 不是运行站点的这台机器、经网络访问站点的设备；分局域网与外网两种（DEC-018） |
| 反证 | 故意制造失败条件，确认检查会报失败——证明检查分得清两种情形 |

---

## 十、遗留问题

| 编号 | 事项 | 状态 | 触发条件 | 关联任务 |
|---|---|---|---|---|
| **LG-001** | 读码基于分支头，须在锁定的 commit 上复核：HRMS 的 `set_expense_claim_type_accounts` 跳过条件与 `Company` 钩子清单、Raven 的 `handle_get_list` 与 handler 存在性、CRM 的 Deal 生成报价单按钮 | 待调研 | 锁定 commit 后、C 步写方案前 | TS-001／004／010 |
| **LG-002** | 归位后缓存：读码查明入口不清缓存、钩子有进程内与 `client_cache` 两层（§4.2.1）；清缓存加重启是否足够未实测 | 待实测 | D 步写归位段时 | TS-003／007 |
| **LG-003** | 不同会话语言下保存公司可能建出中英两个重复科目（读码推断）；DEC-005 预配后应不再触发 | 待实测 | TS-005 第 5 条 | TS-005 |
| **LG-004** | CRM 币种：读码查明 `FCRM Settings.currency` 默认为空、按 USD 算汇率，Deal 币种无默认值；怎么保证恒为 CNY 留 C 步 | 待 C 步落实 | C 步 | TS-008 |
| **LG-005** | Raven `main` 无 `handle_create_document`／`handle_delete_document`；完成标志③已改口径 | 已处置（本轮改完成标志） | — | TS-010 |
| **LG-006** | 报表通道可行性与调用路径上的权限校验，均未实测 | 待实测 | TS-010 | TS-010／011 |
| **LG-007** | 异地终端实时通道被按来访主机名认站点而拒连；本轮重读代码读法成立，仍未实测 | 待实测 | TS-012；解法留 C 步 | TS-012 |
| **LG-008** | 外网暴露的口令与端口约束（§4.8） | 待 C 步落实 | C 步 | TS-012 |
| **LG-009** | **Raven `Get List` 取不到子表的父单**（`parent` 不在放行字段里），问 2、问 3 走现成工具只能逐张 `Get Document`；S7 的 100 条下调用次数与成功率未知 | 待实测 | TS-011；S7 重测三问时 | TS-011 |
| **LG-010** | `update_installed_apps_order` 不同步 `site_config.json` 的 `installed_apps` 镜像；读码未见 python 侧读取方，是否同步留 C 步 | 待确认 | C 步 | TS-003 |
| **LG-011** | 报销类型一家公司只能一个默认科目，销售人员的报销默认进管理费用；映射表五行待领域专家确认 | 待确认 | 实地考察时问客户会计 | TS-004 |
| **LG-012** | 以后新增报销类型时，HRMS 仍会在下一次保存公司时建 `Expense Claims` 科目（DEC-005 已接受） | 暂缓 | 客户在 HRMS 里新增报销类型时；或 IM-016 开工时 | TS-004 |
| LG-085 | `Quotation → Sales Order` 是否需人工介入（需求图谱） | 读码已答，待 AC-001 实测确认 | TS-008 | TS-008 |
| LG-090 | Raven `Get List` 能否支撑跨表比价（需求图谱） | 前提仍成立（无聚合、无 join），另见 LG-009；由三问实测给结论 | TS-011 | TS-011 |
| LG-091 | `handle_get_list` 绕过权限（需求图谱） | 暂缓 | 上生产前 | — |
| LG-139 | 三个以上 app 时钩子顺序未实测（S4 移交） | 待实测 | 本 Stage 装完后由 AC-002／AC-005 部分覆盖 | TS-007 |

