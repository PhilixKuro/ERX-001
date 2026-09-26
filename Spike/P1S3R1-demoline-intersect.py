#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P1-S3-R1-A  stage 3: intersect the GENUINE collision groups with strings that
actually RENDER on the demo line.

"On the demo line" is not "the word appears in the operation script" -- that
over-collects (e.g. shang <= Up / on).  A source string is on the demo line
only if the user can SEE it while walking the 23 huanjie, i.e. it is one of:

  (a) a field label of a demo-line DocType          -> renders as form label
  (b) a Select option of a field of such a DocType  -> renders as a value
  (c) a __("...") literal in that DocType own .js / _list.js
      -> renders as a button / indicator / dialog title

Demo-line DocTypes are the ones the operation script has the user open, plus
their child tables (child-table labels render inside the parent grid).

Also records, per hit, WHICH translation call site renders it, because
__(label, null, df.parent) is context-capable while a bare __("Payment") is
not -- that distinction decides whether a fix can be a context row or must be
a wording change.

Read-only.  Outputs JSON + a report.
"""
import io, os, re, sys, json, glob, collections, argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BENCH = os.path.join("frappe-bench", "apps")

# The DocTypes the operation script actually has the user open a form / list of.
# Derived by hand from the 23 huanjie headings + their steps.
DEMO_DOCTYPES = [
    # 0-3 setup
    "Company", "Global Defaults", "Fiscal Year", "Account", "Warehouse",
    "Cost Center", "UOM", "UOM Conversion Factor", "Stock Settings",
    "Manufacturing Settings", "Accounts Settings", "Transaction Deletion Record",
    # 4-7 masters
    "Item", "Item Group", "Item Price", "Price List", "Operation",
    "Workstation", "BOM", "Customer", "Supplier",
    # 8-13 procure-to-pay
    "Purchase Order", "Purchase Receipt", "Purchase Invoice", "Payment Entry",
    "Mode of Payment", "GL Entry", "Stock Ledger Entry", "Bin",
    # 14-20 order-to-produce
    "Quotation", "Sales Order", "Production Plan", "Work Order", "Job Card",
    "Stock Entry", "Stock Entry Type",
    # 21-23 deliver-to-cash
    "Delivery Note", "Sales Invoice",
]


def index_doctypes():
    idx = {}
    for app in ("erpnext", "frappe"):
        pat = os.path.join(BENCH, app, app, "**", "doctype", "*", "*.json")
        for p in glob.glob(pat, recursive=True):
            b = os.path.basename(p)[:-5]
            if b != os.path.basename(os.path.dirname(p)):
                continue
            try:
                j = json.load(io.open(p, encoding="utf-8"))
            except Exception:
                continue
            if j.get("doctype") != "DocType":
                continue
            idx[j.get("name") or b] = (p, j)
    return idx


def child_tables(j):
    out = set()
    for f in j.get("fields", []):
        if f.get("fieldtype") in ("Table", "Table MultiSelect") and f.get("options"):
            out.add(f["options"])
    return out


def harvest(idx, dt):
    """Return {source_string: [render-site descriptions]} for one DocType."""
    if dt not in idx:
        return {}
    path, j = idx[dt]
    out = collections.defaultdict(list)
    for f in j.get("fields", []):
        lab = (f.get("label") or "").strip()
        if lab:
            out[lab].append(
                "%s label:%s [CTX-OK __(df.label,null,df.parent)]"
                % (dt, f.get("fieldname")))
        if f.get("fieldtype") == "Select" and f.get("options"):
            for o in str(f["options"]).split("\n"):
                o = o.strip()
                if o:
                    out[o].append(
                        "%s select-option:%s [CTX-OK select.js:172 __(v,null,doctype)]"
                        % (dt, f.get("fieldname")))
    # the DocType own client scripts
    base = os.path.dirname(path)
    for js in sorted(glob.glob(os.path.join(base, "*.js"))):
        try:
            src = io.open(js, encoding="utf-8", errors="replace").read()
        except Exception:
            continue
        for i, ln in enumerate(src.split("\n"), 1):
            for m in re.finditer(r'__\(\s*"([^"\\]{1,60})"\s*(,|\))', ln):
                lit, close = m.group(1), m.group(2)
                bare = close == ")"
                out[lit].append("%s:%d %s" % (
                    os.path.relpath(js).replace("\\", "/"), i,
                    "[BARE - no context possible without upstream patch]"
                    if bare else "[has extra args]"))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--classify", default="Spike/P1S3R1-collision-classify.out.json")
    ap.add_argument("--json", default="Spike/P1S3R1-demoline-intersect.out.json")
    a = ap.parse_args()

    cls = json.load(io.open(a.classify, encoding="utf-8"))
    genuine = cls["genuine"]

    idx = index_doctypes()
    scope = list(DEMO_DOCTYPES)
    for dt in DEMO_DOCTYPES:
        if dt in idx:
            scope += sorted(child_tables(idx[dt][1]))
    scope = sorted(set(scope))
    missing = [d for d in scope if d not in idx]

    rendered = collections.defaultdict(list)
    for dt in scope:
        for s, sites in harvest(idx, dt).items():
            rendered[s] += sites

    print("demo-line DocTypes in scope (incl. child tables): %d" % len(scope))
    if missing:
        print("  NOT FOUND in this bench: %s" % ", ".join(missing))
    print("distinct renderable strings harvested           : %d" % len(rendered))

    result = {}
    for tgt, g in genuine.items():
        hits = {s: rendered[s] for s in g["sources"] if s in rendered}
        if len(hits) >= 2:                      # >=2 sources both visible
            result[tgt] = {"sources": g["sources"], "clusters": g["clusters"],
                           "visible": hits}
    print("GENUINE groups with >=2 sources visible on demo line: %d" % len(result))

    one = {t: g for t, g in genuine.items()
           if len([s for s in g["sources"] if s in rendered]) == 1}
    print("  (groups with exactly 1 visible source, no clash felt): %d" % len(one))

    print("\n=== CLASHES FELT ON THE DEMO LINE ===")
    for tgt in sorted(result, key=lambda t: (-len(result[t]["visible"]), t)):
        r = result[tgt]
        print("\n%s  <=  %s" % (tgt, " / ".join(sorted(r["visible"]))))
        for s, sites in sorted(r["visible"].items()):
            print("    %-32s %s" % (s, sites[0]))
            for extra in sites[1:3]:
                print("    %-32s %s" % ("", extra))

    json.dump({"scope": scope, "result": result, "single_visible": sorted(one)},
              io.open(a.json, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("\njson -> %s" % a.json)


if __name__ == "__main__":
    main()
