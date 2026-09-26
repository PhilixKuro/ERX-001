import json, os, glob, sys
BENCH = r'D:\ERX-001\frappe-bench\apps'
targets = [
 ('Vehicle','make'),('Contact Phone','phone'),('ToDo','owner'),
 ('Quality Meeting Minutes','minute'),('Account','tax_rate'),
 ('Sales Taxes and Charges','rate'),('Purchase Taxes and Charges','rate'),
 ('Advance Taxes and Charges','rate'),('Task','task_weight'),('Task Type','weight'),
 ('Project','margin'),('Purchase Invoice Item','manufacture_details'),
 ('Purchase Order Item','manufacture_details'),('Supplier Quotation Item','manufacture_details'),
 ('Material Request Item','manufacture_details'),('Purchase Receipt Item','manufacture_details'),
 ('Bank Account','account_name'),('Bank Account','account_type'),
 ('Bank Account','account_subtype'),('DocPerm','select'),('DocPerm','permlevel'),
 ('Item Customer Detail','ref_code'),('Sales Order','set_warehouse'),
 ('Role Profile','role_profile'),
 ('Bank Reconciliation Tool','bank_statement_closing_balance'),
]
# build index of doctype json files
index = {}
for app in ('frappe','erpnext'):
    root = os.path.join(BENCH, app)
    for path in glob.glob(os.path.join(root, '**', 'doctype', '*', '*.json'), recursive=True):
        base = os.path.basename(path)[:-5]
        parent = os.path.basename(os.path.dirname(path))
        if base != parent:
            continue
        try:
            with open(path, encoding='utf-8') as f:
                d = json.load(f)
        except Exception:
            continue
        if d.get('doctype') != 'DocType':
            continue
        index.setdefault(d.get('name'), path)

for dt, fn in targets:
    path = index.get(dt)
    if not path:
        print('%-32s %-32s FILE-NOT-FOUND' % (dt, fn)); continue
    with open(path, encoding='utf-8') as f:
        d = json.load(f)
    hit = None
    for fld in d.get('fields', []):
        if fld.get('fieldname') == fn:
            hit = fld; break
    if hit is None:
        print('%-32s %-32s FIELD-NOT-FOUND in %s' % (dt, fn, path)); continue
    lbl = hit.get('label')
    ft = hit.get('fieldtype')
    print('%-32s %-32s orig_label=%-34r fieldtype=%-12s istable=%s' % (
        dt, fn, lbl, ft, d.get('istable')))
