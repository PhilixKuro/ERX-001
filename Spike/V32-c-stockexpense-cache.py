# V-32 (c): Does book_stock_expense_gl_entries' per-doc cache leak across documents?
#
# G3 (Spike/S4-G3-整段让位开关.md:80 and :157) claims:
#   ":896 has a per-doc cache `self._book_stock_expense_enabled`; changing the setting
#    mid-document-lifecycle does not take effect. NOT a process-level trap."
# and at :157 admits: "per-doc or does it leak across documents -- depends on the
#   controller instance lifecycle, NOT VERIFIED."
#
# The code under test, erpnext/controllers/stock_controller.py:896-902:
#     def book_stock_expense_enabled(self):
#         if not hasattr(self, "_book_stock_expense_enabled"):
#             self._book_stock_expense_enabled = cint(
#                 frappe.db.get_single_value("Accounts Settings", "book_stock_expense_gl_entries"))
#         return self._book_stock_expense_enabled
#
# There are TWO caches stacked here, and the question "is it per-document" has a
# different answer at each layer. A probe that only tests the `self._` attribute would
# answer the wrong question, so both are tested:
#   L1  self._book_stock_expense_enabled   -- per controller INSTANCE
#   L2  frappe.db.get_single_value's own value_cache (frappe/database/database.py:900-901
#       stores, :926 fills) -- per DB CONNECTION, i.e. process-wide, cleared only in
#       commit()/rollback() (:1193, :1214) and by clear_document_cache (:2321)
# A leak at L2 reaches a document that has a completely fresh controller instance, so
# it is a genuine cross-document leak even if L1 is perfectly per-instance.
#
# A third route can defeat "per-instance" entirely: frappe.get_cached_doc
# (frappe/model/document.py:2278-2292) returns a doc from redis. If the cached payload
# carries the _book_stock_expense_enabled attribute, a later request gets a stale value
# on the SAME document -- worse than the in-lifecycle staleness G3 described. Tested too.
#
# SITE SAFETY
#   - NOTHING IS SUBMITTED. Only `frappe.new_doc` / `frappe.get_doc` (reads), plus
#     frappe.db.set_single_value writes to tabSingles (InnoDB, confirmed by
#     V32-seg0-recon), all inside one transaction and rolled back.
#   - Deliberately avoided: submitting a Purchase Receipt. That path reaches
#     repost_item_valuation.py, which carries frappe.db.commit() at :397 and :465 and
#     frappe.enqueue at :646/:658 -- unrollbackable, so out of bounds under rule 2.
#     Consequently this probe does NOT claim anything about the GL entries actually
#     produced; it answers only the cache-semantics question that was asked.
#   - Grepped the touched paths: purchase_receipt.py, buying_controller.py and
#     stock_controller.py contain NEITHER frappe.db.commit() NOR frappe.enqueue.
#     frappe.db.set_single_value (database.py:843-872) does a delete+insert on tabSingles
#     then clear_document_cache -- no commit.
#   - The switch's original value is captured first and restored by the rollback; the
#     probe re-reads it at the end and reports before/after.
#   - tabError Log is MyISAM: rollback does NOT undo it. Cleanup is POSITIVELY SCOPED --
#     only rows carrying this probe's own marker, never by exclusion.
#   - No frappe.db.commit() anywhere in this file.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -e PYTHONUTF8=1 -e PYTHONIOENCODING=utf-8 \
#     -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V32-c-stockexpense-cache.py

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
OUTDIR = "/workspace/Spike/V32-out"
OUT = os.path.join(OUTDIR, "c-stockexpense-cache.json")

MARKER = "V32PROBEC"
SETTING = "book_stock_expense_gl_entries"
ATTR = "_book_stock_expense_enabled"

result = {"probe": "V-32 (c) does the book_stock_expense per-doc cache leak across docs?"}


def rec(k, v):
    result[k] = v
    print("{0} = {1}".format(k, json.dumps(v, ensure_ascii=False, default=str)))


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

el_baseline = frappe.db.count("Error Log")
rec("error_log_baseline", el_baseline)

ORIGINAL = None

