#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P1-S3-R1-A  stage 6: re-do the demo-line intersect WITHOUT routing through
zelin's group list.

Why: P1S3R1-official-po-collisions.py computed "on the demo line" by asking
whether a msgid appears in `vis`, and `vis` was harvested from the zelin
GENUINE groups only.  So a po collision whose sources are rendered on the demo
line but were never part of a zelin genuine group could be missed.  This script
builds the rendered-string set directly from the demo-line DocTypes (same
harvest rules as P1S3R1-demoline-intersect.py) and intersects the INSTALLED po
collision groups against it.

Read-only.
"""
import io, os, re, sys, json, glob, collections

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
BENCH = os.path.join("frappe-bench", "apps")

DEMO_DOCTYPES = [
    "Company", "Global Defaults", "Fiscal Year", "Account", "Warehouse",
    "Cost Center", "UOM", "UOM Conversion Factor", "Stock Settings",
    "Manufacturing Settings", "Accounts Settings", "Transaction Deletion Record",
    "Item", "Item Group", "Item Price", "Price List", "Operation",
    "Workstation", "BOM", "Customer", "Supplier",
    "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Payment Entry",
    "Mode of Payment", "GL Entry", "Stock Ledger Entry", "Bin",
    "Quotation", "Sales Order", "Production Plan", "Work Order", "Job Card",
    "Stock Entry", "Stock Entry Type",
    "Delivery Note", "Sales Invoice",
]


def index_doctypes():
    idx = {}
    for app in ("erpnext", "frappe"):
        for p in glob.glob(os.path.join(BENCH, app, app, "**", "doctype",
                                        "*", "*.json"), recursive=True):
            b = os.path.basename(p)[:-5]
            if b != os.path.basename(os.path.dirname(p)):
                continue
            try:
                j = json.load(io.open(p, encoding="utf-8"))
            except Exception:
                continue
            if j.get("doctype") == "DocType":
                idx[j.get("name") or b] = (p, j)
    return idx


def harvest(idx, dt):
    if dt not in idx:
        return {}
    path, j = idx[dt]
    out = collections.defaultdict(list)
    for f in j.get("fields", []):
        lab = (f.get("label") or "").strip()
        if lab:
            out[lab].append("%s label:%s [CTX-OK]" % (dt, f.get("fieldname")))
        if f.get("fieldtype") == "Select" and f.get("options"):
            for o in str(f["options"]).split("\n"):
                o = o.strip()
                if o:
                    out[o].append("%s option:%s [CTX-OK]" % (dt, f.get("fieldname")))
    for js in sorted(glob.glob(os.path.join(os.path.dirname(path), "*.js"))):
        try:
            src = io.open(js, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for i, ln in enumerate(src.split("\n"), 1):
            for m in re.finditer(r'__\(\s*"([^"\\]{1,60})"\s*(,|\))', ln):
                out[m.group(1)].append("%s:%d %s" % (
                    os.path.relpath(js).replace("\\", "/"), i,
                    "[BARE]" if m.group(2) == ")" else "[has args]"))
    return out


def main():
    idx = index_doctypes()
    scope = list(DEMO_DOCTYPES)
    for dt in DEMO_DOCTYPES:
        if dt in idx:
            for f in idx[dt][1].get("fields", []):
                if f.get("fieldtype") in ("Table", "Table MultiSelect") and f.get("options"):
                    scope.append(f["options"])
    scope = sorted(set(scope))

    rendered = collections.defaultdict(list)
    for dt in scope:
        for s, sites in harvest(idx, dt).items():
            rendered[s] += sites

    po = json.load(io.open("Spike/P1S3R1-official-po-collisions.out.json",
                           encoding="utf-8"))
    groups, src = po["groups"], po["sources"]
    old = set(po["on_demo_line"])

    direct, one = {}, {}
    for t, v in groups.items():
        hit = [s for s in v if s in rendered]
        if len(hit) >= 2:
            direct[t] = {"sources": v, "visible": {s: rendered[s][:4] for s in hit}}
        elif len(hit) == 1:
            one[t] = hit

    print("demo-line DocTypes in scope (incl. child tables): %d" % len(scope))
    print("distinct renderable strings harvested           : %d" % len(rendered))
    print("po collision groups (installed baseline)        : %d" % len(groups))
    print("  >=2 msgids rendered on demo line (DIRECT)    : %d" % len(direct))
    print("  exactly 1 rendered (no clash felt)           : %d" % len(one))
    print("  off the demo line entirely                   : %d"
          % (len(groups) - len(direct) - len(one)))
    print("\nprevious zelin-routed figure                   : %d" % len(old))
    extra = sorted(set(direct) - old)
    lost = sorted(old - set(direct))
    print("  found by DIRECT but missed before : %d" % len(extra))
    print("  counted before but not by DIRECT  : %d" % len(lost))
    for t in extra:
        hits = [s for s in direct[t]["visible"]]
        print("    + %-16s <= %s" % (t, " / ".join(hits)))
        for s in hits:
            print("      %22s %-34s %s" % ("", s, src.get(s, "?")))
    for t in lost:
        print("    - %-16s <= %s" % (t, " / ".join(groups[t])))

    json.dump({"direct": direct, "single": one},
              io.open("Spike/P1S3R1-po-demoline-direct.out.json", "w",
                      encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\njson -> Spike/P1S3R1-po-demoline-direct.out.json")


if __name__ == "__main__":
    main()
