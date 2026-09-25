# V-19 segment 1: does option A (zelin verbatim -- 4 overrides PLUS the three
# Company doc_events, including erpnext_china_create_charts) build a complete
# Chinese chart of accounts?
#
# This is the go/no-go segment.  It performs the ONE write of the segment:
# inserting test company #1.  Everything after the insert is measurement.
#
# Run (cwd MUST be .../sites, else the frappe logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V19-seg1-a-company.py

import io
import json
import sys
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "V19A案一"
ABBR = "V19A"
CHART = "小企业会计准则(2024)"
BASE = "华东弹簧"
CHART_PATH = ("/workspace/frappe-bench/apps/erx_v19/erx_v19/chart_of_accounts/"
              "custom_accounts/chart_of_accounts/cn_smes_chart_of_accounts2024.json")
OUT = "/workspace/Spike/V19-out/seg1-a-company.json"

result = {"segment": "1 option A company creation + chart integrity"}


def rec(k, v):
    result[k] = v
    print(f"[{k}] {v}", flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")
frappe.flags.in_test = False

# ---- 0. preconditions -------------------------------------------------------
rec("installed_apps", frappe.get_installed_apps())
rec("hook_doc_events_Company", frappe.get_hooks("doc_events", {}).get("Company", "ABSENT"))
rec("hook_override_count", len(frappe.get_hooks("override_whitelisted_methods", {})))
rec("account_count_before", frappe.db.count("Account"))
rec("error_log_count_before", frappe.db.count("Error Log"))
rec("baseline_accounts_before", frappe.db.count("Account", {"company": BASE}))
rec("flag_country_change_before", frappe.flags.get("country_change", "unset"))
rec("flag_ignore_coa_before", frappe.local.flags.get("ignore_chart_of_accounts", "unset"))

if frappe.db.exists("Company", COMPANY):
    rec("precondition_ERROR", COMPANY + " already exists; aborting")
    frappe.destroy()
    sys.exit(2)

# ---- 1. the insert ----------------------------------------------------------
doc = frappe.get_doc({
    "doctype": "Company",
    "company_name": COMPANY,
    "abbr": ABBR,
    "default_currency": "CNY",
    "country": "China",
    "chart_of_accounts": CHART,
    "create_chart_of_accounts_based_on": "Standard Template",
})

rec("insert_attempt", "starting company.insert()")
try:
    doc.insert()
    frappe.db.commit()
    result["insert_failed"] = False
    rec("insert_result", "NO EXCEPTION")
except Exception as e:
    frappe.db.rollback()
    result["insert_failed"] = True
    rec("insert_result", "RAISED")
    rec("exception_type", type(e).__name__)
    rec("exception_str", str(e))
    tb = traceback.format_exc()
    result["traceback"] = tb
    print("=== TRACEBACK BEGIN ===", flush=True)
    print(tb, flush=True)
    print("=== TRACEBACK END ===", flush=True)

# flag state at the END of the insert -- segment 2 question 1 needs this
rec("flag_country_change_after_insert", frappe.flags.get("country_change", "unset"))
rec("flag_ignore_coa_after_insert", frappe.local.flags.get("ignore_chart_of_accounts", "unset"))
rec("flag_ignore_update_nsm_after_insert", frappe.local.flags.get("ignore_update_nsm", "unset"))
rec("doc_attr_erpnext_china_in_insert", doc.get("erpnext_china_in_insert"))
rec("company_exists_after", bool(frappe.db.exists("Company", COMPANY)))

if result["insert_failed"]:
    rec("ABORT", "insert raised; no chart to measure")
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1, default=str)
    print("wrote " + OUT, flush=True)
    frappe.destroy()
    sys.exit(1)

# ---- 2. counts --------------------------------------------------------------
rec("account_count_total_after", frappe.db.count("Account"))
rec("account_count_test_company", frappe.db.count("Account", {"company": COMPANY}))
rec("baseline_accounts_after", frappe.db.count("Account", {"company": BASE}))
rec("error_log_count_after", frappe.db.count("Error Log"))

# ---- 3. JSON vs DB, both directions ----------------------------------------
with io.open(CHART_PATH, encoding="utf-8") as f:
    tree = json.load(f)["tree"]

# the metadata keys the zelin _import_accounts skips (7 of them; erpnext uses
# get_chart_metadata_fields() which also has account_category -- this chart has
# no account_category key anywhere, so the two lists do not diverge here)
META = ["account_name", "account_number", "account_type", "root_type",
        "is_group", "tax_rate", "account_currency"]

json_nodes = []


def walk(node, parent_name):
    for k, v in node.items():
        if k in META:
            continue
        if isinstance(v, dict):
            json_nodes.append({
                "account_name": k,
                "account_number": (v.get("account_number") or ""),
                "is_group": v.get("is_group"),
                "root_type": v.get("root_type"),
                "account_type": v.get("account_type"),
                "parent": parent_name,
            })
            walk(v, k)


walk(tree, None)
rec("json_recursive_node_count", len(json_nodes))

