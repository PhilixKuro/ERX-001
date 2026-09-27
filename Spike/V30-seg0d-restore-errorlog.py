# V-30 seg0d: REPAIR. Restore the pre-existing Error Log rows my own seg2 cleanup bug
# deleted, as far as the available backup allows.
#
# WHAT WENT WRONG (my error, not a product defect):
# V30-seg2-shapes.py built its baseline set with
#     err_names_before = {r.name for r in frappe.get_all("Error Log", pluck="name")}
# but `pluck="name"` returns a list of plain STRINGS, so `r.name` raised
# AttributeError and the try-block aborted before the loop ever ran. The `finally`
# block then computed "rows not in err_names_before" against an EMPTY set, so it
# treated the two PRE-EXISTING rows as its own and deleted them:
#     r2pa0hpb8f  "Report execution failed for: VAT Audit Report"        2026-09-27 02:11:33
#     ukksv2d6f5  "Report execution failed for: Stock and Account Value Comparison"
#                                                                       2026-09-21 04:17:57
# Because tabError Log is MyISAM (non-transactional, proven in seg0c), frappe.db.rollback()
# could not undo it. Error Log went 2 -> 0. No business table was touched.
#
# RECOVERY: the newest backup is 20260925_185058. ukksv2d6f5 (created 09-21) predates it
# and should be recoverable verbatim. r2pa0hpb8f (created 09-27 02:11, after the backup)
# is NOT in any backup and is unrecoverable -- that is reported, not papered over.
#
# Method: locate the `INSERT INTO \`tabError Log\` VALUES` statement in the gzipped dump,
# split it into row tuples with a scanner that respects SQL string quoting and escapes
# (tracebacks contain commas, quotes and parens), then re-insert the matching tuple
# VERBATIM. Working in bytes throughout so the stored text is byte-exact.
#
# This script WRITES (one INSERT into a diagnostic MyISAM table) for the sole purpose of
# undoing my own damage. It restores only names in the lost set, and only if absent.
#
# Run (cwd MUST be .../sites, else frappe's logger dies on a relative path):
#   docker exec -i -w /workspace/frappe-bench/sites erx001-frappe-1 \
#     /workspace/frappe-bench/env/bin/python /workspace/Spike/V30-seg0d-restore-errorlog.py

import glob
import gzip
import json
import traceback

import frappe

SITE = "erx.localhost"
OUT = "/workspace/Spike/V30-out/seg0d-restore-errorlog.json"
LOST = ["r2pa0hpb8f", "ukksv2d6f5"]

result = {"probe": "V-30 seg0d repair: restore Error Log rows deleted by my seg2 bug"}


def rec(k, v):
    result[k] = v
    print("[" + k + "] " + json.dumps(v, ensure_ascii=False, default=str)[:2000], flush=True)


QUOTE = 39      # '
BSLASH = 92     # \
LPAREN = 40     # (
RPAREN = 41     # )
SEMI = 59       # ;


def split_row_tuples(buf: bytes):
    """Split `(...),(...);` into top-level tuples, honouring SQL quoting/escapes."""
    out = []
    depth = 0
    in_str = False
    esc = False
    start = None
    for i in range(len(buf)):
        ch = buf[i]
        if in_str:
            if esc:
                esc = False
            elif ch == BSLASH:
                esc = True
            elif ch == QUOTE:
                in_str = False
            continue
        if ch == QUOTE:
            in_str = True
            continue
        if ch == LPAREN:
            if depth == 0:
                start = i
            depth += 1
            continue
        if ch == RPAREN:
            depth -= 1
            if depth == 0 and start is not None:
                out.append(buf[start:i + 1])
                start = None
            continue
        if ch == SEMI and depth == 0:
            break
    return out


frappe.init(site=SITE)
frappe.connect()
frappe.set_user("Administrator")

try:
    rec("error_log_count_now", frappe.db.count("Error Log"))
    rec("rows_present_now",
        [{"name": r.name, "method": (r.method or "")[:60]}
         for r in frappe.get_all("Error Log", fields=["name", "method"])])

    backups = sorted(glob.glob(
        "/workspace/frappe-bench/sites/erx.localhost/private/backups/*-database.sql.gz"))
    rec("backups_available", [b.split("/")[-1] for b in backups])
    newest = backups[-1]
    rec("backup_used", newest.split("/")[-1])

    with gzip.open(newest, "rb") as f:
        blob = f.read()
    marker = b"INSERT INTO `tabError Log` VALUES"
    idx = blob.find(marker)
    rec("insert_statement_found", idx >= 0)

    recoverable = {}
    if idx >= 0:
        tail = blob[idx + len(marker):]
        tuples = split_row_tuples(tail)
        rec("n_row_tuples_in_backup", len(tuples))
        names_in_backup = []
        for t in tuples:
            # first field is the primary key: ('<name>',...
            try:
                head = t[1:40].decode("utf-8", errors="replace")
            except Exception:
                head = ""
            nm = head.split("'")[1] if head.count("'") >= 2 else None
            if nm:
                names_in_backup.append(nm)
            if nm in LOST:
                recoverable[nm] = t
        rec("names_in_backup", names_in_backup)

    rec("lost_rows", LOST)
    rec("recoverable_from_backup", sorted(recoverable.keys()))
    rec("unrecoverable",
        [n for n in LOST if n not in recoverable])

    # ---------- restore ----------
    restored = []
    failed = {}
    for nm, tup in recoverable.items():
        if frappe.db.exists("Error Log", nm):
            continue
        try:
            stmt = "INSERT INTO `tabError Log` VALUES " + tup.decode("utf-8")
            frappe.db.sql(stmt)
            restored.append(nm)
        except Exception as e:
            failed[nm] = type(e).__name__ + ": " + str(e)[:250]
    rec("restored", restored)
    rec("restore_failures", failed)

    rec("present_after_restore",
        [{"name": r.name, "method": (r.method or "")[:60], "creation": str(r.creation)}
         for r in frappe.get_all("Error Log", fields=["name", "method", "creation"],
                                 order_by="creation")])
    rec("error_log_count_after_restore", frappe.db.count("Error Log"))

except Exception as e:
    rec("probe_error", {"err": str(e), "tb": traceback.format_exc()[-2500:]})

finally:
    # MyISAM writes are non-transactional and already durable; rollback only clears
    # any InnoDB-side state. No commit() is issued.
    frappe.db.rollback()
    rec("error_log_count_final", frappe.db.count("Error Log"))
    counts = {}
    for dt in ["GL Entry", "Stock Ledger Entry", "Account", "Company",
               "Financial Report Template", "Fiscal Year"]:
        counts[dt] = frappe.db.count(dt)
    rec("business_counts_unaffected", counts)

    with open(OUT, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2, default=str)
    print("\nWROTE " + OUT, flush=True)
