# P1-S2-R2-A 调研：官方三 App（Helpdesk / HRMS / Insights）

**调研日期**：2026-09-23
**调研方式**：`git clone --depth 1` 到 `D:\ERX-001\Reference\{helpdesk,hrms,insights}` 后读码 + GitHub API 核实
**本地对照基准**：frappe v16.34.0 / erpnext v16.35.0（`D:\ERX-001\frappe-bench\apps\`）
**未实跑**：三个 app 均**未执行 `bench install-app`**，本报告全部结论来自读码与 API，下文「拿不准」一节标明边界

---

## 一、横向对照总表

| 维度 | Helpdesk | HRMS | Insights | CRM（已调研） | Raven（已调研） | Flow（已调研） |
|---|---|---|---|---|---|---|
| 仓库 | `frappe/helpdesk` | `frappe/hrms` | `frappe/insights` | — | — | — |
| stars | 3,389 | 8,817 | 1,018 | — | — | — |
| 许可证（LICENSE 实读） | **AGPL-3.0**（`LICENSE:1`） | **GPL-3.0**（`license.txt:1`） | **AGPL-3.0**（`license.txt:1`） | — | — | — |
| 许可证矛盾 | **有**：3 个 .py 头写 `MIT License. See license.txt`，而根 LICENSE 是 AGPL；且 `hooks.py:1-8` 声明 `app_license = "AGPLv3"`，仓库里**没有 license.txt 这个文件**（只有 LICENSE） | 轻微：2 个 .py 写 MIT（共 688 个 .py） | 无（0 个 MIT 头） | — | — | — |
| **v16 兼容** | develop 要 `frappe>=16.0.0-dev,<18.0.0` 且 **`requires-python>=3.14`**；`main-hotfix` 要 `frappe>=15.116.1,<17.0.0` + py3.10 | develop 要 **`frappe>=17.0.0-dev`（不兼容 v16）**；**`version-16` 分支要 `frappe>=16.0.0,<17.0.0`** ← 这是该装的 | develop/version-3 都只写 `frappe>=15.0.0`（无上界，未针对 v16 声明） | — | — | — |
| tag / release | 有（最新 `v1.30.1`，2026-09-03） | 有（最新 `v16.20.0`，2026-09-23；v16/v15/v14 三线并行） | 有（最新 `v3.14.1`，2026-09-19；同时在发 v2.2.x） | — | — | — |
| 依赖 ERPNext | **不依赖**（`required_apps = ["telephony"]`，另需装 `frappe/telephony`） | **强依赖**（`required_apps = ["frappe/erpnext"]`） | **不依赖**（无 `required_apps`） | — | — | — |
| **zh.po 条数** | 1,379 | 2,252（develop）/ **2,172（version-16）** | 686 | 1,782 | — | — |
| **未译条数** | 649 | 151（develop）/ **42（version-16）** | 331（develop）/ **482（version-3）** | 689 | — | — |
| **未译率** | **47.1%（比 CRM 更差）** | **1.9%（version-16，远好于 CRM）** | **48.3%（develop）/ 70.3%（version-3），均比 CRM 差** | 38.7% | — | — |
| `doc_events` 侵入性 | 6 个具体 DocType（含核心 `Customer` 5 事件、`User Permission`、`DocShare`、`Comment`） | 13+ 个具体 DocType（含 `Company`、`Holiday List`、`Journal Entry`、`Payment Entry`、`User`） | **1 个**（`User.on_change`）← 三者最低 | 3 个具体 DocType | `"*"`×5 | `"*"`×5 |
| `override_doctype_class` | `Email Account`、`Assignment Rule`、`User Invitation` | **`Employee`、`Timesheet`、`Payment Entry`、`Project`**（四个核心） | **无**（注释掉） | `Contact`、`Email Template` | — | — |
| `override_whitelisted_methods` | 有 1 条：`frappe.realtime.has_permission` | **无**（注释态） | **无**（注释态） | — | — | — |
| **`regional_overrides`** | **无** | **有**：`India`（3 个 HRA/税函数）、无 China | **无** | — | — | — |
| `[deploy.dependencies.apt]` | **无** | **无** | **无** | — | `libgl1` 等 | 有 |
| Python 版本 | develop **>=3.14**（本项目环境须核）；main-hotfix >=3.10 | >=3.10 | >=3.10 | — | — | — |
| `publish_realtime` 调用 | 8 处 | 11 处 | 5 处 | — | 46 处 | — |
| 额外服务 / 进程 | 有 `realtime/handlers.js`（socketio 扩展）；`after_migrate` 要建全文索引 + 下载 textblob corpus | 无独立进程；前端两套 SPA（PWA + roster） | **duckdb 本地文件库**（`{site}/private/files/insights.duckdb`）+ ibis + pandas + SQLAlchemy 重依赖 | — | — | — |
| DocType 撞名 | **0**（全 `HD ` 前缀） | **0**（与 frappe/erpnext 逐条 comm 比对无交集） | **0**（全 `Insights ` 前缀） | 0（`CRM ` 前缀） | — | — |
| 前端形态 | 独立 SPA（Vue3 + frappe-ui + tiptap） | **desk 内页面 + 两个独立 SPA**（Vue3 + Ionic PWA、roster） | 独立 SPA（Vue3 + echarts + codemirror + vue-flow） | 独立 SPA | — | — |
| **进演示** | ❌ 不建议 | ❌ 不建议 | ❌ 不建议 | — | — | — |
| **进生产（远期）** | ⚠ 可考虑（售后立项后） | ✅ 值得（计件工资/工时立项后，装 `version-16`） | ⚠ 可考虑（BI 需求立项后） | — | — | — |

### 译名一句话结论（对照 CRM 38.7%）

- **Helpdesk 47.1% — 比 CRM 差**。且未译的是界面高频词（`1 Year`、`3 Months`、`A short description`），直接违反 `PH-P1001`。
- **HRMS（version-16）1.9% — 远好于 CRM，是三者中唯一过关的**。未译 42 条基本是财务边缘提示（`Advance Account {} currency should be...`）。
- **Insights 48.3%（develop）/ 70.3%（version-3）— 比 CRM 差，且 version-3 是三个候选里最差的一个**。未译的是 `Data Source`、`API Key`、`Foreign Key` 这种核心界面词。

---

## 二、逐 App 详答

（下列各节按统一检查项 6 条 + 专属问题逐条作答，细节补充见后。）

### 2.1 Helpdesk

- **它做什么**：客服工单系统。核心 DocType `HD Ticket`，配套 `HD Team`、`HD Agent`、`HD Customer`、`HD Service Level Agreement`、`HD Article`（知识库）、`HD Ticket Activity`。共 36 个自建 DocType，**全部 `HD ` 前缀**。
- **与 ERPNext 联动**：有，但是**单向轻联动**——`helpdesk/integrations/erpnext/` 目录（9 个文件）只做 `HD Customer ↔ Customer` 双向镜像同步（`hd_customer.py:374-427`），另有 `Erpnext Hd Settings` 单例开关。**没有**工单↔工单（Work Order）、退货（Sales Return）、质检（Quality Inspection）的任何联动。

#### 统一检查项

1. **许可证**：`Reference/helpdesk/LICENSE:1` = `GNU AFFERO GENERAL PUBLIC LICENSE Version 3`（661 行）。**矛盾三处必须报**：
   - `helpdesk/api/search.py:2`、`helpdesk/search.py:2`、`helpdesk/search_sqlite.py:2` 三个文件头写 `# MIT License. See license.txt`；
   - 这三行指向的 `license.txt` **在仓库里不存在**（只有 `LICENSE`）；
   - 另有 4 个 .py 文件头写 `License: GNU General Public License v3`（**GPL，不是 AGPL**），例：`helpdesk/helpdesk/doctype/hd_holiday/hd_holiday.py:2`。
   - `hooks.py:8` 声明 `app_license = "AGPLv3"`。**以根 LICENSE 为准：AGPL-3.0**。

