# P1-S5-R1 需求讨论（plannedDev A 步）

**讨论主题**：S5 演示链路五条需求收敛到可写需求文档——CR-013 CRM 接入＋销售漏斗／IM-005 HRMS 接入／IM-006 Insights 接入／EX-001 Raven（AI 演示）／CR-015 演示终端连通性
**日期**：2026-10-04
**参与者**：用户、Claude
**规划层级**：Stage 级
**依据**：[P1-S5-概况.md](../P1-S5-概况.md)「本 Stage 的输入」＋[路线文档.md](../../0-P1文档/路线文档.md) §四 S5（十条执行清单与边界）＋[需求图谱.md](../../0-P1文档/需求图谱.md) CR-013／CR-015／IM-005／IM-006／EX-001 五行与 §7.4＋[ADR-0003](../../0-P1文档/ADR-0003-app装载顺序自有app末位.md)／[ADR-0004](../../0-P1文档/ADR-0004-不使用override_doctype_class.md)／[ADR-0013](../../0-P1文档/ADR-0013-自有app按域分为frappe_china与frappe_debug.md)
**Spec**：[A-requirement-plannedDev-shape.md](../../../流程体系/workflows/plannedDev/A-requirement-plannedDev-shape.md)

**承接说明**：本轮是本 Stage 首轮，步号自第 1 步起。

**业务规则前置**（play-shape 纪律 2）：[../../../业务规则.md](../../../业务规则.md) v1 现有 BR-001…BR-007，全部是会计准则与增值税类。本 Stage 五条需求不直接触及它们；**唯一间接触点是 RW-01**——HRMS 若往科目体系里加科目，须不破坏 BR-001（执行小企业会计准则）所定的科目表。

---

## 演化过程

#### 第 1 步：S5 开工，先定四个 App 的来源与版本

**① 本 Stage 开工与 A 步启动**

**提出者：** 用户

**背景：** 用户说「继续开发项目，进入 S05」。按流程中枢第 0–2 步读盘：项目概况 → P1 需求摸底（进行中）→ P1 概况指「S5 演示链路（待起）」；S4 中国财税已于 2026-10-04 收口（末轮 R20 `Pai000`），其概况「下一步」字段同指 S5。**判为情形 B（要起新 Stage）**，Workflow 已由路线文档定为 `plannedDev`，进第 5 步。

**结论：** 起 **S5 演示链路**，绑 **`plannedDev`**（原子 Stage）。已做五件机械动作：

| # | 动作 | 结果 |
|---|---|---|
| 1 | 建 Stage 文件夹与 Round 文件夹 | `S05-演示链路/` ＋ `R01-需求讨论/` |
| 2 | 建 Stage 概况 | [../P1-S5-概况.md](../P1-S5-概况.md)（含路线文档 §四 S5 四条完成标志、四条 RW 风险、S4 移交的 DEC-113／LG-151／LG-139／RS-001、图谱四条 LG） |
| 3 | **打 tag**（A 步 `打tag=前`） | **`P1-S5-R1-start`**（本地，未推） |
| 4 | 开落档开关（讨论契约 §5） | `.claude/discussion/{session_id}.json` → 本文件，`turnStartMax` 置 0 |
| 5 | P1 概况级联指针 | 「当前 Stage」改为 S5 进行中 |

**A 步预设执行者是 Claude**（步骤表原值）。**D 步执行者按路线文档 §四 S5 偏离条改为 Claude。**

**② A 步议题安排**

**提出者：** Claude

**背景：** 五条需求各有独立的待定点，按讨论契约「一次一个问题、分节呈现」逐个定。

**结论：** 拟按以下次序分节讨论（次序按依赖：来源与版本是装任何 App 的前提，放首位；工作量重估依赖前面全部议题，放末位）：

| # | 议题 | 要定什么 |
|---|---|---|
| 1 | App 来源与版本 | fork 还是官方仓库、用哪个分支、怎么锁 |
| 2 | 装载顺序与 `frappe_china` 归位 | DEC-113 的验收口径；LG-151「重装无现成手段」在需求层的边界 |
| 3 | HRMS 与 S4 科目体系的交互 | RW-01 怎么验、出冲突时的退路 |
| 4 | CRM 销售漏斗 | 演示到什么程度、LG-085 |
| 5 | Raven AI 演示 | 用哪个模型、三问的具体问法与「答得出」的判据（RW-04／LG-090） |
| 6 | Insights | 装到什么程度算完成（RW-02） |
| 7 | 演示终端连通性 | 两条通路各自的验收口径（CR-015） |
| 8 | 工作量重估 | 回写路线文档（RW-09） |

**③ App 来源与版本**

**提出者：** Claude

**背景：** 读盘时查了四个上游仓库的远端分支（可复现：在 `Reference/` 下对各仓库跑 `git ls-remote --heads origin`；`main` 分支的依赖声明取 `https://raw.githubusercontent.com/{仓库}/main/pyproject.toml`）：

| App | 上游仓库 | 有 `version-16` 分支吗 | 发布分支声明的 frappe 范围 |
|---|---|---|---|
| HRMS | `frappe/hrms` | **有**（另有 `version-16-hotfix`／`version-16-polished`） | `version-16`：`>=16.0.0,<17.0.0`，另要求 erpnext `>=16.0.0,<17.0.0` |
| CRM | `frappe/crm` | **无**，只有 `main`／`develop` | `main`：`>=15.0.0,<17.0.0` |
| Insights | `frappe/insights` | **无**，只有 `main`／`develop` | `main`：`>=15.0.0` |
| Raven | `The-Commit-Company/Raven` | **无**，只有 `main`／`develop` | `main`：`>=15.0.0,<=17.0.0-dev` |

四者的发布分支都声明兼容 v16。另两条相关事实：

- `docker/scripts/setup.sh` 读 `apps.json` 时**缺省分支是 `version-16`**（第 136 行），故 CRM／Insights／Raven 三条必须显式写分支，否则 `bench get-app` 会失败。
- 本项目的 frappe／erpnext 走自有 fork（`PhilixKuro/{frappe,erpnext}`）。用户 GitHub 下目前**没有**这四个 App 的 fork（`git ls-remote` 四个都返回 `Repository not found`）。

**⚠ 讨论中发现：** S2 读码所依据的 `Reference/` 下四个克隆**全部停在 `develop`**（2026-09-22／23 的快照）。若实装用 `main`，此前的读码结论（Raven `handle_get_list` 末端是 `frappe.get_all`、Raven 无 `fixtures`、CRM 的 Deal 页按钮生成报价单、HRMS `doc_events` 挂 28 个 DocType 等）都须在实装版本上复核一次。HRMS 同理：读码看的是 `develop`（已进 v17），实装是 `version-16`。

**选项：**（来源）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| A | 四个都 fork 到 `PhilixKuro`，`apps.json` 指 fork 并锁 commit | 与 frappe／erpnext 现有模型一致；要改它们的源码时随时可改 | 多四个仓库要定期与上游同步；须用户在 GitHub 上建 fork；而 ADR-0013 已把「对官方 App 的修复」划给 `frappe_china`，改源码本就不是预期路径 |
| **B（推荐）** | **直接用官方仓库，`apps.json` 锁 commit；将来确须改它们的源码时再 fork** | 零新增仓库；锁 commit 已保证多机一致；符合 L5「禁止改上游源码，除非无路可走」 | `setup.sh` 第 4 段的 remote 归位会把这四个的 `origin` 指到官方仓库（它把非 frappe／erpnext 一律当自有 app），D 步须小改；上游若删掉被锁的 commit（极少见）则重建失败 |

**选项：**（分支）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **甲（推荐）** | **HRMS 用 `version-16`，其余三个用 `main`** | 都是发布分支；与 v16 的兼容声明明确 | 与 S2 读码用的 `develop` 不同，读码结论须复核 |
| 乙 | 四个都用 `develop` | 与 S2 读码版本一致 | `develop` 是开发线、不稳；HRMS 的 `develop` 已要求 `frappe>=17.0.0-dev`，**装不上本项目**（路线文档 §四 S5 第 1 条），故 HRMS 无论如何不能取乙 |

**推荐理由：** B＋甲。改官方 App 的源码在本项目里本就不是预期路径（修复归 `frappe_china`），fork 只带来同步负担；锁 commit 已能保证可重现。分支取发布线是装生产候选软件的常规做法，读码复核的成本远小于跑在开发线上的不稳定。

**用户回答：** 两问都取推荐项：来源取 B（官方仓库＋锁 commit），分支取甲（HRMS `version-16`，其余 `main`）。

**结论：** **DEC-001**、**DEC-002**（见决策汇总表）。连带两件事：

- `setup.sh` 第 4 段把 frappe／erpnext 之外的 app 一律当自有 app 处理 remote，D 步须让它认出这四个官方 App（`origin`／`upstream` 怎么配留 C 步定）。
- S2 基于 `develop` 的读码结论须在实装版本上复核，登 **LG-001**。

**④ 装载顺序与 `frappe_china` 归位**

**提出者：** Claude

**背景：** DEC-113（S4 移交）要求装完四个 App 后让 `frappe_china` 回到它们之后、并实测覆盖生效；LG-151 记的是「重装」没有现成手段（`install-app --force` 不改位置，`uninstall-app` 会删本 app 全部 DocType 表）。本轮读码查到三条事实（可复现路径附后）：

