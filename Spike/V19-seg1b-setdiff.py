# V-19 segment 1b: segment 1's set difference compared a JSON account_number
# (an unquoted int in the chart file) against a DB varchar, so every row showed
# up on both sides.  This re-runs the same comparison with both sides coerced to
# str, plus a parent-edge comparison.  Read-only.
#
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V19-seg1b-setdiff.py

import io
import json

import frappe

SITE = "erx.localhost"
COMPANY = "V19A案一"
ABBR = "V19A"
CHART_PATH = ("/workspace/frappe-bench/apps/erx_v19/erx_v19/chart_of_accounts/"
              "custom_accounts/chart_of_accounts/cn_smes_chart_of_accounts2024.json")
OUT = "/workspace/Spike/V19-out/seg1b-setdiff.json"

result = {"segment": "1b normalized JSON-vs-DB set difference"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + repr(v), flush=True)


frappe.init(site=SITE)
frappe.connect()

with io.open(CHART_PATH, encoding="utf-8") as f:
    tree = json.load(f)["tree"]

META = ["account_name", "account_number", "account_type", "root_type",
        "is_group", "tax_rate", "account_currency"]

json_nodes = []


def walk(node, parent_key):
    for k, v in node.items():
        if k in META:
            continue
        if isinstance(v, dict):
            num = v.get("account_number")
            num = "" if num is None else str(num).strip()
            json_nodes.append({"account_name": k, "account_number": num,
                               "is_group": v.get("is_group"),
                               "root_type": v.get("root_type"),
                               "account_type": v.get("account_type"),
                               "parent_key": parent_key})
            walk(v, (num, k))


walk(tree, None)
rec("json_node_count", len(json_nodes))

db_rows = frappe.get_all("Account", filters={"company": COMPANY},
                         fields=["name", "account_number", "account_name", "is_group",
                                 "root_type", "report_type", "account_type",
                                 "parent_account"])
rec("db_row_count", len(db_rows))

json_pairs = set()
for n in json_nodes:
    json_pairs.add((n["account_number"], n["account_name"]))
db_pairs = set()
for r in db_rows:
    db_pairs.add((r["account_number"] or "", r["account_name"]))
rec("json_pairs_deduped", len(json_pairs))
rec("db_pairs_deduped", len(db_pairs))
rec("in_JSON_not_in_DB", sorted(json_pairs - db_pairs))
rec("in_DB_not_in_JSON", sorted(db_pairs - json_pairs))

# ---- parent edges ----------------------------------------------------------
# DB account name = "<number> - <account_name> - <abbr>" (or without the number
# when there is none), so rebuild the JSON-side expected parent name and compare
# the edge sets.
def db_name(num, nm):
    if num:
        return num + " - " + nm + " - " + ABBR
    return nm + " - " + ABBR


json_edges = set()
for n in json_nodes:
    child = db_name(n["account_number"], n["account_name"])
    if n["parent_key"] is None:
        json_edges.add((child, None))
    else:
        json_edges.add((child, db_name(n["parent_key"][0], n["parent_key"][1])))

db_edges = set()
for r in db_rows:
    db_edges.add((r["name"], r["parent_account"] or None))

rec("json_edge_count", len(json_edges))
rec("db_edge_count", len(db_edges))
rec("edges_in_JSON_not_in_DB", sorted(json_edges - db_edges))
rec("edges_in_DB_not_in_JSON", sorted(db_edges - json_edges))

# ---- is_group / root_type / account_type agreement -------------------------
json_by_pair = {}
for n in json_nodes:
    json_by_pair[(n["account_number"], n["account_name"])] = n

is_group_mismatch = []
account_type_mismatch = []
for r in db_rows:
    key = (r["account_number"] or "", r["account_name"])
    j = json_by_pair.get(key)
    if not j:
        continue
    # the JSON only states is_group explicitly on some nodes; identify_is_group
    # derives it from whether the node has non-metadata children
    has_children = any(x["parent_key"] == key for x in json_nodes)
    expect_group = 1 if (j["is_group"] or has_children) else 0
    if int(r["is_group"] or 0) != int(expect_group):
        is_group_mismatch.append((key, r["is_group"], expect_group))
    if (j["account_type"] or "") != (r["account_type"] or ""):
        account_type_mismatch.append((key, j["account_type"], r["account_type"]))

rec("is_group_mismatch_count", len(is_group_mismatch))
rec("is_group_mismatch", is_group_mismatch[:20])
rec("account_type_mismatch_count", len(account_type_mismatch))
rec("account_type_mismatch", account_type_mismatch[:20])

# duplicate (number, name) pairs inside the JSON itself
seen = {}
for n in json_nodes:
    k = (n["account_number"], n["account_name"])
    seen[k] = seen.get(k, 0) + 1
rec("json_duplicate_pairs", dict((k, v) for k, v in seen.items() if v > 1))
# duplicate names ignoring the number (this is what add_suffix_if_duplicate keys on)
namekeys = {}
for n in json_nodes:
    if n["account_number"]:
        kk = n["account_number"] + " - " + n["account_name"].strip().lower()
    else:
        kk = n["account_name"].strip().lower()
    namekeys[kk] = namekeys.get(kk, 0) + 1
rec("json_duplicate_suffix_keys", dict((k, v) for k, v in namekeys.items() if v > 1))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print("wrote " + OUT, flush=True)

frappe.destroy()
