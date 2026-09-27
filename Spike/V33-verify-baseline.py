"""V33 post-run site safety verification. Read-only."""

import json
import os

import frappe

OUT = "/workspace/Spike/V33-out"
EXPECT = {
    "GL Entry": 22,
    "Stock Ledger Entry": 12,
    "Account": 95,
    "Company": 1,
    "Financial Report Template": 6,
    "Error Log": 0,
}


def main():
    frappe.init(site="erx.localhost")
    frappe.connect()

    res = {"counts": {}, "ok": True}
    for dt, want in EXPECT.items():
        got = frappe.db.count(dt)
        res["counts"][dt] = {"expected": want, "actual": got, "match": got == want}
        if got != want:
            res["ok"] = False

    fy = [r[0] for r in frappe.db.sql("select name from `tabFiscal Year` order by name")]
    res["fiscal_years"] = {"actual": fy, "expected": ["2026"], "match": fy == ["2026"]}
    if fy != ["2026"]:
        res["ok"] = False

    # any stray v33 artifacts persisted?
    res["stray_v33_rows"] = {
        "gl_entry_v33_voucher": frappe.db.count("GL Entry", {"voucher_no": ("like", "%V33%")}),
        "error_log_v33": frappe.db.count("Error Log", {"error": ("like", "%V33%")}),
        "custom_fields_on_gl_entry": frappe.db.count("Custom Field", {"dt": "GL Entry"}),
    }
    for k, v in res["stray_v33_rows"].items():
        if v:
            res["ok"] = False

    print(json.dumps(res, indent=2, ensure_ascii=False))
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, "verify-baseline.json"), "w", encoding="utf-8") as fh:
        json.dump(res, fh, indent=2, ensure_ascii=False)
    print("BASELINE_OK" if res["ok"] else "BASELINE_MISMATCH")


if __name__ == "__main__":
    try:
        main()
    finally:
        try:
            frappe.db.rollback()
        except Exception:
            pass
        frappe.destroy()
