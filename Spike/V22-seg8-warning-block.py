# V-22 segment 8: name the exact warning that silently blocked segment 6/7.
#
# importer.py:85-92 in Importer.import_data():
#       warnings = self.import_file.get_warnings()
#       warnings = [w for w in warnings if w.get("type") != "info"]
#       if warnings:
#           self.data_import.db_set("template_warnings", json.dumps(warnings))
#           return                      <-- silent: no exception, no log, no row
# and get_warnings() (:590-604) sums ImportFile + per-COLUMN + per-ROW warnings.
# Row warnings (Row.__init__ :648-662) carry NO "type" key at all, so a row-length
# mismatch is automatically non-ignorable.
#
# Segment 6 mapped 余额 (column 5) to bank_account, so the file's 8 headers became
# 9 columns after add_bank_account() appended a literal Bank Account header -- while
# every DATA row still had 8 values. That is exactly a row-length mismatch.
#
# This segment prints the warning list for both files to prove which is which.
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg8-warning-block.py

import json

import frappe
from frappe.core.doctype.data_import.importer import ImportFile

SITE = "erx.localhost"
OUT = "/workspace/Spike/V22-out/seg8-warning-block.json"

result = {"segment": "8 the warning that silently blocked the import"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

files = frappe.get_all("File", filters={"file_name": ["like", "V22-sample-statement%"]},
                       fields=["name", "file_name", "file_url"])
rec("files", files)

MAP_UIFLOW = {"0": "date", "1": "description", "2": "withdrawal", "3": "deposit",
              "4": "bank_account", "5": "bank_party_name", "6": "reference_number",
              "7": "currency"}
MAP_GATED = {"0": "date", "1": "description", "2": "withdrawal", "3": "deposit",
             "5": "bank_party_name", "6": "reference_number", "7": "currency"}

for f in files:
    tag = "uiflow" if "uiflow" in f.file_name else ("gated" if "gated" in f.file_name else "plain")
    m = MAP_UIFLOW if tag != "gated" else MAP_GATED
    try:
        imp = ImportFile("Bank Transaction", f.file_url,
                         frappe._dict({"column_to_field_map": m}), "Insert New Records")
        rec(f"{tag}_header_row", imp.raw_data[0])
        rec(f"{tag}_n_header_cols", len(imp.raw_data[0]))
        rec(f"{tag}_n_data_cols_row1", len(imp.raw_data[1]) if len(imp.raw_data) > 1 else None)
        w = imp.get_warnings()
        rec(f"{tag}_all_warnings", w)
        blocking = [x for x in w if x.get("type") != "info"]
        rec(f"{tag}_BLOCKING_warnings", blocking)
        rec(f"{tag}_would_silently_return", bool(blocking))
    except Exception:
        rec(f"{tag}_ERROR", frappe.get_traceback())

rec("MECHANISM",
    "after add_bank_account() appends a literal 'Bank Account' header the header row "
    "has 9 entries while every data row still has 8, so Row.__init__ (importer.py:648-662) "
    "emits a warning with NO 'type' key; import_data (:85-92) treats any warning whose "
    "type != 'info' as blocking and returns WITHOUT importing, without raising, leaving "
    "Bank Statement Import.status = Pending and zero Data Import Log rows")

# and confirm where that message is parked -- the only place a user could see it
bsis = frappe.get_all("Bank Statement Import",
                      fields=["name", "status", "template_warnings", "import_file"],
                      order_by="creation desc")
for b in bsis:
    rec(f"bsi_{b.name[-15:]}_status", b.status)
    rec(f"bsi_{b.name[-15:]}_template_warnings", b.template_warnings)

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
