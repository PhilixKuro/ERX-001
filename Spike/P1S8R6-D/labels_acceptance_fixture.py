"""Temporary TS-009 display fixtures; only test.localhost, exact cleanup."""
import json
import sys
from pathlib import Path
from unittest.mock import patch

import frappe

MANIFEST = Path('/workspace/frappe-bench/logs/s8-ts009-acceptance-fixture.json')
frappe.init(site='test.localhost', sites_path='/workspace/frappe-bench/sites')
frappe.connect()
try:
    assert frappe.local.site == 'test.localhost'
    frappe.set_user('Administrator')
    frappe.local.lang = 'zh'
    if sys.argv[1] == 'create':
        if MANIFEST.exists():
            raise RuntimeError('Clean previous TS-009 display fixtures first')
        from frappe_china.tests.test_process_loss import TestProcessLoss
        from frappe_china.tests.test_piece_rate import TestPieceRate
        from frappe_china.tests.spc_data import make_spc_inspections

        bom = TestProcessLoss._make_bom(TestProcessLoss(), 1000, 'Nos', (0, 0, 0))
        for row in bom.operations:
            operation = frappe.get_doc('Operation', row.operation)
            operation.cn_piece_rate = 0.004
            operation.save()
            operation.reload()
            assert operation.cn_piece_rate == 0.004
            row.cn_piece_rate = 0.004
        bom.save()
        bom.reload()
        assert all(row.cn_piece_rate == 0.004 for row in bom.operations)
        spc = make_spc_inspections()
        employee = TestPieceRate._employee(TestPieceRate(), assigned=False)
        rows = [dict(operation=bom.operations[0].operation, completed_qty=100, rate=0.004, rate_source=source, amount=0.4)
                for source in ('BOM Operation', 'Operation', 'No Piece Rate')]
        # Synthetic calculation rows are display fixtures only, never payroll evidence.
        with patch('frappe_china.production_plus.doctype.piece_rate_summary.piece_rate_summary.collect_rows', return_value=rows):
            summary = frappe.get_doc(dict(doctype='Piece Rate Summary', employee=employee.name, company=employee.company,
                                          from_date='2026-10-01', to_date='2026-10-31')).insert()
        targets = [('Piece Rate Summary', summary.name), ('Employee', employee.name)]
        targets += [('Quality Inspection', name) for name in spc['inspections']]
        targets += [('Stock Entry', spc['entry']), ('Item', spc['item']), ('Quality Inspection Parameter', spc['parameter'])]
        targets += [('BOM', bom.name), ('Item', bom.item), ('Item', bom.items[0].item_code)]
        targets += [('Operation', row.operation) for row in bom.operations]
        targets += [('Workstation', bom.operations[0].workstation)]
        manifest = dict(site='test.localhost', bom=bom.name, operation=bom.operations[0].operation,
                        spc=spc, summary=summary.name, employee_name=employee.employee_name, targets=targets)
        MANIFEST.write_text(json.dumps(manifest, ensure_ascii=False), encoding='utf-8')
        frappe.db.commit()
        print(json.dumps(manifest, ensure_ascii=False))
    elif sys.argv[1] == 'cleanup':
        manifest = json.loads(MANIFEST.read_text(encoding='utf-8'))
        assert manifest['site'] == 'test.localhost'
        for doctype, name in manifest['targets']:
            if not frappe.db.exists(doctype, name):
                continue
            doc = frappe.get_doc(doctype, name)
            if doc.docstatus == 1:
                doc.cancel()
            frappe.delete_doc(doctype, name)
        remaining = [target for target in manifest['targets'] if frappe.db.exists(*target)]
        assert not remaining, remaining
        frappe.db.commit()
        MANIFEST.unlink()
        print(json.dumps(dict(cleaned=len(manifest['targets']), remaining=remaining)))
    else:
        raise ValueError('Expected create or cleanup')
except Exception:
    frappe.db.rollback()
    raise
finally:
    frappe.destroy()
