# P1-S2-R2-A 调研：工业生产相关的 Frappe 生态 App 普查

调研日期：2026-09-23
调研范围：除 CRM / Raven / Flow（另有 Agent 负责）之外，Frappe 生态中与工业生产相关、较流行的 App
本项目基线：ERPNext 16.35.0 + Frappe 16.34.0，当前 `apps/` 仅 frappe + erpnext 两个 app（已核实）

---

## 一、调查方法与覆盖面

### 用了哪些来源

1. **GitHub API 全量拉取 `frappe` 组织仓库**——分 4 页取全，共约 230 个仓库，带 stars / 最后推送日 / 许可证 / archived 标记 / 描述。这是唯一能保证"官方 app 没漏"的办法，靠记忆列举必然漏。
2. **`git ls-remote --heads --tags`** 探测分支与 tag。中途 GitHub API 触发匿名限流（60 次/小时），`ls-remote` 不受限流约束，成为主要的 v16 兼容判据来源。
3. **`raw.githubusercontent.com` 直取 `pyproject.toml` / `hooks.py` / `install.py` / DocType JSON**，核实能力声明。未克隆大仓库。
4. **`awesome-frappe`**（gavindsouza 维护，自称 225+ app 的社区索引）全文下载后按工业关键词检索，取得第三方 app 候选名单。
5. **Web 搜索**：中国本地化、MES/车间、SPC/CPK、模具工装、排产优化、条码、设备保养等方向。
6. **`git clone --depth 1`** 仅对一个仓库执行（`erpnext_china`），因为它是唯一直接命中缺口 1 和缺口 2 的候选，必须看实际内容而非 README 自述。
7. **本地 `frappe-bench/apps/` 源码核查**——判断"缺口是否真的存在"必须看装在本机上的 v16 代码，不能看文档站。

### 筛选口径

从约 230 个官方仓库里排除：文档站（`frappe_io`、`insights_docs`、`books_docs`）、CI / 测试 / SDK 工具（`semgrep-rules`、`frappe-js-sdk`、`frappe-react-sdk`、`frappe-types`、`caffeine`、`erpc`）、Frappe Cloud 自身基础设施（`press`、`agent`、`atlas`、`central`、`cargo`、`datum`、`suite_cloud`、`pilot`）、明确 archived 或 deprecated 的历史仓库（`schools`、`erpnext_shopify`、`paypal_integration`、`chat`、`frappejs` 等）、与制造业无关的垂直行业（`healthcare`、`education`、`lending`、`non_profit`、`hospitality`、`agriculture`、`lms`）——后者仍在主表中列出并表态，因为任务要求"存在则查、不存在则说不存在"。

### 覆盖面的诚实边界

- 本次**未在任何环境安装或运行**任何 app。所有兼容性判断基于分支/tag 存在性、`pyproject.toml` 的 `frappe-dependencies` 声明、以及源码检索，**不等于实测可用**。
- Frappe Cloud Marketplace 的付费 app 只能看到商品页文案，**无法核实源码**。凡出自商品页的能力描述，本报告一律标注为"厂商自述，未核实"。
- Gitee 上的中国本地化生态存在大量互相 fork 的碎片（`yuzelin` / `shuigu` / `hwl318` / `saoxia` 等多个同名仓库），本次只深查了 GitHub 镜像 `zelin-tech/erpnext_china`，**未逐一比对各 fork 的差异**。

---

## 二、主表

**v16 兼容列的判据说明**：`分支` = 存在 `version-16` 分支或 tag；`声明` = `pyproject.toml` 中 `frappe-dependencies` 上限覆盖 16；`滚动` = 仅单一 `main`/`develop` 分支、随 frappe 滚动更新、无版本分支可依；`未知` = 无任何可依据的信号。

### 官方 app（frappe 组织）