2. **v16 兼容**：
   - develop 分支 `pyproject.toml:22`：`frappe = ">=16.0.0-dev,<18.0.0"`，`telephony = ">=0.0.1,<1.0.0"`；`requires-python = ">=3.14"`（**注意：3.14，非 3.10**）。
   - `main-hotfix` 分支：`frappe = ">=15.116.1,<17.0.0"`，`requires-python = ">=3.10"`。
   - **无 v16 专用分支**（不像 hrms 有 `version-16`）；发布线是 `main` / `main-hotfix` / `develop` / `legacy`，GitHub 上 100+ 分支绝大多数是 mergify 回合并支线。
   - tag/release：**均非空**，最新 release `v1.30.1`（2026-09-03，`target_commitish = main`）。本地 clone 的 develop 版本号 `helpdesk/__init__.py:1` = `1.22.2`。
   - 最后提交：2026-09-22（develop）。stars 3,389。
   - **不依赖 ERPNext**：`hooks.py:9` `required_apps = ["telephony"]` → **要额外装 `frappe/telephony`**（AGPL-3.0，23 stars，2026-08-18 最后提交）。这是一个**隐性第二个 app**。

3. **译名覆盖率**：`Reference/helpdesk/helpdesk/locale/zh.po`，6,769 行。
   - msgid 条数（去 header）：**1,379**
   - 空 msgstr：**649**
   - **未译率 47.1%** → **比 CRM（38.7%）差 8.4 个百分点**
   - `main-hotfix` 分支同一文件为**完全相同的 1,379 / 649 / 47.1%**（已核）
   - 未译样例：`1 Year`、`3 Months`、`6 Months`、`A short description`、`({0}s)`、` commented` —— 都是界面常驻词
   - po 条目来源：1,302 条来自 `desk/`（SPA 前端），743 条来自 `helpdesk/`（后端）→ **前后端字符串都收进同一个 zh.po**，说明 Frappe 的 po 机制已统管 SPA，这点与 CRM 一致

4. **DocType 命名冲突**：36 个自建 DocType，**全部 `HD ` 前缀**（唯一例外 `Erpnext Hd Settings`）。与本地 erpnext 532 个 + frappe 285 个 DocType 逐条 `comm -12` 比对：**零撞名**。策略与 CRM 相同。

5. **hook 侵入性**（`helpdesk/hooks.py`）：
   - `doc_events`（`hooks.py:77-108`）：**6 个具体 DocType，不是 `"*"`**。但注意其中 **`Customer` 挂了 5 个事件**（`after_insert`/`on_update`/`before_rename`/`after_rename`/`on_trash`，`hooks.py:82-88`）——`Customer` 是本项目 23 环节闭环上的核心表；另挂 `User Permission` 4 事件、`DocShare` 4 事件（`hooks.py:89-100`），这两个是权限基础设施表。**侵入性介于 CRM 与 Raven 之间**。
   - `override_doctype_class`（`hooks.py:140-144`）：`Email Account`、`Assignment Rule`、`User Invitation`。**`Email Account` 是 frappe 核心表**，覆盖它会影响全站收发邮件行为。
   - `override_whitelisted_methods`（`hooks.py:126-128`）：**有 1 条** —— `frappe.realtime.has_permission` → `helpdesk.overrides.realtime.has_permission`。**与本项目的科目表模板方案不冲突**（不是同一个方法），但确立了"官方 app 也会用这个 hook"的事实，将来需维护一份被覆盖方法清单。
   - `regional_overrides`：**无**。→ 不与本项目中国本地化争 `[-1]` 末位。
   - `after_install`（`helpdesk/setup/install.py:19-41`，22 个动作）：建 custom field、建默认工单状态/优先级/Agent 状态、建默认 SLA（含默认 Holiday List）、建默认 Assignment Rule、建知识库分类 + 一篇 `Introduction` 文章、**建一张 Welcome Ticket**、改 Agent/Agent Manager/Website Settings 权限、建全文索引（`sql_ddl` 会 commit）。
     **装在已有数据站点的风险**：① 它会往 `Customer` 加 custom field 并挂 5 个 doc_event，之后每次动客户资料都会走一遍 helpdesk 同步逻辑；② 会新建默认 Holiday List，可能与已有配置并存造成选项混淆；③ `add_fts_index()` 直接 `sql_ddl` 提交 DDL，**不可回滚**；④ `after_migrate` 除建索引外还会 `download_corpus()`（`helpdesk/search.py:378-388`）——**从网络下载 NLTK 语料包**（`averaged_perceptron_tagger_eng`、`punkt_tab`、`brown`）。**本项目 Windows Docker + 代理环境下这是一个明确的新增外网依赖点**，属于已知的平台坑类型。

6. **前端形态与挂载链路**：**独立 SPA**。
   - `website_route_rules`（`hooks.py:50-55`）：`{"from_route": "/helpdesk/<path:app_path>", "to_route": "helpdesk"}` —— **与 CRM 完全同构**（`<path:...>` 通配吃深链接）。
   - `[tool.bench.assets]`（`pyproject.toml:22-25`）：`build_dir = "./desk"`、`out_dir = "./helpdesk/public/desk"`、`index_html_path = "./helpdesk/www/helpdesk/index.html"` —— **三键结构与 CRM 一致，仅目录名不同**（CRM 用 `frontend`，helpdesk 用 `desk`）。
   - 技术栈：Vue 3 + frappe-ui（`@framework/ui`）+ tiptap 编辑器 + `@twilio/voice-sdk`（电话）+ tailwind + vite。
   - `add_to_apps_screen`（`hooks.py:12-20`）：注册进 Frappe 应用切换器。

7. **额外进程 / 服务 / 系统依赖**：
   - `[deploy.dependencies.apt]`：**无**（pyproject 里零 apt 声明）→ 不用改 Docker 镜像装系统库。
   - Python 依赖：`textblob==0.18.0.post0`（间接拉 nltk）。
   - **socketio 扩展**：`realtime/handlers.js`（112 行）注册 `view_ticket` / `stop_view_ticket` 等自定义 socket 事件 → **需重启 socketio 进程才生效**，是 Docker 环境的一个改造点（但不需新端口、不需独立 worker）。
   - `publish_realtime` 调用 **8 处**（远低于 Raven 的 46 处）。
   - **网络依赖**：`after_migrate` 要下 NLTK 语料（见上）。

#### 专属问题：该不该进客户演示

**不该。** 三个理由分开说：

- **（长期必需性）售后不在 23 环节闭环内**。闭环终点是收款，Helpdesk 承载的是收款之后的事。它不补任何闭环缺口。
- **（演示可信度）47.1% 未译率比已被否决的 CRM 更差**，且未译词是 `1 Year` / `3 Months` 这类每屏都见的词。按"客户看到的每个界面都应是上线后真要用的那个"的定位，装它只会给演示制造扣分点。
- **（成本）它带一个隐性第二 app（`telephony`）+ 一个网络语料下载 + 一个 socketio 扩展**，在 Windows Docker 下每一项都是已知踩过坑的类型。

**弹簧厂售后场景它能不能承载**（按字段判，不按名字判）：
`HD Ticket` 字段（`hd_ticket.json`）有 `subject` / `description` / `priority` / `status` / `ticket_type` / `customer` / `contact` / `sla` / `response_by` / `resolution_by` / `feedback_rating` / `resolution_details`。
- **能承载**：客户投诉的**受理、分派、响应时限、解决时限、满意度评分**这一层——即"投诉记录与跟踪"。
- **不能承载**：`HD Ticket` **没有任何物料/批次/数量字段**，也没有到 `Item`、`Batch`、`Serial No`、`Work Order`、`Quality Inspection` 的 Link。所以"断簧是哪一炉料、哪张工单、退回多少件、要不要返工"**它一概不管**。批量退货要走 ERPNext 的 Sales Return / Credit Note，质检要走 Quality Inspection，**Helpdesk 与这两条都没有代码级联动**（grep `erpnext` 的全部命中都在 `HD Customer ↔ Customer` 同步上）。
- 结论：它是**投诉工单台账**，不是**质量追溯系统**。弹簧厂真正要的断簧追溯（料→工序→工人→批次）在 ERPNext 侧已有骨架（Batch / Job Card / Quality Inspection），装 Helpdesk 补不上那部分。

