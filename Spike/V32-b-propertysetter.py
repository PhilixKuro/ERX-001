# V-32 (b): Can a DIRECTLY-INSERTED Property Setter bypass ALLOWED_OPTIONS_CHANGE
#           and actually extend a Select field's options?
#
# G3 (Spike/S4-G3-整段让位开关.md:106) concluded 不可行, and at :155 listed this as the
# one open question that "directly决定s whether that 不可行 verdict can be overturned".
# Its reasoning: customize_form.py:852 ALLOWED_OPTIONS_CHANGE = ("Read Only","HTML","Data")
# does not include Select, and :394 msgprints a refusal. It noted property_setter.py does
# not consult that constant, but flagged PropertySetter.on_update ->
# validate_fields_for_doctype as a possible second gate it had NOT checked.
#
# This probe settles it by RUNNING it. "The insert did not raise" is NOT the criterion --
# a Property Setter row can exist and still change nothing. Three independent criteria,
# each of which must hold for the answer to be "yes":
#   C1  meta honours it  : get_meta(...).get_field("charge_type").options contains the
#                          new value, both cached and uncached
#   C2  save honours it  : an ORDINARY ORM insert carrying the new charge_type value
#                          -- the exact insert that probe (a) proved is rejected --
#                          now succeeds, and the value reads back verbatim
#   C3  downstream works : calculate_taxes_and_totals computes on the new charge_type
# Plus a negative control: the same insert is re-attempted AFTER rollback and must be
# rejected again, proving C2's success was caused by the Property Setter and nothing else.
#
# SITE SAFETY -- Property Setter writes mutate DocType meta and are cached, so this is
# the most dangerous of the three probes. Precautions taken:
#   - Grepped the full insert path for frappe.db.commit() / frappe.enqueue:
#       property_setter.py                      -> NEITHER (170 lines, read in full)
#       -> validate: frappe.clear_cache(doctype=) -> cache_manager.clear_cache /
#          clear_doctype_cache / clear_document_cache -> NEITHER
#       -> on_update: doctype.validate_fields_for_doctype (doctype.py:1280) ->
#          validate_links_table_fieldnames + validate_fields (:1287-1815) -> NEITHER.
#          The two hits in doctype.py are frappe.enqueue at :614 (inside the DocType doc
#          method sync_global_search) and frappe.db.commit() at :687 (inside
#          DocType.after_rename) -- neither is on this path.
#       -> wildcard doc_events on_update (hooks.py:173-182): the members that DO contain
#          enqueue/commit are guarded and provably early-return ON THIS SITE, confirmed
#          empirically by V32-seg0-recon (0 Workflow, 0 Assignment Rule, sqlite_search
#          reports 0 search classes). customize_form.py:263's enqueue is inside
#          save_customization, which this probe deliberately never calls.
#   - tabProperty Setter and tabVersion are both InnoDB (V32-seg0-recon), so rollback
#     genuinely removes the row.
#   - AFTER rollback the probe clears the meta cache AND re-verifies, uncached, that
#     charge_type's options are byte-identical to the pre-probe value, and that the
#     custom value is rejected on save again. Both before/after values are reported.
#   - tabError Log is MyISAM: rollback does NOT undo it. Cleanup is POSITIVELY SCOPED --
#     only rows matching this probe's own marker are deleted, never by exclusion.
#   - No frappe.db.commit() anywhere in this file.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -e PYTHONUTF8=1 -e PYTHONIOENCODING=utf-8 \
#     -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V32-b-propertysetter.py

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
OUTDIR = "/workspace/Spike/V32-out"
OUT = os.path.join(OUTDIR, "b-propertysetter.json")

MARKER = "V32PROBEB"
CUSTOM = "On Gross Value"
TARGET_DT = "Sales Taxes and Charges"
COMPANY = "华东弹簧"

result = {"probe": "V-32 (b) can a direct Property Setter extend Select options?"}


def rec(k, v):
    result[k] = v
    print("{0} = {1}".format(k, json.dumps(v, ensure_ascii=False, default=str)))


def flat(rows):
    return [list(r) for r in (rows or [])]


def options_uncached():
    return frappe.get_meta(TARGET_DT, cached=False).get_field("charge_type").options


def options_cached():
    return frappe.get_meta(TARGET_DT).get_field("charge_type").options


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

el_baseline = frappe.db.count("Error Log")
ps_baseline = frappe.db.count("Property Setter")
rec("error_log_baseline", el_baseline)
rec("property_setter_baseline", ps_baseline)

