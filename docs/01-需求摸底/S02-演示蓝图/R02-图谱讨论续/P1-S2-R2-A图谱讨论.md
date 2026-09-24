# P1-S2-R2 图谱讨论（devBlueprint A 步 · 第二卷）

**讨论主题**：客户演示要什么——定位、需求盘点与分级、需求关系（续 R1）
**日期**：2026-09-23 ~ 2026-09-24（收口）
**参与者**：用户、Claude
**规划层级**：Phase 级（分解出 P1 内的后续 Stage）
**Spec**：[../../../流程体系/workflows/devBlueprint/A-vision-devBlueprint-shape.md](../../../流程体系/workflows/devBlueprint/A-vision-devBlueprint-shape.md)

**承接说明**：本卷承接 [../R01-图谱讨论/P1-S2-R1-A图谱讨论.md](../R01-图谱讨论/P1-S2-R1-A图谱讨论.md)（第 1–20 步，1799 行，已达讨论契约 §2 纪律 10 的 1700 行分卷阈值）。本卷自**第 21 步**起，**至第 32 步收口**（A 步状态值 `已收敛`，见尾部「状态值」节）。

**A 步为何仍在继续**：R1 末 Claude 自行判定「已收敛」并走到 B 步，但 A 步 Spec 的「已收敛」含四个条件，第四条「用户确认无补充」未问过用户。用户裁决 A 步改回 `未收敛`，R2 继续（见 R1 第 20 步与 Stage 概况「⚠ A 步曾被误判收口」节）。

---

## 演化过程

#### 第 21 步：用户提出三类新增需求，派五路并行调查

**来源项目：** ERX-001
**适用面·状态：** 仅本项目·提出

**① 新增需求：官方 Frappe CRM App 与客户漏斗**

**提出者：** 用户
**背景：** 用户要求在本次范围内**增加官方 CRM App**，并**在最小闭环里加入 CRM 的「客户漏斗」**。用户对该术语自己也不确定（原话带"是叫这个吗"的疑问）。

R1 已定稿的演示范围是「S1 的 23 环节最小闭环」，起点是**接单**（销售订单）。CRM 的漏斗在**接单之前**（线索 → 商机 → 报价 → 成交），故这是对已定范围的**前向延伸**，不是替换。

**选项：**（本议题尚未到裁决点，先调查后给选项）

**用户回答：** 要求先调查——CRM 是否开源，开源则拉下来分析。
**结论：** **待调查后定分级**。已派出 Agent 查：许可证（要看真实 LICENSE 文件而非 README，R1 已有"README 写 MIT、LICENSE 是 AGPL"的前例）、v16 兼容分支、DocType 是否与 ERPNext 的 `Lead`/`Opportunity` 撞名、漏斗的真实形态与阶段取值、**是否有把 Deal 转成 ERPNext 销售订单的代码**（若无，则漏斗与 23 环节闭环是两套互不相通的数据，这会直接影响它在演示里的位置）、自带中文翻译覆盖多少条。

**术语问题的初步判断（待 Agent 核实）**：行业通用说法是**销售漏斗**或**销售管道（pipeline）**，"客户漏斗"不是标准术语。CRM app 内部的对象名与它自带的中文译名是两回事，须分别查。

**② 新增需求：引入 Flow 与 Raven 两个 AI 模块，且要给客户演示 AI**

**提出者：** 用户
**背景：** 用户要求引入 Flow 与 Raven 两个"AI 模块"，并明确**要给客户演示 AI**。这是 R1 全程未出现过的需求方向——R1 的 8 条核心需求里没有任何 AI 相关项。

**⚠ 讨论中发现：「Flow」这个名字存在歧义。** 至少四个候选指向：① GitHub `frappe` 组织下是否真有 `flow` 仓库（未核实）；② Frappe Framework **内置**的 `Workflow` DocType——若用户指的是它，则它本来就在框架里、**不需"引入"**；③ 第三方的自动化/AI-agent 编排 app；④ Frappe Cloud 上的闭源托管产品。用户称它是"AI 模块"是关键线索，但不足以定论。已派专门 Agent 先做**认定**再做调查，认定失败则如实报告并列出生态里真实存在的 AI 模块候选供用户重新指名。

**用户回答：** 要求确认是否都是开源项目，是则拉下来分析；并要分析它们**是怎么接入的**。
**结论：** **待调查**。Raven 的调查重点已下达为 AI 能力的落地机制——接哪家 LLM、**能否换成 Claude 或国内模型**（中国大陆网络 + 客户现场，若硬编码直连 `api.openai.com` 则演示当场可能连不上）、function calling 怎么真正操作 ERPNext 数据（要求给出"聊天里说一句话 → 真的建出一张销售订单"的完整调用链）、有无 MCP 支持、权限以谁的身份校验。

**③ 战略问题：演示脚本与远期 React 前端能否用同样方式接入**

**提出者：** 用户
**背景：** 用户把 CRM/Raven 的接入方式与本项目两件既有需求并置提问——**演示脚本驱动的外部操控机制**（R1 第 8' 条核心需求）与**远期 React 全面重写前端**（S1-R6 裁决）。若三者能共用同一套机制，则第 8' 条的投入就不只服务演示，而是 React 重写的前置基建；若不能共用，则三件事各自要一套。

这一问直接牵动 R1 遗留的「甲乙选项」未决项：甲=服务端推事件驱动（MCP 与 React 可复用）、乙=浏览器侧驱动（复用不到驱动界面那部分）。

**用户回答：** 要求分析 Flow 和 Raven 的接入方式，并回答演示脚本与 React 重写界面是否也能用同样方式接入。
**结论：** **待调查**。已派 Agent 从本机 frappe v16 源码查六条：独立 SPA 挂路由的完整链路、认证与 CSRF（决定外部脚本能否驱动已登录的浏览器会话）、REST API v2 的实际形态、**realtime 能否让已打开的 desk 页面"自己动"**（要求给明确档位结论，不许含糊）、三者共用面的判定、以及**多 app 并存对 `regional_overrides` 取 `[-1]` 的影响**——这一条是本项目特有风险：中国本地化靠末位装的 app 胜出，再装 CRM/Raven 可能把自有 app 挤到非末位而使覆盖失效。

**④ 新增需求：工业生产相关 Frappe App 的普查**

**提出者：** 用户
**背景：** 用户要求搜索"还有没有什么我没提到的、跟工业生产有关的、Frappe 框架比较流行的 App"，并要知道**每个适用于哪个流程、有没有必要引入**。

**用户回答：** 同上（即本条本身就是用户的指令）。
**结论：** **待调查**。已把本项目的 11 条已知缺口作为判据下达（无中国本地化 / 译名撞名 914 组 / 导航重排 / 图纸版本与通知 / SPC·CPK / 模具工装 / 计件工资 / 质检·外协·月结未覆盖 / 无排产优先级与换型时间 / 打印版式未评估 / 远期 React），要求逐条判断生态里有没有现成 app 能补，并单列一节「只能自己开发的缺口」。重点点名查 `hrms`（对缺口 7 计件工资）、`insights`（BI，可能兼补中国财报格式）、`print_designer`（打印版式）、`drive`（图纸版本管理）、`helpdesk`（售后，当前不在 23 环节内）。

**⑤ 本轮的流程动作**

**提出者：** Claude
**背景：** R1 记录已 **1799 行**，超讨论契约 §2 纪律 10 的 1700 行分卷阈值，且 R1 的第七个议题（需求关系）已收口，**分卷点落在议题边界上**，合规。

**结论：** 三个动作已完成——① 建 `R02-图谱讨论续/` 与本卷（自第 21 步起，头部写承接说明）；② 落档开关改指本卷、`turnStartMax=20`（按契约 §7「分卷时」）；③ 五路 Agent 并行派出，报告各落本 Round 文件夹：`P1-S2-R2-A调研-FrappeCRM.md` / `-Raven.md` / `-Flow.md` / `-接入机制.md` / `-工业生态App.md`。

**用户另有一项排序指令**：**五路调查全部回来之后，再一并解决 R1 遗留问题**（Stage 概况「本 Round 待决项」五条 + 「⚠ A 步暴露的、须带往下游的事」17 条中本步该处理的部分）。故本轮不动那些遗留项。

**⚠ 讨论中发现：R1 的需求分级可能需要整体重排。** 新增的 CRM 漏斗、Flow、Raven 三项若进范围，R1 定的「8 条核心 / 3 条重要 / 2 条增强 / 2 条实验性 / 2 条暂缓」结构会变——尤其**"给客户演示 AI"是一个新的演示目标**，它与 R1 定的定位（可信度优先 A：客户看到的每个界面都是上线后要用的那个）**可能有张力**：AI 演示若依赖外部 LLM 与付费密钥，它就未必是"上线后要用的那个"。该张力待调查结果回来后单独提给用户裁决。

**⑥ 调查回报（一）：Flow 已认准 —— `frappe/flow_client`**

> 本格是第 21 步的后续追记（无新对话轮，按讨论契约 §7 合法例外第 3 项「本轮是在修正既有步骤而非新轮」）。Agent 报告全文见 [P1-S2-R2-A调研-Flow.md](P1-S2-R2-A调研-Flow.md)，浅克隆在 `Reference/flow`（该目录已被 `.gitignore` 排除）。

**提出者：** Claude（Agent 调查回报）

**认定结论**：**Flow = `github.com/frappe/flow_client`**，安装后 app 名即 `flow`，官方定位「AI agents for Frappe」。

四个候选的排除已完成：

| 候选 | 判定 | 证据 |
|---|---|---|
| `frappe/flow` 仓库 | **不存在** | GitHub API 返回 **404**（Claude 自验复现）；`frappe` 组织公开仓库分页取全 5 页无 `flow` |
| `frappe/flow_client` | **✅ 即此** | `flow/hooks.py:1` 为 `app_name = "flow"`（Claude 自验），README 标题即 `# Flow` |
| 框架内置 `Workflow` DocType | 排除 | 非 AI。**但若用户本意是「审批流」，那就是它，本来就在框架里、不需引入任何 app** |
| frappe.io 产品页 / PyPI `frappe-flow` / 第三方 `Frappe-FlowAgent` | 排除 | frappe.io `/products` 全文独立单词 `flow` 命中 0 次、`frappe.io/flow` 404；PyPI 那个是同作者的独立 CLI，依赖里无 frappe |

**改名痕迹两处内证**：`README.md:8` 的 CI badge 仍指 `github.com/frappe/flow`；`flow/patches/rename_ai_to_flow.py` 把 15 个 `AI *` DocType 批量改名为 `Flow *`。

**五问作答要点**（★ 标记为 Claude 自验复现，非仅采信 Agent）：

| 项 | 结论 |
|---|---|
| 开源与许可证 | **AGPL-3.0** ★（`license.txt:1-2` 实读）。**⚠ 矛盾**：**51 个** `.py` 文件头写 `License: MIT` ★（Agent 报 65，Claude 实测 `grep -rl "License: MIT" --include=*.py` 为 **51**，取实测值）。商用前须向上游澄清 |
| 版本可锁定性 | **零 release、零 tag、只有 `develop` 一个分支** ★（GitHub API `/tags` 与 `/releases` 均返回空数组，`default_branch: develop`）。73 star，最后提交 **2026-08-12** ★ |
| 依赖 | **纯 Frappe，不依赖 ERPNext**（全仓 grep `erpnext` 零命中，无 `required_apps`）。声明 `frappe >=16.0.0-dev,<18.0.0` ★，**覆盖我们的 16.34.0**；Python `>=3.14,<3.15` 与 v16 硬要求一致。**但无 v16 专用分支**，CI 只对 `frappe:develop` 跑 |
| 它做什么 | 16 个 DocType（Flow Provider / Model / Tool / Agent / Trigger / Knowledge Base / Session / Run）。AI 走 **litellm** ★（`pyproject.toml:12`），**故可换 provider**；README 明确支持 Ollama / LM Studio，**可离线、免付费 key**；向量库 **lancedb 本地落盘** ★（`:13`）。`execute` 工具是沙箱 Python，禁 import、禁 `frappe.db.sql`/`get_all`，读写走用户权限 |
| **接入形态（本项目最关心）** | **不是 SPA、也不是 desk 页面**，而是**注入 desk 的滑出覆盖面板**——靠 `app_include_js/css` 注入 ★（`flow/hooks.py:26-27`），挂到 `div#flow-root`，`ctrl+i` 唤起。**无 `website_route_rules`、无 `www/` 目录** ★（两项均自验为空）、无任何 `override_*`。后端走 7 个白名单端点 + SSE 流。不需独立进程，但依赖 scheduler + worker 队列 |
| 与 Raven 的关系 | 同属 frappe 组织但非同一团队（Raven 用官方邮箱，Flow 的 publisher 是个人名 `Shrihari Mahabal` ★）。功能部分重叠（聊天式 AI 助手）、整体互补（Raven 载体是聊天室，Flow 是 desk 面板 + 事件触发）。**可只装其一，互不依赖** |

**⚠ 讨论中发现（三条，均须带进裁决）**

1. **`doc_events` 对 `"*"` 挂了五个写事件** ★ —— `flow/hooks.py` 实读：`after_insert` / `on_update` / `on_submit` / `on_cancel` / `on_trash` 全部指向 `flow.triggers.dispatch`。**即全库每一次写操作都过它一道。** 这与「零 release 可锁定版本」叠加后是本次调查最重的一条反对理由：上游一旦回归，影响面是全库写操作，而**无已验证版本点可回退**。
2. **README 的安装命令是错的** —— 写的是 `bench get-app flow`，但 bench 对裸 app 名只探测 `frappe/` 与 `erpnext/` 两个组织，二者对 `flow` 均 404。实际须 `bench get-app https://github.com/frappe/flow_client --branch develop`。
3. **两个 apt 依赖要改 Docker 镜像** ★ —— `pyproject.toml:33` 声明 `libgl1` / `libglib2.0-0`（`onnxruntime` + `rapidocr` 的 OCR 栈所需）。这与本项目已记录的 Windows Docker 坑叠加，是额外的环境改造点。

**Agent 的建议**：**现阶段不引入，先观察。** 主要反对理由即上述第 1 条。

**Claude 对该建议的保留**：该结论合理，但**它是把 Flow 当"生产要装的 app"来评的**，而用户的需求是**给客户演示 AI**——演示环境与生产环境的风险容忍度不同（演示可用一次性环境、演示后即弃）。故不宜直接采纳"不引入"，应作为**两档选项**提给用户：① 进生产（受上述风险约束，倾向不做）；② 只进演示环境（风险大幅降低，但与 R1 定的「可信度优先 A」定位有张力——客户看到的界面本应是上线后真要用的那个）。该张力与 Raven 那路的出网/密钥条件合并后一并提请裁决。

**结论：** **Flow 已认准，待与 Raven 结果合并后一并提请用户裁决分级**。

**⑦ 调查回报（二）：工业生态 App 普查 —— 三条纠错有价值，核心推荐与 R1 裁决相撞**

> 同为第 21 步的后续追记。Agent 报告全文见 [P1-S2-R2-A调研-工业生态App.md](P1-S2-R2-A调研-工业生态App.md)。

**提出者：** Claude（Agent 调查回报）

**⚠ 首要事项：Agent 的唯一强推荐与 R1 已定裁决冲突，Claude 判定维持 R1。**

Agent 把 **`erpnext_china`（zelin-tech / gitee yuzelin）列为本次唯一强推荐引入**，理由是 19350 行补译 + 35 行 `field_property.csv` 改撞名字段标签 + 自建 6 组 DocType 做三大报表。

**但 R1 已对同一个仓库做过更深的调查并已落进 `docs/项目概况.md:119`**：「**可当词汇素材，不可当方案**」。两者证据对比：

| 项 | Agent 本次 | R1 已查（更深） |
|---|---|---|
| 译文规模 | 「19350 行补译」 | **`wc -l` 19350 是物理行**（部分译文内含换行），实际数据行 18332、唯一 source **18297**；其中与官方 v16 **完全一致 13503 条（74%）**，**真正覆盖官方的只有 748 条**。★ Claude 复验 `wc -l` 确为 19350，故 Agent 的数字不错，但**把物理行数当补译量是高估**——它不是增量表而是一份全量表，74% 与官方逐字相同 |
| 是否解决撞名 | 「直击缺口 2」 | **R1 逐条验过：四条已知缺陷只解决第 4 条（未译），前三条一条没解决**，其中缺陷 3 是逐字照抄官方的误译 |
| 译文质量 | 未评估 | **R1 查出确定译错四例**：`May`→「04」、`Work In Progress`→「进行中」、`Committed`→「已提交」、`Ledger`→「会计凭证」 |
| 配置层可靠性 | 「须先实装验证」 | **R1 已查出四处硬缺陷**：其 `一般企业会计准则(2024)` 示例配置 **144 个科目号引用命中 0 个**；四个 setup 函数全包在裸 `except` 里只写 log（建完公司看不出问题、做账时才发现）；4 张科目表 3 张有同名父子（13 处） |

**结论**：**维持 R1 定性不变——可当词汇素材，不可当方案。** Agent 的推荐不成立，因为它评估的是"有没有东西"，R1 评估的是"那些东西对不对"。**但 Agent 带来一项 R1 未注意的新料**：`setup/field_property.csv`（35 行）★ Claude 复验存在，专改撞名字段的标签与命名序列——**这是"改源词用词"这条路的现成样本**，而 R1 第 17 步刚判定撞名"只能改其中一方的用词"。该文件应作 C 步定译名方案时的素材。

**三条纠错（全属「名字像就推定」类型，与本项目 LG-067 同源，价值高）**

| # | 原推定 | 纠正 | ★ 复验 |
|---|---|---|---|
| 1 | `drive` 能补缺口 4（图纸版本管理） | **补不上**。`Drive Document Version` 字段只有 `entity/snapshot(Long Text)/title/snapshot_size`，快照的是 Drive 自带富文本编辑器的**文本**；`Drive File Update` 是活动日志子表。**它不给上传的二进制文件做版本管理**，而图纸是 DWG/PDF | 未复验（drive 未克隆） |
| 2 | `hrms` 能补缺口 7（计件工资） | **补不上**。`hrms/payroll/doctype/` 全部 44 个 DocType 无任何 piecework/piece-rate 表；本地 erpnext 全库 grep `piece.?work\|piece.?rate` 零命中 | 未复验 |
| 3 | `insights` 能补中国财报格式 / `builder` 能补缺口 3（导航） | 均补不上。Builder 做**对外网站页面**，不是 Desk Workspace | 未复验 |

**缺口 7（计件工资）的意外好消息 ★ Claude 已复验**

`Job Card Time Log` 实读字段为 `['from_time','to_time','column_break_2','time_in_mins','completed_qty','employee','operation']`，`istable:1`。**即"每个工人、每道工序、完工多少件"这三个量天然已在库里**，缺的只是「工序单价 × 完工数量 → Salary Component」这段计算与过账。**自研可行且工作量可控**——这把 `PH-P1009`（计件工资）的性质从"无 app 支撑"改为"有数据源、缺计算层"。

**另两条本地复验 ★**

- **缺口 9 确认**：`work_order.json` 与 `sales_order.json` **均无 `priority` 字段**（grep 零命中）。
- **`print_designer` 的 v16 兼容性存疑但有强反证**：其 README 明写 "only compatible with develop and V15"，**但本地 frappe 16.34.0 的 `utils/pdf_generator/browser.py:13` 已读 Print Format 的 `print_designer` 字段**（另 `:109/:257/:378/:385` 共 5 处逻辑），而**核心 `print_format.json` grep `print_designer` 为 0** ★——说明该字段是 app 经 `create_custom_fields` 加的 custom field，**即 v16 核心为它预留了集成点，README 可能只是没更新**。且它 2026-09-17/18 仍在修 bug。**列为待实装验证项，不靠读码下结论。** 代价：其 apt 依赖声明 16 个 Chromium 系统库，明显加重 Docker 构建

**必须自研的六条缺口**：4（图纸版本）、5（SPC·CPK）、6（模具工装）、7（计件工资）、9（排产优先级与换型时间）、10（打印版式，若 print_designer 实装失败）。其中 6/7/9 有原生底座可借（v16 `assets` 模块 26 个 DocType 含 asset_maintenance/asset_repair；Job Card 的 `completed_qty`；Workspace），4/5/10 从零。

**两条事实更新**：① 缺口 8 的**外协有原生底座**——v16 `subcontracting/` 14 个 DocType，含新增的来料加工 `subcontracting_inward_order` 系列；② `frappe/healthcare` 已迁出官方组织，现为 `earthians/marley`（API 301）。

**ECOSIRE 全系列不可用**：其功能清单（Shop Floor MES / SPC / Tooling-Mold / Barcode-RFID / Andon / IIoT / CMMS / APS）正好覆盖缺口 5/6/9，但**无仓库无源码、闭源收费 from $999、按单定制**。只当需求参照，不当可装的 app。

**已停维护或不兼容 v16**：`frappe/assets`（2022-03，且 v16 核心 assets 模块已覆盖）、apparelo（archived）、ERPNext-Frepple-Integration（2022-02，但证明"外挂 frePPLe 做排产"这条路有人走过）、hospitality（2023）、non_profit（archived）、pasigono（停在 v14）、agriculture。

**一条值得下轮查的**：`frappe/erpnext_price_estimation`（官方 MIT 57★ 2026-07-03）——名字贴合"弹簧按线径/材质估价"，**Agent 未核实其模型故不做推荐**。

**结论：** **本路唯一"该引入"的推荐被否**（维持 R1 对 zelin 的定性）；**三条纠错与两条本地复验纳入依据**；`print_designer` 与 `erpnext_price_estimation` 两项列入待验；**缺口 7 的性质改判**（有数据源、缺计算层）。

**⑧ 调查回报（三）：Raven 与 Frappe CRM —— 主 Session 亲自重查**

> 同为第 21 步的后续追记。报告见 [P1-S2-R2-A调研-Raven.md](P1-S2-R2-A调研-Raven.md)（204 行）与 [P1-S2-R2-A调研-FrappeCRM.md](P1-S2-R2-A调研-FrappeCRM.md)（228 行）。

**提出者：** Claude

**⚠ 产出方式异常，须记录**：这两路子 Agent **均完成调查但两次在"写报告"这一步 API 超时中断**，报告始终未落盘（CRM 第二次是网关 503：`分组 aws-q 下模型 claude-opus-5 无可用渠道`）。判定其上下文过重、再续仍会断，故**由主 Session 依本地克隆亲自重查并书写**。故这两份报告的可信度高于同批其它报告（无"采信 Agent 转述"的衰减），但覆盖面窄于原计划。

**用户中途提示**：「如果文件太长，尝试分多段写入」。该提示正确且有效——改为分段 `cat >>` 后两份报告均一次落盘成功。**此为本 Round 的方法论收获，值得带往后续所有长报告任务。**

**一、Raven（`The-Commit-Company/Raven`，AGPL-3.0）**

