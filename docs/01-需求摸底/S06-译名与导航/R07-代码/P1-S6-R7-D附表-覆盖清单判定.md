# P1-S6-R7 D 回执附表：覆盖清单逐条判定（TS-017 第 2 步）

原 218 条；留 57 条、删 161 条。判定脚本 `Spike/P1S6R7/ts017_rebuild.py`。

| 键 | 官方 | ours | 判定 | 依据／原因 |
|---|---|---|---|---|
| `Accounts Receivable` | 应收账款 | 应收账款 | 留 | S3 术语标准 §2.3（保留） |
| `Actual` | 实际 | 实际值 | 留 | DEC-026（R4 TS-014 整句修复） |
| `Actual End Date (via Timesheet)` | 实际结束日期（通过工时表） | 实际结束日期（通过工时单） | 留 | DEC-016（Timesheet 全族） |
| `Actual Start Date (via Timesheet)` | 实际开始日期（通过工时表） | 实际开始日期（通过工时单） | 留 | DEC-016（Timesheet 全族） |
| `Actual Time in Hours (via Timesheet)` | 实际工时（通过工时表） | 实际工时（通过工时单） | 留 | DEC-016（Timesheet 全族） |
| `Add Row` | 添加行 | 添加行 | 留 | DEC-001（需求 §4.2.2 必改条目） |
| `Add Timesheets` | 添加工时表 | 添加工时单 | 留 | DEC-016（Timesheet 全族） |
| `Agents` | 代理列表 | 智能体 | 留 | DEC-001（需求 §4.2.2 必改条目） |
| `Bot` | 聊天机器人 | 机器人 | 留 | DEC-001（需求 §4.2.2 必改条目） |
| `Cash Flow` | 现金流量表 | 现金流量表 | 留 | DEC-015（原生报表保留官方） |
| `Closed Date` | 截止日期 | 实际成交日期 | 留 | DEC-021 |
| `Create Chart Of Accounts Based On` | 科目表模板 | 科目表建立方式 | 留 | DEC-021 |
| `Create Quotation` | 创建报价 | 创建报价单 | 留 | DEC-001（需求 §4.2.2 必改条目；单据用「单」，DEC-016） |
| `Create Timesheet` | 创建工时表 | 创建工时单 | 留 | DEC-016（Timesheet 全族） |
| `Daily Timesheet Summary` | 每日工时表汇总 | 每日工时单汇总 | 留 | DEC-016（Timesheet 全族） |
| `days` | 天 | 天 | 留 | DEC-026（R4 TS-014 整句修复） |
| `Deals` | 商机 | 商机 | 留 | DEC-026（R4 TS-014 整句修复） |
| `Debtors` | 应收账款 | 应收账款 | 留 | S3 术语标准 §2.3（科目名，保留） |
| `Dr` | 博士 | 借方 | 留 | DEC-003／022（S3 DEC-081） |
| `Employee Hours Utilization Based On Timesheet` | 基于工时表的员工工时利用率 | 基于工时单的员工工时利用率 | 留 | DEC-016（Timesheet 全族） |
| `Enabling the check box will fetch timesheet on select of a Project in Sales Invoice` | 勾选此复选框将在销售发票中选择项目时获取工时表 | 勾选此复选框将在销售发票中选择项目时获取工时单 | 留 | DEC-016（Timesheet 全族） |
| `Fetch Timesheet in Sales Invoice` | 允许在销售发票获取工时表 | 允许在销售发票获取工时单 | 留 | DEC-016（Timesheet 全族） |
| `Formula` | 公式 | 计算方式 | 留 | 本 app 自有源词（cn_tax `Cash Flow Code.formula`；S5 装序检查探针 `install.PROBE_SOURCE`） |
| `Get Items for Purchase / Transfer` | 获取需采购/调拨的物料 | 获取采购或调拨物料 | 留 | DEC-026（R4 TS-014 整句修复） |
| `Get Items for Purchase Only` | 仅获取需采购的物料 | 仅获取采购物料 | 留 | DEC-026（R4 TS-014 整句修复） |
| `Get Sub Assembly Items` | 计算子装配件需求 | 获取半成品物料 | 留 | DEC-026（R4 TS-014 整句修复） |
| `Global Defaults` | 全局默认值 | 全局默认值 | 留 | DEC-026（R4 TS-014 整句修复） |
| `Hide timesheets` | 隐藏工时表 | 隐藏工时单 | 留 | DEC-016（Timesheet 全族） |
| `Include Timesheets in Draft Status` | 包含草稿状态工时表 | 包含草稿状态工时单 | 留 | DEC-016（Timesheet 全族） |
| `Leads` | 线索 | 线索 | 留 | DEC-026（R4 TS-014 整句修复） |
| `Max working hours against Timesheet` | 工时表最大工时限制 | 工时单最大工时限制 | 留 | DEC-016（Timesheet 全族） |
| `Opening & Closing` | POS机交接班 | 期初与期末 | 留 | DEC-001（需求 §4.2.2 必改条目，原误译） |
| `Payment Entry Reference` | 付款参考 | 核销明细 | 留 | DEC-014 |
| `Payment References` | 付款参考 | 核销明细 | 留 | DEC-014 |
| `Receivable` | 应收账款 | 应收账款 | 留 | S3 术语标准 §2.3（现值同官方，演示撞名在 TS-019 按 §2.3 判） |
| `Row #{0}: Timesheet amount will overwrite the Earning component amount for the Salary Component {1}` | 行号#{0}：工时表金额将覆盖薪资组件{1}的收入项金额 | 行号#{0}：工时单金额将覆盖薪资组件{1}的收入项金额 | 留 | DEC-016（Timesheet 全族） |
| `Row {0}: Project must be same as the one set in the Timesheet: {1}.` | 行号{0}：项目必须与工时表{1}中设置的一致 | 行号{0}：项目必须与工时单{1}中设置的一致 | 留 | DEC-016（Timesheet 全族） |
| `Salary Component for timesheet based payroll.` | 基于工时表的薪资组件 | 基于工时单的薪资组件 | 留 | DEC-016（Timesheet 全族） |
| `Salary Slip Based on Timesheet` | 基于工时表的工资条 | 基于工时单的工资条 | 留 | DEC-016（Timesheet 全族） |
| `Salary Slip of employee {0} already created for time sheet {1}` | 员工{0}的工资条已关联工时表{1} | 员工{0}的工资条已关联工时单{1} | 留 | DEC-016（Timesheet 全族） |
| `Salary Slip Timesheet` | 工资条工时表 | 工资条工时单 | 留 | DEC-016（Timesheet 全族） |
| `Sales Invoice Timesheet` | 销售发票工时表 | 销售发票工时单 | 留 | DEC-016（Timesheet 全族） |
| `Send` | 发送 | 发送 | 留 | DEC-026（R4 TS-014 整句修复） |
| `Setup` | 设置 | 基础设置 | 留 | DEC-019 |
| `This is based on the Time Sheets created against this project` | 基于项目工时表 | 基于项目工时单 | 留 | DEC-016（Timesheet 全族） |
| `Time Sheet` | 工时表 | 工时单 | 留 | DEC-016（Timesheet 全族） |
| `Time Sheet List` | 工时表清单 | 工时单清单 | 留 | DEC-016（Timesheet 全族） |
| `Time Sheets` | 工时表 | 工时单 | 留 | DEC-016（Timesheet 全族） |
| `Timesheet` | 工时表 | 工时单 | 留 | DEC-016（Timesheet 全族） |
| `Timesheet Detail` | 工时表明细 | 工时单明细 | 留 | DEC-016（Timesheet 全族） |
| `Timesheet for tasks.` | 任务工时表。 | 任务工时单。 | 留 | DEC-016（Timesheet 全族） |
| `Timesheets` | 工时表 | 工时单 | 留 | DEC-016（Timesheet 全族） |
| `Total Billable Amount (via Timesheet)` | 总可开票金额（工时表） | 总可开票金额（工时单） | 留 | DEC-016（Timesheet 全族） |
| `Total Costing Amount (via Timesheet)` | 总成本（工时表） | 总成本（工时单） | 留 | DEC-016（Timesheet 全族） |
| `Update Rate and Availability` | 更新物料成本价和可用数量 | 更新单价与可用量 | 留 | DEC-026（R4 TS-014 整句修复） |
| `Value` | 值 | 值 | 留 | DEC-026（R4 TS-014 整句修复） |
| `Yearly Amount` | 年度金额 | 年内累计金额 | 留 | 本 app 自有源词（cn_tax `Cash Flow Subtotal.yearly_amount`；避开法定列头「本年累计金额」，S4 LG-134） |
| `!=` | != | 中文：!= | 删 | ours 命中守卫：find_placeholder |
| `#{0}` | #{0} | 中文：#{0} | 删 | ours 命中守卫：find_placeholder |
| `0-30` | 0-30 | ???0-30 | 删 | ours 命中守卫：find_placeholder |
| `0.25` | 0.25 | 中文：0.25 | 删 | ours 命中守卫：find_placeholder |
| `0.5` | 0.5 | 中文：0.5 | 删 | ours 命中守卫：find_placeholder |
| `00:00` | 00:00 | 中文：00:00 | 删 | ours 命中守卫：find_placeholder |
| `01:00` | 01:00 | 中文：01:00 | 删 | ours 命中守卫：find_placeholder |
| `02:00` | 02:00 | 中文：02:00 | 删 | ours 命中守卫：find_placeholder |
| `03:00` | 03:00 | 中文：03:00 | 删 | ours 命中守卫：find_placeholder |
| `04:00` | 04:00 | 中文：04:00 | 删 | ours 命中守卫：find_placeholder |
| `05:00` | 05:00 | 中文：05:00 | 删 | ours 命中守卫：find_placeholder |
| `06:00` | 06:00 | 中文：06:00 | 删 | ours 命中守卫：find_placeholder |
| `07:00` | 07:00 | 中文：07:00 | 删 | ours 命中守卫：find_placeholder |
| `08:00` | 08:00 | 中文：08:00 | 删 | ours 命中守卫：find_placeholder |
| `09:00` | 09:00 | 中文：09:00 | 删 | ours 命中守卫：find_placeholder |
| `1-10` | 1-10 | ???1-10 | 删 | ours 命中守卫：find_placeholder |
| `1.0` | 1.0 | 中文：1.0 | 删 | ours 命中守卫：find_placeholder |
| `1000+` | 1000+ | ???1000+ | 删 | ours 命中守卫：find_placeholder |
| `10:00` | 10:00 | 中文：10:00 | 删 | ours 命中守卫：find_placeholder |
| `11-50` | 11-50 | ???11-50 | 删 | ours 命中守卫：find_placeholder |
| `11:00` | 11:00 | 中文：11:00 | 删 | ours 命中守卫：find_placeholder |
| `12:00` | 12:00 | 中文：12:00 | 删 | ours 命中守卫：find_placeholder |
| `13:00` | 13:00 | 中文：13:00 | 删 | ours 命中守卫：find_placeholder |
| `14:00` | 14:00 | 中文：14:00 | 删 | ours 命中守卫：find_placeholder |
| `15:00` | 15:00 | 中文：15:00 | 删 | ours 命中守卫：find_placeholder |
| `16:00` | 16:00 | 中文：16:00 | 删 | ours 命中守卫：find_placeholder |
| `17:00` | 17:00 | 中文：17:00 | 删 | ours 命中守卫：find_placeholder |
| `18:00` | 18:00 | 中文：18:00 | 删 | ours 命中守卫：find_placeholder |
| `19:00` | 19:00 | 中文：19:00 | 删 | ours 命中守卫：find_placeholder |
| `1{0}` | 1{0} | ???1{0} | 删 | ours 命中守卫：find_placeholder |
| `201-500` | 201-500 | ???201-500 | 删 | ours 命中守卫：find_placeholder |
| `20:00` | 20:00 | 中文：20:00 | 删 | ours 命中守卫：find_placeholder |
| `21:00` | 21:00 | 21:00 | 删 | 过守卫但指不出决策 |
| `22:00` | 22:00 | 中文：22:00 | 删 | ours 命中守卫：find_placeholder |
| `23:00` | 23:00 | 中文：23:00 | 删 | ours 命中守卫：find_placeholder |
| `30-60` | 30-60 | ???30-60 | 删 | ours 命中守卫：find_placeholder |
| `501-1000` | 501-1000 | ???501-1000 | 删 | ours 命中守卫：find_placeholder |
| `51-200` | 51-200 | ???51-200 | 删 | ours 命中守卫：find_placeholder |
| `60-90` | 60-90 | ???60-90 | 删 | ours 命中守卫：find_placeholder |
| `<` | < | 中文：< | 删 | ours 命中守卫：find_placeholder |
| `<0` | <0 | ???<0 | 删 | ours 命中守卫：find_placeholder |
| `<div class="text-muted text-center">{0}</div>` | <div class="text-muted text-center">{0}</div> | ???<div class="text-muted text-center">{0}</div> | 删 | ours 命中守卫：find_placeholder |
| `<div id="stock-levels-placeholder"></div>` | <div id="stock-levels-placeholder"></div> | ???<div id="stock-levels-placeholder"></div> | 删 | ours 命中守卫：find_placeholder |
| `<div id=\"item-prices-container\"></div>` | <div id=\"item-prices-container\"></div> | ???<div id=\"item-prices-container\"></div> | 删 | ours 命中守卫：find_placeholder |
| `<hr>` | <hr> | ????<hr> | 删 | ours 命中守卫：find_placeholder |
| `<li>{}</li>` | <li>{}</li> | 中文：<li>{}</li> | 删 | ours 命中守卫：find_placeholder |
| `<table class='table table-bordered'><tr><th>{0}</th><th>{1}</th></tr>` | <table class='table table-bordered'><tr><th>{0}</th><th>{1}</th></tr> | ????<table class='table table-bordered'><tr><th>{0}</th><th>{1}</th></tr> | 删 | ours 命中守卫：find_placeholder |
| `=` | = | 中文：= | 删 | ours 命中守卫：find_placeholder |
| `>` | > | 中文：> | 删 | ours 命中守卫：find_placeholder |
| `>=` | >= | 中文：>= | 删 | ours 命中守卫：find_placeholder |
| `A - B` | A - B | ???A - B | 删 | ours 命中守卫：find_placeholder |
| `A - C` | A - C | ???A - C | 删 | ours 命中守卫：find_placeholder |
| `A-` | A- | ???A- | 删 | ours 命中守卫：find_placeholder |
| `A0` | A0 | 中文：A0 | 删 | ours 命中守卫：find_placeholder；find_word_by_word |
| `A1` | A1 | 中文：A1 | 删 | ours 命中守卫：find_placeholder；find_word_by_word |
| `A2` | A2 | 中文：A2 | 删 | ours 命中守卫：find_placeholder；find_word_by_word |
| `A3` | A3 | 中文：A3 | 删 | ours 命中守卫：find_placeholder；find_word_by_word |
| `A4` | A4 | 中文：A4 | 删 | ours 命中守卫：find_placeholder；find_word_by_word |
| `A5` | A5 | 中文：A5 | 删 | ours 命中守卫：find_placeholder；find_word_by_word |
| `A6` | A6 | 中文：A6 | 删 | ours 命中守卫：find_placeholder；find_word_by_word |
| `A7` | A7 | 中文：A7 | 删 | ours 命中守卫：find_placeholder；find_word_by_word |
| `A8` | A8 | 中文：A8 | 删 | ours 命中守卫：find_placeholder；find_word_by_word |
| `A9` | A9 | 中文：A9 | 删 | ours 命中守卫：find_placeholder；find_word_by_word |
| `AB-` | AB- | ???AB- | 删 | ours 命中守卫：find_placeholder |
| `ACC-PINV-.YYYY.-` | ACC-PINV-.YYYY.- | ???ACC-PINV-.YYYY.- | 删 | ours 命中守卫：find_placeholder |
| `Active Directory` | Active Directory | 启用 Directory | 删 | ours 命中守卫：find_mixed |
| `API` | API | 中文：API | 删 | ours 命中守卫：find_placeholder |
| `Are you sure you want to log out?` | 您确定要退出登录吗？ | 是 您 sure 您 want 至 日志 out? | 删 | ours 命中守卫：find_word_by_word；find_mixed |
| `B-` | B- | ???B- | 删 | ours 命中守卫：find_placeholder |
| `B0` | B0 | 中文：B0 | 删 | ours 命中守卫：find_placeholder |
| `B1` | B1 | 中文：B1 | 删 | ours 命中守卫：find_placeholder |
| `B10` | B10 | 中文：B10 | 删 | ours 命中守卫：find_placeholder |
| `B2` | B2 | 中文：B2 | 删 | ours 命中守卫：find_placeholder |
| `B3` | B3 | 中文：B3 | 删 | ours 命中守卫：find_placeholder |
| `B4` | B4 | 中文：B4 | 删 | ours 命中守卫：find_placeholder |
| `B5` | B5 | 中文：B5 | 删 | ours 命中守卫：find_placeholder |
| `B6` | B6 | 中文：B6 | 删 | ours 命中守卫：find_placeholder |
| `B7` | B7 | 中文：B7 | 删 | ours 命中守卫：find_placeholder |
| `B8` | B8 | 中文：B8 | 删 | ours 命中守卫：find_placeholder |
| `B9` | B9 | 中文：B9 | 删 | ours 命中守卫：find_placeholder |
| `B:Number system` | B | B:编号 系统 | 删 | ours 命中守卫：find_word_by_word |
| `BOM Explorer` | BOM Explorer | 物料清單瀏覽器 | 删 | ours 命中守卫：find_traditional |
| `C5E` | C5E | 中文：C5E | 删 | ours 命中守卫：find_placeholder |
| `CMD` | CMD | 中文：CMD | 删 | ours 命中守卫：find_placeholder |
| `Comm10E` | Comm10E | 中文：Comm10E | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `CSS` | CSS | ???CSS | 删 | ours 命中守卫：find_placeholder |
| `CSV` | CSV | ???CSV | 删 | ours 命中守卫：find_placeholder |
| `D - E` | D - E | ???D - E | 删 | ours 命中守卫：find_placeholder |
| `Defense` | Defense | 國防 | 删 | ours 命中守卫：find_traditional |
| `DFS` | DFS | ???DFS | 删 | ours 命中守卫：find_placeholder |
| `EAN` | EAN | ???EAN | 删 | ours 命中守卫：find_placeholder |
| `EAN-13` | EAN-13 | ???EAN-13 | 删 | ours 命中守卫：find_placeholder |
| `EAN-8` | EAN-8 | ???EAN-8 | 删 | ours 命中守卫：find_placeholder |
| `Edit Filter` | 编辑筛选器 | 编辑 筛选 | 删 | ours 命中守卫：find_word_by_word |
| `ERPNext` | ERPNext | ???ERPNext | 删 | ours 命中守卫：find_placeholder |
| `Excel` | Excel | ???Excel | 删 | ours 命中守卫：find_placeholder |
| `Exotel` | Exotel | 中文：Exotel | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `Facebook` | Facebook | ???Facebook | 删 | ours 命中守卫：find_placeholder |
| `fairlogin` | fairlogin | 中文：fairlogin | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `Filename` | 文件名 | 中文：Filename | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `Frappe` | Frappe | 中文：Frappe | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `Frappe CRM` | Frappe CRM | Frappe CRM | 删 | 过守卫但指不出决策 |
| `G - D` | G - D | ???G - D | 删 | ours 命中守卫：find_placeholder |
| `GitHub` | GitHub | ???GitHub | 删 | ours 命中守卫：find_placeholder |
| `GMail` | GMail | 中文：GMail | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `H - F` | H - F | ???H - F | 删 | ours 命中守卫：find_placeholder |
| `HTML` | HTML | ???HTML | 删 | ours 命中守卫：find_placeholder |
| `I - J` | I - J | ???I - J | 删 | ours 命中守卫：find_placeholder |
| `I - K` | I - K | ???I - K | 删 | ours 命中守卫：find_placeholder |
| `IBAN` | IBAN | ???IBAN | 删 | ours 命中守卫：find_placeholder |
| `InnoDB` | InnoDB | 中文：InnoDB | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `IRS 1099` | IRS 1099 | ???IRS 1099 | 删 | ours 命中守卫：find_placeholder |
| `ISBN-10` | ISBN-10 | ???ISBN-10 | 删 | ours 命中守卫：find_placeholder |
| `ISBN-13` | ISBN-13 | ???ISBN-13 | 删 | ours 命中守卫：find_placeholder |
| `jane@example.com` | jane@example.com | 中文：jane@example.com | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `Javascript` | Javascript | 中文：Javascript | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `Jinja` | Jinja | 中文：Jinja | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `john@doe.com` | john@doe.com | 中文：john@doe.com | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `johndoe@mail.com` | johndoe@mail.com | 中文：johndoe@mail.com | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `JS` | JS | 中文：JS | 删 | ours 命中守卫：find_placeholder |
| `JSON` | JSON | ???JSON | 删 | ours 命中守卫：find_placeholder |
| `Lft` | Lft | 左值 | 删 | 过守卫但指不出决策 |
| `Markdown` | Markdown | 中文：Markdown | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `Mx` | Mx | 中文：Mx | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `O-` | O- | ???O- | 删 | ours 命中守卫：find_placeholder |
| `Office 365` | Office 365 | 中文：Office 365 | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `old_parent` | old_parent | 中文：old_parent | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `OpenLDAP` | OpenLDAP | 中文：OpenLDAP | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `Outlook.com` | Outlook.com | Outlook.com | 删 | 过守卫但指不出决策 |
| `PDF` | PDF | 中文：PDF | 删 | ours 命中守卫：find_placeholder |
| `POS` | POS | ???POS | 删 | ours 命中守卫：find_placeholder |
| `Python` | Python | 中文：Python | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `Sazhen` | Sazhen | 俄丈 | 删 | 过守卫但指不出决策 |
| `Sendgrid` | Sendgrid | Sendgrid | 删 | 过守卫但指不出决策 |
| `Skype` | Skype | 中文：Skype | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `Skype ID` | Skype ID | Skype 帳號 | 删 | ours 命中守卫：find_traditional；find_mixed |
| `Slug` | Slug | 中文：Slug | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `SparkPost` | SparkPost | 中文：SparkPost | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `SQL` | SQL | 中文：SQL | 删 | ours 命中守卫：find_placeholder |
| `T:Number system` | T | T:编号 系统 | 删 | ours 命中守卫：find_word_by_word |
| `Test_Folder` | Test_Folder | 中文：Test_Folder | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `Twilio` | Twilio | 中文：Twilio | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `TwiML SID` | TwiML SID | 中文：TwiML SID | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `UID` | UID | 中文：UID | 删 | ours 命中守卫：find_placeholder |
| `UIDNEXT` | UIDNEXT | 中文：UIDNEXT | 删 | ours 命中守卫：find_placeholder |
| `UIDVALIDITY` | UIDVALIDITY | 中文：UIDVALIDITY | 删 | ours 命中守卫：find_placeholder |
| `UPC-A` | UPC-A | ???UPC-A | 删 | ours 命中守卫：find_placeholder |
| `Verdana` | Verdana | Verdana | 删 | 过守卫但指不出决策 |
| `Webhook URL` | Webhook URL | Webhook 网址 | 删 | ours 命中守卫：find_mixed |
| `Websocket` | Websocket | 中文：Websocket | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `WhatsApp` | WhatsApp | ???WhatsApp | 删 | ours 命中守卫：find_placeholder |
| `XLSX` | XLSX | 中文：XLSX | 删 | ours 命中守卫：find_placeholder |
| `Yandex.Mail` | Yandex.Mail | 中文：Yandex.Mail | 删 | ours 命中守卫：find_placeholder；find_mixed |
| `{0}` | {0} | 中文：{0} | 删 | ours 命中守卫：find_placeholder |
| `{0} ${type}` | {0} ${type} | ????{0} ${type} | 删 | ours 命中守卫：find_placeholder |
| `{0} & {1}` | {0} & {1} | 中文：{0} & {1} | 删 | ours 命中守卫：find_placeholder |
| `{0} = {1}` | {0} = {1} | 中文：{0} = {1} | 删 | ours 命中守卫：find_placeholder |
| `{0} {1} {2}?` | {0} {1} {2}? | 中文：{0} {1} {2}? | 删 | ours 命中守卫：find_placeholder |
| `{0}%` | {0}% | ???{0}% | 删 | ours 命中守卫：find_placeholder |
| `{0}.:Money in words` | {0}. | {0}.:Money 中 words | 删 | ours 命中守卫：find_mixed |
| `{}` | {} | ???{} | 删 | ours 命中守卫：find_placeholder |
