# P1-S2-R2 调研报告：官方 Frappe CRM

**调查者**：Claude（主 Session 亲自查证）
**日期**：2026-09-23
**克隆位置**：`Reference/frappe-crm`（`--depth 1`，`.gitignore` 已排除）

> **⚠ 产出方式同 Raven 报告**：原派出的子 Agent 完成调查后两次在"写报告"这一步中断（第二次是网关 503：`分组 aws-q 下模型 claude-opus-5 无可用渠道`），报告始终未落盘。故由主 Session 依据本地克隆亲自重查并书写，**每条结论均为直接读码所得**，附可复现路径。
> **代价**：覆盖面窄于原计划，未展开的见 §7。

---

## 一、开源结论

| 项 | 值 | 依据 |
|---|---|---|
| **许可证** | **AGPL-3.0** | 打开真实 `LICENSE` 首二行实读：`GNU AFFERO GENERAL PUBLIC LICENSE / Version 3, 19 November 2007`。**无 Flow 那种文件头矛盾** |
| 作者 | `Frappe Technologies Pvt. Ltd.`（官方公司实体） | `pyproject.toml:3-5` |
| 定位 | "Kick-ass Open Source CRM" | `pyproject.toml:6` |
| 分支 | **只有 `develop`**（`git branch -a` 实读） | 与 Flow 同样无 v16 专用分支 |

**三个 AI/CRM 候选的许可证与支持信号对照**：

| | CRM | Raven | Flow |
|---|---|---|---|
| 许可证 | AGPL-3.0，无矛盾 | AGPL-3.0，无矛盾 | AGPL-3.0，**51 个 py 头写 MIT** |
| publisher | **官方公司实体** | 官方邮箱 | 个人名 |
| 分支 | 仅 `develop` | （未核） | 仅 `develop`，零 release 零 tag |

---

## 二、依赖与 v16 兼容

| 项 | 值 | 依据 |
|---|---|---|
| **frappe 版本要求** | **`>=16.0.0-dev,<=17.0.0-dev`** —— **覆盖我们的 16.34.0** ✅ | `pyproject.toml:32-33` |
| 是否依赖 ERPNext | **不强依赖** —— `required_apps` 被注释掉（`crm/hooks.py:14`）。**但有可选的 ERPNext 集成**，见 §5 | 读码 |
| Python | `>=3.10`，与本项目 3.14 兼容 ✅ | `pyproject.toml:7` |
| Python 依赖 | `twilio==8.5.0`、`requests>=2.28.0`、`tldextract>=5.0.0` | `pyproject.toml:10-21` |

**注**：`frappe~=15.0.0` 那行在 `dependencies` 里**是注释状态**，真正的版本约束在 `[tool.bench.frappe-dependencies]`，即 `>=16.0.0-dev`。**故它是明确面向 v16 的**，比 Flow 的信号强（Flow 的 CI 只对 `frappe:develop` 跑）。

---

## 三、DocType 撞名 —— **全部自带 `CRM ` 前缀，不与 ERPNext 冲突**

`crm/fcrm/doctype/` 下 39 个 DocType 实读，**命名一律 `crm_*`（DocType 名为 `CRM *`）**：

`crm_lead` / `crm_deal` / `crm_organization` / `crm_contacts` / `crm_task` / `crm_product` / `crm_products` / `crm_lead_status` / `crm_deal_status` / `crm_lead_source` / `crm_lost_reason` / `crm_territory` / `crm_industry` / `crm_call_log` / `crm_notification` / `crm_dashboard` / `crm_fields_layout` / `crm_form_script` / `crm_view_settings` / `crm_service_level_agreement` / `crm_service_level_priority` / `crm_status_change_log` / `crm_sales_hierarchy` / `crm_invitation` / `crm_holiday` / `crm_holiday_list` / `crm_service_day` / `crm_communication_status` / `crm_dropdown_item` / `crm_global_settings` / `crm_rolling_response_time` / `crm_telephony_agent` / `crm_telephony_phone` / `crm_twilio_settings` / `crm_exotel_settings` / `crm_product_sync_issue` / `fcrm_note` / `fcrm_settings` / **`erpnext_crm_settings`**

**关键判定**：

