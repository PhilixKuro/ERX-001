"""Temporary real TS-010 report documents, isolated on test.localhost."""
import json
import sys
from pathlib import Path

import frappe

manifest_path = Path('/workspace/frappe-bench/logs/s8-strategy-ui-fixture.json')
frappe.init(site='test.localhost', sites_path='/workspace/frappe-bench/sites')
frappe.connect()
try:
    assert frappe.local.site == 'test.localhost'
    frappe.set_user('Administrator')
    frappe.local.lang = 'zh'
    if sys.argv[1] == 'create':
        if manifest_path.exists():
            raise RuntimeError('Clean previous TS-010 fixture before creating another')
        from frappe_china.tests.test_strategy_comparison import TestStrategyComparison
        case = TestStrategyComparison()
        # Explicit fixture setup, not unittest lifecycle: no app setting changes outside this scope.
        case.company = '_Test Company'
        case.warehouse = 'Stores - _TC'
        from frappe.utils import getdate, today
        from datetime import timedelta
        case.start = getdate(today()) - timedelta(days=40)
        case.suffix = frappe.generate_hash(length=7)
        original = frappe.db.get_value('Company', case.company, ['cn_order_cost', 'cn_holding_rate'], as_dict=True)
        targets = []
        try:
            case.item = case.make_item('UI Raw', cn_rule_eoq=1)
            targets.append(['Item', case.item.name])
            for qty, offset in ((100, -1), (-20, 4), (40, 10), (-30, 15)):
                targets.insert(0, ['Stock Entry', case.movement(qty, offset).name])
            for offset in (0, 9, 10):
                targets.insert(0, ['Purchase Order', case.purchase_order(offset).name])
            frappe.db.set_value('Company', case.company, {'cn_order_cost': 20, 'cn_holding_rate': 20})
            manifest = {'site': 'test.localhost', 'company': case.company, 'original': original,
                        'filters': case.filters(), 'targets': targets}
            manifest_path.write_text(json.dumps(manifest, default=str, ensure_ascii=False), encoding='utf-8')
            frappe.db.commit()
            print(json.dumps(manifest, default=str, ensure_ascii=False))
        except Exception:
            frappe.db.rollback()
            raise
    elif sys.argv[1] == 'inspect':
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        assert manifest['site'] == 'test.localhost'
        vouchers = [name for doctype, name in manifest['targets'] if doctype == 'Stock Entry']
        result = {'targets': [], 'ledgers': {}, 'company': frappe.db.get_value(
            'Company', manifest['company'], ['cn_order_cost', 'cn_holding_rate'], as_dict=True)}
        for doctype, name in manifest['targets']:
            result['targets'].append([doctype, name, frappe.db.get_value(doctype, name, 'docstatus')])
        for doctype in ('Stock Ledger Entry', 'GL Entry', 'Repost Item Valuation'):
            fields = ['name', 'docstatus', 'voucher_type', 'voucher_no']
            fields += [field for field in ('is_cancelled', 'item_code', 'company', 'status')
                       if frappe.get_meta(doctype).has_field(field)]
            result['ledgers'][doctype] = frappe.get_all(doctype, filters={
                'voucher_type': 'Stock Entry', 'voucher_no': ['in', vouchers]}, fields=fields)
        result['item_reposts'] = frappe.get_all('Repost Item Valuation', filters={
            'item_code': ['in', [name for doctype, name in manifest['targets'] if doctype == 'Item']]}, fields=['*'])
        print(json.dumps(result, default=str, ensure_ascii=False))
    elif sys.argv[1] == 'cleanup':
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        assert manifest['site'] == 'test.localhost'
        item_names = {name for doctype, name in manifest['targets'] if doctype == 'Item'}
        vouchers = [name for doctype, name in manifest['targets'] if doctype == 'Stock Entry']
        assert len(item_names) == 1 and next(iter(item_names)).startswith('_FCT Strategy UI Raw ')
        # Use ERPNext's native synchronous repost path for isolated test cleanup;
        # otherwise cancelled fixture vouchers wait for the disabled scheduler.
        frappe.in_test = True
        # Validate ownership before cancelling, including each voucher's child rows.
        for doctype, name in manifest['targets']:
            if doctype not in ('Stock Entry', 'Purchase Order') or not frappe.db.exists(doctype, name):
                continue
            doc = frappe.get_doc(doctype, name)
            assert doc.company == manifest['company']
            assert doc.items and {row.item_code for row in doc.items} <= item_names
        for doctype, name in manifest['targets']:
            if doctype == 'Item' or not frappe.db.exists(doctype, name):
                continue
            doc = frappe.get_doc(doctype, name)
            if doc.docstatus == 1:
                doc.cancel()
        # Cancellation can enqueue item-based reposts without a voucher link.
        # The manifest's unique item is the positive ownership key in that path.
        item_reposts = frappe.get_all('Repost Item Valuation', filters={
            'item_code': ['in', sorted(item_names)]}, fields=['name', 'company', 'status'])
        for row in item_reposts:
            assert row.company == manifest['company'] and row.status != 'In Progress'
            repost = frappe.get_doc('Repost Item Valuation', row.name)
            if repost.docstatus == 1:
                repost.cancel()
            frappe.delete_doc('Repost Item Valuation', row.name)
        # Immutable ledger cancellation retains rows. Remove only this manifest's
        # cancelled voucher rows, after their ownership and cancellation checks.
        removed_ledgers = {}
        for doctype in ('Stock Ledger Entry', 'GL Entry'):
            rows = frappe.get_all(doctype, filters={
                'voucher_type': 'Stock Entry', 'voucher_no': ['in', vouchers]}, fields=['*'])
            for row in rows:
                assert row.company == manifest['company'] and row.is_cancelled == 1
                assert frappe.db.get_value('Stock Entry', row.voucher_no, 'docstatus') == 2
                if doctype == 'Stock Ledger Entry':
                    assert row.item_code in item_names
            removed_ledgers[doctype] = [row.name for row in rows]
            if rows:
                frappe.db.delete(doctype, {'name': ['in', removed_ledgers[doctype]]})
        reposts = frappe.get_all('Repost Item Valuation', filters={
            'voucher_type': 'Stock Entry', 'voucher_no': ['in', vouchers]}, pluck='name')
        assert not reposts, reposts
        for doctype, name in manifest['targets']:
            if not frappe.db.exists(doctype, name):
                continue
            doc = frappe.get_doc(doctype, name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc(doctype, name)
        frappe.db.set_value('Company', manifest['company'], manifest['original'])
        remaining = [target for target in manifest['targets'] if frappe.db.exists(*target)]
        assert not remaining, remaining
        for doctype in ('Stock Ledger Entry', 'GL Entry'):
            assert not frappe.db.exists(doctype, {
                'voucher_type': 'Stock Entry', 'voucher_no': ['in', vouchers]})
        frappe.db.commit()
        evidence = {'cleaned': len(manifest['targets']), 'remaining': remaining,
                    'removed_cancelled_ledgers': removed_ledgers,
                    'removed_item_reposts': [row.name for row in item_reposts],
                    'restored_company': frappe.db.get_value('Company', manifest['company'],
                        ['cn_order_cost', 'cn_holding_rate'], as_dict=True)}
        manifest_path.with_name('s8-strategy-ui-cleanup.json').write_text(
            json.dumps(evidence, default=str, ensure_ascii=False), encoding='utf-8')
        manifest_path.unlink()
        print(json.dumps(evidence, default=str, ensure_ascii=False))
finally:
    frappe.destroy()