| # | 事实 | 出处 |
|---|---|---|
| 1 | **框架自带调序入口**：`update_installed_apps_order(new_order)` 只改 `installed_apps` 全局值的顺序，不装不卸；拒绝增删 app、强制 frappe 居首、写一条 Version 留痕；限 System Manager。界面入口在「Installed Applications」单例的调序对话框 | `frappe/core/doctype/installed_applications/installed_applications.py:108-136`、`.js:25-45` |
| 2 | **新装 app 只会追加到末尾** | `frappe/installer.py:378-383` |
| 3 | **四个 App 没有一个覆盖 `frappe_china` 用的那三个 whitelisted 方法**（四个的 `override_whitelisted_methods` 全是注释）。`override_doctype_class`：HRMS 覆盖 `Employee`／`Timesheet`／`Payment Entry`／`Project`，CRM 覆盖 `Contact`／`Email Template`，`frappe_china` 一个都不用 | 四个 `Reference/{app}/{app}/hooks.py`（`develop` 快照） |

⇒ **LG-151 的前提变了**：不必重装，调序就是现成手段，且不碰数据。**而「覆盖生效」在 S5 当下其实不受顺序影响**（事实 3：没人抢那三个覆盖位）。顺序真正起作用的地方有两处：

- **译名**：多个 app 的 `zh` 译文按 `installed_apps` 顺序合并、后者覆盖前者（`frappe/translate.py:179` 起的循环）。S6 往 `frappe_china` 的 csv 里写的译名，若同一源词四个 App 也有译文而 `frappe_china` 不在末位，**会被静默盖掉**。
- **`doc_events` 的执行先后**：HRMS 在 `Company` 上挂了 `validate` 一个、`on_update` 三个（`make_company_fixtures`／`set_default_hr_accounts`／`set_expense_claim_type_accounts`），`frappe_china` 在 `Company` 上挂 `before_insert`／`on_update`。两者都在 `on_update`，先后由顺序定——这正是 RW-01 的交互面，留议题 3 讨论。

**⚠ 讨论中发现：** 完成标志②写「重装后实测覆盖生效（`after_migrate` 自检通过）」，但 **`frappe_china` 目前没有 `after_migrate` 钩子**（`hooks.py` 零命中）。现成的是 `accounting/selfcheck.py` 里的 `check_all_cn_companies()`，接到 `after_migrate` 是 S8G-S1 的 IM-007 的事（路线文档 §七第 3 行）。故完成标志②里的「`after_migrate` 自检」在 S5 无物可验。

**选项：**（归位手段）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A（推荐）** | **装完四个 App 后调 `update_installed_apps_order` 把 `frappe_china` 调到末位**（D 步把它写进 `setup.sh`，新机器重建时自动做） | 不卸载、不碰数据；框架正式入口、带留痕；可脚本化 | 调序后 hooks 缓存是否立即失效未实测（hooks 有 site 级缓存，`frappe/__init__.py:988-1006`） |
| B | 卸载 `frappe_china` 再装 | 不依赖调序入口 | **删本 app 全部 DocType 表**（结转凭证、现金流底稿、银行流水等），演示站须重建 S4 的数据 |
| C | 不调序，只验三个覆盖位生效 | 零动作 | S6 的译名 csv 会被四个 App 的同源词译文盖掉；问题推迟到 S6 才暴露 |

**选项：**（完成标志②的验收口径）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **甲（推荐）** | **改成三条可验项**：① `installed_apps` 末位是 `frappe_china`；② 三个 whitelisted 覆盖解析到 `frappe_china`；③ 一条与四个 App 撞源词的测试译名实测由 `frappe_china` 胜出。`check_all_cn_companies()` 直接调一次、全过。`after_migrate` 接线仍归 S8G-S1 | 每条都可判真假；③ 正好验掉 S6 最怕的那种失效 | 改了路线文档的完成标志措辞（B 步回写） |
| 乙 | 本 Stage 顺手把 `after_migrate` 接上自检 | 与原文字面一致 | 把 S8G-S1 的 IM-007 提前做了一半；IM-007 要的两条断言（派发层归属＋建账结果）本 Stage 只能做后一条 |

**推荐理由：** A＋甲。A 是唯一既不丢数据、又能在新机器上自动重现的手段。甲把「覆盖生效」拆成顺序真正影响的那几处，各给一个可判真假的验法；`after_migrate` 留在原归属，不拆 IM-007。

**用户回答：** 取 A＋甲（回复在第 2 步那一轮到达）。

**结论：** **DEC-003**、**DEC-004**（见决策汇总表）。LG-151「重装无现成手段」由调序入口消解，B 步据此更正。调序后 hooks 缓存是否立即失效未实测，登 **LG-002**。

---

#### 第 2 步：归位方案定为 A＋甲；HRMS 与 S4 科目体系的交互读码查清

**① 归位手段与完成标志②的验收口径**

**提出者：** 用户

**背景：** 回答第 1 步议题 ④。

**用户回答：** 「A＋甲」。

**结论：** 同第 1 步议题 ④ 结论：DEC-003、DEC-004。

**⚠ 收尾记录验证时更正**（原文：「Claude 上一轮在回复末尾又把议题 ④ 当作未答问了一遍，那是误发；本轮已向用户说明」）：**那次「误发」并不存在**。对照原始对话的时间戳，Claude 呈现议题 ④ 的那条消息（10:28:23）早于用户回复「A＋甲」（10:30:50），是议题 ④ 的**首次**呈现，不是重问。Claude 误判后在本轮回复里向用户声称「上一轮误发」，那句说法本身失实，已在 A 步收尾时向用户更正。

**② HRMS 与 S4 科目体系的交互（RW-01／LG-101／RS-001）**

**提出者：** Claude

**背景：** 路线文档 RW-01 的原判断是「`Company.on_update` 会跑 `set_default_hr_accounts`，可能往已定型的科目体系里新增 HR 科目」，LG-101 至今零验证。本轮读了 HRMS **`version-16`** 分支（即 DEC-002 定的实装分支，2026-10-04 的分支头）的 `hrms/overrides/company.py`，对照 `frappe_china/accounting/company.py` 与演示站 `HDTH` 的现有科目。

可复现路径：`https://raw.githubusercontent.com/frappe/hrms/version-16/hrms/overrides/company.py`（238 行）、同分支 `hrms/hooks.py:173-180`、`hrms/setup.py:14-26` 与 `:338-342`；`frappe_china/accounting/company.py:34-65`；演示站查询 `select name,account_number,is_group,root_type,lft from tabAccount where company="华东弹簧有限公司" and root_type="Expense" and is_group=1 order by lft`。

HRMS 在 `Company` 上挂的四个钩子，逐个查了对科目表的实际作用：

| 钩子 | 事件 | 对科目表的作用 |
|---|---|---|
| `validate_default_accounts` | validate | 只校验「应付工资」默认科目的归属与币种；该字段为空时什么都不做。**无影响** |
| `make_company_fixtures` | on_update | 只在国家变更时跑；HRMS 只有 `india`／`united_arab_emirates` 两个地区包，中国走 `ImportError` 跳过；另建默认工资组成（Salary Component 记录，不是科目）。**不动科目** |
| `set_default_hr_accounts` | on_update | **不建科目**，只按名找「Payroll Payable」「Employee Advances」两个明细科目并写进公司默认字段。中式科目表里是「应付职工薪酬」，按译名「应付职工薪资」找不到 ⇒ 写入空值。**无实害** |
| **`set_expense_claim_type_accounts`** | on_update | **⚠ 会建一个科目。** 对每个报销类型（HRMS 装时建 5 个：Calls／Food／Medical／Others／Travel），若该公司未配默认科目：先按名找「Expense Claims」明细，找不到就找「Indirect Expenses」组，再找不到就取**第一个 Expense 类组科目**（按 `lft`）作父级，**新建一个无科目号的「Expense Claims」科目**。在 `HDTH` 上这个父级会是 **`540 - 费用类`**（`lft` 363，Expense 类最顶层的组） |

两个 on_update 钩子在入口都有 `if frappe.local.flags.ignore_chart_of_accounts: return`。而 `frappe_china` 的 `before_insert` 对中式公司把这个 flag 置 1、在自己的 `on_update` 的 `finally` 里复位。**所以结果取决于两个 app 的 `on_update` 谁先跑**：

| 情形 | HRMS 的两个钩子 | 结果 |
|---|---|---|
| **新建中式公司，`frappe_china` 在末位**（DEC-003 之后） | 先于 `frappe_china` 跑，flag 仍为 1 ⇒ 跳过 | 不建科目 |
| 新建中式公司，`frappe_china` 在 HRMS 之前（不调序时） | `frappe_china` 已建完科目表并复位 flag ⇒ 照跑 | **建出「Expense Claims」挂在 540 下** |
| **已有公司（如 `HDTH`）以后任何一次保存** | flag 为 0 ⇒ 照跑 | **建出「Expense Claims」挂在 540 下**，并把 5 个报销类型的默认科目都指向它 |

⇒ **RW-01 的实际形态比原判断窄而具体**：不是「新增一批 HR 科目」，而是**在下一次保存公司时新增一个科目**，位置在费用类最顶层、无科目号，不符合小企业会计准则的科目设置（报销按性质应进 `管理费用`／`销售费用` 下的明细，如 `管理费用_差旅费`）。**DEC-003 的调序同时保住了「新建公司」这条路**（S7 的数据生成器要反复建公司，这点对它要紧）。

**⚠ 讨论中发现：**