| ERPNext/Frappe 既有 | CRM 的做法 | 判定 |
|---|---|---|
| `Lead` | **另建 `CRM Lead`** | 不撞名，两套并存 |
| `Opportunity` | **另建 `CRM Deal`**（不叫 Opportunity） | 不撞名 |
| `Customer` | **不建**，靠集成同步（§5） | 不撞名 |
| `Contact`（Frappe 核心） | **不另建，而是 `override_doctype_class` 覆盖其类** | ⚠ **这是唯一的侵入点**，见 §6 |
| `Item` | **另建 `CRM Product`** + 双向同步 | 不撞名 |

**故 DocType 层面无命名冲突风险**，代价是**同一个客户在系统里有两份记录**（`CRM Deal` 与 `Customer`），靠集成同步而非共用一张表。

---

## 四、客户漏斗 —— 术语与形态

### 4.1 术语：用户说的"客户漏斗"不是标准叫法

| 说法 | 判定 |
|---|---|
| 「客户漏斗」 | **非标准术语**，行业不这么叫 |
| 「销售漏斗」/「销售管道（pipeline）」 | **行业通用说法** |
| CRM app 内部的实际对象名 | **`CRM Deal` + `CRM Deal Status`** —— 它自己既不叫 funnel 也不叫 pipeline，**漏斗是由 Deal 的状态序列隐含表达的** |

### 4.2 形态：状态序列 + 概率，七档

`crm/install.py:91-135` 实读，`add_default_deal_statuses()` 的七个默认状态：

| # | 状态 | type | **概率** | 颜色 |
|---|---|---|---|---|
| 1 | Qualification | Open | **10%** | gray |
| 2 | Demo/Making | Ongoing | **25%** | orange |
| 3 | Proposal/Quotation | Ongoing | **50%** | blue |
| 4 | Negotiation | Ongoing | **70%** | yellow |
| 5 | Ready to Close | Ongoing | **90%** | purple |
| 6 | Won | Won | **100%** | green |
| 7 | Lost | Lost | **0%** | red |

**`probability` 字段的存在是"漏斗"成立的关键** —— 它使加权预测（金额 × 概率）可算，这是漏斗图的数据基础。

另有 `CRM Lead Status` 五档（`install.py:40-90`）：New → Contacted → Nurture → Qualified → Converted。**即完整链路是 Lead 五档 → 转 Deal → Deal 七档**，比"接单"往前延伸了两级。

### 4.3 中文翻译 —— **有，但缺 39%**

`crm/locale/zh.po` 实测：

| 指标 | 值 |
|---|---|
| 文件行数 | 8928 |
| `msgid` 条数 | **1782** |
| **空 `msgstr`（未译）** | **689** |
| **未译比例** | **约 38.7%** |

**⚠ 这直接撞上本项目的最高优先级需求 `PH-P1001`（译名准确稳定）**。用户对译名的原话要求是「不应该出现有些翻译了有些没翻译的情况」——**而 CRM 自带翻译恰好就是这个形态：1782 条里 689 条空着**。装上 CRM 等于把一块新的"半翻译"界面引进演示。**这是本报告最重要的一条发现。**

---

## 五、与 ERPNext 的数据联动 —— **有，且比预想的完整**

**这一条推翻了预设判断**（原设问是"若无联动，则漏斗与 23 环节闭环是两套互不相通的数据"）。

存在专门的 **`ERPNext CRM Settings`** DocType，字段实读：

| 字段 | 类型 | 作用 |
|---|---|---|
| `enabled` | Check | 集成总开关 |
| `erpnext_site_url` | Data | ERPNext 站点地址 |
| `api_key` / `api_secret` | Data / Password | **跨站点认证**（说明它支持 CRM 与 ERPNext **装在不同站点**） |
| **`is_erpnext_in_different_site`** | Check | **同站 / 异站两种部署模式** |
| `erpnext_company` | Data | 对应 ERPNext 里哪个公司 |
| **`create_customer_on_status_change`** | Check | **Deal 状态变化时自动建 Customer** |
| `deal_status` | Link | 触发建 Customer 的是哪个状态 |
| **`sync_products`** | Check | **双向产品同步**（`CRM Product` ↔ ERPNext `Item`） |
| `sync_issues` | Table | 同步失败的问题清单 |

**联动的三条实际机制**（`erpnext_crm_settings.py` 实读）：

