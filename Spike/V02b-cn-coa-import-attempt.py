# V-02 补充探针：现状的 cn_l10n_chart_china.json 直接拿去建公司会怎样。
# 用 create_charts(custom_chart=...) 在事务里试建，结束 rollback。
# 目的：把"要补什么"从推断变成实测报错/实测结果。

import frappe


def run():
    import json
    import os

    from erpnext.accounts.doctype.account.chart_of_accounts import chart_of_accounts as coa

    out = []
    p = os.path.join(os.path.dirname(coa.__file__), "unverified", "cn_l10n_chart_china.json")
    chart = json.load(open(p, encoding="utf-8"))["tree"]
    out.append("模板顶层节点=%s" % len(chart))

    # 造一个临时公司来承接科目
    company_name = "PROBE CN COA Co"
    created = None
    try:
        frappe.flags.ignore_chart_of_accounts = True
        co = frappe.get_doc({
            "doctype": "Company",
            "company_name": company_name,
            "abbr": "PCC",
            "default_currency": "CNY",
            "country": "China",
        })
        co.flags.ignore_permissions = True
        co.flags.ignore_mandatory = True
        co.insert()
        created = co.name
        frappe.flags.ignore_chart_of_accounts = False
        out.append("临时公司已建：%r（科目数=%s）"
                   % (created, frappe.db.count("Account", {"company": created})))

        # 直接用现状模板建科目
        frappe.local.flags.ignore_root_company_validation = True
        try:
            coa.create_charts(created, custom_chart=chart)
            n = frappe.db.count("Account", {"company": created})
            out.append("create_charts 未抛错，建出科目 %s 个" % n)
            # 看 root_type 落成什么
            rts = frappe.db.sql("""
                select coalesce(nullif(root_type,''),'(空)') rt, count(*) c
                from `tabAccount` where company=%s group by rt order by c desc
            """, created, as_dict=True)
            out.append("建出科目的 root_type 分布：%s"
                       % [(r["rt"], r["c"]) for r in rts])
            rpt = frappe.db.sql("""
                select coalesce(nullif(report_type,''),'(空)') rp, count(*) c
                from `tabAccount` where company=%s group by rp order by c desc
            """, created, as_dict=True)
            out.append("report_type 分布：%s" % [(r["rp"], r["c"]) for r in rpt])
            at = frappe.db.sql("""
                select coalesce(nullif(account_type,''),'(空)') a, count(*) c
                from `tabAccount` where company=%s group by a order by c desc
            """, created, as_dict=True)
            out.append("account_type 分布：%s" % [(r["a"], r["c"]) for r in at])
            # 建公司必须能自动取到应收/应付
            out.append("能否自动取到 Receivable 科目：%r"
                       % frappe.db.get_value("Account",
                                             {"company": created, "account_type": "Receivable",
                                              "is_group": 0}, "name"))
            out.append("能否自动取到 Payable 科目：%r"
                       % frappe.db.get_value("Account",
                                             {"company": created, "account_type": "Payable",
                                              "is_group": 0}, "name"))
            out.append("-> root_type 全空的后果：资产负债表/利润表分不了表，"
                       "且 default_receivable/payable_account 取不到")
        except Exception as e:
            import traceback
            out.append("create_charts 抛错：%s: %s" % (type(e).__name__, e))
            out.append(traceback.format_exc()[-900:])

    except Exception as e:
        import traceback
        out.append("建公司抛错：%s: %s" % (type(e).__name__, e))
        out.append(traceback.format_exc()[-900:])
    finally:
        frappe.db.rollback()
        frappe.flags.ignore_chart_of_accounts = False
        out.append("已 rollback；临时公司残留=%s"
                   % (frappe.db.exists("Company", created) if created else None))

    print("\n".join(out))


run()
