# V-06 探针：中国准则财务报表格式能否用原生报表配置产出（不自写报表）。
# v16 新增 Financial Report Template（声明式行+公式引擎），本探针：
#   1) 确认该 DocType 的表达能力（行类型/公式/取数过滤）
#   2) 确认外部 app 可投放模板（sync 按 installed_apps 扫描）
#   3) 真建一张"中国式资产负债表"模板并实跑出数，最后 rollback

import frappe


def run():
    out = []

    # ---- 1. 表达能力 ----
    meta = frappe.get_meta("Financial Report Row")
    ds = meta.get_field("data_source").options.split("\n")
    bt = meta.get_field("balance_type").options.split("\n")
    out.append("[1] Financial Report Row.data_source 可选：%s" % ds)
    out.append("    balance_type 可选：%s" % bt)
    out.append("    关键字段：reference_code(行号) / calculation_formula(取数过滤或公式)")
    out.append("             indentation_level / reverse_sign(方向) / hide_when_empty")
    rt = frappe.get_meta("Financial Report Template").get_field("report_type").options.split("\n")
    out.append("    Template.report_type 可选：%s" % rt)
    out.append("    -> 现金流量表是原生 report_type 之一：%s" % ("Cash Flow" in rt))

    # ---- 2. app 可否投放模板 ----
    import inspect
    from erpnext.accounts.doctype.financial_report_template import (
        financial_report_template as frt,
    )
    src = inspect.getsource(frt._sync_templates_for)
    out.append("[2] _sync_templates_for 按 module 路径扫 <module>/financial_report_template/：")
    out.append("    %s" % [l.strip() for l in src.splitlines() if "template_path" in l or "join" in l][:3])
    src2 = inspect.getsource(frt.sync_financial_report_templates)
    out.append("    sync 遍历 frappe.get_installed_apps()：%s" % ("get_installed_apps" in src2))
    out.append("    COA 里 disable_default_financial_report_template=1 可整体屏蔽 erpnext 自带模板：%s"
               % ("disable_default_financial_report_template" in src2))
    out.append("    -> 外部 app 放 <app>/<module>/financial_report_template/<name>/<name>.json 即被收录")

    # ---- 3. 已装模板 ----
    out.append("[3] 站点现有 Financial Report Template：%s"
               % frappe.get_all("Financial Report Template", pluck="name"))
    out.append("    Account Category 条数：%s" % frappe.db.count("Account Category"))

    # ---- 4. 真建一张中国式资产负债表模板并出数 ----
    company = frappe.db.get_value("Company", {"country": "China"}, "name")
    created = None
    try:
        tpl = frappe.get_doc({
            "doctype": "Financial Report Template",
            "template_name": "PROBE 中国式资产负债表",
            "report_type": "Balance Sheet",
            "module": "Accounts",
            "rows": [
                {"reference_code": "A_HDR", "display_name": "资产", "data_source": "Blank Line",
                 "bold_text": 1, "indentation_level": 0},
                {"reference_code": "A100", "display_name": "货币资金",
                 "data_source": "Account Data", "balance_type": "Closing Balance",
                 "calculation_formula": '["account_type", "in", ["Cash", "Bank"]]',
                 "indentation_level": 1},
                {"reference_code": "A200", "display_name": "应收账款",
                 "data_source": "Account Data", "balance_type": "Closing Balance",
                 "calculation_formula": '["account_type", "=", "Receivable"]',
                 "indentation_level": 1},
                {"reference_code": "A300", "display_name": "存货",
                 "data_source": "Account Data", "balance_type": "Closing Balance",
                 "calculation_formula": '["account_type", "=", "Stock"]',
                 "indentation_level": 1},
                {"reference_code": "A_TOTAL", "display_name": "流动资产合计",
                 "data_source": "Calculated Amount",
                 "calculation_formula": "A100 + A200 + A300",
                 "bold_text": 1, "indentation_level": 1},
                {"reference_code": "L_HDR", "display_name": "负债", "data_source": "Blank Line",
                 "bold_text": 1, "indentation_level": 0},
                {"reference_code": "L100", "display_name": "应付账款",
                 "data_source": "Account Data", "balance_type": "Closing Balance",
                 "calculation_formula": '["account_type", "=", "Payable"]',
                 "indentation_level": 1, "reverse_sign": 1},
                {"reference_code": "L200", "display_name": "应交税费",
                 "data_source": "Account Data", "balance_type": "Closing Balance",
                 "calculation_formula": '["account_type", "=", "Tax"]',
                 "indentation_level": 1, "reverse_sign": 1},
            ],
        })
        tpl.flags.ignore_permissions = True
        # in_import=True 阻止 frappe 把新建的模板导出成 json 文件写进 apps/erpnext/
        frappe.flags.in_import = True
        tpl.insert()
        frappe.flags.in_import = False
        created = tpl.name
        out.append("[4] 已建模板 %r，行数=%s" % (created, len(tpl.rows)))

        # 实跑报表
        # 优先取真实财年（站点被 erpnext 测试 bootstrap 污染，混入大量 _Test Fiscal Year）
        fy = frappe.db.get_value("Fiscal Year", {"name": ["not like", "_Test%"]},
                                 ["name", "year_start_date", "year_end_date"], as_dict=True)             or frappe.db.get_value("Fiscal Year", {},
                                   ["name", "year_start_date", "year_end_date"], as_dict=True)
        out.append("    用财年：%s" % fy)
        if fy:
            filters = {
                "company": company,
                "report_template": created,  # 注意：filter 键是 report_template（balance_sheet.py:32）
                "from_fiscal_year": fy.name,
                "to_fiscal_year": fy.name,
                "periodicity": "Yearly",
                "filter_based_on": "Fiscal Year",
                "period_start_date": str(fy.year_start_date),
                "period_end_date": str(fy.year_end_date),
                "accumulated_values": 1,
            }
            from frappe.desk.query_report import run as run_report
            try:
                res = run_report("Balance Sheet", filters=filters,
                                 ignore_prepared_report=True)
                cols = res.get("columns") or []
                rows = res.get("result") or []
                out.append("    报表跑通：列数=%s 行数=%s" % (len(cols), len(rows)))
                for r in rows[:9]:
                    if isinstance(r, dict):
                        keys = [k for k in r if k not in ("indent", "parent_account")]
                        out.append("      %s" % {k: r[k] for k in keys[:5]})
                    else:
                        out.append("      %s" % str(r)[:160])
            except Exception as e:
                import traceback
                out.append("    跑报表抛错：%s: %s" % (type(e).__name__, e))
                out.append(traceback.format_exc()[-800:])
        else:
            out.append("    站点无 Fiscal Year，跳过实跑（站点为骨架状态）")

    except Exception as e:
        import traceback
        out.append("[4] 建模板抛错：%s: %s" % (type(e).__name__, e))
        out.append(traceback.format_exc()[-1000:])
    finally:
        frappe.db.rollback()
        out.append("[5] 已 rollback；模板残留=%s"
                   % (frappe.db.exists("Financial Report Template", created) if created else None))

    print("\n".join(out))


run()
