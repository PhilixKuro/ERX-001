# REV AUDIT part B: is there a redis-cache residue from V-25's rolled-back
# Fiscal Year insert?
#
# FiscalYear.on_update() does frappe.cache().delete_key("fiscal_years").
# erpnext.accounts.utils._get_fiscal_years() hset's the list into that hash.
# If the V-25 probe's in-transaction FY 2025 got read back through
# get_fiscal_year() before rollback, the cache could still advertise a fiscal
# year that no longer exists in the database.
#
# READ-ONLY. Nothing is written to the DB. Nothing is deleted from the cache
# here either -- this only LOOKS. No frappe.db.commit(), no frappe.enqueue.
#
# Run (cwd MUST be .../sites):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/Rev-P1S4R2-b-cache.py

import json
import os

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/Rev-out/b-cache.json"

result = {"probe": "REV audit part B: fiscal_years cache residue check (read-only)"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=True, default=str)[:1500], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

try:
    # truth from the DB
    rec("fiscal_years_in_db", frappe.db.sql(
        "select name, year_start_date, year_end_date from `tabFiscal Year`"
        " order by year_start_date", as_dict=True))

    # what the cache currently advertises, BEFORE anything repopulates it
    cache = frappe.cache()
    try:
        raw = cache.hgetall("fiscal_years")
        decoded = {}
        for k, v in (raw or {}).items():
            kk = k.decode() if isinstance(k, bytes) else str(k)
            try:
                decoded[kk] = frappe.parse_json(v.decode() if isinstance(v, bytes) else v)
            except Exception:
                decoded[kk] = str(v)[:400]
        rec("cache_hash_fiscal_years", decoded)
    except Exception as e:
        rec("cache_hgetall_error", str(e))

    # every redis key that mentions fiscal
    try:
        keys = []
        for k in cache.get_keys("*fiscal*"):
            keys.append(k.decode() if isinstance(k, bytes) else str(k))
        rec("redis_keys_matching_fiscal", sorted(keys))
    except Exception as e:
        rec("redis_keys_error", str(e))

    # does the app-level accessor hand back a phantom year?
    from erpnext.accounts.utils import _get_fiscal_years, get_fiscal_years

    company = frappe.db.get_value("Company", {}, "name")
    try:
        rec("_get_fiscal_years_for_company", [dict(r) for r in _get_fiscal_years(company=company)])
    except Exception as e:
        rec("_get_fiscal_years_error", str(e))
    try:
        rec("_get_fiscal_years_no_company", [dict(r) for r in _get_fiscal_years(company=None)])
    except Exception as e:
        rec("_get_fiscal_years_no_company_error", str(e))
    try:
        rec("get_fiscal_years_labels", [list(r) for r in get_fiscal_years(company=company)])
    except Exception as e:
        rec("get_fiscal_years_labels_error", str(e))

    # the Fiscal Year link-field query the report filter uses: any phantom 2025?
    rec("fy_names_via_get_all", frappe.get_all("Fiscal Year", pluck="name"))
    rec("phantom_2025_in_db", bool(frappe.db.exists("Fiscal Year", "2025")))

    # also check the document cache, which is a separate layer
    try:
        rec("doc_cache_2025", frappe.cache().hget("Fiscal Year", "2025"))
    except Exception as e:
        rec("doc_cache_error", str(e))

except Exception as e:
    import traceback
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-2000:]})

finally:
    frappe.db.rollback()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
