# P1-S6-R9 C 步中途讨论记录（plannedDev C 步·开发方案，R8 E 报告回流）

**讨论主题**：R8 E 报告交给 C 的两处用词：称呼词候选、Raven 个人状态 `Available` 的译名
**日期**：2026-10-12
**参与者**：用户、Claude（Opus 5.5）
**性质**：`play-build` 契约纪律 3，就地记录 C 步开工时的取舍。**本文件不带状态值**——C 步状态值在本 Round 回执里。
**依据**：[R8 E 确认报告](../R08-确认/P1-S6-R8-E确认报告.md)「清单外发现」（称呼词「由 C 步给候选词，交用户定」）与「用户裁决」第 4 条（IT-048 只修 Raven 一处）
**承接说明**：步号自第 1 步起（同 R3、R6 先例）；决策号接 R6 C 讨论记录续编（DEC-039 起），被否决号接 R6（NV-036 起），遗留号接 R6（LG-011 起）。

---

## 演化过程

#### 第 1 步：C（R9）开工；称呼词与 Raven「Available」定词

**① 读盘定位**

**提出者：** 用户（「继续开发项目」）

**背景：** 按流程中枢读盘：项目概况 → P1 → S6（`plannedDev`）。S6 概况「当前进度」：R8 E `有未通过项`，用户已于 2026-10-12 逐项裁决，`本Session修` 5 项已修；`出方案修` 各项交 C（R9），要求在新 Session 开工。本 Session 就是那个新 Session，判为情形 A。按出口路由「E · 有未通过项 → `出方案修` → 步骤 C」驱动。

**结论：** 本 Round 为 **R9，跑 C 步（build，开发方案）**。依据是 R8 E 确认报告，R6 方案仍有效、R9 只补和改。`打tag=否`，预设执行者 Claude。

**② 称呼词：先查数据，再给候选**

**提出者：** Claude

**背景：** 官方把 `Mrs`／`Ms`／`Miss`／`Madam` 都译成「女士」，`Master` 译成「主表」。称呼下拉里有四个「女士」，分不开。`Salutation` 是 `translated_doctype`（`frappe/contacts/doctype/salutation/salutation.json:60`），Link 显示时会对记录名调 `__()`。装站时 `update_salutations()`（`frappe/desk/page/setup_wizard/install_fixtures.py:41-55`）按 `_()` 的**译文**建记录，记录名唯一，`ignore_if_duplicate=True`。所以中文装站时，四个「女士」只会建出一条记录。

**实查**（`Spike/P1S6R9-C/salut.py`，经 `bench execute` 只读）：

| 站点 | `tabSalutation` 记录 | 业务数据引用 |
|---|---|---|
| 演示站 `erx.localhost` | **0 条** | Contact、Lead、Employee、CRM Lead 的 `salutation` 全为空 |
| 测试站 `test.localhost` | 9 条，记录名都是英文（`Mr`、`Ms`、`Mrs`、`Madam`、`Miss`、`Master`、`Dr`、`Mx`、`Prof`） | 全为空 |

两站都没有引用称呼的业务数据，所以改 csv 不涉及数据迁移。测试站记录名是英文，Link 显示走 `__()`，改 csv 后即可见效。

**占用核查**（`Spike/P1S6R4-occupancy.py`，读合并字典）：「太太」「小姐」「夫人」「少爷」「小先生」都未被占用；「女士」被 `Madam`、`Miss`、`Mrs`、`Ms` 占用，「先生」被 `Mr` 占用。五个源词在 `frappe/locale/main.pot` 中都只有 `install_fixtures.py` 一处出处。

**选项：**

| 选项 | 描述 | 优点 | 缺点 |
|---|---|---|---|
| A（推荐） | Mrs 太太、Miss 小姐、Madam 夫人、Master 少爷；Mr 先生、Ms 女士不变 | 六个称呼互不重名 | 「太太」「少爷」偏口语、旧式 |
| B | Mrs 夫人、Madam 太太，其余同 A | 「夫人」对已婚女性更书面 | 「太太」与 Madam 原义不太贴 |
| C | 同 A，但 Master 用「小先生」 | 比「少爷」中性 | 现代中文少见 |

**用户回答：** 第一次选「Mrs 夫人，其它同推荐项」。Claude 指出这样 `Mrs` 与 `Madam` 都成了「夫人」，又会重名，并请用户三选一：Madam 改「太太」（等同 B）、两个都用「夫人」、Madam 保留「女士」。用户第二次答：「还是用回上一条的推荐项吧，Mrs 不改夫人了」，即**取 A**。

**结论：** **DEC-039**：`Mrs`→太太、`Miss`→小姐、`Madam`→夫人、`Master`→少爷，写进 `frappe_china/translations/zh.csv`（无 context 行），进 `NAMED_TERMS`。四条都覆盖官方，进 `OVERRIDES`，依据为 DEC-039。`Mr`、`Ms` 保留官方。

**推翻过程：** 「Mrs 夫人」由用户提出，又被用户收回。原因是它与推荐项里的 Madam「夫人」重名，与本议题要解决的「称呼分不开」相抵。