ORIGINAL_OPTIONS = None

try:
    from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals
    from frappe.custom.doctype.customize_form.customize_form import ALLOWED_OPTIONS_CHANGE

    tax_account = frappe.db.get_value(
        "Account", {"company": COMPANY, "is_group": 0, "account_type": "Tax"}, "name"
    ) or frappe.db.get_value("Account", {"company": COMPANY, "is_group": 0, "root_type": "Liability"}, "name")
    cost_center = frappe.db.get_value("Cost Center", {"company": COMPANY, "is_group": 0}, "name")

    # ----------------------------------------------------- phase -1 SAFETY GATE
    # Phase 6 inserts a Sales Order, so erpnext's own wildcard `validate` hooks
    # (erpnext/hooks.py:348-353) run. Neither contains commit/enqueue itself, but
    # prove their early returns hold ON THIS SITE rather than trusting the read.
    gate = {}
    try:
        from erpnext.support.doctype.service_level_agreement.service_level_agreement import (
            get_documents_with_active_service_level_agreement,
        )

        sla_doctypes = get_documents_with_active_service_level_agreement() or []
        gate["sla_doctypes_with_active_agreement"] = list(sla_doctypes)
        gate["GATE_sla_hook_returns_early_for_Sales_Order"] = "Sales Order" not in sla_doctypes
        gate["GATE_sla_hook_returns_early_for_template"] = (
            "Sales Taxes and Charges Template" not in sla_doctypes
        )
    except Exception as e:
        gate["sla_probe_error"] = repr(e)
    try:
        for dt in ("Sales Order", "Sales Taxes and Charges Template", "Property Setter"):
            gate["deletion_running_" + dt.replace(" ", "_")] = frappe.cache.get_value(
                "deletion_running_doctype:" + dt
            )
    except Exception as e:
        gate["deletion_cache_probe_error"] = repr(e)
    gate["accounting_periods"] = frappe.db.count("Accounting Period")
    rec("phaseNeg1_safety_gate", gate)

    # ------------------------------------------------------------- phase 0
    # BEFORE snapshot, mandated by the site-safety rules.
    frappe.clear_cache(doctype=TARGET_DT)
    ORIGINAL_OPTIONS = options_uncached()
    rec("phase0_BEFORE_options_uncached", ORIGINAL_OPTIONS)
    rec("phase0_BEFORE_options_cached", options_cached())
    rec("phase0_BEFORE_options_split", (ORIGINAL_OPTIONS or "").split("\n"))
    rec("phase0_ALLOWED_OPTIONS_CHANGE", list(ALLOWED_OPTIONS_CHANGE))
    rec("phase0_Select_in_ALLOWED_OPTIONS_CHANGE", "Select" in ALLOWED_OPTIONS_CHANGE)
    rec(
        "phase0_existing_options_property_setters_sitewide",
        frappe.db.count("Property Setter", {"property": "options"}),
    )

    def try_save_custom_charge_type(tag):
        """The exact operation probe (a) proved is rejected at baseline.
        Returns a dict distinguishing raised / inserted / value-read-back."""
        out = {}
        name = None
        try:
            d = frappe.get_doc(
                {
                    "doctype": "Sales Taxes and Charges Template",
                    "title": MARKER + "-" + tag,
                    "company": COMPANY,
                    "is_default": 0,
                    "taxes": [
                        {
                            "doctype": TARGET_DT,
                            "charge_type": CUSTOM,
                            "account_head": tax_account,
                            "description": MARKER + " " + tag,
                            "rate": 10,
                            "cost_center": cost_center,
                        }
                    ],
                }
            )
            d.insert(ignore_permissions=True)
            name = d.name
            out["raised"] = False
            out["inserted_name"] = name
        except Exception as e:
            out["raised"] = True
            out["exc_class"] = type(e).__name__
            out["exc_msg"] = str(e)
        # positive confirmation, not just "no error"
        out["child_rows_in_db"] = flat(
            frappe.db.sql(
                "select charge_type from `tab" + TARGET_DT + "` where description=%s",
                MARKER + " " + tag,
            )
        )
        out["persisted_verbatim"] = out["child_rows_in_db"] == [[CUSTOM]]
        if name:
            frappe.clear_document_cache("Sales Taxes and Charges Template", name)
            out["orm_reads_back"] = frappe.get_doc(
                "Sales Taxes and Charges Template", name
            ).taxes[0].charge_type
        return out

    # ------------------------------------------------------------- phase 1
    # Confirm the baseline: without any Property Setter the save IS rejected.
    # Without this, phase 4's success would prove nothing.
    rec("phase1_baseline_save_is_rejected", try_save_custom_charge_type("PRE"))

    # ------------------------------------------------------------- phase 2
    # Confirm G3's cited guard is real: the Customize Form route refuses.
    # Calls allow_property_change (customize_form.py:329) directly -- the function that
    # owns the :394 check -- rather than save_customization, which carries an enqueue
    # (:263) and a possible frappe.db.updatedb.
    phase2 = {}
    try:
        cf = frappe.get_doc("Customize Form")
        cf.doc_type = TARGET_DT
        meta = frappe.get_meta(TARGET_DT)
        meta_df = [d for d in meta.fields if d.fieldname == "charge_type"]
        proposed = frappe._dict(
            {
                "fieldname": "charge_type",
                "fieldtype": "Select",
                "label": "Type",
                "options": (ORIGINAL_OPTIONS or "") + "\n" + CUSTOM,
            }
        )
        allowed = cf.allow_property_change("options", meta_df, proposed, meta)
        phase2["allow_property_change_returned"] = allowed
        phase2["customize_form_route_permits_options_change"] = bool(allowed)
        phase2["messages"] = [str(m) for m in (frappe.local.message_log or [])]
        frappe.clear_messages()
    except Exception as e:
        phase2["raised"] = True
        phase2["exc"] = type(e).__name__ + ": " + str(e)
    rec("phase2_customize_form_guard", phase2)

    # ------------------------------------------------------------- phase 3
    # THE ACTUAL TEST: insert a Property Setter directly, bypassing Customize Form.
    phase3 = {}
    ps_name = None
    NEW_OPTIONS = (ORIGINAL_OPTIONS or "") + "\n" + CUSTOM
    try:
        ps = frappe.get_doc(
            {
                "doctype": "Property Setter",
                "doctype_or_field": "DocField",
                "doc_type": TARGET_DT,
                "field_name": "charge_type",
                "property": "options",
                "property_type": "Text",
                "value": NEW_OPTIONS,
                "module": "Accounts",
            }
        )
        ps.flags.ignore_permissions = True
        ps.insert()
        ps_name = ps.name
        phase3["raised"] = False
        phase3["ps_name"] = ps_name
    except Exception as e:
        phase3["raised"] = True
        phase3["exc_class"] = type(e).__name__
        phase3["exc_msg"] = str(e)
    phase3["row_exists_in_db"] = flat(
        frappe.db.sql(
            "select name, property, property_type, value from `tabProperty Setter` "
            "where doc_type=%s and field_name='charge_type' and property='options'",
            TARGET_DT,
        )
    )
    phase3["property_setter_count_now"] = frappe.db.count("Property Setter")
    rec("phase3_direct_property_setter_insert", phase3)

    # ------------------------------------------------------------- phase 4 (C1)
    # Does META honour it? Uncached AND cached, because production request paths
    # read the cached meta.
    phase4 = {}
    phase4["options_uncached_after"] = options_uncached()
    phase4["options_cached_after"] = options_cached()
    phase4["C1_uncached_meta_contains_custom"] = CUSTOM in (phase4["options_uncached_after"] or "")
    phase4["C1_cached_meta_contains_custom"] = CUSTOM in (phase4["options_cached_after"] or "")
    phase4["options_changed_from_original"] = phase4["options_uncached_after"] != ORIGINAL_OPTIONS
    # is the option list otherwise intact (no standard option lost)?
    phase4["standard_options_still_present"] = all(
        o in (phase4["options_uncached_after"] or "").split("\n")
        for o in (ORIGINAL_OPTIONS or "").split("\n")
    )
    rec("phase4_C1_meta_honours_new_option", phase4)

    # ------------------------------------------------------------- phase 5 (C2)
    # Does an ACTUAL SAVE honour it? This is the criterion that matters: the same
    # operation phase 1 proved is rejected.
    rec("phase5_C2_save_with_property_setter_active", try_save_custom_charge_type("POST"))

    # also: the validator that did the rejecting, called directly
    phase5b = {}
    child = frappe.new_doc(TARGET_DT)
    child.charge_type = CUSTOM
    child.account_head = tax_account
    child.description = MARKER + " direct"
    try:
        child._validate_selects()
        phase5b["raised"] = False
        phase5b["charge_type_after"] = child.charge_type
    except Exception as e:
        phase5b["raised"] = True
        phase5b["exc_class"] = type(e).__name__
        phase5b["exc_msg"] = str(e)
    rec("phase5b_validate_selects_with_property_setter_active", phase5b)

    # ------------------------------------------------------------- phase 6 (C3)
    # Does the downstream calculator work on a STORED custom charge_type?
    phase6 = {}
    item_code = frappe.db.get_value("Item", {"disabled": 0}, "name")
    customer = frappe.db.get_value("Customer", {}, "name")
    phase6["item_code"] = item_code
    phase6["customer"] = customer
    if item_code and customer:
        import erpnext.controllers.taxes_and_totals as tnt_mod
        from frappe.utils import flt as _flt

        calls = {"n": 0}

        def resolve_on_gross(calc, item, tax):
            calls["n"] += 1
            return _flt(item.amount) * 3

        tnt_mod.v32b_resolver = resolve_on_gross
        RESOLVER_PATH = "erpnext.controllers.taxes_and_totals.v32b_resolver"
        real_get_hooks = frappe.get_hooks

        def fake_get_hooks(hook=None, *args, **kwargs):
            if hook == "erpnext_taxable_base_resolvers":
                return {CUSTOM: [RESOLVER_PATH]}
            return real_get_hooks(hook, *args, **kwargs)

        so = frappe.new_doc("Sales Order")
        so.company = COMPANY
        so.customer = customer
        so.currency = "CNY"
        so.conversion_rate = 1
        so.transaction_date = frappe.utils.nowdate()
        so.delivery_date = frappe.utils.nowdate()
        warehouse = frappe.db.get_value(
            "Warehouse", {"company": COMPANY, "is_group": 0, "warehouse_name": "成品"}, "name"
        ) or frappe.db.get_value("Warehouse", {"company": COMPANY, "is_group": 0}, "name")
        phase6["warehouse"] = warehouse
        so.append(
            "items",
            {
                "item_code": item_code,
                "qty": 1,
                "rate": 1000,
                "price_list_rate": 1000,
                "warehouse": warehouse,
                "delivery_date": frappe.utils.nowdate(),
            },
        )
        so.append(
            "taxes",
            {
                "charge_type": CUSTOM,
                "account_head": tax_account,
                "description": MARKER + " downstream",
                "rate": 10,
                "cost_center": cost_center,
            },
        )
        try:
            frappe.get_hooks = fake_get_hooks
            calculate_taxes_and_totals(so)
            phase6["calc_raised"] = False
            phase6["net_total"] = so.net_total
            phase6["tax_amount"] = so.taxes[0].tax_amount
            phase6["grand_total"] = so.grand_total
            phase6["resolver_call_count"] = calls["n"]
            # resolver base 3x1000=3000 @10% -> 300; fallback (net_amount) would give 100
            phase6["C3_resolver_honoured"] = float(so.taxes[0].tax_amount) == 300.0
        except Exception as e:
            phase6["calc_raised"] = True
            phase6["calc_exc"] = type(e).__name__ + ": " + str(e)
        # and does the WHOLE Sales Order now validate+insert with the custom charge_type?
        try:
            frappe.get_hooks = fake_get_hooks
            so.flags.ignore_permissions = True
            so.insert()
            phase6["so_insert_raised"] = False
            phase6["so_name"] = so.name
            phase6["so_charge_type_in_db"] = flat(
                frappe.db.sql(
                    "select charge_type, tax_amount from `tab" + TARGET_DT + "` where parent=%s",
                    so.name,
                )
            )
        except Exception as e:
            phase6["so_insert_raised"] = True
            phase6["so_insert_exc"] = type(e).__name__ + ": " + str(e)
        finally:
            frappe.get_hooks = real_get_hooks
    else:
        phase6["skipped"] = "no Item or Customer on site"
    rec("phase6_C3_downstream_with_stored_custom_type", phase6)

    # ------------------------------------------------------------- phase 7
    # Was this a real bypass, or does `options` need the Customize-Form-blessed shape?
    # Try the same thing via frappe.make_property_setter (the documented helper), which
    # ALSO does not consult ALLOWED_OPTIONS_CHANGE -- confirms the bypass is not an
    # artifact of how this probe built the doc.
    phase7 = {}
    try:
        if ps_name:
            frappe.db.delete("Property Setter", {"name": ps_name})
        frappe.clear_cache(doctype=TARGET_DT)
        phase7["options_after_deleting_first_ps"] = options_uncached()
        phase7["custom_gone_after_delete"] = CUSTOM not in (
            phase7["options_after_deleting_first_ps"] or ""
        )
        # NOTE: frappe.make_property_setter (frappe/__init__.py:1193-1245) has NO return
        # statement, so it always yields None -- do not read .name off it.
        frappe.make_property_setter(
            {
                "doctype": TARGET_DT,
                "doctype_or_field": "DocField",
                "fieldname": "charge_type",
                "property": "options",
                "value": NEW_OPTIONS,
                "property_type": "Text",
            },
            is_system_generated=False,
        )
        phase7["raised"] = False
        phase7["rows_in_db"] = flat(
            frappe.db.sql(
                "select name, value from `tabProperty Setter` "
                "where doc_type=%s and field_name='charge_type' and property='options'",
                TARGET_DT,
            )
        )
        phase7["options_after"] = options_uncached()
        phase7["helper_route_also_works"] = CUSTOM in (phase7["options_after"] or "")
        # and the save must succeed through this route too
        phase7["save_via_helper_route"] = try_save_custom_charge_type("HELPER")
    except Exception as e:
        phase7["raised"] = True
        phase7["exc"] = type(e).__name__ + ": " + str(e)
    rec("phase7_make_property_setter_helper_route", phase7)

    rec("ok", True)
