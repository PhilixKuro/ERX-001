# V-32 (a): Is a custom `charge_type` actually blocked on save?
#
# G3 (Spike/S4-G3-整段让位开关.md:106) self-declared this as the item MOST likely to be
# misjudged -- "the one most analogous to the Bank Transaction Mapping mistake".
# Its assertion: `charge_type` is a Select with 5 options; base_document.py:1119
# frappe.throw()s on any value outside them, so a custom charge_type "cannot be stored",
# and erpnext's own 4 tests never prove otherwise because they all use do_not_save=True.
#
# G3 read the code. This probe RUNS it. Four distinct outcomes must be distinguished
# (the project rule: "no error was raised" does NOT mean "it worked"):
#   (1) blocked by validation      -> insert raises, row absent
#   (2) silently accepted          -> insert succeeds, value reads back verbatim
#   (3) silently coerced           -> insert succeeds, value reads back CHANGED
#   (4) accepted-but-broken        -> value persists, but a downstream consumer ignores it
# So every phase reads the value BACK and, separately, asks a downstream consumer.
#
# Paths tested separately because they can differ:
#   A. ORM insert (frappe.get_doc(...).insert())
#   B. ORM insert under frappe.flags.in_import (base_document.py:1102-1103 early return)
#   C. direct raw-SQL UPDATE (bypasses the document layer entirely)
#   D. re-save through the ORM of a doc whose value was planted by C
#   E. downstream: calculate_taxes_and_totals + the erpnext_taxable_base_resolvers hook
#   F. erpnext's own validate_taxes_and_charges (accounts_controller.py:3298)
#
# SITE SAFETY
#   - Vehicle is `Sales Taxes and Charges Template`, whose child table IS the DocType
#     `Sales Taxes and Charges` that owns the charge_type field, so _validate_selects
#     runs on exactly the field under test (document.py:843 loops get_all_children()).
#   - Grepped the whole save path for frappe.db.commit() / frappe.enqueue:
#       sales_taxes_and_charges_template.py  -> neither (file is 99 lines, read in full)
#       sales_taxes_and_charges.py           -> neither (50 lines, `pass` body)
#       accounts_controller.validate_taxes_and_charges / validate_account_head /
#         validate_cost_center / validate_inclusive_tax -> neither (read in full)
#       frappe wildcard doc_events on_update (hooks.py:173-182): the ones that DO contain
#         enqueue/commit are guarded and provably return early ON THIS SITE, confirmed
#         empirically by V32-seg0-recon: 0 Workflow, 0 Assignment Rule, sqlite_search
#         has 0 search classes. notify_mentions' enqueue is not on this path.
#   - Every probe table is InnoDB (seg0: tabSales Taxes and Charges Template /
#     tabSales Taxes and Charges / tabVersion / tabSingles), so rollback is real.
#   - tabError Log is MyISAM: rollback does NOT undo it. Cleanup is POSITIVELY SCOPED --
#     only rows whose content carries this probe's own marker are deleted, never
#     "rows not in my baseline".
#   - No frappe.db.commit() anywhere in this file.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -e PYTHONUTF8=1 -e PYTHONIOENCODING=utf-8 \
#     -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V32-a-chargetype.py

import json
import os
import traceback

import frappe

SITE = "erx.localhost"
OUTDIR = "/workspace/Spike/V32-out"
OUT = os.path.join(OUTDIR, "a-chargetype.json")

MARKER = "V32PROBEA"
CUSTOM = "On Gross Value"  # deliberately outside the 5 standard options
COMPANY = "华东弹簧"

result = {"probe": "V-32 (a) can a custom charge_type be saved?"}


def rec(k, v):
    result[k] = v
    print("{0} = {1}".format(k, json.dumps(v, ensure_ascii=False, default=str)))


def flat(rows):
    """frappe's DB driver returns list-of-lists, not list-of-tuples; normalise so the
    'persisted verbatim' criterion actually compares what it claims to compare."""
    return [list(r) for r in (rows or [])]


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