| App | 仓库 | 许可证 | 活跃度（最后推送 / stars） | v16 兼容 | 它做什么 | 对应缺口/环节 | 建议引入 | 理由 |
|---|---|---|---|---|---|---|---|---|
| **hrms** | frappe/hrms | GPL-3.0 | 2026-09-23 / 8819 | **是**（`version-16` 分支 + `v16.20.0` release，2026-09-23） | HR 与薪资：考勤、休假、报销、薪资结构、个税、离职金 | 缺口 7 计件工资——**但不直接支撑**，见 §3 | **可选，演示不需要** | 已核实 `hrms/payroll/doctype/` 全部 44 个 DocType 中**无任何 piecework / piece rate 相关表**；本地 erpnext 源码全库 grep `piece.?work|piece.?rate` 亦**零命中**。计件仍需自建 |
| **insights** | frappe/insights | AGPL-3.0 | 2026-09-23 / 1018 | **声明**（`frappe = ">=15.0.0"`，无上限） | BI：多数据源接入、可视化查询构建器、图表与仪表盘；底层 Ibis + eCharts，支持 MySQL/PostgreSQL/DuckDB/BigQuery | 演示说服力；缺口 1 的中国财报格式——**不能补** | **不建议进本轮演示** | 财报格式不是"画图问题"而是"科目映射 + 法定版式"问题，Insights 不含任何中国报表模板。演示加分可由 ERPNext 原生 Dashboard/Number Card 承担 |
| **print_designer** | frappe/print_designer | AGPL-3.0 | 2026-09-19 / 452 | **风险**：README 明写"only compatible with develop and V15" | 可视化拖拽设计打印版式 | 缺口 10 打印模板 | **可选，但先验证** | README 的 V15 表述与 v16 核心的集成状况矛盾——见 §5「拿不准的」。另需注意它在 `pyproject.toml` 的 `[deploy.dependencies.apt]` 声明了 16 个 Chromium 系统库，会显著加重 Docker 构建 |
| **drive** | frappe/drive | AGPL-3.0 | 2026-09-16 / 737 | **滚动**（仅 main/develop，最新 release v0.3.0 / 2025-10-08，已近一年无 release） | 文件存储、共享、协作 | 缺口 4 图纸版本管理 | **不建议** | **已核实它不做二进制文件版本管理**：`Drive Document Version` 的字段仅 `entity / snapshot(Long Text) / title / snapshot_size`，快照的是 Drive 自带富文本编辑器的文本内容；`Drive File Update` 是 `istable:1` 的活动日志子表，`type` 仅 `rename/upload/delete/move/edit`。装它补不上图纸版本（这正是"名字像就推定"会踩的坑） |
| **helpdesk** | frappe/helpdesk | AGPL-3.0 | 2026-09-22 / 3389 | **声明**（`frappe = ">=15.116.1,<17.0.0"`，明确覆盖 16） | 工单制客服系统 | 售后（不在 23 环节内） | **不建议进演示** | v16 兼容是这批里声明最干净的之一，但 23 环节最小闭环止于收款，售后不在其中。演示铺这一段会拉长动线、稀释主线 |
| **webshop** | frappe/webshop | GPL-3.0 | 2026-09-15 / 205 | **分支**（有 `version-16`，无 release） | 电商前台 | 无 | 不建议 | 弹簧厂是 B2B 订单制，无网店场景 |
| **ecommerce_integrations** | frappe/ecommerce_integrations | GPL-3.0 | 2026-09-22 / 209 | **是**（`version-16` 分支 + `v16.0.0` release 2026-02-18） | Shopify / Amazon / Unicommerce 对接 | 无 | 不建议 | 同上 |
| **payments** | frappe/payments | MIT | 2026-09-19 / 178 | **分支**（`version-16` / `version-16-hotfix`，无 release） | 支付网关（Razorpay/Stripe/PayPal 等） | 收款环节——**但网关不含中国** | 不建议 | 内置网关无微信支付/支付宝/银企直连；中国 B2B 收款走银行转账 + 手工核销，原生 Payment Entry 已够演示 |
| **lms** | frappe/lms | AGPL-3.0 | 2026-09-22 / 3249 | **是**（`version-16` / `version-16-hotfix` 分支 + `assets-version-16` release 2026-09-16） | 在线课程学习平台 | 无（勉强沾"员工培训"） | 不建议 | 与 23 环节无关 |
| **gameplan** | frappe/gameplan | AGPL-3.0 | 2026-09-22 / 517 | **滚动**（仅 main/develop，**无任何 release**；存在 `agent/frappe-v16-compat` 分支，暗示 v16 适配尚在进行） | 团队讨论区（异步长贴） | 无 | 不建议 | 与生产无关；且 v16 兼容分支名本身就说明还没并入主线 |
| **wiki** | frappe/wiki | MIT | 2026-09-23 / 433 | **滚动**（main/develop + `v3.2.1` release 2026-09-17；有 `fix/search-reindex-v16` 分支说明在跟 v16） | 站内知识库 / 文档空间 | 可承载作业指导书（不在缺口清单内） | 可选，非演示 | 活跃度好、许可证宽松（MIT），但属"锦上添花"，演示不需要 |
| **builder** | frappe/builder | MIT | 2026-09-23 / 2382 | **声明**（`frappe = ">=15.0.0,<18.0.0"`，明确覆盖 16） | 可视化建站 | 缺口 3 导航重排——**不能补** | 不建议 | Builder 做的是对外网站页面，不是 Desk 内的工作区导航。缺口 3 要改的是 Workspace，原生 Workspace 编辑即可 |
| **insights / studio / sheets** | frappe/studio, frappe/sheets | MIT / AGPL-3.0 | studio 2026-09-23 / 283；sheets 2026-07-23 / 37 | **滚动**（各仅单一分支） | studio：可视化搭内部应用；sheets：在线表格 | 无直接对应 | 不建议 | 均处早期形态（sheets 仅 37 stars），引入等于给演示环境加不确定性 |
| **assets** | frappe/assets | GPL-3.0 | **2022-03-28** / 21 | **否**（仅 `main` 单分支，四年半无推送） | 资产管理 | 缺口 6 模具工装（联想） | **不建议** | 已停维护。且 ERPNext v16 核心的 `erpnext/assets/` 已有 26 个 DocType（含 `asset_maintenance` / `asset_maintenance_task` / `asset_maintenance_log` / `asset_repair`），此独立 app 是历史遗留 |
| **agriculture** | frappe/agriculture | GPL-3.0 | 2025-05-26 / 106 | **否**（仅 `develop`） | 农业垂直域 | 无 | 不建议 | 行业不符 |
| **hospitality** | frappe/hospitality | GPL-3.0 | 2023-02-16 / 72 | **否**（仅 `develop`，三年无推送） | 酒店餐饮 | 无 | 不建议 | 行业不符且已停维护 |
| **non_profit** | frappe/non_profit | GPL-3.0 | 2024-07-12 / 64（**archived**） | 否 | 非营利组织 | 无 | 不建议 | 仓库已归档 |
| **education** | frappe/education | NOASSERTION | 2026-09-22 / 645 | **是**（`version-16` 分支 + `v16.1.0` tag） | 学校管理 | 无 | 不建议 | 行业不符 |
| **lending** | frappe/lending | GPL-3.0 | 2026-09-23 / 348 | **是**（`version-16` 分支 + 到 `v16.5.2` tag） | 放贷业务 | 无 | 不建议 | 行业不符 |
| **healthcare** | frappe/healthcare → **已迁出**，现为 `earthians/marley` | GPL-3.0 | 2026-09-22 / 537 | **是**（`version-16` / `version-16-hotfix` 分支） | 医疗管理 | 无 | 不建议 | 行业不符。附带确认：`frappe/healthcare` 对 API 返回 301 Moved Permanently，已不属官方组织，任何按老名字引用它的文档需更新 |
| **erpnext-shipping** | frappe/erpnext-shipping | NOASSERTION | 2026-08-21 / 147 | **是**（`version-16` 分支 + `v16.0.2` tag） | 对接国际快递（LetMeShip/Sendcloud 等） | 发货环节 | 不建议 | 承运商均为欧美服务商，无中国快递/货运；弹簧是工业件走货运专线 |
| **erpnext_price_estimation** | frappe/erpnext_price_estimation | MIT | 2026-07-03 / 57 | 未知（未深查） | 报价估算 | 接单环节（报价） | 拿不准，见 §5 | 名字贴合"弹簧按线径/材质/热处理估价"的场景，但**本次未核实其实际模型**，不做推荐 |
| **frappe/mail, meet, blog, newsletter, letters, draw, toolbox, whatsapp, telephony, exotel/twilio/waba_integration, offsite_backups, eps, mcp, llm, pulse, suite** | — | 多为 AGPL/MIT | 多数活跃 | 不一 | 邮件服务、视频会议、博客、通讯、白板、计算器、通讯集成、备份、积分、MCP、AI 等 | 无 | 不建议 | 与工业生产环节无关，逐一列出以说明"已覆盖、非遗漏" |

