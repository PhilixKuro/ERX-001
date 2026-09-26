#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P1-S3-R1-A  CR-001 target-side term standard: mechanical collision scan.

Purpose
-------
1. Reproduce the "914 collision groups" figure reported in
   docs/01-需求摸底/S02-演示蓝图/R01-图谱讨论/P1-S2-R1-A参考项目-zelin-翻译.md:93
   from Reference/zelin-tech-erpnext_china/erpnext_china/translations/zh.csv
2. Intersect those groups with the demo line, whose boundary is defined by
   docs/01-需求摸底/S01-场景摸底/0-P1-S1文档/最小闭环操作稿.md (23 环节).

Definitions
-----------
collision group := one target Chinese string claimed by >=2 distinct English
                   source strings.  (This is the OPPOSITE shape from
                   "one source, several meanings", which `context` solves.)

Demo-line vocabulary is harvested mechanically from the operation script:
  - English inside full-width or half-width parentheses:  中文（English）
  - text inside backticks
  - bare ASCII words/phrases on their own in table cells
A group is a demo-line CANDIDATE when the target Chinese string occurs
verbatim in the operation script, OR any of its source strings does.

Read-only.  Writes nothing except its own report to stdout / --json.
"""
import csv, sys, re, json, io, os, collections, argparse

ROOT = r"D:\ERX-001"
CSV  = os.path.join(ROOT, "Reference", "zelin-tech-erpnext_china",
                    "erpnext_china", "translations", "zh.csv")
DEMO = os.path.join(ROOT, "docs", "01-需求摸底", "S01-场景摸底",
                    "0-P1-S1文档", "最小闭环操作稿.md")

CJK = re.compile(r"[\u4e00-\u9fff]")


def load_csv(path):
    """Return (plain, ctx) where plain: source->target for 2-col rows,
    ctx: list of (source, target, context) for 3-col rows."""
    plain, ctx = {}, []
    with io.open(path, "r", encoding="utf-8", newline="") as fh:
        for row in csv.reader(fh):
            if not row or not row[0].strip():
                continue
            if len(row) >= 3 and row[2].strip():
                ctx.append((row[0], row[1].strip(), row[2].strip()))
            elif len(row) >= 2:
                plain[row[0]] = row[1].strip()
    return plain, ctx


def collisions(plain):
    """target -> sorted list of sources, for targets with >=2 sources."""
    rev = collections.defaultdict(set)
    for src, tgt in plain.items():
        if not tgt:
            continue
        rev[tgt].add(src)
    return {t: sorted(s) for t, s in rev.items() if len(s) >= 2}


def demo_vocab(path):
    txt = io.open(path, "r", encoding="utf-8").read()
    toks = set()
    # 中文（English） and 中文(English)
    for m in re.findall(r"[（(]\s*([A-Za-z][A-Za-z0-9 _/&.\-]{1,60}?)\s*[）)]", txt):
        toks.add(m.strip())
    # `backticked`
    for m in re.findall(r"`([^`\n]{1,80})`", txt):
        toks.add(m.strip())
    return txt, toks


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", help="dump machine-readable result here")
    ap.add_argument("--show", type=int, default=0, help="print N demo-line groups")
    a = ap.parse_args()

    plain, ctx = load_csv(CSV)
    groups = collisions(plain)
    demo_txt, demo_toks = demo_vocab(DEMO)
    demo_toks_lc = {t.lower() for t in demo_toks}

    on_line, off_line = {}, {}
    for tgt, srcs in groups.items():
        why = []
        if tgt and tgt in demo_txt:
            why.append("target-in-doc")
        hit_src = [s for s in srcs
                   if s in demo_toks or s.lower() in demo_toks_lc]
        if hit_src:
            why.append("source-in-doc:" + "|".join(hit_src))
        (on_line if why else off_line)[tgt] = {"sources": srcs, "why": why}

    print("zh.csv                     : %s" % CSV)
    print("2-col (plain) unique source: %d" % len(plain))
    print("3-col (context) rows       : %d" % len(ctx))
    print("distinct targets           : %d" % len({v for v in plain.values() if v}))
    print("COLLISION GROUPS (>=2 src) : %d" % len(groups))
    print("  sources involved         : %d" % sum(len(v) for v in groups.values()))
    print("demo-line vocab tokens     : %d  (from %s)" % (len(demo_toks), os.path.basename(DEMO)))
    print("  groups touching demo line: %d" % len(on_line))
    print("  groups off demo line     : %d" % len(off_line))
    # distribution by group size
    dist = collections.Counter(len(v) for v in groups.values())
    print("group-size distribution    : " + ", ".join(
        "%d src x%d" % (k, dist[k]) for k in sorted(dist)))

    if a.show:
        print("\n--- demo-line candidate groups (target <= sources) ---")
        for tgt in sorted(on_line, key=lambda t: (-len(on_line[t]["sources"]), t))[:a.show]:
            g = on_line[tgt]
            print(u"%-14s <= %s   [%s]" % (tgt, " / ".join(g["sources"]), ",".join(g["why"])))

    if a.json:
        with io.open(a.json, "w", encoding="utf-8") as fh:
            json.dump({"total_groups": len(groups),
                       "on_demo_line": on_line,
                       "off_demo_line_count": len(off_line),
                       "off_demo_line_sample": dict(list(off_line.items())[:40]),
                       "context_rows": ctx},
                      fh, ensure_ascii=False, indent=1)
        print("\njson -> %s" % a.json)


if __name__ == "__main__":
    main()
