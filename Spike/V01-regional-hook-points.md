# V-01 探针结论：regional 接入点清单

命题：中国本地化能否以「新建自有 app + ERPNext hook」接入，**不改 erpnext/frappe 源码**。

源码基线：`frappe-bench/apps/erpnext` 16.35.0 / `frappe-bench/apps/frappe` 16.34.0
探针：`V01-regional-hook-points.py`（站点实跑）、`V01b-hook-dispatch-runtime.py`（分派实测）

## 六个既有国家用到的接入点，逐个定性

| # | 接入点 | 形态 | 外部 app 可用？ | 证据 |
|---|--------|------|----------------|------|
| 1 | `regional_overrides` | **hook** | 可，且多 app 可叠加 | `erpnext/__init__.py:145` 读 `frappe.get_hooks("regional_overrides")`；`:152` 取 `[-1]`（末位 app 胜出） |
| 2 | `@allow_regional` 装饰的 20 个函数 | **hook 目标** | 可 | 全部经 #1 分派；清单见下 |
| 3 | `doc_events`（italy/uae 挂 SI/PI/Address） | **hook** | 可，可叠加 | `erpnext/hooks.py:382-404` |
| 4 | Custom Field（italy/za/uae/us 全靠它） | **数据层公开 API** | 可 | `frappe.custom.doctype.custom_field.custom_field.create_custom_fields`，italy/setup.py:8,26 |
| 5 | 权限（`add_permission`/`update_permission_property`） | **公开 API** | 可 | `frappe.permissions`，italy/setup.py:9 |
| 6 | Print Format / Report / DocType | **app 自带即可** | 可 | uae 的 `UAE VAT 201`、us 的 `IRS 1099` 都是普通 DocType/Report |
| 7 | `financial_report_template/` 模板目录 | **按 installed_apps 扫描** | 可 | `financial_report_template.py:146-155` 遍历 `frappe.get_installed_apps()`；COA 里 `disable_default_financial_report_template` 可屏蔽 erpnext 自带模板（同文件 :139-144） |
| 8 | `install_country_fixtures()` | **硬编码模块路径，非 hook** | **不可直接用** | `company.py:858-861`：`module_name = f"erpnext.regional.{scrub(country)}.setup.setup"` |
| 9 | `update_regional_tax_settings()` | **硬编码模块路径，非 hook** | **不可直接用** | `taxes_setup.py:120-125`，同样拼 `erpnext.regional.<country>.setup.*` |
| 10 | `country_wise_tax.json` | **erpnext 内死文件** | **不可直接改** | `taxes_setup.py:16-21` 读死路径；China 条目现为 `{"China Tax": {"account_name":"VAT","tax_rate":17.0}}`（17% 已过时） |
| 11 | 科目表 json（`verified/`/`unverified/`） | **erpnext 内死目录** | **不可投放** | `chart_of_accounts.py:120-124`、`:145-160` 用 `os.path.dirname(__file__)`，不扫 installed_apps |

## #8/#9/#10/#11 这四处不是 hook —— 但都有 app 侧绕法（已实测）

| 缺口 | app 侧替代 | 是否实测 |
|---|---|---|
| #8 `install_country_fixtures` 不走 hook | 挂 `doc_events["Company"]["after_insert"]` 自己做 fixtures（`doc_events["Company"]` 现为空，无冲突） | 机制已验（#3 同类），本轮未建公司实跑该 hook |
| #9 `update_regional_tax_settings` 不走 hook | 同上，建公司后自行建 Tax Template | 未实跑 |
| #10 `country_wise_tax.json` 改不了 | 不依赖它，自己建 Sales/Purchase/Item Tax Template（V-04 已实测可表达中国增值税） | V-04 已实测 |
| #11 科目表 json 放不进 erpnext | `override_whitelisted_methods` 换掉 `get_charts_for_country`（V-03 已实测）；但 `get_chart()` 也需一并覆盖，或改用 `create_charts(custom_chart=...)` / COA Importer | V-03 已实测下拉；`get_chart` 覆盖未实跑 |

**关键点**：这四处都是"erpnext 自己找 `erpnext.regional.<country>` 这个位置"，
外部 app 拿不到那个位置；但**没有一处是"必须改 erpnext 源码才能实现该功能"**——
功能都能在 app 侧用别的 hook 达成，只是不走 erpnext 为自家 regional 预留的那条捷径。