### 2.2 HRMS

- **它做什么**：HR + 薪资。160 个自建 DocType（payroll 模块 43 个）。
- **计件工资**：**确认本项目原结论成立** —— payroll 的 43 个 DocType 里**无任何 piecework/piece-rate 表**；`grep -i "piece.?work|piece.?rate"` 在 `.py`/`.json` 中**零命中**，唯一命中在 `hrms/setup.py:400` 附近，是 `Employment Type` 的一个候选值 `"Piecework"`（**只是雇佣类型的名字，不是计件计算逻辑**）。
- **Employee / Department / Holiday List 归属**：**归 erpnext**，不归 hrms。实证：`erpnext/setup/doctype/{employee,department,holiday_list,designation}` 存在；hrms 目录下**没有**同名 doctype 目录。hrms 通过 `override_doctype_class` 接管 `Employee` 的类行为（`hooks.py:162-167`）并用 custom field 往 8 个 erpnext 主表加字段。
- **中国社保/个税/公积金**：**不支持**。`hrms/regional/` 只有 `india` 与 `united_arab_emirates` 两个目录；`grep -i china` 在 `.py`/`.json` 中零命中。

#### 统一检查项

1. **许可证**：`Reference/hrms/license.txt:1` = `### GNU GENERAL PUBLIC LICENSE Version 3`（674 行）。
   **注意：是 GPL-3.0，不是 AGPL**——与 helpdesk/insights 不同（GitHub API 的 `spdx_id` 也报 `GPL-3.0`，两者一致）。
   轻微不一致：688 个 .py 中 **2 个**写 `# MIT License. See license.txt`（`hrms/patches/post_install/update_reason_for_resignation_in_employee.py:2`、`hrms/utils/hierarchy_chart.py:2`），60 个写 GNU 头。**量级远小于"51 个 .py 写 MIT"那种矛盾**，以 license.txt 为准即可，但仍记录在案。

2. **v16 兼容**（⚠ 这是本 app 最要紧的一条）：
   - **develop 分支 `pyproject.toml` 末两行：`frappe = ">=17.0.0-dev,<18.0.0"`、`erpnext = ">=17.0.0-dev,<18.0.0"`** → **develop 不能装在本项目的 v16 上**。本地 clone 的 `hrms/__init__.py:6` = `17.0.0-dev`，证实 develop 已进 v17 开发线。
   - **`version-16` 分支：`frappe = ">=16.0.0,<17.0.0"`、`erpnext = ">=16.0.0,<17.0.0"`** → **这才是本项目该用的分支**。
   - `requires-python = ">=3.10"`（v16 与 develop 相同）。
   - 分支：30 个，其中 `version-14` / `version-15` / `version-15-hotfix` / **`version-16` / `version-16-hotfix`** / `develop` 六条主线并行维护。
   - tag/release：**均非空且最活跃**——最新 `v16.20.0`（2026-09-23，当天），同时还在发 `v15.64.2`、`v14.38.2`。**三条大版本线同时维护，是三个 app 里维护最扎实的**。
   - 最后提交：2026-09-23（今天）。stars 8,817（三者最高）。
   - **强依赖 ERPNext**：`hooks.py:7` `required_apps = ["frappe/erpnext"]`。

3. **译名覆盖率**：`Reference/hrms/hrms/locale/zh.po`（develop），12,027 行；另有 `zh_TW.po`。
   - develop：msgid **2,252** / 空 msgstr **151** / **未译率 6.7%**
   - **`version-16` 分支（实际会装的那份）：msgid 2,172 / 空 msgstr 42 / 未译率 1.9%**
   - **比 CRM（38.7%）好 36.8 个百分点，是本轮唯一在译名上过关的 app**
   - 未译样例（version-16 的 42 条）：`Advance Account {} currency should be sa...`、`Allocated Amount (Company Currency)`、`Allocation was skipped due to exceeding ...` —— 全是财务/休假边缘校验提示，**不是常驻界面词**
   - po 条目来源：2,853 条来自 `hrms/`（后端 + desk），167 条来自 `frontend/`（PWA）→ 同样统管前后端

4. **DocType 命名冲突与 Employee 归属**：
   - 160 个自建 DocType，**无统一前缀**（`Attendance`、`Leave Application`、`Salary Slip`、`Expense Claim`…）。策略与 CRM/Helpdesk/Insights **完全不同**：它不加前缀，靠"这些表本来就不在 erpnext 里"避免撞名。
   - 与本地 erpnext 532 个 + frappe 285 个逐条 `comm -12` 比对：**零撞名**（已实跑比对）。
   - **`Employee` / `Department` / `Holiday List` / `Designation` 归 erpnext，不归 hrms**。实证：
     - `frappe-bench/apps/erpnext/erpnext/setup/doctype/employee/`、`.../department/`、`.../holiday_list/`、`.../designation/` 四个目录**存在于本地 erpnext**；
     - `Reference/hrms/hrms/` 下 `find -type d -name employee -path "*doctype*"` **零命中**。
   - **但装 hrms 会改变这几张表的行为**（两条机制）：
     - `hooks.py:162-167` `override_doctype_class` 把 `Employee` 的 Python 类替换为 `hrms.overrides.employee_master.EmployeeMaster`，另接管 `Timesheet`、`Payment Entry`、`Project` 三个核心类；
     - `hrms/setup.py` 的 `get_custom_fields()` 往 **8 张 erpnext 主表**加 custom field：`Company`、`Department`、`Designation`、`Employee`、`Project`、`Task`、`Timesheet`、`Terms and Conditions`。
     - 所以答用户问：**归属不变（仍是 erpnext 的表），行为会变（类被换 + 字段被加 + 事件被挂）**。Raven 把 doc_events 挂 `Employee`/`Department` 与此不冲突（两者叠加执行），但**叠加后每次改员工资料会连跑 hrms 与 Raven 两套逻辑**。

