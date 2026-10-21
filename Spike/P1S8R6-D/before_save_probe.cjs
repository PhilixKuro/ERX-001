const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');

(async () => {
  const c = await open();
  try {
    assert.equal(await c.evaluate('frappe.boot.sitename'), 'test.localhost');
    await c.evaluate(`frappe.new_doc('BOM')`);
    await c.until(`window.cur_frm?.doctype === 'BOM' && cur_frm.is_new()`);
    await c.evaluate(`(() => {
      window.saveProbe = { calls: [], entered: 0, settled: 0 };
      frappe.ui.form.save = () => saveProbe.calls.push({ settled: saveProbe.settled, validated: frappe.validated });
      frappe.ui.form.on('BOM', { before_save(frm) {
        saveProbe.entered++;
        return new Promise((resolve, reject) => {
          saveProbe.resolve = () => { saveProbe.settled++; resolve(); };
          saveProbe.reject = reject;
        });
      }});
      cur_frm.dirty();
      cur_frm.page.btn_primary[0].click();
    })()`);
    await c.until('saveProbe.entered === 1');
    await c.pause(400);
    assert.equal(await c.evaluate('saveProbe.calls.length'), 0, 'save must wait for before_save');
    await c.evaluate('saveProbe.resolve()');
    await c.until('saveProbe.calls.length === 1');
    assert.deepEqual(await c.evaluate('saveProbe.calls[0]'), { settled: 1, validated: true });
    await c.evaluate('void cur_frm.save()');
    await c.until('saveProbe.entered === 2');
    await c.evaluate(`saveProbe.reject(new Error('HT006 expected rejection'))`);
    await c.pause(400);
    assert.equal(await c.evaluate('saveProbe.calls.length'), 1, 'rejected before_save must block');
    await c.evaluate('void cur_frm.save()');
    await c.until('saveProbe.entered === 3');
    await c.evaluate('frappe.validated = false; saveProbe.resolve()');
    await c.pause(400);
    assert.equal(await c.evaluate('saveProbe.calls.length'), 1, 'frappe.validated=false must block');
    const result = { site: 'test.localhost', ht006: 'go', promiseWaits: true, rejectionBlocks: true, validatedFalseBlocks: true, serverSaves: 0 };
    fs.writeFileSync(path.join(__dirname, '../../frappe-bench/logs/s8-before-save-probe.json'), JSON.stringify(result, null, 2));
    console.log(JSON.stringify(result));
  } finally { await c.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
