// SL-006 and D discussion step 4; staged during SL-005 full regression.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
const sourceRoot = process.env.BOM_CONFIRM_SOURCE || path.join(__dirname, '../../frappe-bench/apps/frappe_china/frappe_china/public/js');

function setup(doctype, row = {}) {
  const events = {}, dialogs = [], calls = [], updates = [];
  const choice = { auto: true, bom: 'BOM-CHEAP', candidates: [
    { bom: 'BOM-DEFAULT', unit_cost: 100 }, { bom: 'BOM-CHEAP', unit_cost: 10 },
  ] };
  const doc = { doctype, docstatus: 0, company: '_Test Company', production_item: '_FCT FG', bom_no: 'BOM-DEFAULT', ...row };
  if (doctype === 'Production Plan') doc.po_items = [{ doctype: 'Production Plan Item', name: 'ROW1', item_code: '_FCT FG', bom_no: 'BOM-DEFAULT', ...row }];
  const target = doc.po_items?.[0] || doc;
  const frm = { doc, fields_dict: {}, is_new: () => true, dirty() {}, refresh_field() {},
    async set_value(field, value) { updates.push([field, value]); if (typeof field === 'object') Object.assign(doc, field); else doc[field] = value; },
    dashboard: { set_headline_alert() {} },
  };
  const escape = value => String(value).replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
  const frappe = { validated: true,
    ui: { form: { on(name, handlers) { events[name] = { ...events[name], ...handlers }; } },
      Dialog: class {
        constructor(options) { Object.assign(this, options); dialogs.push(this); }
        show() {}
        hide() { this.onhide?.(); this.on_hide?.(); }
      },
    },
    utils: { escape_html: escape },
    async xcall(method, args) { calls.push({ method, args }); return choice; },
    call() {},
    model: { async set_value(cdt, cdn, field, value) { const row = doc.po_items?.find(item => item.name === cdn) || target; updates.push([field, value]); if (typeof field === 'object') Object.assign(row, field); else row[field] = value; } },
  };
  vm.runInNewContext(fs.readFileSync(path.join(sourceRoot, doctype === 'Production Plan' ? 'production_plan.js' : 'work_order.js'), 'utf8'), {
    frappe, __: (key, args) => args ? key.replace(/\{(\d+)\}/g, (_, index) => args[index]) : key,
  });
  const save = () => { assert.equal(typeof events[doctype].before_save, 'function', 'saving must request a BOM decision'); return events[doctype].before_save(frm); };
  return { events, dialogs, calls, updates, choice, target, frm, frappe, save };
}

const tick = () => new Promise(resolve => setImmediate(resolve));

test('plan keep survives first save; next save asks again and can use recommendation', async () => {
  const s = setup('Production Plan');
  let settled = false;
  const first = s.save().then(() => { settled = true; });
  await tick();
  assert.equal(settled, false, 'save waits for the decision');
  assert.equal(s.dialogs.length, 1);
  const html = JSON.stringify(s.dialogs[0].fields);
  assert.ok(html.includes('BOM-CHEAP') && html.includes('BOM-DEFAULT'));
  assert.ok(html.includes('100') && html.includes('10'));
  assert.equal(s.dialogs[0].secondary_action_label, 'Keep current BOM');
  s.dialogs[0].secondary_action();
  await first;
  assert.equal(s.target.bom_no, 'BOM-DEFAULT');
  assert.equal(s.target.cn_bom_source, 'kept');
  const second = s.save(); await tick();
  assert.equal(s.dialogs.length, 2, 'kept is asked again under user-approved A');
  assert.equal(s.dialogs[1].primary_action_label, 'Use recommended BOM');
  s.dialogs[1].primary_action(); await second;
  assert.equal(s.target.bom_no, 'BOM-CHEAP');
  assert.equal(s.target.cn_bom_source, 'confirmed');
  await s.save();
  assert.equal(s.dialogs.length, 2, 'confirmed does not ask again');
});

