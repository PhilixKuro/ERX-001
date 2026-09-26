#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P1-S3-R1-A  stage 4: the SAME collision scan against the ACTUALLY INSTALLED
translation source.

Why this script exists
----------------------
The 914-group figure comes from Reference/zelin-tech-erpnext_china's zh.csv.
But frappe-bench/sites/apps.txt lists only `frappe` and `erpnext` -- the zelin
app is NOT installed on the demo site.  So what the 23-huanjie walkthrough
actually renders is frappe/locale/zh.po + erpnext/locale/zh.po.  A term
standard that must hold on the DEMO must be measured against those.

This script scans the installed .po files the same way (one target claimed by
>=2 distinct msgids = a collision group), honouring msgctxt: a msgid carrying
a msgctxt is a separate key and is reported separately, since that is exactly
the `context` split mechanism.

Read-only.
"""
import io, os, re, sys, json, glob, collections, argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

BENCH = os.path.join("frappe-bench", "apps")
INSTALLED = ["frappe", "erpnext"]      # per frappe-bench/sites/apps.txt


def parse_po(path):
    """Yield (lineno, msgctxt_or_None, msgid, msgstr). Handles continuations."""
    lines = io.open(path, encoding="utf-8", errors="replace").read().split("\n")
    i, n = 0, len(lines)

    def take(kw, i):
        m = re.match(r'^%s\s+"(.*)"\s*$' % kw, lines[i])
        if not m:
            return None, i
        val = m.group(1)
        j = i + 1
        while j < n:
            m2 = re.match(r'^"(.*)"\s*$', lines[j])
            if not m2:
                break
            val += m2.group(1)
            j += 1
        return val, j

    while i < n:
        if lines[i].startswith("msgctxt "):
            start = i + 1
            ctx, i = take("msgctxt", i)
            mid, i = take("msgid", i)
            mstr, i = take("msgstr", i)
            if mid is not None:
                yield start, ctx, mid, (mstr or "")
            continue
        if lines[i].startswith("msgid "):
            start = i + 1
            mid, i = take("msgid", i)
            mstr, i = take("msgstr", i)
            if mid is not None:
                yield start, None, mid, (mstr or "")
            continue
        i += 1


def unescape(s):
    return s.replace('\\"', '"').replace("\\n", "\n").replace("\\\\", "\\")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", default="Spike/P1S3R1-official-po-collisions.out.json")
    ap.add_argument("--intersect",
                    default="Spike/P1S3R1-demoline-intersect.out.json")
    a = ap.parse_args()

    plain, ctxrows, sources = {}, [], {}
    for app in INSTALLED:
        p = os.path.join(BENCH, app, app, "locale", "zh.po")
        if not os.path.exists(p):
            print("MISSING %s" % p)
            continue
        cnt = 0
        for ln, ctx, mid, mstr in parse_po(p):
            mid, mstr = unescape(mid), unescape(mstr)
            if not mid or not mstr:
                continue
            cnt += 1
            if ctx:
                ctxrows.append((app, ln, ctx, mid, mstr))
            else:
                # later app wins, matching translate.py get_translations_from_apps
                plain[mid] = mstr
                sources[mid] = "%s/locale/zh.po:%d" % (app, ln)
        print("%-8s zh.po entries with a translation: %d" % (app, cnt))

    rev = collections.defaultdict(set)
    for s, t in plain.items():
        rev[t].add(s)
    groups = {t: sorted(v) for t, v in rev.items() if len(v) >= 2}

    print("\nINSTALLED-baseline figures (frappe+erpnext zh.po, per apps.txt)")
    print("  unique msgid (no msgctxt) : %d" % len(plain))
    print("  msgctxt entries           : %d" % len(ctxrows))
    print("  distinct targets          : %d" % len(rev))
    print("  COLLISION GROUPS (>=2)    : %d" % len(groups))
    print("  msgids involved           : %d" % sum(len(v) for v in groups.values()))

    # intersect with the demo-line visible strings computed by the sibling script
    if os.path.exists(a.intersect):
        inter = json.load(io.open(a.intersect, encoding="utf-8"))
        demo_targets = set(inter["result"].keys())
        # which of OUR groups involve a source that the sibling script saw rendered
        vis = set()
        for g in inter["result"].values():
            vis |= set(g["visible"].keys())
        both = {t: v for t, v in groups.items()
                if len([s for s in v if s in vis]) >= 2}
        print("  of those, >=2 msgids visible on the demo line: %d" % len(both))
        print("\n=== INSTALLED-baseline collisions felt on the demo line ===")
        for t in sorted(both, key=lambda x: (-len(both[x]), x)):
            hits = [s for s in both[t] if s in vis]
            print("%-16s <= %s" % (t, " / ".join(hits)))
            for s in hits:
                print("%18s%s   %s" % ("", s, sources.get(s, "?")))
        json.dump({"groups": groups, "on_demo_line": both,
                   "sources": sources,
                   "ctx_entries": [list(r) for r in ctxrows]},
                  io.open(a.json, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("\njson -> %s" % a.json)


if __name__ == "__main__":
    main()