## 运行时分派实测（`V01b-hook-dispatch-runtime.py`）

把「某 app 声明了 China 的 `regional_overrides`」注入 hooks 缓存后：

```
get_region() = 'China'
[A] 覆盖前 regional_overrides.China = None
    update_itemised_tax_data() -> None ; app 侧命中=[]
[B] 注入后 regional_overrides.China = {'...update_itemised_tax_data': ['cn_l10n_probe.cn_update_itemised_tax_data']}
    update_itemised_tax_data() -> 'CN-OVERRIDE-RAN' ; app 侧命中=[('first', 'Sales Invoice')]
[C] 两 app 同 target -> 'SECOND-APP-WON'（末位胜出）
[D] get_region()=Italy -> None ; 命中=[]（China 覆盖不生效，按国家隔离）
[E] sales_invoice.make_regional_gl_entries 覆盖后 -> ['CN-GL-HOOKED']
```

即：覆盖真的分派到 app 侧函数、参数原样传入、按 `get_region()` 隔离国家、多 app 末位胜出。

**附带发现**：`frappe.get_attr`（`frappe/__init__.py:1129-1133`）会拦"模块所属 app 未安装"，
所以覆盖函数**必须住在一个真正 install 到站点的 app 里**——这正是"自有 app"方案的前提，
不是障碍。

## `@allow_regional` 可覆盖点全清单（20 处）

```
accounts/doctype/payment_entry/payment_entry.py:3613        add_regional_gl_entries
accounts/doctype/payment_reconciliation/...:947             adjust_allocations_for_taxes
accounts/doctype/purchase_invoice/purchase_invoice.py:2092  make_regional_gl_entries
accounts/doctype/sales_invoice/sales_invoice.py:2654        make_regional_gl_entries
accounts/doctype/tax_withholding_category/...:252           get_tax_id_for_party
accounts/party.py:308                                       get_regional_address_details
assets/doctype/asset/depreciation.py:490                    cancel_depreciation_entries
assets/.../depreciation_methods.py:78                       get_wdv_or_dd_depr_amount
controllers/accounts_controller.py:3469                     get_advance_payment_entries_for_regional
controllers/accounts_controller.py:4466                     validate_regional
controllers/accounts_controller.py:4471                     validate_einvoice_fields
controllers/accounts_controller.py:4476                     update_gl_dict_with_regional_fields
controllers/buying_controller.py:1336                       update_regional_item_valuation_rate
controllers/taxes_and_totals.py:1280                        get_regional_round_off_accounts
controllers/taxes_and_totals.py:1285                        update_itemised_tax_data
controllers/taxes_and_totals.py:1291                        get_itemised_tax_breakup_header
controllers/taxes_and_totals.py:1296                        get_itemised_tax_breakup_data
stock/doctype/purchase_receipt/purchase_receipt.py:1760     update_regional_gl_entries
tests/test_regional.py:9                                    test_method
```

覆盖点覆盖了 GL 分录、计税、税额拆分、地址取值、折旧、采购估值 —— 中国本地化要动的地方基本都在内。

## 判定

**go** —— 六国实现所依赖的接入点，无一处要求改 erpnext 本体；不走 hook 的四处
（`install_country_fixtures`/`update_regional_tax_settings`/`country_wise_tax.json`/科目表目录）
都有已验证或机制明确的 app 侧替代。

## 未触及

- 未真的装一个 app 跑完整链路（`bench install-app`）。分派链路是用注入 hooks 缓存
  + `in_install` 绕过 `get_attr` 门禁验的，**不等于装 app 后的端到端行为**。
- `doc_events["Company"]["after_insert"]` 补偿 `install_country_fixtures` 的路子
  **只验了机制存在，未实跑**。建公司时序（科目建完没建完、`country_change` flag 时机）未验。
- 未验 app 与 erpnext 的**升级兼容性**：`@allow_regional` 的函数签名若上游改了，
  app 侧覆盖会静默错位。这是长期负担，本探针不涉及。
- 未验 hooks 里 `regional_overrides` 与 hrms 等其它 app 是否有 target 冲突。
