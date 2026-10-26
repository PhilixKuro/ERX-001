"""P1-S8-R8 F 片2 探针：拒收入库后，生成器的采购发票/付款是否把拒收数量也开票付款。
只在 s8verify.localhost 事务内跑，结束 rollback，核 Error Log 与新建单据残留为 0。"""
import json
import frappe

SITE = "s8verify.localhost"
frappe.init(site=SITE, sites_path="/workspace/frappe-bench/sites")
frappe.connect()
frappe.set_user("Administrator")
frappe.flags.in_scenario_generator = True  # 与生成器同：跳过 scene_date 钩子（s8verify 未迁移 Demo Progress）
assert frappe.local.site == SITE
out = {}
try:
    errors_before = frappe.db.count("Error Log")
    from frappe_debug.builders.common import insert_and_submit
    from frappe_debug.builders.buying import make_and_submit_purchase_receipt, make_and_submit_purchase_invoice
    from frappe_debug.builders.accounts import make_and_submit_payment_entry
    from frappe_debug.scenario.masters import _warehouses
    company = frappe.db.get_value("Company", {"company_name": "华东弹簧有限公司"}, "name")
    whs = _warehouses(frappe.get_doc("Company", company))
    supplier = frappe.db.get_value("Supplier", {"supplier_name": "钢丝供应商01", "prevent_pos": 0}, "name") or frappe.db.get_value("Supplier", {"prevent_pos": 0, "supplier_name": ["like", "钢丝%"]}, "name")
    out["settings"] = {f: frappe.db.get_single_value("Buying Settings", f) for f in ("bill_for_rejected_quantity_in_purchase_invoice", "set_valuation_rate_for_rejected_materials")}
    day = "2026-10-21"
    po = insert_and_submit({"doctype": "Purchase Order", "company": company, "supplier": supplier,
        "schedule_date": day, "items": [{"item_code": "WIRE-65MN-3.0", "qty": 100, "rate": 8, "warehouse": whs["stores"], "schedule_date": day}]}, day)
    pr = make_and_submit_purchase_receipt(po, day, rejected={"WIRE-65MN-3.0": 5}, rejected_warehouse=whs["rejected"])
    pi = make_and_submit_purchase_invoice(pr, day)
    bank = frappe.db.get_value("Company", company, "default_bank_account")
    pe = make_and_submit_payment_entry("Purchase Invoice", pi, day, bank_account=bank, mode_of_payment="Wire Transfer", reference_no="PROBE-R8F")
    out["po"] = frappe.db.get_value("Purchase Order", po, ["grand_total", "net_total"], as_dict=True)
    out["pr_items"] = frappe.get_all("Purchase Receipt Item", {"parent": pr}, ["qty", "rejected_qty", "received_qty", "amount", "warehouse", "rejected_warehouse"])
    out["pr_totals"] = frappe.db.get_value("Purchase Receipt", pr, ["net_total", "grand_total"], as_dict=True)
    out["pi_items"] = frappe.get_all("Purchase Invoice Item", {"parent": pi}, ["qty", "rejected_qty", "received_qty", "amount"])
    out["pi_totals"] = frappe.db.get_value("Purchase Invoice", pi, ["net_total", "grand_total", "outstanding_amount"], as_dict=True)
    out["pe_paid"] = frappe.db.get_value("Payment Entry", pe, "paid_amount")
    out["sle"] = frappe.get_all("Stock Ledger Entry", {"voucher_no": pr, "is_cancelled": 0}, ["warehouse", "actual_qty", "stock_value_difference"])
    gl = frappe.db.sql("""select voucher_type, account, round(sum(debit),2) dr, round(sum(credit),2) cr from `tabGL Entry`
        where voucher_no in (%s,%s,%s) and is_cancelled=0 group by voucher_type, account order by voucher_type, account""", (pr, pi, pe), as_dict=True)
    out["gl"] = gl
    srbnb = frappe.db.get_value("Company", company, "stock_received_but_not_billed")
    out["srbnb_account"] = srbnb
    out["srbnb_net_dr_minus_cr_for_probe"] = frappe.db.sql("""select round(sum(debit-credit),2) from `tabGL Entry` where voucher_no in (%s,%s) and account=%s and is_cancelled=0""", (pr, pi, srbnb))[0][0]
    out["names"] = [po, pr, pi, pe]
finally:
    frappe.db.rollback()
    out["residual_after_rollback"] = {dt: frappe.db.count(dt, {"name": n}) for dt, n in zip(("Purchase Order", "Purchase Receipt", "Purchase Invoice", "Payment Entry"), out.get("names", [None]*4)) if n}
    out["error_log_delta"] = frappe.db.count("Error Log") - errors_before
    print(json.dumps(out, ensure_ascii=False, default=str, indent=1))
    frappe.destroy()
