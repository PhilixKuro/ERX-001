#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
P1-S3-R1-A  stage 2 of the CR-001 collision scan: classify the groups.

Not every collision is a defect.  `Item / Items / For Item / Material` all
landing on 物料 is CORRECT -- they are inflections / prepositional forms of
one concept and SHOULD share a target.  The defect shape is two
SEMANTICALLY DISTINCT sources landing on one target, because the reader then
cannot tell which field they are looking at.

So: normalise each source (case, plural, leading preposition / qualifier,
punctuation, doubled spaces).  If every source in a group normalises to the
same key, the group is BENIGN.  Otherwise it is a GENUINE collision and needs
one side's wording changed.

Input : Spike/P1S3R1-collision-scan.out.json  (produced by the sibling script)
Output: stdout report + optional --json
Read-only w.r.t. the repo.
"""
import io, os, re, sys, json, collections, argparse

sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

ROOT = r"D:\ERX-001"
DEMO = os.path.join(ROOT, "docs", "01-需求摸底", "S01-场景摸底",
                    "0-P1-S1文档", "最小闭环操作稿.md")

# leading words that only mark a field's role, not its meaning
LEAD = r"(?:against|for|from|to|set|in|on|by|is|enter|include|source|target|" \
       r"applicable\s+on|linked|planned|required|reqd(?:\s+by)?|of)"
# trailing words that likewise do not change the concept
TAIL = r"(?:no\.?|name|head|amount|qty|quantity|date|time|list|catalogue|" \
        r"doctype|document|field|fieldname|account)"

IRREG = {
    "modes": "mode", "taxes": "tax", "creditors": "creditor",
    "debtors": "debtor", "statuses": "status", "states": "state",
}


def norm(s):
    t = s.strip().lower()
    t = re.sub(r"[\s_]+", " ", t)
    t = re.sub(r"[&/().,:'\-]", " ", t)
    t = re.sub(r"\s+", " ", t).strip()
    # strip repeated leading qualifiers
    for _ in range(3):
        t2 = re.sub(r"^%s\s+" % LEAD, "", t)
        if t2 == t:
            break
        t = t2
    words = []
    for w in t.split():
        w = IRREG.get(w, w)
        if w.endswith("ies") and len(w) > 4:
            w = w[:-3] + "y"
        elif w.endswith("sses"):
            w = w[:-2]
        elif w.endswith("s") and not w.endswith("ss") and len(w) > 2:
            w = w[:-1]
        if w.endswith("ed") and len(w) > 4:
            w = w[:-2]
        if w.endswith("ing") and len(w) > 5:
            w = w[:-3]
        words.append(w)
    t = " ".join(words)
    # drop pure role suffixes
    for _ in range(2):
        t2 = re.sub(r"\s+%s$" % TAIL, "", t)
        if t2 == t:
            break
        t = t2
    return t or s.strip().lower()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp",
                    default="Spike/P1S3R1-collision-scan.out.json")
    ap.add_argument("--json")
    a = ap.parse_args()

    d = json.load(io.open(a.inp, encoding="utf-8"))
    on = d["on_demo_line"]
    demo_lines = io.open(DEMO, encoding="utf-8").read().split("\n")

    def cite(needle, cap=4):
        """line numbers in the operation script where `needle` shows up"""
        out = []
        for i, ln in enumerate(demo_lines, 1):
            if needle and needle in ln:
                out.append(i)
                if len(out) >= cap:
                    break
        return out

    benign, genuine = {}, {}
    for tgt, g in on.items():
        keys = {norm(s) for s in g["sources"]}
        rec = dict(g)
        rec["norm_keys"] = sorted(keys)
        rec["target_lines"] = cite(tgt)
        if len(keys) == 1:
            benign[tgt] = rec
        else:
            # group sources by normalised key so the report shows the split
            byk = collections.defaultdict(list)
            for s in g["sources"]:
                byk[norm(s)].append(s)
            rec["clusters"] = {k: sorted(v) for k, v in byk.items()}
            genuine[tgt] = rec

    print("demo-line candidate groups      : %d" % len(on))
    print("  BENIGN (inflection/role only) : %d" % len(benign))
    print("  GENUINE (distinct concepts)   : %d" % len(genuine))
    print("  of GENUINE, target cited in")
    print("  the operation script          : %d"
          % sum(1 for g in genuine.values() if g["target_lines"]))
    print("\n=== GENUINE collisions on the demo line ===")
    order = sorted(genuine, key=lambda t: (-len(genuine[t]["clusters"]),
                                           -len(genuine[t]["target_lines"]), t))
    for tgt in order:
        g = genuine[tgt]
        cl = " || ".join(" ~ ".join(v) for v in g["clusters"].values())
        print("%-14s <= %s\n%14s  doc lines: %s"
              % (tgt, cl, "", g["target_lines"] or "-"))

    if a.json:
        json.dump({"benign": benign, "genuine": genuine},
                  io.open(a.json, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=1)
        print("\njson -> %s" % a.json)


if __name__ == "__main__":
    main()