### 第三方 app

| App | 仓库 | 许可证 | 活跃度 | v16 兼容 | 它做什么 | 对应缺口/环节 | 建议引入 | 理由 |
|---|---|---|---|---|---|---|---|---|
| **erpnext_china** | zelin-tech/erpnext_china（GitHub 镜像）；主战场 gitee.com/yuzelin/erpnext_china | **MIT** | 2026-08-08 / 1 star（GitHub 镜像） | **强信号**：唯一提交信息就是 `update translation for v16`；`install.py` 内含 `set_v16_icon()` 函数 | **已 clone 核实**：19350 行 `translations/zh.csv` 补译；中国会计科目表（`default_accounts.csv`）；建公司时自动建税种与 13%/1%/0% 税率模板（`tax_rule.csv`）；**自建 6 组 DocType** 做中国三大报表——`balance_sheet_settings`、`profit_and_loss_statement_settings`、`cash_flow` / `cash_flow_code` / `cash_flow_item` / `cash_flow_subtotal`，配 3 个 report（`fin_balance_sheet`、`fin_profit_and_loss_statement`、`bs_and_pl_missing_account` 科目遗漏检查）；35 行 `field_property.csv` 改命名序列（SO-.YY.- 等）与撞名字段标签；fixtures 含 `custom_field.json` / `property_setter.json` | **缺口 1（部分）+ 缺口 2** | **建议引入——本次唯一强推荐** | 是生态里唯一实打实针对中国本地化的可获取 app，MIT 许可无传染性，且**直接命中本项目两条最痛的缺口**。它的三大报表是"配置式"（需自行维护报表项与科目号对照公式），不是开箱即用，但骨架和科目遗漏检查省下的工作量很实在。**注意**：它 `doc_events` 挂了 Company 的 `before_insert`/`on_update`/`after_insert`，且带 `property_setter` fixtures，与本项目自己的定制有覆盖冲突风险，须在干净站点上先验证 |
| **india-compliance** | resilient-tech/india-compliance | GPL-3.0 | 2026-09-23 / 270 | **是**（`version-16` / `version-16-hotfix` 分支 + 到 `v16.9.1` tag） | 印度 GST 合规：电子发票、E-Way Bill、GSTR 对账 | 缺口 1 的**参照架构**，非解决方案 | **不引入，但建议精读** | 它是"国家级税务合规 app 该怎么写"在 Frappe 生态里维护得最好的样板（v16 已到 16.9.1）。做中国金税/数电票对接时，照它的分层（独立 DocType 记票据状态 + Sales Invoice hook + 网关 provider 抽象）能省很多设计弯路 |
| **alyf-de/banking** | alyf-de/banking | GPL-3.0 | 2026-09-21 / 109 | **是**（`version-16` / `version-16-hotfix` 分支 + 到 `v16.5.0` tag） | 银行流水导入与对账（EBICS 协议） | 缺口 1 的银行对账 | **不引入** | EBICS 是欧洲银行标准，中国银行不用。同上，可作对账 UI 的设计参照 |
| **essdee/production_api** | essdee/production_api | GPL-3.0 | 2026-09-19 / 14 | 未知（未见 version 分支） | 制造流程 app（服装业出身） | 排产/报工（缺口 9 联想） | 不建议 | 活跃但 stars 极低、无 v16 分支、行业模型是服装（SKU 按颜色尺码爆炸），与弹簧的按图加工模型不符 |
| **ParaLogicTech/textile** | ParaLogicTech/textile | GPL-3.0 | 2026-09-09 / 41 | 未知 | 纺织行业 app | 无 | 不建议 | 行业不符 |
| **efeone/aumms** | efeone/aumms | NOASSERTION | 2026-09-22 / 34 | 未知（仅 main/develop） | 黄金饰品制造管理 | 无 | 不建议 | 行业不符；且许可证未声明（NOASSERTION），法务不确定 |
| **aerele/apparelo** | aerele/apparelo | GPL-3.0 | **2024-04-22，已 archived** | 否 | 服装制造工作流 | 无 | 不建议 | 仓库已归档 |
| **ERPNext-Frepple-Integration** | msf4-0/ERPNext-Frepple-Integration | GPL-3.0 | **2022-02-21** / 30 | 否 | 对接 frePPLe 开源排产引擎 | **缺口 9 排产优化** | **不建议引入，但值得记一笔** | 四年半无推送，v14 之前的东西，直接装必坏。但它证明"ERPNext 外挂专业排产引擎"这条路有人走过；缺口 9 若将来要做有限产能排产，frePPLe 是可考虑的外部引擎 |
| **crispy_print** | agatho-daemon/crispy_print | MIT | 2026-07-29 / 15 | 未知（仅 develop） | 基于 Typst 的打印引擎 + 可视化构建器 | 缺口 10 打印模板 | 不建议（本轮） | MIT + 活跃，Typst 排版对中国式表格版式理论上更可控，但仅 15 stars、单分支、无 v16 声明。押注风险高于 print_designer |
| **pasigono** | aisenyi/pasigono | 未查 | 2026 未查 / 低 | `version-14` 分支为最新版本分支 | POS 硬件：电子秤、Stripe 终端、QZ Tray 原始打印 | 收料/发货称重（联想） | 不建议 | 最新版本分支停在 v14 |
| **msf4-0/SWSI** | msf4-0/SWSI | 未查 | 低 | 仅 main | 无线智能电子秤 + Node-RED + ERPNext 库存 | 收料称重（弹簧常按重量收发） | 不建议 | 研究原型性质，非生产级 |
| **biometric-attendance-sync-tool** | frappe/biometric-attendance-sync-tool | GPL-3.0 | 2025-05-23 / 285 | N/A（是独立 Python 脚本，非 bench app） | 轮询考勤机并同步到 ERPNext | 报工/工时（间接） | 不建议 | 不是 app，不进 bench；且计件工资靠的是 Job Card 报工数量而非打卡 |
| **Siddardth7/quality-platform** | Siddardth7/quality-platform | **无许可证** | 2026-09-11 / 4 | N/A（**不是 Frappe app**） | SPC/FMEA/控制计划平台 | 缺口 5 SPC/CPK | **不引入** | **是 Streamlit 应用，不是 Frappe app**——名字容易误判。且无许可证文件，法律上不可复用。仅能当算法参考读 |
| **ECOSIRE 系列**（Shop Floor MES Terminal / SPC & Control Charts / Tooling, Mold & Fixture Lifecycle / Barcode & RFID / Andon / IIoT Connector / Preventive Maintenance CMMS / Advanced Production Scheduling） | 无公开仓库，ecosire.com 商品页 | **闭源、收费**（页面标 from $999 USD，按单定制） | 无法核实 | 页面自称 v15/v16 | 车间终端、SPC 控制图、模具寿命、条码 RFID、安灯、设备联网、预防性保养、有限产能排产 | 缺口 5 / 6 / 9 全覆盖 | **不建议引入** | **厂商自述，完全未核实**——无仓库、无源码、无法验证是否真实存在可交付物。定位是"按单开发"而非现成 app，等于外包而非装 app。列出仅为说明这些缺口在商业侧有人接单，可作自研时的功能清单参照 |