1. **改 ERPNext 的 Quotation 使其可指向 CRM Deal**（`:75-80`）——建一个 `Property Setter`，把 `Quotation.quotation_to` 的 link_filters 改为 `["Customer", "Lead", "Prospect", "CRM Deal"]`。**即报价单可以直接开给一个 CRM Deal。**
2. **在 ERPNext 侧加 custom field**（`:125-136`）——给 `Quotation` 与 `Customer` 各加字段（含 `Customer` 上的「Customer in ERPNext」类字段）。异站模式下经 API 远程建，失败会报 `Could not create custom fields on remote ERPNext site`（`:154`）。
3. **装一段前端脚本「Create Quotation from CRM Deal」**（`:181-200`）——以 `CRM Form Script` 形态落地，即 **Deal 页面上有个按钮能直接生成 ERPNext 报价单**。

**故结论**：**漏斗与 23 环节闭环是能打通的**，衔接点是 **Deal → Quotation（报价单）→ Sales Order（销售订单）**。这正好接在本项目 23 环节闭环的起点「接单」之前，形成 `Lead → Deal → 报价 → 接单 → …… → 收款` 的完整演示线。

**⚠ 但三点要注意**：

1. **衔接点是 Quotation，不是 Sales Order**。**未查实**从 Quotation 到 Sales Order 那一步是否需人工操作（ERPNext 原生有 Quotation → Sales Order 的 mapper，故推断可行，但**本次未验**）。
2. **`create_customer_on_status_change` 是可选开关**，默认状态未查。不开则 Deal 赢单后不自动建 Customer。
3. **产品同步是双向的**，意味着 `CRM Product` 与 ERPNext `Item` 会互相写。本项目 Item 上要挂弹簧的国标型号标记，**同步规则须先弄清再开这个开关**，否则可能被覆盖。

---

## 六、前端挂载链路 —— **可照抄用于 React 前端**

这是用户那个战略问题（「React 重写界面能否同样接入」）的直接答案素材。

**链路**（`crm/hooks.py:74-77` + `pyproject.toml:35-38` 实读）：

| 环 | 机制 | 依据 |
|---|---|---|
| 1. 路由声明 | `website_route_rules = [{"from_route": "/crm/<path:app_path>", "to_route": "crm"}]` —— **`<path:...>` 通配使 SPA 的 history mode 路由全部落到同一个后端 route，故前端深链接不 404** | `hooks.py:74-77` |
| 2. 落地页 | `to_route: "crm"` 指向 `crm/www/crm.html` | `pyproject.toml:38` `index_html_path = "../crm/www/crm.html"` |
| 3. 构建 | 前端源码在 `frontend/`，构建产物出到 `crm/public/frontend`，**index.html 写到 `www/crm.html`** | `pyproject.toml:35-38` `[tool.bench.assets]` 三个键：`build_dir` / `out_dir` / `index_html_path` |
| 4. 静态资源 | 经 `crm/public/` → `/assets/crm/...` | Frappe 标准约定（**未逐环验证**） |
| 5. 另有一条 | `/crm-form/<route>` → `crm_form`，供对外表单用 | `hooks.py:76` |

**关键判断：这条链路与前端框架无关。** `[tool.bench.assets]` 的三个键（`build_dir` / `out_dir` / `index_html_path`）只关心"源码在哪、产物出到哪、index.html 放哪"，**不关心用 Vue 还是 React**。`website_route_rules` 的 `<path:app_path>` 通配同理。

**故初步结论**：**React 前端能走完全一样的路** —— 做成一个 Frappe app、`frontend/` 里放 React 源码、配同样的三个 assets 键、声明 `website_route_rules`。**但这是读码推断，未实做验证**，且 frappe-ui 的 resource 层与 socketio client 封装是否有 Vue 专属依赖**本次未查**（该问题属接入机制那一路）。

**⚠ 注意 CRM 仓库里有个 `frappe-ui` 目录** —— 说明它把 frappe-ui 作为源码级依赖而非仅 npm 包。若 React 方案要复用 frappe-ui 的数据层，这里可能有 Vue 耦合。**未展开查。**

---

## 七、装上去的代价与风险

### 7.1 ⚠ `override_doctype_class` 覆盖了 `Contact` 与 `Email Template`

`crm/hooks.py:231-234` 实读：

```
override_doctype_class = {
    "Contact":       "crm.overrides.contact.CustomContact",
    "Email Template": "crm.overrides.email_template.CustomEmailTemplate",
}
```