5. **hook 侵入性**（`version-16` 分支 `hrms/hooks.py`，已单独核对）：
   - `doc_events`：**不是 `"*"`，但挂了 28 个键**——`User`、`Company`、`Holiday List`、`Timesheet`、`Payment Entry`、`Unreconcile Payment`、`Journal Entry`、`Loan`、`Employee`、`Project`、`Task`、`Leave Application`、`Expense Claim`、`Attendance Request`、`Shift Request`、`Employee Checkin`、`Payroll Entry`、`Job Offer`、`Appraisal`、`Interview`、`Shift Type`、`Leave Type`、`Salary Structure`、`Job Opening`、`Appraisal Cycle`、`Employee Onboarding`、`Salary Slip`，以及一个 `India` 区域块。
     **其中撞本项目核心的四个**：`Company`（validate + on_update 3 个动作 + on_trash）、`Journal Entry`（validate/on_submit/on_cancel）、`Payment Entry`（3 个提交态事件）、`Holiday List`。
     **侵入性排序：Raven/Flow（`"*"`）> HRMS（28 个具体 DocType，含 4 张财务核心表）> Helpdesk（6 个）> CRM（3 个）> Insights（1 个）**。虽不是 `"*"`，但它是本轮三者中最重的。
   - `override_doctype_class`（`hooks.py:155-160` @version-16）：**`Employee`、`Timesheet`、`Payment Entry`、`Project` 四个**。`Payment Entry` 是本项目收款环节的表，**这是最值得警惕的一条**。
   - `override_whitelisted_methods`：**无**（`hooks.py:331` 起整块是注释）。→ **与本项目科目表模板方案零冲突**。
   - **`regional_overrides`：有**（`hooks.py:308-314` @version-16）：只有 `"India"` 一个键，覆盖 3 个 HRA/个税函数。
     **判断：不与本项目中国本地化争 `[-1]`**。理由：`erpnext/__init__.py:145-152` 的取值逻辑是先 `.get(get_region())` 拿到当前区域的 dict，再对**同名 function_path** 取 `[-1]`。hrms 注册的是 `India` 区域下的 `hrms.hr.utils.*` 三个函数，本项目注册的是 `China` 区域下的 erpnext 函数，**区域键与函数路径两层都不相交**。**但**：若将来本项目要在 `China` 键下覆盖 hrms 的函数，就会进入同一竞争，届时装载顺序（hrms 在前 / 本地化 app 在后）才有意义。
   - `after_install`（`hrms/install.py:5-9` → `hrms/setup.py:13-25`，11 个动作）：`create_custom_fields`（8 张 erpnext 主表）、`create_salary_slip_loan_fields`、`make_fixtures`（建 Expense Claim Type 5 条、Vehicle Service Item、**Employment Type 含 `Piecework`**、Leave Type 等）、`setup_notifications`、`update_hr_defaults`（**改 `HR Settings` 单例**，设 `emp_created_by = "Naming Series"` 等）、`add_non_standard_user_types`、`set_single_defaults`（**遍历 `HR Settings` / `Payroll Settings` 所有 DocField 的 default 值写回单例**）、`setup_repost_defaults`、`create_default_role_profiles`、`run_post_install_patches`、`add_default_hr_permissions`。
     另有 `doc_events["Company"]["on_update"]` → `make_company_fixtures` + `set_default_hr_accounts` + `set_expense_claim_type_accounts`（`hooks.py:180-188`）。
     **装在已有数据站点（1 公司 `华东弹簧` / 95 科目 / 已有 SO / 已有 Item+BOM）的风险**：
     - ① **会往 `Company` 加 HR&Payroll 字段并触发 `set_default_hr_accounts`**——它会在现有 95 科目里找/建 HR 默认科目（应付职工薪酬、员工预付款、工资应付），**可能在已定型的科目表里新增科目**，这与本项目"自制科目表模板"的工作直接相邻，是最大的风险点；
     - ② `Payment Entry` 与 `Journal Entry` 被挂提交态事件 + `Payment Entry` 类被覆盖 → **收款环节的行为面变宽**；
     - ③ 160 个 DocType + 8 张表的 custom field 一次性进库，**演示环境的 Desk 侧边栏与搜索结果会显著变杂**；
     - ④ `before_uninstall` 会 `delete_custom_fields` + `delete_company_fixtures`，卸载路径存在但**未实测**。

6. **前端形态与挂载链路**：**混合形态**（与 CRM/Helpdesk 不同）。
   - 主体是 **desk 内页面**：`hooks.py` 有 `app_include_js`（数个 bundle）+ `app_include_css = "hrms.bundle.css"`，160 个 DocType 走标准 Desk 表单。
   - 另有**两个独立 SPA**：`frontend/`（员工自助 PWA，Vue3 + `@ionic/vue` + `vite-plugin-pwa` + **firebase** 推送）与 `roster/`（排班表，Vue3 + frappe-ui）。
   - `website_route_rules`（`hooks.py:82-85`）：`{"from_route": "/hrms/<path:app_path>", "to_route": "hrms"}` 与 `{"from_route": "/hr/<path:app_path>", "to_route": "roster"}` —— **`<path:...>` 通配写法与 CRM/Helpdesk 完全一致**，只是它有两条。
   - **`[tool.bench.assets]`：无此段**（`pyproject.toml` 里没有 `[tool.bench.assets]`）。它用**根 `package.json` 的 `build` 脚本**自建两个 SPA（`build-pwa` + `build-roster`），产物走 `www/hrms.py` 与 `www/roster.py` 两个 Python 页面控制器。
   - **对"React 全面重写"这一关键判断的支持**：Helpdesk 与 Insights 的三键结构与 CRM 一致，**hrms 则证明连三键都可以不用**——`website_route_rules` + `www/*.py` 控制器这条挂载链路是"给我一个路由前缀，我吐一个 index.html"，**与前端框架完全无关**。三个样本合起来，这个结论得到进一步支持（详见 §四前的小结）。

7. **额外进程 / 服务 / 系统依赖**：
   - `[deploy.dependencies.apt]`：**无**。
   - Python 依赖：`pyproject.toml` **没有 `dependencies` 段**（零额外 pip 包）。
   - Node：构建期需 yarn 装两套 SPA 依赖（`postinstall` 跑 `frontend` + `roster` 两次 `yarn install`）→ **构建时间明显变长**，但运行期无独立 Node 进程。
   - `publish_realtime` **11 处**（低）。
   - **firebase**：PWA 前端依赖 `firebase`（`frontend/package.json`）→ 推送要连 Google 服务。**中国大陆环境下这条大概率不通**，但它只影响 PWA 推送，不影响 Desk 主体（**此判断为读依赖清单的推断，未实测**）。
   - 无新端口、无独立 worker。

#### 专属问题 1：计件工资（缺口 7 / `PH-P1009`）

**先确认本项目两条实测都成立**：

- ① **payroll 43 个 DocType 无计件表** —— 已复核（本次数到 43 个，用户记为 44，差 1 个可能是数法差异，**结论一致**）：`additional_salary arrear bulk_salary_structure_assignment employee_benefit_* employee_cost_center employee_incentive employee_other_income employee_tax_exemption_* gratuity* income_tax_slab* payroll_correction* payroll_employee_detail payroll_entry payroll_period* payroll_settings retention_bonus salary_component salary_component_account salary_detail salary_slip salary_slip_leave salary_slip_loan salary_slip_timesheet salary_structure salary_structure_assignment salary_withholding salary_withholding_cycle taxable_salary_slab`。**无一条与 piece 相关**。
  `grep -rni "piece.?work|piece.?rate|per_piece|piece_qty"` 在 `.py`/`.json` **零命中**；唯一命中在各语言 po 文件里的 `msgid "Piecework"`，其源位置注释是 `#: hrms/setup.py:400` —— 即 `make_fixtures()` 建的 **`Employment Type` 候选值之一**。**这是"雇佣类型叫计件工"，不是"按件算钱的逻辑"。名字像 ≠ 有能力，此处正是那个陷阱。**
- ② **`Job Card Time Log` 已带三字段** —— 已实测本地 erpnext v16.35.0：`erpnext/manufacturing/doctype/job_card_time_log/job_card_time_log.json` 字段为 `from_time`、`to_time`、`time_in_mins`、**`completed_qty`**、**`employee`**、**`operation`**。用户结论成立：「哪个工人、哪道工序、完工多少件」**已在库里，且不需要 hrms**。

**Salary Component / Structure / Slip 能不能接受"数量×单价"**（这是本次要查实的核心）：

- `Salary Component` 有 `amount_based_on_formula:Check` + `formula:Code` + `condition:Code`（`salary_component.json`）；`Salary Detail` 同样有 `condition` / `amount_based_on_formula` / `formula`。**所以"公式"这个位置是存在的。**
- **但公式能看到什么数据是被严格限死的**。求值链：`salary_slip.py:1383-1394 eval_condition_and_formula()` → `_safe_eval(formula, self.whitelisted_globals, data)`。
  - `whitelisted_globals = COMPONENT_EVAL_GLOBALS`（`hrms/payroll/utils.py:45-59`）**只有 13 个名字**：`int float long round rounded date getdate get_first_day get_last_day ceil floor min max`。
  - **没有 `frappe`，没有 `frappe.db`，没有 `get_doc`，没有 `get_all`。**
  - `data` 的构成（`salary_slip.py:1358-1381` + `utils.py:87-99`）= 薪资组件缩写默认值 map + Salary Slip 字段默认值 + **Salary Structure Assignment 的字段** + **`Employee` 文档的全部字段** + 本期各组件已算出的金额。
  - 另有 `utils.py:102-121 _check_attributes()` 用 AST 禁掉 `__`、`lambda`、海象运算符与全部 `UNSAFE_ATTRIBUTES`。