1. **建出的科目名随会话语言变**：代码用 `_("Expense Claims")`，`zh` 会话下是「费用报销记录」，后台任务或控制台（默认 `en`）下是「Expense Claims」。找科目也按译名找，故在两种语言下各保存一次公司，**可能建出中英两个重复科目**（读码推断，未实测）。
2. **S4 的漏科目检查预计会报它**（无科目号、不在报表映射里），未实测。
3. **`Payment Entry` 被 HRMS 的 `EmployeePaymentEntry` 整类覆盖**（`override_doctype_class`），而 S4 的收款、银行对账都经过它。这一处读码看不出会不会坏，**只能靠装完后重跑 S4 的 160 条测试来验**。

**选项：**（「Expense Claims」那个科目怎么处理）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **甲（推荐）** | **`frappe_china` 为中式公司预先配好 5 个报销类型的默认科目**，映射到 `管理费用` 下的明细（映射表由 B 步列出、标「待领域专家确认」）。HRMS 见到已配就跳过（`company.py` 里那句 `if frappe.db.exists("Expense Claim Account", ...): continue`） | 科目表保持准则原样；报销进对的科目；新建公司与以后保存公司都不再触发 | 要定一张 5 行的映射表（用户不懂财务，须送专家确认）；以后新增报销类型时仍会触发一次 |
| 乙 | 不处理，接受 HRMS 建出的那个科目，记为已知限制 | 零开发 | 科目表多一个不合准则位置的科目；漏科目检查会报；可能中英各建一个 |
| 丙 | 本 Stage 只验证不处理，规定演示前不保存 `HDTH` 公司；登延迟需求，IM-016 计件工资开工时再处理 | 本 Stage 零开发 | 很脆：任何人在公司设置里点一次保存就触发；而且 HRMS 在演示站上是真装的 |

**本议题另提三条验收项**（无对立方案，随议题一并确认）：

- **先在 `test.localhost` 装四个 App、跑完 S4 全量测试，再装演示站**；装演示站前先备份。这是 RW-01 缓解措施「先在一次性测试公司上验」的具体化。
- **装完后 S4 的 160 条测试全过**（验第 3 条发现的 `Payment Entry` 覆盖）。
- **`HDTH` 保存一次公司后，科目数仍是 266，自检的多余科目为空。**

**推荐理由：** 甲。HRMS 是真装在演示站上的，乙、丙都会让科目表在某次普通操作后变得不合准则，而 S4 花了 20 轮才把这套科目做对。甲的代价只是一张 5 行的映射表。

**用户回答：** 取甲（回复在第 3 步那一轮到达）。

**结论：** **DEC-005**、**DEC-006**（见第 3 步与决策汇总表）。

---

#### 第 3 步：HRMS 科目处理定为甲；CRM 衔接链路读码查清

**① HRMS 报销类型自建科目的处理**

**提出者：** 用户

**背景：** 回答第 2 步议题 ②。

**用户回答：** 「甲」。

**结论：** **DEC-005**（`frappe_china` 为中式公司预配 5 个报销类型的默认科目，映射到 `管理费用` 下的明细，映射表由 B 步列出并标「待领域专家确认」）。Claude 补了一条约束一并记入：**`frappe_china` 不得因此依赖 HRMS**——客户正式库装 `frappe_china`，但未必装 HRMS，故只在 `Expense Claim Type` 这个 DocType 存在时才配。随议题提出的三条验收项记为 **DEC-006**。

**② CRM 销售漏斗：演示到什么程度、客户何时建出（CR-013／LG-085）**

**提出者：** Claude

**背景：** 本轮读了 CRM **`main`** 分支（DEC-002 定的实装分支，分支头 `deedce73`，2026-09-30，版本 1.86.0）与本 bench 的 erpnext `version-16`。可复现路径：在 `Reference/frappe-crm` 下 `git fetch origin main` 后 `git show FETCH_HEAD:{路径}`，读了 `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.{py,json}`、`crm/public/js/erpnext_quotation_prefill.js`、`crm/hooks.py:237-290`、`crm/install.py:88-132`、`crm/api/dashboard.py`；erpnext 侧 `selling/doctype/quotation/quotation.py:236-247`、`:392-420`、`:583-614`。

同站部署（CRM 与 ERPNext 在同一站点）下，整条链路是这样走的：

| 环节 | 怎么做 | 出处 |
|---|---|---|
| Lead → Deal | CRM 界面里把线索转成商机（CRM 自带，不涉及 ERPNext） | CRM 自带 |
| 漏斗七档 | Qualification 10% → Demo/Making 25% → Proposal/Quotation 50% → Negotiation 70% → Ready to Close 90% → Won 100%／Lost 0% | `crm/install.py:88-132` |
| 漏斗看板 | CRM 自带看板：**按概率加权的预测收入**（金额 × 概率）、各档转化率、按阶段分布、输单原因 | `crm/api/dashboard.py:657-736` 等 |
| Deal → Quotation | Deal 页的「Create Quotation」按钮（启用集成时 CRM 自动装一段表单脚本）在新标签页打开 ERPNext 的新报价单，预填公司、联系人、地址；**明细行按 Deal 的产品预填**，前提是该 CRM 产品已映射到 ERPNext 物料（`erpnext_item_code`，靠设置里的产品同步） | `erpnext_crm_settings.py:180-194`、`:459-493`、`:531-545`；`erpnext_quotation_prefill.js` |
| 报价对象 | 已有对应客户则报给 `Customer`；**否则直接报给 `CRM Deal`**（v16 新增的报价对象类型，客户名取 Deal 的组织名） | `erpnext_crm_settings.py:469`；`quotation.py:246-247` |
| Quotation → Sales Order | ERPNext 标准的「创建 → 销售订单」按钮 | `quotation.py:377` |
| 客户何时建出 | 两种机制，**都不用人工建客户**：(a) 默认——保存销售订单时，CRM 挂在 `Sales Order.before_validate` 上的钩子发现没有客户，就从 Deal 建一个；(b) 可选——设置里勾「状态变更时建客户」并指定一个状态（如 Won），Deal 进入该状态时就建 | `crm/hooks.py:276-280`；`erpnext_crm_settings.py:594-651`；`.json` 的 `create_customer_on_status_change`／`deal_status` |

⇒ **LG-085「`Quotation → Sales Order` 是否需人工介入」读码已有答案**：要点一次 ERPNext 的标准按钮，客户由 CRM 自动建出，不需要手工补任何东西。**须由完成标志①的实点来确认**（读码不替代实测）。

**⚠ 讨论中发现：**

1. **CRM 是一个独立的前端**（`/crm`，Vue 写的单页应用），不在 ERPNext 的桌面界面（`/app`）里。演示时要在两个界面之间切：漏斗在 `/crm`，报价单以后都在 `/app`。这对两处有影响：S6 的译名要覆盖两套界面；S7 的演示操控要能驱动两套界面——ADR-0013 已把 `frappe_debug` 的驱动层分为 `drivers/{desk,spa}`，与此一致。
2. **Deal 明细预填依赖产品同步**：CRM 产品要先映射到 ERPNext 物料。演示用的弹簧物料由 S7 建，所以 S5 实点链路时用一个临时测试物料即可，正式数据的同步留给 S7。
3. **CRM 在 `Sales Order` 上挂了 `before_validate`**（L3 累加）。S7 的数据生成器若从报价单批量生成销售订单，会自动走这个建客户的钩子，这对 S7 是有利的。
4. **由 Deal 建出的客户取 `default_currency = deal.currency`**。Deal 的币种默认值本轮没查，若不是 CNY 会一路带进报价单和销售订单。登 **LG-004**。

**选项：**（问题 1：演示从哪一环开始）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A（推荐）** | **从 Lead 开始**：Lead → Deal → 推进几档 → 报价 → 接单，**加漏斗看板**（加权预测收入、各档转化） | 与需求图谱 CR-013 写的起点一致（`Lead → Deal → 报价 → …`）；看板正是「客户自己是销售、看得懂漏斗」的价值所在 | 比 B 多验两样东西（线索转商机、看板），完成标志①要补措辞 |
| B | 从 Deal 开始：Deal → 报价 → 接单 | 正好是完成标志①的字面范围，最省 | 漏斗看板是 CRM 对客户最有说服力的部分，不验它就到 S7 才第一次见；Lead 那一段也没人验过 |

**选项：**（问题 2：客户何时建出）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **甲（推荐）** | **用默认机制**：报价单报给 `CRM Deal`，下销售订单时自动建客户 | 零配置；与真实业务一致（先报价、后成交）；少一处要讲给客户听的设置 | 报价单上的对象类型显示为「商机」而不是「客户」，演示时要解释一句 |
| 乙 | 勾「状态变更时建客户」，状态取 Won | 赢单那一刻客户就有了，讲起来顺 | 先报价后赢单时，报价单仍是报给 `CRM Deal`，甲的那句解释还是省不掉；多一处配置要维护 |

**推荐理由：** A＋甲。A 让 S5 把 CRM 在演示里真正要露的部分都验一遍，不留到 S7；甲最少配置，乙并不能省掉甲的那点代价。

**用户回答：** 问题 1 取 A，问题 2 取甲（回复在第 4 步那一轮到达）。

**结论：** **DEC-007**、**DEC-008**（见第 4 步与决策汇总表）。

---

#### 第 4 步：CRM 定为 A＋甲；Raven 的工具链在实装版本上读码查清

**① CRM 两问**

**提出者：** 用户