try:
    ORIGINAL = frappe.db.get_single_value("Accounts Settings", SETTING)
    rec("phase0_original_setting_value", ORIGINAL)
    rec(
        "phase0_singles_row",
        frappe.db.sql(
            "select value from tabSingles where doctype='Accounts Settings' and field=%s",
            SETTING,
            as_dict=True,
        ),
    )
    rec("phase0_purchase_receipts", frappe.get_all("Purchase Receipt", fields=["name", "docstatus"]))

    def fresh_pr():
        """A brand-new, UNSAVED Purchase Receipt controller instance. Writes nothing."""
        return frappe.new_doc("Purchase Receipt")

    # ------------------------------------------------------------------ phase 1
    # Is the attribute absent before the first call? (i.e. is the cache lazily built)
    p1 = {}
    d = fresh_pr()
    p1["attr_present_on_brand_new_instance"] = hasattr(d, ATTR)
    p1["first_call_returns"] = d.book_stock_expense_enabled()
    p1["attr_present_after_first_call"] = hasattr(d, ATTR)
    p1["attr_value_after_first_call"] = getattr(d, ATTR, None)
    rec("phase1_lazy_cache_shape", p1)

    # ------------------------------------------------------------------ phase 2
    # G3's actual claim: flip the setting, and the SAME instance keeps the old answer.
    p2 = {}
    p2["before_flip"] = d.book_stock_expense_enabled()
    flipped = 0 if int(ORIGINAL or 0) == 1 else 1
    p2["flipped_setting_to"] = flipped
    frappe.db.set_single_value("Accounts Settings", SETTING, flipped)
    p2["db_value_after_flip"] = frappe.db.get_single_value("Accounts Settings", SETTING)
    p2["same_instance_after_flip"] = d.book_stock_expense_enabled()
    p2["L1_same_instance_is_stale"] = p2["same_instance_after_flip"] == p2["before_flip"]
    p2["L1_stale_despite_db_changed"] = str(p2["db_value_after_flip"]) != str(
        p2["same_instance_after_flip"]
    )
    rec("phase2_L1_same_instance_staleness", p2)

    # ------------------------------------------------------------------ phase 3
    # THE ASKED QUESTION: does a DIFFERENT document see the flipped value, or does the
    # first document's cached answer bleed into it?
    p3 = {}
    d2 = fresh_pr()
    p3["second_doc_attr_present_before_call"] = hasattr(d2, ATTR)
    p3["second_doc_value"] = d2.book_stock_expense_enabled()
    p3["first_doc_value"] = d.book_stock_expense_enabled()
    p3["db_value"] = frappe.db.get_single_value("Accounts Settings", SETTING)
    p3["L1_second_doc_sees_current_db_value"] = str(p3["second_doc_value"]) == str(p3["db_value"])
    p3["L1_leaks_across_documents"] = (
        p3["second_doc_attr_present_before_call"]
        or str(p3["second_doc_value"]) == str(p3["first_doc_value"]) != str(p3["db_value"])
    )
    # a third instance, and a real (saved) document rather than a new_doc
    saved_name = frappe.db.get_value("Purchase Receipt", {}, "name")
    p3["saved_doc_used"] = saved_name
    if saved_name:
        d3 = frappe.get_doc("Purchase Receipt", saved_name)
        p3["saved_doc_attr_present_before_call"] = hasattr(d3, ATTR)
        p3["saved_doc_value"] = d3.book_stock_expense_enabled()
        p3["saved_doc_sees_current_db_value"] = str(p3["saved_doc_value"]) == str(p3["db_value"])
    p3["class_level_attr_present"] = hasattr(type(d), ATTR)
    p3["instances_are_distinct_objects"] = id(d) != id(d2)
    rec("phase3_L1_cross_document_leak", p3)

    # ------------------------------------------------------------------ phase 4
    # L2: frappe.db.get_single_value's OWN value_cache is per-connection (process-wide).
    # If tabSingles is changed WITHOUT going through set_single_value (which invalidates),
    # a brand-new instance still gets a stale answer -- a genuine cross-document leak at
    # a layer G3 never named.
    p4 = {}
    p4["value_cache_key_present_before"] = SETTING in dict(
        frappe.db.value_cache.get("Accounts Settings", {})
    )
    p4["value_cache_content_before"] = dict(frappe.db.value_cache.get("Accounts Settings", {}))
    raw_flip = 1 if int(flipped) == 0 else 0
    frappe.db.sql(
        "update tabSingles set value=%s where doctype='Accounts Settings' and field=%s",
        (raw_flip, SETTING),
    )
    p4["raw_sql_set_singles_to"] = raw_flip
    p4["raw_db_read_bypassing_cache"] = frappe.db.sql(
        "select value from tabSingles where doctype='Accounts Settings' and field=%s", SETTING
    )
    p4["get_single_value_after_raw_update"] = frappe.db.get_single_value("Accounts Settings", SETTING)
    p4["get_single_value_cache_False"] = frappe.db.get_single_value(
        "Accounts Settings", SETTING, cache=False
    )
    p4["L2_get_single_value_is_stale_after_raw_write"] = str(
        p4["get_single_value_after_raw_update"]
    ) != str(raw_flip)
    d4 = fresh_pr()
    p4["brand_new_instance_value"] = d4.book_stock_expense_enabled()
    p4["L2_leaks_into_brand_new_document"] = str(p4["brand_new_instance_value"]) != str(raw_flip)
    # buying_controller.py:345 reads the setting directly, with no self._ cache at all --
    # but it still goes through get_single_value, so it inherits the SAME L2 staleness.
    from frappe.utils import cint

    p4["buying_controller_style_direct_read"] = cint(
        frappe.db.get_single_value("Accounts Settings", SETTING)
    )
    p4["L2_affects_uncached_reader_too"] = str(p4["buying_controller_style_direct_read"]) != str(
        raw_flip
    )
    rec("phase4_L2_connection_level_value_cache", p4)

    # ------------------------------------------------------------------ phase 5
    # What clears L2? Distinguish the mechanisms rather than asserting one.
    p5 = {}
    frappe.clear_document_cache("Accounts Settings", "Accounts Settings")
    p5["after_clear_document_cache"] = frappe.db.get_single_value("Accounts Settings", SETTING)
    p5["clear_document_cache_fixes_L2"] = str(p5["after_clear_document_cache"]) == str(raw_flip)
    d5 = fresh_pr()
    p5["new_instance_after_cache_clear"] = d5.book_stock_expense_enabled()
    p5["new_instance_now_correct"] = str(p5["new_instance_after_cache_clear"]) == str(raw_flip)

    # Does L1 survive L2 invalidation? The comparison must be made against a DB value
    # that DIFFERS from what the warm instance cached, otherwise "equal" and "stale"
    # are indistinguishable. So drive the DB to the OPPOSITE of the warm cached value.
    warm_cached = getattr(d, ATTR, None)
    target = 0 if int(warm_cached or 0) == 1 else 1
    p5["warm_instance_cached_value"] = warm_cached
    p5["db_driven_to_opposite_of_warm"] = target
    frappe.db.set_single_value("Accounts Settings", SETTING, target)
    p5["db_value_now"] = frappe.db.get_single_value("Accounts Settings", SETTING, cache=False)
    p5["criterion_is_distinguishing"] = str(p5["db_value_now"]) != str(warm_cached)
    p5["warm_instance_returns"] = d.book_stock_expense_enabled()
    p5["L1_survives_L2_invalidation"] = str(p5["warm_instance_returns"]) == str(warm_cached) and str(
        p5["warm_instance_returns"]
    ) != str(p5["db_value_now"])
    d5b = fresh_pr()
    p5["fresh_instance_returns"] = d5b.book_stock_expense_enabled()
    p5["fresh_instance_sees_new_value"] = str(p5["fresh_instance_returns"]) == str(p5["db_value_now"])
    # the only way to clear L1 is to drop the attribute (or drop the instance)
    delattr(d, ATTR)
    p5["warm_instance_after_delattr"] = d.book_stock_expense_enabled()
    p5["delattr_clears_L1"] = str(p5["warm_instance_after_delattr"]) == str(p5["db_value_now"])
    rec("phase5_what_invalidates_each_layer", p5)

    # ------------------------------------------------------------------ phase 6
    # Does the attribute survive the REDIS document cache? If get_cached_doc hands back a
    # payload carrying _book_stock_expense_enabled, the staleness outlives the request.
    p6 = {}
    if saved_name:
        try:
            from frappe.model.document import get_document_cache_key

            ckey = get_document_cache_key("Purchase Receipt", saved_name)
            p6["cache_key"] = ckey

            frappe.clear_document_cache("Purchase Receipt", saved_name)
            warm = frappe.get_cached_doc("Purchase Receipt", saved_name)
            p6["attr_on_first_get_cached_doc"] = hasattr(warm, ATTR)
            warm.book_stock_expense_enabled()  # warm the L1 cache on the cached instance
            p6["attr_after_warming"] = hasattr(warm, ATTR)
            p6["warm_value"] = getattr(warm, ATTR, None)

            again = frappe.get_cached_doc("Purchase Receipt", saved_name)
            p6["second_get_cached_doc_is_same_object"] = id(again) == id(warm)
            p6["attr_present_on_second_get_cached_doc"] = hasattr(again, ATTR)

            # The same-object result above only proves in-process object identity via
            # redis_wrapper.py:91-92's frappe.local.cache shortcut -- it never exercises
            # the pickle round trip. A DIFFERENT request/process gets the doc via
            # pickle.loads (redis_wrapper.py:102). Simulate that by dropping ONLY the
            # process-local cache entry, leaving the redis payload in place.
            # NOTE: the doc was put in the cache BEFORE the attribute was set, so what
            # matters is whether the attribute is part of the serialized payload at all.
            # frappe.local.cache is keyed by make_key(key) -- db-name prefixed and encoded
            # (redis_wrapper.py:55-62, :74, :90-92) -- NOT by the raw cache key. Popping
            # the raw key evicts nothing, which would make this phase silently prove
            # nothing at all.
            lkey = frappe.cache.make_key(ckey)
            p6["local_cache_key"] = str(lkey)
            p6["raw_key_was_in_local_cache"] = ckey in frappe.local.cache
            p6["made_key_was_in_local_cache"] = lkey in frappe.local.cache
            frappe.local.cache.pop(lkey, None)
            frappe.local.cache.pop(ckey, None)
            p6["local_cache_entry_dropped"] = lkey not in frappe.local.cache
            p6["redis_payload_still_present"] = frappe.cache.get(lkey) is not None
            from_redis = frappe.get_cached_doc("Purchase Receipt", saved_name)
            p6["deserialized_is_distinct_object"] = id(from_redis) != id(warm)
            p6["attr_present_after_deserialize"] = hasattr(from_redis, ATTR)
            p6["attr_value_after_deserialize"] = getattr(from_redis, ATTR, "ABSENT")

            # and now the decisive form: warm the attribute, re-cache the doc explicitly,
            # drop the local entry, and see whether the stale value comes back from redis.
            from frappe.model.document import _set_document_in_cache

            fresh2 = frappe.get_doc("Purchase Receipt", saved_name)
            fresh2.book_stock_expense_enabled()
            p6["explicit_recache_attr_value"] = getattr(fresh2, ATTR, None)
            _set_document_in_cache(ckey, fresh2)
            frappe.local.cache.pop(frappe.cache.make_key(ckey), None)
            frappe.local.cache.pop(ckey, None)
            p6["revive_local_entry_dropped"] = frappe.cache.make_key(ckey) not in frappe.local.cache
            p6["revive_redis_payload_present"] = frappe.cache.get(frappe.cache.make_key(ckey)) is not None
            revived = frappe.get_cached_doc("Purchase Receipt", saved_name)
            p6["revived_is_distinct_object"] = id(revived) != id(fresh2)
            p6["L3_stale_attr_survives_serialized_cache"] = hasattr(revived, ATTR)
            p6["L3_revived_attr_value"] = getattr(revived, ATTR, "ABSENT")
        except Exception as e:
            p6["error"] = type(e).__name__ + ": " + str(e)
            p6["traceback"] = traceback.format_exc()
    else:
        p6["skipped"] = "no saved Purchase Receipt"
    rec("phase6_L3_redis_document_cache", p6)

    # ------------------------------------------------------------------ phase 7
    # Is the attribute ever reset during a document's own save lifecycle? If a reload
    # rebuilds the instance state, the stale value would be dropped -- check explicitly.
    p7 = {}
    if saved_name:
        d7 = frappe.get_doc("Purchase Receipt", saved_name)
        d7.book_stock_expense_enabled()
        p7["attr_before_reload"] = getattr(d7, ATTR, None)
        d7.reload()
        p7["attr_after_reload"] = getattr(d7, ATTR, "ABSENT")
        p7["reload_clears_the_cache"] = not hasattr(d7, ATTR)
        p7["attr_in_as_dict"] = ATTR in (d7.as_dict() or {})
        p7["attr_in_get_valid_dict"] = ATTR in (d7.get_valid_dict() or {})
    rec("phase7_reload_and_serialisation", p7)

    rec("ok", True)