---

## 三、分组解读

### 建议引入（1 个）

只有 **erpnext_china** 一个。它是本次普查里唯一"缺口对得上、许可证干净、有 v16 动作"的三项齐备者：MIT 许可，2026-08-08 的提交信息就是 `update translation for v16`，代码里有 `set_v16_icon()` 这种专门适配 v16 的函数，19350 行补译直接冲着缺口 2 的 914 组撞名去，三大报表的 6 组 DocType + 科目遗漏检查报表直接冲着缺口 1 的中国财报格式去。

要分清两个理由：**为演示加分**——中文界面完整度和"打得开资产负债表/利润表/现金流量表"这件事，在弹簧厂老板面前的说服力是直接的，客户不会看 DocType，会看菜单是不是中文、报表是不是他认得的那三张。**长期必需**——中国科目表和撞名修正是这个项目无论如何都要做的事，自己从零补 19350 行译文不现实。

但引入前必须做两件事，否则就是把风险搬进演示环境：一是它 `doc_events` 挂了 Company 的三个钩子并带 `property_setter` / `custom_field` fixtures，和本项目后续自己的定制存在覆盖冲突的现实可能；二是三大报表是**配置式**的，报表项与科目号的对照公式要自己维护，不是装完就有数。建议在一个独立的干净站点先装一遍、建一个公司走一遍，再决定是否进演示环境。