**背景：** 回答第 3 步议题 ②。

**用户回答：** 「问题 1、A。问题 2、甲。」

**结论：** **DEC-007**（演示从 Lead 开始，含漏斗看板；完成标志①由 B 步补措辞）、**DEC-008**（用默认机制，下销售订单时自动建客户）。

**② Raven AI 演示：bot 挂哪些工具、三问怎么测（EX-001／RW-04／LG-090）**

**提出者：** Claude

**背景：** 本轮读了 Raven **`main`**（DEC-002 定的实装分支，分支头 `e890308e`，2026-09-25）。可复现路径：在 `Reference/raven` 下 `git fetch origin main` 后 `git show FETCH_HEAD:raven/ai/{sdk_tools,functions,agents_integration,handler}.py`；`git grep -n "def handle_create_document\|def handle_delete_document" FETCH_HEAD -- raven`（零命中）；`raven/raven_ai/doctype/raven_ai_function/raven_ai_function.json:51`（18 种类型）。

| # | 事实 | 出处 |
|---|---|---|
| 1 | bot 的工具由 `create_raven_tools` 按挂在 bot 上的 `Raven AI Function` 记录生成。**18 种类型里只映射了 6 种**：`Custom Function`（指向任意函数路径）、`Get List`、`Get Document`、`Update Document`、`Create Document`、`Delete Document`；其余 12 种（含 `Get Report Result`、`Get Value`、`Submit Document`）一律 `continue`，**静默跳过** | `sdk_tools.py:12-110` |
| 2 | **`handle_create_document`、`handle_delete_document` 在 `main` 上根本不存在**，函数查找返回 `None`，工具不生成，只在 Error Log 留一条 ⇒ **「五个内置 handler」实际生效的只有三个**：`Get List`／`Get Document`／`Update Document` | `sdk_tools.py:51-53`、`:219-270`；上述 `git grep` |
| 3 | `handle_get_list` 在 `main` 上与 S2 读的一致：末端 `frappe.get_all`（**绕过权限**，LG-091 仍成立）、字段只能取本表的、filter 是字典、`limit` 默认 20（AI 可传更大）、可排序；**无聚合、无 group by、无 join** ⇒ LG-090 的前提在实装版本上仍成立 | `sdk_tools.py:486-600` |
| 4 | **`Get Report Result` 在新的 Agents 路径不生效**，只在老的 Assistants 路径里有（`handler.py:306`）。但 `Custom Function` 可指向任意路径，指向 `raven.ai.functions.get_report_result`（跑任意报表、返回列与行）**理论上就能让 AI 调 ERPNext 现成报表**——那些报表本身已做好聚合（采购分析、物料采购历史、供应商报价比较、毛利分析、BOM 浏览器等）。未实测 | `sdk_tools.py:55-56`；`functions.py:256-283` |
| 5 | 走 LiteLLM（`Local LLM`＋`OpenAI Compatible`）时 `use_responses=False`，S2 结论在 `main` 上仍成立；**代码解释器只给 OpenAI 直连**，走 LiteLLM 时 AI 不能跑代码算数，算术只能靠模型自己 | `agents_integration.py:55-74`、`:151` 起 |

（LiteLLM 容器在跑，端口 7999。其配置文件可能含密钥，本轮未读。）

**⚠ 讨论中发现：**

1. **完成标志③「五个内置 handler 的记录已建并挂 bot」在 `main` 上做不到**——两个 handler 不存在。登 **LG-005**，由 B 步改口径。
2. **报表通道要经 `Custom Function` 绕**，可不可行、权限是否照常校验都没实测。登 **LG-006**。
3. **S5 手上没有可供三问的数据**：演示站已由 S4 恢复到空账基准点（只剩 `HDTH`），正式数据要到 S7 才建。而 RW-04 要求「先测三问再进 S7」，S7 的数据怎么编又要等这个结论 ⇒ **S5 必须自己备一份测试数据**。

**选项：**（问题 1：演示 bot 挂哪些工具）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A（推荐）** | **只读**：`Get List`＋`Get Document` 按演示要用的 DocType 各建记录；另加一个 `Custom Function` 指向 `get_report_result` 作报表通道。**不建** `Update`／`Create`／`Delete` | 后两问可先试现成报表，可能不必自写查询；AI 在现场改不了数据，符合可信度优先 | 报表通道未实测（LG-006）；完成标志③要改口径 |
| B | 按原完成标志建五类 | 字面符合原文 | 两类根本不生效；`Update Document` 让 AI 在演示现场能改单据 |
| C | 只建 `Get List`＋`Get Document`，不接报表 | 最简单 | 后两问大概率答不出，直接跳到自写 `Custom Function`，可能多花本可省的功夫 |

**选项：**（问题 2：S5 怎么测三问）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **甲（推荐）** | **在 `test.localhost` 造一份最小数据**（每问几条到十几条），**每问事先算好标准答案**；每问跑 3 次，3 次都答对、且说得出依据（引了哪些单据或报表）才算「答得出」；测完清掉 | 「答得出」可判真假；测试数据的结构正好给 S7 编数据当样板 | 要先定每问的口径（下一轮讨论）；最小数据量下答得出，不保证 100 条时也答得出 |
| 乙 | 等 S7 的 100 条数据造好再测 | 数据最真实 | 违反 RW-04「先测再进 S7」，且 S7 编数据要等这个结论，成了循环依赖 |
| 丙 | 直接在演示站造数据测 | 环境与演示一致 | 污染 S4 留下的空账基准点，S7 造数前还得再恢复一次 |

**推荐理由：** A＋甲。A 用现成报表做第一道尝试，成本最低，也不给 AI 写权限；甲让「答得出」变成能判真假的事，且不碰演示站。三问各自的口径（比如「货美」用哪项数据衡量、「符合单子要求」指什么）是判断型问题，**下一轮单独讨论**。

另向用户提了一个事实问题：**LiteLLM 里打算给 Raven 用哪个模型**（决定测试在什么条件下做，结论只对该模型成立）。

**用户回答：** 问题 1 取 A，问题 2 取甲；模型由用户自己在 LiteLLM 里配，S5 只要建立好 Raven 到 LiteLLM 的连接（回复在第 5 步那一轮到达）。

**结论：** **DEC-009**、**DEC-010**、**DEC-011**（见第 5 步与决策汇总表）。

---

#### 第 5 步：Raven 定为 A＋甲，模型归用户；进入三问的口径

**① Raven 两问与模型**

**提出者：** 用户

**背景：** 回答第 4 步议题 ②。

**⚠ 收尾记录验证时更正**（原文：「用户的回复到达后，Claude 先发出的一条消息仍把议题 ② 当作未答又问了一遍（与第 2 步那次同型的误发），本轮已向用户说明」）：**同第 2 步，那次「误发」不存在**。呈现议题 ② 的消息（12:32:49）早于用户回复（12:38:06），是首次呈现。Claude 在本轮回复开头向用户说「上一条消息重问了、是误发」，那句说法失实，已在 A 步收尾时向用户更正。

**用户回答：** 「问题 1、A。问题 2、甲。」模型由用户自己在 LiteLLM 里配，S5 只要建立好跟 LiteLLM 的连接。

**结论：**

- **DEC-009**：演示 bot 只读——`Get List`＋`Get Document` 按演示要用的 DocType 各建记录，另加一个 `Custom Function` 指向 `raven.ai.functions.get_report_result` 作报表通道；不建 `Update`／`Create`／`Delete`。完成标志③由 B 步改口径（LG-005）。
- **DEC-010**：三问在 `test.localhost` 用最小数据测，每问事先算好标准答案，每问跑 3 次，3 次都答对且说得出依据才算「答得出」。（「测完清掉」与「依据＝引了哪些单据或报表」是 Claude 写记录时补的细化，用户选甲时看到的选项里没有这两处。）
- **DEC-011**：**模型选择归用户，不进本 Stage 范围**。S5 负责的是 Raven → LiteLLM 这一段：Raven Settings 里启用本地模型、提供方选 `OpenAI Compatible`、填 LiteLLM 的地址与密钥，bot 的 `model` 字段填用户在 LiteLLM 里配的模型别名。Claude 补两条随之而来的约束：① **三问的结论只对测试时那个别名成立**，测试报告须记下别名；用户以后换模型，三问须重测（写进失效条件）。② 密钥由用户提供、存 Raven Settings 的密码字段，**不进任何文档与仓库**。

**⚠ 讨论中发现：** Raven 跑在 frappe 容器里，**从容器里访问宿主上的 LiteLLM（宿主端口 7999）要用 `host.docker.internal`，不能用 `127.0.0.1`**——这是本项目已踩过的坑（记忆「Windows Docker 环境坑」第 2 条：容器里的 `127.0.0.1` 指容器自己）。具体 URL 留 C 步定，此处只记约束。

**② 三问的口径（EX-001 / RW-04）**

**提出者：** Claude

**背景：** DEC-010 要求每问「事先算好标准答案」，前提是每问先有一个可计算的口径。三问原话来自 S2-R2 第 25 步（用户提出）：**分析销售漏斗找单子／哪个供应商货美价廉／哪个 BOM 在符合单子要求下利润最大化**。三者都有不止一种读法，属判断型问题。本轮查了各问可用的字段（读码：CRM `main` 的 `crm_deal.json`；erpnext 的 `quality_inspection.json`、`bom.json`。**收尾补核**：采购入库明细的 `rejected_qty`／`received_qty` 本轮当时未读码，收尾时已在 `erpnext/stock/doctype/purchase_receipt_item/purchase_receipt_item.json` 确认两字段存在；`expected_deal_value` 的计算式未读，「＝金额 × 概率」是按字段名推断，概率可能以百分数存、须除以 100，C 步核一次）：

