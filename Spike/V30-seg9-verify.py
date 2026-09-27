# V-30 seg9: final site-safety verification after all probes.
#
# Confirms the documented baseline, that no temporary Python module survives anywhere
# in the app trees, that no exported template JSON was written, and that no probe
# template or probe-authored Error Log row remains.
#
# READ-ONLY apart from a closing rollback.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V30-seg9-verify.py

import glob
import json
import os

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/V30-out/seg9-verify.json"

result = {"probe": "V-30 seg9 final verification"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2000], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

try:
    # ---------- documented baseline ----------
    counts = {}
    for dt in ["GL Entry", "Stock Ledger Entry", "Account", "Company",
               "Financial Report Template", "Fiscal Year", "Error Log"]:
        counts[dt] = frappe.db.count(dt)
    rec("counts", counts)

    expected = {"GL Entry": 22, "Stock Ledger Entry": 12, "Account": 95,
                "Company": 1, "Financial Report Template": 6}
    rec("baseline_matches_expected",
        {k: (counts[k] == v) for k, v in expected.items()})
    rec("all_business_baselines_ok", all(counts[k] == v for k, v in expected.items()))

    fys = frappe.get_all("Fiscal Year", pluck="name")
    rec("fiscal_years", fys)
    rec("fiscal_year_only_2026", fys == ["2026"])

    rec("templates_present", frappe.get_all("Financial Report Template", pluck="name"))
    rec("any_probe_template_left",
        frappe.get_all("Financial Report Template",
                       filters={"template_name": ["like", "%V30%"]}, pluck="name"))
    rec("any_zz_probe_template_left",
        frappe.get_all("Financial Report Template",
                       filters={"template_name": ["like", "ZZ-PROBE%"]}, pluck="name"))

    # ---------- no temporary python module anywhere in the app trees ----------
    app_roots = ["/workspace/frappe-bench/apps/erpnext",
                 "/workspace/frappe-bench/apps/frappe"]
    stray_py = []
    for root in app_roots:
        for pat in ["**/zz_v30*", "**/*v30*", "**/*V30*"]:
            stray_py += glob.glob(os.path.join(root, pat), recursive=True)
    rec("stray_probe_modules_in_app_trees", stray_py)
    rec("no_temp_module_survives", stray_py == [])

    # ---------- no exported template JSON written into the source tree ----------
    exp_dir = os.path.join(frappe.get_app_path("erpnext"), "accounts",
                           "financial_report_template")
    listing = sorted(os.listdir(exp_dir)) if os.path.isdir(exp_dir) else []
    rec("financial_report_template_export_dir_listing", listing)
    suspicious = [f for f in listing
                  if "v30" in f.lower() or "probe" in f.lower() or f.startswith("zz")]
    rec("suspicious_exported_files", suspicious)

    # ---------- Error Log state ----------
    rec("error_log_rows",
        [{"name": r.name, "method": (r.method or "")[:80], "creation": str(r.creation)}
         for r in frappe.get_all("Error Log", fields=["name", "method", "creation"],
                                 order_by="creation")])
    rec("any_probe_authored_error_log",
        frappe.get_all("Error Log", filters={"method": ["like", "%zz_v30%"]},
                       pluck="name"))
    rec("any_v30_marker_error_log",
        frappe.get_all("Error Log", filters={"method": ["like", "%V30%"]},
                       pluck="name"))
    rec("NOTE_error_log_baseline_was_2",
        "seg2 bug deleted the 2 pre-existing rows; tabError Log is MyISAM so rollback "
        "could not restore them. Restore from backup was attempted and DENIED by the "
        "permission system. Unresolved, reported to the user.")

finally:
    frappe.db.rollback()
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
