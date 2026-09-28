# ADR-0013: 自有 app 按域分为 `frappe_china` 与 `frappe_debug` 两个

- 状态：accepted
- 日期：2026-09-28（落成）／决策出自 P1-S4-R1 A 步第 8 步（划分、推送侧归属、生产修正归属）与 P1-S4-R6 B 讨论第 2 步 ②（代码标识）
- 决策者：**用户提出划分并裁决**（R1 第 8 步 ①–④），Claude 核判据与补事实；代码标识由用户在 Claude 所出三个选项中选定
- 对应决策：DEC-109（数目与装载顺序）／DEC-092（代码标识）／DEC-110（推送侧归属）／DEC-111（生产修正归属）／DEC-112（不为 React 另建 Debug app）／DEC-113（S5 后重装交接约束）

## 上下文

ADR-0001 定了单 app（`erx_core`），核心理由是「四处 `[-1]` 机制都取 `installed_apps` 的顺序，自有 app 每多一个，要守住的位置就多一个」；ADR-0002 给它起名 `erx_core`。两条都在 D 步建 app 之前，改它们仍是纯文档工作。

P1-S4 的 A 步里用户提出重新划分：中国财税、译名与导航、对原生 ERPNext 与官方 app 的修复放一个 app；演示操控、数据生成放另一个 app，因为这些「不但适合演示，还适合自动化测试」；远期 React 重写另放一个 app，顺序到时再定。

**判据的关键事实**：两个新 app 抢的不是同一样东西。

| app | 要不要占 `[-1]` | 为什么 |
|---|---|---|
| `frappe_china` | **要，全部四处**：区域覆盖（`erpnext/__init__.py:152`）／whitelisted 覆盖（`frappe/__init__.py:1577-1580`）／类覆盖（`base_document.py:110-125`）／译名 csv（`translate.py:179`） | 覆盖科目表方法（L4）、译名要盖住所有业务 app |
| `frappe_debug` | **一处都不要** | 演示操控是推 realtime 事件、数据生成是调 whitelisted 方法建单，都是新增，不覆盖任何上游行为 |

⇒ 不是「两个 app 争末位」，而是「`frappe_china` 要压住全部业务 app，`frappe_debug` 不在乎位置」。ADR-0001 的核心理由在这种划分下不成立。

## 决策

自有 app 建 **2 个**，装载顺序 **`frappe → erpnext → CRM → HRMS → Insights → Raven → frappe_china → frappe_debug`**：

- **`frappe_china`**（界面标题 Frappe China）：中国财税（`cn_tax`）、译名与导航、对原生 ERPNext 与官方 app 的修复（CR-003／CR-004 等，与中国化无关的通用缺陷也归这里）、**事件协议的推送助手与契约**。客户正式库一定装。
- **`frappe_debug`**（界面标题 Frappe Debug）：演示操控的 23 个节点函数与编排、数据生成、自动化测试。**客户正式库不装。** 内部按三层分：`data/`（造数据与建单辅助，两类界面共用）／`nodes/`（23 个节点的业务定义，共用）／`drivers/desk`（Cypress）与 `drivers/spa`（Playwright，将来给 React）。具体目录留 S7 的开发方案。
- 远期 React 重写的 app 另建，顺序到时再定（见失效条件）。

**交接约束**（DEC-113）：新装的 app 一定追加到末尾（`installer.py:379-383` 的 `if app_name not in installed_apps` 守卫）。S4 先建 `frappe_china` 并装上；**S5 装完四个官方 app 后须让 `frappe_china` 回到它们之后，并实测覆盖是否生效**，否则它被挤掉 `[-1]`，S6 的译名 csv 静默不生效。⚠ 「重装」的手段不是现成的：`--force` 不改位置、卸载会删表丢数据，详见 ADR-0003「决策」节；手段留 S5 的 C 步（LG-151）。

## 后果

