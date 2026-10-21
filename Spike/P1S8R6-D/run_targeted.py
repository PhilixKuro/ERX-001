"""Run several focused modules with the standard Frappe runner, one initialization."""
import sys

import frappe
from frappe.testing import TestConfig, TestRunner, discover_module_tests
from frappe.testing.environment import _cleanup_after_tests, _initialize_test_environment

assert sys.argv[1] == 'test.localhost'
config = TestConfig(skip_before_tests=True)
_initialize_test_environment(sys.argv[1], config)
try:
    runner = TestRunner(cfg=config, verbosity=2)
    for module in sys.argv[2:]:
        discover_module_tests(module, runner, None)
    results = []
    for app, category, suite in runner.iterRun():
        print(f'Running {suite.countTestCases()} {category} tests for {app}', flush=True)
        result = runner.run(suite)
        results.append(result.wasSuccessful())
    exit_code = int(not all(results))
    print(f'Targeted suites successful: {results}; exit_code={exit_code}', flush=True)
finally:
    _cleanup_after_tests()
    frappe.destroy()
sys.exit(exit_code)
