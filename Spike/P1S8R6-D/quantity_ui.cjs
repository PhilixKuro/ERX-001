const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { open } = require('../P1S6R4-cdp.cjs');

(async () => {
  const manifest = JSON.parse(fs.readFileSync(path.join(__dirname, '../../frappe-bench/logs/s8-quantity-ui-fixture.json'), 'utf8'));
  const c = await open();
  try {
    assert.equal(await c.evaluate('frappe.boot.sitename'), 'test.localhost');
    await c.evaluate(`frappe.set_route('Form', 'Production Plan', ${JSON.stringify(manifest.plan)})`);
    await c.until(`window.cur_frm?.doc?.name === ${JSON.stringify(manifest.plan)} && !cur_frm.is_new() && !!cur_frm.fields_dict.po_items.grid.grid_rows.length`, 45000);
    const values = await c.evaluate(`(() => {
      const row = cur_frm.fields_dict.po_items.grid.grid_rows[0];
      row.toggle_view(true);
      return { site: frappe.boot.sitename, plan: cur_frm.doc.name, planned: row.doc.planned_qty,
        recommended: row.doc.cn_recommended_qty, demand: row.doc.cn_demand_qty };
    })()`);
    assert.equal(values.planned, 5300);
    assert.equal(values.recommended, 5264);
    assert.equal(values.demand, 5000);
    await c.until(`document.body.innerText.includes('推荐 5264') || document.body.innerText.includes('Recommended 5264')`);
    await c.evaluate(`cur_frm.fields_dict.po_items.grid.grid_rows[0].grid_form.fields_dict.planned_qty.$wrapper[0].scrollIntoView({ block: 'center' })`);
    await c.pause(300);
    await c.screenshot(path.join(__dirname, 'SL003-manual-recommendation.png'));
    console.log(JSON.stringify({ ...values, recommendationVisible: true, screenshot: 'SL003-manual-recommendation.png' }));
  } finally { await c.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