| 项 | 结论 |
|---|---|
| v16 兼容 | `frappe >=15.0.0,<=17.0.0-dev` ★ 覆盖 16.34.0 |
| **AI 可换 provider** | **✅ 能接国内模型**。`raven_settings` 有 `enable_local_llm` / `local_llm_provider`（取值 `LM Studio`/`Ollama`/`LocalAI`/**`OpenAI Compatible`**）/ `local_llm_api_url` ★；分派逻辑 `agents_integration.py:55-90`，本地三种**密钥直接填 `"not-needed"`**。故 DeepSeek/通义/智谱可接，**不必出网、不必付费** |
| **但有能力损失** | `agents_integration.py:350-375`：走本地模型时**过滤掉七类 hosted 工具**——含 **MCP**、联网搜索、代码解释器、文件检索，只剩自定义函数调用 |
| MCP | 全仓 grep `mcp` **仅两处命中**，来自 `openai-agents` SDK 的 `HostedMCPTool`，**非 Raven 自建**，且走本地模型时被过滤 |
| AI 操作数据 | **18 种函数类型**（`Create Document`/`Submit Document`/`Get Report Result` 等全覆盖）。建单链路：`functions.py:24-43` `frappe.get_doc(...).insert()`；提交 `:110-121` `doc.submit()` |
| **权限模型（关键）** | **✅ 不放宽**。`grep -rn "ignore_permissions" raven/ai/` **零命中** ★；`doc.insert()` 未传绕过参数；执行身份 `frappe.session.user`（`handler.py:311/:396/:419`）。**AI 以发起者身份执行** |
| realtime | **46 处** `publish_realtime` ★。`realtime/` 下只有 `handlers.js` 一个文件，**不另起进程**；推送中继可选 |
| ⚠ hook 侵入 | **`doc_events` 挂 `"*"` × 5 个写事件**（`hooks.py:131` 起）★，与 Flow 同型。另挂 `User`/`Department`/`Employee`（后两个来自未装的 hrms）。**无** `override_whitelisted_methods`、**无** `override_doctype_class` |
| 演示硬前置 | 8 条（见报告 §7）。**最大未知是第 7 条**：国内端点在 `use_responses=False`（chat/completions）路径下 function calling 是否稳定，**必须实跑**——若不稳，"AI 建出一张销售订单"这个演示不成立 |

**二、Frappe CRM（`frappe/crm`，AGPL-3.0，官方公司实体 publisher）**

| 项 | 结论 |
|---|---|
| v16 兼容 | `frappe >=16.0.0-dev,<=17.0.0-dev` ★ —— **明确面向 v16**，信号强于 Flow |
| **术语纠正** | **「客户漏斗」非标准术语**。行业通用是**销售漏斗 / 销售管道（pipeline）**；而 CRM 自己既不叫 funnel 也不叫 pipeline，**漏斗由 `CRM Deal` + `CRM Deal Status` 的状态序列隐含表达** |
| **漏斗形态** | 七档带**概率**★（`install.py:91-135`）：Qualification 10% → Demo/Making 25% → Proposal/Quotation 50% → Negotiation 70% → Ready to Close 90% → Won 100% / Lost 0%。**`probability` 字段是漏斗成立的关键**（使金额×概率的加权预测可算）。另有 Lead 五档在前：New → Contacted → Nurture → Qualified → Converted |
| DocType 撞名 | **✅ 不撞**。39 个 DocType 全带 `CRM ` 前缀 ★（`CRM Lead` 而非 `Lead`，**`CRM Deal` 而非 `Opportunity`**）。代价是**同一客户有两份记录**（`CRM Deal` 与 `Customer`），靠同步而非共表 |
| **⚠ 与 ERPNext 联动（推翻预设）** | **原设问"若无联动则两套数据互不相通"不成立**。有专门的 `ERPNext CRM Settings` DocType ★，三条实际机制：① `erpnext_crm_settings.py:75-80` 建 Property Setter 把 **`CRM Deal` 加进 `Quotation.quotation_to` 的可选范围**；② `:125-136` 给 `Quotation`/`Customer` 加 custom field（异站模式经 API 远程建）；③ `:181-200` 装表单脚本「**Create Quotation from CRM Deal**」——**Deal 页面有按钮直接生成 ERPNext 报价单**。另支持 CRM 与 ERPNext **异站部署**（`api_key`/`api_secret`/`is_erpnext_in_different_site`） |
| **故演示线可延伸** | `Lead → Deal → 报价 → 接单 → …… → 收款`，**衔接点是 Quotation**，正接在 23 环节闭环起点「接单」之前 |
| ✅ hook 侵入性低 | `doc_events` **只挂 `Contact`/`Notification Log`/`ToDo` 三个具体 DocType**★（`hooks.py:240` 起），**不是 `"*"`** —— 显著优于 Flow 与 Raven。**无** `override_whitelisted_methods`（`:343` 注释掉）→ **不与本项目中国本地化方案冲突** |
| ⚠ 次要顾虑 | `override_doctype_class` **覆盖核心 `Contact` 与 `Email Template`** ★（`hooks.py:231-234`）。**未读那两个 override 的实现，影响面未知**——最该补查的一条 |
| **⚠ 最硬的反对理由** | **自带中文翻译 1782 条 msgid、689 条空 `msgstr`、未译率 38.7%** ★（`crm/locale/zh.po` 实测）。**这直接撞 `PH-P1001`**——用户原话「不应该出现有些翻译了有些没翻译的情况」。装 CRM 等于**在演示里引进一块 39% 未译的界面，且译名工作量凭空加 689 条**，与「可信度优先」定位冲突 |

**三、⭐ 本路的附带收获：React 接入链路已有答案素材**

用户战略问题（React 重写能否同样接入）的**机制层答案在 CRM 的构建配置里** ★：

| 环 | 机制 | 依据 |
|---|---|---|
| 路由 | `website_route_rules = [{"from_route": "/crm/<path:app_path>", "to_route": "crm"}]` —— **`<path:...>` 通配吃掉 SPA 深链接故不 404** | `hooks.py:74-77` |
| 构建三键 | `build_dir = ./frontend` / `out_dir = ../crm/public/frontend` / **`index_html_path = ../crm/www/crm.html`** | `pyproject.toml:35-38` |

**关键判断**：这三个键只关心"源码在哪、产物出哪、index.html 放哪"，**不关心用 Vue 还是 React**；`<path:>` 通配同理。**故 React 前端能走完全一样的路**——做成 Frappe app、`frontend/` 放 React 源码、配同样三键、声明 `website_route_rules`。

**⚠ 但这是读码推断，未实做**。且 **CRM 仓库内有 `frappe-ui` 目录**，说明它把 frappe-ui 当源码级依赖——若 React 要复用其数据层可能有 Vue 耦合，**未展开查**（属接入机制那一路）。

**四、三个候选的横向对照（供裁决）**

| 维度 | CRM | Raven | Flow |
|---|---|---|---|
| 许可证矛盾 | 无 | 无 | **51 个 py 头写 MIT vs 根 AGPL** |
| publisher | **官方公司实体** | 官方邮箱 | 个人名 |
| v16 信号 | **`>=16.0.0-dev` 明确** | `>=15.0.0` 覆盖 | 仅 CI 对 develop |
| 可锁版本 | 仅 develop 分支 | （未核） | **零 release 零 tag** |
| **hook 侵入** | **✅ 三个具体 DocType** | ⚠ `"*"` × 5 | ⚠ `"*"` × 5 |
| 覆盖核心类 | ⚠ `Contact`/`Email Template` | 无 | 无 |
| **译名未译率** | **⚠ 38.7%** | 未查 | 未查 |
| 额外环境改造 | 无 | 无需新进程/端口 | **需改 Docker 镜像** |

**结论：** 三路均已落档。**CRM 技术上最该引入**（侵入性最低、联动最完整、v16 信号最明确），**但 38.7% 未译率是硬伤**，须作两档选项提请用户裁决：甲＝装并把 689 条补译纳入 `PH-P1001`；乙＝不装、漏斗现场口头说明（与质检/外协/月结同处置）。**Raven 优于 Flow**（官方信号、无许可证矛盾、无需改镜像三项占优，离线能力两者皆有），但"聊天式 vs desk 内助手式"的演示形态差异属产品判断，须用户定。

**⑨ 调查回报（四）：官方三 App —— Helpdesk / HRMS / Insights（用户中途追加）**

> 同为第 21 步的后续追记。报告见 [P1-S2-R2-A调研-官方三App.md](P1-S2-R2-A调研-官方三App.md)（441 行）。克隆在 `Reference/{helpdesk,hrms,insights}`（insights 需代理才通）。

**提出者：** 用户（本轮中途追加「还想要接入 Frappe Helpdesk、HR、Insights，把这几个也加入调研」）

**⭐ 本路质量高于前几路**，且**复用了前五路磨出的统一检查项**——尤其「译名未译率」这一项，因 CRM 的 38.7% 已成最硬反对理由，故它升为筛选 app 的第一道闸。

**一、译名未译率（第一道闸，两差一优）★ Claude 抽查确认量法**

| App | msgid | 未译 | **未译率** | vs CRM 基准 38.7% |
|---|---|---|---|---|
| **HRMS**（version-16） | 2172 | **42** | **1.9%** | **远好** —— 本轮唯一在 `PH-P1001` 上站得住的 |
| CRM（基准） | 1782 | 689 | 38.7% | — |
| **Helpdesk** | 1379 | 649 | **47.1%** | **差 8.4 点** |
| **Insights**（develop） | 686 | 331 | **48.3%** | 差 |
| **Insights**（`version-3`） | 686 | 482 | **70.3%** | **本轮最差** |

两条附注：① Insights 存在**"选有 tag 的稳定分支"与"选译名好些的分支"互相矛盾**的困境；其 develop 未译词含 **`Data Source`**——它自己最核心的概念。② HRMS 那 42 条未译全是财务/休假边缘校验提示。③ 计数用了能处理 po 多行续行的脚本，裸 `grep -c '^msgstr ""$'` 会高估。

**二、⭐ 计件工资的判断被改写 ★ Claude 亲自复验**

R2 前段刚把 `PH-P1009` 从"无 app 支撑"改判为"有数据源、缺计算层"。本路**又推进一层，把问题的性质整个换掉**：

| 查证 | 结果 |
|---|---|
| hrms payroll 有无计件表 | **无**。43 个 DocType（Agent 数 43，此前记 44，差 1 不影响结论），`grep -Ei "piece.?work\|piece.?rate"` 在 `.py`/`.json` **零命中** ★ |
| 唯一 `Piecework` 命中是什么 | **`setup.py` 里 `Employment Type` 的一个候选值名** ★，**不是计算逻辑**——又一例"名字像≠有能力" |
| **⭐ 新硬依据** | **hrms 的薪资公式引擎读不到自定义数据** ★ —— `payroll/utils.py` 的 `COMPONENT_EVAL_GLOBALS` **只白名单 13 个数学/日期函数**（`int`/`float`/`round`/`rounded`/`date`/`getdate`/`get_first_day`/`get_last_day`/`ceil`/`floor`/`min`/`max`/`long`），**无 `frappe`、无 `frappe.db`、无 `get_doc`** ★。可见数据仅 Employee 字段 + SSA 字段 + 其它组件金额（`salary_slip.py:1358-1381`），另有 AST 黑名单（`utils.py:102-121`） |

**故结论**：「完工件数 × 工序单价」**在 hrms 里也写不出来**，必须在外面算好再用 `Additional Salary` 整笔塞进 Salary Slip。**既然"算"这步两条路工作量一样，就没理由为它承担 160 个 DocType + 4 个核心类覆盖。**

**⭐ 决策点因此改变**：不是「计件怎么算」，而是「**要不要整套 HR**」。这是本路最有决策价值的一条。

**三、⚠ HRMS 的 develop 已进 v17，装不上本项目 ★ Claude 复验**

`Reference/hrms/pyproject.toml` 末两行实读：`frappe = ">=17.0.0-dev,<18.0.0"` / `erpnext = ">=17.0.0-dev,<18.0.0"`；`hrms/__init__.py:6` = `17.0.0-dev` ★。**须用 `version-16` 分支**（Agent curl 核过：`frappe = ">=16.0.0,<17.0.0"`）。**将来往 `docker/apps.json` 加条目时 `branch` 必须写 `version-16`。**

**四、hook 侵入性排序（六 app 全景）**

| App | `doc_events` | `override_doctype_class` |
|---|---|---|
| Raven / Flow | ⚠ **`"*"` × 5 个写事件** | 无 |
| **HRMS** | ⚠ **28 个具体 DocType**，含 `Company`/`Journal Entry`/**`Payment Entry`**/`Holiday List` | ⚠ **`Employee`/`Timesheet`/`Payment Entry`/`Project`** |
| Helpdesk | 6 个，含 `Customer` 5 事件 + `User Permission`/`DocShare` | `Email Account`/`Assignment Rule`/`User Invitation` |
| CRM | 3 个具体 DocType | `Contact`/`Email Template` |
| **Insights** | **1 个**（`User.on_change`）—— **本轮最低** | **无** |

**⚠ HRMS 的最大风险**：`doc_events["Company"]["on_update"]` 会跑 `set_default_hr_accounts`，**可能往本项目已定型的 95 科目里新增 HR 科目**——与正在做的科目表工作直接相邻。另 `Payment Entry` 被覆盖，**正压在 23 环节闭环的「收款」上**。

**五、✅ 本项目两个关切点全部无冲突（重要的否定性结论）**

| 关切 | 结论 |
|---|---|
| `override_whitelisted_methods` | helpdesk 仅 1 条 `frappe.realtime.has_permission`（**不是**科目表模板那个方法），hrms 与 insights 均注释态 → **V-03 方案（自制科目表模板送进建公司下拉）不会被抢** |
| `regional_overrides` | **只有 hrms 有**，且只注册 `India` 键下 3 个 HRA/税函数。`erpnext/__init__.py:145-152` 是**先按区域取 dict、再对同名 function_path 取 `[-1]`**，**区域键与函数路径两层都不相交** → **不争末位** |

**六、Employee/Department/Holiday List 的归属查实**

**归 erpnext，不归 hrms**（`erpnext/setup/doctype/{employee,department,holiday_list,designation}` 存在；hrms 下同名目录零命中）。**但装 hrms 会改行为**：`Employee` 类被 `EmployeeMaster` 替换，并往 **8 张 erpnext 主表**加 custom field。

**七、Insights 不改变现金流量表的原结论**（四条依据）

① `grep -i "gl_entry"` 零命中——**它不认识会计语义**；② 图表类型固定 9 种（`frontend/src2/types/chart.types.ts:5-18`），中国现金流量表的分组/缩进/小计层级**只能退化成一张 Table**；③ 它只能查已归类的数据、**不能替你把现金收支归到现金流量项目**（而这正是原方案"自建可提交单据"的由来）；④ v16 的 `Financial Report Template` 仍是更对的工具。

**⚠ 另两条对演示的实质限制**：① 它**把源表导入** `{private files}/insights.duckdb` 再查（`data_warehouse.py:68`），**看板数据不实时**——演示"实时产量"会露馅；② `fixtures` 只导一条数据源，**零预置仪表盘**，四张图全要从零建。另：`connectors/frappe_db.py:20-45` 读 `frappe.conf` 凭据**直连 MariaDB、绕过 Frappe 权限层**（另做 `Insights Team` 权限）。**故演示看板应走 ERPNext 原生 Dashboard Chart / Number Card。**

**八、Helpdesk 的三个隐性成本 ★ 第一条已复验**

① **`required_apps = ["telephony"]`** ★ → **连带装第二个 app** `frappe/telephony`；② `after_migrate` 会 `download_corpus()`（`helpdesk/search.py:378-388`）**联网下 NLTK 语料**——Windows Docker + 代理环境下是明确的新增外网依赖；③ develop 要 **`requires-python >= 3.14`**（`main-hotfix` 才是 py>=3.10 / frappe>=15.116.1,<17.0.0），**而本项目容器 Python 版本本次未查实**，须在决定装之前先核。

**售后能力按字段判**：`HD Ticket` 有 subject/priority/status/sla/response_by/feedback_rating，**能承载投诉受理与时限跟踪**；但**无任何物料/批次/数量字段**，无到 `Item`/`Batch`/`Serial No`/`Work Order`/`Quality Inspection` 的 Link。**故它是投诉工单台账，不是质量追溯系统**——断簧追溯（料→工序→工人→批次）它补不上。

**九、许可证（helpdesk 有矛盾，须报）**

| App | 许可证 | 矛盾 |
|---|---|---|
| Helpdesk | 根 `LICENSE:1` AGPL-3.0 | ⚠ **3 处 .py 写 `# MIT License. See license.txt`，而仓库里根本没有 `license.txt`**；另 4 个 .py 写 GPL v3 |
| HRMS | **GPL-3.0**（不是 AGPL，`license.txt:1`） | 688 个 .py 里仅 2 个写 MIT |
| Insights | AGPL | **干净**（0 个 MIT 头） |

**十、DocType 撞名：三个全部零撞名**（实跑 `comm -12` 对本地 erpnext 532 + frappe 285）。策略：helpdesk 全 `HD ` 前缀、insights 全 `Insights ` 前缀（同 CRM）；**hrms 不加前缀**，靠"这些表本来不在 erpnext 里"避免撞名。

**十一、⭐ 附带收获：React 接入结论被修正（比 CRM 单样本更准）**

四个样本（CRM + 本轮三个）的 `website_route_rules` **全部用 `/前缀/<path:app_path>` 通配**，机制与前端框架无关——**此点得到四样本支持**。

**但修正一处**：**`[tool.bench.assets]` 三键并非必需** —— hrms 与 insights **都没有这一段**，改用 `www/*.py` 页面控制器 + 根 `package.json` 自建产物。**故三键只是"让 bench 帮你 build"的糖。** 换 React 的代价是**失去 frappe-ui 组件库，不是要改挂载链路**。（此前从 CRM 单样本得出的"配同样三键"表述因此收窄。）

**十二、其它**：三个 app **全部无 `[deploy.dependencies.apt]`**（不用改 Docker 镜像装系统库）。`publish_realtime` 计数：helpdesk 8 / hrms 11 / insights 5，**都远低于 Raven 的 46**。

**结论：三个都不进客户演示。** 理由各异——Helpdesk 与 Insights 的未译率比已被否的 CRM 更差；HRMS 译名过关（1.9%）但**功能不在 23 环节闭环上**（闭环里没有考勤/休假/工资单），且它是本轮侵入性最高的一个，恰好压在本项目正在建设的两处（`Company` 科目体系、`Payment Entry` 收款）——**为演示装它等于给闭环加风险却不加闭环内容**。

进生产的判定：Helpdesk ⚠（售后单独立项后）；**HRMS ✅ 条件性**（要整套 HR 时，装 `version-16`）；Insights ⚠（数据积累后有自助取数需求时）。

**⚠ 未实跑（10 条，报告已单列）**：三个 app 全部未 `bench install-app`，`after_install` 副作用均为读码推断；**Insights 的 duckdb/ibis 在 Windows Docker 的可安装性完全未验证**（属本项目高风险依赖类型）；容器 Python 版本未查实（影响 helpdesk 分支选择）；未译率是静态度量、真实观感须装上走一遍 23 环节；三个 app 的卸载干净度全未测。

**⑩ 调查回报（五）：realtime 能否驱动界面 —— 主 Session 亲自查证**

> 同为第 21 步的后续追记。报告见 [P1-S2-R2-A调研-接入机制-realtime.md](P1-S2-R2-A调研-接入机制-realtime.md)（150 行）。

**提出者：** Claude

**⚠ 产出方式异常（第五次同型失败后的处置）**：接入机制这块原派一路（六问），因报告体量过大在"写报告"这一步中断；按用户指示拆为三路重派，**三路又在上个 Session 结束时全部中断、报告均未落盘**。**全批七个 Agent 里五个同型失败**（调查完成、报告丢失）。故判定不再派 Agent 查此问，**由主 Session 亲自查证**最关键的一问（realtime），余三块另派收窄指令的小 Agent。

**一、⭐ 六档判定（选甲还是乙的分水岭）**

| 档 | 能力 | 现成机制 | 依据 ★ 全部 Claude 直接读码 |
|---|---|---|---|
| (a) | 弹提示消息 | **✅ 开箱即用** | `socketio_client.js:76-77` 内置 `socket.on("msgprint", msg => frappe.msgprint(msg))` |
| (b) | 刷新列表/表单数据 | **✅ 开箱即用** | 列表 `list_view.js:1757` `list_update` → `debounced_refresh()`；表单 `model.js:154` `doc_update` → `cur_frm.debounced_reload_doc()` |
| (c) | 跳转路由 | **⚠ 仅一种窄情形** | `form.js:339-344` `doc_rename` → `frappe.set_route("Form", doctype, data.new)`，**只在"当前表单被后台改名"时触发**，无通用"跳到 X"事件 |
| (d) | 打开指定单据 | **❌ 无内置** | 20 个订阅点中无一个做此事 |
| (e) | 往表单字段填值 | **❌ 无内置** | 同上 |
| (f) | 点按钮/触发动作 | **❌ 无内置** | 同上 |

**故现成机制到 (b) 为止。** 已把 **20 个订阅点**（15 个 `realtime.on` + 5 个 `socketio_client.js` 内直接 `socket.on`）逐个查过处理器实现，**共性是全在"刷新数据"或"提示消息"，无一在"执行操作"**——**数据层（事件抵达）与渲染层（处理器实现）两层都有依据**，符合 LG-067 的取证要求。

**二、⭐ 一条使能事实，改变了结论性质**

`socketio_client.js:12-17` 实读：`realtime.on(event, callback)` 只是 socket.io 原生 `socket.on` 的**薄包装，对事件名无白名单、无校验**；服务端 `publish_realtime` 的 `event` 亦为自由字符串（`realtime.py:23-41`）。

**故 (d)(e)(f) 不是"框架不支持"，而是"框架没预置这个用途的处理器"** —— 自注册一个自定义事件监听即可，**不必改 frappe 源码**。**这把选项甲从"要改框架"降为"要写一段监听"。**

**三、推送侧的定向能力（对演示脚本关键）**

`publish_realtime` 签名（`realtime.py:23-41`）含 **`user`**（推给指定用户）、`room`（默认整站）、`doctype`+`docname`、**`after_commit`**（默认 `False`）。

**两条对演示的直接含义**：① 可精确推给"正在演示的那个浏览器会话所属用户"，不惊动其它人；② **`after_commit=True` 必须用**——否则可能事件先到、数据后落库，界面刷新时取到旧数据。

**四、甲乙两选项的重新评估**

**甲成立，且比 R1 估计的更划算。** 代价分档：只做 (c)(d) 约 20-30 行；加 (e) 约 +20 行；加 (f) 约 +30 行（走 `cur_frm.save()`/`savesubmit()` API 而非模拟 DOM 点击）。监听代码写在**自有 app 的 `app_include_js`**——与 Flow 同型（Flow 就是靠它注入 desk 覆盖面板）。

**⭐ 查出第三条路**：**(f) 那档不必真的"点"** —— `cur_frm` 暴露 `save()`/`savesubmit()`，故"提交单据"是监听器**直接调方法**，不是模拟点击，**脆性大幅降低**。

**⚠ 但须与用户讲清一件事**：这样客户看到的是"**界面自己完成了操作**"，不是"**鼠标自己在动**"。若用户期待后者（光标移动、按钮高亮），须另做且脆性高得多。**此条待用户确认期待形态。**

**⚠ 两处收窄 R1 的表述**：

1. **"MCP 与 React 都能复用"说宽了** —— 复用的是**事件协议与推送侧**，**前端监听那段 React 要重写**（它是针对 desk 的 `cur_frm`/`frappe.set_route` 写的，React 有自己的路由与表单状态）。
2. **乙比 R1 估计的更差** —— 乙要满足"可从任一节点起跑"，**仍需服务端先把数据造到那个状态**，故并不比甲少一半工作；省下的只是那 20-30 行监听，却失去推送侧复用性。

**五、⚠ 一条现场风险（必须进演示纪律）**

realtime 断连是**静默**的。演示时若断了，症状是「**脚本在跑、界面不动**」，且**当场分不清是脚本没跑还是 realtime 断了**（`socketio_client.js:72` 有 `connect_error` 处理器但界面只是不再更新）。

**故选项甲必须配一条演示前的心跳自检**：推一个事件、前端收到后回显，确认链路通再开始。本项目已有两标签页验法可用。

**结论：** **选项甲成立且更优**，代价 20-80 行监听代码（视要做到哪一档），不必改 frappe 源码。**待用户裁决两件事**：① 期待的是"界面自己完成操作"还是"鼠标自己在动"；② 要做到六档里的哪一档（这决定代码量与演示观感）。

**六、本轮仍未查的三块（已派收窄指令的小 Agent）**

| 块 | 要答什么 | 优先级 |
|---|---|---|
| REST API v2 | 路径清单、v1/v2 差异、**建单+提交的最小调用序列**（含 `sales_order.json` 的 `reqd:1` 字段） | 高——演示脚本要用 |
| 认证与 CSRF | **api key 是否豁免 CSRF**、外部脚本能否影响已打开的 desk 会话（两层：以自己身份 publish 给演示用户 / 复用浏览器 cookie） | 高——决定脚本复杂度 |
| **`get_hooks()` 合并顺序** | **装新 app 会不会把自有 app 挤出 `regional_overrides` 的 `[-1]` 末位**；四类 hook 多 app 并存时累加还是后者胜出 | **最高**——本项目特有风险 |

**末位风险已有一条间接缓解证据**（官方三 App 报告第五节）：六个候选 app 里只有 hrms 有 `regional_overrides` 且只注册 `India` 键下 3 个函数，**区域键与函数路径两层都不相交** → 就这六个而言不争末位。**但"合并顺序由什么决定"这个机制本身仍未查清**，故无法排除将来装别的 app 的风险。

#### 第 22 步：六路调查合并、需求分级重排提案、四项裁决点摆出

**来源项目：** ERX-001
**适用面·状态：** 仅本项目·提出

**① 用户指令：三块各派一路，然后合并并摆出裁决点**

**提出者：** 用户
**背景：** 接入机制余三块（API v2 / 认证 CSRF / hook 顺序）此前因 Agent 五次同型失败未查。用户指令：派子 Agent 查这三块，**然后把六路调查合并、把需求分级重排和裁决点摆出来**。

**用户回答：** 即本条指令本身。
**结论：** 三路已派（收窄指令、报告限 120-130 行、写盘策略前置为"查够就停、先落盘再补"）。**合并不等三路** —— 那三块答的是"怎么做"（API 路径 / 认证方式 / hook 顺序），**不影响"做不做、什么优先级"**。唯一可能翻盘的是末位风险，而它已有间接缓解证据。

**② 认证与 CSRF 已查回（三路之一）**

**提出者：** Claude（Agent 回报 + 主 Session 复验）
**背景：** 演示脚本要从外部让客户眼前那个已打开的界面动起来，须先定认证路径。报告见 [P1-S2-R2-A调研-接入机制-认证CSRF.md](P1-S2-R2-A调研-接入机制-认证CSRF.md)。

**⚠ 一处机制更正（Agent 表述不准，主 Session 复验后改写）**：Agent 称"api key 豁免 CSRF"，**但豁免是偶然的、不是设计的**。

★ Claude 复验的执行顺序：`app.py:139` 调 `init_request()`，而 `HTTPRequest()`（内含 CSRF 校验）构造在 `app.py:242`、属 `init_request` 内部，**故 CSRF 校验跑在 `validate_auth()`（`app.py:141`）之前**——那时 api key 尚未识别、会话仍是 Guest。而 `validate_csrf_token`（`auth.py:81-97`）的短路条件含 `not (saved_token := frappe.session.data.csrf_token)`，**Guest 会话无 csrf_token 故直接返回**。

**真正的机制**：**不带 cookie 的干净客户端 → Guest 会话 → 无 saved token → 短路放行。** api key 并未被特别豁免。

**⚠ 该区别有实际后果**：脚本一旦带上有效 `sid` cookie，`saved_token` 就存在 → **CSRF 立即强制校验**，且 api key **顶不掉身份**（`auth.py:743-744` ★ 实读：只在当前 user 为 `""` 或 `Guest` 时才 `set_user`）。**故"干净客户端"不是建议而是硬要求。**

