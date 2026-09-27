# V-30 seg0c: identify the storage engine of tabError Log.
#
# seg0b showed the Error Log row survives rollback with ZERO commit() calls
# intercepted. On MariaDB the classic cause is a NON-TRANSACTIONAL storage engine
# (MyISAM/Aria): DML against such a table is never part of the InnoDB transaction,
# so rollback cannot undo it -- and no commit() appears anywhere, which matches
# exactly what seg0b observed.
#
# This is READ-ONLY (information_schema + a rollback-only cleanup attempt).
# It decides whether sub-question (c) can be run safely, and if so, how to clean up:
# for a non-transactional table the cleanup is an explicit frappe.db.delete of the
# rows I create, scoped by primary key -- NOT a site-wide truncate.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V30-seg0c-engine.py

import json
import traceback

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/V30-out/seg0c-engine.json"

result = {"probe": "V-30 seg0c: storage engine of tabError Log"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2500], flush=True)


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

try:
    rows = frappe.db.sql(
        """select table_name, engine, table_rows
           from information_schema.tables
           where table_schema = %s
             and table_name in ('tabError Log', 'tabGL Entry', 'tabAccount',
                                'tabFinancial Report Template', 'tabVersion',
                                'tabActivity Log')
           order by table_name""",
        (frappe.conf.db_name,), as_dict=True)
    rec("table_engines", rows)

    err_engine = None
    for r in rows:
        if r["table_name"] == "tabError Log":
            err_engine = r["engine"]
    rec("tabError_Log_engine", err_engine)
    rec("is_transactional", err_engine == "InnoDB")

    # DocType-level declaration, if any
    meta_engine = frappe.db.get_value("DocType", "Error Log", "engine")
    rec("doctype_engine_field", meta_engine)

    # confirm business tables ARE transactional (so the rest of the spike's
    # rollback-based safety still holds for the writes that actually matter)
    biz = {r["table_name"]: r["engine"] for r in rows if r["table_name"] != "tabError Log"}
    rec("business_tables_engines", biz)
    rec("all_business_tables_innodb", all(v == "InnoDB" for v in biz.values()))

    # ---- clean up the two marker rows my own earlier probes left behind ----
    # Non-transactional => rollback will not do it; delete them explicitly by name.
    marks = frappe.get_all("Error Log", filters={"method": ["like", "%V30 seg0%"]},
                           fields=["name", "method"])
    rec("my_marker_rows_found", marks)
    for m in marks:
        frappe.db.delete("Error Log", {"name": m["name"]})
    rec("markers_remaining_after_delete",
        frappe.get_all("Error Log", filters={"method": ["like", "%V30 seg0%"]},
                       fields=["name"]))
    rec("error_log_rows_now",
        [{"name": r.name, "method": (r.method or "")[:70]}
         for r in frappe.get_all("Error Log", fields=["name", "method"],
                                 order_by="creation desc", limit=8)])
    rec("error_log_count_now", frappe.db.count("Error Log"))

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-2500:]})

finally:
    # No commit: on a non-transactional table the delete already took effect;
    # on a transactional one there is nothing here worth keeping.
    frappe.db.rollback()
    rec("error_log_count_after_rollback", frappe.db.count("Error Log"))
    rec("markers_after_rollback",
        frappe.get_all("Error Log", filters={"method": ["like", "%V30 seg0%"]},
                       fields=["name"]))

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