**③ Raven 个人状态 `Available`**

**提出者：** Claude

**背景：** R7 DJ-001 为演示面工作站把无 context 的 `Available` 定成「工位可用」。它波及 Raven 个人状态（`raven/apps/web/src/components/features/settings/panels/Profile.tsx:28`、`hooks/useSetAvailability.ts:9`，都是模块级常量 `_("Available")`，不带 context）。R8 用户裁决只修 Raven 这一处。Raven 对「手动设为 Available 但不在线」画空心圈，与真正在线的实心绿点区分（`components/features/message/UserAvatar.tsx:156-157`）。

**选项：**

| 选项 | 描述 | 优点 | 缺点 |
|---|---|---|---|
| A（推荐） | 有空 | 表达「手动设为可联系」，不与 Raven 的在线点混淆 | — |
| B | 在线 | 最常见的即时通讯用词 | 与 Raven 的「实际在线」语义重叠 |
| C | 空闲 | 中性 | 略像描述设备而非人 |

**用户回答：** 选「有空」。

**结论：** **DEC-040**：Raven 个人状态 `Available` 显示「有空」。落法：csv 加 context 行 `Available,有空,Raven User`（`Raven User.availability_status` 的 Select 在 Desk 里经 `desk_patches.js` 的 Select formatter 按父 DocType 取 context，同时生效）；Raven 独立前端由 `frappe_china` 注入脚本把 `Available` 限定改取该 context 行（方案 TS-031）。无 context 的 `Available`→工位可用 不变。

**④ 清单外其余四条的落法**

**提出者：** Claude

**背景：** R8 报告「清单外发现」五条，用户裁决「其它按建议来」，称呼一条见 ②。另外四条按 E 建议落。覆盖清单的依据必须匹配 `_BASIS_FORM`，所以要一个决策号承接。本步核实了几项事实：`JAN` 只在 `item_barcode.json` 的 `barcode_type` 选项中出现（`erpnext/locale/main.pot`），官方译「01」；`UOM Conversion Factor` 的 `From` 已有 context 行「原单位」，`To` 无 context 行，显示官方「至」；`Manufacturing Setup` 官方无译文，csv 现为批量档的「生产设置」，与 `Manufacturing Settings` 的官方译名「生产设置」撞名；同族的 `Stock Setup`、`Selling Setup`、`Buying Setup` 在 csv 中都是「…初始化」；`CN Tax` 不在任何 po 中，`_app_source_strings()` 不读 Workspace Sidebar json，所以测试抓不到它。

**结论：** **DEC-041**：`JAN`→JAN（原样，覆盖官方「01」，进 `OVERRIDES` 与 `UNTRANSLATED`）；`To:UOM Conversion Factor`→目标单位；`Manufacturing Setup`→生产初始化；`CN Tax`→中国财税，同时让 `_app_source_strings()` 读 Workspace Sidebar 与 Desktop Icon 的 json。四条都进 `NAMED_TERMS`。

---

## 决策汇总表

| 编号 | 决策内容 | 最终选择 | 选择理由 | 提出者 | 失效条件 |
|---|---|---|---|---|---|
| DEC-039 | 称呼词定词 | `Mrs` 太太、`Miss` 小姐、`Madam` 夫人、`Master` 少爷；`Mr`、`Ms` 保留官方 | 六个称呼互不重名；用户先选「Mrs 夫人」后收回，因其与 Madam 重名 | Claude 给候选，用户定 | 客户要求改称呼用词时；或装站方式改为不经 `update_salutations()` 时 |
| DEC-040 | Raven 个人状态 `Available` | 有空（context 行 `Available:Raven User`，Raven 前端限定改取） | 不与 Raven 的实际在线状态混淆 | Claude 给候选，用户定 | Raven 改为带 context 调用、或改了状态取值时 |
| DEC-041 | 清单外四条的定词 | `JAN` 原样；`To:UOM Conversion Factor` 目标单位；`Manufacturing Setup` 生产初始化；`CN Tax` 中国财税（取法补 Workspace Sidebar／Desktop Icon json） | R8 E 建议，用户裁决「其它按建议来」 | E 提出，用户按建议裁决 | 上游改了这些键的官方译文时 |

## 被否决方案汇总表

| 编号 | 方案 | 否决理由 |
|---|---|---|
| NV-036 | `Mrs` 夫人（`Madam` 仍为夫人） | 与 `Madam` 重名，下拉仍分不开（用户自行收回） |
| NV-037 | `Master` 小先生 | 现代中文少见 |
| NV-038 | Raven `Available` 译「在线」 | 与 Raven 的实际在线状态语义重叠 |

## 遗留问题

| 编号 | 事项 | 状态 | 触发条件 |
|---|---|---|---|
| LG-011 | 中文装站时 `update_salutations()` 会按新译文建 `Salutation` 记录：太太、小姐、夫人、少爷各一条；`Dr` 照 S6 DEC-003 会建出一条「借方」（S3 LG-119 的代价，未变） | 待确认 | 客户正式库装站前 |