except Exception:
    result["fatal"] = traceback.format_exc()
    print(result["fatal"])
finally:
    try:
        frappe.db.rollback()
        rec("rolled_back", True)
    except Exception:
        result["rollback_error"] = traceback.format_exc()

    # Phase 6 deliberately put a Purchase Receipt doc into the REDIS document cache, and
    # redis is NOT transactional -- frappe.db.rollback() does not undo it. That payload
    # may carry a _book_stock_expense_enabled derived from the (now rolled back) flipped
    # setting, so it must be evicted explicitly or it would outlive this probe.
    try:
        pr_names = frappe.get_all("Purchase Receipt", pluck="name")
        for n in pr_names:
            frappe.clear_document_cache("Purchase Receipt", n)
        rec("phaseZ_purchase_receipt_doc_caches_evicted", pr_names)
        left = {}
        for n in pr_names:
            from frappe.model.document import get_document_cache_key

            k = get_document_cache_key("Purchase Receipt", n)
            left[n] = {
                "in_local_cache": k in getattr(frappe.local, "cache", {}),
                "in_redis": frappe.cache.get_value(k) is not None,
            }
        rec("phaseZ_purchase_receipt_cache_state_after_evict", left)
        rec(
            "phaseZ_no_stale_pr_cache_left",
            all(not v["in_local_cache"] and not v["in_redis"] for v in left.values()),
        )
    except Exception:
        result["pr_cache_cleanup_error"] = traceback.format_exc()

    try:
        frappe.clear_document_cache("Accounts Settings", "Accounts Settings")
        after = frappe.db.get_single_value("Accounts Settings", SETTING, cache=False)
        rec("phaseZ_setting_after_rollback", after)
        rec("phaseZ_setting_restored", str(after) == str(ORIGINAL))
        rec(
            "phaseZ_singles_row_after",
            frappe.db.sql(
                "select value from tabSingles where doctype='Accounts Settings' and field=%s",
                SETTING,
                as_dict=True,
            ),
        )
        rec(
            "phaseZ_counts",
            {
                dt: frappe.db.count(dt)
                for dt in (
                    "GL Entry",
                    "Stock Ledger Entry",
                    "Account",
                    "Company",
                    "Financial Report Template",
                    "Fiscal Year",
                    "Property Setter",
                    "Purchase Receipt",
                    "Repost Item Valuation",
                    "Version",
                )
            },
        )
        rec("phaseZ_fiscal_years", frappe.get_all("Fiscal Year", pluck="name"))
    except Exception:
        result["restoration_check_error"] = traceback.format_exc()

    # tabError Log is MyISAM -> rollback does NOT undo it.
    # POSITIVELY SCOPED cleanup: only rows carrying this probe's marker.
    try:
        mine = frappe.db.sql(
            "select name from `tabError Log` where error like %s or error like %s",
            ("%" + MARKER + "%", "%V32-c-stockexpense-cache%"),
            as_dict=True,
        )
        rec("error_log_rows_matching_my_marker", mine)
        for row in mine:
            frappe.db.sql("delete from `tabError Log` where name=%s", row["name"])
        rec("error_log_rows_i_deleted", [r["name"] for r in mine])
        final_el = frappe.db.count("Error Log")
        rec("error_log_final", final_el)
        rec("error_log_back_to_baseline", final_el == el_baseline)
        if final_el != el_baseline:
            rec(
                "error_log_UNEXPLAINED_rows",
                frappe.db.sql(
                    "select name, method, left(error,300) as err from `tabError Log` "
                    "order by creation desc limit 10",
                    as_dict=True,
                ),
            )
            rec("error_log_note", "left in place deliberately: NOT provably mine, never delete by exclusion")
    except Exception:
        result["error_log_cleanup_error"] = traceback.format_exc()

    os.makedirs(OUTDIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1, default=str)
    print("WROTE " + OUT)
    frappe.destroy()