- **结论（有源码行号依据）：hrms 的薪资公式无法引用自定义 DocType 的数据，也无法查库。** 它只能拿 `Employee` 字段、SSA 字段、其它组件金额来做算术。**所以"本月完工件数"这个数进不了公式**——除非先把它写成 `Employee` 或 `Salary Structure Assignment` 上的一个字段，或者用 `Additional Salary` 把算好的金额整笔塞进这张 Salary Slip。

**两条路的代价**：

| | 路 A：装 hrms，在其体系内扩展 | 路 B：不装 hrms，自己从 Job Card Time Log 算 |
|---|---|---|
| 实现方式 | 建工序单价主数据 → 写定时/触发脚本汇总 `Job Card Time Log`（按 `employee`+`operation`+`completed_qty`）→ 为每人每期生成一条 **`Additional Salary`**（金额已算好）→ Salary Slip 自动并入 | 建工序单价主数据 → 建一张可提交的「计件工资单」DocType → 从 `Job Card Time Log` 拉数算钱 → 提交时生成 Journal Entry 计入应付职工薪酬 |
| 必须付的代价 | 160 个 DocType 进库；4 个核心类被覆盖（含 `Payment Entry`）；28 个 DocType 挂 doc_events（含 `Company`/`Journal Entry`/`Payment Entry`）；`Company` 被加 HR 科目字段并可能新建科目；构建期多两套 SPA；**且计件逻辑仍要自己写**（hrms 不提供） | 自建 1~2 个 DocType + 一段汇总逻辑 + 一张 JE 模板；**没有任何 hook 冲突、无 app 依赖、无构建负担** |
| 换来的好处 | 白拿 Salary Structure / Salary Slip 的工资单格式、个税框架（印度）、考勤/休假/工时全套；工资单据与会计分录已通；将来要做全套 HR 时不用重做 | 轻；完全可控；译名不受第三方 po 影响 |
| 不能解决的 | 中国社保/个税/公积金**它也没有**（见下），仍要自建 | 工资单格式、个税、社保全部自建 |

**判断：计件工资这一项本身，路 B 更划算。** 依据是 hrms 并不提供计件逻辑（要自己写的部分两条路一样多），而它索取的代价（4 个核心类覆盖 + 28 个 doc_events + 动 `Company` 科目）与"算一笔计件钱"这件事不成比例。
**但要说清分界**：若本项目将来要做的不止计件，而是**考勤 + 休假 + 工资单 + 员工自助**整套 HR，那 hrms 是该装的（它是三个 app 里维护最扎实、译名最好的一个），届时计件仍按上表路 A 的 `Additional Salary` 方式接入。**决策点不在"计件怎么算"，而在"要不要整套 HR"。**

#### 专属问题 2：装 hrms 对 Employee / Department / Holiday List 的影响

见上文第 4 条与第 5 条。摘要：**归属不变（都是 erpnext 的表）**；行为改变有三条——`Employee` 的 Python 类被 `EmployeeMaster` 替换、`Employee`/`Department` 等 8 张表被加 custom field、`Holiday List` 被挂 `on_update`/`on_trash` 缓存失效钩子。与 Raven 在 `Employee`/`Department` 上的 `doc_events` **叠加执行不覆盖**，但两者同装会让改一次员工资料连跑两套逻辑。

#### 专属问题 3：中国社保 / 个税 / 公积金

**明确回答：没有 china。**
- `hrms/regional/` 下只有 **`india`** 与 **`united_arab_emirates`** 两个目录（`ls hrms/regional/` 实跑）。
- `hooks.py:308-314` 的 `regional_overrides` 只有 `"India"` 一个键。
- `grep -rni "china" hrms --include=*.py --include=*.json` **零命中**。
- 个税框架（`Income Tax Slab`、`Taxable Salary Slab`、`Employee Tax Exemption *`）在结构上是通用累进税率表，**理论上可配中国个税税率**，但中国的专项附加扣除、累计预扣预缴算法、社保三险一金基数上下限**均无对应 DocType**。（**此为读 DocType 清单的推断，未实建验证。**）

### 2.3 Insights

- **它做什么**：BI 工具（自助查询 + 图表 + 仪表盘）。克隆到的 develop 是 **v4.0.0-dev**（`insights/__init__.py:6`），DocType 全带 `V3` 后缀（`Insights Query V3` 等 21 个），即**代码基是 v3 架构**；v2 代码已被拆走（有 `split-v2-code` 分支，且仍在发 `v2.2.x`）。
- **duckdb 确认存在**：`pyproject.toml` 直接依赖 `duckdb~=1.4.3` + `ibis-framework~=11.0.0` + `pandas` + `SQLAlchemy` + `psycopg`。它会在 `{site}/private/files/insights.duckdb` 建一个本地列式数据仓库（`data_warehouse.py:68`，`WAREHOUSE_DB_NAME = "insights"`），把源表导入其中再查。**不是直连 MariaDB 出报表，是另建一份数据副本。**
#### 统一检查项

1. **许可证**：`Reference/insights/license.txt:1` = `GNU AFFERO GENERAL PUBLIC LICENSE Version 3`（661 行）。
   **无矛盾**：`grep -rln "MIT License" --include=*.py` **零命中**，1 个文件带 GNU 头，其余统一写 `# For license information, please see license.txt`。**三个 app 里许可证最干净的一个。**

2. **v16 兼容**：
   - develop 与 `version-3` 分支的 `pyproject.toml` 都只写 **`frappe = ">=15.0.0"`（无上界，也未针对 v16 声明）**。`requires-python = ">=3.10"`。
     **判断：这是"没写死所以装得上"，不是"声明支持 v16"。** 与 hrms 的 `>=16.0.0,<17.0.0` 那种明确声明性质不同，风险更高。
   - 分支 29 个，主线为 `develop` / `main` / `version-3` / `version-3-hotfix`，另有 `split-v2-code`。**无 v16 专用分支**。
   - tag/release：**均非空**——最新 tag `v3.14.1`（2026-09-19），且**同时仍在发 v2 线**（`v2.2.15`，2026-09-22）。
   - 最后提交：2026-09-23（今天）。stars 1,018（三者最低）。
   - **不依赖 ERPNext**：`hooks.py` 无 `required_apps`。
   - **Python 依赖很重**（`pyproject.toml:10-25`）：`pandas~=2.3.3`、`SQLAlchemy==2.0.41`、`duckdb~=1.4.3`、`sqlglot`、`ibis-framework~=11.0.0` + 其 duckdb/mysql/sqlite/clickhouse/postgres 五个 extras、`psycopg[binary]`、`python-telegram-bot==21.4`。**这是本轮三个 app 里唯一带重型数据栈的。**

3. **译名覆盖率**：`Reference/insights/insights/locale/zh.po`（develop），3,595 行；另有 `zh_TW.po`。
   - develop：msgid **686** / 空 msgstr **331** / **未译率 48.3%**
   - **`version-3` 分支：msgid 686 / 空 msgstr 482 / 未译率 70.3%** ← **三个候选里最差的一份**
   - 两者都**比 CRM（38.7%）差**
   - 未译样例（version-3）：`API Configuration`、`API Key / Bearer Token`、`Above average`、`1:1`、`1:N`；develop 未译样例：**`Data Source`**、`Force Refresh`、`Foreign Key`、`Fiscal Year Start` —— **`Data Source` 是这个 app 最核心的一个词，它没译**
   - po 条目来源：531 条来自 `frontend/`，502 条来自 `insights/` → 前端占比过半，而未译主要落在前端
   - **对 `PH-P1001` 的含义**：这是一个"客户一打开就看到一屏英文按钮"的 app。以"可信度优先"的定位，它是本轮最不该出现在演示里的一个。