### 可选（2 个，都不进本轮演示）

**hrms** —— v16 支持是这批里最扎实的（`version-16` 分支 + 当天的 `v16.20.0` release），但对本项目的核心诉求（缺口 7 计件工资）**帮不上**。这一点已核实到 DocType 粒度，详见下节。它的价值在将来做人员、考勤、薪资时，不在演示。

**print_designer** —— 缺口 10 唯一像样的官方候选，但它 README 明写只兼容 develop 和 V15，而本地 frappe 16.34.0 核心里已有大量 `is_print_designer` 判断逻辑。这个矛盾本次没查清（见 §5），所以只能"可选 + 先验证"。另外它在 `[deploy.dependencies.apt]` 声明了 16 个 Chromium 系统库（libgtk-3-0、libnss3、libasound2 等），按项目记忆里那条 Windows Docker 环境的教训，这会实打实加重构建时间和镜像体积。

**wiki** 勉强算第三个：MIT、活跃、能承载作业指导书，但不在 11 条缺口内，演示不需要。

### 不建议引入

**drive 是本次最需要点出来的一个。** 它看起来天造地设地对应缺口 4（图纸文件版本管理与变更通知），实际核实下来不是：`Drive Document Version` 的全部字段是 `entity / snapshot(Long Text) / title / snapshot_size`，快照对象是 Drive 自带富文本编辑器的文本内容；`Drive File Update` 是 `istable:1` 的活动日志子表，`type` 选项只有 `rename/upload/delete/move/edit`。**它不对上传的二进制文件做版本管理**——而弹簧图纸就是 DWG/PDF 这类二进制。README 里那句"Manually version your documents"说的是它的在线文档，不是你传上去的图纸。装它补不上缺口 4。这正是项目此前三次判错的同一个坑：查到一张名字像的表就推定它是那个东西。

