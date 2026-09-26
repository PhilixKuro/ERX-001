#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P1-S3-R1-A  stage 5: harm ranking by CO-OCCURRENCE.

A collision only bites the demo audience where they can see BOTH colliding
labels at once and cannot tell which is which.  Two grades:

  SAME-FORM  two colliding sources are labels/options on the same DocType
             (or on that DocType and one of its child tables, which renders
             inside the parent's grid) -> the user literally sees the same
             Chinese twice on one screen.  Highest harm.
  SAME-FLOW  the colliding sources sit on different DocTypes that the
             walkthrough visits within the same phase, so the user carries the
             word from one screen to the next and it means something else.

Input : Spike/P1S3R1-demoline-intersect.out.json
        Spike/P1S3R1-official-po-collisions.out.json
Read-only.
"""
import io, os, re, sys, json, glob, collections, argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BENCH = os.path.join("frappe-bench", "apps")

# the 23 huanjie grouped into phases, by the DocType each opens
PHASES = {
    "P0 setup (0-3)": ["Company", "Global Defaults", "Fiscal Year", "Account",
                       "Warehouse", "Cost Center", "UOM", "Stock Settings",
                       "Accounts Settings", "Manufacturing Settings",
                       "Transaction Deletion Record"],
    "P1 masters (4-7)": ["Item", "Item Group", "Item Price", "Price List",
                         "Operation", "Workstation", "BOM", "Customer", "Supplier"],
    "P2 procure-to-pay (8-13)": ["Purchase Order", "Purchase Receipt",
                                 "Purchase Invoice", "Payment Entry",
                                 "Mode of Payment", "GL Entry",
                                 "Stock Ledger Entry", "Bin"],
    "P3 order-to-produce (14-20)": ["Quotation", "Sales Order", "Production Plan",
                                    "Work Order", "Job Card", "Stock Entry",
                                    "Stock Entry Type"],
    "P4 deliver-to-cash (21-23)": ["Delivery Note", "Sales Invoice"],
}


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
                idx[j.get("name") or b] = j
    return idx


def strings_of(j):
    """source strings rendered by this DocType's own fields"""
    out = set()
    for f in j.get("fields", []):
        if f.get("label"):
            out.add(f["label"].strip())
        if f.get("fieldtype") == "Select" and f.get("options"):
            for o in str(f["options"]).split("\n"):
                if o.strip():
                    out.add(o.strip())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--inter", default="Spike/P1S3R1-demoline-intersect.out.json")
    ap.add_argument("--po", default="Spike/P1S3R1-official-po-collisions.out.json")
    ap.add_argument("--json", default="Spike/P1S3R1-cooccurrence.out.json")
    a = ap.parse_args()

    idx = index_doctypes()
    po = json.load(io.open(a.po, encoding="utf-8"))["on_demo_line"]

    # expand each phase DocType with its child tables; build screen -> strings
    screens = {}
    dt_phase = {}
    for ph, dts in PHASES.items():
        for dt in dts:
            if dt not in idx:
                continue
            dt_phase[dt] = ph
            s = set(strings_of(idx[dt]))
            for f in idx[dt].get("fields", []):
                if f.get("fieldtype") in ("Table", "Table MultiSelect"):
                    ch = f.get("options")
                    if ch in idx:
                        s |= strings_of(idx[ch])
            screens[dt] = s

    rows = []
    for tgt, srcs in po.items():
        same_form, per_screen = [], {}
        for dt, sset in screens.items():
            hit = sorted(s for s in srcs if s in sset)
            if len(hit) >= 2:
                same_form.append((dt, hit))
            if hit:
                per_screen[dt] = hit
        phases_touched = collections.defaultdict(set)
        for dt, hit in per_screen.items():
            for h in hit:
                phases_touched[dt_phase[dt]].add(h)
        same_flow = [ph for ph, hs in phases_touched.items() if len(hs) >= 2]
        grade = "SAME-FORM" if same_form else ("SAME-FLOW" if same_flow else "SPLIT")
        rows.append({"target": tgt, "sources": srcs, "grade": grade,
                     "same_form": same_form, "same_flow": same_flow,
                     "screens": per_screen})

    order = {"SAME-FORM": 0, "SAME-FLOW": 1, "SPLIT": 2}
    rows.sort(key=lambda r: (order[r["grade"]], -len(r["same_form"]), r["target"]))

    cnt = collections.Counter(r["grade"] for r in rows)
    print("demo-line collision groups graded: %d" % len(rows))
    for g in ("SAME-FORM", "SAME-FLOW", "SPLIT"):
        print("  %-10s %d" % (g, cnt[g]))

    for r in rows:
        print("\n[%s] %s  <= %s" % (r["grade"], r["target"], " / ".join(r["sources"])))
        for dt, hit in sorted(r["same_form"])[:6]:
            print("      SAME FORM %-24s sees: %s" % (dt, " + ".join(hit)))
        if not r["same_form"]:
            for dt, hit in sorted(r["screens"].items())[:6]:
                print("      %-28s %s   (%s)" % (dt, " + ".join(hit), dt_phase[dt]))
        if r["same_flow"]:
            print("      same phase: %s" % "; ".join(sorted(r["same_flow"])))

    json.dump(rows, io.open(a.json, "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)
    print("\njson -> %s" % a.json)


if __name__ == "__main__":
    main()