4. **DocType 命名冲突**：21 个自建 DocType，**全部 `Insights ` 前缀**（`Insights Query V3`、`Insights Chart V3`、`Insights Dashboard V3`、`Insights Data Source V3`、`Insights Workbook`、`Insights Team`…）。与本地 erpnext + frappe 逐条比对：**零撞名**。策略与 CRM 相同。

5. **hook 侵入性**（`insights/hooks.py`，254 行）：
   - `doc_events`（`hooks.py:162-166`）：**只有 1 个** —— `User.on_change` → `update_admin_team`。**本轮三者中最低，也低于 CRM 的 3 个。**
   - `override_doctype_class`：**无**（`hooks.py:154-156` 是注释）。
   - `override_whitelisted_methods`：**无**（`hooks.py:196-198` 是注释）。→ **与本项目科目表模板方案零冲突。**
   - `regional_overrides`：**无**。
   - 另有一条别的 app 没有的：**`page_renderer = "insights.utils.InsightsPageRenderer"`（`hooks.py:243`）** —— 它插进 Frappe 的页面渲染链。这是全站级别的 hook，**虽然只为把 `/insights` 路由交给自己的 SPA，但它确实是一条全局介入点**（读码判断其作用范围仅限自身路由，**未实测**）。
   - `fixtures`（`hooks.py:105-110`）：只导出 `Insights Data Source v3` 里 name = `Site DB` 的那一条。
   - `after_install = "insights.migrate.after_migrate"`（`hooks.py:99`，与 `after_migrate` 同一个函数）：动作很少 —— `create_admin_team()`（建一个 `Insights Team` 名为 `Admin`，成员 Administrator）+ 模板指纹重戳与同步（`migrate.py:27-56`）。
     **装在已有数据站点的风险：三个 app 里最低。** 它不加 custom field、不改 `Company`、不动科目、不建业务单据。唯一副作用是建 Admin Team 与 `Site DB` 数据源。
   - `scheduler_events`（`hooks.py:171-186`）：`all` 队列跑 `send_alerts`，`hourly` 跑数据同步状态更新与导入任务，`daily` 跑 `sync_tables` + **`telemetry_scan.run_site_scan`**，`weekly` 跑 `cleanup_data_store`。
     **注意 `telemetry_scan.run_site_scan` 是每日一次的站点扫描（遥测）**，本项目若装，应确认它是否外发（**本次未追这条链路，列入拿不准**）。

6. **前端形态与挂载链路**：**独立 SPA**。
   - `website_route_rules`（`hooks.py:245-248`）：`{"from_route": f"/{insights_path}/<path:app_path>", "to_route": "_insights"}` + 一条不带 path 的兜底。**`<path:...>` 通配写法与 CRM/Helpdesk/HRMS 一致**；不同之处是路由前缀可由 `frappe.conf.insights_path` 配置（`hooks.py:18-21` 有注释警告：多站点共享 bench 进程时，先 import 的站点的值会生效——**这是一个已知的多站点隐患，作者自己写在注释里**）。
   - **`[tool.bench.assets]`：无此段**（与 hrms 相同）。它走 `www/_insights.py` 页面控制器 + 根 `package.json` 的 `build` 脚本（`cd frontend && yarn build`）。
   - 技术栈：Vue 3 + **echarts**（图表）+ codemirror（SQL/Python 编辑器）+ `@vue-flow/core`（查询关系图）+ `@tanstack/vue-table` + tailwind。源码在 **`frontend/src2/`**（不是 `src/`，印证 v3 是重写版）。

7. **额外进程 / 服务 / 系统依赖**：
   - `[deploy.dependencies.apt]`：**无**（pyproject 零 apt 声明）。
   - **但这不等于无系统依赖**：`duckdb`、`psycopg[binary]`、`ibis-framework` 五个 extras 都要在 Windows Docker 镜像里 pip 编译/安装成功。`ibis-framework[clickhouse]`、`[postgres]`、`[mysql]` 会拉一串数据库驱动。**这是本轮三个 app 里对镜像最有可能造成麻烦的一个，属于本项目已踩过的"Python 依赖装不上"坑类型。**（**未实测。**）
   - **独立数据库：是。** 不是独立 DB 服务，而是**一个本地 duckdb 文件**：`data_warehouse.py:68` 拼出 `{private files}/insights.duckdb`（`WAREHOUSE_DB_NAME = "insights"`），并用 `local_duckdb_write_lock` 做写锁（`connectors/duckdb.py:96-134`）。它把源表**导入**这个文件再查（`UNUSED_TABLE_DAYS = 30` 会淘汰 30 天未用的表，`weekly` 跑 `cleanup_data_store`）。
     **这意味着：仪表盘看到的数不是实时的，是上次同步时的。** 这对"演示产量/良率实时看板"是一个实质性限制。
   - `publish_realtime` **5 处**（三者最低）。
   - 无独立 worker、无新端口、无 socketio 扩展、无 Node 运行期进程。

#### 专属问题 1：版本（v2 还是 v3）

**克隆到的 develop 是 v3 架构的延续，版本号 `insights/__init__.py:6` = `4.0.0-dev`。** 依据三条：① 21 个 DocType 全带 `V3` 后缀（`Insights Query V3`、`Insights Data Source V3`…），无一个 v2 DocType；② 前端源码目录是 `frontend/src2/`；③ 仓库有 `split-v2-code` 分支且仍在独立发 `v2.2.x` release，说明 v2 已被剥离维护。
**若要装，稳妥选择是 `version-3` 分支（有 tag 的发布线）** —— 但注意它的 zh.po 未译率 **70.3%**，比 develop 的 48.3% 还差得多。**"选稳定分支"与"选译名好一点的分支"在这个 app 上是矛盾的。**

#### 专属问题 2：能不能补上中国财务报表格式（尤其现金流量表）

**明确回答：不改变本项目原结论。现金流量表仍然要自建单据 + 从 GL Entry 拉流水。**

四条依据：

1. **Insights 不认识会计语义。** `grep -rni "gl entry|gl_entry" insights --include=*.py` **零命中**。它眼里没有"科目""借贷""现金流量项目"，只有表和列。所有会计含义都得由用户在查询里手写。
2. **它不是报表引擎，是查询+图表工具。** 图表类型是固定的 9 种（`frontend/src2/types/chart.types.ts:5-18`）：`Number`、`Bar`、`Line`、`Row`、`Donut`、`Funnel`、`Table`、`Map`、`Bubble`、`Sankey`、`Heatmap`。**中国现金流量表的样式（三大类分组、"加："/"减："缩进行、小计与合计层级、补充资料表）不在这 9 种任何一种里**，只能退化成一张 `Table`。
3. **"直接法需要把每笔现金收支归类到现金流量项目"这个判断，Insights 一个字也没帮上。** 归类要么靠单据上人工选的现金流量项目字段（这就是本项目原方案里"自建可提交单据"的由来），要么靠科目对科目的规则推断。**Insights 只能查已经归好类的数据，不能替你归类。** 这正是原结论的核心，Insights 不触碰它。
4. **v16 的 `Financial Report Template` 仍是更对的工具。** 本地已确认存在 `erpnext/accounts/doctype/financial_report_template/` 与 `erpnext/accounts/financial_report_template/`。资产负债表与利润表继续走它；现金流量表继续按原方案自建。

**所以 Insights 在财务报表这一项上的定位是：零帮助，不减负。**

#### 专属问题 3：对客户演示的说服力（老板看板）

**能力上能做，但四个前提都不成立，所以演示不该用它。**