db_rows = frappe.get_all("Account", filters={"company": COMPANY},
                         fields=["name", "account_number", "account_name", "is_group",
                                 "root_type", "report_type", "account_type",
                                 "parent_account", "lft", "rgt"])
rec("db_row_count", len(db_rows))

json_pairs = set()
for n in json_nodes:
    json_pairs.add((n["account_number"], n["account_name"]))
db_pairs = set()
for r in db_rows:
    db_pairs.add(((r["account_number"] or ""), r["account_name"]))
rec("json_pair_count_deduped", len(json_pairs))
rec("db_pair_count_deduped", len(db_pairs))
rec("in_JSON_not_in_DB", sorted(json_pairs - db_pairs))
rec("in_DB_not_in_JSON", sorted(db_pairs - json_pairs))

# ---- 4. six top-level root_types -------------------------------------------
roots = [r for r in db_rows if not r["parent_account"]]
rec("root_count", len(roots))
rec("roots", sorted([(r["account_number"], r["account_name"], r["root_type"],
                      r["report_type"], r["is_group"]) for r in roots]))
hist = {}
for r in db_rows:
    hist[r["root_type"]] = hist.get(r["root_type"], 0) + 1
rec("root_type_histogram", dict(sorted(hist.items())))
gh = {}
for r in db_rows:
    gh[r["is_group"]] = gh.get(r["is_group"], 0) + 1
rec("is_group_histogram", dict(sorted(gh.items())))

# ---- 5. the 20 VAT details --------------------------------------------------
want = ["22210%02d" % i for i in range(1, 21)]
vat_rows = frappe.get_all("Account",
                          filters={"company": COMPANY, "account_number": ("in", want)},
                          fields=["account_number", "account_name", "parent_account",
                                  "is_group", "root_type", "account_type"],
                          order_by="account_number")
rec("vat_detail_found_count", len(vat_rows))
found_numbers = set()
for r in vat_rows:
    found_numbers.add(r["account_number"])
rec("vat_detail_missing", sorted(set(want) - found_numbers))
rec("vat_details", [(r["account_number"], r["account_name"], r["parent_account"],
                     r["is_group"], r["account_type"]) for r in vat_rows])
parent_split = {}
for r in vat_rows:
    parent_split.setdefault(r["parent_account"], []).append(r["account_number"])
rec("vat_detail_parent_split",
    dict((k, (len(v), v[0], v[-1])) for k, v in parent_split.items()))
rec("acct_2221000", frappe.db.get_value(
    "Account", {"company": COMPANY, "account_number": "2221000"},
    ["name", "account_name", "parent_account", "is_group"], as_dict=True))
rec("acct_2221", frappe.db.get_value(
    "Account", {"company": COMPANY, "account_number": "2221"},
    ["name", "account_name", "parent_account", "is_group"], as_dict=True))

# ---- 6. tree integrity ------------------------------------------------------
rec("nsm_bad_rows_test_company", frappe.db.sql(
    "select count(*) from tabAccount where company=%s and (lft is null or rgt is null or lft>=rgt)",
    COMPANY)[0][0])
rec("nsm_bad_rows_site_wide", frappe.db.sql(
    "select count(*) from tabAccount where lft is null or rgt is null or lft>=rgt")[0][0])
rec("lft_rgt_span_test_company", frappe.db.sql(
    "select min(lft), max(rgt) from tabAccount where company=%s", COMPANY)[0])
rec("orphan_parent_refs", frappe.db.sql(
    "select count(*) from tabAccount a where a.company=%s and a.parent_account is not null "
    "and a.parent_account != '' and not exists "
    "(select 1 from tabAccount b where b.name=a.parent_account)", COMPANY)[0][0])
rec("cross_company_parent_refs", frappe.db.sql(
    "select count(*) from tabAccount a join tabAccount b on b.name=a.parent_account "
    "where a.company=%s and b.company!=%s", (COMPANY, COMPANY))[0][0])
rec("duplicate_name_suffix_rows", frappe.db.sql(
    "select account_number, account_name from tabAccount where company=%s "
    "and account_name regexp ' [0-9]+$'", COMPANY))
rec("duplicate_name_suffix_count", frappe.db.sql(
    "select count(*) from tabAccount where company=%s and account_name regexp ' [0-9]+$'",
    COMPANY)[0][0])
rec("report_type_mismatch_rows", frappe.db.sql(
    "select count(*) from tabAccount where company=%s and "
    "((root_type in ('Asset','Liability','Equity') and report_type!='Balance Sheet') or "
    " (root_type in ('Income','Expense') and report_type!='Profit and Loss'))", COMPANY)[0][0])
rec("null_root_type_rows", frappe.db.sql(
    "select count(*) from tabAccount where company=%s and (root_type is null or root_type='')",
    COMPANY)[0][0])
rec("tree_rebuild_error_logs", frappe.get_all(
    "Error Log", filters={"error": ("like", "%create_charts2%")}, fields=["name", "creation"]))

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=1, default=str)
print("wrote " + OUT, flush=True)

frappe.destroy()
