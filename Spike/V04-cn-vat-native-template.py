# V-04 探针：中国增值税逻辑（进项/销项分离、多税率档位、价税分离取值）
# 能否用原生 Sales/Purchase Taxes and Charges Template + Item Tax Template 表达。
# 本探针只读 DocType 元数据 + 用原生计税引擎做纯内存试算，不建单据、不落库。

import frappe


def run():
    out = []

    # ---------- 1. 进项/销项分离：靠两套 Template + 两个科目 ----------
    out.append("[1] 进项/销项分离")
    out.append("    Sales Taxes and Charges Template  -> 销项（account_head 指 销项税额）")
    out.append("    Purchase Taxes and Charges Template -> 进项（account_head 指 进项税额）")
    out.append("    两者是独立 DocType，各自 taxes 行的 account_head 指向不同 Account：")
    for dt in ("Sales Taxes and Charges", "Purchase Taxes and Charges"):
        meta = frappe.get_meta(dt)
        f = meta.get_field("account_head")
        out.append("      %s.account_head: fieldtype=%s options=%s reqd=%s"
                   % (dt, f.fieldtype, f.options, f.reqd))
    # 现成的中国科目表里已有进项/销项科目
    out.append("    cn_l10n_chart_china.json 应交税费>应交增值税 下已含：进项税额/销项税额/"
               "进项税额转出/未交增值税 等 10 个子目（源码已核）")

    # ---------- 2. 多税率档位：Item Tax Template ----------
    out.append("[2] 多税率档位（13%/9%/6%/3%/0%）")
    meta = frappe.get_meta("Item Tax Template")
    out.append("    Item Tax Template.taxes -> %s（每行 tax_type=Account, tax_rate=Float）"
               % meta.get_field("taxes").options)
    d = frappe.get_meta("Item Tax Template Detail")
    for fn in ("tax_type", "tax_rate", "not_applicable"):
        f = d.get_field(fn)
        out.append("      Detail.%s: %s %s" % (fn, f.fieldtype, f.options or ""))
    out.append("    -> 一个档位一个 Item Tax Template，挂到 Item 或 Item Group；")
    out.append("       单据行的 item_tax_template 覆盖表头 Template 的税率")
    itm = frappe.get_meta("Sales Invoice Item")
    out.append("      Sales Invoice Item.item_tax_template 存在：%s"
               % bool(itm.get_field("item_tax_template")))
    out.append("      Sales Invoice Item.item_tax_rate 存在：%s"
               % bool(itm.get_field("item_tax_rate")))

    # ---------- 3. 价税分离：included_in_print_rate ----------
    out.append("[3] 价税分离（含税单价 -> 拆出不含税金额与税额）")
    f = frappe.get_meta("Sales Taxes and Charges").get_field("included_in_print_rate")
    out.append("    Sales Taxes and Charges.included_in_print_rate: %s (%s)"
               % (f.fieldtype, f.label))
    out.append("    charge_type 可选值：%s"
               % frappe.get_meta("Sales Taxes and Charges").get_field("charge_type").options.split("\n"))

    # ---- 用原生计税引擎实跑一遍含税价拆分（内存对象，不 insert） ----
    from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals

    company = frappe.db.get_value("Company", {"country": "China"}, "name") \
        or frappe.db.get_value("Company", {}, "name")
    out.append("    试算用公司：%r" % company)

    tax_acct = frappe.db.get_value(
        "Account", {"company": company, "account_type": "Tax", "is_group": 0}, "name")
    out.append("    试算用税金科目：%r" % tax_acct)

    if tax_acct:
        # 含税单价 113，13% 增值税，included_in_print_rate=1
        doc = frappe.new_doc("Sales Invoice")
        doc.company = company
        doc.currency = frappe.db.get_value("Company", company, "default_currency")
        doc.conversion_rate = 1
        doc.customer = None
        doc.append("items", {
            "item_code": None, "item_name": "PROBE", "description": "PROBE",
            "qty": 1, "rate": 113, "uom": "Nos", "conversion_factor": 1,
            "income_account": None, "cost_center": None,
        })
        doc.append("taxes", {
            "charge_type": "On Net Total",
            "account_head": tax_acct,
            "description": "VAT 13% (incl)",
            "rate": 13,
            "included_in_print_rate": 1,
        })
        try:
            calculate_taxes_and_totals(doc)
            out.append("    含税价 113 / 13% / included_in_print_rate=1 试算结果：")
            out.append("      items[0].rate(含税录入)      = %s" % doc.items[0].rate)
            out.append("      items[0].net_rate(不含税)    = %s" % doc.items[0].net_rate)
            out.append("      items[0].net_amount          = %s" % doc.items[0].net_amount)
            out.append("      net_total(不含税合计)        = %s" % doc.net_total)
            out.append("      taxes[0].tax_amount(税额)    = %s" % doc.taxes[0].tax_amount)
            out.append("      grand_total(价税合计)        = %s" % doc.grand_total)
            ok = abs(float(doc.net_total) - 100.0) < 0.02 and abs(float(doc.taxes[0].tax_amount) - 13.0) < 0.02
            out.append("      -> 100/13/113 拆分正确：%s" % ok)
        except Exception as e:
            out.append("    试算抛错：%s: %s" % (type(e).__name__, e))
    else:
        out.append("    站点无 Tax 类科目，跳过试算")

    # ---------- 4. 不含税录入 + 价外税 ----------
    if tax_acct:
        doc2 = frappe.new_doc("Sales Invoice")
        doc2.company = company
        doc2.currency = frappe.db.get_value("Company", company, "default_currency")
        doc2.conversion_rate = 1
        doc2.append("items", {"item_name": "PROBE", "description": "PROBE", "qty": 1,
                              "rate": 100, "uom": "Nos", "conversion_factor": 1})
        doc2.append("taxes", {"charge_type": "On Net Total", "account_head": tax_acct,
                              "description": "VAT 13%", "rate": 13,
                              "included_in_print_rate": 0})
        try:
            calculate_taxes_and_totals(doc2)
            out.append("[4] 不含税价 100 / 13%% 价外税：net_total=%s tax=%s grand=%s"
                       % (doc2.net_total, doc2.taxes[0].tax_amount, doc2.grand_total))
        except Exception as e:
            out.append("[4] 试算抛错：%s: %s" % (type(e).__name__, e))
    # 多档位同单共存试算
    if tax_acct:
        doc3 = frappe.new_doc("Sales Invoice")
        doc3.company = company
        doc3.currency = frappe.db.get_value("Company", company, "default_currency")
        doc3.conversion_rate = 1
        doc3.append("items", {"item_name": "A13", "description": "A13", "qty": 1,
                              "rate": 100, "uom": "Nos", "conversion_factor": 1,
                              "item_tax_rate": frappe.as_json({tax_acct: 13})})
        doc3.append("items", {"item_name": "B6", "description": "B6", "qty": 1,
                              "rate": 100, "uom": "Nos", "conversion_factor": 1,
                              "item_tax_rate": frappe.as_json({tax_acct: 6})})
        doc3.append("taxes", {"charge_type": "On Net Total", "account_head": tax_acct,
                              "description": "VAT", "rate": 13,
                              "included_in_print_rate": 0})
        try:
            calculate_taxes_and_totals(doc3)
            out.append("[4b] 同一单两档位(13%% + 6%%)，各行 item_tax_rate 覆盖表头：")
            out.append("     net_total=%s  tax_amount=%s  grand_total=%s"
                       % (doc3.net_total, doc3.taxes[0].tax_amount, doc3.grand_total))
            out.append("     -> 期望税额 13 + 6 = 19，实得 %s，逐行档位生效：%s"
                       % (doc3.taxes[0].tax_amount,
                          abs(float(doc3.taxes[0].tax_amount) - 19.0) < 0.02))
        except Exception as e:
            out.append("[4b] 试算抛错：%s: %s" % (type(e).__name__, e))

    # ---------- 5. 原生机制没覆盖的部分 ----------
    out.append("[5] 原生 Template 机制不直接覆盖的中国增值税事项（边界）：")
    out.append("    - 进项税额转出、未交增值税月末结转：属期末账务处理，Template 不管，"
               "需 Journal Entry 或自有逻辑")
    out.append("    - 差额征税、简易计税、免抵退：不是税率问题，Template 表达不了")
    out.append("    - 发票号/发票代码等票面字段：需 Custom Field（V-05 范畴）")
    out.append("    - 小规模纳税人 1%/3% 征收率：只是税率档位，Template 可表达")

    print("\n".join(out))


run()
