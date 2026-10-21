const assert = require('node:assert/strict');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');

(async () => {
  const c = await open();
  try {
    assert.equal(await c.evaluate('frappe.boot.sitename'), 'test.localhost');
    await c.evaluate(`frappe.new_doc('BOM')`);
    await c.until(`window.cur_frm?.doctype === 'BOM' && cur_frm.is_new()`);
    await c.evaluate(`cur_frm.set_value('with_operations', 1)`);
    await c.until(`!!cur_frm.fields_dict.operations.grid`);
    const data = await c.evaluate(`(() => {
      const field = cur_frm.fields_dict.operations;
      field.grid.refresh();
      field.$wrapper[0].scrollIntoView({ block: 'center' });
      return {
        site: frappe.boot.sitename,
        columns: field.grid.visible_columns.map(([df, width]) => ({ name: df.fieldname, label: __(df.label), width })),
        required: ['operation', 'workstation', 'time_in_mins', 'cn_process_loss_percentage'].map(name => {
          const el = field.$wrapper.find('.grid-heading-row [data-fieldname=' + name + ']')[0];
          const rect = el?.getBoundingClientRect();
          return { name, visible: !!rect && rect.width > 0 && rect.height > 0 };
        }),
      };
    })()`);
    for (const col of data.required) assert.equal(col.visible, true, col.name);
    await c.pause(400);
    await c.screenshot(path.join(__dirname, 'SL005-bom-operation-columns.png'));
    console.log(JSON.stringify({ ...data, screenshot: 'SL005-bom-operation-columns.png' }));
  } finally { await c.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
