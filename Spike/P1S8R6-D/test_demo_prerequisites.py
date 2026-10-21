"""SL-010 expectations fixed from R5 Part1; test docker script before implementation."""

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch

import frappe

spec = importlib.util.spec_from_file_location(
    's8_configure_apps', '/workspace/docker/scripts/configure_apps.py'
)
configure = importlib.util.module_from_spec(spec)
spec.loader.exec_module(configure)


class Document(dict):
    def __init__(self, **values):
        super().__init__(values)
        self.saves = 0

    def set(self, key, value):
        self[key] = value

    def save(self, **kwargs):
        self.saves += 1


class TestDemoPrerequisites(unittest.TestCase):
    def run_configuration(self, *, first_name='Administrator', stock_enabled=0, seeded=False):
        from frappe.desk.page.setup_wizard import install_fixtures

        counts = {'Gender': 7 if seeded else 0, 'Salutation': 9 if seeded else 0}
        stock = Document(enable_serial_and_batch_no_for_item=stock_enabled)
        administrator = Document(first_name=first_name)
        notes = []

        def seed_gender():
            counts['Gender'] = 7

        def seed_salutation():
            counts['Salutation'] = 9

        with (
            patch.object(frappe.db, 'count', side_effect=lambda doctype: counts[doctype]),
            patch.object(install_fixtures, 'update_genders', side_effect=seed_gender),
            patch.object(install_fixtures, 'update_salutations', side_effect=seed_salutation),
            patch.object(frappe, 'get_single', return_value=stock),
            patch.object(frappe, 'get_doc', return_value=administrator),
        ):
            first = configure.configure_demo_prerequisites(notes)
            second = configure.configure_demo_prerequisites(notes)
        return first, second, stock, administrator, counts

    def test_initial_run_seeds_native_lists_and_enables_batch_and_admin_name(self):
        changes, repeated, stock, admin, counts = self.run_configuration()
        self.assertEqual(counts, {'Gender': 7, 'Salutation': 9})
        self.assertEqual(stock['enable_serial_and_batch_no_for_item'], 1)
        self.assertEqual(admin['first_name'], '演示管理员')
        self.assertTrue(changes)
        self.assertEqual(repeated, {})
        self.assertEqual((stock.saves, admin.saves), (1, 1))

    def test_custom_administrator_name_is_preserved(self):
        changes, repeated, stock, admin, counts = self.run_configuration(
            first_name='车间管理员', stock_enabled=1, seeded=True
        )
        self.assertEqual(admin['first_name'], '车间管理员')
        self.assertEqual((changes, repeated), ({}, {}))
        self.assertEqual((stock.saves, admin.saves), (0, 0))

    def test_target_state_reports_no_changes(self):
        changes, repeated, stock, admin, counts = self.run_configuration(
            first_name='演示管理员', stock_enabled=1, seeded=True
        )
        self.assertEqual((changes, repeated), ({}, {}))
        self.assertEqual((stock.saves, admin.saves), (0, 0))

    def test_main_keeps_both_stock_changes_in_output_and_runs_prerequisites_after_stock(self):
        calls = []
        output = []

        def stock(notes):
            calls.append('stock')
            return {'Stock Settings': {'auto_indent': (1, 0)}}

        def prerequisites(notes):
            calls.append('prerequisites')
            return {'Stock Settings': {'enable_serial_and_batch_no_for_item': (0, 1)}}

        with (
            patch.object(frappe, 'init'),
            patch.object(frappe, 'connect'),
            patch.object(frappe, 'destroy'),
            patch.object(frappe, 'clear_cache'),
            patch.object(frappe.db, 'commit') as commit,
            patch.object(configure, 'preflight', return_value='_FCT CRM'),
            patch.object(configure, 'configure_crm', return_value={}),
            patch.object(configure, 'configure_stock', side_effect=stock),
            patch.object(configure, 'configure_demo_prerequisites', side_effect=prerequisites),
            patch.object(configure, 'configure_raven', return_value={}),
            patch.object(configure, 'ensure_bot_and_functions', return_value={}),
            patch.object(configure, '_print_changes', side_effect=lambda result: output.append(result)),
        ):
            self.assertEqual(configure.main(['--site', 'test.localhost']), 0)
        self.assertEqual(calls, ['stock', 'prerequisites'])
        self.assertEqual(output, [{'Stock Settings': {
            'auto_indent': (1, 0), 'enable_serial_and_batch_no_for_item': (0, 1)}}])
        commit.assert_called_once()


if __name__ == '__main__':
    frappe.init(site='test.localhost', sites_path='/workspace/frappe-bench/sites')
    frappe.connect()
    try:
        unittest.main(verbosity=2)
    finally:
        frappe.destroy()
