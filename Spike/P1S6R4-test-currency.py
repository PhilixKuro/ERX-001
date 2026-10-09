import json
import os
from pathlib import Path

import frappe


def main():
    os.chdir("/workspace/frappe-bench/sites")
    frappe.init(site="test.localhost", sites_path=".")
    frappe.connect()
    frappe.set_user("Administrator")
    try:
        currency = frappe.get_doc("Currency", "CNY")
        before = currency.symbol
        if before != "¥":
            currency.symbol = "¥"
            currency.save(ignore_permissions=True)
            frappe.db.commit()
            frappe.clear_cache()
        after = frappe.db.get_value("Currency", "CNY", "symbol")
        assert after == "¥"
        result = {"site": frappe.local.site, "currency": "CNY", "symbol_before": before,
                  "symbol_after": after, "changed": before != after,
                  "authorization": "用户裁决：保留 Part1 未完成，先修测试站的货币配置"}
        path = Path("/workspace/Spike/P1S6R4-test-currency.json")
        previous = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
        previous.append(result)
        path.write_text(json.dumps(previous, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(frappe.as_json(result))
    finally:
        frappe.db.rollback()
        frappe.destroy()


if __name__ == "__main__":
    main()
