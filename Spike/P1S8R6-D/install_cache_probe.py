"""SL-001 commit/rollback probe; no test fixtures or persistent setting writes."""

import os
import sys

import frappe

os.chdir("/workspace/frappe-bench/sites")
frappe.init(site="test.localhost")
frappe.connect()
try:
    if "--smoke" in sys.argv:
        from runpy import run_path

        smoke = run_path("../apps/frappe_debug/frappe_debug/tests/test_smoke.py")
        smoke["TestSmoke"]().test_debug_is_installed_after_china()
        print("debug installation/order smoke: passed")
    else:
        from frappe_china.tests.test_install import TestInstall

        for commit in (True, False):
            TestInstall()._check_reorder_transaction_cache(commit=commit)
            print(f"commit={commit}: passed")
finally:
    frappe.db.rollback()
    frappe.destroy()