**另一条已证实** ★：`publish_realtime` **无 `@frappe.whitelist()`** —— `realtime.py` 内仅 `:118`（`has_permission`）与 `:142`（`get_user_info`）带装饰器，两者均 `allow_guest=True`。**故不能直接调 `/api/method/frappe.realtime.publish_realtime`，必须在自有 app 里包一层。**

**结论（演示脚本的技术路径已定）：** 专用 API 用户 + `Authorization: token key:secret`，**干净客户端不带 cookie**，调自有 app 的 whitelisted 方法，方法内 `publish_realtime(event=..., user="演示用户")`。**不需处理 CSRF，不开 `ignore_csrf`**（后者是站点级安全洞，`auth.py:85`）。

其余要点：四种认证方式统一入口 `validate_auth()`（`auth.py:629-652`）；CSRF 判据是**方法而非路径**（`UNSAFE_HTTP_METHODS = {POST,PUT,DELETE,PATCH}`，`auth.py:29` ★）；token 下发**不是 meta 标签**而是内联 script 全局变量 `frappe.csrf_token`。**未实跑**：全部为静态读码，未发过真实 HTTP 请求；`session_ip`/`user_agent` 是否参与拒绝复用未查实。

**③ ⭐ 六路调查合并：十一个 app 的筛选结果**

**提出者：** Claude
**背景：** 本 Round 共查 11 个 app（CRM / Raven / Flow / Helpdesk / HRMS / Insights / erpnext_china / drive / builder / print_designer / 及工业生态普查涉及的其它），须给用户一份可裁决的汇总。

**筛选卡在两道闸上**（两道闸本身是本 Round 磨出来的方法论产物）：

**第一道闸：译名未译率**（对应 `PH-P1001`，用户原话「不应该出现有些翻译了有些没翻译的情况」）

| App | 未译率 | 判定 |
|---|---|---|
| **HRMS**（version-16） | **1.9%**（42/2172） | 唯一过闸 |
| CRM | **38.7%**（689/1782） | ⚠ 硬伤 |
| Helpdesk | **47.1%**（649/1379） | ❌ 比 CRM 差 8.4 点 |
| Insights develop / `version-3` | **48.3% / 70.3%** | ❌ 最差 |

**第二道闸：hook 侵入性**

| App | `doc_events` | 覆盖核心类 |
|---|---|---|
| Insights | 1 个（`User.on_change`） | 无 |
| CRM | 3 个具体 DocType | `Contact`/`Email Template` |
| Helpdesk | 6 个 | 3 个 |
| HRMS | **28 个**，含 `Company`/`Payment Entry` | **4 个，含 `Payment Entry`** |
| Raven / Flow | **`"*"` × 5 个写事件** | 无 |

**④ ⭐ 需求分级重排提案（产物快照，完整形态）**

R1 原定：8 核心 / 3 重要 / 2 增强 / 2 实验性 / 2 暂缓。**本提案的增量**：

| 动作 | 项 | 理由 |
|---|---|---|
| **进核心（+1）** | **第 8'' 项：演示脚本的最小操控机制**（从 R1 的"够演示用"**升格**） | realtime 六档判定已证甲成立、只需 20-80 行监听、不改 frappe 源码；且它同时是 React 重写的**推送侧基建**（复用面已查清：复用事件协议与推送侧，前端监听 React 要重写） |
| **进重要（+1）** | **CRM 销售漏斗** | 不进核心——它的 689 条未译**直接撞最高优先级需求** |
| **进实验性（+1）** | **AI 演示（Raven 二选一）** | 不进核心也不进重要——**最关键前置未验**：国内端点在 `use_responses=False` 路径下 function calling 是否稳定。**不验掉不能向客户承诺演示 AI** |
| **明确不进本次范围** | Flow（零 release 零 tag + `"*"` hook + 要改 Docker 镜像）；Helpdesk / Insights（未译率比已否的 CRM 更差）；HRMS（译名过关但功能不在 23 环节闭环上，侵入性最高且压在科目体系与收款两处）；`erpnext_china`（维持 R1 裁决） | 见两道闸 |
| **一条性质改判** | **`PH-P1009` 计件工资**：从"无 app 支撑" → "**有数据源、缺计算层，且装 hrms 也帮不上**" | hrms 的 `COMPONENT_EVAL_GLOBALS` 只白名单 13 个数学函数、读不到自定义数据 ★。**决策点变成"要不要整套 HR"** |

**⑤ 四项裁决点（已摆给用户，待回答）**

| # | 裁决点 | 选项 | Claude 倾向 |
|---|---|---|---|
| **裁决一** | **CRM 漏斗进不进演示** | 甲＝进，演示线延伸为 `Lead → Deal → 报价 → 接单 → … → 收款`（客户自己是销售、看得懂漏斗），代价是**译名 +689 条且须演示前补完**；乙＝不进，保住 R1 已定稿的 23 环节，漏斗改现场口头说明 | **倾向甲**，但代价须用户认 |
| **裁决二** | **AI 演示做不做、用哪个** | Raven / Flow 均能接国内模型、不必出网付费；但走本地模型都失去 MCP 等七类 hosted 工具 | **只装 Raven**（官方 publisher、无许可证矛盾、不需改 Docker 镜像）。**无论选哪个都要先验 function calling** |
| **裁决三** | **演示脚本期待哪种观感** | A＝界面**自己完成操作**（单据自己开、字段自己填、状态自己变），20-80 行监听走 `cur_frm` API，稳；B＝**鼠标自己在动**（光标移动、按钮高亮），要模拟 DOM 事件，**脆性高得多** | **倾向 A** |
| **裁决四** | **要做到六档里的哪一档** | (b) 刷新数据免费；(c)(d) 跳转+开单据约 20-30 行；+(e) 填字段 +20 行；+(f) 提交 +30 行 | 待用户定 |

**⑥ 两条纪律建议（非裁决点，建议进演示纪律）**

1. **Raven 的 function calling 必须实跑验证** —— 在向客户承诺演示内容之前。
2. **realtime 心跳自检必须做** —— 断连是静默的；最坏情况是"演示到一半才发现界面从头没动过"。演示前推一个事件、前端回显确认链路通。

**用户回答：** **裁决一 = 甲**（CRM 漏斗进演示）。**裁决二 = AI 演示用 Raven，但最终两套都要接入、按需使用**；**AI 经 LiteLLM 接入，用户已自测 LiteLLM 可连**，故只需搞定「Raven → LiteLLM」这一段，**且可以不急着弄**。**裁决三 = A**（界面自己完成操作）。**裁决四未答。**
**结论：** 三项已裁决（详见第 23 步逐项落地）；**裁决四待答**——但其问法已因本轮技术路径查清而改变，见第 23 步③。

#### 第 23 步：裁决四定为半自动；hook 顺序查回；新增项需求关系补齐

**来源项目：** ERX-001
**适用面·状态：** 仅本项目·已落地

**① 裁决四：演示脚本形态 = 半自动**

**提出者：** Claude（问法经本轮技术路径查清后改写）
**背景：** 第 22 步原问「要做到六档里的哪一档」。**该问法已失效**——裁决三选了 A（走 `cur_frm` API）后，(c) 跳转 / (d) 开单据 / (e) 填字段 / (f) 提交在这条路上是**同一套机制的连续动作**，不是四个独立档位。故真问题改为「要不要自动往下走」。

**选项：**

| 选项 | 描述 | 优点 | 缺点 |
|---|---|---|---|
| **半自动** | 脚本推一个事件 → 界面跳到该节点、单据打开、字段填好，**停在那里等讲解**；人按一下再走下一步 | **演示节奏可控，讲到哪停哪**；每个节点是可独立触发的事件，**天然满足"可从任一节点起跑"**；约 40-60 行 | 需人工推进 |
| 全自动 | 一键从头连续跑完 23 环节 | 无需人工干预 | **演示时插不进话**；中途出错难收场；约 60-80 行 |

**用户回答：** **半自动。**
**结论：** **DEC：演示脚本形态定为半自动。** 代价约 40-60 行监听代码，落在自有 app 的 `app_include_js`。**"可从任一节点起跑"由此自然满足**——每节点一个独立事件。

**② hook 顺序查回（接入机制三块之三，最后一块）**

**提出者：** Claude（Agent 回报）
**背景：** 本项目特有风险——中国本地化靠 `regional_overrides`，而 `erpnext/__init__.py:152` 取 `[-1]` 末位胜出，故须查清装新 app 会不会把自有 app 挤出末位。报告见 [P1-S2-R2-A调研-接入机制-hook顺序.md](P1-S2-R2-A调研-接入机制-hook顺序.md)（91 行）。

**⭐ 核心结论：不会被挤出末位。**

合并机制：`frappe/__init__.py:962-985` `_load_app_hooks()`，`:966` 取 `get_installed_apps()`、`:968` 按该 list 顺序逐个 import。**顺序完全等于 `installed_apps` 列表顺序，无优先级字段**。`append_hook()`（`:1017-1035`）对 list 型**只 append 到尾部、绝不 prepend**；dict 型**按 key 递归深合并**（`:1025-1029`）故不同 region key 互不干扰。顺序唯一来源是**数据库全局值 `installed_apps`**（`:936`），**`apps.txt` 不决定顺序**（只做成员过滤且保序）；装新 app 一律 `.append()` 追加到尾部（`installer.py:379-383`）。

**为何不会被挤出**：`[-1]` 取的是 `overrides[function_path]` **这一条**列表，只含真正注册了「同一 region key 下同一 function_path」的 app。**出事需四条同时成立**（声明该 hook + 同 region key + 同 function_path + 装在自有 app 之后），而已知六个候选 app **无一满足**——CRM/Raven/Flow/Insights 零贡献，HRMS 只在 `India` 键下注册而 `:145` 按 `get_region()` 单键查找。

**规避办法（推荐第三条）**：① 自有 app 最后装；② 不改库强制排位；③ **启动自检 + 告警**——挂 `after_migrate`/`boot_session` 断言 `get_hooks("regional_overrides")["China"]` 每条 list 的 `[-1]` 落在自己模块前缀上，否则告警。**第三条直接校验 `[-1]` 语义，不依赖对 app 顺序的假设，故最稳。**

**⭐ 四类 hook 的冲突规则（对"两套 AI 都接入"的决定直接相关）**

| hook | 规则 | 实现位置 |
|---|---|---|
| `doc_events` | **全部累加执行**；具体 DocType handler **全部先于** `"*"` 通配 | `model/document.py:1651-1663` composer；`:1633-1648` |
| `override_whitelisted_methods` | **后者胜出** | `frappe/__init__.py:1577-1581` `overrides[-1]` |
| `override_doctype_class` | **后者胜出** | `model/base_document.py:110,116-117` `[-1]` |
| `app_include_js/css` | **累加，无覆盖** | `www/desk.py:38-39` |

**三条对本项目的直接含义**：

1. **验证了第 22 步对"两套同装"的提醒**：Flow 的 `"*"`×5 与 Raven 的 `"*"`×5 **全跑、互不覆盖**，即全库每次写操作过两道。
2. **`app_include_js` 的 realtime 监听注入不会被覆盖或挤掉** ✅ —— 唯一注意点是加载时序取决于 app 顺序，**监听代码应自带 `frappe.realtime` 就绪判断**。
3. **三组 `override_doctype_class` 无实际冲突**（CRM 的 `Contact`/`Email Template`、HRMS 的 `Employee`/`Timesheet`/`Payment Entry`/`Project`、Helpdesk 的 3 个，**两两无交集**）；且 `erpnext/hooks.py` 的 `override_doctype_class` **零命中**，erpnext 本体不覆盖任何 DocType。

**⚠ 两条附带发现（须记，都是静默失败型）**：① `installer.py:325-331` 安装时会检测 DocType 重复覆盖，**但只打一行黄字警告、不阻断**；② `base_document.py:120-126` 要求覆盖类必须是**原类**子类，故**多 app 串联覆盖时后者只基于原始类校验、前一个 app 的覆盖被静默丢弃**。

**hooks 缓存**：三层。非 developer_mode 走 redis（TTL 600s），developer_mode 走进程内 `site_cache`。**改 hooks.py 必须 `bench clear-cache`**，稳妥做法 `bench restart`；**装新 app 不需手动清**（`install_app` 自己清了）。

**⚠ 最要紧的未查实项**：**`get_region()` 对中国返回的字符串究竟是不是 `China`** 未在本机站点核对实际值（取决于 `Company.country`）。**自有 app 的 region key 必须逐字匹配，这是实测第一步该确认的。**

**③ 裁决二的风险评估因 LiteLLM 而改善（含一条能力可能救回）**

**提出者：** Claude
**背景：** 用户裁决二给出三条新信息：AI 经 **LiteLLM** 接入、**用户已自测 LiteLLM 可连**、**两套最终都要接入按需使用**、**可以不急着弄**。

**⭐ 一条此前判为丢失的能力可能救回**：第 21 步曾报「走本地模型会失去 MCP 等七类 hosted 工具」。该结论的成因是 `agents_integration.py:350-375` 按 **`model_provider == "Local LLM"` 这个条件**过滤，而该分支强制 `use_responses=False`。**但 LiteLLM 提供 OpenAI 兼容端点**，故存在另一条路：把它配在**标准 OpenAI 分支**上（`openai_api_key` + 自定义 base_url），走 `use_responses=True`、**七类工具不被过滤**。

**是否成立取决于 LiteLLM 对 `/v1/responses` 端点的支持程度** —— **故「Raven → LiteLLM 那一段」要验的核心不只是连通性，而是 `/v1/responses` 能否走通**。这一条改写了第 21 步的待验项。

**两套都接入的影响**：Flow 的最大反对理由（零 release 零 tag 不可锁版本 + `"*"` hook）**在"按需使用、演示环境用完即弃"的前提下不致命**。**但据本步②已查实的"`doc_events` 全部累加执行"**——两套同装时全库每次写操作过两道 hook。

**⚠ 故给出一条操作建议**：**不要在改服务端工艺损耗与费用科目那两处逻辑的同时装着这两个 app**，否则写路径上多两层第三方 hook 会让问题定位变难。

**结论：** 裁决二落地为——**Raven 为 AI 演示载体**，经 LiteLLM 接入；**Flow 后续接入、按需使用**；**该项排在译名/导航/操控机制之后，不进演示关键路径**（与其"实验性"分级一致）。

**④ 新增项的需求关系（补 Spec 议题 7，产物快照）**

三项新增（CRM 漏斗进重要 / AI 演示进实验性 / 操控机制升格核心）的关系：

| 关系 | 内容 |
|---|---|
| **依赖（硬）** | **CRM 漏斗 → 译名**：+689 条未译**必须在演示前补完**，否则违背"可信度优先"定位。故 `PH-P1001` 的范围因裁决一而**扩大** |
| **依赖（硬）** | **操控机制 → realtime 链路健康**：断连静默，故**演示前心跳自检是硬前置** |
| **依赖（硬）** | **AI 演示 → LiteLLM 的 `/v1/responses` 支持**（见③），且 **→ function calling 实跑验证**（未验则不能承诺演示 AI） |
| **共享数据** | **CRM 漏斗 ↔ 23 环节闭环**：衔接点是 **Quotation**（`Deal → Quotation → Sales Order`）。⚠ **Quotation → Sales Order 那一步是否需人工未查实** |
| **共享机制** | **操控机制 ↔ React 重写**：共享**事件协议与推送侧**；**前端监听 React 要重写**（不是共享） |
| **潜在冲突** | **Flow + Raven 同装 ↔ 服务端修正工序**：`doc_events` 累加，写路径多两层。**建议不同时** |
| **次序约束（新增第 3 条）** | 原有两条（服务端修正先于建样本数据、V-01 先于建演示公司）之外新增：**译名补完（含 CRM 那 689 条）先于演示脚本编写**——脚本里的节点名与提示文案都要用译名，反序要改两遍 |

**用户回答：** 本步未答「有无补充」（**第 24 步用户即给出补充，见该步五条**；A 步 Spec 第四条件到第 32 步后才由用户明示补齐）。
**结论：** **A 步四个条件中前三个已齐备**——定位（R1 已定，未变）、需求分级（本轮重排完成）、需求关系（本步④补齐）。**只剩第四条件。**

#### 第 24 步：译名分两档且须查码定义；App 分档路线图（纠正表述错误）；新增 AI 分析用数据集

**来源项目：** ERX-001
**适用面·状态：** 仅本项目·已落地

**① ⭐ 译名的做法被细化为两档，且性质从"一次性翻译"改为"可配置文件 + 长期演进"**

**提出者：** 用户
**背景：** **是用户先要求把 A、B 两个定位选项再说明一次**（原话「1、我不知道A、B选项分别是什么，请再说明一次」），Claude 才回读 R1 原文取出两案原文（读回过程因编码问题失败两次，最后用 `sed` 直读命中 R1 第 51 行）。**不是 Claude 主动重问**——收尾 §6 核出原记录把信息流向写反了，此处已改。定位 A/B 的分野押在"译名全量准确"这条既有裁决上。

**⚠ 同一条用户消息里的第 3 条原记录整条漏落（收尾 §6 核出，此处补记）**：用户批评「**我实际上还不清楚目前决定好了的要做的事情是什么，因为基本上全程都是查各种项目，但并没有真正好好讨论过要做什么，以及怎么做**」。Claude 两次明确接受该批评，并因此**先回读 R1 原始记录把已定事项列清楚，再答前两条**（而非凭印象复述）。**这条批评是本 Round 后半"先调查再出表"（DEC-050）与第 29 步出 43 项工作量表的直接动因**——用户要的是"决定了要做什么"，不是更多调研报告。

**用户回答：** 三条：
1. **要通过查代码确认某个按钮的实际作用，再按中国大陆习惯翻译这个作用**。**至少「可信度优先」覆盖的范围内要这么做。**
2. **其它部分至少都补上简单翻译**——"不能让客户看到有些翻译了有些没翻译"。
3. **"你们厂这里怎么做"这类内容是需要长期跟着厂边调研边改进的，不是一次性能做完的事**。**因此译名应写成一个容易配置的文件**，之后直接改该文件就能改翻译。

**结论（三项，均为对既有裁决的实质细化）：**

**一、译名质量分两档，这解掉了 A/B 的张力。** R1 的 A 定位要求"全量准确"，成本最高；用户现在给的是**全量覆盖（无缺口）+ 准确度分两档**：

| 档 | 范围 | 做法 | 成本特征 |
|---|---|---|---|
| **精确档** | **「可信度优先」覆盖范围内**（即演示要走的那条线：漏斗三环 + 23 环节） | **查代码确认按钮/字段的实际作用，再按中国大陆习惯译这个作用** | 单条贵（要读源码），但范围有界 |
| **覆盖档** | 其余全部 | **至少补上简单翻译**，保证无"有些译了有些没译" | 单条便宜，但量大 |

**故 Claude 在第 23 步提的"是否重新考虑 A/B"一问已无须回答**——用户给出的是第三条路：不放弃覆盖面，而是把准确度分档。**A 定位维持不变。**

**二、交付物形态改变：从"一次翻译动作"改为"一份可配置文件"。** 技术路径 S1 已查清（`translate.py:135-240` 五级优先级）：**自有 app 的 `zh.csv` 做批量基线（git 管理、可直接编辑）+ `Translation` DocType 记录做运行时最高优先覆盖**，两者叠加、均零侵入。**用户要的"容易配置的文件"即前者。**

**三、第 14 项「内置摸底问点清单」的性质改变。** 原设想是演示时一次性问完；用户明确它是**长期跟厂边调研边改进**的事。故它不是"演示的一个交付物"，而是**一条持续机制的起点**。**这也反向支持了第二项**——译名要可配置，正因为调研会持续带回新的用词修正。

**② ⚠ 纠正 Claude 的表述错误：App 不是"只留两个"，而是分档路线图**

**提出者：** 用户
**背景：** 用户指出：「**为什么十一个 App 只留下两个，我要你查的实际上大多数都是之后要加入的，我从来没有说哪个要放弃。**」

**⚠ 这是 Claude 的表述错误，须记录**：第 22 步记录里写的是「明确**不进本次范围**」（口径正确），**但 Claude 给用户的汇总说成"十一个 app 里只有两个建议进演示范围"、并把五个列为"明确不进本次范围"**——该表述读起来是去留判定而非时序安排。**用户从未说要放弃任何 app。**

**结论：改用分档路线图表达（产物快照）：**

| 档 | App | 依据 |
|---|---|---|
| **A 进本次演示** | **CRM**（裁决一＝甲） | 漏斗三环延伸演示线 |
| **B 本次演示的实验性项** | **Raven** | 裁决二；经 LiteLLM 接入 |
| **C 已裁决要接入、时机在后** | **Flow** | **裁决二明确"两套都要接入、按需使用"** |
| **D 待定接入时机（非放弃）** | **HRMS**（要整套 HR 时，须 `version-16`）、**Helpdesk**（售后立项后，连带 `telephony`）、**Insights**（数据积累后有自助取数需求时）、**print_designer**（打印版式，v16 兼容性待实装验证） | 各自的唤醒条件已查清 |
| **E 参考不接入** | `erpnext_china`(zelin)、`saoxia` | R1 已裁决：可当**词汇素材**，不可当方案 |
| **F 已排除（有实证理由）** | `drive`（版本管理只管在线富文本、不管上传的二进制文件，补不上图纸版本）、`builder`（做对外网站页面非 Desk Workspace）、ECOSIRE 全系列（闭源收费、无源码）、`frappe/assets`·apparelo·hospitality·non_profit·pasigono·agriculture（停维护或不兼容 v16） | 见工业生态报告 |

**③ 新增议题：哪些 App 接入、哪些参考后自建（待讨论）**

**提出者：** 用户
**背景：** 用户指出「**每个 App 哪个要接入，哪个用来参考然后自己新建 App 还需要讨论。**」

**结论：立为一个独立议题，本步先摆出候选与初步倾向，待专门讨论。** 已查清的素材：

| 需求 | 候选做法 | Claude 初步倾向（待议） |
|---|---|---|
| 中国本地化（内部账） | 参考 zelin 的科目表与三大报表 DocType 设计 → **自建** | **参考自建**。zelin 有四处硬缺陷（144 个科目号引用命中 0 个、裸 `except` 只写 log 等），但其现金流量表"做成可提交单据 + 从 GL Entry 拉流水"的思路是对的 |
| 译名 | 参考两仓 `zh.csv` 作词汇素材 → **自建** `zh.csv` | **参考自建**。zelin 的 `setup/field_property.csv`（35 行改撞名字段标签）是"改源词用词"这条路的现成样本 |
| 图纸版本管理 | 无现成 → **自建** | 自建（`drive` 已证补不上） |
| SPC·CPK / 模具工装 | 无开源现成（ECOSIRE 闭源）→ **自建** | 自建 |
| 计件工资 | **自建**（hrms 也帮不上：`COMPONENT_EVAL_GLOBALS` 只白名单 13 个数学函数、读不到自定义数据） | 自建，数据源用 `Job Card Time Log` 的 `completed_qty`+`employee`+`operation` |
| 排产优先级与换型时间 | 无原生字段 → **自建** | 自建 |
| 打印版式 | `print_designer` **接入**（若 v16 实装通过）否则自建 | 先实装验证再定 |
| 销售漏斗 | **接入 CRM** | 接入（已裁决） |
| AI | **接入 Raven + Flow** | 接入（已裁决） |

**④ 财务范围：只做内部账，对外接口延后；银行对账留**

**提出者：** 用户
**背景：** 用户第 23 步后明确「财务系统只做内部账部分，涉及对外的部分，比如通过跟政府的财税系统对接之类的、可能需要资质的部分，暂时延后」；本步补答「**银行对账留**」。

**结论（范围边界，产物快照）：**

| 项 | 判定 |
|---|---|
| 增值税 Tax Template 三件套（V-04 已验 `go`） | **留**——内部账计税逻辑，不涉外 |
| 中国科目表 | **留** |
| 资产负债表、利润表（V-06 已验 `go`） | **留** |
| 现金流量表 | **留**，但须自建（可提交单据 + 从 GL Entry 按现金银行科目拉流水） |
| **银行对账** | **留**（用户本步明确）——只导入流水做匹配，不需资质 |
| **专票 / 金税盘对接** | **移出本次范围**。⚠ **用户的判据是"涉及对外"，不是"需资质"**——原话「涉及对外的部分，比如通过跟政府的财税系统对接之类的，**可能需要资质**的部分，暂时延后」，"可能需要资质"是带保留的举例。**原记录把它硬化成确定性的"需资质"，与本项目自己查实的 V-05（专票沙箱不需企业资质，已验 `go`）相抵**（收尾 §6 核出，此处已改）。**故下游不得据 V-05 反推该项应重新纳入**——排除理由是"涉及对外"这条范围边界，V-05 与它无关 |

**⚠ 连带影响**：Claude 在第 23 步提的第二个疑问（"中国本地化判为核心的理由是客户会计会当场问专票，但范围里没有专票"）**已自动消解**——该缺口是有意为之，非遗漏。**V-05 的结论**（专票沙箱不需企业资质，已验 `go`）**暂时用不上，但留档不作废**。

**⑤ ⭐ 新增需求：编一套 100 条起步的数据，用于演示 AI 的分析功能**

**提出者：** 用户
**背景：** 用户提出「**事实上还需要编一套数据，至少 100 条起步，用于演示 AI 的分析功能**」。

**⚠ 这一条对第 6' 项（闭环样本）是量级变更，不是新增一个并列项。** R1 的第 6' 项是"真实弹簧产品闭环样本（A/B 两套）"——**两套的量级是"能走通一遍"**；而 AI 分析需要的是**有统计意义的数据量 + 可被发现的规律或异常**。

