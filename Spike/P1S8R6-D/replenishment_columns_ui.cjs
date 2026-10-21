const { open } = require('../P1S6R4-cdp.cjs');
const path = require('node:path');
(async () => {
 const c = await open();
 try {
  await c.evaluate("frappe.set_route('List', 'Replenishment Suggestion')");
  await c.until("window.cur_list?.doctype === 'Replenishment Suggestion'");
  await c.until("Array.isArray(cur_list.columns) && cur_list.columns.length > 0");
  const list = JSON.parse(await c.evaluate(`JSON.stringify({
   site: frappe.boot.sitename,
   columns: cur_list.columns.map(c => c.df?.fieldname || c.type),
  })`));
  await c.evaluate("frappe.new_doc('Replenishment Suggestion')");
  await c.until("cur_frm?.doctype === 'Replenishment Suggestion' && cur_frm.is_new()");
  await c.until("!!cur_frm.fields_dict.basis?.grid && !!cur_frm.fields_dict.source_orders?.grid");
  const details = JSON.parse(await c.evaluate(`JSON.stringify({
   basis: cur_frm.fields_dict.basis.grid.visible_columns.map(([df]) => df.fieldname),
   sources: cur_frm.fields_dict.source_orders.grid.visible_columns.map(([df]) => df.fieldname),
   options: frappe.meta.get_docfield('Replenishment Basis Item', 'basis').options.split('\\n').map(value => __(value)),
  })`));
  if (details.basis.join(',') !== 'basis,value,note') throw Error('Basis columns mismatch: ' + details.basis);
  if (details.sources.join(',') !== 'sales_order,item_code,pending_qty') throw Error('Source order columns mismatch: ' + details.sources);
  if (details.options.length !== 23 || details.options.some(value => value.trim() === '' || /^[A-Za-z %.-]+$/.test(value))) throw Error('Basis options are not fully translated');
  await c.screenshot(path.join(__dirname, 'SL007-suggestion-details.png'));
  console.log(JSON.stringify({ ...list, ...details, screenshot: 'SL007-suggestion-details.png' }));
 } finally { await c.close(); }
})().catch(e => { console.error(e); process.exitCode = 1; });