| 问 | 可用数据 | 一张表能答吗 |
|---|---|---|
| 漏斗找单子 | `CRM Deal`：`deal_value`／`probability`／`expected_deal_value`／`expected_closure_date`／`status`／`next_step`／`lost_reason` | **能**（`Get List` 按加权金额排序即可） |
| 货美价廉 | 价：采购订单或采购入库明细的单价；美：采购入库明细的拒收数量 `rejected_qty`／`received_qty`，或来料检验单 `Quality Inspection` 的合格与否 | 不能，要按供应商汇总 ⇒ 靠报表通道或自写查询 |
| BOM 利润最大化 | `BOM`：`item`／`quantity`／`total_cost`／`is_active`；订单单价在销售订单明细 | 部分能（同物料几个 BOM 的成本可单表比，利润要再跨到订单） |

**选项：**（问 1：「找单子」指什么）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A（推荐）** | **「该优先跟进哪几单」**：进行中的商机按金额 × 概率排序取前几名，附预计成交日 | 单表可答，最可能答对；是销售日常最常问的那句 | 只看静态数字，不看「卡住没动」 |
| B | A 再加「哪些单卡住了」：超过一定天数没推进阶段的商机 | 更像真的销售分析 | 「推进阶段」要看状态变更历史，单表答不了；多一个要定的阈值 |

**选项：**（问 2：「货美」用什么衡量，「价廉」比什么）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A（推荐）** | **价＝同一物料各供应商的采购入库平均单价；美＝收货拒收率**（拒收数量 ÷ 收货数量），两项都在采购入库明细里 | 一张明细表就装下两项数据，S7 编数据也简单（入库时填拒收数） | 拒收率是粗指标，不分缺陷类型 |
| B | 价同 A；**美＝来料检验不合格率**（`Quality Inspection`） | 更贴近质量管理的真实做法 | 要另建检验单与检验模板，S7 编数据的工作量明显加大；跨两张表 |
| C | A 再加**准时交货率**（实际入库日对比采购订单的要求到货日） | 「货美」更完整 | 又多跨一张表（采购订单）；演示时 AI 要同时权衡三项，答案更难事先定死 |

**选项：**（问 3：「符合单子要求」与「利润」怎么算）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A（推荐）** | **某张销售订单里的某个物料，有几个有效 BOM（比如用不同线材）；利润＝订单单价 − BOM 单位成本，取利润最高的那个**。「符合要求」＝ BOM 产出的正是订单上那个物料 | 标准答案能精确算出；对 S7 的要求也清楚——同一弹簧至少要有两三个成本不同的有效 BOM | 「符合要求」读得最窄，不含交期与工艺约束 |
| B | A 再加**交期约束**：按工艺路线工时判断哪个 BOM 能按期交 | 更接近「在符合要求下」的原意 | 要工艺路线、工作站、产能数据，S5 的最小数据造不出来；答案依赖排产假设 |

**推荐理由：** 三问都取 A。原则是**先把每问压到能事先算出唯一标准答案的口径**，因为可信度优先（AI 在现场答错比不演示 AI 代价更大）。B／C 的增量都可以留到 A 口径测通之后再加，届时只是在同一套数据上加字段。

**用户回答：** 三问**先**都取 A；其余选项进延迟需求（回复在第 6 步那一轮到达）。

**结论：** **DEC-012**、**DEC-013**、**DEC-014**（见第 6 步与决策汇总表）。

---

#### 第 6 步：三问口径定为全 A、其余进延迟需求；Insights 的分支须更正

**① 三问的口径**

**提出者：** 用户

**背景：** 回答第 5 步议题 ②。

**用户回答：** 三问先都选 A。当前主要保证演示流畅与稳定；别的选项应加入延迟需求，便于实际交付客户时能做更复杂的判断（用户提出）。

**结论：**

- **DEC-012**（问 1）：「找单子」＝进行中的商机按加权金额（`expected_deal_value`，按字段名推断为金额 × 概率，计算式未读）排序取前几名。（「附预计成交日」是 Claude 写记录时补的，用户选 A 时看到的选项里没有。）
- **DEC-013**（问 2）：价＝同一物料各供应商的采购入库平均单价；美＝收货拒收率（`rejected_qty ÷ received_qty`），两项都取采购入库明细。
- **DEC-014**（问 3）：某张销售订单上的某个物料有几个有效 BOM，利润＝订单单价 − BOM 单位成本，取最高者；「符合要求」＝ BOM 产出的正是订单上那个物料。
- **未选的四个选项进本轮延迟需求节**（第 6 步提出），唤醒条件统一取「四阶段战略第 ④ 阶段（调研客户实际生产环境、做定制）开工时」。用户原话是「便于实际交付客户的时候」，**把它对应到第 ④ 阶段是 Claude 做的**，用户未就此表态。

**② Insights：分支须更正，并定「装成」的口径（IM-006／RW-02）**

**提出者：** Claude

**背景：** 本轮为议题 6 读 Insights 时，查到 DEC-002 对 Insights 那一半**建立在错误前提上**。可复现路径：在 `Reference/insights` 下 `git fetch origin main` 与 `git fetch origin tag v3.14.2`，`git log -4 FETCH_HEAD`、`git show {FETCH_HEAD,v3.14.2}:pyproject.toml`、`git ls-remote --tags origin`；PyPI 的 `https://pypi.org/pypi/{包}/{版本}/json`。

| # | 事实 |
|---|---|
| 1 | **Insights 的 `main` 是旧的 v2 线**：最新提交是 v2.2.14（2026-06-23），之后只有一次依赖修补（2026-09-22）。依赖里**没有 duckdb／ibis** |
| 2 | **v3 才是现行版本，以 tag 发布**：最新 tag **`v3.14.2`**（commit `5447f162`，2026-09-29）。依赖有 `duckdb~=1.4.3`、`ibis-framework~=11.0.0` 等。**⚠ 收尾记录验证时更正**：原文写「从 `develop` 打 tag」「仅落后 `develop` 头 1 个提交」，与工具返回不符——`merge-base --is-ancestor v3.14.2 origin/develop` 未通过，`git branch -r --contains` 为空，而本地 `origin/develop` 是 09-23 的旧快照、本轮没有重新 fetch。**tag 与 `develop` 的关系未查清**；DEC-015 只依赖「v3 是现行版本、tag 是正式发布点」，不受影响 |
| 3 | **S2 对 Insights 的全部判断读的是 v3**（`develop` 快照）：未译率 48.3%～70.3%、导入 duckdb 后看板不实时、`connectors/frappe_db.py` 直连 MariaDB、`doc_events` 仅 1 个。⇒ 第 1 步说「`main` 是发布分支」**对 CRM、Raven 成立，对 Insights 不成立** |
| 4 | **RW-02 的风险比原判断低**：原判断是「duckdb／ibis 在 Windows Docker 的可安装性完全未验证」，但 bench 跑在 **Linux 容器**里，PyPI 上 `duckdb` 1.4.3／1.4.4 与 `pandas` 2.3.3 都有 **`cp314` 的 manylinux x86_64 预编译包**，`ibis-framework` 是纯 Python 包（只查了最新的 12.0.0，v3.14.2 要求的 11.0.x 未查）⇒ 不需要现场编译。**仍未实装验证** |

**选项：**（问 1：Insights 装哪个版本）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **A（推荐）** | **装 v3：`apps.json` 写 tag `v3.14.2` 并锁 commit `5447f162`** | 现行版本，S2 的所有判断都建立在它上面；tag 是正式发布点，不是开发线上的任意提交 | `setup.sh` 是按 `--branch` 克隆的，要确认传 tag 名可行（`git clone --branch` 接受 tag，D 步实测一次） |
| B | 装 `main`（v2.2.14） | 符合 DEC-002 的字面 | 已停更的旧线；S2 的判断（未译率、侵入度、直连数据库）全都不适用，等于对一个没评估过的东西做决定 |
| C | 装 `develop` 头 | 最新 | 开发线，与 DEC-002 避开 `develop` 的理由相冲（原写「比 A 只多 1 个提交」，收尾时查明不成立，见上方事实 2） |

**选项：**（问 2：Insights 装到什么程度算完成）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **甲（推荐）** | **装成＋能用一次**：`install-app` 成功；`/insights` 能打开；对本站点建一个数据源、跑一次查询出结果（例如销售订单条数） | 证明依赖确实装上、直连数据库那条路通，与「装它是执行用户指令、不为演示」相称 | 比只装多半小时 |
| 乙 | 只要 `install-app` 成功 | 最省 | duckdb 这类依赖有时装得上、一跑就崩，只装不跑等于没验 RW-02 |
| 丙 | 甲再加一个看板 | 更完整 | Insights 不进演示（NV-022），看板没有消费方 |

**推荐理由：** A＋甲。A 让装的东西与 S2 评估过的东西一致；甲用最小的代价把 RW-02 实际验掉。若装不上，按 RW-02 原缓解办法当场记延迟需求、把 331 条译名从 S6 范围扣掉。

**用户回答：** 取 A＋甲；装不上就把 331 条译名从 S6 范围里扣掉（回复在第 7 步那一轮到达）。