**正面**
- **演示代码不进客户正式库由「靠开关」变为「靠不装」**。ADR-0001 自陈的负面（演示专用代码与长期资产同仓发布）消失。
- `frappe_debug` 兼做自动化测试，把原本会被当成「演示临时脚本」的东西定为长期资产。
- `frappe_china` 的名字与内容一致：可独立复用的中国化资产，不挂在项目代号下。
- 需求图谱 §7.3 的「数据生成与演示操控同一套机制」照样成立——两者都在 `frappe_debug` 内。

**负面**
- 两份 `hooks.py`、两次 `install-app`。
- **`frappe_debug` 依赖 `frappe_china`**（它调用后者的推送助手），须在 `required_apps` 里声明；依赖单向，`frappe_china` 不得反向依赖 `frappe_debug`。
- 装载顺序仍是隐式约定，守护仍全靠 IM-007 的 `after_migrate` 自检（同 ADR-0003「中性」）；自检断言的对象由「`erx_core` 在末位」改为「`frappe_china` 在全部业务 app 之后」。

**中性**
- 事件名 `erx_demo_step` **不随 app 改名**：它是 ADR-0008 定的跨单位接口契约（已升进 P1 概况），改名要两侧同改，而名字本身不影响功能。
- `frappe_` 前缀可能被误认为官方出品（DEC-092 的已知缺点），用户接受。

## 备选方案

**保持单 app `erx_core`（ADR-0001 原案）** —— 只守一个位置、一次安装。**没选**：核心理由在新划分下不成立（`frappe_debug` 不占任何覆盖位）；且单 app 让演示代码进客户库只能靠开关。见 NV-107。

**推送侧放 `frappe_debug`** —— 演示相关代码集中一处。**没选**：客户正式库不装 `frappe_debug`，生产环境的 React 界面将拿不到实时推送。决定性的理由是「它必须存在于生产环境」，不是「多方共用」。见 NV-104。

**为 React 界面另建一个 Debug app** —— desk 与 SPA 的测试工具链本就不同（Cypress／Playwright）。**没选**：工作量大头是数据层与编排层，二者与界面无关；拆开则这两层要么复制、要么跨 app 依赖，付两个 app 的成本拿不到隔离收益。见 NV-105。

**代码标识取 `frappechina`／`frappedebug` 或 `erx_china`／`erx_debug`** —— 前者最接近原名，后者一眼可辨是本项目代码。**没选**：前者长词连写难读；后者与「通用、可复用」的定位相反。见 NV-087／NV-088。

## 关联

- **取代**：ADR-0001（单 app）、ADR-0002（命名 `erx_core`）——两者状态改为 `superseded by ADR-0013`，原文保留。
- **随本决策修订**（原文就地改、文末加修订记录）：ADR-0003（装载顺序与 `[-1]` 归属）、ADR-0007（落点与覆盖数）、ADR-0008（推送侧落点）、ADR-0012（模块与普通包在两个 app 间的分配）。
- **只改读法**（文中 `erx_core` 按下表读，头部加一行指针）：ADR-0004、ADR-0005、ADR-0006、ADR-0010。

| 旧文中的 `erx_core/...` | 现归 |
|---|---|
| `cn_tax`、`i18n/`、`translations/zh.csv`、`patches_mfg/`、`workspace_sidebar/`、`desktop_icon/`、推送助手 | `frappe_china` |
| `demo/` 的节点函数、编排、数据生成器与数据集 | `frappe_debug` |

- 依赖：无。
- 被依赖：ADR-0003、ADR-0007、ADR-0008、ADR-0012。

## 失效条件

- **React 重写 app 立项且要覆盖上游行为**时，须重判它与 `frappe_china` 争 `[-1]` 的问题。
- **React 界面的测试不再依赖 ERPNext 的数据层**（如另配独立 mock 数据源）时，`frappe_debug` 可拆出独立的 SPA 测试 app。
- 代码标识**装进站点后冻结**；若决定对外发布且须避免被误认为官方出品，须在装站前重判。
