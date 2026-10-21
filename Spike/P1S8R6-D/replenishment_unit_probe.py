"""Run SL-007 mock contracts without opening a site or database connection."""
import importlib.util
import logging
import os
import runpy
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch

import frappe
import frappe_china.replenishment

frappe.logger = lambda *args, **kwargs: logging.getLogger(args[0] if args else 'frappe')

root = Path('/workspace/Spike/P1S8R6-D')
if os.environ.get('REPLENISHMENT_DRAFT'):
    for name in ('types', 'demand', 'safety_stock', 'reorder_level', 'rules', 'suggestion', 'daily'):
        full = 'frappe_china.replenishment.' + name
        spec = importlib.util.spec_from_file_location(full, root / 'replenishment-draft' / (name + '.py'))
        mod = importlib.util.module_from_spec(spec)
        sys.modules[full] = mod
        setattr(frappe_china.replenishment, name, mod)
        spec.loader.exec_module(mod)
stub = types.ModuleType('frappe_china.tests.utils')
stub.FrappeChinaTestCase = unittest.TestCase
sys.modules[stub.__name__] = stub
cls = runpy.run_path(root / 'test_replenishment_s8_details.py')['TestS8ReplenishmentDetails']
with patch('frappe.get_system_settings', return_value='Commercial Rounding'):
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(cls))
raise SystemExit(not result.wasSuccessful())