**insights** 补不上中国财报格式——财报是科目映射加法定版式的问题，不是画图问题，Insights 里没有任何中国报表模板。演示的图表说服力用 ERPNext 原生 Dashboard / Number Card 就够，不值得为此多背一个 AGPL app。

**builder** 补不上缺口 3 —— 它做的是对外网站页面，不是 Desk 内的 Workspace 导航；缺口 3 改 Workspace 即可，原生就能改。

**helpdesk** v16 声明最干净（`frappe = ">=15.116.1,<17.0.0"`），但 23 环节最小闭环止于收款，售后不在其中。演示动线拉长会稀释主线，建议明确不进本轮。

**ECOSIRE 全系列**虽然功能清单正好覆盖缺口 5/6/9，但无仓库、无源码、无法核实，且是按单定制（from $999）而非现成 app。把它当"外包报价单"看，不当"可装的 app"看。

**行业不符的一批**（education、lending、healthcare→earthians/marley、agriculture、hospitality、webshop、ecommerce_integrations、textile、aumms）和**与生产无关的官方工具**（mail、meet、blog、newsletter、draw、toolbox 等）统一不建议，列出只为证明覆盖到了、不是漏查。

顺带一条需要更新的事实：`frappe/healthcare` 已迁出官方组织，现在是 `earthians/marley`，API 对老地址返回 301。

### 已停维护或不兼容 v16

- **assets**（frappe/assets）：最后推送 **2022-03-28**，仅 `main` 单分支。而且没必要——ERPNext v16 核心 `erpnext/assets/` 已有 26 个 DocType，含 `asset_maintenance` / `asset_maintenance_task` / `asset_maintenance_log` / `asset_maintenance_team` / `asset_repair`，设备点检保养的骨架原生就有。
- **apparelo**（aerele）：GitHub 已标 archived，2024-04-22 停更。
- **ERPNext-Frepple-Integration**：2022-02-21，v14 前时代。
- **hospitality**：2023-02-16，三年无推送。
- **non_profit**：archived。
- **pasigono**：最新版本分支停在 `version-14`。
- **agriculture**：2025-05-26，仅 `develop`，无版本分支。
- 官方组织内另有一大批明确 deprecated/archived 的历史仓库（`schools`、`erpnext_shopify`、`paypal_integration`、`chat`、`frappejs`、`bench_manager`、`event_streaming`、`storage_integration`、`erpnext_gst_compliance`、`india_payroll` 等），均不在候选之列。

---

## 四、已确认生态里没有现成方案的缺口

下列判断建立在"全量扫了官方 230 个仓库 + awesome-frappe 社区索引 + 多轮定向搜索，均未找到开源可获取、v16 兼容的方案"之上。这是**未找到**，不等于**绝对不存在**，但足以支撑"按自研规划"的决策。