**结论：** **DEC-015**、**DEC-016**（见第 7 步与决策汇总表）；DEC-002 的 Insights 部分由 DEC-015 更正。

---

#### 第 7 步：Insights 定为 A＋甲；演示终端连通性读码查出一处会静默失效的点

**① Insights 版本与完成口径**

**提出者：** 用户

**背景：** 回答第 6 步议题 ②。

**用户回答：** 「A＋甲」；装不上就把 331 条译名从 S6 范围里扣掉。

**结论：**

- **DEC-015**：Insights 装 **v3，`apps.json` 写 tag `v3.14.2`、锁 commit `5447f162`**。**更正 DEC-002 的 Insights 部分**（DEC-002 原写「Insights 用 `main`」，建在「`main` 是发布分支」这个对 Insights 不成立的前提上，见第 6 步议题 ②）。`setup.sh` 用 tag 克隆是否可行，D 步实测。
- **DEC-016**：Insights 的完成口径＝`install-app` 成功＋`/insights` 能打开＋对本站点建一个数据源、跑一次查询出结果。**装不上则当场记延迟需求，并把 331 条译名从 S6 范围扣掉**（用户重申 RW-02 原缓解办法）。

**② 演示终端连通性（CR-015／LG-103）**

**提出者：** Claude

**背景：** CR-015 的判据是「页面能打开」与「实时通道能通」两条独立通路都要验到，具体连通机制留本 Stage 定。本轮读了前端的实时连接代码与实时服务的鉴权代码（可复现路径：`frappe/public/js/frappe/socketio_client.js` 的 `get_host`、`frappe/templates/base.html:52`、`frappe/__init__.py:85`；`realtime/middlewares/authenticate.js:13-40`、`:89-113`；`realtime/index.js:12-14`；`sites/common_site_config.json`；`docker/compose.yaml:49-57`）。

| # | 事实 |
|---|---|
| 1 | **两条通路在物理上就是分开的**：开发服务器模式下（本项目是否设了 `DEV_SERVER` 未直接查，据 `docker/compose.yaml:50-54` 的注释推断是），浏览器连实时服务时**取页面的主机名、换成实时服务自己的端口**，不走页面那个端口。⇒ 异地终端能打开页面，**不代表**它能到达实时服务的端口 |
| 2 | **实时服务按「请求的主机名」认站点**：请求头带站点名就用它；主机名是 `localhost`／`127.0.0.1` 时用默认站点；**否则用来访者的主机名当站点名**。而浏览器连的命名空间是站点本名 `erx.localhost`。⇒ **异地终端只要不是用 `localhost` 访问，站点名就对不上，连接被拒（`Invalid namespace`）** |
| 3 | 页面那一侧**不受这条影响**：站点配置开了「任何主机名都服务默认站点」，所以页面照样能打开 |
| 4 | 实时服务另要求请求的主机名与来源主机名一致，否则也拒（`Invalid origin`） |

⇒ **事实 2＋3 正是 CR-015 最怕的形态**：异地终端上**页面一切正常、实时通道静默断开**，界面不报错。本机浏览器测不出它（本机用 `localhost` 访问，命中默认站点那条分支）。**读码结论，未实测**；具体怎么解（在前面加一层转发补站点名、或让两条通路走同一入口等）属连通机制，留 C 步定。

**选项：**（问 1：CR-015 怎么算验到）

| 选项 | 描述 | 优点 | 缺点 |
|------|------|------|------|
| **甲（推荐）** | **三条**：① 异地终端登录、打开一张单据；② 本机发一条测试事件，**异地终端界面上实收到**（不只看连接建立）；③ **反证一次**：故意让实时通道不通，确认同一套检查会报失败 | ③ 证明这套检查**分得清**通与不通（开发守则「判据必须能区分它要区分的两种情形」）；② 直接对上 S7 的 CR-008／CR-009 要用的那条路 | 比只验连接多一步 |
| 乙 | ① 同甲；② 只看异地终端上实时连接是否建立 | 最省 | 连接建立后鉴权仍可能被拒；且没有反证，检查本身可能永远报「通」 |

**选项：**（问 2：「异地终端」指什么环境）——这是事实问题，要请用户说明实际演示场景

| 选项 | 描述 | 对验证的影响 |
|------|------|------|
| A | **另一台设备，与本机在同一局域网** | 验证可在本地做完；但演示现场若不在同一网络，结论不能直接搬过去 |
| B | **另一台设备，经外网访问本机**（客户现场与本机不在同一网络） | 与真实演示一致；连通机制要多解决一段外网可达 |
| C | 两种都要 | 最稳；两套都要验 |

**推荐理由：** 问 1 取甲：这个问题在本机上测不出来，而 ③ 反证正是用来防「检查本身报不了失败」这种情况。问 2 要按真实演示场景定，故先问用户。

**用户回答：** 问 1 取甲，问 2 取 C（回复在第 8 步那一轮到达）。

**结论：** **DEC-017**、**DEC-018**（见第 8 步与决策汇总表）。

---

#### 第 8 步：CR-015 定为甲＋两种环境都验；工作量重估

**① CR-015 的验法与环境**

**提出者：** 用户

**背景：** 回答第 7 步议题 ②。

**用户回答：** 「问 1、甲。问 2、C。」

**结论：**

- **DEC-017**：CR-015 验三条——① 异地终端登录并打开一张单据；② 本机发一条测试事件，异地终端界面上实收到；③ 反证一次：故意让实时通道不通，同一套检查须报失败。
- **DEC-018**：异地终端**局域网与外网两种环境都要验**，每种各跑一遍 DEC-017 的三条。

**⚠ 讨论中发现：** 外网环境意味着本机站点要能从外网访问到，这是把站点对外暴露。Claude 提出两条随之而来的约束，交 C 步落实：① 暴露前确认管理员口令不是搭建时的初始值（本轮未查初始值是什么；`docker/scripts/setup.sh:397` 只看到用户名 `Administrator`）；② 只暴露页面与实时两条通路，数据库、缓存等其余端口不对外。具体连通机制仍留 C 步定。登 **LG-008**。

**② 工作量重估（RW-09）**

**提出者：** Claude

**背景：** 路线文档 v1.4 给本 Stage 的是 **5.5–9.5 人日**（CR-013 1–2／IM-005 0.5–1／IM-006 含在接入内／EX-001 3–5／CR-015 0.5–1，后者是类推值）。RW-09 要求 A 步按讨论结果重估并回写。按第 1–8 步定下的范围逐项重估：

| 项 | 本轮定下的范围 | 原估 | 重估 | 变动原因 |
|---|---|---|---|---|
| 接入公共部分 | 四个 App 的 `apps.json` 条目（含 Insights 用 tag）；`setup.sh` 认出官方 App 的 remote 归位；装完调序（DEC-003）；先在 `test.localhost` 装并跑 S4 全量 160 条回归，再装演示站（DEC-006） | 未单列 | **1–1.5** | 原估把它摊在各 App 里；本轮多出调序、tag 克隆、两站各装一次与全量回归 |
| IM-005 HRMS | 报销类型科目预配（DEC-005，含 5 行映射表）；`HDTH` 保存后科目数不变的验证 | 0.5–1 | **0.5–1** | 不变 |
| IM-006 Insights | 装成＋建数据源＋跑一次查询（DEC-016） | 含在接入内 | **0.5** | 单列 |
| CR-013 CRM | Lead → Deal → 推进 → 报价 → 接单＋漏斗看板（DEC-007）；临时测试物料做产品同步；LG-004 币种 | 1–2 | **1–1.5** | 读码已查清链路，上限下调 |
| EX-001 Raven | 连 LiteLLM（0.5）；只读工具记录＋报表通道（0.5，DEC-009）；三问最小数据与标准答案（1–1.5，DEC-010／012–014）；每问 3 次实测（0.5）。**报表通道走不通须自写查询则另加 1–2** | 3–5 | **2.5–3，最坏 3.5–5** | 下限下调（工具只读、模型不归本 Stage）；自写查询那段原估已含 |
| CR-015 连通性 | 解 LG-007；局域网与外网两种环境各验三条（DEC-017／018）；外网暴露的两条约束（LG-008） | 0.5–1（类推） | **1–2.5** | 原估只按局域网一种想；外网可达的机制未定，上限因此放宽 |
| **合计** | | **5.5–9.5** | **6.5–12** | 主要来自「接入公共部分」单列与外网验证 |

**用户回答：** 确认（回复在第 9 步那一轮到达）。

**结论：** **DEC-019**（见第 9 步与决策汇总表）。

---

#### 第 9 步：工作量确认，A 步收尾；B 步由用户在下一 Session 开

**① 工作量重估**

**提出者：** 用户

**背景：** 回答第 8 步议题 ②。

**用户回答：** 确认。

**结论：** **DEC-019**：本 Stage 工作量重估为 **6.5–12 人日**（原 5.5–9.5），分项见第 8 步议题 ② 的表。由 B 步回写路线文档（RW-09）。

**② 收尾方式**

**提出者：** 用户

**背景：** 第 8 步末 Claude 说明 A 步收尾要做三件事（派子 Agent 对照原始对话核讨论记录、写状态值与复核建议、关落档开关），然后进 B 步。

**用户回答：** 做完这三件事后**不要直接进 B 步**，用户会在下一个 Session 自己开（用户提出）。

**结论：** 本 Session 做完三件收尾、更新 Stage 概况进度即停，不起 B 步。Stage 概况的下一步写「B 步需求文档，由用户在新 Session 开」。