**四条技术约束（本轮已查清的事实直接适用）：**

| # | 约束 | 依据 |
|---|---|---|
| 1 | **必须走单据、不能裸插数据** | 若直接写库或 insert 时带 `docstatus:1`，会**跳过 `on_submit`**（`document.py:1103-1106`），则 GL Entry / Stock Ledger Entry 不生成 → **财务与库存数据不一致，AI 分析出来的结论是错的** |
| 2 | **`insert_many` 上限 200** | `client.py:239-240`。100 条在限内，但若要扩到数百条须分批 |
| 3 | **数据要有可分析性** | 须有**时间跨度**（否则无趋势）、**多产品多客户**（否则无对比）、**可被发现的异常点**（否则 AI 无话可说）。这是"编数据"与"造数据"的区别 |
| 4 | **与演示脚本机制同源** | 演示脚本已定的技术路径（API v2 两调用建单+提交）**正好就是数据生成器**。故第 7 项与本项共享实现，不是两套 |

**⚠ 一处待用户明确**：**"100 条"是指什么的 100 条**——销售订单？工单？还是全链（每条都走完接单到收款）？三者工作量差一个量级：100 张销售订单只需 2×100 次调用；100 条走完全链则是 100×23 环节。

**分级建议**：**本项应进核心**（不是随 AI 演示进实验性）——因为这套数据同时服务第 6' 项闭环样本与 AI 分析两个用途，**即使 AI 演示最终不做，数据本身也是演示的必需品**。

**用户回答：** 本步未答；**下一轮（第 25 步）即答**——口径＝**全链**（从销售漏斗到生产到交付货物全流程），另附三项数据要求与三类 AI 分析用途，详见第 25 步⑩（原记录漏落，收尾 §6 补记）。③ 的接入/自建议题**用户同轮答「同意」**，即同意立为独立议题。
**结论：** 五条指令均已落地为范围与做法的修订。**A 步的第四条件仍未满足**——用户本轮提出了补充（即本步五条），故按 Spec 出口路由，**A 步继续迭代、状态值仍为 `未收敛`**。

#### 第 25 步：标准缺口两路调查 —— MRP II 观察被证实，且发现一条共同模式

**来源项目：** ERX-001
**适用面·状态：** 仅本项目·已落地

**① 用户指令：查 ERPNext"用的不是最新标准"的其它环节**

**提出者：** 用户
**背景：** 用户在实操最小闭环时发现「**ERPNext 似乎存在用的不是最新标准的情况，比如说没有用 MRP II 模型，这就导致了有些需求不能满足**」，要求查清**还有哪些环节存在此类问题、有没有开源项目能补**，并指示派子 Agent 调查。

**用户回答：** 即本指令。
**结论：** 派两路——生产计划与排产、质量与追溯。**方法上要求按标准体系分层逐项判定**（而非零散找缺口），故产出是"落在哪一层、缺哪几层"的图。报告：[P1-S2-R2-A调研-标准缺口-生产计划.md](P1-S2-R2-A调研-标准缺口-生产计划.md)（95 行）、[P1-S2-R2-A调研-标准缺口-质量追溯.md](P1-S2-R2-A调研-标准缺口-质量追溯.md)（80 行）。

**② ⭐ 用户的 MRP II 观察被证实：ERPNext v16 落在 MRP 层，够不上 MRP II**

**判据**：**产能这一维没有参与任何计划层计算。** 不是看功能多少。

| 层 | v16 实现 |
|---|---|
| S&OP | ❌ |
| 需求管理/预测 | ⚠ `Sales Forecast` 存在但**只有 92 行、无预测算法**，是人工录入独立需求的容器 ★ |
| **MPS** | ✅ **`Master Production Schedule`（480 行）是真的 MPS** ★ ——汇总 SO + Material Request，递归 BOM 累加提前期，算 `order_release_date = delivery_date - cumulative_lead_time` |
| MRP 运算 | ✅ 在一个 **1427 行的 `Material Requirements Planning Report`** 里。BOM 逐层展开 ✅ / 净需求扣库存与在途 ✅ / 提前期倒排 ✅ / 安全库存 ✅ / **lot sizing 只有最小订购量补足**（无 EOQ、无固定批量、无期间批量） |
| **RCCP / CRP** | **❌ 这是 MRP II 相对 MRP 的核心增量，确实没有** |
| 有限产能排产 | ❌ 无优先级、无换型矩阵 |
| 闭环反馈 | ❌ 无重排机制、无计划与实绩对比 |

**⚠ 三个 DocType 是本项目文档从未记载过的**（★ Claude 复验目录与字段均存在）：`Master Production Schedule`、`Sales Forecast`、**`Item Lead Time`**（后者字段含 `capacity_per_day`/`no_of_workstations`/`daily_yield`/`no_of_shift`/`total_workstation_time`）。**故此前"ERPNext 排产是朴素顺排"的记载需补充——v16 在计划侧比我们记录的多一层。**

**⭐ 一处"看起来有"的坑（LG-067 同型，第 N 例）**：MRP 报表有一列名为 **`Capacity`**，极易误判为产能计划。实际 `capacity` 在那 1427 行里仅 8 处命中，**全是取值/传值/列定义，无一处把需求与 capacity 做比较、告警或削峰**；且它取自 `Item Lead Time.capacity_per_day`，是**物料级的，与 Workstation / Routing 完全无关**。

**唯一真查产能的地方**：`job_card.py:400-434` 的 `has_overlap` —— 但那是**工单下达后的执行层防重叠**（FCFS 顺延、递归重试），**不是计划层 CRP，且不反馈给计划**。

**③ Workstation 的产能模型部分可用（比预想的好）**

| 能力 | 有无 |
|---|---|
| "每天可用几小时" | ✅ `working_hours` 子表 + `holiday_list`，排产**真按时段切分、跨班次拆分、跳假日** |
| "同时开几台" | ✅ `production_capacity` 是并行槽位数，`alloted_capacity` dict 按它判满载 |
| 冲突检查 | ✅ 真查已有 Job Card 时间重叠 |
| **产能负荷报表** | **❌** —— 22 个报表 + 8 个 dashboard chart 逐个看过，无一是负荷口径 |
| `Workstation Type` | **无任何产能字段**；按 type 排产取第一个工作中心，**不做负载均衡** |

**④ ⚠ 发现一处疑似上游缺陷（★ Claude 复验，证据硬但未实跑）**

`master_production_schedule.py:445` 实读：`frappe.enqueue_doc("Master Production Schedule", self.name, "make_mrp", queue="long", timeout=1800)`。

但：**全仓 `def make_mrp` 只有 1 处命中、且在测试文件里叫 `make_mrp_plan`** ★（`test_material_requirements_planning_report.py:192`），不是它要调的方法；**`MRP Log` DocType 目录数为 0** ★。报表自己的测试文件还留着注释 "left in draft: on_submit enqueues MRP Log creation in a background job"。

**推断：提交 MPS 会 AttributeError、MRP 结果不落库。** **这直接决定 v16 的 MPS 能不能用，须实跑验证。**

**⑤ ⭐ 质量与追溯：一条推翻既有记载、一条推翻 Claude 本轮的乐观判断**

**一、⭐ 批次/序列追溯不必自研——v16 已有现成报表**（推翻 Claude 此前把追溯列进"必须自研"的表述）

★ Claude 复验：`erpnext/stock/report/serial_no_and_batch_traceability/` 存在，带 **`traceability_direction`** 过滤器，取值 **Backward / Forward / Both**（`:50`/`:63-72` 实读）——反查原料走 Stock Entry，正查流向也支持。另有 `serial_and_batch_summary`、`batch_wise_balance_history`、`serial_no_ledger`。

**故弹簧断裂索赔追责那条链是通的**，不必自己刨 SLE。**未实测**：多级 BOM 的连续穿透深度。

**二、⚠ Claude 本轮犯了一次"看名字不看字段"的错，须记录**

Claude 在本步之前看到 `quality_management/` 有 17 个 DocType，就对用户说"质量管理比我预期的多"、"是我们没走过，不是 ERPNext 没有"。**该判断错了，且正是 LG-067 那类错误。**

★ Claude 复验 `Non Conformance` 字段表：**仅 10 个字段**（`subject`/`procedure`/`status`/`details`/`process_owner`/`full_name`/`corrective_action`/`preventive_action` + 2 分栏）。**无数量、无物料、无批次、无仓库、无到 Quality Inspection 的链接** → **它记不住"哪批多少件不合格"。**

**故那 17 个 DocType 是 ISO 9001 的文档留痕体系**（程序文件、管理评审、会议纪要），**不是检验执行系统**。CAPA 有壳无骨，8D 完全无。

**三、真正的检验层在 `stock` 模块，且三段检验齐全**

★ Claude 复验 `quality_inspection.json`：`inspection_type` 取值 **`Incoming / Outgoing / In Process`**（IQC/OQC/IPQC 齐全）；`reference_type` 可挂 **`Job Card`**（故 IPQC 能挂工序卡）、另含 Purchase Receipt / Delivery Note / Stock Entry 等 7 种。拒收有拦截（`Stock Settings.action_if_quality_inspection_is_rejected` = Stop/Warn，逻辑在 `controllers/stock_controller.py:1676-1695`）。

**但拒收之后没有流程**：无隔离仓、无让步接收审批、无 MRB（不合格品评审）。

**四、SPC / CPK / MSA / APQP 确实完全无** ★ Claude 复验六个关键词全部 **0 命中**：`control_chart`、`process_capability`、`cpk`、`nelson`、`western_electric`、`standard_deviation`。`Quality Inspection Reading` 只有 `reading_1..reading_10` + min/max/acceptance_formula，**是单次判合格、无跨批次时序统计**。

抽样方案几乎无：只有一个人工填的 `sample_size`（★ 复验其 `options` 为 None，即自由输入）。**易混点**：Item 上的 `sample_quantity`/`retain_sample` 是**留样**，不是抽样方案。

**五、Agent 自己避开了两个"名字像"陷阱**（方法正确，值得记）：`andon` grep 出 39 个命中，逐条看全是西班牙语科目表里 "aband**ono**" 的子串噪声；`Mold` 那 1 处命中亦无关。**它没停在命中数上。**

**⑥ ⭐ 两路调查揭示一条共同模式（本步最有价值的结论）**

**ERPNext 在每个领域都实现了"记录层"，但缺"计算层"：**

| 领域 | 有记录层 | 缺计算层 |
|---|---|---|
| 质量 | 检验记录（`Quality Inspection Reading` 的 10 个读数） | **SPC 统计、CPK 过程能力** |
| 计划 | 物料需求运算（1427 行 MRP 报表） | **产能需求运算（RCCP/CRP）** |
| 不合格品 | 台账（`Non Conformance`） | **处置流程（隔离/让步/MRB）** |
| 工时 | `Job Card Time Log` 的 `completed_qty`+`employee` | **计件工资计算**（第 24 步已判） |

**这个模式解释了用户的原始观察**——不是"某个功能没做"，而是**系统性地停在"能记下来"这一档，没走到"能算出结论"**。**故本项目自研的重心应是计算层，而非重建记录层**（记录层大多可复用，如 SPC 的读数已在 `Quality Inspection Reading` 里）。

**⑦ 开源候选：frePPLe 是唯一真正可用的**

| 候选 | 许可证 | 活跃度 | 结论 |
|---|---|---|---|
| **frePPLe/frepple** | **Community 版 MIT**（仓库字段 NOASSERTION，双许可） | **2026-09-23 今天仍在提交**，747★ | **补的正是 RCCP/CRP + FCS + 预测** |
| msf4-0/ERPNext-Frepple-Integration | GPL-3.0 | **2022-02-21，停更 4 年半** | 不可用 |
| TimefoldAI/timefold-solver | Apache-2.0 | 2026-09-23 今天，1791★ | 求解器内核，与 ERPNext **无现成集成**，全要自建 |

**关键线索**：**frePPLe 官方有 ERPNext connector 文档页**（文档版本 9.19.0），比停更的社区仓库可靠得多。**但是否 Enterprise 限定、支持到 ERPNext 哪个版本、Community 版能否用，均未查实**——**这是选型前第一件要确认的事。**

**质量侧无可用 app**：Frappe 生态内搜五组关键词零结果（命中的 `iniself/dataq` 是 data quality、`priyankongit/edu_quality` 是学校管理，均名称误导）。生态外**只有计算内核**：`pycontrolcharts`（MIT，2026-03）、`pyspc`（GPL-3.0，243★ 但停更三年）。

**用户给的两条线索均成立**：`Siddardth7/quality-platform` 的 `/LICENSE` 直连 **404**、API license 字段 None、依赖 streamlit 无 frappe → **无许可证等于法律上不授权任何使用，确认不可复用**。ECOSIRE 按指示只作需求参照、不推荐。

**⑧ 自研清单（两路合并，按"计算层"重心排）**

| 优先 | 项 | 有利条件 |
|---|---|---|
| 高 | **SPC 控制图 + CPK** | **读数已在 `Quality Inspection Reading`**，新增 `Control Chart`/`Process Capability Study` 读它即可；CPK 公式是公开标准 <200 行。Nelson 8 条判异须自写。**客户直接要 CPK ≥ 1.33** |
| 高 | 优先级字段、**换型矩阵** | 弹簧按线径/材质/卷簧方向切换，**是工序对工序的矩阵而非单值 `setup_time`** |
| 高 | 工艺损耗反算投料量 | 已在核心需求第 4 项 |
| 中 | 工作中心级 CRP 负荷报表 | Workstation 的 `working_hours`/`production_capacity` 可作数据源 |
| 中 | GB/T 2828.1 抽样方案 | 现有 `sample_size` 可作落点 |
| 中 | 不合格品闭环 | **在 `Non Conformance` 上扩字段比新建划算** |
| 中 | Routing 基准量、MPS 时界、`make_mrp` 缺失的绕行 | — |
| 低 | 模具工装、8D、APQP/PPAP、MES 车间层 | — |

**用户回答：** 指示先落档，然后派两路验证，**且 frePPLe 要先拉下来再验证**。
**结论：** 两路标准缺口调查已落档。**两条待验已派出**（`make_mrp` 结果见本步⑨；frePPLe 待回）。

**⑨ 验证回报：`make_mrp` 缺陷判定 `go` —— 命题成立，且比原描述更严重**

> 本格是第 25 步的后续追记（无新对话轮，按讨论契约 §7 合法例外第 3 项）。报告见 [P1-S2-R2-A验证-make_mrp.md](P1-S2-R2-A验证-make_mrp.md)（79 行）。

**提出者：** Claude（Agent 实跑验证 + 主 Session 复验静态面）

**判定：`go`。** 命题三点全部**实测**确认（不再是静态推断）：

| 查证 | 实测结果 |
|---|---|
| `hasattr(doc, "make_mrp")` | **`False`**；模块级 `frappe.get_attr(...make_mrp)` 抛 `AttributeError` |
| `frappe.db.exists("DocType", "MRP Log")` | **`False`**；`%MRP%` 模糊查 DocType 为空 |
| 实跑 worker 入口 | 复现 traceback：`AttributeError: 'MasterProductionSchedule' object has no attribute 'make_mrp'`（`background_jobs.py:236` 的 `run_doc_method`） |

★ 主 Session 复验：**调用方存在、被调方不存在** —— `master_production_schedule.py` 的类里只有 `enqueue_mrp_creation`，而它 `:445` 要调的 `make_mrp` 全仓无定义。

**⭐ 命题之外的关键发现（改变绕行方案的形状）**

★ Claude 复验：**MPS 的 DocType JSON 里完全没有 `is_submittable` 这个键**（`grep -c is_submittable` = **0**，json 解析取值 **ABSENT**）。DB 里 `is_submittable = 0` 这一项**只来自 Agent 回报、主 Session 未复验**（收尾 §6 核出 ★ 标记原覆盖过宽，已收窄；结论不受影响）。

**故 v16 的 MPS 是两层都没接完的半成品：**

1. **界面上提交不了** —— 无 `is_submittable` 即无提交按钮，`on_submit` 在正常 UI 流程里**根本走不到**；
2. **绕过界面用 Python `.submit()` 强行提交，则前台完全静默成功** —— docstatus 落库为 1，`msgprint("MRP Log documents are being created in the background.")` 照常发出，**失败只发生在后台 worker**。**这是个安静失败，界面上看不到任何错误。**

**旁证** ★：`master_production_schedule.js:65` 的 `View MRP` 按钮跳的是 **`Material Requirements Planning Report` 报表**，不是 MRP Log 单据 —— **MRP Log 这条线是未完成的设计残留。**

**⚠ 故"静默失败"这一类又多一例**，与本项目既有的三例同型（realtime 断连静默、`installer.py` 检测 DocType 重复覆盖只打黄字不阻断、`base_document.py` 多 app 串联覆盖时前者被静默丢弃）。**本项目应把"静默失败"立为一类专门的排查对象。**

**建单成本比预期低** ★ 复验：MPS 只有 **4 个必填字段**（`naming_series`/`company`/`posting_date`/`from_date`），三个子表（sales_orders / material_requests / items）**全部非必填**，**不需要 SO/BOM/Material Request 前置数据**。故 Agent 真建单真提交做到了，不是只验存在性。

**对本项目的含义**：**若要用 MPS 做闭环，绕行方案是必需的**（自研清单里"`make_mrp` 缺失的绕行"一项由"待确认"升为"已确认必需"）。**但本次演示的 23 环节闭环不经 MPS**（排产走 Work Order / Production Plan），故**它不阻塞演示**，属第 ② 阶段（通用版）的事。⚠ 后半句是 Claude 结合项目上下文的**推断**，不在 Agent 回报里（收尾 §6 核出，此处补标）。

**方法学妥协一处（Agent 如实交代）**：未跑 `docker/start.sh` 故无 worker 消费队列，任务停在 QUEUED；改为直接调 `frappe.utils.background_jobs.run_doc_method(...)`（即 `enqueue_doc` 实际投递的那个 callable）等价复现。**差异仅在异常是否被 RQ 捕获落 Error Log。**

**清理已完成**：`MPS26-000001` 已 cancel + delete（count 归 0）、队列 2 条 job 已删（三个队列深度归 0）、临时脚本目录已删。未改源码、未 install-app、未重装站点、未做 git 操作；`apps/erpnext` 的 `git status` 为空。

**⚠ 一项未回滚的环境副作用**（收尾 §6 核出原记录漏落）：**Docker daemon 原本没运行，Agent 启动了 Docker Desktop**（未改任何配置）。这是本次实跑唯一没有回滚的动作。

**⭐ 附带产出一条环境坑，建议补进 `docker/README.md`**：即使 `export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'`，`docker cp /tmp/x.py container:/tmp/x.py` 的**源**路径仍被 MSYS 改写成 `D:\tmp`，报 `GetFileAttributesEx D:\tmp: The system cannot find the file specified`。**规避办法**：把脚本写进 bind mount 的项目目录、用容器内 `/workspace/...` 路径引用，完全不用 `docker cp`。（此条与项目记忆里已记的七处 Windows Docker 坑同类，是第八处。）

**未验证**：未在浏览器目视确认提交按钮不显示（该结论来自 meta 与 JSON 的 `is_submittable`，无 UI 验证）。
**⑩ ⚠ 补记：本轮用户消息里另有三条，原记录漏落（收尾 §6 记录验证时发现）**

用户 L713 那条消息编号提了四件事，原记录只落了第 6 项（即本步①的查标准缺口指令），**另三条漏记**：

| 编号 | 用户原话要点 | 落点 |
|---|---|---|
| **1** | 译名**先写成容易改的可配置文件**，等之后稳定了，再按 S1 查清的那个技术路径写成稳定版 | 对第 24 步①「可配置文件」的**时序补充**——先易改版、后稳定版，是两阶段而非一次做成 |
| **5** | ⭐ **「100 条」的口径**：指**从销售漏斗到生产到交付货物全流程**；且**不能所有全链都是同一个产品**——应据公开资料多写几个 BOM，再编**数十个**供应商与客户，供应商客户**最好还有历史成交单价**。目的是结合 AI 演示三类分析：**分析销售漏斗找单子 / 哪个供应商货美价廉 / 哪个 BOM 在符合单子要求下利润最大化**。总之尽可能接近现实，让 AI 有足够数据 | **这正是第 24 步⑤标为「待用户明确」的那一问的答案**——口径＝**全链**（即 100×23 环节那一档，非 2×100 调用档）。工作量表第 19 项写的「100 条全链数据集 + 生成器，4–6 人日」**据此成立，不是单方面推定** |
| **4** | 「每个 App 哪个接入、哪个参考后自建还需讨论」→ **同意**（即同意第 24 步③把它立为独立议题） | 第 24 步③的议题成立已获用户确认 |

**⚠ 漏记性质**：不是概括压缩，是**整条指令无痕**——第 24 步⑤的「待回答」格子在本步实际已被回答，却因本步只处理了第 6 项而未回填，导致"口径未定"这一状态在记录里多挂了八步。**这类漏记只有拿原始对话比对才暴露**（讨论契约 §6 正为此设）。


#### 第 26 步：frePPLe 判 no-go；自研 CRP 的难度分三档评估

**来源项目：** ERX-001
**适用面·状态：** 仅本项目·已落地

**① 验证回报：frePPLe 判 `no-go`**

**提出者：** Claude（Agent 验证）
**背景：** 第 25 步派出，用户指示"先拉下来再验证"。报告见 [P1-S2-R2-A验证-frePPLe.md](P1-S2-R2-A验证-frePPLe.md)（88 行）。克隆在 `Reference/frepple`（直连被 reset，经 Clash 7897 成功）。

**许可证：干净。** 打开真实 `COPYING`（仓库根）：开头明写 dual licensing，随后是**完整 MIT 正文，全文无 AGPL/GPL 字样**。`doc/license.rst` 定三层结构：Community = MIT（明确允许 reuse within proprietary software）/ Enterprise = 专有且**源码不随仓库分发**（在另一仓库 `frePPLe/frepple-enterprise`，仅客户可取）/ OEM 商业许可。**故克隆到的全部代码都是 MIT，无 Enterprise-only 目录混杂**；GitHub 的 `NOASSERTION` 是双许可扰乱自动识别，**不是 AGPL 污染**。活跃度证实：版本 `9.19.0`，最后提交在 **2026-09-23 今天**。

**⭐ 但最关键的一问翻了：仓库里没有 ERPNext connector 代码。**

| 查证 | 结果 |
|---|---|
| 全仓 `grep -ril erpnext` | 只命中**两个文件，都是文档** |
| 搜 `frappe` | **零个代码文件** |
| `doc/erp-integration/erpnext-connector.rst` | **全文仅 9 行**，原文称该集成 "is available as a **third-party application**"，并声明 "we are **not owning or actively maintaining** this connector"，指向的正是停更的 msf4-0 仓库 |
| 对比：官方真维护的 Odoo connector | `freppledb/odoo/`，**31 个文件、4533 行 Python**，含 import/export 命令、migrations、tests、独立文档章节 |

**故"官方文档页比社区停更仓库可靠"这个期待落空——那个文档页本身就是一张转手指路页。** 且"Community 还是 Enterprise"一问**不成立**：connector 两者都不是，它是第三方的、形态是装在 ERPNext 侧的 Frappe app，**"Community 版 MIT"对它没有覆盖力**。

**一处前提修正**（Agent 纠正 Claude 给它的背景）：msf4-0 同组织另有更新分支 `...Enhanced-Integration-Version-1.3`（`pushed_at` 2023-12-21），但仍停更约 2 年 9 个月、1 star。**两个 README 通篇无任何 ERPNext/Frappe 版本号声明**，对 v16 无一字；同组织另有 `ERPNext_version-12_update-1.2`，推断基线在 v12–v14。

**⚠ 一条对弹簧厂要害的限制**：`doc/model-reference/setup-matrices.rst:5-15` 明写 Community 求解器**尊重**换型矩阵，但 "does NOT do any effort to **reduce** the setup times"，且不具备传播换型变更的完整逻辑（"Your mileage will vary"）——**换型优化要 Enterprise 高级求解器**。库存计划亦仅 Enterprise。**而卷簧机调机/线径换型优化正是弹簧厂痛点。** Community 给的是真有限产能排产，**不是换型最优化**。

**部署增量**：C++ 求解器 + Django + **PostgreSQL**，官方 compose 为 2 容器（Apache `9000:80` + `postgres:16`，各预留 4GB）。`requirements.txt` 末行钉 frePPLe **自己 fork 的 Django**（tag `frepple-9.18`），升级节奏受其约束。有预构建镜像可免自编译。净增量：**+2 容器、+第二套 RDBMS（与现有 MariaDB 并存）、+1 对外端口须核 Windows 保留段**（注：`9000:80` 的宿主侧 9000 **恰好落在本项目已知的 Windows 保留段 8995-9094**，必须改）。

**判定 `no-go`。主要反对理由：官方根本没有 ERPNext connector**，走这条路等于自己从零承接并长期维护整套集成。

**⚠ 最该补而未查的一条**（若将来重议此路）：**同步粒度是否覆盖 Workstation / Routing / Operation**——只读到 README 功能标题、无字段级清单。**若它只同步 Item/BOM 而不同步工作站与工艺路线，CRP 根本补不上**，这比许可证与版本号都更决定性。

**② ⭐ 用户提问：只参考 frePPLe 逻辑、自己实现一套，难度大吗（全程由 AI 开发）**

**提出者：** 用户

**结论：难度分三档，档间差一个量级。** ★ 以下数据底座均为 Claude 本步直接读码复验。