| 缺口 | 结论 | 依据 |
|---|---|---|
| **1. 中国本地化** | **部分有、关键部分没有**。科目表 / 三大报表 / 税率模板：`erpnext_china` 提供骨架（配置式）。**增值税专用发票、金税盘/数电票对接、中国银行对账：生态内零开源方案**，只能自研 | 本地已核实 `erpnext/regional/` 仅 australia / italy / south_africa / turkey / united_arab_emirates / united_states，**无 china**。搜索仅找到他国方案（eu_einvoice / ZATCA / italian_invoice / FBR / eTIMS）。frappe.io 的中文落地页自称合规金税，但页面自标 [Draft] 且不指向任何仓库，交付靠本地伙伴 |
| **2. 中文译名缺失与撞名** | **有可用起点**：`erpnext_china` 的 19350 行 `zh.csv` + 35 行 `field_property.csv` 专门改撞名字段标签 | 已 clone 核实文件与行数 |
| **3. 导航按业务流重排** | **无需 app，自己配**。原生 Workspace 就能改，Builder 不是干这个的 | 生态内无"Desk 导航重排"类 app；Builder 定位是对外网站 |
| **4. 图纸版本管理与变更通知** | **无现成方案，须自研**。Drive 明确不做二进制文件版本 | 已核实 Drive 的 `Drive Document Version` 字段与 `Drive File Update` 的 `type` 选项（见主表） |
| **5. SPC / CPK** | **无 v16 兼容的开源 Frappe app，须自研**。原生 Quality Inspection 只记读数与合格判定，无控制限、无过程能力指数 | 本地核实 `erpnext/stock/doctype/` 有 quality_inspection 系列 6 个 DocType（含 `quality_inspection_reading` / `quality_inspection_parameter`），`erpnext/quality_management/` 17 个 DocType 是体系文件类（quality_procedure / quality_review / non_conformance / quality_goal），**无控制图、无 Cp/Cpk**。生态内唯一像样的 SPC 实现是 Streamlit 的 `quality-platform`（非 Frappe，且无许可证），其余是闭源收费 |
| **6. 模具工装管理** | **无现成 app，须自研；但底座是现成的**。核心需求（按模次/冲次累计寿命、到限预警、修模后计数重置）无开源实现 | ERPNext v16 原生 `assets` 模块有 asset / asset_maintenance / asset_maintenance_task / asset_maintenance_log / asset_repair / asset_movement，可作模具台账与保养的底座；"按模次计寿命"需自建计数字段 + Job Card 钩子 |
| **7. 计件工资** | **hrms 补不上，须自研；但数据源是现成的**。已核实 hrms payroll 的 44 个 DocType 中无任何 piecework/piece-rate 表，本地 erpnext 全库 grep `piece.?work|piece.?rate` 零命中 | **关键发现**：`Job Card Time Log`（`istable:1`）字段为 `from_time / to_time / time_in_mins / completed_qty / employee / operation`——**已带 `completed_qty` 和 `employee`**。计件工资的数据源天然存在，缺的是"工序单价 × 完工数量 → Additional Salary / Salary Component"这一段计算与过账。这是自研可行且工作量可控的一块 |
| **8. 质检 / 外协 / 月结** | 三块**原生都有骨架**，不需要 app，需要的是摸底把流程走通 | 质检：`quality_inspection` 系列 6 + `quality_management` 17 个 DocType；外协：v16 `erpnext/subcontracting/` 有 14 个 DocType，含 v16 新增的 `subcontracting_inward_order` 系列（来料加工）；月结：原生会计期间与结账凭证 |
| **9. 优先级字段与换型/调机时间** | **无现成 app，须自研**。已核实 v16 的 Work Order 与 Sales Order **均无 `priority` 字段** | 对 `work_order.json` / `sales_order.json` grep `"fieldname": "priority"` 均零命中；Work Order 只有 sales_order / subcontracting_inward_order 等关联字段。v16 虽新增 `master_production_schedule` / `sales_forecast` / `plant_floor` / `work_order_configuration`，但换型时间概念仍无。外挂 frePPLe 这条路有人走过（已停维护），自研有限产能排产是另一条 |
| **10. 打印模板** | **有候选但需验证**：print_designer（v16 兼容存疑）、crispy_print（小众）。中国式版式（增值税发票、送货单、质检报告）无任何现成模板，版式本身必须自己画 | print_designer README 自述仅兼容 V15；生态内无中国式单据模板库 |
| **11. React 重写前端** | **有成熟基建，不是缺口**：`frappe-ui`(1033★)、`frappe-react-sdk`(189★)、`frappe-js-sdk`(169★)、`frappe-types`(69★) 均活跃维护（2026-07 以后有推送） | 官方组织仓库列表核实。官方新 app（crm/helpdesk/insights/drive）走的都是 frappe-ui（Vue）路线，React SDK 是独立维护的一条 |

**一句话收口**：11 条缺口里，生态能帮上的只有缺口 1 的一部分和缺口 2（都靠 `erpnext_china`）；缺口 3、8 靠原生配置；缺口 11 有现成基建；**缺口 4、5、6、7、9、10 六条必须自研**，其中 6、7、9 有原生底座可借（assets / Job Card Time Log 的 completed_qty / Workspace），4、5、10 是从零。