---

## 复核建议

按「错了代价最大」排序：

1. **LG-007（异地终端的实时通道会被静默拒连）是读码结论，CR-015 的整套验法（DEC-017／018）和工作量上限都压在它上面。** 查法：读 `frappe-bench/apps/frappe/realtime/middlewares/authenticate.js:13-40` 与 `:89-113`，按「异地终端用局域网 IP 访问」走一遍 `get_site_name` 的四条分支，确认落到「用来访主机名当站点名」那条、且与命名空间 `erx.localhost` 不等。若读法不成立，CR-015 会比估的简单，但 DEC-017 的反证一条仍要做。
2. **DEC-005 的 HRMS 风险分析读的是 `version-16` 分支头，而 D 步要锁的 commit 还没定。** 查法：D 步锁定 HRMS 的 commit 后，在该 commit 上重读 `hrms/overrides/company.py` 的 `set_expense_claim_type_accounts`（看跳过条件是否仍是「已有 `Expense Claim Account` 就跳过」）与 `hrms/hooks.py` 的 `Company` 钩子清单。DEC-005 整个方案依赖那个跳过条件。
3. **DEC-009 的报表通道（`Custom Function` → `get_report_result`）是本轮最勉强的一处：只试过这一个方向。** 它若走不通（LG-006），Raven 的工作量取最坏值 3.5–5，后两问要自写查询。查法：B 步写需求时把「报表通道不通 → 自写 `Custom Function`」写成显式的备选路径与触发条件，不要只写一条路。

**拿不准处：**

- **DEC-003 的调序是否立即生效**（LG-002）：hooks 有 site 级缓存，调序后要不要 `clear-cache` 读码没看全。
- **DEC-013 的「美」取拒收率**，用户说的是「先都选 A」。记录按「当前定 A、其余进延迟需求」写，没有写成永久口径。

**收尾时补核的一处**（不占步）：DEC-004 第 ③ 条依赖的译名合并方向，已逐行读 `frappe/translate.py:172-187`（`get_translations_from_apps`）确认——按 `installed_apps` 顺序逐个 `dict.update`，**后装的 app 覆盖先装的**，故 `frappe_china` 在末位即胜出。另读出一处细节交 S6：**同一 app 内先读 `.csv`、后读 `.mo`，`.mo` 覆盖 `.csv`**。ADR-0006 定的是 csv 单一来源，`frappe_china` 不放 `.mo` 即不受影响；但若哪天给 `frappe_china` 生成了 `.mo`，csv 里的译名会被静默盖掉。

## 记录验证（记录验证契约，收尾时做，不占步）

对照的是本 Session 原始对话（transcript 以 `S05-演示链路`／`update_installed_apps_order`／`v3.14.2` 三个关键词交叉命中定位）。分两段派子 Agent：第 1–4 步一段、第 5–9 步一段。第 1–4 步那段首次派出时被 API 安全拦截中断，改为只读对话文字、不读工具返回后重派完成。

| # | 查出的问题 | 处理 |
|---|---|---|
| 1 | **第 2 步与第 5 步记的两次「Claude 误发重问」都不存在**。按时间戳，两次被说成「重问」的消息都早于用户的回复，是议题的首次呈现；是 Claude 误判后，在回复里向用户说了失实的「误发」 | 两处原文保留，各加更正段；向用户当面更正 |
| 2 | Insights「从 `develop` 打 tag」「仅落后 `develop` 1 个提交」与工具返回不符（本地 `develop` 是旧快照，tag 不在其历史上） | 事实 2 与选项 C 改写并注明，DEC-015 不受影响 |
| 3 | 工作量上限 12 含 Raven 最坏值，与 DEC-019 失效条件的写法矛盾 | DEC-019 注明两种口径（常规 6.5–10），修正失效条件 |
| 4 | 归属：DEC-010「测完清掉」、DEC-012「附预计成交日」是 Claude 写记录时补的，用户选时看不到；DEC-011 的两条约束、DEC-018 的理由、延迟需求唤醒条件的对应关系也是 Claude 加的 | 逐处标明「Claude 补」；DEC-012 删去「附预计成交日」；DEC-018 理由改为「取 C，未说明理由」 |
| 5 | 未读码即写入的字段：`rejected_qty`／`received_qty`、`expected_deal_value` 的计算式、本项目是否开了开发服务器模式、ibis 11.0.x 是否纯 Python | 前者收尾时已读码确认；其余标为推断，留 C 步核 |
| 6 | 第 5 步「用户回答」丢了「先」字；LG-001 与 NV-002 未随 DEC-015 更正；DEC-008 等行序错乱 | 补字、补注、按编号重排 |

**未能逐字核对的一处**：第 1 步议题 ③ 两问由选择题工具作答，子 Agent 只读文字块故未见原文；主 Session 核对了工具返回，用户所选为「官方仓库＋锁 commit」与「HRMS v16，其余 main」，与记录一致。

## 状态值

| 字段 | 内容 |
|---|---|
| 状态值 | `已收敛` |
| 判定依据 | 第 1 步排定的 8 个议题全部经用户裁决（DEC-001～DEC-019），每条完成标志都已定可判真假的验法；遗留的 LG-001～LG-008 都是待实测或待 C 步落实的事项，不阻塞写需求文档。用户第 9 步确认收尾，并指示 B 步由其在下一 Session 开 |

---

## 决策汇总表

