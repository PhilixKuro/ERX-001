# P1-S2-R1-A待验表

> 发起步骤：P1-S2-R1 A 步（图谱讨论）。前三列由 shape 写，后三列由 spike（SA 步）填回。
> 格式与纪律见 [../../../流程体系/交接契约.md](../../../流程体系/交接契约.md)。

| 编号 | 待验命题 | 阻塞否 | 判定 | 实际观察 | 探针代码 |
|------|---------|--------|------|---------|---------|
| V-01 | 中国本地化能否以「新建自有 app + ERPNext hook」方式接入，**不改 erpnext/frappe 源码**——即 `erpnext/regional/` 下既有国家（australia / italy 等）的接入点是否全部是 hook 或可被 app 覆盖的配置，无一处依赖改动 erpnext 本体 | 阻塞 | go | **六国实现所依赖的接入点无一处要求改 erpnext 本体。**<br>**核心机制是 hook**：`erpnext/__init__.py:135-154` `allow_regional` 装饰器在 `:145` 读 `frappe.get_hooks("regional_overrides").get(get_region())`，`:152` 取 `[-1]`（末位安装的 app 胜出）。全仓 **20 个** `@allow_regional` 覆盖点，含 `sales_invoice.py:2654`/`purchase_invoice.py:2092`/`payment_entry.py:3613` 的 `make_regional_gl_entries`、`taxes_and_totals.py:1285` `update_itemised_tax_data`、`:1291/:1296` 税额拆分、`accounts_controller.py:4466` `validate_regional`、`:4476` `update_gl_dict_with_regional_fields`、`party.py:308` 地址取值、`buying_controller.py:1336` 采购估值（清单见探针 md）。`get_region()`（`__init__.py:120-132`）取 `Company.country`，实测站点 `country='China'`。<br>**分派实测**（注入 hooks 缓存模拟装了 app）：覆盖前 `update_itemised_tax_data()` → `None`；注入后 → `'CN-OVERRIDE-RAN'`，app 侧函数命中且收到原参数 `('first','Sales Invoice')`；两 app 同 target → `'SECOND-APP-WON'`（末位胜出）；`get_region()` 改 Italy → 覆盖不生效（按国家隔离）；`sales_invoice.make_regional_gl_entries` 覆盖后返回 `['CN-GL-HOOKED']`。<br>**其余接入点形态**：`doc_events`（`hooks.py:382-404`，italy/uae 挂 SI/PI/Address）是 hook 可叠加；Custom Field 用公开 API `create_custom_fields`（italy/setup.py:8,26）；权限用 `frappe.permissions.add_permission`（:9）；uae 的 `UAE VAT 201`、us 的 `IRS 1099` 就是 app 自带普通 DocType/Report；`financial_report_template/` 目录按 `frappe.get_installed_apps()` 扫描（`financial_report_template.py:146-155`），app 可投放且 COA 里 `disable_default_financial_report_template` 能屏蔽 erpnext 自带模板（:139-144）。<br>**四处不是 hook（如实记下）**：① `install_country_fixtures()`（`company.py:858-861`）硬编码 `module_name = f"erpnext.regional.{scrub(country)}.setup.setup"`；② `update_regional_tax_settings()`（`taxes_setup.py:120-125`）同样拼死路径；③ `country_wise_tax.json`（`taxes_setup.py:16-21` 读死文件，China 条目现为 `{"China Tax":{"account_name":"VAT","tax_rate":17.0}}`，17% 已过时）；④ 科目表 json 目录（`chart_of_accounts.py:120-124`、`:145-160` 用 `os.path.dirname(__file__)`，不扫 installed_apps）。**但四处均非"必须改源码才能实现该功能"**：①②可挂 `doc_events["Company"]["after_insert"]` 自办（实测 `doc_events["Company"]` 现为 `{}`，无冲突）；③不依赖它、自建 Tax Template（V-04 已实测可表达）；④覆盖 whitelisted 方法（V-03 已实测）。<br>**附带门禁**：`frappe.get_attr`（`frappe/__init__.py:1129-1133`）拦「模块所属 app 未安装」，故覆盖函数必须住在真正 install 的 app 里——这是自有 app 方案的前提而非障碍。 | Spike/V01-regional-hook-points.md<br>Spike/V01-regional-hook-points.py<br>Spike/V01b-hook-dispatch-runtime.py |
| V-02 | 中国会计科目表（`unverified/cn_l10n_chart_china.json`，82 平铺节点、`root_type` 全空）整理为可用模板的工作量：补 `root_type`/`account_type`/`account_number` + 按五大类重组 + 清理废止科目（营业税等），是否 ≤ 3 人日 | 不阻塞 | 无法判定 | **工作量的客观计数已测准，但"≤3 人日"判不了——人日折算取决于执行者对中国科目表的熟悉度，探针无从测量。以下交计数与实测报错，不折算工时。**<br>**现状实测**：82 顶层节点 / 全部 103 个科目节点 / 最大层级 4；`root_type` 已填 **0** 个、`account_type` **0** 个、`account_number` **0** 个；82 个顶层里**只有 1 个**（`应交税费`）有子科目，其余 81 个全平铺。`country_code=cn`，无 `disabled` 字段。<br>**拿现状直接建公司会硬失败**（`create_charts(custom_chart=...)` 实跑）：`ValidationError: The root account 主营业务成本 - PCC must be a group`（`account.py:249` `validate_root_details`）——因 81 个平铺节点被当作 root 且 `identify_is_group()`（`chart_of_accounts.py:90-98`）判其无子节点即 `is_group=0`，而 root 必须是 group。**故这不是"能用但不好看"，是根本建不出来。**<br>**要动多少处（可核对）**：① `root_type` 实际只需给**顶层**赋值——`create_charts` 的 `_import_accounts` 在 `:72` 以 `root_account=True` 入口，`:23-24` 仅 root 层读 `child.get("root_type")`，`:67` 递归时把 root_type 透传给子级，即子科目继承父级；重组成 5 大类后**只需 5 处**，维持现状则 82 处。② 按五大类重组：需建 资产/负债/权益/收入/费用 5 个 root + 中间层，把 82 个节点归位（这是主要工作量，也是①从 82 降到 5 的前提）。③ `account_number`：103 个节点全要编号，财会[2006]3号有标准编号可照抄。④ `account_type`：只有语义科目需指定（现金/银行/应收/应付/存货/税金/固定资产/累计折旧/成本等），按 ERPNext 的 `account_type` 选项（30 个值）约 20-30 处；**必须包含 Receivable 与 Payable**，否则 `create_default_accounts`（`company.py:425-435`）取不到 `default_receivable_account`/`default_payable_account`。⑤ 删废止科目：`应交税费>应交营业税` 与顶层 `营业税金及附加` 两处（营业税 2016 年已全面改征增值税）。<br>**对照已 verified 的国家模板**（同口径实测）：`ar` 5 顶层/264 节点/`root_type` 5 填/`account_number` 264 填；`au` 8/235/8/235；`be` 9/425/9/414 且 `account_type` 填 318 处；`ae` 6/281/6/**0**（编号可留空）。即：**顶层只有 5-9 个、子节点几百个、编号基本填满**，中国这份的形态（82 个平铺顶层、元字段全空）与已验模板差距在"结构"而非"条数"。<br>**已有可利用部分**：`应交税费>应交增值税` 下已含 进项税额/销项税额/进项税额转出/转出未交增值税/未交增值税/已交税金/减免税款/出口退税/出口抵减内销产品应纳税额/销项税额 共 10 个子目，层级正确，这部分不用重建（V-04 的进项/销项分离直接用得上）。<br>**计数之外还需**：改完实际建一次公司，核 `create_charts` 不报错、`default_receivable/payable_account` 能自动取到、资产负债表与利润表能出数——这一步本探针只对"现状"跑了（失败），对"改好后"未跑。 | Spike/V02-cn-coa-workload.py<br>Spike/V02b-cn-coa-import-attempt.py |
| V-03 | 自有 app 能否让自制科目表模板出现在建公司时的下拉里——即 `get_charts_for_country()`（`chart_of_accounts.py:147-149` 默认只扫 `verified/`）是否可被 app 侧扩展或覆盖，**无需改 erpnext 源码** | 不阻塞 | go | **下拉可被 app 覆盖，实测生效；但"选中后能建出科目"需连 `get_chart()` 一起覆盖，这一步未实跑。**<br>**原生行为实测**：`get_charts_for_country('China')` → `['Standard','Standard with Numbers']`，中国模板不在列（它在 `unverified/`，`chart_of_accounts.py:145-152` 默认 `folders=("verified",)`）。置 `frappe.local.flags.allow_unverified_charts=True` 后 → `['China - 中国会计科目表  （财会[2006]3号《企业会计准则》）']`，即该 flag 是现成开关，app 可在自己的 hook 里置位。<br>**覆盖链路成立**：建公司表单的下拉来自 `company.js:264` 的 `frappe.call("erpnext...get_charts_for_country")`；该调用经 `handler.py:65-66` `execute_cmd()` 首行 `cmd = frappe.override_whitelisted_method(cmd)` 解析，而后者（`frappe/__init__.py:1577-1580`）读 `override_whitelisted_methods` hook 并取 `[-1]`。实测 `get_charts_for_country` 确在 `frappe.whitelisted` 集合中；注入 app 侧 override 后 `override_whitelisted_method()` 返回 `cn_coa_probe.get_charts_for_country`（未注入时返回原路径），调用它得 `['ERX 中国科目表（自有 app 提供）','Standard','Standard with Numbers']` —— **自制模板进了下拉，未改 erpnext 源码**。<br>**走不通的那条路（排除掉）**：把 json 放进自己 app 不会被扫到——`get_charts_for_country` 与 `get_chart` 的目录都写死为 `os.path.join(os.path.dirname(__file__), folder)`（`chart_of_accounts.py:123`、`:151`），只认 erpnext 包内的 `verified/`/`unverified/`，不遍历 `installed_apps`。<br>**留的缺口**：下拉只管"选项可见"。选中后建科目走 `Company.create_default_accounts`（`company.py:419-423`）→ `create_charts(company, chart_name)` → `chart = custom_chart or get_chart(chart_template)`（`chart_of_accounts.py:16`）。`get_chart` 同样是 `@frappe.whitelist()`（`:101-102`）但**由服务端内部直接调用、不经 `execute_cmd`**，故 `override_whitelisted_methods` 对它无效。app 侧要让自制模板真建出科目，需改走 `create_charts(custom_chart=<自己的 tree>)`（该参数存在，`:13-16`）或 `Chart of Accounts Importer`（`chart_of_accounts_importer.py:502,521`），或在 Company 的 hook 里自行建科目。**这条替代路径本探针只确认了参数与入口存在，未实跑建公司。** | Spike/V03-coa-dropdown-override.py |
| V-04 | 中国增值税逻辑（进项/销项分离、多税率档位、价税分离取值）能否用 ERPNext 原生 `Sales Taxes and Charges Template` / `Purchase Taxes and Charges Template` + `Item Tax Template` 表达，无需自有 DocType 与自定义计税代码 | 不阻塞 | go | **三项要求全部用原生机制实跑通过（在事务内建临时 Item Tax Template 试算，结束 rollback）。**<br>**① 价税分离**：靠 `Sales Taxes and Charges.included_in_print_rate`（"Is this Tax included in Basic Rate?"）。实测含税单价 113 + 13% + `included_in_print_rate=1` → `net_rate=100.0`、`net_amount=100.0`、`net_total=100.0`、`tax_amount=13.0`、`grand_total=113.0`，**100/13/113 拆分正确**。价外税对照：不含税 100 + 13% → `net_total=100.0`、`tax=13.0`、`grand=113.0`。<br>**② 多税率档位**：靠 `Item Tax Template` 逐行覆盖表头税率。实测同一单两行分别挂 13% 与 6% 的 Item Tax Template（表头 Template 仍是 13%）→ `items[0].item_tax_rate={"VAT - HDS":13.0}`、`items[1].item_tax_rate={"VAT - HDS":6.0}`、`net_total=200.0`、**`tax_amount=19.0`**（=13+6，逐行档位生效）、`grand_total=219.0`。含税录入叠多档位同样正确：113(13%)+106(6%) 且 `included_in_print_rate=1` → `net_total=200.0`、`tax=19.0`、两行 `net_rate` 均 100.0。<br>**⚠ 一处反直觉，实现时会踩**：直接给 `item.item_tax_rate` 手填 JSON **无效**——`calculate_taxes_and_totals` 在 `taxes_and_totals.py:84` → `:144-150` `update_item_tax_map()` 会用 `get_item_tax_map(tax_template=item.item_tax_template)`（`get_item_details.py:941-956`）**重算并覆盖该字段**。首次试算即因此得 26.0（两行都吃了表头 13%）而非 19.0。必须走真的 `Item Tax Template`，取数逻辑在 `:397-404` `_get_tax_rate`（`tax.account_head in item_tax_map` 则用行内税率，否则用表头 `tax.rate`）。<br>**③ 进项/销项分离**：`Sales Taxes and Charges Template` 与 `Purchase Taxes and Charges Template` 是两个独立 DocType，各自 taxes 行的 `account_head`（均 `Link→Account`、`reqd=1`）指向不同科目即可分离。进项侧实跑 `Purchase Invoice` 100 + 13% → `net_total=100.0`、`tax=13.0`、`grand=113.0`。科目侧现成：中国科目表 `应交税费>应交增值税` 下已含 进项税额/销项税额/进项税额转出/未交增值税 等 10 个子目。`Purchase Taxes and Charges` 另有 `category`（Valuation and Total/Valuation/Total）与 `add_deduct_tax`（Add/Deduct）可控进项是否进成本。<br>**原生 Template 表达不了、需另想办法的（边界，非本命题否定项）**：进项税额转出与未交增值税月末结转（属期末账务，需 Journal Entry 或自有逻辑）；差额征税/简易计税/免抵退（不是税率问题）；发票号与发票代码等票面字段（需 Custom Field，属 V-05 范畴）。小规模纳税人 1%/3% 征收率只是档位，Template 可表达。<br>**未触及**：未提交任何单据、未验 GL 分录借贷方向与税金科目落账是否符合中国习惯（试算只到 `calculate_taxes_and_totals`，未走 `on_submit`→`make_gl_entries`）。 | Spike/V04-cn-vat-native-template.py<br>Spike/V04b-multi-rate-item-tax-template.py |
| V-05 | 增值税专用发票开票与金税盘对接的**现实可得性**：主流服务商（航信 / 百望 / 诺诺等）的开票接口是否需要企业资质或商务签约才能申请到测试环境——即本项目现阶段能否自行完成技术验证 | 不阻塞 | go | **测试环境不需要企业资质，本项目现阶段可自行做技术验证；但"真开出一张专票"必须有资质。命题按"测试环境"问 → 不需要。**<br>**实测（2026-09-22，经本机代理 127.0.0.1:7897）**：诺诺（航信系）沙箱端点 `https://sandbox.nuonuocs.cn/open/v1/services` 对**未签约、未认证的任意调用方**开放——`GET` 返 `HTTP=200`（0.32s）；空 `POST {}` 返 **`{"code":"070501","describe":"请求的API不存在"}`**，`HTTP=200`。**关键在这个错误码是业务层的**（"请求的API不存在"，因未带 `method`），不是 401/403/"未开通"/"请联系商务"——说明请求已进入其业务路由，平台**未在入口校验调用方资质**。<br>**文档侧（多个独立社区来源互相一致：cnblogs 对接实录、Gitee `nn-sdk` README、CSDN 系列）**：沙箱用**公开流传的共享测试凭据**（多篇给出同一组 appKey/appSecret），非申请制；配套测试税号 `339901999999142`（换 `339902999999789114` 可测纸票作废）；**沙箱下 `token`（access_token）可为空**——即不走针对真实纳税人账户的 OAuth 授权，这是沙箱无需企业实名的技术原因；沙箱支持**专票**与全电发票红冲测试。生产侧则一致指向：appKey/appSecret 来自在开放平台注册的自有应用，调用需真实 `salerTaxNum` 并授权一个已在平台开通开票能力的企业。**即企业实名与开票资质落在生产侧，不在沙箱侧。**<br>**⚠ 本探针主动放弃的一步**：未用那组社区流传的凭据签名发起开票调用——凭据不属本项目，以他人凭据访问第三方系统不做（工具侧亦拒绝执行）。故**"沙箱是否接受并正确处理业务请求"只验到协议层与错误码层，未成功开出测试发票**；签名算法、必填字段、返回报文结构均仅有文档描述、**未实测**。若要闭合，需本项目在开放平台自行注册取得自己的沙箱凭据。<br>**另一处未闭合**：诺诺（`open.nuonuo.com` 返 302 后为前端渲染 SPA）与百望（`pop3.baiwang.com` 同）的开放平台首页 curl 取不到注册表单字段，**未能从官方页面直接读到"自助注册要填哪些资质字段、是否卡在企业认证步"**。需真实浏览器走一遍。<br>**范围限制**：只验了诺诺沙箱端点；百望云、航信直连是否同样有开放沙箱**未测**。金税盘/税控设备本地对接路径（若客户仍用税控盘而非服务商 API）**完全未触及**。 | Spike/V05-einvoice-sandbox-access.md |
| V-06 | 中国财务报表格式（资产负债表 / 利润表 / 现金流量表的中国准则格式）能否用 ERPNext 原生报表配置（`Financial Statements` + 科目 `root_type`/`report_type`）产出，无需自写报表 | 不阻塞 | go | **实建了一张中国式资产负债表模板并跑出数，8 行全部正确映射到科目，未写一行报表代码。**<br>**⚠ 命题前提需更新**：v16 的报表配置**不止**靠科目 `root_type`/`report_type`，而是新增了 `Financial Report Template` —— 一个声明式的"行 + 公式"引擎，表达力远高于命题设想。`balance_sheet.py:31-33`：`if filters and filters.report_template: return FinancialReportEngine().execute(filters)`，即模板存在就完全接管出数。<br>**表达力（实测 DocType 元数据）**：`Financial Report Template.report_type` 可选 `Profit and Loss Statement` / `Balance Sheet` / **`Cash Flow`** / `Custom Financial Statement` —— **现金流量表是原生 report_type 之一**。`Financial Report Row` 的 `data_source` 可选 `Account Data`（按条件取科目数）/ `Calculated Amount`（行间公式）/ `Custom API` / `Blank Line` / `Column Break` / `Section Break`；`balance_type` 可选 `Opening Balance` / `Closing Balance` / `Period Movement (Debits - Credits)`；另有 `reference_code`（行号，供公式引用）、`calculation_formula`、`indentation_level`、`reverse_sign`（方向）、`hide_when_empty`、`bold_text`。自带 IFRS 资产负债表模板 53 行，取数写法如 `["account_category","=","Trade Receivables"]`，合计行写法如 `CA100 + CA200 + CA300 + CA400 + CA500 + CA600`。<br>**实跑**：建 8 行模板（货币资金 `["account_type","in",["Cash","Bank"]]`、应收账款 `["account_type","=","Receivable"]`、存货 `["account_type","=","Stock"]`、流动资产合计 `A100+A200+A300`、应付账款与应交税费两行带 `reverse_sign=1`），跑 `Balance Sheet` 报表 → **列数 5、行数 8**，各行 `child_accounts` 实际命中站内科目：货币资金→`['现金 - HDS']`、应收账款→`['应收账款 1 - HDS']`、存货→`['存货 - HDS']`、应付账款→`['员工预支 - HDS','应付账款 1 - HDS']`、应交税费→`['VAT - HDS']`。合计行与标题行正常出现。结束 rollback，模板残留 `None`。<br>**app 可投放模板**：`sync_financial_report_templates`（`financial_report_template.py:146-155`）遍历 `frappe.get_installed_apps()`，`_sync_templates_for` 扫每个 module 下的 `financial_report_template/` 目录，故外部 app 放 `<app>/<module>/financial_report_template/<name>/<name>.json` 即被收录（与 V-01 同一结论）；且 COA 里 `disable_default_financial_report_template=1` 可整体屏蔽 erpnext 自带模板（`:139-144`），避免中英两套模板并列。<br>**⚠ 实现时会踩的坑（两处，均已实测）**：① 报表 filter 键名是 **`report_template`**（`balance_sheet.py:32`），不是 `financial_report_template`——用错会静默返回 0 行而不报错，首次试跑即因此得"行数 0"。② 通过代码 `insert()` 建模板会触发 frappe 的 fixture 导出，**把 json 写进 `apps/erpnext/erpnext/accounts/financial_report_template/`**（本探针触发过一次，已删除并确认 erpnext 仓库 `git status` 干净）；建模板时需置 `frappe.flags.in_import = True` 抑制。<br>**未触及**：① **只建了资产负债表，利润表与现金流量表未建未跑**——`Cash Flow` 是原生 report_type 且自带 IFRS 现金流模板，但中国准则现金流量表的"经营/投资/筹资"三段分类能否用 `Account Data` 条件表达，**未验**。② **站点无 GL Entry（0 条）、无真实财年**，所以只验了"行结构与科目映射正确"，**没验金额算得对不对**（跑的是 `_Test Fiscal Year 2050`，全零）。③ 中国报表的"年初余额/期末余额"双列格式未验（`balance_type` 有 `Opening Balance` 应可表达，未试）。④ 未验附注、未验导出 Excel 的版式是否符合报送要求。 | Spike/V06-cn-financial-statements.py |
| V-07 | `PH-P1002` 的其余四例前端不刷新即不显示（仓库列表空白 / 工作区侧栏卡片缺失 / BOM 保存后「提交」按钮不出现 / `Job Card` 的 `time_logs` 残留空行）**是否同源**——四例是否共用同一个前端缓存或文档重载路径，修一处即四例同修 | 不阻塞 | no-go | **四例分属三条互不相干的路径，无公共缓存或重载点。分组 {1,5} / {2} / {3} / {4}。**<br>**① 仓库列表空白＝路由/视图选择，与第五例完全同源**：`warehouse.json:287` `is_tree=1`，目录下只有 `warehouse_tree.js` 无 `warehouse_list.js`（同 `Account`）。侧栏链接走 `utils.js:1531` `generate_route()` 的 `default:` 分支（`:1576-1577`）生成裸路由，因 `Workspace Sidebar Item` 字段清单无 `doc_view`（实测 21 字段）。**但 v16 有一层兜底 R6 未提到**：`router.js:223-231`，裸路由遇 `meta.default_view==="Tree"` 应改写为 `["Tree",doctype]`；实测站点 DB `tabDocType` 中 `Warehouse`/`Account`/`Cost Center` 的 `default_view` 均为 `Tree`（`force_re_route_to_default_view=0`）。另一入口 `list_view.js:7-22` `load_last_view()` 按 `user_settings.last_view` 重定向且**不看 `default_view`**，是空白复现的通道（`__UserSettings` 在服务端，故 `Ctrl+Shift+R` 无效）。数据层无恙——实测 `reportview.get("Warehouse")` 返 20 行（站内 85 条、17 条 `is_group`、0 `disabled`）。**顺带更正**：「`*_list.js` 缺失 ⇒ 列表空白」前提不成立，erpnext 641 个 doctype 仅 79 个 `*_list.js`，`Brand` 无 `_list.js` 亦无 `_tree.js` 而列表正常，该文件只是可选定制钩子。<br>**② 侧栏卡片缺失＝v16 架构变更＋死代码，刷新也永不出现**：v16 侧栏改由独立 DocType 驱动，`boot.py:170-173` → `boot.py:442-515` `get_sidebar_items()` 读 `Workspace Sidebar`/`Workspace Sidebar Item`，`sidebar.js:14,31-33` 只吃 `frappe.boot.workspace_sidebar_item`，从不读 Workspace 的 `content`。「物料与价格」只存在于 `buying/workspace/buying/buying.json` 的 `content`（8 张卡），**`erpnext/workspace_sidebar/buying.json` 的 32 项里没有它**——站点实测 `get_bootinfo()` 的 `buying` 侧栏 32 项确无该卡、且无"卡片"概念。且 `sidebar.js:305-309` `add_card()` **全仓（frappe+erpnext，js/py/html）零调用者**，`this.cards` 恒为 `[]`（`:22`），`add_sidebar_cards()`（`:311-316`）永远渲染 0 张。**故 R3「数据层三查正常却侧栏不显示」不矛盾——查的是 Workspace 页面那套数据，侧栏读的是另一套**，这也解释清缓存与无痕窗口均无效。<br>**③ BOM 提交按钮＝表单 dirty 状态**：开关在 `toolbar.js:680-689` `can_submit()` 的 `!this.frm.doc.__unsaved`（`:764-770` 据此分派 `"Submit"`）；服务端四项 R3 已排除，故只能是 `__unsaved` 未清。置位链路：`form.js:283-292` 注册 `frappe.model.on(doctype,"*")` 回调内 `me.dirty()`（`:1495-1496` 即 `__unsaved=1`，子表同理 `:316-330`）← `model.js:506-546` `set_value()` 的 `skip_dirty_trigger` 默认 `false` ← `bom.js:853-854,863-864,810-813,834-845` 成本重算全走 `set_value` ← `bom.js:866-868` `cscript.validate = update_cost`（`:796-800`）。时序见 `form.js:865-878` `run_serially([validate, before_save, save])` 与 `:843` `after_save` 的 `me.refresh()`。**未能实际复现（站点 0 Item/0 BOM），判定基于源码分析。**<br>**④ `time_logs` 空行＝服务端写入，根本不是前端问题**：`job_card.py:680-685` `add_start_time_log()` 用 `self.append(...)` + `row.db_update()` 旁路插库（调用链 `job_card.js:557-568` → `job_card.py:1823-1831` → `:643-678`）。`base_document.py:463-465` 给无 `name` 新行置 `__islocal=1`+`__temporary_name`，`:804-807` `db_update()` 对 `__islocal` 行直接 `db_insert()`（`:736-738` 才补 `set_new_name`）——**绕过 `self.save()` 的校验与 idx 重排，正是 R3 在 DB 见到 `new-job-card-time-log-*` 与 idx 重复(1,1,2,2) 的成因**（前端 `create_new.js:78-80` 产 `new-{doctype}-{hash}`，`model.js:631` 判该前缀）。读取侧 `job_card.js:615-622` 只看末行 `to_time`、不验该行是否有效，`:609-613` `should_show_start` 以 `!time_logs?.length` 为判据，空行双双骗过（R3 定位无误）。**写入侧在 Python，与前三例连同一层都不是。未能实际复现（站点 0 Job Card/0 Work Order），判定基于源码分析。**<br>**不能同修的原因**：要动的文件互不相交——① `utils.js`/`router.js`/`list_view.js` 或给 `Workspace Sidebar Item` 加 `doc_view`；② `sidebar.js` 补调用者或改 `workspace_sidebar/*.json` fixture；③ `toolbar.js`+`form.js` dirty 时序或 `bom.js` 的 `set_value` 用法；④ `job_card.py:680-685`+`job_card.js:615-622`。唯一公共点只是"用户感知为不刷新"。 | Spike/V07-frontend-refresh-paths.md |
| V-08 | `https://github.com/saoxia/erpnext_china` 是否以自有 app + hook 形态实现了可用的中国本地化逻辑，且其实现方式可被本项目借用（许可证允许、v16 兼容或可移植） | 不阻塞 | no-go | 财税本地化零实现：全仓检索 `chart_of_accounts`/`发票`/`金税`/`税控`/`balance_sheet`/`cash_flow`/`bank_reconcil` 均零命中（排除 translations）；唯一「税」相关代码是 `sales_order.py:21-26` 按硬编码字符串 `'P13专票含税'` 查一个需手工预建的原生 `Sales Taxes and Charges Template` 的方法，且全仓无调用方。实际实现的是中文 CRM 线索自动分配（9 个自建 DocType + 991 行）、中国 HR 字段（身份证解析、社保公积金字段但无计算引擎）、企业微信登录与通讯录、9221 行 zh.csv、422 行三级行政区划。29 个自建 DocType 无一涉财税。接入机制：标准 Frappe app，用 13 类 hook（`override_doctype_class` 6 个、`doctype_js`、`doc_events`、`fixtures`、`permission_query_conditions`、`scheduler_events` 等），磁盘上未篡改上游源码，但 `install_fixtures.overwrite_workspace()` 靠 6 层 `.parent` 爬进 `apps/frappe`、`apps/erpnext` 读 17 个 workspace JSON 做字符串替换再全量 `save_page`，硬依赖上游目录布局与英文文案。许可证：根 `license.txt` 为 MIT 但版权行是未填占位 `Copyright (c) [year] [fullname]`，多个源文件头标 GPL v3（`install_fixtures.py`、`lead.py`、`employee.py`）与之冲突。版本：Dockerfile 硬编码 `FRAPPE_BRANCH=version-15`/`ERPNEXT_BRANCH=version-15`，README 只提 v15 已测、v14 理论兼容，测试基类用 v15 的 `FrappeTestCase`，无 v16 证据。活跃度：最后功能提交 2025-01-21，此后仅两次文档与依赖改动，只有 `develop` 分支无 tag。29 个 `test_*.py` 全为 9 行空壳，无 CI。`utils/old_system_data.py` 含 33727 个真实手机号与 10 个 `@zhushigroup.cn` 员工邮箱，被 `lead.py:5` import 用于线索查重；另有 `employee = 'HR-EMP-00002'` 硬编码组织树根。详情见 `P1-S2-R1-A参考项目-saoxia.md` | 无（只读调研，未写探针） |
| V-09a | 同左 | 不阻塞 | **no-go**（不可当译名方案基线，可当词汇素材） | **四条已知缺陷只解决第 4 条**：缺陷 1（`Setup`/`Settings` 都译「设置」）未解决，且它多加 `ERPNext Settings,设置` **把二重撞名变成三重**；缺陷 2（`Accounts Receivable`/`Debtors` 都译「应收账款」）未解决且**范围更宽**——该目标词被 5 个源词占用；缺陷 3（`Opening & Closing`→「POS机交接班」）与官方 v16 逐字相同，**而它同时收了正确的 `Opening and Closing,开账与关账`**；缺陷 4（`Item`/`Accounts Setup`/`Sales Taxes` 未译）**已解决**。缺陷 2、3 核实为从官方 `erpnext/locale/zh.po`（`:2244`/`:15827`/`:33973`）继承，2026-08-08 的 v16 重刷未碰。**`context` 用了 32 条（0.17%）**，选点准、格式正确（填 DocType 名），说明作者懂该机制——**但 `context` 解不了缺陷 1、2**（见下方判读更正）。形态：`translations/zh.csv` 18297 唯一 source + `locale/zh.po` 56 条，靠 `translate.py:172-187` 按 app 顺序后装覆盖先装，**不经 `Translation` DocType**。**是自带全量表非官方增量**：与官方 14330 条基线比对——完全一致 13503（74%）、**覆盖官方仅 748（4%，自主价值所在）**、官方没有的 4046（多为 HRMS）。机械扫出同类撞名（同一目标词 ≥2 源词）**共 914 组**（此为本项目译名工作量的实测量级）。**四条确定译错**：`May`→`04`（月份整组译数字，5 月与 Apr 重复，图表轴与报表月份列 5 月显示成 4 月）、`Work In Progress`→「进行中」（WIP 是在制品，WIP 仓库那一路全错）、`Committed`→「已提交」（库存已占用量与单据 Submitted 混同）、`Ledger`→「会计凭证」（账簿与凭证语义拉平）；另 `Request for`/`Requesting Site`→`仓库` 张冠李戴、`Amortization` 缺失。主干质量好（占位符丢失 0 条）。 | docs/.../P1-S2-R1-A参考项目-zelin-翻译.md |
| V-09b | 同左 | 不阻塞 | **go**（账务侧真做了，可作实践参考；但四处配置缺陷不可照搬） | **与 saoxia 截然相反——真做了财税且财税就是其主体**，saoxia 的零命中清单在此几乎全转命中。**账务侧有，票据侧全无**：科目表**有**（4 份中国准则 JSON，190–353 科目，格式同原生 verified）／增值税**部分**（7 个 Tax Category，命名 `P{税率}{票种}{含税/未税}`，覆盖 13/3/1/0 四档，进项销项分离靠模板挂不同 `account_head` 做到）／财务报表**有**（代码量最大：**中国习惯的左右双栏**资产负债表 + 利润表带 `amount_from` 指定借贷方取数 + **现金流量表做成可提交单据**而非 Report、从 GL Entry 拉现金银行科目流水即直接法正确做法、四级优先级自动打编码、校验拆分和等于总账原值、22 条 Cash Flow Code fixture）／**发票·开票 0 命中**（发票/普票/fapiao/开票/电子发票）／**金税·税控 0 命中**（金税/税控/航信/百望/诺诺）／**银行对账 0 命中**。**建公司能选到中国科目表**：`hooks.py` 覆盖 **4 个** whitelisted 方法（`get_charts_for_country`/`get_chart`/`get_coa`/`get_all_nodes`）指向 `custom_account.py`，扫完原生 `verified/` 后再扫本 app 目录——**此即 V-03「点了能用」那半步的解法**。**四处已验证缺陷（全在配置数据层、会静默上线）**：① `小企业会计准则(2024)` 两个 13% 销项科目号错（实际 `2221005`，写成 `222105`/`22210005`，脚本遍历确认均 NOT FOUND）；② `一般企业会计准则(2024)` 挂过渡科目（`待转销项税额` 而非应交增值税明细，**根因是该 COA 只给这几个标了 `account_type: Tax`、`应交增值税`(22210010) 的 `account_type` 为空串**）；③ Cash Flow Code 无公司维度；④ **示例配置与所有随包科目表都对不齐**（144 个引用科目号命中率：小企业 119/144、小企业2024 54/144、民非 19/144、**一般企业2024 0/144**），且利润表示例税金明细行**系统性错位 7 处**（label「其中：消费税」引用 222103 实为预交增值税等）。**放大器**：`setup_tax_template`/`setup_tax_rule`/`set_default_accounts`/`set_item_group_account` **全包在裸 `except` 里只写 log，失败不中断建公司**。**PII 干净**：`1[3-9][0-9]{9}` 全仓 **0 命中**（saoxia 33727），无数据倾倒文件；唯一真实公司名在 `fin_profit_and_loss_statement.py:356-367` 的 `"""for testing"""` 三引号串内（字符串字面量非可执行，且同段 import 路径错、佐证从未执行）。**许可证有矛盾且位置要命**：根 `license.txt` 写 MIT 但 copyright 行是未填占位 `[year] [fullname]`；抽查 25 处文件头，`chart_of_accounts/custom_accounts/custom_account.py:1-2` 标 **GPL v3**（复刻 erpnext `chart_of_accounts.py` 连文件头搬来）——**而这正是「建公司能选到中国科目表」所依赖的文件**。**v16 风险最高的一点**：未见任何 v16 会计模块适配提交，而代码依赖 **4 处 erpnext 非公开内部函数**（`from_detailed_data`、chart_of_accounts 的 4 个、`get_rootwise_opening_balances`、`erpnext.accounts.utils` 三个），需对 v16 源码逐个核签名。**README 未提的破坏性动作**：预置 44 个中文 UOM 并**把清单外所有原生 UOM 一律禁用**（`install.py:69`）。 | docs/.../P1-S2-R1-A参考项目-zelin-财税.md |
| V-09c | 同左 | 不阻塞 | **go**（接入方式干净、不污染上游；但三处手法须避开） | **hooks 极度克制**：`hooks.py` 仅 52 行 / 7 个 hook——`after_install`、`setup_wizard_requires`、`app_include_icons`/`web_include_icons`（v16 新 hook）、`doctype_js`（3 个单据非全局）、`override_whitelisted_methods`（4 项全为科目表接入，其中 1 项覆盖 frappe 核心 `frappe.desk.treeview.get_all_nodes`）、`doc_events`（仅 Company 3 事件）、`jinja`。**明确未用 `regional_overrides`**（即 V-01 查明的正规接入点），亦未用 `override_doctype_class`/`fixtures`/`after_migrate`/`scheduler_events`；`patches.txt` 为空。**最有价值的事实：同一作者走完了 monkeypatch → 纯 hook 的迁移**——`e2a62c0`(2026-01) 曾引入 `monkey_patches/` 5 模块、**包装 `frappe.connect`** 遍历所有已装 app 的 `monkey_patches/` 自动导入（给整个 bench 建隐式 patch 协议），`59752c1`(2026-03) **整体删除、净减 319 行**，职责改由 `doc_events` + `override_whitelisted_methods` 承担，**迁移后 hook 集合反而更小**；当前 HEAD 全仓 `setattr`/`monkey`/`save_page` **零命中**。**不存在 saoxia 那种爬进 `apps/` 写上游的手法**——`custom_account.py` 两处用 `get_bench_path()` 读上游科目表目录但**只读不入库**，8 处 `open()` 全为读模式。**三处须避开**：① **复刻上游方法体 3 处**——`erpnext_china_create_charts` 复刻上游 `create_charts`，而上游已把字段列表抽成 `get_chart_metadata_fields()` 并**新增 `account_category`**，复刻版仍硬编码 7 项 inline list → 该字段静默丢失、带该键的叶子会被 `identify_is_group()` 误判 `is_group=1`（触发范围已 grep 收窄：其自带 4 张科目表不含该键，主路径不触发），另它把 `rebuild_tree` 包进 `try/except+log_error`、**建账失败被吞**；② `add_suffix_if_duplicate`/`identify_is_group` 被 import 后**又本地重定义**、影子覆盖；③ **`fixtures/` 三个 json 是死文件**（4 field + 49 setter + 287 行编码主数据，但 hooks.py 从无 `fixtures` hook、代码也不读），`setup/field_property.csv` 靠 `after_install` 代码 insert，**完全未用 `module/custom/{doctype}.json`** → 无任何一条 Custom Field 是 migrate 自动生效的声明式形态；且 `after_install` 整体包在 `if not frappe.is_setup_complete():` 下——**站点初始化后再装则全部中国默认值不生效**。唯一做对的是 `get_all_nodes`（5 行薄包裹、原样委派）。**版本号自身是乱的**：`pyproject` 声明 `>=15.0.0,<17.0.0`，`__init__.py` 的 `__version__='15.0.0'`；v16 实质落地有（icon hook、`install.py:set_v16_icon()` 用 `table_exists()` 做 v15/v16 双兼容、workspace json 加 `type`），残留 v15 写法：测试仍用 `FrappeTestCase`。**测试 4 个文件全是 9 行空壳、函数体 `pass`、版权头还是脚手架的 `Vnimy`**——与 saoxia 的 29 个空壳同构，**两项目都零有效回归测试**；无 CI，但有完整 `.pre-commit-config.yaml`（ruff + prettier）。**与 saoxia 不同源**：各自 `git cat-file -e` 对方 root commit 均 rc=1，19 个同路径文件只有 `license.txt` 内容相同，同名源于 `bench new-app` 脚手架，`zh.csv` 交集仅 319 行（约 3%）。**交叉确认（应 V-09a 请求）**：① workspace 标签**未回避撞名**——唯一 workspace 内两个 Card Break 的 label 是**裸英文 `Report`/`Settings`**、全靠运行时翻译（提交 `9e891c8 workspace label use english` 是有意为之，但动机是走翻译层不是回避撞名）；② **中国科目表里科目名是写死的中文字面量、不过翻译层**，故「两源词撞一目标词」路径不存在；但**同名父子结构存在于 3/4 张表**（一般企业2024 **13 处**含 `应收账款 > 应收账款`(11220/11221)、小企业2024 2 处、民非 4 处但应收段干净、`cn_sme_coa.json` 0 处）——**且不会触发官方那种追加数字 `1`**（`add_suffix_if_duplicate` 去重键是 `account_number + " - " + name.lower()`，科目号不同故键不冲突），**症状从「只差一个数字 1」变成「只差科目号前缀」**（`11220 - 应收账款` 是 group、`11221 - 应收账款` 才能记账）。 | docs/.../P1-S2-R1-A参考项目-zelin-机制.md |

| V-11a | 站点配置 `socketio_port`（9000）与 compose 宿主映射端口（9100）不一致，是否致浏览器 realtime 全程断连 | 不阻塞 | **go** | **命题成立，且已修复。** 修前：站点配置 `socketio_port: 9000`（`realtime/index.js:91-92` 据它 listen；`boot.py:166` 塞进 `frappe.boot.socketio_port`；`socketio_client.js:124` 与 `base.html:53` 据它拼 URL），但 compose 映射为 `9100:9000` → 浏览器按 9000 连宿主。实测宿主 `9000` → HTTP 000 不通、`9100` → 200 通；容器内 socketio 进程正常（`node apps/frappe/socketio.js`）。**故根因是配置与映射错位，非服务未起。** `netsh interface ipv4 show excludedportrange` 实测排除范围含 **8995-9094**，故 compose 原注释「9000 常落在保留段」属实，**不能把宿主映射改回 9000**。修法：两头同挪 9100——`socketio_port` 改 9100（`bench set-config --parse`，不加 `--parse` 会写成字符串）+ 映射改 `9100:9100` + 重建容器。修后实测：容器内 `:::9100 LISTEN 24/node`、宿主 9100 握手返 `0{"sid":"76duFqMeJ4dniKHQAAAF","upgrades":["websocket"],...}`（是真 socketio）、旧 9000 已 000。**用户浏览器实证：两个标签的表单自动同步，`ERR_CONNECTION_REFUSED` 与 `xhr poll error` 全部消失**（`socketio_client.js:153 throttled` 是正常节流日志非错误）。 | 无（配置修正，非探针代码）；改动落 `docker/compose.yaml` + 站点配置，备份 `/tmp/compose.yaml.bak` |
| V-11b | realtime 接通后，`PH-P1002` 的各例现象（仓库列表空白 / 工作区卡片缺失 / BOM 保存后「提交」按钮不出现 / `Job Card` 空行致状态错乱）是否消失或减少 | 不阻塞 | 待验 | — 须**实际重跑那组操作**才能判。**已确立的事实**：S1 全程实操都在 realtime 死的环境下做的（端口错位自环境搭建即存在，属 v15 时期遗留，而 S1-R3 的 23 环节实操与 R6 导航实操均在其后）。**但"形态吻合"不足以判定**——见讨论记录第 14 步③记下的失误形态（拿两个未验证的东西互相支撑）。**与 V-07 不矛盾**：V-07 判"四例源码路径互不相交"在其范围内成立，本条问的是它们是否共享同一个断掉的前置条件，两者可同时为真。 | — |
| V-12 | 侧栏头部 app 切换菜单拼图片 URL 时拿到 `undefined`（`sidebar_header.js:352` `add_app_item`），致每次加载侧栏即发一个 `GET /undefined` 404 请求——该缺陷的成因与影响面 | 不阻塞 | **go** | **命题成立。根因是上游 Frappe v16 的渲染遗漏：`icon_html` 有写入点、无读取点。** 设值侧 `sidebar_header.js:138-146` 与 `:153-161` 两处逻辑相同——`get_desktop_icon()` 有结果则设 `item.icon_url`，**否则走 else 设 `item.icon_html`**；而渲染侧 `:351-375` `add_app_item` 只处理 `item.icon`（→`frappe.utils.icon()`）与 `item.icon_url`（→`<img src="${item.icon_url}">`），**从不读 `icon_html`**。故走 else 分支的菜单项 `icon_url` 为 `undefined`，模板插值成字符串 `"undefined"` → 请求 `/undefined` → 404。**决定性证据**：`grep -rn "icon_html" .../ui/sidebar/` 只有 `:145`、`:160` 两行赋值、**零个读取点**。用户实测调用栈 `add_app_item@:352 ← populate_dropdown_menu@:346 ← constructor@:103` 与此吻合——`:103` 是 `dropdown_items.push(item)`，故出问题的是动态加进来的项（`sibling_workspaces` 一类），`:9` 那批硬编码项自带 `icon` 故不受影响。**影响面**：功能不受损（菜单可点、路由正常），仅图标渲染为破图占位 + 每个此类项 1 个 404 请求。**属上游缺陷，非本项目引入**（本项目未改过该文件）。与 V-11a 无关（修完 socketio 后仍在，用户二次实测确认）。 | Spike/V12-sidebar-undefined-404.md |
| V-13 | 工作区图表 widget 报 `"" is not a valid color`（`BaseChart.js:78`）与 `<rect> attribute width: A negative value is not valid. ("-40")`（`animation.js:55`），致演示时工作区首页显示破图或空图——是否为数据为空时的除零/负值计算，以及是否可由样本数据补齐消除 | 不阻塞 | 待验 | — | — |

## 命题来源

| 编号 | 来源 |
|---|---|
| V-01 ~ V-06 | 本 Round 第 2 步②（中国本地化处置）——用户裁决「先做完整，但先派子 Agent 深度测工作量」 |
| V-07 | 本 Round 第 2 步③（核心需求分级）——用户裁决「其它三个需要测，但等先把其它讨论完再测」 |
| V-08 / V-09 | 本 Round 第 5 步②——用户追加两个参考项目（`saoxia/erpnext_china`、`zelin-tech/erpnext_china`），要求看有没有能用的逻辑 |
| V-09a / V-09b / V-09c | 本 Round 第 16 步②——原 V-09 单条任务连续失败两次（heredoc 致命令断裂+API 超时；跑太久无响应被停），**用户要求把任务拆分、派多个 Agent**，故按主题拆三条 |
| V-11 ~ V-13 | 本 Round 第 15 步——用户按第 14 步末请求做浏览器实点，交回 F12 Console 内容，Claude 从中识别出三处此前未记载的问题（V-07 与 V-10 都只读源码与查 DB、未看浏览器运行时，故均未发现） |

## 阻塞说明

**V-08 / V-09 与 V-01~V-06 的关系**：重叠但不冗余。后者问"erpnext 的接入点是否够用"（读上游源码回答），前者问"别人实际怎么做的、做到哪一步"（读两个真实项目回答）。**若两个项目中有一个已用 app + hook 实现了可观的中国本地化，V-01 即被实证回答**，且能直接看到它们踩过什么坑。故两者是"理论可行性"与"实践证据"的互补。

**V-11 的特殊性**：它是本 Round 出现的第一个"改一处可能同时影响多例"的候选，与 V-07 判的 `no-go` 构成对照——V-07 说的是"四条源码路径不能同修"（在其范围内成立），V-11 问的是"它们是否共享同一个断掉的前置条件（realtime 推送）"。两者可同时为真。**验法特别干净：只改配置不改代码，改前改后对比同一组操作。**

**⚠ V-11 目前是假说，不是结论。** 其形态与 V-07 对 `load_last_view()` 的猜测同类（都能解释现象、都未验证），而后者已被 V-10 以一条 SQL 推翻。**在改端口实测之前，不得把它当结论写进任何产物，也不得用它去解释别的现象**（见讨论记录第 14 步③记下的失误形态：拿两个都未验证的东西互相支撑）。

**只有 V-01 标阻塞**：它决定中国本地化是"在自有 app 里做"还是"必须改 erpnext 本体"。后者会改变本次规划的架构基调（涉及上游同步的持续负担，见 `docs/开发守则.md`），故不拿到结论无法定需求分级。其余六条只影响工作量估算与分级细节，A 步可继续推进不依赖它们的议题。

## 复核建议（V-07）

**验证深度**：例 1、例 2 为源码取证 + 站点实测双重验证，可靠；例 3、例 4 为纯源码路径分析，**未实际复现**。

**有没有实际复现**：

| 例 | 实测了什么 | 复现了吗 |
|---|---|---|
| 1 仓库列表空白 | 85 条 Warehouse、`reportview.get` 返 20 行、DB `tabDocType.default_view=Tree`、`force_re_route=0`、`Workspace Sidebar Item` 21 个字段无 `doc_view` | **部分**——数据层与元数据实测，但未在浏览器点侧栏看现象 |
| 2 侧栏卡片缺失 | `get_bootinfo()` 取出 `buying` 侧栏 32 项（确无该卡）、全仓 grep `add_card` 零调用者 | **是**（等价复现：确认该卡不在侧栏数据源里、卡片机制无调用者） |
| 3 BOM 提交按钮 | — | **否**，站点 0 Item / 0 BOM |
| 4 `time_logs` 空行 | — | **否**，站点 0 Job Card / 0 Work Order |

**拿不准的**：

1. **例 1 的最终成因与 R6 既有判据有偏差，需 shape 注意**。R6 记「`*_list.js` 缺失 ⇒ 落列表路由即空白」，但本次查出两点：① `*_list.js` 只是可选定制钩子（erpnext 641 个 doctype 仅 79 个有，`Brand` 无此文件而列表正常），缺失本身不致空白；② v16 `router.js:223-231` 对裸路由有 `default_view==="Tree"` 的兜底，而 `Warehouse`/`Account`/`Cost Center` 的 `default_view` 实测确为 `Tree`。**按此逻辑裸路由本应被改写为树视图**，则"从侧栏点进恒落列表路由"这一判定在 v16 需重新取证——很可能真正的入口是 `list_view.js:7-22` 的 `last_view` 用户设置（与 R3「敲过树视图地址后就正常了」相符），而非侧栏链接本身。**结论（不同源）不受影响**，但第五例"已查明根因"那一条的根因描述可能需要修订，这不在本探针任务范围内。

2. **例 3 的具体失效点未钉死**。`__unsaved` 未清是唯一可能（服务端四项 R3 已排除），但「是哪一次 `set_value` 在保存响应回来之后又跑了一遍」没有实测证据。有 BOM 数据后在浏览器里断点看 `cur_frm.doc.__unsaved` 才能定死。

3. **例 4 的两处缺陷是否需分开修**未判。写入侧（`job_card.py:680-685` 的 `db_update()` 旁路）与读取侧（`job_card.js:615-622` 不验行有效性）是两个独立缺陷，只修读取侧能消除状态错乱但空行仍会入库、idx 仍会重复。这属"该怎么改"，按纪律不在本表给建议。

4. **例 2 是否该算进本条命题**存疑。它不是"不刷新即不显示"（刷新也永不出现），而是 v16 架构变更下的功能缺失。若 shape 要重新归类，这一例可能该独立成条。

## 复核建议（V-01 ~ V-06）

> 本节为 V-01~V-06 这一批的验证深度说明。源码基线 erpnext 16.35.0 / frappe 16.34.0，
> 站点 `erx.localhost`（容器在跑）。

### 每条的验证深度

| 编号 | 判定 | 证据类型 | 实际跑了吗 |
|---|---|---|---|
| V-01 | go | 源码取证（19 处文件行号）+ 分派运行时实测 | **部分**——分派链路实测生效，但**未真装 app** |
| V-02 | 无法判定 | 静态计数 + 建公司实跑（失败，拿到确切报错） | **是**（对"现状"跑了；对"改好后"未跑） |
| V-03 | go | 源码取证 + 下拉覆盖实测 | **是**（下拉）／**否**（选中后建科目） |
| V-04 | go | 原生计税引擎实跑试算，三项要求各跑一遍 | **是**（试算层）／**否**（未提交单据、未验 GL） |
| V-05 | go | 网络可达性实测 + 多源文档一致 | **否**——未成功开出测试发票（见下） |
| V-06 | go | 实建模板 + 实跑报表出 8 行 | **是**（结构与映射）／**否**（金额，站点 0 GL Entry） |

### 触及了哪些边界、没触及哪些

**V-01（阻塞项，结论最需稳）**
- 触及：`regional_overrides` hook 的读取与分派（末位胜出、按国家隔离、参数透传）、20 个
  `@allow_regional` 覆盖点清单、`doc_events`/Custom Field/权限/Report 四类接入点定性、
  `financial_report_template` 的 installed_apps 扫描、以及**四处非 hook 缺口的精确位置**。
- **没触及**：① 未执行 `bench install-app`。分派是用"注入 hooks 缓存 + 置 `in_install` 绕过
  `get_attr` 的已装 app 门禁"验的，**与真装一个 app 的端到端行为不等价**——装 app 还会牵动
  patches、fixtures、DocType 同步、`installed_apps` 排序（决定 `[-1]` 谁胜出）。
  ② `doc_events["Company"]["after_insert"]` 补偿 `install_country_fixtures` 这条替代路，
  **只确认机制存在与无冲突，未实跑**；建公司的时序（`country_change` flag 时机、科目建完与否）未验。
  ③ **未验升级兼容性**：`@allow_regional` 函数签名若上游变动，app 侧覆盖会**静默错位**
  （`allow_regional` 不校验签名），这是长期负担。④ 未验 `regional_overrides` 与 hrms
  等其它已装 app 是否有 target 冲突。
- 探针与真实场景的差距：**最大的一处**。结论"可以用自有 app 做"在机制层站得住，但
  "装上后一切正常"没被证明。

**V-02**
- 触及：现状的客观计数（82/103/层级 4、元字段全 0 填）、拿现状建公司的**确切失败报错**、
  `root_type` 只需顶层赋值的源码依据、与 6 份已 verified 模板的同口径对照。
- **没触及**：① **没折算人日**——这是命题判不了真假的原因，不是漏验。②"改好后能不能用"
  完全没验（没真去补一份完整模板再建公司）。③ 财会[2006]3号的标准编号表未核对，
  "可照抄"是常识判断不是实测。④ 未核该模板的科目集合相对现行准则是否有缺漏
  （只查了营业税两处废止科目，没做全量准则比对）。

**V-03**
- 触及：原生下拉内容、`allow_unverified_charts` flag 效果、`override_whitelisted_methods`
  的解析链路（`execute_cmd` → `override_whitelisted_method`）与覆盖后的实际返回值、
  以及"把 json 放自己 app"为何走不通的源码依据。
- **没触及**：**选中自制模板后真去建公司**。`get_chart()` 因不经 `execute_cmd` 而无法被
  `override_whitelisted_methods` 覆盖，替代路径（`create_charts(custom_chart=...)` /
  COA Importer / Company hook 自建）只确认了入口存在，一条都没跑。**这意味着 V-03 的 go
  只保证"下拉里看得见"，不保证"点了能用"** —— 若 shape 要据此定需求，这半步得补。

**V-04**
- 触及：价税分离（113→100+13）、多档位逐行生效（13%+6%=19）、含税叠多档位、进项侧
  Purchase Invoice，四项均实跑；并撞出 `item_tax_rate` 手填无效这个反直觉点及其源码成因。
- **没触及**：① **未提交任何单据**，试算只到 `calculate_taxes_and_totals`，
  **没走 `on_submit` → `make_gl_entries`**，故税金科目的借贷方向、是否落到"销项税额/进项税额"
  对应子目、GL 分录是否符合中国记账习惯，**全未验**。② 未验 `Tax Category` + `Tax Rule`
  自动套模板（六国里 australia 用这套）。③ 未验红冲/退货场景的税额反向。
  ④ 差额征税、简易计税、免抵退明确划在原生机制外，但**没验"自有逻辑补上"的难度**。

**V-05**
- 触及：诺诺沙箱端点的真实可达性与业务层错误码（这是"对未签约方开放"的硬证据）、
  多个独立来源对沙箱凭据/测试税号/token 可空/支持专票的一致描述、生产侧资质要求的定位。
- **没触及**：① **未成功开出一张测试发票**。社区流传的沙箱凭据不属本项目，用它签名调用
  第三方系统本探针主动不做（工具侧亦拒绝）。**签名算法、必填字段、返回报文结构、
  红冲流程全部只有文档描述，零实测。** ② **未读到官方注册流程页**（诺诺/百望均为 SPA），
  "自助注册能否拿到沙箱凭据、会不会卡在企业认证"**没有官方依据**——这是本条判定
  `go` 的主要不确定来源。③ 只验诺诺；**百望云、航信直连未测**。
  ④ 金税盘/税控设备本地对接（客户若不走服务商 API）**完全未触及**。
  ⑤ 沙箱与生产的字段差异、限额、并发限制未查。

**V-06**
- 触及：`Financial Report Template` 的完整表达力（行类型/余额类型/公式/方向/缩进）、
  自带 IFRS 模板的写法、实建一张中国式资产负债表并跑出 8 行且科目映射正确、
  app 可投放模板的扫描机制、以及两处会踩的坑（filter 键名 `report_template`、
  `insert()` 会把 json 导出进 apps/）。
- **没触及**：① **利润表与现金流量表一张没建**。`Cash Flow` 虽是原生 report_type，
  但**中国准则现金流量表的经营/投资/筹资三段分类能否用 `Account Data` 条件表达，未验**——
  现金流量表通常需按现金收支性质归集，不一定能靠科目条件筛出来，**这是本条最可能翻车的地方**。
  ② **金额对不对完全没验**：站点 0 条 GL Entry、无真实财年，跑的是 `_Test Fiscal Year 2050`，
  全零。只证了"行结构与科目映射对"。③ 中国报表的"年初余额/期末余额"双列格式未试
  （`balance_type` 有 `Opening Balance`，应可表达）。④ 附注、报送版式（导出 Excel）未验。

### 哪几条拿不准

1. **V-06 的"现金流量表"——最不放心的一条**。判定 `go` 建立在"`Cash Flow` 是原生
   report_type + 资产负债表跑通"上，但现金流量表的取数逻辑与资产负债表**性质不同**
   （按收支性质归集，而非按科目余额）。资产负债表跑通**不构成**现金流量表也能跑通的证据。
   若 shape 要把"三张表都能出"写进需求，这条得单独再验。

2. **V-01 的"未真装 app"**。这是阻塞项，结论会定架构基调。机制层证据我认为足够硬
   （hook 读取、分派、隔离、末位胜出都实测了），但"装上后 patches/fixtures/DocType 同步
   一切顺利"没证明。建议在真正动手做 app 之前，先花半天装一个空 app 跑通
   `bench install-app` + 一条 `regional_overrides` 生效，再正式开工。

3. **V-05 的 `go` 依赖社区文档而非官方页面**。沙箱端点开放是实测的硬事实，但
   "本项目自己注册能拿到沙箱凭据"是**推断**（依据是"沙箱凭据本就公开共享、token 可空"）。
   若实际注册时卡在企业认证，这条会翻成 `no-go`。闭合成本很低——去开放平台注册一次即可。

4. **V-03 只验了一半**。下拉可覆盖是实测的，但"选中后能建出科目"没跑。我倾向认为
   `create_charts(custom_chart=...)` 这条路没问题（参数就是为此存在的，V-02 也正是用它试建的），
   但没实测。

5. **V-04 没验 GL 分录**。计税数字全对，但落账对不对没看。中国财务对"进项税额/销项税额
   分别挂哪个子目"很敏感，这一步建议在有真实单据后补验。

6. **V-02 判 `无法判定` 而非给个工时数字**，是因为按纪律不能把"我觉得 2-3 天"当结论。
   客观计数已给全（82 顶层重组 + 103 处编号 + 20-30 处 account_type + 5 处 root_type
   + 删 2 处废止科目），shape 可据此按执行者熟悉度自行折算。

### 一处需要主 Session 知道的环境副作用

探针早期有一版脚本 `import erpnext.tests.test_regional`，该模块在 import 时会触发
ERPNext 测试数据 bootstrap（`erpnext/tests/utils.py:3013` 模块级 `BootStrapTestData()`），
**已向 `erx.localhost` 写入测试数据并提交**：Company 从 1 增至 **17**（多出
`_Test Company`、`Wind Power LLC`、`Parent Group Company India`、`_Test Company UAE VAT` 等 16 个）、
Account 从 95 增至 **1632**、Warehouse 从 5 增至 **85**、Fiscal Year 从 0 增至 **40** 条
（全为 `_Test Fiscal Year 20xx`）、UOM 239、Item Group 6。单据仍为 0（Sales Invoice /
Purchase Invoice / Item / Customer 均 0），原公司「华东弹簧」及其科目未被改动。

- 后续探针已全部避开 `erpnext.tests.*`，且自身写操作均在事务内 rollback（已逐个确认无残留）。
- 另有一次 `insert()` 把探针模板导出成 json 写进了 `apps/erpnext/.../financial_report_template/`，
  **已删除**，`git -C frappe-bench/apps/erpnext status` 与 frappe 同样确认干净。
- 干净备份在手且早于污染：`docker/backups/20260922_145623-erx_localhost-database.sql.gz`
  （已核对：`_Test Company` 出现 0 次、含「华东弹簧」、Company/Account/Warehouse/Fiscal Year
  各 1 条 INSERT 语句）。
- **恢复站点需 restore 数据库，属破坏性操作且影响共享环境，本探针未擅自执行**，交主 Session
  与用户决定。若后续 Round 要用干净骨架站点（例如实测建公司流程），建议先 restore；
  若只做源码分析则不影响。

### 探针与真实场景的总体差距

1. **站点是空骨架**（0 单据、0 GL Entry、0 Item），所以所有"金额算得对不对""落账对不对"
   的验证一概缺席。本批六条里 V-04 与 V-06 的结论都只到"机制能表达"，不到"数字正确"。
2. **没装 app**，V-01/V-03 的结论是"机制允许"而非"实际跑通"。
3. **V-05 没发出一次真实业务请求**。
4. 六条判定中 **5 个 go 有 4 个带"半步未验"**（V-01 未装 app、V-03 未建科目、
   V-04 未验 GL、V-06 未验金额与另两张表）。这些半步都不推翻结论方向，但若后续
   Workflow 直接把它们当"已验证可行"往下压需求，风险落在实现阶段。
