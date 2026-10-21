const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');
const root = path.join(__dirname, '../../frappe-bench/logs');

(async () => {
  const fixture = JSON.parse(fs.readFileSync(path.join(root, 's8-bom-confirmation-fixture.json'), 'utf8'));
  assert.equal(fixture.site, 'test.localhost');
  const c = await open();
  try {
    assert.equal(await c.evaluate('frappe.boot.sitename'), 'test.localhost');
    await c.evaluate('frappe.new_doc(\'Production Plan\')');
    await c.until('window.cur_frm?.doctype === \'Production Plan\' && cur_frm.is_new()');
    await c.evaluate('cur_frm.set_value(' + JSON.stringify({ company: fixture.company, get_items_from: 'Sales Order' }) + ')');
    await c.evaluate('(() => { const row=cur_frm.add_child(\'sales_orders\'); row.sales_order=' + JSON.stringify(fixture.order) + '; cur_frm.refresh_field(\'sales_orders\'); })()');
    await c.evaluate('void cur_frm.trigger(\'get_items\')');
    await c.until('cur_frm.doc.po_items?.length === 1 && !frappe.dom.freeze_count');
    assert.equal(await c.evaluate('cur_frm.doc.po_items[0].bom_no'), fixture.default_bom);
    await c.evaluate('frappe.model.set_value(cur_frm.doc.po_items[0].doctype, cur_frm.doc.po_items[0].name, \'warehouse\', \'Finished Goods - _TC\')');
    await c.evaluate('(() => { window.bomSaveError=null; window.bomSaveDone=false; cur_frm.save().then(() => {window.bomSaveDone=true;}).catch(e => {window.bomSaveError=String(e);}); })()');
    await c.until('window.cur_dialog?.title === __(\'Confirm BOM recommendation\')');
    const table = await c.evaluate('cur_dialog.$body.text()');
    assert.ok(table.includes(fixture.cheap_bom) && table.includes(fixture.default_bom));
    await c.screenshot(path.join(__dirname, 'SL006-plan-first-confirm.png'));
    await c.evaluate('cur_dialog.get_secondary_btn()[0].click()');
    await c.until('window.bomSaveDone || window.bomSaveError', 60000);
    assert.equal(await c.evaluate('window.bomSaveError'), null);
    const first = await c.evaluate('({name:cur_frm.doc.name,bom:cur_frm.doc.po_items[0].bom_no,source:cur_frm.doc.po_items[0].cn_bom_source})');
    assert.equal(first.bom, fixture.default_bom); assert.equal(first.source, 'kept');
    await c.screenshot(path.join(__dirname, 'SL006-plan-kept.png'));

    await c.evaluate('cur_frm.reload_doc()');
    await c.evaluate('(() => { window.bomSaveDone=false; cur_frm.dirty(); cur_frm.save().then(() => {window.bomSaveDone=true;}).catch(e => {window.bomSaveError=String(e);}); })()');
    await c.until('window.cur_dialog?.title === __(\'Confirm BOM recommendation\')');
    await c.screenshot(path.join(__dirname, 'SL006-plan-second-confirm.png'));
    await c.evaluate('cur_dialog.get_primary_btn()[0].click()');
    await c.until('window.bomSaveDone || window.bomSaveError', 60000);
    assert.equal(await c.evaluate('window.bomSaveError'), null);
    await c.evaluate('cur_frm.reload_doc()');
    const second = await c.evaluate('({name:cur_frm.doc.name,bom:cur_frm.doc.po_items[0].bom_no,source:cur_frm.doc.po_items[0].cn_bom_source})');
    assert.equal(second.name, first.name); assert.equal(second.bom, fixture.cheap_bom); assert.equal(second.source, 'confirmed');
    await c.screenshot(path.join(__dirname, 'SL006-plan-confirmed.png'));
    await c.evaluate('(() => {window.bomSaveDone=false; cur_frm.dirty(); cur_frm.save().then(() => {window.bomSaveDone=true;}).catch(e => {window.bomSaveError=String(e);});})()');
    await c.until('window.bomSaveDone || window.bomSaveError', 60000);
    assert.equal(await c.evaluate('window.bomSaveError'), null);
    assert.equal(await c.evaluate('!!window.cur_dialog?.display'), false);

    const result = { site: fixture.site, first, second, confirmedSaveHasNoDialog: true };
    fs.writeFileSync(path.join(root, 's8-bom-confirmation-ui.json'), JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result));
  } finally { await c.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
