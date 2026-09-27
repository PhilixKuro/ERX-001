# V-31 seg9 -- final site-safety verification. READ-ONLY.
#
# Confirms the exact baseline the task brief specifies, after all V-31 probes have run:
#   GL Entry 22 / Stock Ledger Entry 12 / Account 95 / Company 1 /
#   Financial Report Template 6 / Fiscal Year only 2026 / Error Log still 0.
#
# Also confirms no probe template survived, no stray template JSON landed in the erpnext
# source tree, and nothing landed in the site's files dirs.
#
# Error Log is MyISAM -- rollback does not undo it. Any row found here is REPORTED, never
# deleted: another probe this round destroyed two pre-existing rows by deleting "rows not
# in my baseline". Positive scoping only, and this probe deletes nothing at all.
#
# Run:
#   docker exec -i -e PYTHONUTF8=1 -e PYTHONIOENCODING=utf-8 \
#     -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V31-seg9-verify.py

import glob
import json
import os
import subprocess

import frappe

SITE = "erx.localhost"
OUT_DIR = "/workspace/Spike/V31-out"
OUT = os.path.join(OUT_DIR, "seg9-verify.json")

result = {"probe": "V-31 seg9 final site-safety verification (read-only)"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2000], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")
os.makedirs(OUT_DIR, exist_ok=True)

expected = {"GL Entry": 22, "Stock Ledger Entry": 12, "Account": 95, "Company": 1,
            "Financial Report Template": 6, "Error Log": 0}
actual = {k: frappe.db.count(k) for k in expected}
fy = sorted(r.name for r in frappe.get_all("Fiscal Year", fields=["name"]))

rec("BASELINE_VERIFICATION", {
    "expected": expected, "actual": actual,
    "all_match": actual == expected,
    "per_item": {k: {"expected": expected[k], "actual": actual[k], "ok": actual[k] == expected[k]}
                 for k in expected},
    "Fiscal Year": {"expected": ["2026"], "actual": fy, "ok": fy == ["2026"]},
})

rec("templates_in_db", sorted(r.name for r in frappe.get_all(
    "Financial Report Template", fields=["name"])))
rec("any_probe_template_survived", sorted(
    r.name for r in frappe.get_all("Financial Report Template", fields=["name"])
    if "PROBE" in r.name.upper() or r.name.upper().startswith("ZZ")))

rec("error_log_rows_verbatim", frappe.get_all(
    "Error Log", fields=["name", "method", "creation"], limit=50))
rec("other_nonInnoDB_tables", {
    "Data Import Log": frappe.db.count("Data Import Log"),
    "Access Log": frappe.db.count("Access Log"),
    "Prepared Report": frappe.db.count("Prepared Report"),
    "Translation": frappe.db.count("Translation"),
    "File": frappe.db.count("File"),
})
rec("Report_prepared_report_flag", frappe.db.get_value(
    "Report", "Custom Financial Statement", "prepared_report"))

# stray exported template JSON in the erpnext source tree
strays = []
for pat in ("*probe*", "*PROBE*", "*v31*", "*V31*", "*zz*", "*ZZ*"):
    strays += glob.glob(frappe.get_app_path(
        "erpnext", "accounts", "financial_report_template", pat))
    strays += glob.glob(frappe.get_app_path(
        "erpnext", "accounts", "doctype", "financial_report_template", pat))
rec("stray_exported_template_files", sorted(set(strays)))
rec("exported_template_dir_listing", sorted(
    os.path.basename(p) for p in glob.glob(frappe.get_app_path(
        "erpnext", "accounts", "financial_report_template", "*"))))

# site files dirs + /tmp jars
sf = []
for d in (frappe.get_site_path("private", "files"), frappe.get_site_path("public", "files")):
    for pat in ("*V31*", "*v31*", "*PROBE*", "*probe*", "*glyph*", "*.pdf", "*.xlsx", "*.csv"):
        sf += glob.glob(os.path.join(d, pat))
rec("stray_files_in_site_files_dirs", sorted(set(sf)))
rec("tmp_cookie_jars", sorted(glob.glob("/tmp/*.jar")))

# independent check: git status of the two app trees
for app in ("frappe", "erpnext"):
    cp = subprocess.run(
        ["sh", "-c", "cd /workspace/frappe-bench/apps/%s && git status --porcelain" % app],
        capture_output=True, text=True)
    rec("git_status_" + app, cp.stdout.strip().splitlines() or ["(clean)"])

rec("files_V31_produced", sorted(os.path.basename(p)
                                for p in glob.glob(os.path.join(OUT_DIR, "*"))))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print("\nWROTE " + OUT, flush=True)