**档 1：CRP 负荷报表 —— 容易，建议现在就做**

两侧数据**都已存在**：

| 侧 | 已有字段 ★ |
|---|---|
| 需求侧 | `Job Card`：`time_required`、`expected_start_date`、`expected_end_date`、`workstation`、`workstation_type`、`total_completed_qty`、`pending_qty`、`scheduled_time_logs` |
| 产能侧 | `Workstation`：`working_hours` 子表（`start_time`/`end_time`/`enabled`/`hours`）、**`production_capacity`**（并行槽位数）、`holiday_list`、`total_working_hours`、`plant_floor`、`status`/`disabled` |

**故负荷报表的本质是**：按工作中心与时间桶汇总 `Job Card.time_required`，对比 `working_hours × production_capacity` 算出的可用产能。**确定性聚合 + 对比，无搜索、无优化。**

**AI 做这档特别顺**——输入输出明确、逻辑可判定、可写测试。量级约一个 Query Report、200-400 行。

**⭐ 而这一档就补上了 MRP II 最核心的缺口（产能可见性）**：能看到"这周三个工作中心超载 40%"，而这是目前**完全没有**的东西。

**档 2：优先级字段 + 换型矩阵 —— 中等，真风险在侵入性**

加字段本身 trivial；**难的是让排产真的尊重它们**——要改 `job_card.py` 的排程逻辑（`:400-434 has_overlap` 那套 FCFS 顺延）。

风险不在写代码，在于：① **这是覆盖上游核心逻辑，每次 erpnext 升级都要重新对**；② 本项目已查明 `base_document.py:120-126` 的多 app 串联覆盖会**静默丢弃前者**。

换型矩阵对弹簧厂是真需求（线径/材质/卷簧方向切换，**是工序对工序的矩阵而非单值 `setup_time`**），且 frePPLe Community 恰好**不做**换型优化，**故这块无论如何都要自己做**。

**档 3：有限产能优化排产 —— AI 的优势在这一档大幅下降，且现在做是错的时机**

这是组合优化问题，frePPLe 的 C++ 求解器是二十年产物。**但难点不在代码量，在三件 AI 帮不上的事**：

| # | 难点 | 为何 AI 帮不上 |
|---|---|---|
| 1 | **模型对不对** | 约束要反映真实车间，而**本项目从未实地考察**、弹簧资料为零、52 场景按行业通识生成。现在写优化器＝**对着猜出来的约束做优化** |
| 2 | **怎么验证结果"好"** | **无 ground truth**。排产方案好不好要车间主任看一眼说"这两个活不能排一台机"——**这类知识只能从现场来** |
| 3 | **稳定性** | 输入微调致排产结果天翻地覆会摧毁用户信任。**这不是 bug，是优化本身的性质** |

**⭐ 本步立的一条判断原则**：**AI 开发改变的是"写代码"的成本，不是"知道该写什么"的成本。** 档 1、2 的规格清楚、验证机械，故 AI 杠杆极大；**档 3 的规格模糊、验证要现场知识，正是 AI 杠杆最小处。**

**若真要做档 3，不该自己写求解器**：应用现成约束求解器建模。候选 **OR-Tools 的 CP-SAT**（Python 生态最自然、Apache-2.0）或 Timefold（活跃但 Java）。**⚠ OR-Tools 现状本轮未验证**，动手前须单独查一次。

**建议次序**：**档 1 现在做**（低风险高价值，**且它是档 3 的前置**——先能度量负荷才能优化负荷）；**档 2 在演示之后、通用版阶段做**；**档 3 等实地考察之后再判断要不要做**。

**⭐ 一条须防的目标漂移**：**不要把"补齐 MRP II"当成目标本身。** 目标是解决客户实际问题。**产能可见性可能解决 80% 的痛，而剩下 20% 的自动优化要付 10 倍代价、还得先有现场数据。** 很可能中小弹簧厂根本不需要自动优化排产——一张看得见超载的负荷表加人工调整就够了。

**③ ⚠ 一处既有记载可能有误，须复核**

★ Claude 本步读 `bom_operation.json` 发现它**有 `batch_size` 字段**（另有 `sequence_id`、`set_cost_based_on_bom_qty`、`fixed_time`）。而项目概况与 P1 概况记载「**`Routing` 无基准量**（无法表达"每 100 件耗时 X"）」——**而 `Routing` 用的正是 `BOM Operation` 作子表**。

**故该条记载可能与 LG-021 同型**（"grep 未找到即推定缺口"，已应验三次且全部是范围缩小方向）。**未复核，不改结论**，但若成立则自研清单可再去掉一项。**列为待复核项。**

**用户回答：** 待回答（A 步第四条件仍未满足）。
**结论：** frePPLe 判 `no-go`；自研分三档、建议只做档 1 与档 2 且档 3 缓到实地考察后；新增一条待复核项（`Routing` 基准量）。

#### 第 27 步：MRP II 判定溯源；全链路标准排查立项（六方向）；档 2 hook 可行性与 Routing 复核派出

**来源项目：** ERX-001
**适用面·状态：** 仅本项目·已落地

**① MRP II 判定的溯源（用户要求先看闭环实操记录）**

**提出者：** 用户
**背景：** 用户要求「先看一下闭环实操记录，看一下当初是怎么判定出要 MRP II 的」。

**结论：该判定不是泛论，而是从一个具体字段卡住引出的。**

**源头**：`R03-闭环实操/P1-S1-R3-Pai000协作记录.md:888`。触发点是 **`fixed_time`**。用户当时设想「Routing 写工序 + 用时 + 标准产量 + 固定工时」，记录判定这正是 **MRP II 的标准工艺路线模型**：

```
总工时 = 准备时间（Setup，换模调机装炉，不随批量变）+ 单件时间 × 数量
```

**具体卡在哪**：回火要表达「准备 90 分 + 单件 0」，卷簧要表达「准备 20 分（换线调簧距）+ 每支 0.05 分」；而 **`fixed_time` 只有"固定"与"线性"两档、不能相加**，故只能二选一。旁证：SAP 工艺路线有基准数量（Losgröße）+ 准备/机器/人工三种时间类型，Oracle 与 Dynamics 同为 setup + run 结构。

**由此引出的四条缺口，全记在 `SH-P1S1005`**：

| 缺口 | 出处 |
|---|---|
| `setup_time` 缺失（工时模型二选一） | R3 第 15 步 |
| **工艺损耗不反算投料量**（scrap/yield factor） | LG-039，实证 SO 5000 → 完工 4750、缺 250 支 |
| **工序间数量链不通**（三张 Job Card 的 `for_quantity` 都是 5000） | LG-040，MRP II 标准是每工序有 Input/Output/Scrap 三栏 |
| `Routing` 无基准量 | `SH-P1S1005` 第 ③ 层 |

**⚠ 一处须明确的证据性质**：这些记录里 MRP II 的部分**均标注「行业通识，非本项目查证」**；R3 忠实度报告 `:143` 亦把「MRP II 标准做法 / SAP・Oracle 有无 scrap factor」列为**论述与外部知识、非本项目可重跑的事实**。

**故当初的判定是"拿行业标准对照出缺口"，不是读 ERPNext 源码得出的。** 而 R2 第 25 步查的是"读源码确认产能未参与计算"——**两者是互补的两条独立证据，方向一致**。这使 MRP II 这个判定的可信度比单一来源时更高。

**⭐ 关键发现：`SH-P1S1005` 早已登记了用户本轮要的那件事。** 该条原文含「**并由此展开一次全量排查：ERPNext 哪些常用流程（Routing / BOM 优先）未跟上行业现行标准，逐项列出并定二开范围**」，且唤醒条件标注「**全量排查须先做——它决定 ②④ 两阶段的二开范围，是 devBlueprint 的输入**」。

**故本轮的全链路排查不是新增需求，而是 S1 指定要在 devBlueprint 做的事被正式启动。**

**② Claude 的诚实交代：前两轮未覆盖全链路**

**提出者：** 用户提问 + Claude 回答
**背景：** 用户问「除了 MRP II，刚刚的调查有在从客户到生产到交互的全链路上发现其它的没有跟上标准的环节吗」（原话如此，"交互"应为"交付"之误；直引不替用户改字）。

**回答：没有。第 25 步只覆盖了生产计划与质量两块**，采购、库存、销售、财务成本、需求预测**均未查**。

**用户指令：每个方向派出至少一个子 Agent 全量排查。**

**六个方向与各自的查点**（Claude 拟、已下达）：

| # | 方向 | 重点查（按"记录层/计算层"模式设问） |
|---|---|---|
| 1 | 采购与供应商 | ABC 分类、经济订货批量 EOQ、供应商配额 quota arrangement、询价比价、框架协议。已知有 8 个 `Supplier Scorecard` DocType |
| 2 | 库存与仓储 | ABC/XYZ 分类、周期盘点 cycle counting、批次有效期预警、**安全库存是手填还是能自动算**、多级 BOM 可用量计算 |
| 3 | 销售与交付 | **ATP/CTP（可承诺量）——客户问"这单何时能交"系统能否算**、信用额度控制、价格阶梯与折扣体系 |
| 4 | 成本核算 | **标准成本 vs 实际成本的差异分析**（SAP variance analysis）、工序级成本归集、间接费用分摊 |
| 5 | 需求预测与计划 | 已知 `Sales Forecast` 仅 92 行无算法。查有无移动平均/指数平滑等、安全库存与预测误差的联动 |
| 6 | 工程变更与主数据 | ECN/ECO 工程变更、BOM 版本与生效日期、图纸与程序文件版本（已知 `drive` 补不上） |

**③ 用户纠正 Claude 一处笼统表述：档 2 的升级成本要分做法看**

**提出者：** 用户
**背景：** 用户问「档 2 靠 hook 也要每次升级重新对吗，直接覆盖某一个环节不行吗」。

**Claude 承认此前「每次升级都要重新对」讲得太笼统**，须按做法分档：

| 做法 | 升级要否重对 | 原因 |
|---|---|---|
| **加字段**（Custom Field / fixtures） | **不用** | 字段是数据，不碰上游代码 |
| **`doc_events` 挂钩子**（在 validate/on_submit 后追加） | **基本不用** | 第 23 步已查实**累加执行**；上游改自己的逻辑不影响你追加那段 |
| **`override_doctype_class` 覆盖整个类** | **要** | 你的类继承原类，上游改被覆盖方法的签名或内部调用就要跟 |
| 直接改 erpnext 源码 | **每次都要，最糟** | 升级即冲突 |

**故关键问题变成**：排产逻辑能否用 `doc_events` **追加**而非**覆盖整个类**？

**Claude 的推测（未查实）**：若排程结果写在字段上（`expected_start_date`/`scheduled_time_logs`），则可在它算完之后用 `on_update` 之类钩子**重算并改写那些字段**，不碰其方法；升级时只要字段名没变就不用动。

**用户指令：派一路查清。** **这条直接决定档 2 的长期维护成本**，故优先级高。

**④ `Routing` 基准量待复核 —— 用户指示派出**

第 26 步③提出：`bom_operation.json` **有 `batch_size` 字段**（★ Claude 已读码确认），而项目概况记载「`Routing` 无基准量」——两者矛盾，疑与 LG-021 同型（grep 未找到即推定缺口，已应验三次且全部是范围缩小方向）。**用户指示派出复核。**

**⑤ 第 5、6 条（侵入度分析 + 工作量与时间表）暂缓，先调查**

**提出者：** 用户
**背景：** 用户要求「列目前已决定要做的事 + 每件事的改造侵入度（能否用 App/Hook 解决）」与「列工作量 + 大致流程 + 参考时间表」。

**Claude 建议先调查后出表**，理由：这两份表**依赖第②条的答案**——若全链路排查再查出三五个缺口，清单与时间表都要重排，现在出的表下一轮就作废。

**用户回答：** **「先调查再出表」，同意。**

**⑥ 用户指令：做以上内容前先及时记录**

**提出者：** 用户
**结论：** 本步即该记录。**⚠ 这条是对讨论契约 §2 纪律 1（即时记录时序）的执行纠正**——第 26 步之后 Claude 先答了长篇分析再落档，次序反了。本步先落档再派 Agent。

**用户回答：** 六条指令如上。
**结论：** 本步落档后立即派出 **5 路**（采购与库存 / 销售与成本核算 / 预测计划与工程变更 三路承担六个排查方向——两两合并；另加档 2 hook 可行性、Routing 基准量复核各一路）。回来后一次性产出第 5、6 条要的侵入度分析与工作量时间表。**A 步第四条件仍未满足**（用户本轮又提出补充）。

**⚠ 收尾 §6 核出一处数值错，已改**：原记录此处写"派出 **8 路**"，**实际只派了 5 路**——六个排查方向被两两合并成 3 路（报告文件只有 5 份可证）。且用户第 906 条指令原话是「**每个方向派出至少一个子 Agent 全量排查**」，**故合并本身即未完全满足该指令**，写成 8 路会掩掉这一点。**下游若要按方向核排查完整度，须知道实际是 3 路覆盖 6 方向。**

#### 第 28 步：六路全链路排查回报；LG-021 连续五次应验；三个常驻文件按契约改写

**来源项目：** ERX-001
**适用面·状态：** 仅本项目·已落地

**① 六路排查全部回报（报告清单）**

| 路 | 报告 |
|---|---|
| 排程可扩展性 | [P1-S2-R2-A验证-排程可扩展性.md](P1-S2-R2-A验证-排程可扩展性.md)（79 行） |
| Routing 与工时模型复核 | [P1-S2-R2-A复核-Routing工时模型.md](P1-S2-R2-A复核-Routing工时模型.md)（65 行） |
| 预测与工程变更 | [P1-S2-R2-A排查-预测与工程变更.md](P1-S2-R2-A排查-预测与工程变更.md)（58 行） |
| 采购与库存 | [P1-S2-R2-A排查-采购库存.md](P1-S2-R2-A排查-采购库存.md)（约 60 行） |
| 销售与成本 | [P1-S2-R2-A排查-销售成本.md](P1-S2-R2-A排查-销售成本.md)（51 行） |
| frePPLe 验证 | 见第 26 步 |

**② ⭐ 档 2 的可行性答案：能用 `doc_events` 追加，不必覆盖类 —— 但 Claude 的前提推测错了**

**提出者：** Claude（Agent 调查 + 主 Session 复验）

**⚠ Claude 第 27 步③的推测被推翻**：曾推测"排程结果写在字段上，可用钩子改写那些字段"。**该前提错误。**

★ 主 Session 复验 `job_card.py:926-950 set_expected_and_actual_time`：`expected_start_date`/`expected_end_date`/`time_required` 是**从子表 `scheduled_time_logs` 各行取 min/max/sum 算出的派生量**，用 `self.set(...)` 而非 `db_set`；且全仓 **`db_set("expected_*")` 命中数为 0** ★，确认该函数是唯一赋值点。

**两条落地结论**：① **钩子要改子表 `scheduled_time_logs`，不能单改 `expected_*`**（单改会在下次 save 被 `before_save` 按子表重算回去）；② **⚠ 换型分钟数不能加在 `time_required` 上**——会被 `:950` 的 sum 覆盖，**必须体现为子表的行时长或额外行**。

**钩子执行顺序对本项目有利** ★：`document.py:1636` 的 compose runner **先跑类自己的方法体、再依次跑 app hooks**，故 **erpnext 逻辑永远先跑、我们的 handler 后跑**——正是追加式改写所需顺序。

**两个最有价值的钩子位**：**Work Order `on_submit`**（在 `create_job_card()` 整个方法体之后，是跨工序整批重排唯一的纯钩子位置）；**Work Order `validate`**（在排程之前，可"喂参数"——改 `operations` 行的 `time_in_mins`/`sequence_id`、按优先级改 `planned_start_date`，**完全不碰排程代码**）。

**三档判定**：

| 档 | 能做什么 | 升级要跟什么 |
|---|---|---|
| **(a) 纯 `doc_events` 追加** | **优先级 + 换型矩阵的绝大部分需求都落这里** | 只跟**字段名与子表结构**，方法签名不用跟 |
| (b) 覆盖类 | 只有**改变冲突判定本身**才必须。★ 复验 `has_overlap` 是**实例方法**（`job_card.py:400`）、**未 whitelist**。⚠ **由此推出"`override_whitelisted_methods` 管不到"这一步仍依赖未读的实现**——调查该路明确把「`override_whitelisted_methods` 实现代码未读」列为五项未查实之一，原记录把这条 caveat 丢了（收尾 §6 核出）。**(b) 档判定的承重点就在这里，开工前须补读** | 每次升级跟方法体，且**覆盖位一旦占掉即锁死其它 app** |
| (c) 第三条路 | ★ 复验 `Manufacturing Settings.disable_capacity_planning` 存在；关掉后 `schedule_time_logs` 不跑，`scheduled_time_logs` 成空白画布，可自建 DocType 存优先级/换型矩阵后自行排程回写 | 与 (a) 同级 |

**Claude 对 (c) 的保留**：(c) 要把工作站工时切片、节假日、并行产能**全部自己重新实现**，而这些 ERPNext 已做对。**为换型矩阵把这套全重写，代价可能超过收益。** 故**倾向 (a) 为主**，仅在 (a) 确实做不到时才考虑 (c)。**⚠ 调查方的立场与此相左，原记录未呈现**（收尾 §6 核出）：该路报告把 (c) 标为「**第三条路（建议重点考虑）**」，建议「主体走 (a) 并**认真评估 (c)**——它把算法收进自己家，**长期维护成本最低**；(b) 留作最后手段」。**两边意见不一致这件事本身要留给下游**，不能只留 Claude 那一侧。

**⚠ 一条该尽早实跑的**：`work_order.py:1244` 取 `scheduled_time_logs[-1]` 的约定——**重排后须保证末行确为最晚行**，否则 WO Operation 的 `planned_end_time` 与 `:1247` 的 `plan_days` 校验会抛 `CapacityError`。

**③ ⭐ LG-021 连续第四、五次应验——本轮推翻约四条既有判定，其中三条全推、一条部分推，方向都是范围缩小**

**⚠ 收尾 §6 核出原标题两处写宽，已改**：① **"六条"偏高**——下表第 6 行（`Workstation` 的 `over_heads`）纠正的是 **Claude 本轮写给 Agent 的任务书之误，不是既有判定**（记录自己在该行括号里就这么标了）；第 3 行经复验后结论是「**LG-054 原话成立**，只需补一句」，属补充而非推翻。真正能算的是 #1/#4/#5 全推 + #2 部分推。② **"全部是范围缩小方向"把断言扩到了没依据的那条**——原始对话里方向判断只覆盖两路（Routing 路、预测路）；而第 6 行的实际方向**相反**：由它推出「间接费用只能按工时/机时单一基准分摊，无法按产量/重量/材料成本」，是**把原以为有的能力削掉、缺口变大**，本步⑥ 也确实把它当新增缺口写进了项目概况。

| # | 原记载 | 复核结论 | ★ |
|---|---|---|---|
| 1 | `Routing` 无基准量 | **不成立**。`BOM Operation.batch_size` 即工时基准量，`work_order.py:1490-1497` 真消费 | ★ |
| 2 | `fixed_time` 两档不能相加故表达不了换型+单件 | **部分成立**。单行内不可相加成立；但 Routing 拆两行原生即可表达，`setup_time` 非必需 | ★ |
| 3 | 变体属性值非数值不可计算 | **部分不准**。`attribute_value` 确是 `Data`（原话成立），**但属性定义层原生有 `numeric_values`/`from_range`/`increment`** | ★ |
| 4 | 预测算法完全无 | **不成立**。`exponential_smoothing_forecasting`（264 行）实现一次指数平滑，**但结果不落库** | ★ |
| 5 | MRP 结果只是报表、无法驱动执行 | **不成立**。`:1303 make_order()` 分派到 `make_purchase_orders()`/`make_work_orders()`，各自 `new_doc().insert()` | ★ |
| 6 | `Workstation` 有 `hour_rate` 与 `over_heads`（**Claude 写给 Agent 的任务书里的错**） | **`over_heads` 是 Tab Break 标签、不是数值字段**。真来源是子表 `Workstation Cost` | ★ |

**⭐ 本步立一条规则（建议进长效）**：**凡要断言"原生没有 X"，默认假设是"可能有但藏在别处"**，须满足三条才下结论——① grep 了多个同义关键词；② 看过相关模块的**目录清单**（不只 grep）；③ 说明为什么它不可能在别的模块。

**本轮三个"藏法"很典型，值得记住**：预测算法藏在**报表**里（不是 DocType）；`batch_size` 藏在**成本节**且无 description（从工时视角看不见）；数值属性藏在**一个 Check 字段的条件分支**里。

**④ 一处对 Agent 越界断言的纠正（Claude 复验所得）**

预测那路称"变体属性值非数值不准"，**但它把两件事混为一谈**：★ 复验 `item_variant_attribute.json` 确认 `attribute_value` **就是 `Data`（字符串）**；Agent 举的 `numeric_values`/`from_range`/`increment` 是 **`Item Attribute`（属性定义层）**的字段，管的是"取值范围与步进约束"，**不是"存储值变成了数值"**。**故 LG-054 原话成立，只需补一句"范围与步进机制原生有、不必自建"。**

**⑤ "记录层/计算层"模式被部分推翻 —— 这是本轮方法论上最重要的修正**

该模式在质量、计划、库存三块成立，**但采购块有三处是真算法**：`Supplier Scorecard` 真能算分（★ 复验 `:49-55` 权重校验合计 100、`:73-74` `frappe.safe_eval` 解析公式、`hooks.py:468` 挂 daily 自动跑）、`Blanket Order` 累计量控制与价格锁定、`Item Lead Time` 确有消费方。**销售侧另有四项"以为缺、实际有完整计算层"**（信用额度硬拦、价格阶梯、副产品成本分配、成本卷积）。

**故该模式是"多处成立的观察"，不是普适规律。** 用它当排查视角有效，**但不能用它反推"某处必定缺算法"**。

**⑥ 全链路排查的新发现（已按契约落进 `docs/项目概况.md`）**

**两处两层皆无的洞**：**ATP/CTP**（零命中；**与"无 CRP"是同一个洞的两端——没有产能计划就算不出交期承诺**，故 CRP 负荷报表同时是 ATP 前置）；**ECN/ECO 工程变更**（erpnext 与 frappe 双双零命中，**已排除"被 `Workflow` 覆盖"**；对弹簧厂是硬缺口）。

**一段死代码**：`bin.py:56-62` 有 `"Standard Cost"` 分支并 import `item_standard_cost`，**而该模块全 bench 零文件、`"Standard Cost"` 不在任何取值域**（★ 复验 `valuation_method` options 仅 `FIFO/Moving Average/LIFO`）。**二开前应实机看该下拉，免得重复造。**

**性价比最高的一处二开**：再订货点推荐值算法**已存在于 `itemwise_recommended_reorder_level.py:29`**（`平均日出库 × lead_time_days + safety_stock`）**却不回写**。

**弹簧特有缺口（不在原清单内）**：★ 复验 `UOM Conversion Detail` 只有 `uom`+`conversion_factor` 两个实字段，**系数是物料级固定 float**；而弹簧 kg↔pcs 随线径与圈数变、同规格不同批次线密度还有差异。**直接影响领料与成本准确性。**

**一个坑**：**两套提前期字段并存**（`Item Lead Time.purchase_time` 与 `Item.lead_time_days`），**消费方不同**，二开须统一口径。

**⚠ 一条未查实须实机验的**：`Supplier Scorecard` 的**默认评分标准是否随安装自带 fixtures 未查**。鉴于 S1 已应验 fixtures 缺口（v16 把一批初始化搬进配置向导），**不宜按"自带"推定**；若不自带，"评分卡可直接用"的结论要打折。

**⑦ 三个常驻文件已按契约改写（用户裁决前先载入 `常驻文件契约.md`）**

按契约 §5 纪律 1「**改写优先于追加**」与 §1 判据 A「**同一事实的新版本必须覆盖旧版本**」，**不是加一句"已改判"，而是直接改写原句**：

| 文件 | 改了什么 |
|---|---|
| `docs/项目概况.md` | ① 「无优先级字段/朴素顺排」那条**整条改写**为「**落在 MRP 层、够不上 MRP II**」含有的/缺的/Workstation 产能模型三节；② 新增 MPS 提交必然失败（实跑）；③ 工艺损耗那条补「**库存层其实是通的、不通的只是计划层**」并合并原 LG-040 为同一缺口两面；④ **新增 8 条全链路发现**（记录层/计算层总纲、两处两层皆无的洞、标准成本死代码、间接费用单一基准、UOM 批次级缺失、质量能力实际分布、预测开环、两套提前期字段） |
| `docs/01-需求摸底/P1-概况.md` | R5 那 5 项待排序中**两项打删除线并附复核表**（Routing 基准量不成立、`setup_time` 降为便利性改造），并指出 **LG-055 的前提已变**——真正的前置是换型矩阵 |
| `S01-场景摸底/P1-S1-概况.md` | `SH-P1S1005` 的 **② ③ 两层各打删除线并改写**：③ 由"加基准数量字段"改为"**解耦工时基准量与任务单拆批粒度**"、量级下调；② 降级为"便利性改造" |

**用户回答：** 「好的」（同意先改写常驻文件再出表）。
**结论：** 六路排查全部落档、三个常驻文件已按契约改写。**下一步出用户第 5、6 条要的三样**：已决定要做的事清单、每件的侵入度（App/Hook 能否解决）、工作量与参考时间表。

---

#### 第 29 步：侵入度与工作量表出炉；用户五条裁决 + 一问重排阶段 A；zelin 抄用与官方科目表两处实测推翻原设想