for (const doctype of ['Production Plan', 'Work Order']) {
  test(doctype + ' respects confirmed and manual choices', async () => {
    for (const source of ['confirmed', 'manual']) {
      const s = setup(doctype, { cn_bom_source: source }); await s.save();
      assert.equal(s.calls.length, 0);
      assert.equal(s.target.bom_no, 'BOM-DEFAULT'); assert.equal(s.dialogs.length, 0);
    }
  });
  test(doctype + ' skips matching recommendations and disabled auto-selection', async () => {
    for (const change of [{ bom: 'BOM-DEFAULT' }, { auto: false }, { bom: null }]) {
      const s = setup(doctype); Object.assign(s.choice, change); await s.save();
      assert.equal(s.dialogs.length, 0); assert.equal(s.target.bom_no, 'BOM-DEFAULT');
    }
  });
  test(doctype + ' dismissal prevents save without recording a choice', async () => {
    const s = setup(doctype); const saving = s.save(); await tick();
    s.dialogs[0].hide(); await saving.catch(() => {});
    assert.equal(s.frappe.validated, false); assert.equal(s.target.bom_no, 'BOM-DEFAULT');
    assert.equal(s.target.cn_bom_source, undefined);
  });
  test(doctype + ' escapes candidate identifiers in confirmation table', async () => {
    const s = setup(doctype); s.choice.candidates[0].bom = '<img src=x onerror=alert(1)>';
    const saving = s.save(); await tick(); const html = JSON.stringify(s.dialogs[0].fields);
    assert.ok(html.includes('&lt;img')); assert.ok(!html.includes('<img'));
    s.dialogs[0].secondary_action(); await saving;
  });
}

test('work order use updates BOM through form setter and records confirmed before saving', async () => {
  const s = setup('Work Order'); const saving = s.save(); await tick();
  s.dialogs[0].primary_action(); await saving;
  assert.equal(s.target.bom_no, 'BOM-CHEAP'); assert.equal(s.target.cn_bom_source, 'confirmed');
  assert.ok(s.updates.some(([field]) => field === 'bom_no' || typeof field === 'object' && field.bom_no));
});

test('work order inherited from production plan is saved without a new choice', async () => {
  const s = setup('Work Order', { production_plan: '_FCT Plan' }); await s.save();
  assert.equal(s.calls.length, 0); assert.equal(s.dialogs.length, 0);
});

test('saved draft work order with kept source asks again and can switch', async () => {
  const s = setup('Work Order', { cn_bom_source: 'kept' }); s.frm.is_new = () => false;
  const saving = s.save(); await tick();
  assert.equal(s.dialogs.length, 1); s.dialogs[0].primary_action(); await saving;
  assert.equal(s.target.bom_no, 'BOM-CHEAP'); assert.equal(s.target.cn_bom_source, 'confirmed');
});

test('production plan confirms multiple rows sequentially', async () => {
  const s = setup('Production Plan');
  s.frm.doc.po_items.push({ ...s.target, name: 'ROW2', item_code: '_FCT FG2' });
  const saving = s.save(); await tick();
  assert.equal(s.dialogs.length, 1); assert.equal(s.calls.length, 1);
  s.dialogs[0].secondary_action(); await tick();
  assert.equal(s.dialogs.length, 2); assert.equal(s.calls.length, 2);
  s.dialogs[1].primary_action(); await saving;
  assert.equal(s.frm.doc.po_items[0].cn_bom_source, 'kept');
  assert.equal(s.frm.doc.po_items[1].cn_bom_source, 'confirmed');
  assert.equal(s.frm.doc.po_items[1].bom_no, 'BOM-CHEAP');
});

test('dismissing first plan row prevents processing later rows', async () => {
  const s = setup('Production Plan');
  s.frm.doc.po_items.push({ ...s.target, name: 'ROW2', item_code: '_FCT FG2' });
  const saving = s.save(); await tick(); s.dialogs[0].hide(); await saving.catch(() => {});
  assert.equal(s.frappe.validated, false); assert.equal(s.calls.length, 1);
  assert.equal(s.frm.doc.po_items[1].cn_bom_source, undefined);
});

test('submitted work order with kept source is not prompted', async () => {
  const s = setup('Work Order', { cn_bom_source: 'kept', docstatus: 1 });
  s.frm.is_new = () => false; await s.save(); assert.equal(s.calls.length, 0);
});
