# V-04 补充探针：多税率档位是否真能逐行生效。
# 上一版直接手填 item.item_tax_rate 无效——原因是 calculate_taxes_and_totals
# 在 update_item_tax_map()（taxes_and_totals.py:144-150）里会用
# get_item_tax_map(tax_template=item.item_tax_template) 重算并覆盖该字段
# （get_item_details.py:941-956）。所以必须走真的 Item Tax Template。
# 本探针建两个 Item Tax Template 试算，结束 rollback，不留数据。

import frappe


def run():
    from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals

    out = []
    company = frappe.db.get_value("Company", {"country": "China"}, "name")
    out.append("公司=%r" % company)

    # 找/建两个税金科目：销项 13% 与 6% 共用一个 account_head 即可
    tax_acct = frappe.db.get_value(
        "Account", {"company": company, "account_type": "Tax", "is_group": 0}, "name")
    out.append("税金科目=%r" % tax_acct)

    created = []
    try:
        for title, rate in (("PROBE-CN-VAT-13", 13), ("PROBE-CN-VAT-6", 6)):
            if not frappe.db.exists("Item Tax Template", {"title": title, "company": company}):
                d = frappe.get_doc({
                    "doctype": "Item Tax Template",
                    "title": title,
                    "company": company,
                    "taxes": [{"tax_type": tax_acct, "tax_rate": rate}],
                })
                d.insert(ignore_permissions=True)
                created.append(d.name)
        out.append("已建临时 Item Tax Template：%s" % created)

        t13 = frappe.db.get_value("Item Tax Template",
                                  {"title": "PROBE-CN-VAT-13", "company": company}, "name")
        t6 = frappe.db.get_value("Item Tax Template",
                                 {"title": "PROBE-CN-VAT-6", "company": company}, "name")

        doc = frappe.new_doc("Sales Invoice")
        doc.company = company
        doc.currency = frappe.db.get_value("Company", company, "default_currency")
        doc.conversion_rate = 1
        doc.append("items", {"item_name": "A13", "description": "A13", "qty": 1,
                             "rate": 100, "uom": "Nos", "conversion_factor": 1,
                             "item_tax_template": t13})
        doc.append("items", {"item_name": "B6", "description": "B6", "qty": 1,
                             "rate": 100, "uom": "Nos", "conversion_factor": 1,
                             "item_tax_template": t6})
        doc.append("taxes", {"charge_type": "On Net Total", "account_head": tax_acct,
                             "description": "VAT", "rate": 13,
                             "included_in_print_rate": 0})
        calculate_taxes_and_totals(doc)
        out.append("两行分别挂 13%% / 6%% 的 Item Tax Template：")
        out.append("  items[0].item_tax_rate=%s" % doc.items[0].item_tax_rate)
        out.append("  items[1].item_tax_rate=%s" % doc.items[1].item_tax_rate)
        out.append("  net_total=%s tax_amount=%s grand_total=%s"
                   % (doc.net_total, doc.taxes[0].tax_amount, doc.grand_total))
        ok = abs(float(doc.taxes[0].tax_amount) - 19.0) < 0.02
        out.append("  -> 期望 13+6=19，实得 %s，逐行档位生效：%s" % (doc.taxes[0].tax_amount, ok))

        # 含税录入 + 两档位
        doc2 = frappe.new_doc("Sales Invoice")
        doc2.company = company
        doc2.currency = frappe.db.get_value("Company", company, "default_currency")
        doc2.conversion_rate = 1
        doc2.append("items", {"item_name": "A13", "description": "A13", "qty": 1,
                              "rate": 113, "uom": "Nos", "conversion_factor": 1,
                              "item_tax_template": t13})
        doc2.append("items", {"item_name": "B6", "description": "B6", "qty": 1,
                              "rate": 106, "uom": "Nos", "conversion_factor": 1,
                              "item_tax_template": t6})
        doc2.append("taxes", {"charge_type": "On Net Total", "account_head": tax_acct,
                              "description": "VAT incl", "rate": 13,
                              "included_in_print_rate": 1})
        calculate_taxes_and_totals(doc2)
        out.append("含税录入 113(13%%) + 106(6%%)，included_in_print_rate=1：")
        out.append("  net_total=%s tax_amount=%s grand_total=%s"
                   % (doc2.net_total, doc2.taxes[0].tax_amount, doc2.grand_total))
        out.append("  items net_rate = %s / %s" % (doc2.items[0].net_rate, doc2.items[1].net_rate))
        ok2 = (abs(float(doc2.net_total) - 200.0) < 0.05
               and abs(float(doc2.taxes[0].tax_amount) - 19.0) < 0.05)
        out.append("  -> 期望不含税 200、税 19：%s" % ok2)

        # 进项侧同样机制
        doc3 = frappe.new_doc("Purchase Invoice")
        doc3.company = company
        doc3.currency = frappe.db.get_value("Company", company, "default_currency")
        doc3.conversion_rate = 1
        doc3.append("items", {"item_name": "P13", "description": "P13", "qty": 1,
                              "rate": 100, "uom": "Nos", "conversion_factor": 1,
                              "item_tax_template": t13})
        doc3.append("taxes", {"charge_type": "On Net Total", "account_head": tax_acct,
                              "description": "进项 13%", "rate": 13,
                              "category": "Total", "add_deduct_tax": "Add"})
        calculate_taxes_and_totals(doc3)
        out.append("进项侧 Purchase Invoice 100 / 13%%：net_total=%s tax=%s grand=%s"
                   % (doc3.net_total, doc3.taxes[0].tax_amount, doc3.grand_total))

    except Exception as e:
        import traceback
        out.append("抛错：%s: %s" % (type(e).__name__, e))
        out.append(traceback.format_exc()[-1200:])
    finally:
        frappe.db.rollback()
        out.append("已 rollback，临时 Item Tax Template 未留库：%s"
                   % [frappe.db.exists("Item Tax Template", n) for n in created])

    print("\n".join(out))


run()