**`Contact` 是 Frappe 核心 DocType，ERPNext 的客户/供应商联系人全用它。** 覆盖其类意味着 CRM 的代码会介入所有 Contact 的行为。**本次未读那两个 override 的实现**，故影响面未知——**这是本报告最该继续查的一条**。

### 7.2 `doc_events`

`hooks.py:240` 起实读，**挂的是具体 DocType 而非 `"*"`**（这点比 Flow 与 Raven 好）：

| DocType | 事件 |
|---|---|
| `Contact` | `validate` |
| `Notification Log` | `before_insert` |
| `ToDo` | `validate` / `after_insert` / `on_update` |

**故 CRM 不拦全库写操作**，风险显著低于 Flow 与 Raven（那两个都是 `"*"` × 5 个写事件）。

### 7.3 `after_install` 会写入大量数据

`crm/install.py:20-37` 实读，`after_install` 依次跑 **18 个** 初始化函数：默认 Lead/Deal 状态、通信状态、字段布局、`add_property_setter()`、Email Template 与 Email Account 的 custom field、Web Form custom field、默认行业/来源/丢单原因/快捷筛选、下拉项、默认脚本、经理仪表盘、**分派规则的 custom field 与 property setter**、默认规则与映射。

**⚠ 装在已有数据的站点上（1 公司 `华东弹簧` / 95 科目 / 已有销售订单）的风险点**：它会加 custom field 与 property setter 到 `Email Template`、`Email Account`、`Web Form`、以及分派规则相关 DocType 上。**本次未逐个核对这些改动是否与本项目既有定制冲突**（当前项目尚无自有 app，故冲突概率低，但**导航重整与译名改造开工后须重查**）。

### 7.4 `override_whitelisted_methods`

**无**（`hooks.py:343` 该键被注释掉）。**故不与本项目的中国本地化 `override_whitelisted_methods` 方案冲突**（V-03 用它把自制科目表模板送进建公司下拉）。

---

## 八、拿不准 / 未能验证的

**全部结论均为静态读码，无一条实跑。** 具体未查实：

1. **`crm.overrides.contact.CustomContact` 与 `CustomEmailTemplate` 的实现** —— §7.1，影响面未知，**最该补查**。
2. **Quotation → Sales Order 那一步是否需人工** —— §5 注 1。
3. **`create_customer_on_status_change` 的默认值** —— §5 注 2。
4. **产品双向同步的覆盖规则** —— §5 注 3，与本项目要在 Item 上挂国标型号标记有潜在冲突。
5. **Kanban / 漏斗图 / 转化率报表的具体实现** —— 只确认了状态与概率的数据基础（§4.2），**未查前端有没有现成的漏斗可视化组件**。原设问要求查这个，未完成。
6. **frappe-ui 是否有 Vue 专属耦合** —— §6 末。
7. **静态资源路径 `/assets/crm/...`** —— §6 第 4 环按 Frappe 约定推断，未验。
8. **stars / 最后提交日期 / release 列表** —— 未核（原 Agent 报告缺失）。
9. **`add_property_setter()` 具体改了哪些字段** —— §7.3。

---

## 九、对本项目的直接影响

**一句话**：**技术上该引入——它是三个候选里侵入性最低、与 ERPNext 联动最完整、v16 信号最明确的一个**；`Lead → Deal → 报价 → 接单` 正好把演示线往前延伸到成交之前，而这是"给客户演示"最有说服力的一段（客户自己就是销售，他看得懂漏斗）。

**最主要的一个反对理由**：**它自带的中文翻译 1782 条里 689 条未译（38.7%）** —— 而本项目的最高优先级需求 `PH-P1001` 正是译名，用户的原话要求是「不应该出现有些翻译了有些没翻译的情况」。**装上 CRM 等于在演示里引进一块新的半翻译界面，且译名工作量凭空增加 689 条。** 这与 R1 定的「可信度优先」定位直接冲突——客户看到的每个界面都该是上线后要用的那个，而一块 39% 未译的界面不是。

**次要顾虑**：`override_doctype_class` 覆盖了核心 `Contact`（§7.1，影响面未查实）。

**给用户的选项应是两档**，而非"装/不装"：
- **甲：装，且把那 689 条补译纳入 `PH-P1001` 的范围** —— 演示线最完整，代价是译名工作量增加；
- **乙：不装，演示仍从「接单」起** —— 保持 R1 已定稿的 23 环节范围，漏斗改为现场口头说明（与质检/外协/月结的处置方式一致）。
