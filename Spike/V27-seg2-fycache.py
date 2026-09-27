"""
V-27 seg2: DIAGNOSTIC for the fiscal-year cache artifact.

Run 1 of V27-pcv-yearend.py submitted the 2025 JE fine. Run 2 failed at
je.submit() with "Date 2025-06-30 is not in any active Fiscal Year", even though
FY2025 had just been inserted in the same transaction. Redis is not
transactional, so a rolled-back FY2025 (or a stale list that predates it) can
survive in the `fiscal_years` cache between processes and poison the next run.

This segment measures WHICH it is instead of guessing, and validates the fix.
`fiscal_years` is a Redis HASH keyed by company (accounts/utils.py:146,171), and
FiscalYear.on_update only calls delete_key (fiscal_year.py:37).

Writes: inserts Fiscal Year 2025 inside a transaction, rolls back. No commit.
"""

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
COMPANY = "华东弹簧"
OUT = "/workspace/Spike/V27-out/seg2-fycache.json"

res = {}


def rec(k, v):
    res[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:1500], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")


def cache_state(tag):
    """What the fiscal_years hash holds, and what the resolver returns."""
    out = {}
    try:
        out["hget_for_company"] = frappe.cache().hget("fiscal_years", COMPANY)
    except Exception as e:
        out["hget_for_company__err"] = str(e)
    try:
        out["hgetall"] = {k: v for k, v in (frappe.cache().hgetall("fiscal_years") or {}).items()}
    except Exception as e:
        out["hgetall__err"] = str(e)
    try:
        out["local_cache_keys_matching_fy"] = [
            k for k in list(getattr(frappe.local, "cache", {}) or {}) if "fiscal_year" in str(k)
        ]
    except Exception as e:
        out["local_cache__err"] = str(e)
    out["db_fiscal_years"] = [r["name"] for r in frappe.db.get_all("Fiscal Year", fields=["name"])]
    rec("cache_state__" + tag, out)
    return out


def try_resolve(tag):
    from erpnext.accounts.utils import get_fiscal_year
    try:
        fy = get_fiscal_year("2025-06-30", company=COMPANY, raise_on_missing=False)
        rec("resolve_2025_06_30__" + tag, {"ok": bool(fy), "value": fy})
        return bool(fy)
    except Exception as e:
        rec("resolve_2025_06_30__" + tag, {"ok": False, "err": str(e)})
        return False


try:
    # ---- state as inherited from the previous process (the suspect) ----
    cache_state("0_process_start")
    rec("resolve_before_any_write", try_resolve("0_process_start"))

    # ---- insert FY2025 (this fires on_update -> delete_key) ----
    fy = frappe.get_doc({
        "doctype": "Fiscal Year", "year": "2025",
        "year_start_date": "2025-01-01", "year_end_date": "2025-12-31",
    })
    fy.insert(ignore_permissions=True)
    rec("fy2025_inserted", {"name": fy.name})
    cache_state("1_after_fy_insert")
    ok_plain = try_resolve("1_after_fy_insert")

    # ---- the candidate fix: explicitly drop the company key from the hash ----
    fixes_applied = []
    if not ok_plain:
        try:
            frappe.cache().hdel("fiscal_years", COMPANY)
            fixes_applied.append("hdel(fiscal_years, company)")
        except Exception as e:
            fixes_applied.append("hdel failed: " + str(e))
        try:
            frappe.cache().delete_key("fiscal_years")
            fixes_applied.append("delete_key(fiscal_years)")
        except Exception as e:
            fixes_applied.append("delete_key failed: " + str(e))
        # local cache can shadow redis (redis_wrapper.hget checks it first)
        try:
            frappe.local.cache = {}
            fixes_applied.append("reset frappe.local.cache")
        except Exception as e:
            fixes_applied.append("local reset failed: " + str(e))
    rec("fixes_applied", fixes_applied or "none needed")
    cache_state("2_after_fix")
    ok_fixed = try_resolve("2_after_fix")

    rec("DIAGNOSIS", {
        "resolved_without_fix": ok_plain,
        "resolved_after_cache_drop": ok_fixed,
        "conclusion": (
            "on_update's delete_key was sufficient; failure was elsewhere"
            if ok_plain else
            ("stale fiscal_years cache was the cause; dropping it fixes resolution"
             if ok_fixed else
             "NOT a cache problem -- resolution still fails with cache cleared")),
    })

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-2500:]})

finally:
    frappe.db.rollback()
    # leave Redis clean for the next process: FY2025 no longer exists in the DB
    try:
        frappe.cache().hdel("fiscal_years", COMPANY)
        frappe.cache().delete_key("fiscal_years")
        frappe.local.cache = {}
        rec("cleanup_cache", "fiscal_years dropped after rollback")
    except Exception as e:
        rec("cleanup_cache", "error: " + str(e))
    rec("fiscal_years_after_rollback",
        [r["name"] for r in frappe.db.get_all("Fiscal Year", fields=["name"])])
    cache_state("3_final")

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(res, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
