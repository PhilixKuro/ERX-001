import argparse
import json
import os
from pathlib import Path

import frappe
from frappe.model.document import Document

from frappe_china.tests.utils import make_cn_company


STATE = Path("/workspace/Spike/P1S6R4-rename-probe.json")


def prepare():
    assert frappe.db.exists("DocType", "Cash Flow")
    assert not frappe.db.exists("DocType", "Cash Flow Worksheet")
    assert not STATE.exists()
    frappe.local.lang = "zh"
    frappe.set_user("Administrator")
    company = make_cn_company("_FCT S6 rename probe", "S6REN")
    fiscal_year = frappe.db.get_value("Fiscal Year", {"year_start_date": "2025-01-01"}, "name")
    assert fiscal_year
    doc = Document({"doctype": "Cash Flow", "company": company.name,
                    "fiscal_year": fiscal_year, "month": 1})
    doc.name = "_FCT-S6-rename-probe"
    doc.append("items", {"cash_flow_code": "15", "debit": 1})
    doc.db_insert()
    for child in doc.get_all_children():
        child.db_insert()
    frappe.db.commit()
    evidence = {"company": company.name, "name": doc.name,
                "old_rows": frappe.db.count("Cash Flow", {"name": doc.name}),
                "child_parenttype_before": frappe.db.get_value("Cash Flow Item", {"parent": doc.name}, "parenttype")}
    STATE.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(frappe.as_json(evidence))


def verify():
    evidence = json.loads(STATE.read_text(encoding="utf-8"))
    assert not frappe.db.table_exists("Cash Flow")
    doc = frappe.get_doc("Cash Flow Worksheet", evidence["name"])
    assert len(doc.items) == 1
    assert doc.items[0].parenttype == "Cash Flow Worksheet"
    from frappe_china.patches.s6_rename_cash_flow_worksheet import execute

    execute()
    evidence.update({"new_rows": frappe.db.count("Cash Flow Worksheet", {"name": doc.name}),
                     "old_table_exists": frappe.db.table_exists("Cash Flow"),
                     "child_parenttype_after": doc.items[0].parenttype,
                     "controller": type(doc).__name__, "idempotent": True})
    STATE.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(frappe.as_json(evidence))


def cleanup():
    evidence = json.loads(STATE.read_text(encoding="utf-8"))
    frappe.delete_doc("Cash Flow Worksheet", evidence["name"], ignore_permissions=True)
    frappe.delete_doc("Company", evidence["company"], ignore_permissions=True)
    frappe.db.commit()
    assert not frappe.db.exists("Cash Flow Worksheet", evidence["name"])
    assert not frappe.db.exists("Cash Flow Item", {"parent": evidence["name"]})
    assert not frappe.db.exists("Company", evidence["company"])
    evidence["cleanup_verified"] = True
    STATE.write_text(json.dumps(evidence, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(frappe.as_json(evidence))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=("prepare", "verify", "cleanup"))
    args = parser.parse_args()
    os.chdir("/workspace/frappe-bench/sites")
    frappe.init(site="test.localhost", sites_path=".")
    frappe.connect()
    try:
        {"prepare": prepare, "verify": verify, "cleanup": cleanup}[args.action]()
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == "__main__":
    main()
