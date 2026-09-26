# V-22 segment 16: the one residue class that cannot be undone -- naming series
# counters. Documents are gone, but tabSeries keeps its high-water mark, so the
# next Payment Entry / Bank Transaction on this site will skip the numbers this
# probe consumed. Report it honestly rather than fake-resetting it (rewinding a
# series counter is riskier than the gap it would close).
#
# Run:
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V22-seg16-series-residue.py

import json

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/V22-out/seg16-series-residue.json"

result = {"segment": "16 naming series residue"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()

rec("series_rows", frappe.db.sql("select name, current from tabSeries order by name", as_list=True))
rec("payment_entries_live", frappe.get_all("Payment Entry", fields=["name"], order_by="name"))
rec("bank_transactions_live", frappe.db.count("Bank Transaction"))
rec("RESIDUE_NOTE",
    "ACC-BTN-2026- was created by this probe and its counter sits at 12; ACC-PAY-2026- was "
    "advanced from 7 to 10. The documents are all deleted, but the counters keep their "
    "high-water mark, so the next Bank Transaction starts at 13 and the next Payment Entry "
    "at 11. This is the only residue left. It is cosmetic (a gap in numbering) and was NOT "
    "rewound on purpose: editing tabSeries downward risks a future name collision.")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2, default=str)
print(f"\nWROTE {OUT}", flush=True)