- **能做的部分（有依据）**：数据源连接方式已查实 —— `connectors/frappe_db.py:20-45 get_primary_data_source()` 会读 `frappe.conf` 的 `db_host` / `db_port` / `db_name` / `db_password`，建一个名为 **`Site DB`** 的数据源。`Insights Data Source V3` 的 `database_type` 选项为 `MariaDB / PostgreSQL / SQLite / DuckDB / BigQuery / ClickHouse`，并有 `is_site_db` 勾选。
  **即：它是拿站点 DB 的真实凭据直连 MariaDB 读表，不是走 Frappe ORM / query report。** 这有两个含义：① 它**绕过 Frappe 的权限层**读原始表（自己另做一套 `Insights Team` / `Insights Resource Permission` 权限）；② 连接是 SQL 层的，所以"产量、良率、在制品、应收账龄"这些只要 SQL 写得出来就能出图。
- **四个前提不成立**：
  1. **译名**：48.3%~70.3% 未译，`Data Source` 这种核心词都是英文。老板看板出现在演示里，等于把最刺眼的未译界面推到最前面。**直接撞 `PH-P1001`。**
  2. **数据不实时**：数据先导入 `insights.duckdb` 再查（`data_warehouse.py`），看板反映的是上次同步时刻。演示"实时产量"会露馅。
  3. **没有现成看板**：`fixtures` 只导一条数据源，**不带任何预置仪表盘**。产量/良率/在制品/应收账龄四张图**全部要自己从零建查询**，工作量不小于用 ERPNext 原生 Dashboard Chart + Number Card 搭一套。
  4. **演示环境数据量**：演示站点数据稀薄（1 公司、少量 SO、少量 BOM），BI 图表在数据稀薄时非常难看——空图比没有图更减分。
- **更省的替代**：ERPNext v16 原生就有 `Dashboard Chart` / `Number Card` / `Dashboard`（本地 erpnext 里有 `manufacturing/dashboard_chart/job_card_analysis` 这类现成图表），**译名走 erpnext 自己的 po（覆盖率远好于 Insights），且数据实时、零新增 app**。演示看板应当走这条。

**"为演示加分"与"长期必需"分开说**：
- 为演示加分：**负分**（未译 + 空图 + 要自己建查询）。
- 长期必需：**不是必需，但有真实价值**。当客户上线一段时间、数据积累起来、且提出"我要自己拉数看"的需求时，Insights 是正确工具（它的 hook 侵入性是本轮最低的，装它的技术代价很小）。**它的问题几乎全在译名与时机，不在架构。**

---

---

## 三、跨 App 得到的一个通用结论：SPA 挂载链路与前端框架无关

这条是本次调研的附带收获，对"远期用 React 全面重写前端"这个决策有直接意义。

四个样本（CRM + 本轮三个）的挂载写法：

| App | `website_route_rules` | `[tool.bench.assets]` | 页面控制器 | 前端栈 |
|---|---|---|---|---|
| CRM | `/crm/<path:app_path>` → `crm` | `./frontend` / `../crm/public/frontend` / `../crm/www/crm.html` | `www/crm.html` | Vue3 |
| Helpdesk | `/helpdesk/<path:app_path>` → `helpdesk` | `./desk` / `../helpdesk/public/desk` / `../helpdesk/www/helpdesk/index.html` | `www/helpdesk/index.html` | Vue3 + tiptap |
| HRMS | `/hrms/<path:app_path>` → `hrms`；`/hr/<path:app_path>` → `roster` | **无此段** | `www/hrms.py`、`www/roster.py` | Vue3 + Ionic PWA、Vue3 |
| Insights | `/{insights_path}/<path:app_path>` → `_insights`（+ 无 path 兜底） | **无此段** | `www/_insights.py` | Vue3 + echarts |

**结论（三条，均有依据）**：

1. **`<path:...>` 通配吃 SPA 深链接这一机制，四个样本全部一致**，且不只 CRM 一家这么写。这是 Frappe 侧的标准做法，**与前端用什么框架完全无关**——它只做一件事：把 `/前缀/任意深路径` 全部路由到同一个页面。
2. **`[tool.bench.assets]` 三键不是必需的**。HRMS 与 Insights 都没有这一段，它们用 `www/*.py`（Python 页面控制器）+ 根 `package.json` 的 build 脚本自建产物。**所以三键只是"让 bench 帮你 build"的糖，不是挂载的必要条件**。本项目若用 React，两条路都可走：要么照 CRM/Helpdesk 填三键让 bench 管构建，要么照 HRMS/Insights 自己管构建只留一个 `www/*.py` 控制器。
3. **四个样本全是 Vue3 + frappe-ui**，所以"官方都用 Vue"是事实；但从上面两条看，**这是生态惯例而非机制约束**。换 React 要付的代价是失去 frappe-ui 组件库与 `frappe-ui` 的资源加载约定，**不是要改挂载链路**。

（第 3 条的"代价"部分为读依赖清单后的推断，**未实建 React 验证**。）

---

## 四、拿不准 / 未实跑

**明确区分读码与实测。本报告除下列标注项外，其余均为读源码/读 API 的一手事实。**

### 已实测（本机实跑命令）

- 三个仓库均已 `git clone --depth 1` 成功，落在 `D:\ERX-001\Reference\{helpdesk,hrms,insights}`。
- 全部 zh.po 计数为**本机脚本实跑**（脚本处理了 po 的多行续行，不是简单 `grep -c '^msgstr ""$'`——后者会把带续行的条目误判为未译，故本报告的数字与粗 grep 略有差异，以脚本结果为准）。
- DocType 撞名比对为**实跑 `comm -12`**，对照集是本地 `erpnext` 532 个 + `frappe` 285 个 doctype 目录名。
- `Job Card Time Log` 六个字段为**实读本地 erpnext v16.35.0 的 json**。
- `hrms/regional/` 只有 india 与 uae、`grep -i china` 零命中，为**实跑**。
- hrms `version-16` 分支的 hooks 与 pyproject 为**单独 curl 下来实读**，不是拿 develop 推的。

### 未实跑 / 推断（不可当定论）

1. **三个 app 全部未执行 `bench install-app`**。所有 `after_install` 副作用（尤其 hrms 会不会真在 95 科目里新建 HR 科目、helpdesk 的 `add_fts_index` 在 MariaDB 下是否顺利）**均为读码推断**。
2. **Windows Docker 下的可安装性未测**：Insights 的 `duckdb` + `ibis-framework` 五个 extras + `psycopg[binary]` 能否在本项目镜像里装上，**完全未验证**。按本项目历史，这类重型 Python 依赖是高风险项。
3. **Helpdesk develop 要 `requires-python >= 3.14`**，而本项目容器内 Python 版本**本次未能查实**（`docker/` 目录下只有 `apps.json` / `compose.yaml` 等，未找到写明 Python 版本的 Dockerfile）。若容器是 3.11/3.12，**helpdesk develop 装不上，只能用 `main-hotfix`（要 py>=3.10、frappe>=15.116.1,<17.0.0）**。这条需在决定装之前先核容器 Python 版本。
4. **po 未译率是静态度量，不等于演示路径上的可见未译量**。真实观感要装上后走一遍 23 环节才知道。不过 helpdesk 与 insights 的未译词里有 `Data Source`、`1 Year`、`3 Months` 这类高频词，**可见量大概率不低**。
5. **Insights 的 `telemetry_scan.run_site_scan`（daily）是否外发数据**，本次未追调用链，**未知**。若装，应先看这一条。
6. **HRMS PWA 依赖 firebase 是否在大陆网络下阻塞**，为读 `frontend/package.json` 的推断，**未实测**；判断其只影响 PWA 推送不影响 Desk 主体，亦为推断。
7. **Insights 的 `page_renderer` 全局 hook 的实际作用范围**，读码判断仅限自身路由，**未实测**。
8. **hrms payroll DocType 数**：本次数到 43 个，用户记录为 44 个。差 1，可能是数法差异（是否计入某个不在 `payroll/doctype/` 下的表）。**"无计件表"这个结论不受影响。**
9. **中国个税能否用 `Income Tax Slab` 配出来**：只看了 DocType 清单与字段名，**未实建税率表验证**。专项附加扣除与累计预扣预缴无对应 DocType 是读清单所得；能否用现有字段变通实现，**未验证**。
10. **卸载路径**：三个 app 的 `before_uninstall` 都存在（hrms 会删 custom field 与 company fixtures），但**卸载是否干净、会不会留下孤立数据，全部未测**。