el_baseline = frappe.db.count("Error Log")
rec("error_log_baseline", el_baseline)

try:
    from erpnext.controllers.taxes_and_totals import calculate_taxes_and_totals

    # ---------------------------------------------------------------- phase 0
    # the field as the site actually sees it
    df = frappe.get_meta("Sales Taxes and Charges").get_field("charge_type")
    std_options = (df.options or "").split("\n")
    rec("phase0_meta", {"fieldtype": df.fieldtype, "options": std_options, "reqd": df.reqd})
    rec("phase0_custom_value_is_outside_options", CUSTOM not in std_options)

    tax_account = frappe.db.get_value(
        "Account", {"company": COMPANY, "is_group": 0, "account_type": "Tax"}, "name"
    ) or frappe.db.get_value("Account", {"company": COMPANY, "is_group": 0, "root_type": "Liability"}, "name")
    cost_center = frappe.db.get_value("Cost Center", {"company": COMPANY, "is_group": 0}, "name")
    rec("phase0_tax_account", tax_account)
    rec("phase0_cost_center", cost_center)

    def build_template(title, charge_type):
        return frappe.get_doc(
            {
                "doctype": "Sales Taxes and Charges Template",
                "title": title,
                "company": COMPANY,
                "is_default": 0,
                "taxes": [
                    {
                        "doctype": "Sales Taxes and Charges",
                        "charge_type": charge_type,
                        "account_head": tax_account,
                        "description": MARKER + " " + charge_type,
                        "rate": 10,
                        "cost_center": cost_center,
                    }
                ],
            }
        )

    # ---------------------------------------------------------------- phase A
    # ORM insert, ordinary path. G3 predicts a throw from _validate_selects.
    phase_a = {}
    doc_a_name = None
    try:
        d = build_template(MARKER + "-A", CUSTOM)
        d.insert(ignore_permissions=True)
        doc_a_name = d.name
        phase_a["raised"] = False
        phase_a["inserted_name"] = d.name
    except Exception as e:
        phase_a["raised"] = True
        phase_a["exc_class"] = type(e).__name__
        phase_a["exc_msg"] = str(e)
    # criterion must distinguish "blocked" from "silently accepted": read back
    phase_a["row_exists_in_db"] = bool(
        frappe.db.sql(
            "select name from `tabSales Taxes and Charges Template` where title=%s", MARKER + "-A"
        )
    )
    phase_a["child_rows_in_db"] = frappe.db.sql(
        "select charge_type from `tabSales Taxes and Charges` where description=%s",
        MARKER + " " + CUSTOM,
        as_dict=True,
    )
    phase_a["verdict"] = (
        "blocked by validation"
        if phase_a["raised"] and not phase_a["row_exists_in_db"]
        else "NOT blocked -- investigate"
    )
    rec("phaseA_orm_insert_custom_charge_type", phase_a)

    # control: same insert with a STANDARD charge_type must succeed, otherwise
    # phase A proved nothing (it could have failed for an unrelated reason).
    phase_a_ctl = {}
    ctl_name = None
    try:
        d = build_template(MARKER + "-CTL", "On Net Total")
        d.insert(ignore_permissions=True)
        ctl_name = d.name
        phase_a_ctl["raised"] = False
        phase_a_ctl["inserted_name"] = d.name
        phase_a_ctl["charge_type_read_back"] = frappe.db.sql(
            "select charge_type from `tabSales Taxes and Charges` where parent=%s", d.name
        )
    except Exception as e:
        phase_a_ctl["raised"] = True
        phase_a_ctl["exc_class"] = type(e).__name__
        phase_a_ctl["exc_msg"] = str(e)
    phase_a_ctl["control_is_valid"] = not phase_a_ctl["raised"]
    rec("phaseA_control_standard_charge_type", phase_a_ctl)

    # ---------------------------------------------------------------- phase B
    # base_document.py:1102-1103: `if frappe.flags.in_import: return` skips
    # _validate_selects entirely. Does the custom value then persist?
    phase_b = {}
    b_name = None
    try:
        frappe.flags.in_import = True
        d = build_template(MARKER + "-B", CUSTOM)
        d.insert(ignore_permissions=True)
        b_name = d.name
        phase_b["raised"] = False
        phase_b["inserted_name"] = d.name
    except Exception as e:
        phase_b["raised"] = True
        phase_b["exc_class"] = type(e).__name__
        phase_b["exc_msg"] = str(e)
    finally:
        frappe.flags.in_import = False
    if b_name:
        phase_b["charge_type_in_db"] = flat(
            frappe.db.sql(
                "select charge_type from `tabSales Taxes and Charges` where parent=%s", b_name
            )
        )
        phase_b["persisted_verbatim"] = phase_b["charge_type_in_db"] == [[CUSTOM]]
        # also confirm via the ORM, not only raw SQL
        frappe.clear_document_cache("Sales Taxes and Charges Template", b_name)
        phase_b["orm_reads_back"] = frappe.get_doc(
            "Sales Taxes and Charges Template", b_name
        ).taxes[0].charge_type
    rec("phaseB_orm_insert_under_in_import_flag", phase_b)

    # ---------------------------------------------------------------- phase C
    # direct raw-SQL UPDATE: bypasses the document layer completely.
    phase_c = {}
    if ctl_name:
        frappe.db.sql(
            "update `tabSales Taxes and Charges` set charge_type=%s where parent=%s",
            (CUSTOM, ctl_name),
        )
        phase_c["db_value_after_update"] = flat(
            frappe.db.sql(
                "select charge_type from `tabSales Taxes and Charges` where parent=%s", ctl_name
            )
        )
        phase_c["persisted_verbatim"] = phase_c["db_value_after_update"] == [[CUSTOM]]
        # does the ORM hand the custom value back, or coerce/blank it?
        frappe.clear_document_cache("Sales Taxes and Charges Template", ctl_name)
        reread = frappe.get_doc("Sales Taxes and Charges Template", ctl_name)
        phase_c["orm_reads_back"] = reread.taxes[0].charge_type
        phase_c["orm_matches_db"] = reread.taxes[0].charge_type == CUSTOM
    else:
        phase_c["skipped"] = "control insert failed, no row to update"
    rec("phaseC_direct_db_write", phase_c)

    # ---------------------------------------------------------------- phase D
    # a value planted by C: does the NEXT ordinary ORM save reject it?
    # This is what decides whether a DB-planted custom charge_type survives
    # normal use or blows up the first time anyone edits the record.
    phase_d = {}
    if ctl_name:
        try:
            frappe.clear_document_cache("Sales Taxes and Charges Template", ctl_name)
            d = frappe.get_doc("Sales Taxes and Charges Template", ctl_name)
            d.flags.ignore_permissions = True
            d.save()
            phase_d["raised"] = False
            phase_d["charge_type_after_resave"] = frappe.db.sql(
                "select charge_type from `tabSales Taxes and Charges` where parent=%s", ctl_name
            )
        except Exception as e:
            phase_d["raised"] = True
            phase_d["exc_class"] = type(e).__name__
            phase_d["exc_msg"] = str(e)
            phase_d["charge_type_still_in_db"] = frappe.db.sql(
                "select charge_type from `tabSales Taxes and Charges` where parent=%s", ctl_name
            )
    else:
        phase_d["skipped"] = "no control row"
    rec("phaseD_resave_db_planted_value", phase_d)

    # ---------------------------------------------------------------- phase E
    # downstream: does the CALCULATOR honour a custom charge_type?
    # In-memory only (no insert), mirroring how erpnext's own tests do it, so this
    # phase writes nothing. Distinguishes "accepted-but-broken downstream" from
    # "genuinely usable once stored".
    phase_e = {}
    item_code = frappe.db.get_value("Item", {"is_stock_item": 1, "disabled": 0}, "name") or frappe.db.get_value(
        "Item", {"disabled": 0}, "name"
    )
    phase_e["item_code"] = item_code
    if item_code:
        # The hook value is a dotted path resolved by frappe.get_attr, which REFUSES any
        # path whose first segment is not an installed app (frappe/__init__.py:1132-1133),
        # so "__main__.resolve_on_gross" cannot be used. Register a real attribute on an
        # installed-app module instead and point the hook at that.
        import erpnext.controllers.taxes_and_totals as tnt_mod
        from frappe.utils import flt as _flt

        # The resolver must return a base that the FALLBACK cannot produce, otherwise
        # "tax_amount == 100" would not distinguish "resolver honoured" from "fallback
        # ran" -- the fallback is flt(item.net_amount), which is also 1000 here.
        # Use 3x the line amount: resolver -> base 3000 -> tax 300; fallback -> tax 100.
        calls = {"n": 0}

        def resolve_on_gross(calc, item, tax):
            calls["n"] += 1
            return _flt(item.amount) * 3

        tnt_mod.v32_probe_resolve_on_gross = resolve_on_gross
        RESOLVER_PATH = "erpnext.controllers.taxes_and_totals.v32_probe_resolve_on_gross"
        phase_e["resolver_path"] = RESOLVER_PATH
        phase_e["resolver_path_loadable"] = (
            frappe.get_attr(RESOLVER_PATH) is resolve_on_gross
        )

        real_get_hooks = frappe.get_hooks

        def fake_get_hooks(hook=None, *args, **kwargs):
            if hook == "erpnext_taxable_base_resolvers":
                return {CUSTOM: [RESOLVER_PATH]}
            return real_get_hooks(hook, *args, **kwargs)

        so = frappe.new_doc("Sales Order")
        so.company = COMPANY
        so.customer = frappe.db.get_value("Customer", {}, "name")
        so.currency = "CNY"
        so.conversion_rate = 1
        so.transaction_date = frappe.utils.nowdate()
        so.delivery_date = frappe.utils.nowdate()
        so.append(
            "items",
            {
                "item_code": item_code,
                "qty": 1,
                "rate": 1000,
                "price_list_rate": 1000,
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
            phase_e["raised"] = False
            phase_e["net_total"] = so.net_total
            phase_e["tax_amount"] = so.taxes[0].tax_amount
            phase_e["grand_total"] = so.grand_total
            phase_e["resolver_call_count"] = calls["n"]
            # resolver base = 3 x 1000 = 3000, rate 10% -> 300.
            # fallback base = net_amount = 1000 -> 100. The two are distinguishable.
            phase_e["resolver_was_actually_invoked"] = calls["n"] > 0
            phase_e["calculator_honours_custom_type"] = float(so.taxes[0].tax_amount) == 300.0
            phase_e["tax_amount_if_fallback_had_run"] = 100.0
        except Exception as e:
            phase_e["raised"] = True
            phase_e["exc_class"] = type(e).__name__
            phase_e["exc_msg"] = str(e)
        finally:
            frappe.get_hooks = real_get_hooks

        # and WITHOUT the resolver: get_item_taxable_base falls back to item.net_amount
        so2 = frappe.new_doc("Sales Order")
        so2.company = COMPANY
        so2.customer = frappe.db.get_value("Customer", {}, "name")
        so2.currency = "CNY"
        so2.conversion_rate = 1
        so2.transaction_date = frappe.utils.nowdate()
        so2.delivery_date = frappe.utils.nowdate()
        so2.append(
            "items",
            {
                "item_code": item_code,
                "qty": 1,
                "rate": 1000,
                "price_list_rate": 1000,
                "delivery_date": frappe.utils.nowdate(),
            },
        )
        so2.append(
            "taxes",
            {
                "charge_type": CUSTOM,
                "account_head": tax_account,
                "description": MARKER + " downstream norsv",
                "rate": 10,
                "cost_center": cost_center,
            },
        )
        try:
            calculate_taxes_and_totals(so2)
            phase_e["no_resolver_raised"] = False
            phase_e["no_resolver_tax_amount"] = so2.taxes[0].tax_amount
        except Exception as e:
            phase_e["no_resolver_raised"] = True
            phase_e["no_resolver_exc"] = type(e).__name__ + ": " + str(e)
    else:
        phase_e["skipped"] = "no Item on site"
    rec("phaseE_downstream_calculator", phase_e)

    # ---------------------------------------------------------------- phase F
    # erpnext's own row validator: independent of frappe's Select check.
    phase_f = {}
    try:
        from erpnext.controllers.accounts_controller import validate_taxes_and_charges

        probe_tax = frappe._dict(
            {
                "doctype": "Sales Taxes and Charges",
                "charge_type": CUSTOM,
                "row_id": None,
                "idx": 1,
                "rate": 10,
            }
        )
        validate_taxes_and_charges(probe_tax)
        phase_f["raised"] = False
        phase_f["rate_after"] = probe_tax.rate
        phase_f["note"] = "erpnext row validator does not object to a custom charge_type"
    except Exception as e:
        phase_f["raised"] = True
        phase_f["exc_class"] = type(e).__name__
        phase_f["exc_msg"] = str(e)
    rec("phaseF_erpnext_validate_taxes_and_charges", phase_f)

    # ---------------------------------------------------------------- phase G
    # Which layer is the gate? Call _validate_selects directly on a child doc.
    phase_g = {}
    child = frappe.new_doc("Sales Taxes and Charges")
    child.charge_type = CUSTOM
    child.account_head = tax_account
    child.description = MARKER + " direct"
    try:
        child._validate_selects()
        phase_g["raised"] = False
        phase_g["charge_type_after"] = child.charge_type
    except Exception as e:
        phase_g["raised"] = True
        phase_g["exc_class"] = type(e).__name__
        phase_g["exc_msg"] = str(e)
    rec("phaseG_validate_selects_called_directly", phase_g)

    rec("ok", True)
except Exception:
    result["fatal"] = traceback.format_exc()
    print(result["fatal"])
finally:
    try:
        frappe.flags.in_import = False
        frappe.db.rollback()
        rec("rolled_back", True)
    except Exception:
        result["rollback_error"] = traceback.format_exc()

    # verify the rollback actually removed everything this probe inserted
    try:
        rec(
            "post_rollback_probe_templates",
            frappe.db.sql(
                "select name from `tabSales Taxes and Charges Template` where title like %s",
                MARKER + "%",
                as_dict=True,
            ),
        )
        rec(
            "post_rollback_probe_child_rows",
            frappe.db.sql(
                "select name, charge_type from `tabSales Taxes and Charges` where description like %s",
                MARKER + "%",
                as_dict=True,
            ),
        )
        rec(
            "post_rollback_counts",
            {
                dt: frappe.db.count(dt)
                for dt in (
                    "Sales Taxes and Charges Template",
                    "Sales Taxes and Charges",
                    "GL Entry",
                    "Property Setter",
                    "Version",
                )
            },
        )
        # the standard charge_type options must be untouched
        frappe.clear_cache(doctype="Sales Taxes and Charges")
        rec(
            "post_rollback_charge_type_options",
            frappe.get_meta("Sales Taxes and Charges").get_field("charge_type").options,
        )
    except Exception:
        result["post_rollback_check_error"] = traceback.format_exc()

    # tabError Log is MyISAM -> rollback does not undo it.
    # POSITIVELY SCOPED cleanup: delete ONLY rows carrying this probe's marker.
    try:
        mine = frappe.db.sql(
            "select name from `tabError Log` where error like %s or error like %s",
            ("%" + MARKER + "%", "%V32-a-chargetype%"),
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
                    "select name, method, left(error,300) as err from `tabError Log` order by creation desc limit 10",
                    as_dict=True,
                ),
            )
            rec("error_log_note", "left in place deliberately: NOT provably mine, must not delete by exclusion")
    except Exception:
        result["error_log_cleanup_error"] = traceback.format_exc()

    os.makedirs(OUTDIR, exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=1, default=str)
    print("WROTE " + OUT)
    frappe.destroy()