**来源项目：** ERX-001
**适用面·状态：** `仅本项目·已落地`

**⓿ 上一轮的交付（第 5、6 条的答案）**

**提出者：** Claude
**背景：** 第 27、28 步落档完毕，按用户「5+6、先调查再出表」与「按单人AI开发的人日给」出表。
**结论：** 产出 [P1-S2-R2-A侵入度与工作量.md](P1-S2-R2-A侵入度与工作量.md)（120 行）。**38 项**，侵入度分 L0-L5 六级。

**关键结论**：**L5（改上游源码）0 项，L4（hook 覆盖，升级须跟方法体）仅 2 项**——自制科目表进建公司下拉、工时基准量解耦。**其余 36 项全可用追加式（L0-L3）解决**，即用户第 5 条问的「能否尽量用 App 覆盖或 Hook 解决」答案是**基本能**。

原总量：演示前 24–38 人日 / 通用版 39–59 / 更后 30–60+。

三条排期建议：① **B2 插到 B1 之前**（3.5–4 人日拿再订货点+安全库存+覆盖自检，第 20 项算法现成只差回写，性价比全清单最高）；② **A3 译名是阶段 A 关键路径**（8–13 人日占三分之一，精确档须读码故不可压缩）；③ **第 38 项优化排产不要排期**（实地考察前排期等于给猜出来的约束做优化）。

**① 译名·覆盖档能否直接照抄 zelin-tech**

**提出者：** 用户
**背景：** 用户问覆盖档（全量无缺口）能否直接照抄 zelin 的翻译，以压缩工作量。

**实测（可复现）**：提取 zelin `translations/zh.csv` 第一列共 **18695 个唯一源词**，与各 app `locale/zh.po` 的**未译 msgid** 做 `comm -12` 精确交集：

| App | 未译条目 | zelin 命中 | 覆盖率 |
|---|---|---|---|
| erpnext | 1776 | **1416** | **80%** |
| frappe | 339 | 179 | 53% |
| hrms | 151 | 43 | 28% |
| frappe-crm | 688 | **6** | **0.9%** |
| helpdesk | 649 | **4** | **0.6%** |
| insights | 331 | **1** | **0.3%** |
| raven | **1867（全部）** | — | **无 `zh.po`，只有 `main.pot`** |

复现：`awk -F',' '{k=$1;gsub(/^"|"$/,"",k);print k}' Reference/zelin-tech-erpnext_china/erpnext_china/translations/zh.csv | sort -u`，po 侧用 awk 抽 `msgstr` 为空的 `msgid`，两侧 `sort -u` 后 `comm -12`。

**结论：能抄 ERPNext 本体（八成缺口），但抄不到本轮新增的四个 app。** CRM/Helpdesk/Insights 三者 1668 条缺口 zelin 只命中 11 条；Raven 1867 条零起点。**真正要自己译的是 3500+ 条。**

**抄之前须洗两处**：

1. **HTML 实体污染 169 行**。`get_translation_dict_from_file`（`frappe/translate.py:196-217`）只做 `\n` 替换与 `strip()`，**不做 HTML 反转义**，故 `&#39;收件人&#39;未指定`、`&lt;HEAD&gt; HTML` 会原样显示给客户。复现：`grep -cE '&(#[0-9]+|amp|lt|gt|quot|#39);' <该csv>` = 169。
2. **914 组撞名**（R1 V-09a 已测，同一目标词被 ≥2 源词占用）。

**机制侧已查实可行**：`get_translations_from_apps`（`translate.py:172-187`）按 `installed_apps` 顺序逐 app `translations.update(...)`，**我们的 app 排最后故能覆盖上游**；**但同一 app 内 `mo` 在 `csv` 之后 update（`:180-181`），故我们只放 `zh.csv`、不放 `zh.po`**。

**⚠ 纠正 R1 的一处记载**：zelin 是 **MIT**（`license.txt`），**可并入本项目 app**（保留许可文本与署名；其版权行是未填模板 `Copyright (c) [year] [fullname]`，按仓库 owner 署）。R1「许可证矛盾」那条**指的是 saoxia，不是 zelin**。

**⚠ 讨论中发现：Flow 补不进翻译体系。** Flow 无 `locale/` 也无 `translations/`，是纯 Vue 前端（`frontend/`），**不走 frappe 的 po/csv 机制**。汉化须改前端源码或自建 i18n 层。它排在「更后」故不冲突，但「两套都要接入」这笔账须记。

**用户回答：** 提问，未预设答案。
**结论：** **可抄且许可允许，但只覆盖 ERPNext 本体八成**；译名覆盖档人日**由 3–5 上调到 5–8**（多 3500+ 条 + 洗 169 行污染）。

**② 译名·精确档延后到演示后**

**提出者：** 用户
**背景：** 精确档（读源码确认按钮实际作用再按大陆习惯译）原估 5–8 人日、是阶段 A 关键路径。用户裁决延后。
**用户回答：** 精确档先延后，留到演示后。
**结论：** **接受**。阶段 A 减 5–8 人日，**关键路径消失**。

**但 Claude 提出一道保险并建议保留**：覆盖档是机械批量补译、质量不可控，而 LG-063 的教训同型（*漂亮但错误的数字比不演示更糟*）——客户看到译错的提交按钮比看到英文更伤可信度。**建议只抽检演示线上会改变数据的按钮**（提交/取消/过账/完工入库类），约 20–40 词，**0.5–1 人日**。

**③ CRM 接入 + 销售漏斗提到 100 条数据集之前**

**提出者：** 用户
**背景：** 原表把 CRM 排 A6、数据集排 A4。用户指出销售漏斗流程本身也是演示的一部分。
**用户回答：** CRM 接入 + 销售漏斗要放到 100 条全链数据集 + 生成器之前。
**结论：** **接受，且原表次序确实是错的**——漏斗是数据链起点，`Deal → Quotation → Sales Order` 不通则 100 条无法从漏斗起头生成。**新增一条硬次序：CRM → 数据集。**

**④ 「先直接照抄官方科目表」—— 手段不成立，但意图成立且必须执行**

**提出者：** 用户
**背景：** 用户要求中国科目表提到数据集之前，并「先直接照抄官方的科目表，然后按需增加弹簧行业需要的，再生成对应数据」。

**实测（可复现）**：官方**确有**一张中国科目表 `erpnext/accounts/doctype/account/chart_of_accounts/unverified/cn_l10n_chart_china.json`，名字很正——`China - 中国会计科目表（财会[2006]3号《企业会计准则》）`，274 行 82 节点。**但四处全缺，抄不了**：