| 编号 | 决策内容 | 最终选择 | 选择理由 | 提出者 | 失效条件 |
|---|---------|---------|---------|--------|---------|
| **DEC-001** | 四个 App 的来源 | **官方仓库，`apps.json` 锁 commit**；确须改其源码时再 fork | 修复已归 `frappe_china`（ADR-0013），改上游源码是 L5；fork 只带来同步负担 | Claude（第 1 步） | 须改某个 App 的源码且无 hook 可走时，该 App 改为 fork |
| **DEC-002** | 四个 App 的分支 | **HRMS `version-16`；CRM／Raven `main`**；~~Insights `main`~~ **→ 由 DEC-015 更正为 v3 tag `v3.14.2`**（第 7 步） | 均为发布分支、均声明兼容 v16；HRMS 的 `develop` 已要求 v17。⚠「`main` 是发布分支」对 Insights 不成立 | Claude（第 1 步），用户确认（第 1 步） | 某 App 日后出 `version-16` 分支时可改用；`main` 改为要求 v17 时须锁在兼容的 commit |
| **DEC-003** | `frappe_china` 的归位手段 | **装完四个 App 后调 `update_installed_apps_order` 把 `frappe_china` 调到末位**，写进 `setup.sh` | 不卸载、不碰数据，可在新机器上自动重现；取代 LG-151 的「重装」 | Claude（第 1 步），用户确认（第 2 步） | 调序入口被上游移除或改语义时 |
| **DEC-004** | 完成标志②的验收口径 | **三条**：① `installed_apps` 末位是 `frappe_china`；② 三个 whitelisted 覆盖解析到 `frappe_china`；③ 一条与四个 App 撞源词的测试译名实测由 `frappe_china` 胜出。`check_all_cn_companies()` 直接调一次全过；`after_migrate` 接线仍归 S8G-S1 | 「覆盖生效」在 S5 当下不受顺序影响（四个 App 都不抢那三个覆盖位），顺序真正起作用的是译名合并 | Claude（第 1 步），用户确认（第 2 步） | 某个 App 日后开始覆盖那三个方法时，② 的意义随之改变 |
| **DEC-005** | HRMS 报销类型自建科目的处理 | **`frappe_china` 为中式公司预先配好 HRMS 5 个报销类型的默认科目**，映射到 `管理费用` 下的明细；映射表由 B 步列出、标「待领域专家确认」。**`frappe_china` 不得因此依赖 HRMS**（客户正式库未必装 HRMS），只在 `Expense Claim Type` 存在时才配 | 保住 S4 的科目表；HRMS 见已配即跳过（`company.py` 的 `if frappe.db.exists("Expense Claim Account", ...): continue`） | Claude（第 2 步），用户确认（第 3 步） | HRMS 改了 `set_expense_claim_type_accounts` 的跳过条件；或新增报销类型 |
| **DEC-006** | RW-01 的验法 | **三条**：① 先在 `test.localhost` 装四个 App 并跑完 S4 全量测试，再装演示站，装前先备份；② 装完后 S4 的 160 条测试全过；③ `HDTH` 保存一次公司后科目数仍为 266、自检多余科目为空 | 把 RW-01「先在一次性测试公司上验」具体化；② 同时验 HRMS 对 `Payment Entry` 的整类覆盖 | Claude（第 2 步），用户确认（第 3 步） | — |
| **DEC-007** | CRM 演示的起点与范围 | **从 Lead 开始**：Lead → Deal → 推进几档 → 报价 → 接单，**含 CRM 漏斗看板**（加权预测收入、各档转化）。完成标志①的措辞由 B 步补 | 与图谱 CR-013 的起点一致；看板是 CRM 对客户最有说服力的部分，S5 先验掉，不留到 S7 | Claude（第 3 步），用户确认（第 4 步） | — |
| **DEC-008** | 由 Deal 建客户的时机 | **用 CRM 默认机制**：报价单报给 `CRM Deal`，保存销售订单时由 CRM 的 `before_validate` 钩子自动建客户；不勾「状态变更时建客户」 | 零配置、与先报价后成交的真实业务一致；勾选那一项也省不掉报价单对象是「商机」这句解释 | Claude（第 3 步），用户确认（第 4 步） | CRM 改了该钩子的行为；或客户要求赢单即建客户 |
| **DEC-009** | 演示 bot 挂哪些工具 | **只读**：`Get List`＋`Get Document` 按演示要用的 DocType 各建记录，另加 `Custom Function` → `raven.ai.functions.get_report_result` 作报表通道；不建 `Update`／`Create`／`Delete` | `Create`／`Delete` 两个 handler 在 `main` 上不存在（LG-005）；AI 在现场不能改数据，符合可信度优先；报表通道可能省掉自写查询 | Claude（第 4 步），用户确认（第 5 步） | 报表通道实测不通（LG-006）时改为自写 `Custom Function` |
| **DEC-010** | 三问怎么测 | **`test.localhost` 上造最小数据，每问事先算好标准答案；每问跑 3 次，3 次都答对且说得出依据（引了哪些单据或报表）才算「答得出」；测完清掉** | 「答得出」可判真假；不碰演示站的空账基准点；数据结构给 S7 当样板 | Claude（第 4 步），用户确认（第 5 步）；「测完清掉」与依据的括注由 Claude 写记录时补 | 最小数据下答得出、S7 的 100 条下答不出时，S7 须重测 |
| **DEC-011** | Raven 用哪个模型 | **由用户在 LiteLLM 里配，不进本 Stage 范围**；S5 只负责 Raven → LiteLLM 的连接（`OpenAI Compatible`），bot 的 `model` 填用户给的别名。测试报告记下别名；密钥不进文档与仓库 | 用户裁决 | 用户（第 5 步）；「记下别名」「密钥不进文档」两条约束由 Claude 补 | **用户换模型时三问须重测** |
| **DEC-012** | 三问·问 1「找单子」的口径 | **进行中的商机按 `expected_deal_value`（加权金额；「＝金额 × 概率」按字段名推断，计算式未读）排序取前几名** | 单表可答、标准答案唯一；演示稳定优先 | Claude（第 5 步），用户确认（第 6 步）；原写「附预计成交日」，用户选时未见，收尾时删 | 进入第 ④ 阶段时按延迟需求重判 |
| **DEC-013** | 三问·问 2「货美价廉」的口径 | **价＝同一物料各供应商的采购入库平均单价；美＝收货拒收率（`rejected_qty ÷ received_qty`）** | 两项同在采购入库明细，S7 编数据简单 | Claude（第 5 步），用户确认（第 6 步） | 同上 |
| **DEC-014** | 三问·问 3「BOM 利润最大化」的口径 | **订单上某物料有几个有效 BOM，利润＝订单单价 − BOM 单位成本，取最高者；「符合要求」＝ BOM 产出的正是订单上那个物料** | 标准答案可精确算出；对 S7 的要求明确（同一弹簧两三个成本不同的有效 BOM） | Claude（第 5 步），用户确认（第 6 步） | 同上 |
| **DEC-015** | Insights 装哪个版本（**更正 DEC-002 的 Insights 部分**） | **v3：`apps.json` 写 tag `v3.14.2`、锁 commit `5447f162`** | Insights 的 `main` 是已停更的 v2 线；S2 的判断全部基于 v3；tag 是正式发布点 | Claude（第 6 步），用户确认（第 7 步） | 有更新的 v3 tag 时可改锁 |
| **DEC-016** | Insights 的完成口径 | **`install-app` 成功＋`/insights` 能打开＋对本站点建数据源、跑一次查询出结果**；装不上则当场记延迟需求、把 331 条译名从 S6 范围扣掉 | 用最小代价实际验掉 RW-02；不进演示，不建看板 | Claude（第 6 步），用户确认（第 7 步） | — |
| **DEC-017** | CR-015 怎么算验到 | **三条**：① 异地终端登录并打开一张单据；② 本机发测试事件、异地终端界面实收到；③ 反证：故意让实时通道不通，同一套检查须报失败 | 该失效在本机测不出（LG-007）；③ 证明检查分得清通与不通 | Claude（第 7 步），用户确认（第 8 步） | — |
| **DEC-018** | 「异地终端」的环境 | **局域网与外网两种都验**，各跑一遍 DEC-017 | 用户裁决（取 C，未说明理由） | 用户（第 8 步） | 演示场景确定为其中一种时可减 |
| **DEC-019** | 本 Stage 工作量 | **6.5–12 人日**（原 5.5–9.5）：接入公共部分 1–1.5／HRMS 0.5–1／Insights 0.5／CRM 1–1.5／Raven 2.5–3（最坏 3.5–5）／连通性 1–2.5。**⚠ 收尾核算**：上限 12 是把 Raven 取最坏值 5 算进去的；Raven 取常规值 3 时合计是 **6.5–10**。用户确认的是 6.5–12，数不改，B 步回写路线文档时两种口径都写明 | 按第 1–8 步定下的范围逐项重估（RW-09） | Claude（第 8 步），用户确认（第 9 步） | 报表通道走通（LG-006）则上限按 10 算；外网连通机制在 C 步定后可再收窄 |

## 被否决方案汇总表

| 编号 | 方案 | 否决理由 |
|---|------|---------|
| **NV-001** | 四个 App 先 fork 到 `PhilixKuro` | 本项目不预期改它们的源码，fork 只带来四个仓库的同步负担（第 1 步） |
| **NV-002** | CRM／Insights／Raven 用 `develop` | 开发线不稳；唯一好处（与 S2 读码版本一致）可由复核读码替代（第 1 步）。**Insights 另见 DEC-015**：它的 v3 以 tag 发布，最终取 tag `v3.14.2`，既不是 `main` 也不是 `develop` 头 |

## 延迟需求

| 提出步 | 需求 | 不在本级做的理由 | 唤醒条件 |
|---|---|---|---|
| 第 6 步 | **AI 分析·「卡住的单」**：在 DEC-012 之上加「超过一定天数没推进阶段的商机」（须读状态变更历史，另定天数阈值） | 用户裁决：当前保证演示流畅稳定，单表口径先行 | 四阶段战略第 ④ 阶段（调研客户实际生产环境、做定制）开工时 |
| 第 6 步 | **AI 分析·「货美」改用来料检验不合格率**（`Quality Inspection`），替代或补充 DEC-013 的拒收率 | 同上；且 S7 须另建检验单与检验模板 | 同上 |
| 第 6 步 | **AI 分析·「货美」加准时交货率**（实际入库日对比采购订单要求到货日） | 同上；多跨一张表，标准答案更难定死 | 同上 |
| 第 6 步 | **AI 分析·BOM 选择加交期约束**（按工艺路线工时判断能否按期交） | 同上；须工艺路线、工作站、产能数据 | 同上 |

## 遗留问题

| 编号 | 事项 | 状态（暂缓/待确认/待调研） | 触发条件（何时重新处理） |
|---|------|--------------------------|------------------------|
| **LG-001** | S2 对四个 App 的读码结论基于 `Reference/` 下的 `develop` 快照（2026-09-22／23），实装是 HRMS `version-16`、CRM 与 Raven `main`、Insights tag `v3.14.2`（DEC-015），须在实装版本上复核（至少：Raven `handle_get_list` 末端、Raven 无 `fixtures`、CRM Deal 生成报价单的按钮、HRMS 的 `doc_events`／`override_doctype_class` 清单） | 待调研 | 四个 App 实装后、C 步写方案前 |
| **LG-002** | 调 `update_installed_apps_order` 之后 hooks 的 site 级缓存（`frappe/__init__.py:988-1006`）是否立即失效，还是要 `clear-cache`／重启 | 待实测 | D 步写 `setup.sh` 调序段时 |
| **LG-003** | HRMS 的 `set_expense_claim_type_accounts` 按译名找、按译名建科目，不同会话语言下保存公司可能建出中英两个重复科目（读码推断） | 待实测 | 议题 3 定案后，D 或 E 步验 |
| **LG-004** | CRM Deal 的币种默认值未查；由 Deal 建出的 Customer 取 `default_currency = deal.currency`，若不是 CNY 会带进报价单与销售订单 | 待调研 | C 步写方案前（CRM 实装后读一次即可） |
| **LG-005** | Raven `main` 里 **`handle_create_document`／`handle_delete_document` 全仓零定义**，`Create Document`／`Delete Document` 两类记录建了也静默不生效（只在 Error Log 留一条）。完成标志③「五个内置 handler」须改口径 | 已读码确认，待 B 步改完成标志措辞 | B 步 |
| **LG-006** | `Get Report Result` 在 Raven 的 Agents 路径不生效（`sdk_tools.py:55-56` 的 `continue`）；改用 `Custom Function` 指向 `raven.ai.functions.get_report_result` 理论可通，且该路径下报表权限是否照常校验，均未实测 | 待实测 | 议题 5 定案后、三问实测前 |
| **LG-007** | **异地终端用非 `localhost` 主机名访问时，实时服务按来访主机名认站点、与命名空间 `erx.localhost` 对不上而拒连**，页面却照常能开（`realtime/middlewares/authenticate.js:13-40`、`:89-113`）。读码结论 | 待实测 | CR-015 实测时；解法留 C 步 |
| **LG-008** | 外网环境须把本机站点对外暴露：暴露前须确认管理员口令不是搭建时的初始值，且只暴露页面与实时两条通路、数据库与缓存端口不对外 | 待 C 步落实 | C 步定连通机制时 |
