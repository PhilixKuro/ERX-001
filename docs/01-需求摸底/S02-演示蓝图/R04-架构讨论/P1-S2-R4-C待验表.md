# P1-S2-R4-C待验表

**发起步骤**：devBlueprint C 步（架构讨论）第 1 步③
**日期**：2026-09-24
**填表规范**：`docs/流程体系/交接契约.md`｜**判定标准**：`docs/流程体系/workflows/devBlueprint/SA-probe-devBlueprint-spike.md`

> **编号承接**：本 Stage 的 A 步已用到 V-01…V-13（含 V-09a/b/c、V-11a/b），故本表自 **V-14** 起，不复用旧号。
> **环境**：容器 `erx001-frappe-1` 在跑，站点 `erx.localhost`，已恢复 `20260922_145623` 完整闭环数据（1 公司 `华东弹簧` / 95 科目 / 2 Item / 1 BOM / 2 销售订单）。

| 编号 | 待验命题 | 阻塞否 | 判定 | 实际观察 | 探针代码 |
|------|---------|--------|------|---------|---------|
| V-14 | `get_region()` 在本机站点对公司 `华东弹簧` 返回的字符串是否**逐字**等于 `China`（大小写、有无空格、是否中文名皆须核实） | **阻塞** | go | **逐字等于 `China`。** `get_region("华东弹簧")` → `'China'`：`repr()` 形态 `'China'`，`len=5`，codepoints `0x43 0x68 0x69 0x6e 0x61`，utf8 字节 `4368696e61`，`isascii()=True`，`== "China"` 为 `True`——无前后空格、非同形异码、非中文名。无参调用 `get_region()` 亦返回 `'China'`（经 `frappe.local.flags.company` / 全局默认公司路径）。<br>**各公司 country 原值**：站内仅 1 家公司 `华东弹簧`，`country='China'`，`default_currency='CNY'`。<br>**全局侧**：`frappe.db.get_default("company")='华东弹簧'`，`get_default("country")=null`，System Settings `country='China'`。<br>**Country 记录**：`code='cn'` 的记录 name 仅 `China` 一条。`Company.country` 字段为 `Link`→`Country`，存的是 docname，故即便 System Settings `language='zh'`，该值仍为 ASCII `China`，中文只出现在翻译层。<br>**当前已注册的 `regional_overrides` 键**：`France` / `United Arab Emirates` / `Saudi Arabia` / `Italy` 四个；`"China" in frappe.get_hooks("regional_overrides", {})` → `False`（`installed_apps` 仅 `frappe`,`erpnext`，自有 app 尚未存在）。 | `Spike/V14-get-region-china.py` |
| V-15 | 改 `standard=1` 的导航记录（`Workspace Sidebar` / `Workspace Sidebar Item` / `Desktop Icon`）后跑 `bench migrate`，改动是否被覆盖回原值 | 不阻塞 | go | **三张表均不被覆盖**。各改一条非命名字段后跑 `bench migrate`：`Workspace Sidebar.Stock.header_icon` `stock`→`bug` 后仍为 `bug`；`Workspace Sidebar Item`（`Stock` 第 3 行）`label` `Stock Entry`→`Stock Entry-V15TEST` 后仍带后缀；`Desktop Icon.Stock.icon` `stock`→`bug` 后仍为 `bug`。三条的 `db_modified` 前后一字未变、子行名仍 `d25tkm7tnm`，即导入整条被**跳过**而非写回同值。**覆盖判据是比对 `modified` 时间戳，非 hash**：`import_file.py:130` 的 `stored_hash` 仅在 `doctype=="DocType"` 时读取，故这三张表只走 `:141` `is_db_timestamp_latest`（`json.modified <= db.modified` 则 `continue`）；`save()` 把 `db.modified` 刷成 `now()`，必然较新，故跳过。**失效边界（已实测）**：把 json 的 `modified` 调到未来（模拟上游升级换文件）再跑 migrate，三张表**全部被打回 json 原值**，且子表整表删后重插（行名 `d25tkm7tnm`→`9h1c109pd0`）。**另更正命题前提**：`Desktop Icon` 在 migrate 路径上**不是生成的**——`create_desktop_icons_from_workspace()` 全仓仅 `install.py:203` 调用（装站/装 app 时），`migrate.py` 无调用；migrate 走 `sync.py:120` 的 `app_level_folders = ["desktop_icon","workspace_sidebar","sidebar_item_group"]`，与 `Workspace Sidebar` 同一条 json 导入路径、同一套判据。`Workspace Sidebar Item` 无自己的 `standard` 字段（`istable:1`），随父 sidebar json 一起进出。**前置陷阱**：本站点 `developer_mode=1`，`doc.save()` 会经 `workspace_sidebar.py:53` / `desktop_icon.py:71` 把改动**导出写回 app 的 json 源**，致 DB 与 json 同时变化；若不先把 json 改回原值，migrate 看到的"未被覆盖"是假阳性。本探针已核 json 与 HEAD 逐字节一致后才判定 | Spike/V15-standard-record-migrate.md、Spike/V15_standard_record_migrate.py、Spike/V15-verify-clean.py |
| V-16 | desk 自带前端 js 的行为能否在自有 app 侧覆盖而不改上游源码（判据：`app_include_js` 注入的脚本能否改变已定义的 desk 类/方法的行为，且在 `bench build` 后仍生效） | 不阻塞 | go | **加载顺序：自有 app 的脚本在 desk 自身 bundle 之后**——desk 的 9 个 bundle 本身就是 frappe 这个 app 的 `app_include_js` hook 值（`apps/frappe/frappe/hooks.py:25-34`），自有 app 与它们进同一个列表，`get_all_apps()` 强制把 frappe 提到第 0 位，故顺序恒为 frappe→erpnext→自有 app。desk 页实测 script 标签：1-8 frappe 各 bundle（3 号为 `desk.bundle`）、9 erpnext、**10-11 自有 app**；全部同步 `<script src>`，无 `defer`/`async`/`module`（实测计数 0）。①追加：两条注入路径（`erx_spike.bundle.js` 与裸 `/assets/erx_spike/js/*.js`）均被执行。②覆盖：因在后，desk 类在自有脚本 parse 时已定义（`readyState=loading` 时 `frappe.ui.SidebarHeader`/`ListView`/`ui.form.Form`/`QueryReport`/`KanbanView`/`utils.desktop_icon` 全为 function），**直接改原型即可，无需等待**；四手法真浏览器实测被调用次数：换原型方法 `SidebarHeader.prototype.get_icon_for_menu_item` 17 次、包命名空间函数 `frappe.utils.desktop_icon` 2 次、包渲染方法 `add_app_item` 26 次（首调在注入后 +54~61ms）、跨 SPA 路由 `ListView.prototype.setup_defaults` 1 次且三次路由变更后仍在；对照组（CDP `addScriptToEvaluateOnNewDocument` 预置禁用标志）patch 全空、DOM 一致。**但 `frappe.app`（实例）与 `frappe.ready` 在 parse 时均为 `undefined`**（desk 页无 `frappe.ready`，回调实测从未触发），改实例须改用 `DOMContentLoaded`（+8~12ms）或 `frappe.router.on("change")`（+1ms 可挂）；懒加载的 `frappe.form_builder`/`ui.FormBuilder`/`PrintPreview` parse 时亦为 `undefined`，须待其被 `frappe.require` 拉入（实测强制跳 Kanban 路由后 `KanbanView` 才由 undefined 变 function）。③构建：`bench build` 退出码 0，assets.json 44→45（新增 `erx_spike.bundle.js`，零删除，其余 **44 条哈希全变**，含 `desk.bundle` LHZJYI3U→OSOIKW5M）；build 后四手法 calls 与 build 前完全一致（17/2/26/1）。**前提：bundle 路径 build 前 HTTP 404**（assets.json 无条目，`bundled_asset()` 原样返回 `/erx_spike.bundle.js`），build 后 200；裸路径 build 前后均 200。环境：frappe 16.34.0@c1f1e8e / erpnext 16.35.0@12cd563 / Chrome 153 headless 经 CDP。 | Spike/V16-desk-js-override.md；Spike/V16-desk-js-override.probe.js；Spike/V16-setup-test-app.sh；Spike/V16-cdp-run.js；Spike/V16-cdp-inspect.js；Spike/V16-cdp-trace-undefined.js；Spike/V16-cleanup-check.py；Spike/V16-cleanup-check.sql；Spike/V16-out/*.json |
| V-17 | 自有 app 的 `translations/` 同级目录 `workspace_sidebar/*.json`（与 erpnext 同名的文件）能否覆盖 erpnext 同名导航记录，即 `bench migrate` 后生效的是自有 app 那份 | 不阻塞 | 待验 | — | — |
| V-18 | erpnext **原生**建公司流程（不挂 Company 三钩子、不置 `ignore_chart_of_accounts`）能否用 zelin 的 `cn_smes_chart_of_accounts2024.json` 建出完整科目表；且随后 `setup_tax_template` 能否建出 13% 销项模板并指向正确科目 | **阻塞**（决策 5 的 B 案押在它上面） | no-go | **第一段 no-go：原生流程取不到那份 JSON，建公司当场抛错、公司被回滚。** 4 个 `override_whitelisted_methods` 本身注册无误（`frappe.override_whitelisted_method("...chart_of_accounts.get_chart")` → `'erx_v18...custom_account.get_chart'`），但 **`override_whitelisted_methods` 只在 4 个白名单派发点被查**（`frappe/handler.py:67`、`api/v2.py:36`、`desk/treeview.py:17`、`model/mapper.py:20,44`——全仓仅此 5 处调用 `frappe.override_whitelisted_method`），而 `Company.create_default_accounts()`（`company.py:420`）是 `from ...chart_of_accounts import create_charts` **直接 import**，`create_charts` 再调自己的模块级 `get_chart`，**整条路径不经派发点，覆盖永不生效**。实测同一进程内两个返回值分叉：`get_chart` 经覆盖→`['资产类','负债类','权益类','成本类','收入类','费用类']`，**原生直调→`None`**；`get_charts_for_country("China")` 经覆盖→`['Standard','Standard with Numbers','小企业会计准则(2024)']`，**原生→`['Standard','Standard with Numbers']`**（erpnext `verified/` 73 个 json 中 `cn*`／`China*` 文件数为 **0**）。<br>**确切报错**（`company.insert()`，`AttributeError`，`str(e)` 为 `'NoneType' object has no attribute 'get'`）：`document.py:513 insert` → `:1454 run_post_save_methods` → `:1260 run_method("on_update")` → **`erpnext/setup/doctype/company/company.py:348 on_update` → `sync_financial_report_templates(self.chart_of_accounts, self.existing_company)`** → **`erpnext/accounts/doctype/financial_report_template/financial_report_template.py:144` → `if coa.get("disable_default_financial_report_template", False):`**（`coa = get_chart(chart_of_accounts)` 得 `None`）。事后 `Company` 不存在、该公司 `Account` 0 条、站内 `Account` 仍 95、`Error Log` 仍 1 条（**不写日志、纯抛栈**）。<br>**该报错与运行方式无关，HTTP 亦同**：`POST /api/resource/Company` → **HTTP 500**，异常类型、`str`、以及 `company.py:348` / `financial_report_template.py:144` 两处行号**逐字相同**。反倒是白名单 HTTP 路由**正常返回** app 那份表（`get_charts_for_country` 含 `小企业会计准则(2024)`；`get_chart` 经 POST／百分号编码均得 6 个顶层键、`root_type` 全对）——即**桌面下拉能选出这张表，选了建公司就 500**。<br>**且报错并非唯一失败形态**：`:348` 崩在 `:349` `create_default_accounts()` 之前，故另单独实测 `create_charts(不存在的公司, '小企业会计准则(2024)', None)`——**不抛错、静默返回 `None`、新建 0 个 Account**（`create_charts` 首行 `chart = custom_chart or get_chart(...)` 后 `if chart:` 直接落空）。即**即便修掉 `:348` 那处崩，B 案得到的也是「公司建出来、科目表 0 条」的静默空表**。<br>**内容侧另验（探针脚手架强行喂进，非 B 案可用机制）**：把 `coa_mod.get_chart` 在进程内替成 app 那份后跑完全原生的 `Company.insert()`（`doc_events.Company` 为 `ABSENT`、`ignore_chart_of_accounts` 全程 `unset`），**原生 `create_charts` 吃得下这份 JSON**：`insert` 无异常，**`Account` 建出 267 条**（JSON 递归节点 **266**，号码无重复；逐对 `(account_number, account_name)` 比对 **`in_json_not_in_db` 为空集**，多出的 1 条见下）。**六个顶层 `root_type` 全对**：`1 资产类`=Asset、`2 负债类`=Liability、`3 权益类`=Equity、`4 成本类`=Asset、`500 收入类`=Income、`540 费用类`=Expense（`report_type` 依次 Balance Sheet×4 / Profit and Loss×2）；直方图 Asset 72 / Equity 15 / Expense 85 / Income 26 / Liability 69，`is_group` 1→41、0→226，NSM `lft>=rgt` 或空值 **0** 行、跨度 1..534、孤儿父引用 **0**、重名加后缀 **0**。**`2221001`…`2221020` 20 条全部建出（缺 0 条）**，但**须更正命题前提**：这 20 条在 JSON 里**本就不全在 `2221000` 下**——`2221001`–`2221010` 挂 `2221000 应交增值税`（10 条），`2221011`–`2221020` 是 `2221 应交税费` 的直接子级（10 条），`2221` 共 25 个子级。<br>**多出的那 1 条是原生流程自己塞的**：`VAT - V18B`，**`account_number` 为空**、`account_type=Tax`、`root_type=Liability`、父为 `2221000 - 应交增值税 - V18B`，创建时刻 `02:05:29.325149` 晚于科目表最后一条（`02:05:27.023517`）——来自 `Company.on_update:357` 的 `create_default_tax_template()` → `setup_taxes_and_charges(company,"China")` 读 erpnext 自带 `country_wise_tax.json` 的 `China: {"China Tax": {"account_name":"VAT","tax_rate":17.0}}`，经 `get_or_create_account` 新建；被 `China Tax - V18B` 的销项／进项模板按 **17%** 引用（`华东弹簧` 上同形：`VAT - HDS`，父 `关税与税项 - HDS`）。即**原生流程会往中式科目表里注入一个无编号的 17% VAT 科目**。<br>**另一处原生副作用（`go` 门槛外、但属同次观察）**：默认科目自动挑选**挑错**——`default_receivable_account` = **`2203 - 预收账款`（负债类、预收）**而非 `1122 应收账款`；`default_payable_account` = **`2211010 - 职工工资`（应付职工薪酬下的工资明细）**而非 `2202 应付账款`；`default_inventory_account` = `1421 消耗性生物资产`；`default_bank_account` = `1012 其他货币资金`（非 `1002 银行存款`）；`default_income_account` 与 `round_off_account` 为 `None`。成因：`company.py:425-434` 用 `frappe.db.get_value("Account", {...account_type...})` **不带 `order_by`**，取 DB 返回的第一条；照抄该无序调用复现得同样两个答案。JSON 里标 `Receivable` 的有 2 条（`1122`/`2203`）、标 `Payable` 的有 3 条（`1123`/`2202`/`2211010`），共 185 条带 `account_type`。另建出 5 个仓库、2 个成本中心、13 个部门，`Financial Report Template` 6 条（即第一段崩的那步在内容到位时正常跑完）。<br>**第二段 go（三问全答，发现八成立）**：不修 `tax_template.json` 那两处科目号（`P13专票含税` 写 `222105`、`P13专票未税` 写 `22210005`，表中正确号为 `2221005`，md5 `6dadb00e192ffea28f9e7f8b49700e8e` 与 zelin 原文件一致），直接跑 zelin 原样 `setup_tax_template`。**① 13% 两个模板都建出来了**：`P13专票含税 - V18B` 与 `P13专票未税 - V18B` 均存在。**② `account_head` 都指向正确科目 `2221005 - 销项税额 - V18B`**（`account_number='2221005'`、`account_name='销项税额'`、`root_type=Liability`、`account_type=Tax`、父 `2221000 - 应交增值税 - V18B`、`is_group=0`），含税那条 `rate=13.0, included_in_print_rate=1`、未税那条 `rate=13.0, included_in_print_rate=0`，两条 `description` 均为 `销项税额 @ 13`（该串由 `account_name` 拼出，正是按名命中的旁证）。**野科目未出现**：`account_number` 为 `222105` 与 `22210005` 的 Account 在跑前跑后**均为空结果集**，`account_name='销项税额'` 前后都只有 `2221005` 这一条，该段**新增 Account 数为 0**（267→267）。**③ `Error Log` 无该条目**：跑前跑后均 **1** 条，且那唯一一条是 2026-09-21 的 `Report execution failed for: Stock and Account Value Comparison`（与本次无关）；按 `error LIKE '%setup_tax_template%'` 与 `method LIKE '%setup_tax_template%'` 两种查法均为空——**那个裸 `except` 根本没触发**。附带：7 个 `Tax Category` 全建出，销项 5 条（13/3/13/3/0）＋进项 5 条（1/3/13/13/0）齐全，`含税` 后置 UPDATE 正确只把含税行置 1。**故既有记载的因果链不成立**：`get_or_create_account`（`taxes_setup.py:209-226`）的 `filters={company, root_type}` 为 AND、`or_filters={account_name, account_number}` 为 **OR**，科目号写错时按 `account_name='销项税额'` 仍命中，模板照常建出并指向正确科目。<br>**顺带核出 zelin 另一处缺陷**（探针误发未编码中文查询串时暴露）：其 `get_chart` 在**全不匹配**时 `return chart`，而 `chart` 是循环里最后读到的**原始文件文本（str）**——实测返回了 Taiwan 那份 json 的字符串；erpnext 原生同情形返回 `None`。<br>**环境**：frappe 16.34.0 / erpnext 16.35.0、`developer_mode=1`、测试 app 手搓（`bench new-app` 在本 bench 跑不通）、零 `bench build`。**基准数据 `华东弹簧` 全程未动**（95 科目 / 22 GL / 12 SLE / 1 BOM / 2 销售订单 / 2 Item / 6 仓库，跑前跑后一致）。 | Spike/V18-setup-test-app.sh；Spike/V18-app-custom_account.py；Spike/V18-app-utils.py；Spike/V18-seg1-native-company.py；Spike/V18-seg1b-content-digestible.py；Spike/V18-seg2-tax-template.py；Spike/V18-seg3-http-boundary.py；Spike/V18-seg3b-http-getchart.py；Spike/V18-seg4-forensics.py；Spike/V18-seg5-detail-checks.py；Spike/V18-seg6-cleanup-inventory.py；Spike/V18-seg7-cleanup.py；Spike/V18-seg8-final-verify.py；Spike/V18-seg9-create-charts-none.py；Spike/V18-out/*.json |
| V-19 | **A 案**（原样抄 zelin：4 个 `override_whitelisted_methods` **＋ Company 三钩子** `before_insert`／`on_update`／`after_insert`，含 `erpnext_china_create_charts`）能否建出完整的中式科目表；以及它相对原生路径多出／少掉哪些副作用 | **阻塞**（DEC-058 已定案 A，D 步要把它写进 ADR；若 no-go 则该 ADR 立错，须回 C 步改决策） | go | **第一段 go：A 案建出的科目表与那份 JSON 逐项一致。** `company.insert()` **无异常**（`insert_result` = `NO EXCEPTION`，无 traceback）。`Account` 建出 **266** 条（JSON 递归节点 **266**），**V-18 原生为 267 条，A 案为 266 条** —— 少的那 1 条正是 V-18 记载的无编号 `VAT`（第二段详述）。逐对 `(account_number, account_name)` 双向集合差（两侧统一转 `str` 后比，JSON 里号码是无引号整数、DB 列是 varchar，不归一化会得到假差集）：**`in_JSON_not_in_DB` 空集、`in_DB_not_in_JSON` 亦空集**；父子边集合（`(子号, 父号)`）两个方向亦**均为空集**（各 266 条边）；`is_group` 不一致 **0** 处、`account_type` 不一致 **0** 处。**六个顶层 `root_type` 全对**：`1 资产类`=Asset、`2 负债类`=Liability、`3 权益类`=Equity、`4 成本类`=Asset、`500 收入类`=Income、`540 费用类`=Expense，`report_type` 依次 Balance Sheet×4 / Profit and Loss×2。直方图 **Asset 72 / Equity 15 / Expense 85 / Income 26 / Liability 68**（**V-18 原生 Liability 为 69，A 案为 68**，差的就是那条 VAT；另五类逐个相同）；`is_group` 1→**41**、0→**225**（**V-18 原生 0→226，A 案 0→225**，同一成因）。**`2221001`…`2221020` 20 条齐全、缺 0 条**，父级分布与 V-18 更正过的前提**完全吻合**：`2221001`–`2221010` 挂 `2221000 - 应交增值税 - V19A`（10 条），`2221011`–`2221020` 挂 `2221 - 应交税费 - V19A`（10 条）。树完整性三项**均为 0**：NSM（`lft>=rgt` 或空值）本公司 **0** 行、站内 **0** 行；孤儿父引用 **0**；重名加后缀 **0**（`add_suffix_if_duplicate` 未触发，JSON 自身亦无重复 `(号, 名)` 对）。另核 `report_type` 与 `root_type` 不符 **0** 行、`root_type` 为空 **0** 行、跨公司父引用 **0**。`lft/rgt` 跨度 **1..532**（**V-18 原生 1..534，A 案 1..532**，少 1 个节点即少 2 个边界值）。`rebuild_tree` 未报错（`Tree Rebuild Error` 类 `Error Log` **0** 条）。 <br>**第二段（与 V-18 原生逐项对账，四问）**。**① 无编号 17% `VAT` 科目：少掉。** A 案下 `account_name='VAT'` 的 Account 为 **`None`**（**V-18 原生为 `VAT - V18B`，A 案为无**），且该公司 `account_number` 为空的 Account **0 条**；erpnext 自带 `country_wise_tax.json` 里 China 条目仍是 `{"China Tax": {"account_name": "VAT", "tax_rate": 17.0}}`，但 A 案下 `China Tax` 销项／进项模板**各 0 条**（未生成）。成因已测定：`company_before_insert` 置 `frappe.flags.country_change = False`，`insert` 结束时终值为 **`True`**（由 `company_on_update` 置回），但 `company.py:355` 的判断发生在 `on_update` 里 zelin 钩子之前，`create_default_tax_template()` 因此**整块未执行**。`install_country_fixtures`：**两条路径下都等于没跑** —— `erpnext/regional/` 下现有 10 个地区目录（australia / italy / south_africa / turkey / united_arab_emirates / united_states 等），**没有 `china`**，`scrub("China")`=`china`，实测 import 得 `ImportError -> silently passed: No module named 'erpnext.regional.china'`，被 `company.py:858` 的 `except ImportError: pass` 静默吞掉。`insert` 结束时 `ignore_chart_of_accounts` 终值 **`1`**（**未被任何代码复位**）。**② 默认科目：A 案把六个里的五个改对了（多出的修正）。** `set_company_default` 跑通，六值实测 `default_receivable_account` = **`1122 - 应收账款 - V19A`**（**V-18 原生为 `2203 预收账款`，A 案为 `1122 应收账款`** —— 原生挑错，A 案挑对）、`default_payable_account` = **`2202 - 应付账款 - V19A`**（**V-18 原生 `2211010 职工工资`，A 案 `2202 应付账款`**）、`default_inventory_account` = **`1403 - 原材料 - V19A`**（**V-18 原生 `1421 消耗性生物资产`**）、`default_bank_account` = **`1002 - 银行存款 - V19A`**（**V-18 原生 `1012 其他货币资金`**）、`default_income_account` = **`5001010 - 销售商品收入 - V19A`**（**V-18 原生 `None`**）、`round_off_account` = **`None`**（**与 V-18 原生相同，两边都是 `None`**）。另附带设上 `default_cash_account` = `1001 库存现金`、`default_expense_account` = `5401010 销售商品成本`、`stock_adjustment_account` = `400103 制造成本…`。修正是真实覆盖而非巧合：在同进程内照抄 `company.py:425-434` 那组**不带 `order_by`** 的查询复现，仍得原生那两个错答案（`Receivable`→`2203 - 预收账款 - V19A`、`Payable`→`2211010 - 职工工资 - V19A`、`Bank`→`1012 其他货币资金`、`Stock`→`1421 消耗性生物资产`），即 A 案是**先被 erpnext 挑错、再被 `set_company_default` 按 CSV 覆盖对**。`round_off_account` 落空的成因已定位：`default_accounts.csv` 共 **35** 行映射，其中 **14 行在本表里查不到对应科目**（`round_off_account` 那行写的是 `财务费用-圆整差异`，本科目表无此名；另有 `应付账款-供应商款`、`应付职工薪酬-职工工资` 等），故 `round_off_account` 仍为空 —— 这一条**A 案没修好**。**③ `Error Log`：跑前 1 条、跑后 1 条，裸 `except` 未触发。** 唯一那条是 2026-09-21 的 `Report execution failed for: Stock and Account Value Comparison`（与本次无关）。按 `error LIKE '%set company default%'`、`method LIKE '%company_on_update%'`、`create_charts2`、以及"今日新增"四种查法**均为空结果集**（**与 V-18 原生相同，两边都是 1 条**）。**④ 仓库／成本中心／部门／财报模板：四项全相同。** 仓库 **5**（Stores / Work In Progress / Finished Goods / Goods In Transit / All Warehouses，由 `on_update` 显式调 `create_default_warehouses()` 建出）、成本中心 **2**、部门 **13**（**三项 V-18 原生依次 5／2／13，A 案相同**）。`Financial Report Template` 站内 **6** 条（**V-18 原生 6，A 案 6，相同**）—— 与命题预判的"很可能一条都没有"不同：实测 `Financial Report Template` **没有 `company` 字段**（`frt_has_company_field` = `false`），那 6 条是 erpnext 安装时按 `module=Accounts` 装好的站级模板（Financial Ratios Analysis / Horizontal Balance Sheet (Columnar) / Horizontal Profit and Loss (Columnar) / Standard Balance Sheet (IFRS) / Standard Cash Flow Statement (IFRS) / Standard Profit and Loss (IFRS)），`sync_financial_report_templates` 被守卫跳过**不会减少站内条数**，故 A 案在这一项上**没有缺口**。**税侧与 V-18 无差异**：`Tax Category` **7** 条、销项模板 **5** 条、进项模板 **5** 条（**三项均与 V-18 原生相同**）；销项五条 `account_head` 全指 `2221005 - 销项税额 - V19A`（税率 13/3/13/3/0），进项五条全指 `2221001 - 进项税额 - V19A`（13/3/0/13/1）；另建 `Tax Rule` **11** 条。`Item Tax Template` **0** 条、`Mode of Payment Account` **0** 条。 <br>**第三段（边界，`go` 门槛所在，四项里三项通过、一项查出真实缺陷）**。**① 重复 `on_update`：干净。** 对已建成的公司再 `save()`，十二项计数 delta **全为 0**（`Account` 266→266、站内 361→361、仓库／成本中心／部门／销项／进项模板／`Tax Rule`／`Tax Category`／`Error Log`／财报模板全不变），**无异常**，六个默认科目**逐值未变**，重名后缀行 **0**、NSM 坏行 **0**。另在**全新进程**里对第二家公司重跑一次（排除同进程 flag 残留干扰），结论相同：delta 全 0、`defaults_changed` 为**空字典**。机制已测定：`company_after_insert` 置的 `doc.erpnext_china_in_insert` **不是 Company 的 docfield**（`resave_field_exists_in_meta` = `false`），只活在内存里，重新加载的 doc 上为 `None`，故 `set_company_default` 那段 `if` 不成立、不会二次跑；建账那段则被 `if not frappe.db.exists("Account", ...)` 守卫挡住。**② 第二家公司、同一张表：干净、互不串。** `V19A案二`／`V19B` 插入**无异常**，建出 **266** 条（与第一家同数），第一家仍 **266** 条不变。两家逐对 `(号, 名)` 差集 **空**（`c2_vs_c1_pair_diff` = `[]`），六个顶层 root 齐全且 `root_type` 全对。**跨公司父引用两个方向均为 0**；两家的 Account `name` **无一条不带自己的 abbr 后缀**（`c2_names_all_carry_abbr` = 0、`c1_names_all_carry_abbr` = 0，即"不带本公司 abbr 的行数"为零）；重名加后缀 **0** 条 —— 即 `add_suffix_if_duplicate` 在跨公司场景下**不需要也没有**加后缀，公司隔离靠的是 `name` 拼 abbr。第二家的六个默认科目与第一家同形（`1122`／`2202`／`5001010`／`1002`／`1403`／`None`）；`Tax Category` 仍 **7** 条（**复用而非重建**，未翻倍）；NSM 坏行 **0**、`Error Log` 仍 **1** 条。**③ 错误路径（`country='China'` 但 `chart_of_accounts='Standard'`）：两种结果，取决于是否同进程。** 在**全新进程**里（`ignore_chart_of_accounts` 起始 `unset`）**成功**：插入无异常，落地的是**原生 Standard 表** —— 5 个英文顶层（Application of Funds (Assets) / Equity / Expenses / Income / Source of Funds (Liabilities)），**中文顶层 0 个**，`Account` **95** 条；`VAT - V19C` **存在**（`account_type=Tax`、`tax_rate=17.0`、父 `Duties and Taxes - V19C`）；默认科目走原生一套（`Debtors`／`Creditors`／`Sales`／`Stock In Hand`，**`round_off_account` = `Round Off - V19C` 有值**）；仓库 5／成本中心 2／部门 13／销项 1／进项 1；**`account_category` 有值的科目 73 条**（原生 `create_charts` 会写这个字段）；**两条建账路径只跑了一条** —— zelin 的 `company_on_update` 被自己的 `not exists Account` 守卫正确跳过（`before_insert` 的 `if` 因 `Standard` 不在 `china_coa` 而不成立，`ignore_chart_of_accounts` 未被置上，故 erpnext 原生那条建账分支照常执行，zelin 那条随后发现已有 Account 即退出）；重名后缀 0、`Error Log` 前后均 1 条、财报模板 6 条不变。但在**同一进程内先建过中式公司之后**再建这家，**当场崩、公司被整体回滚**（`c3_company_exists` = `false`、`c3_accounts` = **0**）：`ignore_chart_of_accounts` 被前一家公司置为 `1` 后**无人复位**（本项目全仓无任何复位点），erpnext 原生建账分支被跳过，于是 zelin 的 `company_on_update` 那条 `not exists Account` 守卫成立、去建 `Standard` 表，而 `erpnext_china_create_charts` 的 `_import_accounts`（`custom_account.py:52`）在此崩出 **`AttributeError: 'str' object has no attribute 'get'`** —— 成因是 zelin 硬编码的跳过清单只有 7 个键、**漏了 `account_category`**（erpnext `get_chart_metadata_fields()`（`chart_of_accounts.py:281`）实为 8 个），而 `Standard` 表的节点带 `account_category`，该字符串值被当成子节点递归。**紧接着恢复处理自身又崩**：`custom_account.py:97` 写的是 `frappe.log_error(f"...{e}", title="Tree Rebuild Error")`，而 `frappe.log_error` 的真实签名是 `(title=None, message=None, ...)`，第一个位置参就是 `title`，故抛 **`TypeError: log_error() got multiple values for argument 'title'`** —— **连日志都没写下**（`Error Log` 前后均 1 条、今日新增 0 条）。同一误用在本次抄进测试 app 的那份里出现在 **6 处**（第 97、182、198、217、236、254 行），在 zelin 原文件 `Reference/zelin-tech-erpnext_china/erpnext_china/chart_of_accounts/custom_accounts/custom_account.py` 里对应 **6 处**（第 86、173、189、208、227、245 行）。**④ `existing_company` 分支：本次未验**（`UNTOUCHED_existing_company_path`，无任何公司带 `existing_company` 建过）。<br>**环境**：容器 `erx001-frappe-1`、站点 `erx.localhost`、frappe **16.34.0** / erpnext **16.35.0**、Python 3.14、MariaDB、`developer_mode=1`；测试 app `erx_v19` 手搓（`.pth` 进 `sys.path`），`installed_apps` 跑时为 `['frappe','erpnext','erx_v19']`，`hooks` 实测挂上三个 Company doc_events 与 22 个 `override_whitelisted_methods`（4 个自带 + 18 个上游）；**hrms 未装**。三个数据文件与 zelin 原文件 md5 一致，`utils.py` 字节相同。**基准公司 `华东弹簧` 全程未动**，跑前跑后逐项一致：95 科目 / 22 GL / 12 SLE / 1 BOM / 3 工单 / 2 销售订单 / 2 Item / 6 仓库 / 2 成本中心 / 13 部门，公司行十一个字段（含 `应收账款 1 - HDS`／`应付账款 1 - HDS`／`现金 - HDS`／`default_bank_account` 为 `None`／`存货 - HDS`／`销售 - HDS`／`小数精度尾差 - HDS`）与 `VAT - HDS`（父 `关税与税项 - HDS`）逐值不变。**清理已完成并核验**：三家测试公司（`V19A案一`／`V19A案二`／`V19A案三`）安全门全过（各 0 GL、0 SLE、`is_group=0`、无父子公司、非 `default_company`／`demo_company`）后删除，删后站内 `Account` 回到 **95**、公司只剩 `华东弹簧`（`lft/rgt` 1..2）、`Tax Category` 0 条、`Tax Rule` 0 条、按 `%V19%` 搜九类 doctype **全空**、NSM 坏行 0、`Error Log` 仍 1 条；测试 app 已 `uninstall-app`（`Module Def 'Erx V19'` 随之删除、`tabDocType` 无该模块行），`apps/erx_v19` 目录、`.pth`、`sites/assets/erx_v19` 均已删，`sites/apps.txt` 用 `od -c` 核为 `frappe\nerpnext` **14 字节无尾换行**，`assets.json` 无 `erx_v19` 残留，`bench serve` 已重启、`/api/method/ping` 返 **200** 且 `erx_v19` 不再可 import。 | Spike/V19-setup-test-app.sh；Spike/V19-app-custom_account.py；Spike/V19-app-doc_events.py；Spike/V19-app-utils.py；Spike/V19-seg0-baseline.py；Spike/V19-seg1-a-company.py；Spike/V19-seg1b-setdiff.py；Spike/V19-seg2-side-effects.py；Spike/V19-seg3-boundaries.py；Spike/V19-seg3b-errorpath-fresh.py；Spike/V19-seg3c-resave-fresh.py；Spike/V19-seg4-cleanup-inventory.py；Spike/V19-seg5-cleanup.py；Spike/V19-seg6-final-verify.py；Spike/V19-out/*.json |

## 命题背景与判据（供 spike 判断验到什么程度）

### V-14（阻塞）

**为什么阻塞**：CR-005／CR-006／CR-007（中国科目表、增值税、财务三表）的技术路线全部建在 `regional_overrides` hook 上，而 `erpnext/__init__.py:146` 是 `frappe.get_hooks("regional_overrides", {}).get(get_region())`——**region key 是字符串精确匹配**，`get_region()` 返回值与自有 app `hooks.py` 里写的键不逐字一致，整条覆盖路线静默失效（不报错，只是覆盖函数永不被调用）。

**已知事实**（本轮读码）：`get_region(company=None)` 在 `erpnext/__init__.py:120-132`——传了 company 或 `frappe.local.flags.company` 有值时返回 `frappe.get_cached_value("Company", company, "country")`；否则返回 `frappe.flags.country or frappe.get_system_settings("country")`。**故实际取的是 `Company.country` 字段值**。

**判 `go` 的条件**：返回值逐字为 `China`。若返回中文「中国」或带空格等变体，判 `no-go` 并**如实填出实际字符串**——那个字符串就是自有 app 该用的键。

**已备探针**：`Spike/V14-get-region-china.py`（六项：无参调用 / 传公司名 / 各公司 country 原值 / 全局默认与 System Settings / Country 记录 / 当前已注册的 regional_overrides 键）。

### V-15

**决定什么**：CR-010（导航按业务流重排）走 **L0（直接改记录，零代码）** 还是 **L1（出 fixtures）**，侵入度表第 22 项标注工作量差一倍（2.5–3.5 人日的走法差异）。

**验到什么程度**：**不能只验 `bench migrate` 跑完记录还在**——要验改动的**字段值**有没有被覆盖回 json 原值。三张表分别验，因为它们的 `standard` 语义可能不同：`Workspace Sidebar` 标准记录来自 `erpnext/workspace_sidebar/*.json`，而 `Desktop Icon` 是 `create_desktop_icons_from_workspace()` 生成的（生成源与导入源不是一回事，可能行为不同）。

**⚠ 改的是已恢复的演示数据站点**：请只改一条可辨识的测试记录（如给某个 `Workspace Sidebar Item` 的 label 加后缀 `-V15TEST`），验完**改回原值**，不要动多条。若判断有风险，先跑 `docker/backup.sh`。

### V-16

**决定什么**：三处的改法都押在它上面——
- **CR-008** 演示操控：图谱定的是 `app_include_js` 注入监听 + 走 `cur_frm` API，这条本身是**追加**不是覆盖，风险较低；但若要在演示中改变 desk 既有行为（如拦某个跳转）就需要覆盖能力。
- **LG-074** 侧栏 `/undefined` 404：根因在上游 `sidebar_header.js:145/:160` 写 `icon_html` 而 `:351-375` 模板只读 `icon`/`icon_url`（全仓 `icon_html` 零读取点）。修法两个方向——改上游模板，或 app 侧覆盖。**Stage 概况第 17 条明记「前端 js 的覆盖机制本 Round 未验」。**
- **EN-001** 树形 DocType 空白：`*_list.js` 是空文件、实现在 `*_tree.js`。

**验到什么程度**（按 SA Spec 纪律 3「架构类命题要验到边界」）：
1. **追加能力**（基线）：`app_include_js` 注入的 js 确实被加载进 desk 页面。
2. **覆盖能力**（关键）：能否改变一个**已定义的** desk 类或方法的行为。`app_include_js` 的加载时机相对 desk 自身 bundle 是先还是后，决定覆盖要用什么手法（直接改原型 / 等 `frappe.ready` / monkey-patch）。**请把实测到的加载顺序写进实际观察**。
3. **构建边界**：`bench build` 之后是否仍生效（bundle 重建会不会丢）。
4. **没触及什么也要写**（Spec 复核建议第 1 点）。

**不需要真修 LG-074**——只验机制成不成立。

### V-17（第 6 步追加）

**决定什么**：决策 3 的分派表把导航记录（CR-010）定为"标准记录 json 放 `erx_core` 同名目录"，而这一步押在"自有 app 的同名 json 能覆盖 erpnext 同名记录"上。**V-15 没验这件事**——它验的是"改 DB 记录不被 migrate 覆盖"，是另一回事。

**已知机制**（读码，给不出确定答案故须实验）：`frappe/model/sync.py:120-126` 的 `app_level_folders = ["desktop_icon", "workspace_sidebar", "sidebar_item_group"]` 是**按 app 逐个扫**的，而 `sync_for(app)` 的调用顺序随 `installed_apps`；`import_file.py:128-141` 的跳过判据是 `json.modified <= db.modified`。**故同名冲突的结果取决于两者如何交互**：若 erpnext 先导入、`erx_core` 后导入，则后者的 json `modified` 是否新于此刻的 db 值决定它赢不赢；而两个 json 的 `modified` 是我们可控的字段。

**验到什么程度**：
1. 在测试 app 的 `{app}/workspace_sidebar/` 放一份与 erpnext 同名（如 `stock.json`）但内容不同的 json，跑 `bench migrate`，看 DB 里最终是哪一份。
2. **若自有 app 赢**：判 `go`，并记下它靠的是什么（modified 更新？扫描顺序在后？）——**这决定"我们要不要每次改完都手动把 json 的 modified 调新"**。
3. **若 erpnext 赢或结果不稳定**：判 `no-go`，则导航记录须改走别的手法（如 `after_install` 里直接改记录、或 fixtures），决策 3 的分派表要改那一行。
4. 顺手记：`Workspace Sidebar` 的 `app` 字段在自有 app 的 json 里该填什么（它参与 `export_sidebar` 的守卫与 `delete_file` 的路径推导）。

**⚠ 沿用 V-15 的安全约束**：先备份、只动可辨识的测试记录、验完清理干净（含测试 app 卸载与 assets.json 残留）、禁 reinstall/drop/删记录。**并注意 V-16 报告的并发教训——若同时段有别的 spike 在动同一站点，先错开。**

### V-18（第 8 步追加，阻塞决策 5）

**决定什么**：决策 5 取 **B**（只抄 4 个 `override_whitelisted_methods`，**不抄 Company 三钩子**）还是退回 **A**（原样抄 zelin，含 Company 的 `before_insert`／`on_update`／`after_insert`）。

**为什么必须实跑**：zelin 用 `before_insert` 置 `frappe.local.flags.ignore_chart_of_accounts = True` **绕过**原生建账，再在 `on_update` 里自己调 `erpnext_china_create_charts`。它为什么要绕过，代码里没有注释说明——**可能是原生流程吃不下它那份 JSON，也可能只是作者图省事**。这两种情形对本项目的架构后果完全不同：

- 若原生流程吃得下 ⇒ 取 B，**Company 上零钩子**，避开与 HRMS 在 `Company.on_update` 上的同钩子交互（HRMS 在那里跑 `set_default_hr_accounts`，可能往已定型的科目体系里加 HR 科目；执行顺序按 `installed_apps`，我们在 HRMS 之后）。
- 若吃不下 ⇒ 退回 A，并**记下具体的失败形态**（那正是 zelin 绕过它的理由，值得留档）。

**两段验证，都要跑**：

**第一段 —— 原生建账能否吃下那份科目表**

1. 只注册 4 个 `override_whitelisted_methods`（指向抄进测试 app 的 `get_charts_for_country` / `get_chart` / `get_coa` / `get_all_nodes`），**不挂任何 Company doc_events、不置 `ignore_chart_of_accounts`**。
2. 建一家新公司（**不要用 `华东弹簧`**，另起一个测试公司名），`chart_of_accounts` 选 `小企业会计准则(2024)`。
3. 判据（逐项报，不要只报「成功」）：建公司是否报错；`Account` 记录数是多少（zelin 那份 JSON 是 **266 个节点**，故期望量级在此）；**根节点的 `root_type` 是否正确**（`资产类`→Asset／`负债类`→Liability／`权益类`→Equity／`成本类`→Asset／`收入类`→Income／`费用类`→Expense，这是本轮已从 JSON 读出的六个顶层）；`2221000 应交增值税` 下那 20 条明细（`2221001` 进项税额 … `2221020` 未交增值税）是否都建出来了。
4. **若报错，完整记下报错与 traceback** —— 那就是 zelin 绕过原生流程的理由。

**第二段 —— 税模板的科目匹配（验发现八的判读）**

本轮读码得出一个与既有记载相反的结论，**须实跑确认**：

- 既有记载说 `tax_template.json` 小企业键下 P13 销项引用了不存在的科目号 `222105`／`22210005`（应为 `2221005`），而装载包在裸 `except` 里只 log ⇒ **「最常用的 13% 销项模板会静默建不出来」**。
- 本轮读 `erpnext/setup/setup_wizard/operations/taxes_setup.py:209-226` 的 `get_or_create_account`，发现 `filters={company, root_type}` 是 AND 而 `or_filters={account_name, account_number}` 是 **OR** ⇒ 科目号不存在时**按 `account_name` 仍能命中**（`销项税额` 在该表里存在，号 `2221005`，`root_type=Liability` 与默认值一致），故模板应当照常建出且指向正确科目；即便名字也不命中，`:228-240` 会**新建**一个科目，仍非「建不出来」。

**故这一段要验的是**：**不修那个 bug**、直接跑 `setup_tax_template`（或等价地走 zelin 的 `after_install` 路径），然后查：

1. `Sales Taxes and Charges Template` 里 **13% 那两个模板（含税／未税）是否存在**？
2. 若存在，它们的 `account_head` 指向哪个科目——是正确的 `2221005 销项税额`，还是**新建出来的野科目 `222105`／`22210005`**？
3. `Error Log` 里有无 `china_company_default.utils.setup_tax_template` 的条目（即是否真触发了那个裸 `except`）？

**这三问的答案决定那条记载该怎么改**：若模板存在且指向 `2221005` ⇒ 发现八成立，记载的因果链错，性质降为「应修否则埋脆依赖」；若模板确实缺失 ⇒ 发现八错、原记载对，**照原记载办并写清 Claude 的读码错在哪**。

**⚠ 安全约束（沿用 V-15，另加两条）**

- 先跑 `docker/backup.sh`；**不要动 `华东弹簧` 这家公司**（它是演示基准数据，含 22 GL／12 SLE／1 BOM／**3 工单** —— ⚑ 第 18 步改正：本文原写 2 工单，站点实查为 3；`docs/项目概况.md` 对该备份也记的 2 工单，**Stage 收口按常驻文件契约逐出时需核清到底是备份内容不同还是此后新增了一张**）——另建测试公司。
- 验完**删掉测试公司及其科目**，或明确报告「未删、留待人工处置」并说清残留了什么。删公司在 ERPNext 里牵连甚广，**若判断删不干净，宁可不删、如实报告**，不要勉强清理到破坏站点。
- 测试 app 用完卸载，**含 `assets.json` 残留与 `sites/apps.txt` 还原**（V-16 已踩过这个坑，见 `Spike/V16-desk-js-override.md`）。
- **不要与别的 spike 同时段跑**（V-16 报告的并发教训：它与 V-15 的 `bench migrate` 撞过同一站点）。
- 禁 `bench reinstall`、禁 drop/restore 数据库、禁改上游源码。

### V-19（D 步开工前追加，阻塞 DEC-058 的 ADR）

**追加缘由**：C 步第 18 步忠实度核对查出一处漏记 —— 探针原话（本表 V-18 行内，另见 `P1-S2-R4-C架构讨论.md:805`）：「命题只问 B 案成不成立，故 `erpnext_china_create_charts` 与三个 doc_events **刻意没有抄进测试 app**（抄了会让探针证明错的东西）。即 A 案跑得通本次**未经实测**，只是 zelin 上游在用。」C 步复核建议据此建议「D 步开工前补一次实测」，用户 2026-09-25 指名派出。**本步是附属形态可选步骤（SA spike），不另占 Round，产物沿用 C 步字母填回本表**（`流程规范.md` §7.1／§11.1）。

**决定什么**：DEC-058 已定案取 **A**（原样抄 zelin，含 Company 三钩子）。D 步要把它写成 ADR 且状态标 `accepted`。**若本探针判 no-go，该 ADR 从落笔就是错的**，须回 C 步重开决策 5 —— 而 B 已被 V-18 证伪，即两案皆废、须另找第三条路（`create_charts(custom_chart=...)` 参数直传是已在案的 LG-102）。

**为什么必须实跑（三条都是 V-18 没覆盖的）**

1. **「不崩」与「建出来」是两件事，V-18 已亲自证明过这一点。** A 案的现有依据只到「不崩」：`company.py:346` 的 `if not frappe.local.flags.ignore_chart_of_accounts:` 守卫把整块（含 `:348` 崩点与 `:349 create_default_accounts()`）跳掉，这是机制必然。但 V-18 第 9 段实测 `create_charts(不存在的公司, '小企业会计准则(2024)', None)` **不抛错、静默返回 `None`、建 0 个 Account** —— 即绕过崩点之后完全可能得到一张空表。A 案建账靠的是 zelin 自己的 `erpnext_china_create_charts` → `_import_accounts`（`Reference/zelin-tech-erpnext_china/erpnext_china/chart_of_accounts/custom_accounts/custom_account.py:20`／`:27`），**那是一条 V-18 刻意排除、至今零实测的第三条代码路径**，与 erpnext 的 `create_charts` 不是同一份实现。
2. **A 案的 flag 组合与原生不同，副作用不可由 V-18 的观察外推。** zelin 的 `company_before_insert` 置 `ignore_chart_of_accounts=True` **并置 `frappe.flags.country_change = False`**，而 `company_on_update` 在无 Account 时又把 `country_change` 置回 `True`（`Reference/zelin-tech-erpnext_china/erpnext_china/doc_events.py`）。`country_change` 正是 `company.py:355-357` 上 `install_country_fixtures()` 与 `create_default_tax_template()` 的开关 —— 即 V-18 观察到的那个**无编号 17% VAT 科目**在 A 案下是照样注入还是被跳过，纯看这两处置值的先后与 `on_update` 的执行次数，读码推不定。
3. **`set_company_default` 挂在裸 `except` 里，失败静默。** `company_on_update` 末段是 `try: set_company_default(doc.name) except: frappe.log_error(...)`。它正是可能把 V-18 观察到的**默认科目挑错**修正回来的那一步。它跑通与否只在 `Error Log` 留痕，界面上看不出。

**三段验证，都要跑**

**第一段 —— A 案能否建出完整科目表（核心，决定 go／no-go）**

1. 复用 `Spike/V18-setup-test-app.sh` 的脚手架手法（手搓 app、`.pth` 进 sys.path、`sites/apps.txt` 整份重写），但**把 V-18 刻意排除的两样抄进来**：`erpnext_china_create_charts` 及其依赖（`_import_accounts` / `add_suffix_if_duplicate` / `identify_is_group` / `get_coa`）、以及 `Company` 的三个 `doc_events`（`before_insert` / `on_update` / `after_insert`）。4 个 `override_whitelisted_methods` 照 V-18 一并注册。
2. 建一家新测试公司（**不得用 `华东弹簧`**），`country='China'`、`chart_of_accounts='小企业会计准则(2024)'`。
3. 判据逐项报，**不要只报「成功」**；且**与 V-18 的原生观察逐项对账**（V-18 那组数字是用脚手架 monkeypatch 强行喂进后测得的内容侧基线，不是 A 案的实测值）：
   - 建公司有无报错；有则完整 traceback。
   - `Account` 条数。V-18 基线：JSON 递归节点 **266**，原生路径建出 **267**（多的 1 条是 `VAT`）。A 案建出几条、多出／少掉的是哪些（逐对 `(account_number, account_name)` 做集合差，两个方向都报）。
   - **六个顶层 `root_type`**：`1 资产类`=Asset／`2 负债类`=Liability／`3 权益类`=Equity／`4 成本类`=Asset／`500 收入类`=Income／`540 费用类`=Expense。V-18 基线直方图 Asset 72／Equity 15／Expense 85／Income 26／Liability 69，`is_group` 1→41、0→226。
   - `2221001`…`2221020` 是否 20 条齐全。**注意 V-18 已更正过本命题的前提**：这 20 条在 JSON 里本就不全挂在 `2221000` 下（`2221001`–`2221010` 挂 `2221000 应交增值税`，`2221011`–`2221020` 是 `2221 应交税费` 的直接子级）。
   - 树完整性：NSM（`lft>=rgt` 或空值的行数）、孤儿父引用数、重名加后缀数。V-18 基线三项均为 **0**，`lft/rgt` 跨度 1..534。

**第二段 —— 副作用对账（A 案 vs 原生，逐项判「多出／少掉／相同」）**

1. **无编号 17% `VAT` 科目**在不在？（V-18 原生路径下有：`account_number` 为空、`account_type=Tax`、`root_type=Liability`、父 `2221000 应交增值税`，由 `create_default_tax_template()` 读 erpnext 自带 `country_wise_tax.json` 的 China 17% 条目新建。）顺带报 `frappe.flags.country_change` 在 `insert` 结束时的终值，以及 `install_country_fixtures` 有无执行痕迹。
2. **默认科目**六个值各是什么：`default_receivable_account` / `default_payable_account` / `default_inventory_account` / `default_bank_account` / `default_income_account` / `round_off_account`。V-18 原生基线依次为 `2203 预收账款`（错，应为 `1122 应收账款`）／`2211010 职工工资`（错，应为 `2202 应付账款`）／`1421 消耗性生物资产`／`1012 其他货币资金`／`None`／`None`。**A 案下 `set_company_default`（`.../chart_of_accounts/company_default/utils.py:6` → `set_default_accounts:13`）是否把它们改对了？** 这一问对决策意义最大：若 A 案顺带修了默认科目，「必须取 A」就多一条硬理由；若没修，本项目仍须自己补一步设默认科目，那是要进架构文档的一条模块职责。
3. `Error Log` 跑前跑后各几条、新增的是哪些。**特别查 `set_company_default` 那个裸 `except` 有没有触发**（按 `error LIKE '%set company default%'` 与 `method LIKE '%company_on_update%'` 两种查法都查一遍）。
4. 仓库（`create_default_warehouses()` 在 A 案里由 `on_update` 显式调）、成本中心、部门、`Financial Report Template` 各建出几条。V-18 原生基线：5 仓库／2 成本中心／13 部门／6 条 `Financial Report Template`。**`sync_financial_report_templates` 在 A 案下被守卫跳过了，故那 6 条财报模板很可能一条都没有** —— 若确实没有，这是 A 案的一处实质缺口，须记下来（财报模板缺失意味着资产负债表与利润表的取数模板没建，属「要自己补」的清单项）。

**第三段 —— 触及边界（`go` 的门槛：SA Spec 要求不能只验 happy path）**

1. **重复 `on_update`**：`company_on_update` 的建账入口条件是 `if not frappe.db.exists("Account", {"company": doc.name, "docstatus": ("<", 2)})`。改一下已建好的测试公司再 `save()`（触发第二次 `on_update`），确认**不重复建账、不抛错**。
2. **第二家公司**：在同站点再建一家测试公司（同一份科目表）。验重名科目的 `add_suffix_if_duplicate` 是否按公司缩写正确加后缀、两家公司的科目互不串。
3. **错误路径**：建一家 `country='China'` 但 `chart_of_accounts` 选 `Standard`（不在 `china_coa` 列表内）的公司 —— 此时 `before_insert` 的 `if` 不成立、`ignore_chart_of_accounts` 不置，但 `on_update` 的建账分支**与 `chart_of_accounts` 无关、照样跑**（它只看有无 Account）。故须验：这种组合下建出来的是 `Standard` 还是那份中式表、会不会报错、两条建账路径会不会各建一遍。**这是读码就看得出的一处可疑处，实测确认它的实际行为。**
4. **`existing_company` 路径不验**（`erpnext_china_create_charts` 第三参），本项目无此场景，明确记为未触及。

**明确不在本探针范围（记为未触及边界，不要顺手验）**

- **HRMS 同钩子交互（LG-101）仍无法验**：本 bench 未装 hrms（`frappe-bench/apps/` 仅 frappe 与 erpnext），`Company.on_update` 上的执行顺序、以及 `set_default_hr_accounts` 是否往已定型科目体系里加 HR 科目，**装 HRMS 之后才能验**。本探针只需确认「本次未验」这一事实，**不要为此装 app**。
- `after_install`（税模板 + 默认科目那一套）**已由 V-18 第二段覆盖**（13% 两个模板建出、`account_head` 指向正确的 `2221005 销项税额`、裸 `except` 未触发），本探针不必重跑；但若 A 案路径下税模板行为与 V-18 不同，须报出差异。

**⚠ 安全约束（逐条沿用 V-18）**

- 先跑 `docker/backup.sh`；**不要动 `华东弹簧` 这家公司**（它是演示基准数据，含 95 科目／22 GL／12 SLE／1 BOM／3 工单／2 销售订单／2 Item／6 仓库）—— 另建测试公司。
- 验完**删掉测试公司及其科目**（本探针会建 2~3 家，全部要清），或明确报告「未删、留待人工处置」并说清残留了什么。删公司在 ERPNext 里牵连甚广，**若判断删不干净，宁可不删、如实报告**，不要勉强清理到破坏站点。
- 测试 app 用完卸载，**含 `assets.json` 残留与 `sites/apps.txt` 还原**（`apps.txt` 无末尾换行，须整份重写，见 `Spike/V18-setup-test-app.sh`）。
- **不要与别的 spike 同时段跑**。
- 禁 `bench reinstall`、禁 drop/restore 数据库、禁改上游源码（zelin 的代码是**抄进测试 app**，不是改 `Reference/` 下那份）。

**填表纪律**（`docs/流程体系/交接契约.md`）：只填后三列（判定／实际观察／探针代码），前三列不动；**判定只回答事实，不写架构建议**；`无法判定` 不得当 `go`；`go` 的门槛是触及边界 —— 只跑通 happy path 则判 `无法判定` 或据实说明。建议一律写进本表末尾的「复核建议」节。

## 复核建议

（由 spike 填回，按 `SA-probe-devBlueprint-spike.md`「复核建议」节：验证深度与未触及的边界 / 探针与真实场景的差距 / 拿不准处）

### V-14（本轮已验）

**1. 验证深度与未触及的边界**

已触及：
- **字符串逐字层面**（本命题的核心边界）——不止看 `repr()`，另核了 `len` / 每字符 codepoint / utf8 原始字节 / `isascii()` / `== "China"`，排除了前后空格与同形异码字符（如全角字母、西里尔 `С`）这两类会让精确匹配静默失效而 `repr()` 看不出的情形。
- **两条调用路径**：传 company 与无参各跑一次，均为 `'China'`。
- **值来源的语义边界**：`Company.country` 是 `Link`→`Country`，存的是 docname；站点 `language='zh'` 下该值仍为 ASCII，确认中文只在翻译层、不落库。
- **hook 侧键空间**：读出当前实际注册的四个键，并核了 `China` 键当前不存在。

未触及：
- **未装自有 app 做端到端分派验证**。本探针只验 `get_region()` 的返回值本身；`@allow_regional` 的分派机制（含末位 app 胜出、按国家隔离）在 A 步 V-01/V-01b 已验，本次未重复。即「键写对了覆盖就会命中」这一段依赖前述判定，本探针不复验。
- **未验多公司 / 多国家场景**。站内仅 `华东弹簧` 一家公司，无第二个 country 值可比对；`get_region()` 按公司取值，多公司下返回值随公司而变，本次无数据可验。
- **未验 `frappe.flags.country` 运行期被改写的分支**（仅在未传 company 且 `frappe.local.flags.company` 为空时才走到）。
- **未验 `Country` 记录被改名 / 站点被换国家后的表现**，也未验升级（`bench migrate` / 换 erpnext 版本）是否会改动该字段值。

**2. 探针与真实场景的差距**

- **环境**：本机 Docker 容器 `erx001-frappe-1`，站点 `erx.localhost`，`erpnext 16.35.0 (12cd563)` / `frappe 16.34.0 (c1f1e8e)`，`installed_apps` 仅 `frappe`,`erpnext`。
- **数据**：已恢复的 `20260922_145623` 演示数据（1 公司）。
- **手段**：纯读，未写任何 DB 记录，未改生产码。
- **复查法**：`docker exec -i -w /workspace/frappe-bench erx001-frappe-1 bench --site erx.localhost console < Spike/V14-get-region-china.py`（须先 `export MSYS_NO_PATHCONV=1 MSYS2_ARG_CONV_EXCL='*'`）。第 7 段打印 codepoints 与等值判断，第 8 段打印语言与字段定义；要换公司看返回值，改第 2 段 `get_region()` 的参数。
- **已知差距**：`China` 键当前不在 `regional_overrides` 里，这不是缺陷，而是自有 app 尚未建立的如实反映；该键是否生效须等 app 落地后复验。

**3. 拿不准处**

命题未被收窄，原表述可直接判真假，无保留。

### V-15（本轮已验）

**1. 验证深度与未触及的边界**

已触及：
- **字段值层面**（本命题核心，非"记录还在"）——三张表各改一条记录的一个字段，migrate 后逐一比对实际值与 json 原值。
- **三张表分别验**，未一概而论；并顺带核出它们的 `standard` 语义实为**两套而非三套**（`Workspace Sidebar Item` 是 `istable:1`、无自己的 `standard` 字段，随父 sidebar json 进出）。
- **覆盖判据**：读码定位到 `import_file.py:128-142`，且用两次 migrate **实测了判据的两侧**——`json.modified` 较旧时跳过（不覆盖），较新时覆盖。失效边界是实测的，不是推断。
- **覆盖时的副作用**：观察到子表整表删后重插（行名变更），非原地更新。
- **假阳性排除**：发现 `developer_mode=1` 会把改动导出回 app json 源，先把 json 核到与 HEAD 逐字节一致才判定，否则"未被覆盖"不成立。

未触及：
- **未验真实升级**（`bench update` / 换 erpnext 版本）。失效边界是靠**手工把 json 的 `modified` 调到未来**来模拟上游换文件，未跑真实升级流程；真实升级是否还有其它触达导航记录的动作（patch、`after_migrate` hook）本探针未查。
- **未验"删记录"与"增记录"**。只验了改字段值。读码显示记录不存在时 `db_modified_timestamp` 为 `None`、守卫被跳过而无条件导入（即删掉会被重建），但**未实测**——按纪律 5 只作读码陈述记在探针文档，不据此判定。
- **未验改多条 / 批量重排**。每张表只改一条、且是单个字段；整体重排（改 `idx` 顺序、增删子行、跨 sidebar 搬条目）的行为未验。子表在覆盖时整表重插这一点提示"改顺序"与"改单字段"未必同构，本次无数据。
- **未验 `sidebar_item_group`**。`sync.py:120` 的 `app_level_folders` 第三类，命题未列，未验。
- **未验非 `standard` 记录与 `for_user` 记录**，也未验 `developer_mode=0` 下的表现（§3 陷阱只在 `developer_mode=1` 成立，关掉后 `save()` 不导出，但本次未实测关掉后的 migrate 行为）。
- **未验前端实际呈现**。全程在 DB 与 json 层比对字段值，未开浏览器确认侧栏/图标网格的显示随之改变。

**2. 探针与真实场景的差距**

- **环境**：本机 Docker 容器 `erx001-frappe-1`，站点 `erx.localhost`，`erpnext 16.35.0 (12cd563)`，`developer_mode=1`。
- **数据**：已恢复的 `20260922_145623` 演示数据；跑前另做备份 `20260924_231033`（旧三份及 `保留-R6重装前/` 均未被覆盖）。
- **手段**：改了 DB 记录（数据，非生产码），已改回并核零残留；两个 erpnext json 源被 `developer_mode` 导出波及，已改回至与 HEAD 逐字节一致。演示数据经核完好（1 公司 / 95 科目 / 6 仓库 / 财年 2026 / 2 Item / 1 BOM / 2 销售订单）。
- **复查法**：见 `Spike/V15-standard-record-migrate.md` §2 的命令序列。注意两处跑法坑：`bench execute Spike.xxx` 不可用（`/workspace/Spike` 不在 import 路径），直接跑脚本须以 `/workspace/frappe-bench/sites` 为 cwd（否则 logger 相对路径报 `FileNotFoundError`）。
- **已知差距**：`developer_mode=1` 是开发机配置，**演示机 / 生产站点若为 `developer_mode=0`，§3 的导出陷阱不出现**，此时改记录只落 DB。判定（不被覆盖）本身不依赖该开关——判据是 `modified` 时间戳比对，与 `developer_mode` 无关——但"改动会不会同时污染 app 源码目录"随该开关而变。

**3. 拿不准处**

- 命题未被收窄，原表述可直接判真假。
- 命题背景称 `Desktop Icon` 由 `create_desktop_icons_from_workspace()` 生成、"生成源与 json 导入源不是一回事"，与实测不符：该函数在 migrate 路径上不被调用（全仓仅 `install.py:203` 一处调用点）。已在实际观察与探针文档 §6 如实更正。若发起步骤另有依据认为存在其它生成时机（如装 app、`bench build`），该处需复核——本探针只覆盖 `bench migrate` 这一条路径。
- 第一次 migrate 日志有 `Deleting icon Frappe Framework`，来自 `delete_duplicate_icons()` 清理重命名后的陈旧 App 图标，与本次三条测试记录无关，图标总数仍 35；判为既有上游行为，但本探针未追它的来历。

### V-16（本轮已验）

**1. 架构类命题的验证深度：触及了哪些边界、没触及哪些**

已触及：
- **加载顺序**（本命题核心）——不止读码定顺序，另用真浏览器核了三层：desk 页 HTML 的 script 标签次序、自有脚本 parse 那一刻各 desk 符号的 `typeof`、以及 `defer`/`async`/`module` 计数为 0（故为顺序执行，不是竞态）。顺序的**成因**也定了：desk 的 9 个 bundle 本身就是 frappe 的 `app_include_js` hook 值，与自有 app 进同一列表，由 `get_all_apps()` 的 frappe 置顶决定，故顺序**不是巧合、不可配置**。
- **覆盖真的生效**（非"看代码觉得可以"）：四种手法各自记录**被调用次数**而非仅安装成功，并跑了**对照组**（CDP `Page.addScriptToEvaluateOnNewDocument` 预置禁用标志，先于任何页面脚本执行）——对照组 patch 全空、DOM 一致，故 calls 不是探针自证。
- **错误路径**：注入脚本引用尚未定义的符号时的表现已实测（`frappe.app`/`frappe.ready`/`form_builder`/`FormBuilder`/`PrintPreview` 在 parse 时为 `undefined`，安装失败被记录而非静默成功）。
- **构建边界**：`bench build` 前后各跑一遍，且 assets.json **全量 44 条逐条 diff**（非抽查一个 bundle——这是 MEMORY 里那条教训的直接应用），确认 `desk.bundle` 哈希也变了而覆盖仍生效。
- **跨 SPA 路由存活**：客户端 `frappe.set_route` 两跳（`List/Item`、落到 `Tree/Account`），patch 在三次路由变更后仍生效。这是 CR-008 演示操控的真实形态，非首屏一次性。
- **两条注入路径**：过 esbuild 的 bundle 路径与不过 esbuild 的裸路径分别验，故"覆盖能力"不依赖打包器行为。
- **懒加载边界**：实测强制跳 Kanban 路由后 `frappe.views.KanbanView` 才由 `undefined` 变 `function`，确认"未被 `frappe.require` 拉入的模块 parse 时改不到"。

未触及：
- **没验并发 / 体量**。单浏览器、单标签、单用户 Administrator。多标签同时开 desk、或多用户并发下覆盖是否仍稳定，未验（此类原型补丁是进程内 JS，理论上无跨标签共享状态，但**未实测**）。
- **没验跨浏览器**。只跑 Chrome 153 headless。Edge/Firefox/Safari 未验；`headless` 与真实带头浏览器的差异亦未验（headless 无扩展、无真实渲染节流）。
- **没验多个自有 app 互相覆盖同一目标**时的胜出顺序。只装了一个测试 app；两个 app 都改同一个原型方法谁赢（按列表顺序应是后者，但未实测）。
- **没验 `bench build --app` / `bench watch` / 生产模式**。只跑了全量 `bench build`（`developer_mode=1`、`bench serve` 开发服务器）。生产部署（gunicorn + nginx 静态资源、`developer_mode=0`、CDN/缓存）下注入是否一致，未验。
- **没验缓存边界**。`bench build` 换哈希天然破缓存，但裸路径 `/assets/erx_spike/js/*.js` **无哈希**，浏览器/反代缓存下改了 js 是否立即生效，未验。
- **没验升级边界**（本次最值得注意的一条）。只验了 `bench build` 后仍生效，**没验 frappe 升级后仍生效**。覆盖手法依赖被覆盖对象的**内部形状**（类名 `frappe.ui.SidebarHeader`、方法名 `get_icon_for_menu_item`/`add_app_item`、参数签名），这些都是上游**非公开 API**，升级改名/改签名即静默失效（不报错，只是补丁不再命中或命中后行为错）。本命题只问"能不能覆盖"，该问题已答；但"覆盖能撑多久"未验。
- **没验 `frappe.ready` 之外的官方等待钩子是否存在**。只实测了 `frappe.ready` 在 desk 页为 `undefined`、以及 `DOMContentLoaded` 与 `frappe.router.on("change")` 可用；是否另有官方推荐的 desk 就绪钩子（如某个 `frappe.after_ajax` / boot 事件），未穷举。
- **没验覆盖对性能的影响**。`add_app_item` 被调 26 次这类热路径包一层的开销未测。
- **没验真实修 LG-074**（命题未要求，见下「拿不准处」）。

**2. 探针与真实场景的差距**

- **环境**：容器 `erx001-frappe-1`，站点 `erx.localhost`，frappe `16.34.0@c1f1e8e` / erpnext `16.35.0@12cd563`，Python 3.14.7，`developer_mode=1`，`bench serve` 开发服务器；浏览器为 Windows 宿主的 Chrome 153 headless 经 CDP 驱动。
- **测试 app 是手搓的，不是 `bench new-app` 产物**。这是**已知差距**：本 bench 未装 `flit_core`，`bench new-app` 会 `pip install -e` 而跑不通，故按 frappe/erpnext 自己在本 bench 用的 `.pth` 机制手搓。后果有二——① 缺 `pip install -e` 的 dist-info，`bench` 的部分 app 管理命令行为可能与正规 app 不同；② 实测该手搓 app 在 `frappe.boot.app_data` 里的 `app_logo_url` 回来的是**数组**而非字符串、`app_route` 为空串（正规 app 靠 `add_to_apps_screen` 的 `logo` 字段避开）。**但这两点都不影响本命题的判定**：`app_include_js` 的注入与执行、加载顺序、覆盖生效、build 保留，全部与 app 的打包方式无关（顺序只取决于 `sites/apps.txt` 的 app 次序）。自有 app 正式落地后建议按正规方式建，本探针不据此判定。
- **数据**：站点为已恢复的 `20260922_145623` 演示数据；本探针**未写任何业务数据**，只装/卸了一个 app。
- **复查法**：见 `Spike/V16-desk-js-override.md` 的「复现步骤」。要换覆盖目标，改 `Spike/V16-desk-js-override.probe.js` 里 `targets` 数组与 a/b/c/d 四段的目标路径；要看某符号在 parse 时到底有没有，加进 `targets` 即可（**注意**：bundle 路径的改动须重跑 `bench build` 才生效，裸路径立即生效——本次就踩到过一次，run[0] 用的是旧哈希 bundle 而 run[1] 已是新 payload）。四次跑的原始输出在 `Spike/V16-out/*.json`。
- **共用容器**：探针进行中容器里另有一个我未启动的 `bench migrate`（V-15 探针）在跑。本次未观察到互相干扰，但**这是同时段并发操作同一站点**，若日后复现结果不一致，此为一个可疑变量。

**3. 拿不准处**

- **命题未被收窄**。任务书曾预留"若无浏览器则收窄到加载顺序 + 构建保留两档"的余地，**本次未动用**：宿主有 Chrome 与 Node 24（自带全局 `WebSocket`），故经 CDP 拿到了真浏览器证据，四档按原表述全验。
- **命题背景对 LG-074 的两处描述与实测不符，已在实际观察与探针文档如实更正**：① 根因文件路径是 `frappe/public/js/frappe/ui/sidebar/sidebar_header.js`，不是背景所写的 `.../views/workspace/sidebar_header.js`（该路径不存在；行号 145/160 对得上）；② 「全仓 `icon_html` 零读取点」不成立——源码里 `frappe/public/js/frappe/ui/menu.js:96-97` 与 `frappe/public/js/frappe/ui/settings_dialog.js:255-258` 都读 `item.icon_html`。背景说的「`add_app_item` 只读 `icon`/`icon_url`」这一处是对的。
- **`/desk/undefined` 那条 404 的确切产生点本次没定到**，判 `无法判定`（仅此子问题，不影响 V-16 主命题）。已排除的：不是 `get_icon_for_menu_item`——探针把它整个换掉并实测被调 17 次，该 404 仍出现 1 次，且**未打补丁的对照组也是 1 次**，数量相同；也不是测试 app 引入的——卸载后 `app_data` 回到 2 条，该 404 依旧出现。指向 `sidebar_header.js:299-316` 的 `set_header_icon()`（四个分支都拼 `` `<img src=${...}></img>` `` 且**属性值未加引号**），但实测 `frappe.boot.app_data[0].app_logo_url` 有值、DOM 里 `.header-logo` 最终渲染出正常 svg、`imgs_with_undefined_src` 为空数组——即 404 发生在**中间态**、随后被重渲染覆盖。CDP 抓到该请求 `initiator.type="script"` 但 **`stack` 为空**（异步初始化，调用栈已丢），故未能定到发出它的那一行。**由此，「修 LG-074 只要 app 侧三行」这个判断本次给不出**：覆盖机制本身成立，但不知该覆盖哪个方法能消掉它。若后续要修，需先定产生点（可行方向：给 `set_header_icon` 打补丁后观察 404 是否消失，即用覆盖能力反查根因——本次未做）。
- **`bench build` 跑过一次**，`sites/assets/` 下全部 44 个 bundle 哈希已变（正常产物、不进版本管理，`frappe-bench/` 在 .gitignore 内）。若别处文档记录过旧哈希，那些记录已过期。
- **环境收尾（V-16）**：测试 app `erx_spike` 已 `bench uninstall-app` 卸载、**目录连同 `.pth` 与 `sites/assets/erx_spike` 符号链接一并删除**；`sites/apps.txt` 还原为原始字节 `b'frappe\nerpnext'`（原文件结尾无换行，已逐字节核对）；`bench build` 写入 assets.json 的 `erx_spike.bundle.js` 条目已清（45→44，`uninstall-app` **不管这个文件**，会残留并被塞进每个 desk 页的 boot 负载）；数据库 Module Def / Desktop Icon / Workspace Sidebar / Workspace Sidebar Item / DocType / installed_apps / DefaultValue 均无 `erx_spike` 残留（SQL 核验见 `Spike/V16-cleanup-check.sql`）。**上游源码未改**（纪律 8）：`apps/frappe` 工作区 `git status --porcelain` 为空；`apps/erpnext` 有 2 个文件显示改动（`banking/yarn.lock`、`.../total_stock_value.json`），**非本次造成**——mtime 均为 2026-09-18 16:10（本 Session 为 09-24），diff 为纯行尾符差异（3741 增/3741 删、逐行等量）。

### V-18（本轮已验）

**1. 架构类命题的验证深度：触及了哪些边界、没触及哪些**

已触及：

- **命题被拆成「投递」与「内容」两问分别验**（本次最关键的一步）。第一段照命题原样跑，得 `no-go`，但那次失败是**投递失败**（原生流程取不到那份 JSON），若就此收手，「原生 `create_charts` 吃不吃得下这份 JSON」将**仍是未知**，而这正是决策 5 真正要问的。故另跑一段，用进程内 monkeypatch 把 `coa_mod.get_chart` 强行替成 app 那份（**探针脚手架，不是 B 案可用的机制**），让投递必成，再看内容——内容侧吃得下。两问的答案相反，混在一起报会误导。
- **覆盖机制的成因定到行**：不止观察到"覆盖没生效"，而是定位到 `override_whitelisted_methods` 全仓只在 5 处被查（`handler.py:67`、`api/v2.py:36`、`desk/treeview.py:17`、`model/mapper.py:20` 与 `:44`），而 `company.py:420` 是直接 import。并在**同一进程里同时打印**两个返回值（经覆盖得树、原生得 `None`），故"不生效"是实测到的分叉，不是读码推断。
- **错误路径验了两种形态，不止一种**。`:348` 抛错只是其一；因该崩发生在 `:349` `create_default_accounts()` 之前，另单独实测了 `create_charts(..., '小企业会计准则(2024)', None)`——**静默返回、建 0 条**。即"修掉 `:348` 就能用 B 案"这条退路也被验掉了：那会得到静默空表，比抛错更难发现。
- **跨运行方式边界（in-process vs HTTP）**。前两段都是 `env/bin/python script.py`，而真人走桌面 UI 经 `frappe/handler.py`——**而 handler.py 恰是那 4 个派发点之一**，故"经 HTTP 会不会就好了"是个真问题、不能靠推断。实测 `POST /api/resource/Company` 得 HTTP 500，异常类型／`str`／两处行号与 in-process **逐字相同**。同时白名单路由本身正常返回 app 那份表——**即桌面下拉选得出、选了就 500**，这个不对称只有过 HTTP 才看得到。
- **数量与结构的完整核对，非抽查**。266 个 JSON 节点逐对 `(account_number, account_name)` 与 DB 双向差集比对（`in_json_not_in_db` 空集），并核了 NSM 完整性（`lft>=rgt` 0 行、跨度 1..534）、孤儿父引用 0、重名加后缀 0、六个顶层的 `root_type` 与 `report_type`、五类直方图。多出的 1 条（`VAT`）**追到了创建时刻与来源函数**，没当成误差放过。
- **命题前提被核出有误并更正**：任务书说 20 条明细都在 `2221000` 下，实际 JSON 里是 10＋10（`2221011`–`2221020` 挂 `2221 应交税费`）。20 条全建出这一判据成立，但**它们的位置与前提所述不同**，已如实写进实际观察。
- **第二段验的是"不修 bug 会怎样"，且核了 payload 确实没被修**。跑前打印了五条销项条目的 `account_number` 原值（`222105` / `2221005` / `22210005` / `2221005` / `2221005`），并以 md5 核过拷进测试 app 的两个 JSON 与 zelin 原文件逐字节一致——否则"模板照常建出"会是假阳性。三问各自用了**正反两种查法**（模板存在性＋`account_head` 指向的科目全字段；野科目号跑前跑后两次查；`Error Log` 按 `error` 与 `method` 两种 LIKE）。

没触及：

- **没验修掉那处 `:348` 崩之后的完整原生路径**。这是本次最值得注意的缺口：`no-go` 的判定只需要第一处失败，故一旦 `:348` 抛错就没有继续往下走。B 案若日后想靠"绕开 `sync_financial_report_templates`"翻盘，`create_default_accounts` 之后还有 `install_country_fixtures` / `create_default_tax_template` / `set_default_accounts` 等步骤**在原生路径上从未被真跑过**（第二段跑到了它们，但那是靠脚手架喂进内容的，不是 B 案的机制）。
- **没验任何真正能让 app 的科目表进入原生路径的机制**。本次只证明"这 4 个覆盖做不到"，**没有去找做得到的别的钩子**（如是否存在某个 chart 路径 hook、或 `frappe.local.flags.allow_unverified_charts` 配合把 json 放进 erpnext 目录——后者属改上游源码，纪律 8 禁止，未试）。读码时核过 `chart_of_accounts.py` **无任何 `get_hooks` 调用**、erpnext 全仓只从自己的 `verified/` 目录扫，但"是否另有别的正规机制"本探针给不出结论。
- **没验 HRMS 同钩子交互**——即决策 5 要避的那个风险本身。本 bench `installed_apps` 只有 frappe／erpnext，**HRMS 未装**，故 `Company.on_update` 上多 app 并存时的执行顺序与 `set_default_hr_accounts` 是否往已定型科目体系里加 HR 科目，**完全没触及**。A 案是否真会撞上这个风险，本次无数据。
- **没验 A 案（zelin 原样三钩子）**。命题只问 B 案成不成立，故 `erpnext_china_create_charts` 与三个 doc_events **刻意没有抄进测试 app**（抄了会让探针证明错的东西）。即"A 案跑得通"本次**未经实测**，只是 zelin 上游在用。
- **没验体量与并发**。单公司、单进程、单次创建，266 节点。多公司同时建、父子公司（`existing_company` 分支）、`Chart of Accounts Importer` 路径（`chart_of_accounts_importer.py:106` 也调 `create_charts`）均未验。
- **没验另外两份中式科目表**（`cn_norm_chart_of_accounts2024.json` 一般企业、`cn_cnpo_chart_of_accounts2025.json` 民非、以及 `cn_sme_coa.json`）。只验了 `小企业会计准则(2024)`。前者节点数更多（85KB vs 64KB），是否有本次没碰到的形态未知。
- **没验升级边界**。崩溃点 `financial_report_template.py:144` 与 `company.py:348` 都是上游具体行，`sync_financial_report_templates` 是 v16 新引入的调用；换 erpnext 版本后失败形态可能变（甚至因上游给 `coa` 加了 `or {}` 而变成静默空表）。本次只覆盖 erpnext 16.35.0。
- **没验前端呈现**。全程在 DB／HTTP API 层比对，未开浏览器确认桌面上科目树、税模板下拉的实际显示。
- **没验 zelin 的其余 `set_company_default` 步骤**。第二段只跑 `setup_tax_template` 一个函数（纪律 4：一个探针一个命题）；`set_default_accounts` / `setup_tax_rule` / `set_item_group_account` / `set_warehouse_account` 未跑，故它们各自的裸 `except` 会不会触发、`tax_rule.csv` 引用的模板名对不对，均未验（实测 `Tax Rule` 为 0 条即因未跑该步）。

**2. 探针与真实场景的差距**

- **环境**：容器 `erx001-frappe-1`，站点 `erx.localhost`，frappe `16.34.0` / erpnext `16.35.0`，Python 3.14，MariaDB，`developer_mode=1`，`bench serve` 开发服务器。`installed_apps` 跑前为 `frappe`,`erpnext`（无 HRMS、无自有 app）。
- **最大的一处差距：第二段的内容结论依赖 monkeypatch**。`coa_mod.get_chart` 被进程内替换，这在真实部署里不存在。它回答的是"原生 `create_charts` 这段代码能否消化这份 JSON"，**不是**"B 案能不能工作"。两者不可混用——B 案的投递问题是第一段的结论，`no-go`。
- **测试 app 是手搓的，不是 `bench new-app` 产物**（沿用 V-16 的做法与已知差距：本 bench 无 `flit_core`）。但本命题的判定与打包方式无关——`override_whitelisted_methods` 的注册实测正常（4 条全在 `get_hooks` 里），失效原因在派发机制而非 app 形态。
- **未跑 `bench build`**。本次无前端资源，故 `assets.json` 全程 44 条、无 `erx_v18` 条目（V-16 那个残留坑本次不适用，已核）。
- **数据**：站点为已恢复的 `20260922_145623` 演示数据；跑前另做备份 `20260925_014739`（`docker/backup.sh`，含 files）。基准公司 `华东弹簧` 全程只读。
- **复查法**：先 `bash Spike/V18-setup-test-app.sh`（容器内，装 app），再按 `seg1` → `seg1b` → `seg2` → `seg3`/`seg3b` → `seg4` → `seg5` 顺序跑，最后 `seg6`（清理前盘点）→ `seg7`（删公司＋清 Tax Category＋清孤儿子行）→ 卸载 app → `seg8`（残留核验）。`seg9` 与 app 无关、可独立跑。**两处跑法坑（沿用 V-16）**：`bench execute Spike.xxx` 不可用；直接跑脚本须以 `/workspace/frappe-bench/sites` 为 cwd。**第三处本次新踩**：装完 app 必须重启 `bench serve`（`.pth` 只在解释器启动时读），否则整站 500 而看起来像站点坏了。要换科目表，改各脚本顶部的 `CHART` 常量；要换公司名改 `COMPANY`/`ABBR`。十段的原始输出在 `Spike/V18-out/*.json`。
- **无并发干扰**：本次容器独占，未观察到他人进程（V-16 报告过它与 V-15 撞同一站点）。跑前 `ps` 只有一个 `bench serve`。

**3. 拿不准处**

- **命题未被收窄，但被拆开报**。原表述"原生建公司流程能否用那份 JSON 建出完整科目表"整体判 `no-go`（投递不通，故整条命题不成立）；内容侧的事实另行报出，供发起步骤判断。**若发起步骤原意其实是"原生 `create_charts` 的代码质量够不够"，那答案是够**（267 条、结构完整）——但这不改变 B 案按其字面机制不可行。
- **`no-go` 的成因判定明确，但"是否存在别的正规投递机制"未穷举**（见上「没触及」第 2 条）。即本判定是"这 4 个覆盖做不到"，不是"任何办法都做不到"。
- **原生流程往中式科目表注入 `VAT`（无编号、17%）这件事，其严重性不由本探针判断**（纪律 5）。只报事实：它由 `create_default_tax_template()` 经 erpnext 自带 `country_wise_tax.json` 的 China 条目产生，`华东弹簧` 上同形存在，故**这不是本次测试公司特有**。
- **默认科目挑错（`default_receivable_account` 落在 `2203 预收账款`、`default_payable_account` 落在 `2211010 职工工资`）本次判为上游无序查询所致**，已复现该无序调用得同样结果；但**未验它是否稳定**——`frappe.db.get_value` 无 `order_by` 时的返回次序由存储引擎决定，换一次建库顺序可能得别的答案。若后续要依赖这两个字段，此处需复核。
- **清理时顺带删掉了 4 条与本次无关的历史孤儿数据**：`Company.on_trash` 用裸 `frappe.db.sql` 删税模板父表、**不级联子表**，故本次清理扫孤儿子行时，一并扫出并删除了 `China Tax - ERX`、`China Tax - ERXD` 的销项／进项子行各 2 条（共 4 条）——这两家公司在本 Session 之前就已被删除，其子行是历次探针／重装留下的既有残留。**如实登记在此**：这 4 条不是本次产生的，删除动作是本次做的。删除后全站孤儿子行为 0。
- **测试公司与测试 app 均已清理干净并逐项核验**：`V18原生乙` 已 `frappe.delete_doc` 删除（安全门全过：0 GL Entry、0 SLE、`is_group=0`、无 `parent_company`、非 `default_company`、非 `demo_company`），该公司 `Account` 0 条、按 `- V18B` 后缀匹配 0 条，成本中心／仓库／部门／三类税模板／Mode of Payment Account 全 0；`Tax Category` 7 条（**不随公司删除，本次手工清**）已清空回 0（站内跑前本就是 0）。测试 app `erx_v18` 已 `bench uninstall-app`，**目录、`.pth`、`sites/assets/erx_v18` 一并删除**，`sites/apps.txt` 还原为原始字节 `b'frappe\nerpnext'`（原文件结尾无换行，已逐字节核对），`Module Def` / `DocType` / `Desktop Icon` / `Workspace Sidebar` / `Workspace Sidebar Item` / `DefaultValue` 均无残留。站内 `Account` 回到 **95**、`Company` 仅 `华东弹簧`、`Error Log` 仍 1 条、`Financial Report Template` 6 条、NSM 无坏行。**上游源码未改**（纪律 8）：`apps/frappe` `git status --porcelain` 为空；`apps/erpnext` 那 2 个文件（`banking/yarn.lock`、`.../total_stock_value.json`）mtime 仍为 **2026-09-18 16:10**，非本次造成（与 V-16 报告一致）。`Reference/zelin-tech-erpnext_china/` 工作区干净、只读使用。

### V-19（SA 步附属探针已验）

**1. 验证深度与未触及的边界**

已触及：

- **三段全跑，且 `go` 不是靠 happy path 拿到的**。第一段（建表）之外，另跑了重复 `on_update`、第二家公司同表、以及错误路径三个边界，其中错误路径**查出两处实质缺陷**（下节）。判定取 `go` 是因为命题问的那两件事（能否建出完整中式科目表 / 相对原生多出少掉哪些副作用）在四项边界里三项通过，且失败那项有明确的触发条件与可规避性 —— 但**失败那项本身必须进 D 步的"要自己补"清单**。
- **建表结果做的是双向集合差与父子边比对，不是抽查**。266 个节点逐对 `(account_number, account_name)` 两个方向都比、父子边（`(子号, 父号)`）两个方向都比、`is_group` 与 `account_type` 逐条比 —— 全为空／0。这一步踩过一个坑并修掉：JSON 里号码是**无引号整数**、DB 列是 varchar，第一版脚本没归一化，得到"266 条两边都有差异"的假结果（`V19-seg1-a-company.py` 里那段差集已被 `V19-seg1b-setdiff.py` 取代，前者的差集字段不可引用）。
- **副作用对账是逐项 verdict，不是整体印象**。第二段把 V-18 那组原生数字写成脚本内的常量表，每项打印 `A / native_V18 / 相同或不同`，故"少掉一条 VAT"与"多出五个默认科目修正"都是机器比出来的，不是人眼看出来的。
- **`set_company_default` 是否真的覆盖了 erpnext 的错选，做了对照复现**。不止看最终值对不对，还在同进程里照抄 `company.py:425-434` 那组不带 `order_by` 的查询，确认 erpnext 仍会挑出 `2203 预收账款` / `2211010 职工工资`，即 A 案是"先挑错、再被覆盖对"，而不是"erpnext 在这张表上恰好挑对了"。
- **`round_off_account` 为何没修好定到了数据行**。不是"`set_company_default` 没跑"，而是 CSV 35 行里 14 行在本表查不到对应科目，`round_off_account` 那行写的 `财务费用-圆整差异` 不存在。这 14 行已逐行记进 `Spike/V19-out/seg2-side-effects.json` 的 `csv_rows_unresolved`。
- **flag 泄漏被当成独立变量单独跑了两遍**。第三段发现 `ignore_chart_of_accounts` 被置 `1` 后**全仓无任何复位点**，同进程建第二、第三家公司时它仍生效，于是错误路径与重复保存**各在全新进程里重跑一次**（`V19-seg3b` / `V19-seg3c`），两组结果都保留 —— 因为"泄漏的那组"才是脚本批量建公司或数据导入时真实会遇到的形态。
- **清理做了前置盘点再动手**。删之前先跑只读盘点（`V19-seg4`）确认三家公司各 0 GL、0 SLE、非 `default_company`／`demo_company`，任一门不过就整体不删；删后按 `%V19%` 搜九类 doctype 核残留，并扫了 `Company.on_trash` 不级联的孤儿税模板子行。

没触及：

- **HRMS 同钩子交互（LG-101）未验，即决策 5 最初要避的那个风险本身。** 本 bench `installed_apps` 只有 frappe／erpnext，**hrms 未装**，且用户明确指示本次不为此装 app。故"`Company.on_update` 上多 app 的钩子并存时，zelin 那条 `not exists Account` 守卫与 hrms 自己的 Company 钩子谁先跑、会不会互相吃掉对方的前提"**完全未测**。A 案把三个钩子挂到 `Company` 上正是这条风险的落点，**装 hrms 之后须重验本命题的第三段**。
- **`existing_company` 分支未验。** 本次三家公司都是从 chart 模板建的，无一家带 `existing_company`。zelin 的 `erpnext_china_create_charts` 把该参数直传给自己的 `get_chart`，后者在 `existing_company` 非空时走 `get_account_tree_from_existing_company` —— 这条路径**零实测**。父子公司（集团架构）建账会走它。
- **未验另外两份中式科目表**。只验了 `小企业会计准则(2024)`；`一般企业会计准则(2024)`、`民间非营利组织会计制度(2025)`（均在 zelin 的 `china_coa` 列表里）未建过。三份表的节点结构不同，`account_category` 那处缺陷是否也在它们上触发，未知。
- **未验并发与体量**。单进程顺序建三家、266 节点，无并发。多进程同时建公司时 `frappe.local.flags` 各自独立、但 `rebuild_tree("Account")` 是全表操作，互相干扰与否未测。
- **未验前端呈现**。全程在 DB 层比对，没开浏览器看桌面上科目树、默认科目字段、税模板下拉的实际显示（V-10／V-12 记载过前端另有坑）。
- **未验 `after_install` 路径下的 `set_company_default`**。按任务书，`after_install`（税模板＋默认科目那一套）由 V-18 第二段覆盖、本次不重跑；本次只走公司创建路径。A 案的 `hooks.py` 在抄进测试 app 时**故意没抄 `after_install`**，这是有意的范围限制，不是遗漏。
- **未验升级边界**。`company.py:346`／`:355`／`:425-434` 与 `chart_of_accounts.py:281` 的 `get_chart_metadata_fields()` 都是 v16 具体实现；`account_category` 那处缺陷的触发条件（上游元数据字段数 8 vs zelin 硬编码 7）**会随上游加字段而变化**，换 erpnext 版本须重验。

**2. 探针与真实场景的差距**

- **环境**：容器 `erx001-frappe-1`，站点 `erx.localhost`，frappe `16.34.0` / erpnext `16.35.0`，Python 3.14，MariaDB，`developer_mode=1`。`installed_apps` 跑时为 `['frappe','erpnext','erx_v19']`，**hrms 未装**（差距见上节第 1 条）。
- **测试 app 是手搓的，不是 `bench new-app` 产物**（沿用 V-16／V-18 的做法与已知差距：本 bench 无 `flit_core`，`bench new-app` 的 `pip install -e` 跑不通）。经 `.pth` 进 `sys.path`，`sites/apps.txt` 整份重写。这对本命题的判定无影响 —— 判定依赖的是 `doc_events` 钩子生效与否，实测 `frappe.get_hooks("doc_events")["Company"]` 三个钩子全在。
- **app 名不同是唯一的代码改动**。`erpnext_china` → `erx_v19` 的模块前缀（`doc_events.py` 两处 import、`custom_account.py` 两处自定义 chart 路径）。其余**字节相同**：`utils.py` 与 zelin 原文件 md5 一致，三个数据文件（`default_accounts.csv` / `tax_template.json` / `tax_rule.csv`）与 chart JSON 的 md5 亦逐个核过。**没有修 zelin 的任何缺陷**（`tax_template.json` 那两个错科目号、`account_category` 缺失、`log_error` 误用全部原样保留）—— 这是有意的，探针要测的是"原样抄进来会怎样"。
- **`hooks.py` 有一处有意的删减**：未抄 `after_install`。见上节"没触及"最后一条。
- **数据**：站点为已恢复的演示数据；跑前另做备份 `20260925_185058`（`docker/backup.sh`，含 files）。基准公司 `华东弹簧` 全程只读，跑前跑后逐项核过。
- **复查法**：先 `bash Spike/V19-setup-test-app.sh`（容器内，装 app），再按 `seg0` → `seg1` → `seg1b` → `seg2` → `seg3` → `seg3b` → `seg3c` → `seg4` → `seg5` → `seg6` 顺序跑。**`seg3b` / `seg3c` 必须是独立进程**（它们测的就是 flag 起始为 `unset` 时的行为，合进 `seg3` 会得到另一组结论）。
- **`seg3` 第三段那组"崩"的结果依赖进程内状态**，复现须在同一进程里先建至少一家中式公司。单独跑 `seg3b` 得到的是"成功"那组。两组都真实，区别只在 `ignore_chart_of_accounts` 的起始值。
- **未跑 `bench build`**。本次无前端资源，`assets.json` 无 `erx_v19` 条目（已核）。
- **无并发干扰**：容器独占，`ps` 只有一个 `bench serve`；清理后已重启它（`.pth` 只在解释器启动时读，不重启的话旧进程仍带着 app 的 `sys.path`），`/api/method/ping` 返 200。

**3. 拿不准处**

- **`go` 的判定边界在哪里，请复核人自行掂量。** 四项边界里三项通过、第三项在"同进程内先建过中式公司"时崩。判 `go` 的理由是：命题问的是"能否建出完整中式科目表"与"副作用多出少掉什么"，这两问都有确切答案（能，且逐项一致；少一条 VAT、多五个默认科目修正）；错误路径的崩发生在**配置本就不该出现的组合**上（`country='China'` 却选 `Standard`）。但**若复核人认为"同进程连续建公司会崩"本身就够触 `no-go`，本探针不反对** —— 事实已全部列出，判定值取哪个是复核人的裁量。
- **`ignore_chart_of_accounts` 全仓无复位点这件事的严重性不由本探针判断**（纪律 5）。只报事实：`company_before_insert` 与 `company_on_update` 各置一次，本项目／erpnext／frappe 全仓无任何地方把它置回；一个进程内建第二家公司起，erpnext 自己的建账分支（`company.py:346`）就永远被跳过。桌面 UI 每个请求一个新进程上下文，故单人手工建公司不受影响；`bench execute`、数据导入、`Chart of Accounts Importer`、批量脚本会受影响。
- **`account_category` 那处缺陷的影响面未穷举。** 已确证：zelin 硬编码的跳过清单 7 键、上游 `get_chart_metadata_fields()` 实为 8 键、`Standard` 表节点带 `account_category` 故触发。**未测**：三份中式表的节点带不带 `account_category`（本次那份不带，否则第一段就崩了）；也未测 `Chart of Accounts Importer` 产出的表带不带。即"只在选 `Standard` 时崩"是本次观察，不是已证的全集。
- **`log_error` 误用 6 处是读码＋一次实触**。`custom_account.py:97` 那处已实测抛 `TypeError`（在 `seg3` 的 traceback 里），另 5 处（182／198／217／236／254 行，对应 zelin 原文件 173／189／208／227／245）是同一写法、**未各自触发过**。它们都在 `except` 分支里，即"出错时连日志都写不下"这一后果对 6 处成立，但只有 1 处有实测栈。
- **`Financial Report Template` 这一项与命题预判相反，成因已查明但请复核。** 任务书预判"那 6 条财报模板很可能一条都没有"，实测站内仍 6 条 —— 因为该 doctype **没有 `company` 字段**（已核 `frt_has_company_field` = `false`），那 6 条是站级模板，`sync_financial_report_templates` 被跳过不减少站内条数。故这一项**不构成 A 案的缺口**。但"站级模板对中式科目表取数对不对"是另一个命题，本探针没测。
- **清理时顺带删掉了 4 条与本次无关的历史孤儿数据**：`Company.on_trash` 用裸 `frappe.db.sql` 删税模板父表、不级联子表，本次扫 `Item Tax Template Detail` 孤儿子行时一并清掉了 `China Tax - V18B`（V-18 残留）、`China Tax - ERX`、`China Tax - ERXD`（更早的探针残留）这 3 条，加本次的 `China Tax - V19C` 共 4 条。销项／进项孤儿子行各 11 条全是本次的。删后三类孤儿均为 0。**这一步扩大了本探针的写入范围**，如认为不该动那 3 条历史残留，请记一笔。
- **测试公司与测试 app 均已清理并逐项核验**：三家公司删除后站内 `Account` 回到 **95**、公司只剩 `华东弹簧`、`Tax Category` 与 `Tax Rule` 归 0、按 `%V19%` 搜九类 doctype 全空、NSM 坏行 0、`Error Log` 仍 1 条（且是 2026-09-21 那条旧的）；`erx_v19` 已 `uninstall-app`，`Module Def 'Erx V19'` 与 `tabInstalled Application` 均已无该行，目录／`.pth`／`sites/assets/erx_v19` 已删，`apps.txt` 经 `od -c` 核为 14 字节 `frappe\nerpnext` 无尾换行。**上游源码未改**：`apps/frappe` 工作区干净，`apps/erpnext` 有 2 个文件显示 modified，但 `git diff --ignore-cr-at-eol` 为**空**（纯 CRLF 差异）且两文件 mtime 为 **2026-09-18**，早于本次探针一周，与本次无关；`Reference/` 工作区干净。