| 项 | 实测值 | 复现 |
|---|---|---|
| `root_type` | **82 处全部是空字符串 `""`** | `grep -oE '"root_type": "[^"]*"' <f> \| sort \| uniq -c` → `82 "root_type": ""` |
| `account_type` | **0 处** | `grep -c '"account_type"' <f>` → 0 |
| `account_number` | **0 处** | `grep -c '"account_number"' <f>` → 0 |
| 树结构 | **82 个顶层节点直挂 `tree`**，不是五大类树 | 缩进层数分布 4/8/12/16，`8` 有 164 处即 82 个顶层节点。⚠ **"全部平铺"这个说法过头了**（收尾 §6 核出后回文件实测）：`应交税费` 带 **11 个子节点**，其下 `应交增值税` 还有 **10 条明细**（减免税款/出口抵减内销产品应纳税额/出口退税/已交税金/未交增值税/转出多交增值税/转出未交增值税/**进项税额**/进项税额转出/**销项税额**）。**全文 103 节点、最大深度 3**，82 只是带 `root_type` 的顶层数。**结论"须自建"不变**（根层 `root_type` 全空仍会 `throw`），但**可复用的不止 82 个中文名——那段税金子树的层级与命名同样可抄，且正好是第 32 步判定 NORM 缺的那一层** |

**且它在 `unverified/` 下，默认不出现在建公司下拉**：`chart_of_accounts.py:120-122` 与 `:148-150` 写死 `folders = ("verified",)`，仅当 `frappe.local.flags.allow_unverified_charts` 为真才加 `unverified`；**而全 bench 无任何写入点**（grep 只命中 `chart_of_accounts.py` 的 4 处读取与 `account.py:108` 一处读取，**零赋值**）。`verified/` 下无任何 `cn_*`/`china*` 文件。

**这正是 R1 V-02 测出的「拿现状直接建公司是硬失败」**——`create_charts` 的 `_import_accounts` 用 `root_type` 推 `report_type`（`chart_of_accounts.py:31-36`），全空即每个科目都建不出来。

**⚠ 这是 LG-067 错误型的又一例**（查到一个名字像的文件就推定它能用）。**Claude 自陈**：上一轮把「官方有中国科目表」当可抄依据，未验其内部字段。

**可复用的只有那 82 个科目中文名**——财政部 2006 准则官方用词，省掉「叫什么」的争议。树结构、`root_type`、`account_number`、`account_type` 四项须自建，**即第 13 项那 3–5 人日压不成「照抄」**。

**用户回答：** 中国科目表放到数据集之前，先照抄官方再按需增加弹簧行业科目。
**结论：** **提前的意图接受并且是必然的**——V-01/V-02 的硬次序约束本就是「公司一旦开始记账，科目表不能换」，故第 13 项从阶段 B 挪进阶段 A 不是可选项。**但「照抄」不成立，仍是 3–5 人日自建**（可复用 82 个官方中文名）。**新增硬次序：科目表 → 建演示公司 → 数据集。**

**⑤ 中国财税不需资质的部分全部提到演示前**

**提出者：** 用户
**背景：** 用户希望「整个中国财税系统不需要资质的部分，都在演示前以 App 的形式做出来」。按 V-05 的口径，**连开票接口都在「不需资质」范围内**（诺诺沙箱对未签约方开放，实测 `HTTP=200` + 业务层错误码 `070501` 而非 401/403）。

**选项：**

| 选项 | 描述 | 优点 | 缺点 |
|---|---|---|---|
| A 含开票接口 | 财税六块 + 开票沙箱对接 + 票面 Custom Field + 红冲 | 客户会计当场问专票能答 | **+4–8 人日，且前置是未知量**——V-05 的 `go` 是**推断非实测**（未开出测试票；签名算法/必填字段/返回报文零实测），须先自行注册拿沙箱凭据，**可能卡在企业认证** |
| B 不含开票接口 | 财税六块 + 月末结转 | 去掉唯一「前置未知」项，不压关键路径 | 客户问专票答不上（R1 复核建议点过的洞） |

**用户回答：** 开票接口不进演示（选 B）。
**结论：** **开票接口出范围**，V-05 的推断性 `go` 不再压在关键路径上。**转为摸底问点**（现场问「你们开票现在怎么走、用哪家」），归第 14 项摸底问点清单。

**⚠ 讨论中发现：多一项原表没有的工作。** V-04 已明确原生 Tax Template **表达不了进项税额转出与未交增值税月末结转**（属期末账务，需 Journal Entry 或自有逻辑）。原表把财务按六块列，**漏了这一块**，补为独立项 **2–4 人日**。

**⑥ AI 演示前接入 Raven；演示数据即那 100 条**

**提出者：** 用户
**背景：** 用户指出「之前已试过经由 LiteLLM 调用的 AI 能够调工具」，故 AI 演示数据就用那 100 条数据集。Claude 上一轮把「LiteLLM 支不支持 `/v1/responses`」列为关键未知、并称不确定 MCP 等七类工具是否被过滤。

**实测（两轮，第二轮推翻第一轮的一半）**：

**第一轮**：`_filter_tools_for_provider`（`agents_integration.py:348-374`）过滤的 `hosted_tool_types` 是 `CodeInterpreterTool/FileSearchTool/WebSearchTool/ComputerTool/HostedMCPTool/ImageGenerationTool/LocalShellTool` 七类，**`FunctionTool` 不在其中**；且 `_setup_client`（`:63-71`）对 Local LLM 走 `use_responses=False`（注释明写 `Force use of chat/completions endpoint`），**根本不碰 `/v1/responses`**。→ 故用户结论成立，**Claude 原标的那个风险不存在**。

**第二轮自查发现第一轮引错了依据**：`_create_crud_tools`（`:179`）里那六个 `@function_tool`（`get_document_tool`/`search_documents`/`create`/`update`/`delete`/`submit`）**是死代码——全仓零调用者**（`grep -rn "_create_crud_tools" raven/` 只命中定义行）。**Claude 自陈这是又一次 LG-067**：看到一段名字对的代码就当它在运行。

**真正生效的是 `create_raven_tools`**（`raven/ai/sdk_tools.py:12-56`）：遍历 `bot.bot_functions` → 逐条查 `Raven AI Function` 记录 → 按 `type` 映射到内置 handler（`Get List`→`handle_get_list`、`Get Document`/`Create`/`Update`/`Delete Document` 各有 handler，`Custom Function` 用记录里的 `function_path`）。

**而 Raven 不带任何预置记录**：`hooks.py` **无 `fixtures` 键**，`raven_ai_function/` 下除 DocType 定义外**零 json**。**故五个内置 handler 虽实现好了，须我们自己在站里建 `Raven AI Function` 记录并挂到 bot 上**，AI 才拿得到工具。

**`handle_get_list` 的能力边界已读全**（`sdk_tools.py:486-600`）：签名 `(filters, fields, limit=20, order_by="modified desc", reference_doctype)`，做字段白名单校验（非法字段**静默忽略并回 warning**，不报错）、支持 `"field >"` 这类带操作符的 filter key，末端调 `frappe.get_all(...)`。**两处须知**：① **无聚合、无 group by、无 join**——「哪个供应商货美价廉」这类须跨表比较历史成交价的分析，**得靠 AI 自己多次调用再在上下文里算**，或走 `Custom Function` 自写查询工具；② **`frappe.get_all` 强制 `ignore_permissions=True`**（`frappe/__init__.py:1383-1404`），即**此工具绕过权限**，演示无妨但上生产前须评估。

**用户回答：** 已试过经 LiteLLM 的 AI 能调工具，故 AI 演示数据用那 100 条数据集。
**结论：** **用户结论成立**——工具不被过滤、不碰 `/v1/responses`，`Get List` 足以支撑「分析漏斗找单子」。**但「现成可用」不成立**：须建 `Raven AI Function` 记录 + 配 bot + 出 fixtures，**Raven 接入由 2–4 上调到 3–5 人日**（新增的是配置与 fixtures，非代码）。**两条新未确认项**：跨表比价可能须 `Custom Function`；`get_all` 绕权限须在上生产前处置。

**产物快照：修订后的阶段 A（完整形态，替代原表「一、演示前必做」）**

| 块 | 内容 | 人日 |
|---|---|---|
| 原 A 项（减精确档、译名覆盖档上调） | ①术语标准 ②覆盖档5–8 ④费用科目 ⑤工艺损耗 ⑥导航 ⑦行业参数 ⑧样本AB ⑨100条数据集 ⑩演示脚本 ⑪心跳自检 ⑫CRM | **21–33** |
| 中国财务（不含开票） | 科目表3–5 / 增值税2–3 / 下拉1–2 / 两表2–3 / 现金流4–6 / 银行对账3–5 | **15–24** |
| **新增** 月末结转 | 进项税额转出 + 未交增值税（V-04 明确原生表达不了） | **2–4** |
| Raven 接入 | 含建 `Raven AI Function` 记录 + 配 bot + fixtures；1867 条翻译已计入译名 | **3–5** |
| 精确档抽检保险 | 20–40 个会改数据的按钮 | **0.5–1** |
| **阶段 A 合计** | | **41.5–67**（⚠ 原写 41–66 是加总错，收尾 §6 核出并改：21+15+2+3+0.5=41.5、33+24+4+5+1=67。**第 30 步引的"43–68"是含另两项调整后的口径，与本表这个中间值不是同一个数**） |

**四条硬次序（原三条 → 现四条，LiteLLM 那条验证已不需要）**：
1. 术语标准 → 译名覆盖档 → 演示脚本
2. 费用科目 + 工艺损耗 → 样本 + 数据集
3. **科目表 → 建演示公司 → 数据集**（新）
4. **CRM 接入 → 数据集**（新）

**故 100 条数据集是整个阶段 A 的汇流点**——科目表、CRM、AI 能力三者任一未定，建出的数据就得重建。**原表排 A4，应挪到阶段 A 最后。**

---

#### 第 30 步：zelin 财税模块实测可直接接入；官方科目表"不可用"的**理由**被推翻（判定仍成立，LG-067 第三次）；三 App 自带 zh.po 推翻译名工作量

**来源项目：** ERX-001
**适用面·状态：** 仅本项目·实测结论

用户四条：① 澄清"照抄官方科目表"只指**中国官方标准科目表**，弹簧与客户特定科目留到实际运行时慢慢加；② 问"自制科目表进建公司下拉""工时基准量解耦"分别什么意思；③ 调查 zelin 中国财税模块能否直接接入、有无可直接照抄的**内账**逻辑；④ **先接入 CRM、HRMS、Insights、Raven 四个 App 并全部纳入覆盖档翻译**，zelin 等③的结果决定——能直接用最好，不能用就参考后重写 App。

##### ① 我第 29 步对官方科目表的**推理过程**是错的——判定（不可用）仍成立（LG-067 第三次应验）

第 29 步我说官方 `unverified/cn_l10n_chart_china.json`「`root_type` 82 处全空」故不可用。**"全空"这个观察对，"因此不可用"这个推论错。**

读 `chart_of_accounts.py:20-22`：

```python
def _import_accounts(children, parent, root_type, root_account=False):
    for account_name, child in children.items():
        if root_account:
            root_type = child.get("root_type")
```

`root_type` **只在 `root_account=True` 那一层读取**，然后作为参数向下递归继承（`:66` `_import_accounts(child, account.name, root_type)`）。`Account.validate` 侧同理——`account.py:167-173` 从 `parent_account` 继承 `root_type`。**故非根节点 `root_type` 为空是正确约定，不是缺陷。** 实测 zelin 四份科目表全都只在根节点填 `root_type`（`cn_smes` 266 节点仅 6 处非空、`cn_norm` 353 节点仅 7 处非空），**印证这就是标准写法**。

**官方那份的真问题是别的**：实测 `grep -nE '^ {1,4}"'` 只有 `country_code`/`name`/`tree` 三个顶层键，**82 个节点全部直挂 `tree` 之下**——即全部是根节点，而根节点的 `root_type` 全空。`create_charts` 在根层 `root_type = child.get("root_type")` 取到 `""`，`account.py:488-492 validate_mandatory` 即 `throw("Root Type is mandatory")`。**所以它确实建不起来，但原因是"没有树只有平铺的 82 个根"，不是"非根节点没填 root_type"。**

**这是 LG-067 的第三次应验，且这次是在我自己引用 LG-067 自我标记的同一步里犯的**——第 29 步我一边写着"这是 LG-067 第二次"，一边对同一个文件做了第二个未验证推论（把"字段空"直接等同于"机制要求它非空"）。**教训升级**：自我标记 LG-067 不构成对该次判断的豁免，标记本身也要验。

##### ② 用户"照抄官方标准科目表"的目标可达成，但载体不是官方那份文件

用户澄清后目标很清楚：**要财政部标准科目表，行业与客户科目后补。** 这个目标 zelin 已经做完了——`cn_smes_chart_of_accounts2024.json`（小企业会计准则 2024，266 节点）与 `cn_norm_chart_of_accounts2024.json`（一般企业会计准则 2024，353 节点）**都是完整可用的树**：

| 文件 | 准则 | 节点 | 根 | 最大深度 | 叶子 | 叶子有 account_number | 叶子有 account_type |
|---|---|---|---|---|---|---|---|
| `cn_smes_..2024` | 小企业会计准则(2024) | 266 | 6（资产/负债/权益/成本/收入/费用） | 4 | 225 | **225（100%）** | 183（81%） |
| `cn_norm_..2024` | 一般企业会计准则(2024) | 353 | 7（多"共同类"） | 4 | 294 | **294（100%）** | 198（67%） |
| `cn_sme_coa` | 小企业会计准则（旧） | 190 | — | — | — | — | — |
| `cn_cnpo_..2025` | 民间非营利组织(2025) | 217 | — | — | — | — | — |

**四份全部 `country_code: cn`**，根节点 `root_type` 正确（注意「成本类」映射为 `Asset`，这是对的——生产成本是资产类）。**故第 8 项从"自建五大类树"降级为"选一份 + 补弹簧科目"，3–5 人日 → 1–2 人日。**

**推荐 `cn_smes_chart_of_accounts2024`（小企业会计准则 2024）**，理由：叶子 `account_type` 覆盖率 81% 高于 norm 的 67%；小企业准则对弹簧厂这个规模更贴合；且增值税明细科目齐全（实测含 进项税额 2221001 / 销项税额 2221005 / 转出未交增值税 2221003 / **进项税额转出 2221007** / **未交增值税 2221020** / 待抵扣进项税额 / 待认证进项税额 等 19 个二三级科目）。

**⚠ 但用户须裁决准则版本**——这不是技术选择。小企业准则与一般企业准则的报表格式、科目设置都不同，且**公司一旦开始记账科目表不能换**。客户实际执行哪套准则应现场确认，归第 21 项摸底问点。

##### ③ 回答用户问的两个术语

**「自制科目表进建公司下拉」**：建公司时有个「Chart of Accounts」下拉，用户要在里面看到中国科目表才能选。该下拉的内容由 `get_charts_for_country()` 生成，它**只扫 `apps/erpnext/.../chart_of_accounts/verified/` 目录**，而且只收文件名以国家码开头的（`fname.startswith(country_code)`）。我们自己 app 里的 JSON 它根本不看。所以"把自制科目表塞进那个下拉"需要覆盖这个方法——这是它算 L4 的原因（`override_whitelisted_methods` 后者胜出、占掉即锁死其它 app）。

**「工时基准量解耦」**：指拆开一个被复用的开关。实测 `work_order.py:1490-1497`：

```python
for d in data:
    if not d.fixed_time:
        if frappe.get_value("Operation", d.operation, "create_job_card_based_on_batch_size"):
            qty = d.batch_size
        if exploded: d.time_in_mins *= flt(qty)
        else:        d.time_in_mins /= flt(qty)
```

要表达"每 100 支耗时 40 分"，必须勾 Operation 的 `create_job_card_based_on_batch_size`。但**同一个开关还管任务单拆批**（`:2902-2906`）：

```python
def split_qty_based_on_batch_size(wo_doc, row, qty):
    if not cint(frappe.db.get_value("Operation", row.operation, "create_job_card_based_on_batch_size")):
        row.batch_size = row.get("qty") or wo_doc.qty
    row.job_card_qty = row.batch_size
```

勾了它，10000 支的工单就被拆成 100 张 Job Card（每张 100 支）。**所以"我只想说清工时基准量"和"我不想要一百张任务单"在原生里二选一。** 解耦即：加一个独立的工时基准量字段（或独立开关），让工时计算读它、拆批仍读原开关，两件事互不牵连。1–2 人日。

##### ④ zelin 中国财税模块：内账部分可直接接入（用户问③的答案）

**结论：能直接接入，且它做的正好是"不需资质的内账部分"**——全仓 `grep "Journal Entry"` 零命中，没有任何对外接口、没有开票、没有金税对接。许可证 MIT（`app_license = "MIT"`）。实测构成：

| 部件 | 形态 | 规模 | 可直接用 |
|---|---|---|---|
| 四份中国科目表 | JSON | 266/353/190/217 节点 | ✅ 完整可用（见①） |
| 科目表进下拉 | `override_whitelisted_methods` 覆盖 4 个方法 | `custom_account.py` | ✅ 机制已验（见下） |
| 增值税税模板 | `tax_template.json` + `utils.py` 落地 | 7 个 tax_category、销/进各 5 个模板 | ⚠ **有 bug**（见下） |
| 资产负债表 | Report + Settings DocType | 676 行 | ✅ |
| 利润表 | Report + Settings DocType | 367 行 | ✅ |
| **现金流量表** | **DocType**（可提交单据）+ **2 个子表**（`Cash Flow Item` / `Cash Flow Subtotal`，两者 `istable: 1`；⚠ 原写"4 个子表"错，收尾 §6 核出后回文件复查：`cash_flow.json` 只有 2 个 Table 字段，且 `Cash Flow Code` 是 fixtures 主数据**不是**子表） | 230 行 + `Cash Flow Code` fixtures | ✅ **V-06 的实证在此** |
| 缺口报表 | `bs_and_pl_missing_account` | 83 行 | ✅ 附加价值：查哪些科目没进报表 |
| 中文 UOM + 系统默认值 | `install.py` | 45 个中文单位 + 系统设置 | ✅ 顺带的 |
| Property Setter + Custom Field | fixtures | 3 份 | ✅ |

**科目表进下拉的完整机制**（正是第 9 项要做的事，zelin 已做完）：

```python
override_whitelisted_methods = {
    "erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_charts_for_country": "...custom_account.get_charts_for_country",
    "erpnext.accounts.doctype.account.chart_of_accounts.chart_of_accounts.get_chart": "...custom_account.get_chart",
    "erpnext.accounts.utils.get_coa": "...custom_account.get_coa",
    "frappe.desk.treeview.get_all_nodes": "...custom_account.get_all_nodes",
}
```

**四个方法，不是我第 29 步说的两个。** 我漏了 `get_coa`（建公司向导里预览科目树）与 `get_all_nodes`（树视图展开）。**且 `frappe.override_whitelisted_method` 在 v16 确实存在**（`frappe/__init__.py:1577`），zelin 用它在 `get_all_nodes` 里做二次派发。另有 `doc_events` 三个钩子接 Company 的 `before_insert`/`after_insert`/`on_update`——它**绕过原生建账流程**（`before_insert` 里设 `ignore_chart_of_accounts = True`），改在 `on_update` 里调自己的 `erpnext_china_create_charts`。**第 9 项由 1–2 人日降到 0.5（改路径常量），且"点了能用"这个未跑项由 zelin 的生产使用背书。**

**⚠ 实测发现 zelin 一个真 bug，照抄会踩**：`tax_template.json` 引用的科目号对不上科目表。逐条核验三个键：

| 税模板键 | 对应科目表 | 引用科目号 | 存在? |
|---|---|---|---|
| 小企业会计准则 | `cn_sme_coa.json` | 22210101 进项税额 / 22210108 销项税额 | ✅ 全对 |
| **小企业会计准则(2024)** | `cn_smes_..2024.json` | 2221001 进项 ✅ / 2221005 销项 ✅ / **222105 销项 ❌** / **22210005 销项 ❌** | **2 处不存在** |
| 一般企业会计准则(2024) | `cn_norm_..2024.json` | 22210190 待抵扣进项 / 22210210 待转销项 | ✅ 存在但**语义可疑**（待抵扣/待转不是常规进销项科目） |

坏的两条正是 **P13（13% 税率）的销项模板**——即最常用的那档。而 `utils.py:40-59 setup_tax_template` 整个包在 `try/except` 里、失败只 `frappe.log_error`，**故 P13 销项模板会静默建不出来**。这与 LG-063 同型（漂亮但错误比没有更糟）：演示时选了 13% 专票却没有税模板可用，是当场暴露的故障。**修它约 0.5 人日**（改两个科目号为 2221005）。

**故第 10 项增值税**：原生机制 V-04 已验 `go`，zelin 提供了现成的 7 档 tax_category + tax_rule 映射 + 含税/未税处理（它还补了原生没做的 `included_in_print_rate` 批量回写），**2–3 人日 → 1–1.5 人日**（含修 bug 与核对全部科目号）。

**⚠ 月末结转 zelin 也没做**：全仓无 Journal Entry、无结转逻辑，只在科目表里**备好了科目**（进项税额转出 2221007、转出未交增值税 2221003、未交增值税 2221020）。**第 11 项 2–4 人日保留不变**，但科目不用自己设计了。

##### ⑤ 接入 vs 参考重写：按用户判据「能直接用最好」→ 结论是直接接入

用户第④条的判据是"能直接用最好，不能用就参考然后重写 App"。**zelin 属于"能直接用"**，理由三条：

1. **MIT 许可**（`app_license = "MIT"`，license.txt 是未填 year/fullname 的 MIT 模板）——可并入我们自己的 app，保留许可证文本与署名即可。
2. **侵入方式与我们规划的一致**——它全部用 `override_whitelisted_methods` + `doc_events` + fixtures，**零处改上游源码**（L5=0）。
3. **它占掉的 L4 覆盖位正是我们本来要占的那几个**（科目表三方法 + treeview），不冲突。

**但"直接接入"不等于"整包安装"。** 建议**并入式接入**——把 zelin 的科目表 JSON、税模板、三张报表的 DocType 与 Report 抄进我们自己的 app，而不是 `bench get-app erpnext_china`。三条理由：

- zelin 的 `get_chart` 里**硬编码了自己的路径**：`os.path.join(bench_dir, "apps", "erpnext_china", ...)`。装它就得同时接受它的目录名，我们自己再加科目表还得放它的目录下。
- 它的 `install.py` 会**改全局设置**（`System Settings` 的 country/language/currency/timezone/rounding_method、`Global Defaults` 的 `disable_rounded_total`、把不在它 45 个中文单位列表里的 UOM **全部禁用** `frappe.db.set_value('UOM',{'name': ('not in', uom_list)}, 'enabled', 0)`）。这个副作用面太大，尤其禁用 UOM 那条会影响我们已建的物料。
- 它的 `doc_events` 接了 Company 三个钩子并**改写建账流程**，与我们后续要接的钩子在同一 DocType 上叠加，自己抄进来能控制顺序。

**并入工作量：1–2 人日**（抄文件 + 改路径常量 + 修税模板 bug + 剥掉不要的 `install.py` 副作用）。**这一项是新增的**，但它换来第 8/9/10/12/13/14 项合计从 15–24 人日降到 **8–12.5**（⚠ 原写 6.5–10.5 是加总错，收尾 §6 核出并改：1–2 + 0.5 + 1–1.5 + 1–1.5 + 1.5–2 + 3–5 = 8–12.5。**A-4 小计 11–18.5 与"净省 6–9.5"两处都对**，错的只是这一句局部算式）。

**⚠ 另一个可抄对象未查**：`Reference/saoxia-erpnext_china` 本轮未读（R1 曾记它有许可证问题）。若 zelin 有缺口应回查它。

##### ⑥ 用户第④条"四个 App 全部纳入覆盖档翻译"——实测推翻我第 29 步的译名工作量

第 29 步我说"CRM 688 / Helpdesk 649 / Insights 331 / Raven 1867 条要自己译，合计 3500+"。**这个数字的性质我说错了**——那不是"要从零译"，是"**现有 zh.po 里未译的条数**"。实测四个 App 的 `locale/`：

| App | 有 zh.po | 条目 | 已译 | 未译 | 完成度 |
|---|---|---|---|---|---|
| frappe-crm | ✅ | 1781 | 1093 | **688** | **61.4%** |
| hrms | ✅（另有 zh_TW.po） | 2252 | 2101 | **151** | **93.3%** |
| insights | ✅（另有 zh_TW.po） | 686 | 355 | **331** | **51.7%** |
| **raven** | **❌ 只有 main.pot** | 1867 | 0 | **1867** | **0%** |

**三个 App 自带 zh.po，上游已经译了一大半**（CRM 1093 条、HRMS 2101 条、Insights 355 条现成）。**HRMS 尤其好——93.3% 已完成，只差 151 条。** 这是用户第④条把 HRMS 加进来的意外收益：**它是四个 App 里翻译负担最轻的**。

**真正要自己译的是 3037 条**（688+151+331+1867），其中 **Raven 独占 1867 条占 61%**。fuzzy 条目为 0，说明已译部分没有标记待复核的。

**故第 6 项译名覆盖档的构成变了**：

| 来源 | 条数 | 处理 |
|---|---|---|
| erpnext 本体缺口 | 1776 | zelin `zh.csv` 命中约八成（19350 行 / 18695 唯一键），洗 169 行 HTML 实体污染 + 914 组撞名 |
| CRM | 688 | 自译（上游已给 1093） |
| HRMS | 151 | 自译（上游已给 2101） |
| Insights | 331 | 自译（上游已给 355） |
| **Raven** | **1867** | **全部自译，无 zh.po** |
| 合计自译 | **3037 + erpnext 未命中部分** | |

**人日不变仍 5–8**（HRMS 新进场带来 `main.pot` **2321** 条可译词，但 `zh.po` 已译到只差 **151** 条，与我原先把"3500 条"当全新译量的估算相抵）。⚠ **两个数字口径不同**（收尾 §6 核出原文未注明）：**2321 是 `main.pot` 的 msgid 数**（可译词总量），上表的 **2252 是 `zh.po` 的条目数**（扣表头后）——不是同一个量，不必对齐。**⚠ 但有个机制问题须先定**：三个 App 的翻译在它们自己的 `locale/zh.po`（编译为 mo），而我们的补译若放自有 app 的 `zh.csv`——按 `translate.py:172-187`，**后装的 app 覆盖先装的**，我们的 app 最后装故能盖上。但**同一 app 内 mo 盖 csv**，所以不能把补译塞进这些 App 自己的目录。**结论：补译全部落我们自有 app 的 `zh.csv`，不改这些 App 的 po 文件**（改了升级即丢）。

##### ⑦ HRMS 新进场带来的连带变化

用户第④条把 HRMS 加进接入清单。**这推翻了第 29 步"不为计件工资装 hrms"那条结论的前提**——当时的理由是"装 hrms 帮不上计件工资"（`COMPONENT_EVAL_GLOBALS` 只白名单 13 个数学函数、读不到自定义数据），**这个技术事实不变**，但既然 HRMS 因别的理由要装了，计件工资那项（第 32 项）的成本结构变了：**基础设施（Employee/Salary Structure/Salary Slip）现成，只需自建"从 Job Card Time Log 汇总计件量"的 Custom Function 或附加组件，3–5 人日 → 2–4 人日。**

**⚠ 但 HRMS 装了要付代价**：它会在导航里加一整套 HR 模块入口（考勤/请假/招聘/薪资），与第 22 项导航重整冲突——**演示时客户会看到一堆与弹簧生产无关的入口**。须在导航重整里把它折叠或隐藏。**第 22 项 2–3 人日 → 2.5–3.5 人日。**

**产物快照：第 30 步后的阶段 A 修订（增删对照）**

| 项 | 第 29 步 | 第 30 步 | 变动理由 |
|---|---|---|---|
| **新增** 并入 zelin 财税模块 | — | **1–2** | 抄文件 + 改路径 + 修税模板 bug + 剥 install.py 副作用 |
| 8 中国科目表 | 3–5 | **1–2** | zelin 四份现成完整树，改为"选一份 + 补弹簧科目" |
| 9 科目表进下拉 | 1–2 | **0.5** | zelin 已实现四方法覆盖，改路径常量即可 |
| 10 增值税 | 2–3 | **1–1.5** | zelin 现成 7 档，含修它的 P13 销项 bug |
| 11 月末结转 | 2–4 | **2–4** | zelin 未做，仅备好科目 |
| 12 资产负债表+利润表 | 2–3 | **1–1.5** | zelin 现成（676 + 367 行） |
| 13 现金流量表 | 4–6 | **1.5–2** | zelin 现成 DocType（V-06 实证来源） |
| 14 银行对账 | 3–5 | **3–5** | zelin 未做 |
| **A-4 小计** | **17–28** | **11–18.5** | **净省 6–9.5 人日** |
| **新增** HRMS 接入 | — | **0.5–1** | 用户第④条 |
| 22 导航重整 | 2–3 | **2.5–3.5** | 须折叠 HRMS 带来的 HR 入口 |
| 6 译名覆盖档 | 5–8 | **5–8** | 构成变（三 App 自带 zh.po）但总量相抵 |
| 32 计件工资（**属阶段 B**） | 3–5 | **2–4** | HRMS 的 `Additional Salary` 省掉发放侧。⚠ **本步也改了阶段 B**（收尾 §6 核出本快照原只写"阶段 A 修订"、漏落此项）：**B3 工时与工序 13–21 → 12–20，阶段 B 小计 29–46 → 28–43** |
| **阶段 A 合计** | **43–68** | **38–60** | 〔落表时复核加总，原写 38–63 是笔误：A-4 净省 6–9.5、A-5 +0.5–1、A-7 +0.5，42.5–68 → 37.5–60〕 |

**新增一条待用户裁决**：**会计准则版本**（小企业 vs 一般企业，影响科目表选哪份、报表格式，且开始记账后不可换）。

**另提示一条已定项的新代价（不是待裁决）**：**HRMS 用户第④条已无条件下令接入**（「先接入CRM、HRMS、Insights和Raven，并且都纳入到覆盖档翻译」——那句"看 zelin 等三个的调查结果再定"限定的是 **zelin 的接入方式**，不是 HRMS 是否装）。本步新查出的代价是**导航污染**（会加整套 HR 入口）。**⚠ 原记录把它降格成"待裁决②"，收尾 §6 核出并改** —— 用户已下的指令不该退回待裁决栏，该记为"已定，提示新代价请复核"。（第 32 步用户又明确"真装"，是对该代价的复核确认。）

---

#### 第 31 步：两份准则本就并存、真卡点是报表 Settings 单例；HRMS 省的是发放侧不是计算侧

**用户两问**：① 不能做成两套都加进预设、使用时可选吗；② 「装 HRMS 让计件工资便宜 1 人日」是什么意思，原本要自己写、装了就不用写了吗。

**两问都指向第 30 步表述不准。逐条查证。**

---

##### ① 两套并存 —— 分三层看，前两层本就可选，卡在第三层

**Layer 1 建公司下拉 ✅ 已并存**：zelin `get_charts_for_country`（`custom_account.py:195-235`）扫自己的 `custom_accounts/{chart_of_accounts,custom_of_accounts}` 两个目录，**把所有匹配 `country_code` 的 chart name 全部 append 进 `charts`**。四份科目表本来就全在下拉里。**「两套都加进预设」不是待做工作，是 zelin 现状。**

**Layer 2 税模板 ✅ 已并存**：`tax_template.json` 本就**以 chart name 作键**（小企业会计准则 / 小企业会计准则(2024) / 一般企业会计准则(2024) 三键并列），每键配自己那套科目号。

**Layer 3 财务报表 ❌ 这层卡死**：
- `Balance Sheet Settings` 与 `Profit and Loss Statement Settings` **都是 `issingle: 1` 单例**，字段里**无 `company`、无准则维度**（前者只有 asset_row/liability_row/equity_row/items，后者只有 items）。
- 报表侧 `fin_balance_sheet.py:57,359` 与 `fin_profit_and_loss_statement.py:16,363` 全用 `frappe.get_single()` 取。
- 配置行 `Balance Sheet Settings Item` 的 `lft_name` / `lft_calc_sources` **直接引用科目名**。
- ⇒ **报表版式是全局一份且绑死一套科目编号。** 两家公司各用一套准则，资产负债表只能对其中一套配对。

**对照可见这是 zelin 的设计不一致而非必然**：`Cash Flow` 是普通 DocType 且**有 `company` 字段** ✅，现金流量表天然按公司分；`Cash Flow Code` 也是普通 DocType。**只有那两张表做成了单例。**

**故真成本落在这里**：要「两套都能出正确报表」，须把这两个 Settings 从 `issingle` 改为按准则（或按公司）分组的普通 DocType 并改报表取值侧 —— **估 +1–2 人日**。不是零成本，但也不贵。

**第 30 步把两件事混为一谈了**：

| 第 30 步写的 | 实际是两件事 |
|---|---|
| 「会计准则版本须用户裁决」 | **系统里放哪些** —— 可以都放，免费，zelin 已如此 |
| 「公司一旦开始记账不可换」 | **这家公司用哪份** —— 须选一份，且对该公司不可逆 |

只有第二件需要裁决。**且对演示公司这条约束很轻** —— 演示数据本就由脚本生成（第 19 项），选错了删库重建演示公司即可。**「不可换」的真实重量在客户正式部署那一次，不在演示。**

---

##### ② HRMS 省的 1 人日 —— 省发放侧，计算侧照写

**「装了就不用自己写」不成立。** 分两半：

| | 不装 HRMS | 装 HRMS |
|---|---|---|
| **计算侧**：从 `Job Card Time Log` 按 `completed_qty` × 工序单价汇总出每人计件额 | 自己写 | **照样自己写** |
| **发放侧**：工资单据 / 汇总 / 审批 / 打印 / 与其它薪资项合并 | 自建一整套 | **省掉** |

**计算侧不可省的硬理由已复核**：`hrms/payroll/utils.py:45-59` 的 `COMPONENT_EVAL_GLOBALS` **正好 13 项**（`int` `float` `long` `round` `rounded` `date` `getdate` `get_first_day` `get_last_day` `ceil` `floor` `min` `max`），`_safe_eval` 只喂这些 globals 加一个 `data` —— **薪资公式里读不到 Job Card 的任何东西**。

**发放侧能省的具体接口**（比第 30 步说的「基础设施现成」更具体）：**`Additional Salary` 正是为「外部算出的金额」准备的注入口** —— 有 `salary_component` + `amount` + `payroll_date` + `overwrite_salary_structure_amount`，还有 **`ref_doctype` + `ref_docname`（Dynamic Link）可回指来源单据**。自算完写一条 `Additional Salary`，`Salary Slip` 自会收进去且留下溯源链。

**一处更正**：第 30 步说「Employee / Salary Structure / Salary Slip 基础设施现成」，其中 **`Employee` 本就在 erpnext**（`erpnext/setup/doctype/employee/employee.json`），装不装 HRMS 都有 —— 把它算进 HRMS 的好处里**夸大了收益**。真正随 HRMS 来的是 `Salary Slip` / `Salary Structure` / `Salary Component` / `Salary Structure Assignment` / `Payroll Entry` / `Additional Salary` / `Employee Incentive`（均在 `hrms/payroll/doctype/`）。

**故 3–5 → 2–4 的下调仍成立**，但理由须改写为「省掉发放侧单据体系」，不是「模块不用写了」。

---

##### 产物影响

| 处 | 改动 |
|---|---|
| 第 12 项（资产负债表 + 利润表） | 补 `issingle` 约束与「两套并存 +1–2 人日」的条件项 |
| 第 32 项（计件工资） | 理由改写为「省发放侧」，并更正 `Employee` 归属 |
| 第 5 节待裁决① | 从「选哪份准则」改为「**演示公司用哪份**（轻，可重建）+ **是否现在就要两套报表并存**（+1–2 人日）」 |
| 第 5 节待裁决② | HRMS 收益说明改写 |

**一条方法教训（LG-067 的又一形态）**：第 30 步把「不可逆」这个强约束贴在了一个**可重建对象**（演示公司）上。**约束的重量取决于挂在谁身上** —— 同一条「开始记账不可换」，挂客户正式库是硬约束，挂脚本生成的演示库近乎零成本。**凡断言约束，须连带说明它约束的是哪个对象、那个对象能不能重建。**

---

#### 第 32 步：一般企业准则不是小企业的超集（实测）；两条待裁决落定 —— 小企业(2024) + 真装 HRMS

**用户裁决**：① 一般企业会计准则若是小企业的超集就选一般企业，否则选小企业；② HRMS 真装。

**①的前提须实测。逐项比对两份科目表。**

---

##### 实测：不是超集，且在本项目最要紧的地方反而更差

**按科目号比 —— 几乎不相交**：

| | 节点 | 交集 | 仅 SME | 仅 NORM |
|---|---|---|---|---|
| 小企业(2024) | 266 | **9** | 257 | — |
| 一般企业(2024) | 353 | **9** | — | 344 |

**编号体系完全不同**：小企业用 4–7 位（`2221001`），一般企业用 5–8 位（`22210010`）。**故不存在编号层面的包含关系。**

**按科目名比 —— 共享 209 条，但两边各有独有**：SME 独有 **47** 条，NORM 独有 **122** 条。**决定性的是 SME 独有那 47 条 ⇒ NORM 不含 SME 的全部科目 ⇒ 超集关系被否定。**（⚠ 收尾 §6 核出原表述"双向都有独有 ⇒ 数学上已否定"落点不准：**NORM 独有 122 条与超集判定无关**——超集本就允许有额外项。否定超集只靠 SME 独有那一侧 > 0。数据无误，论证已收窄。）

**决定性缺口在增值税明细科目**（正是第 10、11 项要用的）：

| 科目 | 小企业(2024) | 一般企业(2024) |
|---|---|---|
| 应交增值税（二级） | ✅ `2221000` | ✅ `22210010` |
| **进项税额** | ✅ `2221001` | **❌ 无** |
| **销项税额** | ✅ `2221005` | **❌ 无** |
| **转出未交增值税** | ✅ `2221003` | **❌ 无** |
| **进项税额转出** | ✅ `2221007` | **❌ 无** |
| **已交税金** | ✅ `2221002` | **❌ 无** |
| 未交增值税 | ✅ `2221020` | ✅ `22210020` |
| 待抵扣进项税额 | ✅ `2221012` | ✅ `22210190` |
| 待认证进项税额 | ✅ `2221013` | ✅ `22210200` |
| 待转销项税额 | ✅ `2221014` | ✅ `22210210` |

小企业那份在 `应交增值税` 下挂了**完整的 10 条三/四级明细**；一般企业那份**只到二级就断了**，`应交税费` 下是平铺的税种，**缺的是进项/销项这一层**（⚠ 收尾 §6 核出原表述"无一条增值税明细"与本表自相矛盾——NORM 确有未交增值税/待抵扣/待认证/待转销项四条，只是不在 `应交增值税` 之下、且不含进项/销项这一对。已收窄）。（字符串核验：NORM 文件里「进项税额」**2 处命中分别在 `待抵扣进项税额` 与 `待认证进项税额`**（⚠ 原记录写"全在待抵扣内"并漏列后者，收尾 §6 核出后已回原文件复查补正）、「销项税额」1 处在`待转销项税额`内，「转出未交增值税」「进项税额转出」「已交税金」**零命中**。）

**这顺带解释了第 30 步记下的一个疑点**：当时记「NORM 的 tax_template 引用 `22210190`/`22210210`，存在但语义可疑」。现在清楚了 —— **因为 NORM 根本没有进项/销项科目，zelin 只能指向最接近的「待抵扣/待转」**。那是"尚未确认/尚未结转"的过渡科目，拿它当进销项是**记账语义错误**。

**故两份的 bug 性质不同，量级差一个数量级**：

| | bug | 修法 |
|---|---|---|
| 小企业(2024) | P13 两个模板把 `2221005` 误写成 `222105`/`22210005` | **改两个字符串** |
| 一般企业(2024) | 税模板指向语义错误的科目，且**正确科目在表里不存在** | **须先补建整套增值税明细科目，再重配模板** |

**NORM 唯一的实际优势是成本类更细**：58 节点对 24，按行业拆开（制造/农业/商贸/运输/施工…）。**但我们只用得上「制造企业成本」那一支**，而小企业那份的 `生产成本` + `制造费用` 已带 ERPNext 挂钩所需的 `结转库存`(`Expenses Included In Valuation`)、`结转资产`(`Expenses Included In Asset Valuation`)、`库存调整`(`Stock Adjustment`) 三个关键 `account_type`。**其余行业分支对弹簧厂是纯噪音。**

`account_type` 覆盖率复测确认：**SME 叶子 225 条有 183 条带 type（81%）**；**NORM 叶子 294 条有 198 条（67%）**。

##### 裁决落定

**① → 小企业会计准则(2024)。** 按用户规则「不是超集就选小企业」，且实测显示**在增值税明细这个本项目最要紧的维度上小企业是严格更优**，不只是"不劣"。

**② → 真装 HRMS。** 第 16.5 项 0.5–1 人日成立；第 32 项计件工资 2–4 成立（**省发放侧、计算侧照写**）。

**一处自我更正**：第 31 步在第 5 节写了「装则第 22 项相应加 0.5」，但第 22 项在同一轮已被改为 2.5–3.5 且正文明写含「折叠 HRMS 的 HR 模块」——**那 0.5 已经在里面了，再加就是重复计数**。删掉该句。故**阶段 A 合计 38–60 不变**。

##### 产物影响

| 处 | 改动 |
|---|---|
| 第 8 项 | 准则已定，去掉待裁决标记，补入超集实测结论 |
| 第 10 项 | 补入「选 SME 使该 bug 降为改两个字符串」 |
| 第 16.5 项 | 去掉「是否真装须裁决」，改为已定 |
| 第 12 项 | 「两套并存 +1–2」**转为延后项**（只用一套，客户正式部署若需另一套再说）。⚠ **这是 Claude 的推导、非用户裁决**——用户只答了"选哪份准则"，**未就"是否现在就要两套报表并存"表过态**（收尾 §6 核出，此处补标）。推导依据：既定一套准则，做第二套报表在演示前无收益。**客户正式部署时须回头问定。** |
| 第 5 节 | 待裁决①的**前半**（选哪份准则）与待裁决②（是否真装 HRMS）**由用户销项**；①的**后半**（是否现在就要两套报表并存）**由 Claude 推导为延后，未经用户裁决**。删掉第 22 项重复计数那句 |

**一条方法教训（LG-082）**：**「节点更多的表」不等于「超集」。** 353 对 266 的直觉是"大的包含小的"，实测**小的那份有 47 条大的没有**（这一侧 > 0 即否定超集；大的独有多少与判定无关）、编号体系还完全不同，且**大的那份恰好缺了我们最需要的那一层**。凡判包含关系，须按键实测两个方向的差集，不能以规模推断 —— 与 LG-067「名字像就推定是那个东西」同源，都是拿间接特征替代直接比对。

---

## 决策汇总表

承接 R1（DEC-023…DEC-037），本 Round 自 DEC-038 起。

| 编号 | 决策内容 | 最终选择 | 选择理由 | 提出者 | 失效条件 |
|---|---|---|---|---|---|
| DEC-038 | 三个新增需求（CRM 销售漏斗 / AI 智能体 / 外部操控）是否进演示 | **全部进**，且 CRM 漏斗取甲案（完整漏斗，Lead→Deal→Quotation→Sales Order） | 演示要在客户面前跑通整个流程，漏斗是数据链起点；AI 是差异化卖点 | 用户 | 实地考察后发现客户不用 CRM 流程 |
| DEC-039 | AI 智能体的演示载体 | **Raven**（内置 LLM 对话 + `Raven AI Function` 工具调用），经 **LiteLLM** 接入 | Raven 自带 ERPNext 文档读写工具链，`use_responses=False` 即可走标准 chat/completions；LiteLLM 统一多家模型 | 用户 | Raven 的 Local LLM 配置在 v16 失效 |
| DEC-040 | Raven 与 Flow 两套 AI 方案取哪套 | **两套都接入、按需使用**；Flow 归阶段 C | 两者定位不同（对话式 vs 编排式），不互斥 | 用户 | — |
| DEC-041 | 外部操控的形态 | **AI 界面自己完成操作**（不是"AI 告诉人怎么点"） | 演示要的是"看着它自己跑"，讲解式没有说服力 | 用户 | — |
| DEC-042 | 外部操控走全自动还是半自动 | **半自动**——后端 `publish_realtime` + 前端 `app_include_js` 注入监听，约 40–60 行 | 已查清现成机制只到"事件抵达"为止，20 个订阅点无一在执行操作；全自动须自建执行层，半自动即够演示 | Claude 提出，用户裁决 | 上游补出原生操控 API |
| DEC-043 | 译名改造的档次 | **覆盖档全量 + 精确档只抽检**；精确档全量延后到演示后 | 覆盖档解除关键路径；精确档须逐词读码确认作用，5–8 人日拿不到演示增量 | Claude 提出，用户裁决 | 客户对术语准确度提出硬要求 |
| DEC-044 | **R2 新增两条硬次序**：③ 科目表 → 建演示公司 → 数据集；④ CRM 接入 → 数据集（叠加 R1 的 ①术语→译名→脚本、②服务端修正→建数据，**共四条**） | **确立为硬次序** | 数据集是阶段 A 汇流点，上游任一未定则建出来的数据要重建；公司一旦记账科目表不能换；漏斗是数据链起点，`Deal → Quotation → Sales Order` 不通则 100 条无法从漏斗起头生成 | 用户提出③④的排序要求，Claude 落为硬次序 | — |
| DEC-045 | 中国财税的范围 | **只做内账侧**：科目表 + 增值税模板 + 月末结转 + 三张报表 + 银行对账；**专票/金税移出**，开票接口转摸底问点 | 开票须企业资质与签约，演示阶段拿不到；诺诺沙箱的 `go` 是推断非实测 | 用户 | 客户提供已签约的开票通道 |
| DEC-046 | zelin `erpnext_china` 的接入方式 | **并入式**（抄源码进自有 app），**不走 `bench get-app` 整包装** | 三条实测理由：硬编码 `apps/erpnext_china/` 路径；`install.py` 会禁用不在它 45 个中文单位表里的所有 UOM 并改 System Settings；`doc_events` 接 Company 三钩子并置 `ignore_chart_of_accounts=True` | Claude | zelin 上游把这三处改成可配置 |
| DEC-047 | 会计准则选哪份 | **小企业会计准则(2024)** | 用户判据是"一般企业若为超集则选它"——实测不是超集（**按科目名 SME 独有 47 条即已否定**；按科目号交集仅 9 条、编号体系 4–7 位对 5–8 位）；且小企业在 `应交增值税` 下有 10 条三四级明细，一般企业只到二级且那五条零命中；叶子 `account_type` 覆盖 81% 对 67% | 用户给判据，Claude 实测后裁定 | 客户正式部署要求一般企业准则（届时须补建整套增值税明细并重配税模板） |
| DEC-048 | 是否真装 HRMS | **真装** | 省掉计件工资的发放侧（`Additional Salary` 是"外部算好金额"的现成注入口，`Salary Slip` 自会收进并留溯源链）；151 条未译是四个 App 里最轻 | 用户 | — |
| DEC-049 | AI 演示用哪套数据 | **用第 19 项那 100 条全链数据集**，不另建 | 跨时间跨产品且含可发现的异常点，正是 AI 分析要展示的素材；与第 20 项共享生成机制 | 用户 | — |
| DEC-050 | 工作量表的出表次序 | **先调查再出表**——六路全链路排查完、三个常驻文件按契约改写完，才出侵入度与工作量表 | 未排查就出表会把虚高的缺口写进人日，且已五次应验 grep 未命中即推定缺口偏严 | Claude 提出，用户同意 | — |
| DEC-051 | 工作量的计量口径 | **单人 AI 开发的人日**，不给日历日期 | AI 辅助下实际速度与传统估算差距大，给日期会误导；相对比例与依赖次序才是可用信息 | 用户 | — |

## 被否决方案汇总表

承接 R1（NV-012…NV-019），本 Round 自 NV-020 起。

| 编号 | 方案 | 否决理由 |
|---|---|---|
| NV-020 | 接入 frePPLe 做产能计划 | 判 **no-go**：仓库里**没有 ERPNext connector 代码**（只有 odoo/erp 通用侧）；Community 版求解器尊重换型时间但**不优化它**，换型优化要 Enterprise。第 26 步实测 |
| NV-021 | 自写有限产能求解器 | 档 3（优化排产）**不自写**。难点不在代码量，在"约束模型对不对"与"怎么验证结果好"——**AI 杠杆最小处**。若做应用 OR-Tools CP-SAT |
| NV-022 | Helpdesk / Insights 进客户演示 | 与弹簧生产链无关，且各自带风险：Helpdesk `required_apps=["telephony"]` 且 `after_migrate` 会 `download_corpus()` 联网下 NLTK 语料；Insights 的 duckdb/ibis 在 Windows Docker 可安装性完全未验证 |
| NV-023 | Flow 进本次范围 | 零 release 零 tag、hook 里写 `"*"`（对所有 DocType 挂事件）、要改 Docker 镜像；且无 `locale/` 也无 `translations/`，纯 Vue 前端不走 frappe 翻译机制。归阶段 C |
| NV-024 | 照抄 ERPNext 官方自带的中国科目表 | **手段不成立**：`unverified/` 下那份 82 节点**全直挂 `tree`**（即全是根），根层 `root_type` 为空会触发 `validate_mandatory` 的 `throw`。⚠ 第 29 步"`root_type` 82 处全空故不可用"的**推论过程是错的**（`root_type` 只在根层读取后向下继承，`chart_of_accounts.py:20-22`，非根为空是标准约定）——结论对、理由错，见第 30 步① |
| NV-025 | `bench get-app` 整包安装 zelin `erpnext_china` | 三条实测副作用不可控，改取并入式。见 DEC-046 |
| NV-026 | 「装了 HRMS 就不用自己写计件工资」 | **不成立**。`hrms/payroll/utils.py:45-59` 的 `COMPONENT_EVAL_GLOBALS` 正好 13 项，`_safe_eval` 只喂这些加一个 `data`，**薪资公式里读不到 Job Card 任何东西**。计算侧装不装都得写，HRMS 省的只是发放侧 |
| NV-027 | 为两套会计准则都做出正确报表（本轮做） | **延后**。zelin 两个报表 Settings 都是 `issingle: 1` 单例、无 `company` 也无准则维度，消费侧全走 `frappe.get_single()`，配置行又直接引用科目名 ⇒ 版式全局一份且绑死一套编号。改为按准则分组须 +1–2 人日；准则已定只用一套，故不做 |
| NV-028 | 全量精确档译名进演示前 | 5–8 人日拿不到演示增量（覆盖档已无缺口）。只留 20–40 词抽检保险，理由同 LG-063：漂亮但错误比没有更糟 |
| NV-029 | 用 `setup_time` Custom Field + 改 `calculate_time()` 表达换型 | 均非必需——Routing **拆两行**（一行 `fixed_time=1`，一行 `fixed_time=0`）用同一 `sequence_id` 即可原生表达。真需求是**换型矩阵**（工序对工序），不是单值 `setup_time` |

## 遗留问题

承接 R1（LG-071…LG-081），本 Round 自 LG-082 起。**R1 的待验表 V-01…V-09 仍然有效**，不在此重复。

| 编号 | 事项 | 状态 | 触发条件 |
|---|---|---|---|
| LG-082 | **「节点更多的表」不等于「超集」** —— 判包含关系须按键实测两个方向的差集，不能以规模推断。与 LG-067 同源 | 已立为长效（**进 `docs/开发守则.md`「判据必须能区分…」节第四条反例**） | 常驻，不必唤醒 |
| LG-083 | **第 24 步「100 条口径待回答」的格子在第 25 步已被回答，却漏记了八步** —— 用户答的是「**从销售漏斗到生产到交付货物全流程**」，即全链档；同条消息还给了三项细化（多个 BOM、数十个供应商客户、最好有历史成交单价）与三类 AI 分析用途。**收尾 §6 记录验证时才发现，已补记为第 25 步⑩** | **口径已定**（全链）。遗留的是**漏记本身**——同一条用户消息里的多个编号项，只处理了其中一项就进下一步 | 常驻警戒项：**每轮收尾前对照用户消息的编号项逐条点数**。§7 落档开关只管步号 +1，管不了"一步里漏落几条" |
| LG-084 | `get_region()` 对中国的返回字符串未核 | 待实测 | 第 23 项 `regional_overrides` 启动自检开工前。**本轮最要紧的未查实项**——`regional_overrides` 的覆盖判断全建在这个字符串上 |
| LG-085 | `Quotation → Sales Order` 是否需人工介入未查实 | 待实测 | 第 15 项 CRM 接入时顺带验 |
| LG-086 | `Supplier Scorecard` 的默认评分标准是否随安装自带 fixtures 未查 | 待实测 | 采购侧开工前。S1 已应验 v16 把一批初始化搬进配置向导，**不宜按"自带"推定** |
| LG-087 | `valuation_method` 下拉有无 "Standard Cost" | 待实测 | 第 40 项标准成本开工前。`bin.py:56-62` 有该分支并 import `item_standard_cost`，而该模块全 bench 零文件 |
| LG-088 | `scheduled_time_logs[-1]` 末行约定须实跑验 | 待实测 | 第 30 项换型矩阵开工前。**该尽早实跑**——排产重排整批建在这个约定上 |
| LG-089 | LG-061：改 `standard=1` 记录会不会被 `bench migrate` 覆盖 | 待实测 | 第 22 项导航重整开工前。决定它走 L0 还是 L1 |
| LG-090 | Raven `Get List` 能否支撑跨表比价 | 待实测 | 第 16 项 Raven 接入时。`handle_get_list` 末端是 `frappe.get_all`，**无聚合、无 group by、无 join**，"哪个供应商货美价廉"可能须走 `Custom Function` 自写查询 |
| LG-091 | `handle_get_list` 绕过权限 —— `frappe.get_all` 强制 `ignore_permissions=True`（`frappe/__init__.py:1383-1404`） | **待处置**（非待查，已确认） | 演示无妨，**上生产前必须处置** |
| LG-092 | `print_designer` 的 v16 兼容性存疑 | 待确认 | 打印格式开工时。有强反证——`utils/pdf_generator/browser.py:13` 已读 v16 才有的字段 |
| LG-093 | CRM 内有 `frappe-ui` 目录，React 复用可能有 Vue 耦合 —— 本轮未展开查 | 待调研 | 远期 React 重写 UI 时（PH-P1003 之后） |
| LG-094 | 多级 BOM 连续穿透深度未实测 | 待实测 | 第 19 项数据集建多层 BOM 时 |
| LG-095 | frePPLe 同步粒度是否覆盖 Workstation / Routing / Operation 未查 | 待调研 | 已判 no-go（NV-020），仅在重议 frePPLe 时唤醒 |
| LG-096 | OR-Tools 在 v16 环境的现状未验证 | 待调研 | 第 43 项优化排产立项时（实地考察后） |
| LG-097 | MPS 提交按钮不显示未做浏览器目视确认 | 待实测 | 已实跑确认 `make_mrp` 全仓零定义故必然失败，仅补一次目视 |
| LG-098 | `Reference/saoxia-erpnext_china` 本轮未读 —— zelin 缺的两块（月末结转、银行对账）它可能有 | 待调研 | 第 11、14 项开工前值得先翻一眼。⚠ 但 NV-016 已记该仓三条硬事实（含 33727 个真实手机号），**只可读不可并入** |

## 状态值

| 字段 | 内容 |
|---|---|
| 状态值 | **`已收敛`** |
| 判定依据 | Spec「状态输出」的 `已收敛` 要求四条同时成立，逐条核：① **定位选定**——R1 DEC-024 已选「可信度优先」A 案；② **需求分级完成**——R1 分级经 R2 第 22 步按三个新增需求重排后定稿，落成 43 项的侵入度与工作量表（阶段 A/B/C 三段）；③ **关系梳理清楚**——需求关系收敛为四条硬次序（术语→译名→脚本；服务端修正→建数据；科目表→建公司→数据集；CRM→数据集），并识别第 19 项为阶段 A 汇流点；④ **用户确认无补充**——用户第 33 轮原话「**没问题了，可以收尾 A 步了**」。**第四条是 R1 判为 `未收敛` 的唯一欠项，本轮由用户明示补齐。** |

> **⚠ 与 R1 那次误判的区别**：R1 曾把四个条件写成三个、漏掉「用户确认无补充」而报 `已收敛`，收口后撤回。本次四条逐条对 Spec 原文核过，第四条有用户原话，不是推断。

## 复核建议

> 按流程规范 §2.2 与本步 Spec「复核建议」节写。按风险排序，给可操作的查法，并交代拿不准处。

### 一、定位选项是否真的对比过（Spec 点名的第一项，回退最贵处）

**本 Round 没有重开定位讨论，沿用 R1 的 DEC-024（可信度优先 A 案）。** 查法：读 R1 记录第 1–3 步，确认那里真给过 2–3 个不同方向的方案对比。**⚠ 但本轮用户确实碰过这个问题一次**——第 24 步用户说「我不知道 A、B 选项分别是什么，请再说明一次」，Claude 回读 R1 原文把两案摆了出来，**用户看后没有改选**，而是转去细化译名做法。这算不算"重新确认了定位"，判断留给下游：**说它已确认，依据是用户看过两案原文后未改选；说它未确认，依据是用户没对定位本身表过态。** 本记录取后者的保守读法。**R2 的风险不在"有没有对比"，而在"沿用是否还成立"**——R2 新增了三个需求（CRM 漏斗 / AI 智能体 / 外部操控），其中 AI 智能体把演示从"功能可信"推向"能力惊艳"，**这与"可信度优先"是两种气质**。

**具体该查的一处**：DEC-049 定了「AI 演示就用那 100 条数据集」。若 AI 在演示现场答错或答得含糊，按可信度优先的定位，代价比不演示 AI 更大——**而 LG-090（`Get List` 无聚合无 join）恰好指向"跨表比价这类最有说服力的问题可能答不了"**。建议 B 步落图谱时，把 AI 演示的问题清单限定在已验证能答的范围内，而不是留给现场即兴。

### 二、分级最可疑的需求

| 项 | 疑点 |
|---|---|
| **第 19 项 100 条全链数据集**（判为核心，4–6 人日） | 口径已由用户定为**全链**（第 25 步⑩），故 4–6 人日的档位对；三项数据细化（多 BOM、数十供应商客户、历史成交价）**也已在表里**。**可疑处在另一头**——用户同条消息给的**三类 AI 分析用途**（分析销售漏斗找单子 / 哪个供应商货美价廉 / 哪个 BOM 在符合单子要求下利润最大化）**没有任何一项被验证过 Raven 答得出来**。而 LG-090 恰好指出 `handle_get_list` 末端是 `frappe.get_all`、**无聚合无 group by 无 join** ⇒ 第二、三类正是典型的跨表聚合比较。**数据建得对，不等于 AI 问得出** |
| **第 16 项 Raven 接入**（3–5 人日，判为阶段 A） | 摇摆在"核心"与"重要"之间。它是差异化卖点故进 A，但 LG-090/LG-091 两条未验；若 `Get List` 撑不起比价，须加 `Custom Function` 自写查询，人日上浮而演示效果反而缩水。**建议 B 步把它标为"效果待验的核心"** |
| **第 14 项银行对账**（3–5 人日，判进阶段 A） | 进 A 的理由只是"不需资质故在范围内"，**没有演示必要性论证**。演示线上不经银行对账。可疑在"因为能做所以做" |
| **第 22 项导航重整**（2.5–3.5 人日） | 折叠四个 App 无关入口的成本含在这个区间里，但 HRMS 整套 HR 模块（考勤/请假/招聘/薪资）的折叠量未实际清点过，**是估的**。且走 L0 还是 L1 取决于 LG-089 未实测 |
| **第 11 项月末结转**（2–4 人日，L2） | zelin 没做、科目已备好，但"进项税额转出 + 未交增值税结转"的账务正确性**没有可对照的实现**，2–4 人日里不含"确认账务逻辑对不对"的时间。建议实地考察时问客户现行做法 |

### 三、范围分解的判定（Spec 点名：判为单目标须说明三条标准各自为何不成立）

判为**单目标**（S2 演示蓝图不拆）。三条标准逐条：

- **多个不相关的用户场景** → 不成立。全部 43 项服务同一个场景：**在客户面前跑通弹簧厂全链**。连阶段 B/C 的项也是同一目标的后续，不是另一个场景。
- **多个彼此无关联的数据模型** → 不成立。CRM（Deal→Quotation）、生产（BOM→WO→Job Card）、财务（科目表→税模板→报表）三块**共用同一条单据链**，且第 19 项数据集要求它们在同一批数据上贯通。
- **多个独立的目标用户群** → 不成立。目标用户只有一个：**客户方决策者**（演示的观众）。执行者（用户本人）是生产者不是目标用户群。

**⚠ 但有一处该记下**：阶段 C 那 10 项（54–94 人日）与演示目标的关联已经很弱——ECN/ECO、优化排产这类是"客户真实生产需求"而不是"演示需求"。**它们更像下一个 Phase 的目标，不是本 Stage 的。** 建议 E/F 两步分解 Stage 时，明确把阶段 C 划出本 Phase，而不是当成本 Phase 的尾巴。

### 四、拿不准处

1. **`已收敛` 的第②条「需求分级完成」是按工作量表判的，不是按需求图谱判的。** 本步产物是讨论记录 + 侵入度与工作量表，**需求图谱是 B 步的产物**。工作量表的 43 项已有分级（阶段 A/B/C），但那是**排期分级**，Spec 议题清单要的是**核心/重要/增强/实验性/暂缓**五档。两者不是同一套刻度——**B 步落图谱时须做一次映射，可能暴露分级空洞**。
2. **阶段 A 的 38–60 人日全是基于读码的估算，无一项实做过。** 误差最大的三项已在工作量表第五节点明（第 6 项译名 3037 条自译量、第 30 项换型矩阵、第 43 项优化排产）。
3. **七项须实机验证的（LG-084…LG-090）都没验，而其中三项卡在阶段 A 开工前。** 若 B 步之后直接进 C 步架构讨论而不先跑 SA spike，这三项会带着不确定性进架构。
4. **第 30 项「换型分钟数不能加在 `time_required` 上」这条约束来自读码**（`:950` 的 sum 会覆盖），**未实跑**。它决定换型矩阵的落点，判错会让第 30 项的 5–8 人日方向性返工。
5. **"zelin 在生产用所以能用"这个理由，本项目一次都没验证过。** 收尾 §6 核出它曾被用来消掉第 9 项的未跑项（V-03「点了能用」），已改回"机制已读通、仍未实跑"。**本项目对 zelin 只验了代码形态与许可证**，没有任何证据表明它被生产使用。连带地：第 12、13 项（两张报表 + 现金流量表）抄的是它的代码，**我们没跑过它们出的报表对不对**——只验了 DocType 结构完整、字段齐全。**"报表数字正确"零证据。**
6. **R2 的记录里有四处自我批评打折的同型问题**（R1 复核建议第四项列过）。本轮第 30 步①又出现一次同型：一边自我标记 LG-067、一边在同一步对同一文件做第二个未验证推论。**已在第 30 步末尾把"标记本身也要验"立为教训，但这条本身没有机制保障**——下一个 shape 步仍可能复发。
7. **§6 记录验证已跑，查出并修完 27 处。⚠ 但覆盖面是五段不是六段** —— 记录切成六段派出，**第 21–22 步那段（transcript L1–L560，六段里最大的一段）的核查未回报，已中止，本次没有对照原始对话核过**。按讨论契约 §6.3「transcript 不可得时须在产物里注明」的同一理由，此处明示：**第 21–22 步的落记忠实度本轮未验**。下述发现全部来自另五段。未核那段涵盖：用户提出三类新增需求（CRM / AI / 外部操控）与派五路调查、六路调查合并、需求分级重排提案、四项裁决点摆出。**DEC-038…042 五条决策的落记依据都在这一段里** —— 下游若要复核这五条，须自行回 transcript L1–L560 比对，不能引本次 §6 作为背书。

transcript 定位按 §6.3 用关键词交叉命中判定：R2 全部 12 步落在 `583932fe` 一个文件内（`4d0ee58a` 对 `R02-图谱讨论续`/`frePPLe` 零命中、末行时间 07:40:29 早于 R2 起点 07:57:15），**故此前"跨两个 transcript"的判断不成立**。

**按严重度排，须知道的五处**：

| # | 发现 | 类型 |
|---|---|---|
| 1 | **用户 L713 那条消息四个编号项只落了一项**——「100 条」口径答案（**全链**）与另两项漏记八步，工作量表第 19 项的 4–6 人日看似是单方面推定、实则有用户依据 | 漏记（高） |
| 2 | **用户 L668 第 3 条整条无痕**——「基本上全程都是查各种项目，但并没有真正好好讨论过要做什么」。这条批评正是后半程"先调查再出表"与 43 项工作量表的直接动因，却在记录里不存在 | 漏记（高） |
| 3 | **第 27 步"派出 8 路"实为 5 路**（六方向两两合并成 3 路），且该合并本身未满足用户「每个方向至少一路」的指令 | 计数错（中） |
| 4 | **两套报表并存的"延后"被并入"用户裁决全部落定"**——用户只裁了选哪份准则，未就这半表态 | 归属错（中） |
| 5 | **专票排除理由被硬化**：用户说"涉及对外、**可能**需要资质"，记录写成确定的"需资质"，与本项目自查的 V-05（沙箱不需资质）相抵 | 强度变（低–中） |

**第 27–29 步段另查出四处中等**：⑥ **"本轮共推翻六条既有判定"偏高**——其中一条纠正的是 Claude 本轮任务书之误（非既有判定）、一条经复验后是补充而非推翻，实为四条（三全推一部分推）；⑦ **"全部是范围缩小方向"把断言扩到了没依据的那条**——那条的方向恰好相反（间接费用只能单一基准分摊，是**缺口变大**）；⑧ **官方科目表"82 节点全部平铺"过头了**——回文件实测：`应交税费` 带 11 个子节点、其下 `应交增值税` 还有 10 条明细，全文 103 节点最大深度 3。**"须自建"的结论不变，但可复用的不止 82 个中文名——那段税金子树正好是第 32 步判定 NORM 缺的那一层**；⑨ **(b) 档判定丢了承重的 caveat**——「`override_whitelisted_methods` 实现代码未读」被调查方明确列为未查实，记录未落。

**第 30 步段另查出四处中等**：⑩ **一句局部算式加错**（8/9/10/12/13/14 项合计应为 8–12.5，原写 6.5–10.5，夸大了 zelin 带来的节省；**但 A-4 小计 11–18.5、净省 6–9.5、阶段 A 38–60 三处加总都对**）；⑪ **标题把"理由被推翻"写成"判定被推翻"**（正文区分得很干净，标题独立读会以为官方科目表可用了）；⑫ **用户已下的 HRMS 接入指令被降格回"待裁决"**（用户第④条是无条件下令接入，那句"看调查结果再定"限定的是 zelin 的接入方式）；⑬ **"zelin 在生产用"被当成已验事实去消 V-03 的未跑项**——本项目只验了代码形态与许可证，没有任何生产使用的证据。

低度处：第 29 步表「阶段 A 合计 41–66」加总错（应 41.5–67）、"用户六条裁决"含一条其实是提问、排程调查方"建议重点考虑 (c)"的立场被 Claude 的保留整段取代（两边意见相左这件事没留下）、一项未回滚的环境副作用漏记（Agent 启动了 Docker Desktop）、★ 复验标记覆盖到未复验项、一处推断写成断定句、一处直引替用户改错别字、NORM「进项税额」漏列 `待认证进项税额`、"无一条增值税明细"与本表自相矛盾、现金流量表"4 个子表"实为 2 个、HRMS 2321/2252 两个口径混用未注明、"双向都有独有 ⇒ 否定超集"论证落点不准（数据无误）、LG-072 撞 R1 已用编号、第 30 步改了阶段 B 却只写"阶段 A 修订"。

**⚠ 契约指向一个独立 Round，这里没跑**：讨论契约 §6 第二段写明——若某段讨论的记录可信度本身已成问题（**出现过漏记、错报范围、编造事实、产物反复纠错**），收尾自查的体量不够，**应改由一个独立 Round 专门查清并修复**（`freeform/Fid001` 形态）。**本轮 27 处里漏记、错报范围、计数错三类都有，且 R1 已跑过一次 Fid 核查修了 11 条——连续第二轮命中该判据。** 而本次仍是在收尾里自查，还漏掉了六段里最大的一段。**是否起 Fid Round 须用户裁决**；若起，第一件事就是补核第 21–22 步那段。

**状态值不受影响**：`已收敛` 的四个条件（定位选定 / 需求分级完成 / 关系梳理清楚 / 用户确认无补充）不含 §6，故状态值判定仍成立。**但收口的完整性有这个缺口，不应被 `已收敛` 盖过去。**

**⚠ 该批发现暴露的机制空洞**：§7 落档开关只机械核验"步号恰好 +1"，管得住"漏掉整步"，**管不住"一步里漏落几条"**——第 1、2 条正是这个形态。**本轮查出来靠的是 §6 派 Agent 比对原文；若跳过 §6，这些会带进 B 步的需求图谱。** 建议每轮收尾前**对照用户消息的编号项逐条点数**，这是比重读记录更廉的一道检查。

---

**⚠ 本卷已达分卷阈值**：本记录 12 步、1700 行以上，已过讨论契约 §2 纪律 10 的阈值。**A 步已在本卷收口（议题边界），故分卷点天然成立。** 若 B 步之后还要回 A 步补议题，**必须开 R3 新卷**，不得再追加到本卷。
