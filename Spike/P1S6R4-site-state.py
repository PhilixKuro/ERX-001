import frappe
import os


def main():
    os.chdir("/workspace/frappe-bench/sites")
    frappe.init(site="test.localhost", sites_path=".")
    frappe.connect()
    try:
        result = {}
        for name in ("Cash Flow", "Cash Flow Worksheet"):
            exists = frappe.db.exists("DocType", name)
            result[name] = {
                "doctype": bool(exists),
                "table": frappe.db.table_exists(name),
                "rows": frappe.db.count(name) if exists else None,
            }
        print(frappe.as_json(result))
    finally:
        frappe.destroy()


if __name__ == "__main__":
    main()