---

---

## 五、对本项目的建议

| App | 一句话结论 | 最主要的一个反对理由 | 进演示 | 进生产 |
|---|---|---|---|---|
| Helpdesk | 是投诉工单台账，不是质量追溯系统，且译名比 CRM 还差 | **47.1% 未译（比 CRM 差 8.4 点），直接撞 `PH-P1001`** | ❌ 不进 | ⚠ 仅在售后单独立项后考虑 |
| HRMS | 译名是本轮唯一过关的（1.9%）、维护最扎实，但它补不上计件工资这个真缺口 | **索取代价与所得不成比例：4 个核心类被覆盖（含 `Payment Entry`）+ 28 个 DocType 挂 doc_events + 动 `Company` 的 HR 科目，而计件逻辑仍要自己写** | ❌ 不进 | ✅ 条件性推荐：**要整套 HR 时装，且必须装 `version-16` 分支**（develop 已要 frappe>=17，装不上） |
| Insights | 架构代价最低（hook 侵入性本轮最小），但译名最差、数据非实时、零预置看板 | **48.3%（develop）/ 70.3%（version-3）未译，本轮最差，连 `Data Source` 都没译** | ❌ 不进 | ⚠ 客户数据积累后、提出自助取数需求时再考虑 |

### 共同结论

**本轮三个 app 都不进客户演示。** 演示定位是「可信度优先」，逐个对上这条判据：

- Helpdesk 与 Insights 的未译率**比已被否决的 CRM 更差**（47.1% / 48.3%~70.3% vs 38.7%）。既然 38.7% 已被认定为反对 CRM 的最硬理由，这两个连门槛都没到。
- HRMS 译名过关（1.9%），**它是唯一在 `PH-P1001` 上站得住的一个**——所以否决它的理由不是译名，而是：① 它的功能不在 23 环节闭环上（闭环里没有考勤、休假、工资单）；② 它是本轮侵入性最高的一个，且恰好压在本项目正在建设的两处（`Company` 的科目体系、`Payment Entry` 收款）。**为演示装它 = 给闭环增加风险却不增加闭环内容。**

### 三条落在具体动作上的提醒

1. **若将来决定装 hrms，必须指定 `version-16` 分支**。`develop` 的 `pyproject.toml` 已改成 `frappe>=17.0.0-dev` / `erpnext>=17.0.0-dev`，装在本项目 v16 上会被 bench 的依赖检查拦住（或更糟：绕过检查后运行期出错）。`docker/apps.json` 现在只有 frappe / erpnext 两条，将来加条目时 `branch` 要写 `version-16`。
2. **若将来决定装 helpdesk，先核容器 Python 版本**。develop 要 `>=3.14`；若容器低于此，只能用 `main-hotfix`（`frappe>=15.116.1,<17.0.0`，py>=3.10）。另外它会连带装 `frappe/telephony`（第二个 app），且 `after_migrate` 要联网下 NLTK 语料——**在 Windows Docker + 代理环境下这两条都要单独验证**。
3. **`override_whitelisted_methods` 冲突风险：本轮三个 app 全部无风险**。helpdesk 只覆盖 `frappe.realtime.has_permission`（与科目表模板方案不是同一方法），hrms 与 insights 都是注释态。**本项目把自制科目表模板送进建公司下拉的方案，不会被这三个 app 中任何一个抢走。** 同理 `regional_overrides`：只有 hrms 有，且只注册 `India` 区域，与本项目的 `China` 键在区域与函数路径两层都不相交。

### 计件工资（缺口 7 / `PH-P1009`）的独立建议

**推荐路 B：不装 hrms，自建计件工资单，从 `Job Card Time Log` 取数。**

依据是一条读码事实：**hrms 的薪资公式引擎看不到自定义数据**——`hrms/payroll/utils.py:45-59` 的 `COMPONENT_EVAL_GLOBALS` 只白名单了 13 个数学/日期函数，**没有 `frappe`、没有 `frappe.db`、没有 `get_doc`**；可见数据（`salary_slip.py:1358-1381`）只有 Employee 字段 + SSA 字段 + 其它组件金额。所以"本月完工 N 件 × 单价"这个式子**在 hrms 里也写不出来**，必须在外面算好再用 `Additional Salary` 塞进去。既然算的部分两条路一样多，就没有理由为此承担 160 个 DocType 与 4 个核心类覆盖。

**唯一会翻转这个结论的情形**：本项目决定做整套 HR（考勤 + 休假 + 工资单 + 员工自助）。那时 hrms 是正确选择（译名 1.9%、三条版本线在维护、8.8k stars），计件按 `Additional Salary` 方式接入即可。**决策点是"要不要整套 HR"，不是"计件怎么算"。**

---

## 附：克隆位置与可复现命令

```bash
# 克隆（helpdesk 直连成功；insights 需代理）
cd D:/ERX-001/Reference
git clone --depth 1 https://github.com/frappe/helpdesk.git helpdesk
git clone --depth 1 https://github.com/frappe/hrms.git hrms
git -c http.proxy=http://127.0.0.1:7897 clone --depth 1 https://github.com/frappe/insights.git insights

# 许可证实读
head -3 D:/ERX-001/Reference/helpdesk/LICENSE        # AGPL-3.0
head -3 D:/ERX-001/Reference/hrms/license.txt        # GPL-3.0
head -3 D:/ERX-001/Reference/insights/license.txt    # AGPL-3.0
grep -rn "MIT License" --include=*.py D:/ERX-001/Reference/helpdesk   # 3 处矛盾

# v16 兼容（关键：hrms develop 要 frappe>=17）
grep -A3 "tool.bench.frappe-dependencies" D:/ERX-001/Reference/{helpdesk,hrms,insights}/pyproject.toml
curl -s https://raw.githubusercontent.com/frappe/hrms/version-16/pyproject.toml | grep -A3 frappe-dependencies

# 译名计数（用能处理多行续行的脚本，不要用裸 grep -c '^msgstr ""$'）
# 各 app 的 zh.po 路径：
#   D:/ERX-001/Reference/helpdesk/helpdesk/locale/zh.po
#   D:/ERX-001/Reference/hrms/hrms/locale/zh.po
#   D:/ERX-001/Reference/insights/insights/locale/zh.po
wc -l <各 zh.po>

# DocType 撞名比对
find D:/ERX-001/frappe-bench/apps/erpnext/erpnext -type d -path "*/doctype/*" | sed 's|.*/doctype/||' | grep -v '/' | sort -u > /tmp/erpnext_dt.txt
find D:/ERX-001/Reference/hrms/hrms -type d -path "*/doctype/*" | sed 's|.*/doctype/||' | grep -v '/' | sort -u > /tmp/hrms_dt.txt
comm -12 /tmp/hrms_dt.txt /tmp/erpnext_dt.txt   # 空 = 无撞名

# 计件相关（零命中 = 无计件表）
grep -rni -E "piece.?work|piece.?rate|per_piece|piece_qty" D:/ERX-001/Reference/hrms/hrms --include=*.py --include=*.json

# 中国区域支持（零命中）
ls D:/ERX-001/Reference/hrms/hrms/regional/          # 只有 india、united_arab_emirates
grep -rni "china" D:/ERX-001/Reference/hrms/hrms --include=*.py --include=*.json
```
