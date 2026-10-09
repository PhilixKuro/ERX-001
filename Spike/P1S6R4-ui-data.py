import argparse
import json
import os
from datetime import date
from pathlib import Path

import frappe

from frappe_china.tests.utils import make_cn_company


STATE = Path("/workspace/Spike/P1S6R4-ui-data.json")
COMPANY = "_FCT S6 界面验证"


def prepare():
    assert not frappe.db.exists("Company", COMPANY)
    company = make_cn_company(COMPANY, "S6UI")
    fiscal_year = frappe.db.get_value("Fiscal Year", {"year_start_date": "2025-01-01"}, "name")
    assert fiscal_year
    equity = frappe.db.get_value("Account", {"company": COMPANY, "account_number": "3"})
    account = frappe.get_doc({
        "doctype": "Account", "account_name": "_FCT S6 未映射科目", "account_number": "3990",
        "parent_account": equity, "company": COMPANY, "root_type": "Equity",
        "report_type": "Balance Sheet", "cash_flow_code": "15",
    }).insert(ignore_permissions=True)
    journals = []
    for month, amount, contra in ((1, 1000, "3001"), (3, 25, "3990")):
        journal = frappe.get_doc({
            "doctype": "Journal Entry", "company": COMPANY, "posting_date": date(2025, month, 15),
            "voucher_type": "Journal Entry", "user_remark": "_FCT S6 UI evidence",
        })
        for number, debit, credit in (("1002", amount, 0), (contra, 0, amount)):
            journal.append("accounts", {
                "account": frappe.db.get_value("Account", {"company": COMPANY, "account_number": number}),
                "cost_center": company.cost_center,
                "debit_in_account_currency": debit, "credit_in_account_currency": credit,
            })
        journal.insert(ignore_permissions=True)
        journal.submit()
        journals.append(journal.name)
    worksheets = {}
    for month, status in ((1, "submitted"), (2, "cancelled"), (3, "draft")):
        doc = frappe.get_doc({"doctype": "Cash Flow Worksheet", "company": COMPANY,
                              "fiscal_year": fiscal_year, "month": month})
        doc.get_cash_flow_items()
        for item in doc.items:
            item.cash_flow_code = "15"
        doc.insert(ignore_permissions=True)
        if status != "draft":
            doc.submit()
        if status == "cancelled":
            doc.cancel()
        worksheets[status] = doc.name
    frappe.db.commit()
    state = {"company": COMPANY, "fiscal_year": fiscal_year, "journals": journals,
             "worksheets": worksheets, "unmapped_account": account.name}
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(frappe.as_json(state))


def cleanup():
    state = json.loads(STATE.read_text(encoding="utf-8"))
    assert state["company"] == COMPANY
    if "currency_symbol_before" in state:
        assert frappe.db.get_value("Currency", "CNY", "symbol") == "¥"
        frappe.db.set_value("Currency", "CNY", "symbol", state["currency_symbol_before"])
    for name in reversed(list(state["worksheets"].values())):
        if not frappe.db.exists("Cash Flow Worksheet", name):
            continue
        doc = frappe.get_doc("Cash Flow Worksheet", name)
        if doc.docstatus == 1:
            doc.cancel()
        frappe.delete_doc(doc.doctype, doc.name, ignore_permissions=True)
    for name in reversed(state["journals"]):
        doc = frappe.get_doc("Journal Entry", name)
        assert doc.company == COMPANY
        if doc.docstatus == 1:
            doc.cancel()
        assert doc.docstatus == 2
        entries = frappe.get_all("GL Entry", filters={"company": COMPANY, "voucher_type": "Journal Entry", "voucher_no": name},
                                 fields=["name", "is_cancelled"])
        assert all(entry.is_cancelled for entry in entries)
        frappe.db.delete("GL Entry", {"name": ("in", [entry.name for entry in entries]), "company": COMPANY})
        frappe.delete_doc(doc.doctype, doc.name, ignore_permissions=True)
    frappe.delete_doc("Company", COMPANY, ignore_permissions=True)
    frappe.db.commit()
    for doctype in ("Company", "Account", "GL Entry", "Journal Entry", "Cash Flow Worksheet"):
        filters = {"name": COMPANY} if doctype == "Company" else {"company": COMPANY}
        assert not frappe.db.exists(doctype, filters), doctype
    assert not frappe.db.exists("Cash Flow Item", {"parent": ("in", list(state["worksheets"].values()))})
    assert not frappe.db.exists("Cash Flow Subtotal", {"parent": ("in", list(state["worksheets"].values()))})
    assert not frappe.db.exists("Expense Claim Account", {"company": COMPANY})
    if "currency_symbol_before" in state:
        assert frappe.db.get_value("Currency", "CNY", "symbol") == state["currency_symbol_before"]
    state["cleanup_verified"] = True
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(frappe.as_json(state))


def inspect():
    state = json.loads(STATE.read_text(encoding="utf-8"))
    state["currency"] = frappe.db.get_value("Currency", "CNY", ["symbol", "enabled"], as_dict=True)
    state["translation_count"] = frappe.db.count("Translation")
    state["worksheet_state"] = frappe.get_all("Cash Flow Worksheet", filters={"company": COMPANY},
                                             fields=["name", "docstatus", "month"])
    state["residual_company_tables"] = {}
    tables = frappe.db.sql("SELECT TABLE_NAME FROM information_schema.COLUMNS WHERE TABLE_SCHEMA=DATABASE() AND COLUMN_NAME='company'", pluck=True)
    for table in tables:
        if not table.startswith("tab"):
            continue
        count = frappe.db.count(table[3:], {"company": COMPANY})
        if count:
            state["residual_company_tables"][table] = count
    for doctype in ("Cash Flow Item", "Cash Flow Subtotal", "Journal Entry Account"):
        parents = list(state["worksheets"].values()) if doctype != "Journal Entry Account" else state["journals"]
        state[doctype] = frappe.db.count(doctype, {"parent": ("in", parents)})
    state["journal_exists"] = [name for name in state["journals"] if frappe.db.exists("Journal Entry", name)]
    print(frappe.as_json(state))


def currency_fixture():
    state = json.loads(STATE.read_text(encoding="utf-8"))
    assert state["company"] == COMPANY
    assert "currency_symbol_before" not in state
    state["currency_symbol_before"] = frappe.db.get_value("Currency", "CNY", "symbol")
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    frappe.db.set_value("Currency", "CNY", "symbol", "¥")
    frappe.db.commit()
    frappe.clear_cache()
    print(frappe.as_json({"currency": "CNY", "symbol_before": state["currency_symbol_before"], "symbol": "¥"}))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "inspect", "currency-fixture", "cleanup"))
    args = parser.parse_args()
    os.chdir("/workspace/frappe-bench/sites")
    frappe.init(site="test.localhost", sites_path=".")
    frappe.connect()
    frappe.local.lang = "zh"
    frappe.set_user("Administrator")
    try:
        {"prepare": prepare, "inspect": inspect, "currency-fixture": currency_fixture, "cleanup": cleanup}[args.action]()
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == "__main__":
    main()
