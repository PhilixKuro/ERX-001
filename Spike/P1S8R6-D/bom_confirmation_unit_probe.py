"""Run SL-006 mocked contracts without connecting to any Frappe site."""
import importlib.util
import os
import runpy
import sys
import types
import unittest
from pathlib import Path

from frappe_china.production import bom_selection

root = Path("/workspace/Spike/P1S8R6-D")
draft = os.environ.get("BOM_CONFIRM_DRAFT")
if draft:
    spec = importlib.util.spec_from_file_location(bom_selection.__name__, root / "bom-confirmation-draft/bom_selection.py")
    bom_selection = importlib.util.module_from_spec(spec)
    sys.modules[bom_selection.__name__] = bom_selection
    spec.loader.exec_module(bom_selection)
    import frappe_china.production
    frappe_china.production.bom_selection = bom_selection

# These four tests exercise pure functions with mocks only; meta needs real migration later.
stub = types.ModuleType("frappe_china.tests.utils")
stub.FrappeChinaTestCase = unittest.TestCase
sys.modules[stub.__name__] = stub
sources = {
    "Inherited from production plan": "由生产计划带入",
    "Cost recommendation confirmed": "按成本推荐、人已确认",
    "Cost recommendation kept current": "按成本推荐、人选择保留",
    "BOM manually specified": "人工指定",
    "Selected automatically by cost": "按成本自动选用",
}
bom_selection._ = lambda value: sources.get(value, value)
cls = runpy.run_path(root / "test_bom_confirmation.py")["TestBomConfirmation"]
suite = unittest.TestSuite(cls(name) for name in unittest.defaultTestLoader.getTestCaseNames(cls)
                           if name != "test_hidden_source_fields_match_frozen_plan")
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(not result.wasSuccessful())