except Exception:
    result["fatal"] = traceback.format_exc()
    print(result["fatal"])
finally:
    # ---------------- ROLLBACK + META RESTORATION (site-safety rule 4) ----------------
    try:
        frappe.db.rollback()
        rec("rolled_back", True)
    except Exception:
        result["rollback_error"] = traceback.format_exc()

    try:
        # a rollback alone is not enough: DocType meta is CACHED. Clear it explicitly.
        frappe.clear_cache(doctype=TARGET_DT)
        try:
            from frappe.model.meta import clear_meta_cache

            clear_meta_cache(TARGET_DT)
        except Exception:
            pass
        frappe.local.meta_cache = {}

        after_uncached = options_uncached()
        after_cached = options_cached()
        rec("phaseZ_AFTER_options_uncached", after_uncached)
        rec("phaseZ_AFTER_options_cached", after_cached)
        rec("phaseZ_options_restored_byte_identical", after_uncached == ORIGINAL_OPTIONS)
        rec("phaseZ_cached_options_restored", after_cached == ORIGINAL_OPTIONS)
        rec("phaseZ_custom_value_gone_from_meta", CUSTOM not in (after_uncached or ""))
        rec(
            "phaseZ_property_setters_on_charge_type_remaining",
            flat(
                frappe.db.sql(
                    "select name, property, value from `tabProperty Setter` "
                    "where doc_type=%s and field_name='charge_type'",
                    TARGET_DT,
                )
            ),
        )
        rec(
            "phaseZ_counts",
            {
                dt: frappe.db.count(dt)
                for dt in (
                    "Property Setter",
                    "Sales Taxes and Charges Template",
                    "Sales Taxes and Charges",
                    "Sales Order",
                    "GL Entry",
                    "Stock Ledger Entry",
                    "Account",
                    "Company",
                    "Financial Report Template",
                    "Fiscal Year",
                    "Version",
                )
            },
        )
        rec("phaseZ_property_setter_back_to_baseline", frappe.db.count("Property Setter") == ps_baseline)
        rec("phaseZ_fiscal_years", frappe.get_all("Fiscal Year", pluck="name"))
        rec(
            "phaseZ_probe_rows_left_behind",
            flat(
                frappe.db.sql(
                    "select name from `tabSales Taxes and Charges Template` where title like %s",
                    MARKER + "%",
                )
            )
            + flat(
                frappe.db.sql(
                    "select name from `tab" + TARGET_DT + "` where description like %s", MARKER + "%"
                )
            ),
        )

        # NEGATIVE CONTROL: with the Property Setter gone, the save must be rejected again.
        # This proves phase 5's success was caused by the Property Setter, not by anything
        # else this probe happened to do.
        neg = try_save_custom_charge_type("NEG")
        rec("phaseZ_negative_control_save_rejected_again", neg)
        frappe.db.rollback()
        rec("phaseZ_rolled_back_negative_control", True)
    except Exception:
        result["restoration_check_error"] = traceback.format_exc()

    # tabError Log is MyISAM -> rollback does NOT undo it.
    # POSITIVELY SCOPED cleanup: only rows carrying this probe's marker.
    try:
        mine = frappe.db.sql(
            "select name from `tabError Log` where error like %s or error like %s",
            ("%" + MARKER + "%", "%V32-b-propertysetter%"),
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