---

## 五、拿不准的

1. **print_designer 到底能不能在 v16 上用？** 这是本次最该继续查而没查透的一条。矛盾的两组事实：一边是它 `main` 分支 README 明写 "only compatible with develop and V15 version of frappe framework"，最新 release `v1.6.7` 是 2026-02-10（半年多前）；另一边是本地 frappe 16.34.0 的 `frappe/utils/pdf_generator/browser.py` / `page.py` / `chrome_pdf_generator.py` 里已有大量 `is_print_designer` 判断，其中 `browser.py:13` 读的是 `frappe.get_cached_value("Print Format", print_format, "print_designer")`——但我在核心 `print_format.json` 里 grep `print_designer` **零命中**，说明该字段是 print_designer app 通过 `install.py` 的 `create_custom_fields(CUSTOM_FIELDS)` 加上去的 custom field。所以核心代码是"为这个 app 预留了集成点"，而 app 自己的 README 可能只是没更新。它 2026-09 仍有提交（09-18、09-17 都在修 print designer 页面 bug）。**结论悬空：需要在测试环境实装一次才能定。** 建议作为 R2 的一个具体验证动作，而不是靠读代码下结论。

2. **`erpnext_china` 的 v16 兼容到什么程度？** 有强信号（`update translation for v16` 提交、`set_v16_icon()` 函数），但 `pyproject.toml` 里 frappe/erpnext 依赖行是**注释掉的**（`#"frappe >= 15.0.0 <17.0.0"`），等于没有机器可读的版本约束；仓库仅 `master` 单分支，无 v16 分支或 tag。它的三大报表 DocType 是自建的、不依赖 erpnext 内部 API，兼容风险主要在 `doc_events` 挂的 Company 钩子和 `property_setter` fixtures 上。**必须实装验证，不能凭信号下结论。**

3. **Gitee 生态的碎片化没摸清。** 搜索显示 `erpnext_china` 至少有 `yuzelin`（主）、`shuigu`、`hwl318`、`saoxia`、gitcode 镜像等多个同名仓库，另有 `accounting_cn`、`CAS`、`ShudouCN`、`erpnext_oob`（开箱即用）、`zh_chinese_language`（声明支持到 v15）、`frappe_locale` 等相关项目。本次只深查了 GitHub 镜像一支，**没有比对各 fork 谁更新、谁的译文质量更好、谁和谁冲突**。README 里明确提到它与旧的"中文汉化""开箱即用"两个 app 冲突需先卸载——说明这个圈子里互斥关系是真实存在的。若决定走 `erpnext_china`，值得再花一轮把 Gitee 主仓库和主要 fork 的差异摸一遍。

4. **`erpnext_price_estimation`（frappe 官方，MIT，57★，2026-07-03）没查。** 名字贴合弹簧按线径/材质/圈数/热处理估价的场景，可能对接单环节的报价有用。本次未核实其实际模型，**不做任何推荐，但建议列入下一轮候选**。

5. **ECOSIRE 是否真有可交付物，无法判断。** 它的 SPC app 商品页给出的 DocType 命名（`SPC Characteristic` / `SPC Subgroup` / `SPC Control Chart` / `SPC Capability Study`）和 AIAG 常数、Western Electric / Nelson 判异规则等细节，专业度看着像真做过；但**没有任何仓库或源码可验证**，也可能只是销售页面上的功能设想。自研 SPC 时可拿它的功能清单当需求参照，但不应把它当"存在的产品"写进任何方案。

6. **`quality-platform` 的 SPC 算法核心能否复用，法律上不确定。** 它的 `quality_core/spc/` 据搜索结果含控制图、判异规则、Cp/Cpk/Pp/Ppk、EWMA、CUSUM 等且有测试，但**仓库无 LICENSE 文件**——无许可证即保留全部权利，不可复用。且它是 Streamlit 应用而非 Frappe app。若要参考，须先联系作者或改用其他有明确开源许可的实现。

7. **本次所有 v16 兼容判断都是静态判断。** 分支存在 ≠ 能装上、装上 ≠ 不冲突、不冲突 ≠ 功能正常。特别是多个 app 同装时的 DocType 命名冲突与 hook 覆盖，静态检查看不出来。任何进演示环境的 app（当前只有 `erpnext_china` 一个候选）都应在独立站点先走一遍最小闭环。
