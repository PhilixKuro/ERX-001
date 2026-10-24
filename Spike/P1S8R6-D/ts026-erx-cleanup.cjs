const assert = require('node:assert/strict');
const { open } = require('../P1S6R4-cdp.cjs');

(async () => {
  const c = await open('http://erx.localhost:8000');
  const api = (method, args = {}) => c.evaluate('frappe.xcall(' + JSON.stringify(method) + ', ' + JSON.stringify(args) + ')');
  try {
    await c.until('!!window.frappe?.xcall && frappe.session.user === "Administrator"', 60000);
    assert.equal(await c.evaluate('frappe.boot.sitename'), 'erx.localhost');
    assert.equal(await c.evaluate('frappe.session.user'), 'Administrator');
    const registry = await api('frappe_debug.demo.snapshot.snapshot_status');
    const base = registry.base_db;
    assert(base && registry.acts && Object.keys(registry.acts).length === 9);
    const starting = await api('frappe_debug.demo.switch.switch_status');
    if (starting.db !== base) {
      await c.evaluate('window.__ts026_returning = true');
      try { await c.evaluate('frappe_debug.demo.return_to_base()'); }
      catch (error) { if (!/context|navigat/i.test(error.message)) throw error; }
      await c.until('!window.__ts026_returning && !!window.frappe_debug?.demo?.config && !location.pathname.includes("/assets/")', 120000);
    } else if (!(await c.evaluate('!!window.frappe_debug?.demo?.config'))) {
      await c.navigate('http://erx.localhost:8000/desk');
      await c.until('!!window.frappe?.xcall && frappe.session.user === "Administrator"', 60000);
    }
    const status = await api('frappe_debug.demo.switch.switch_status');
    assert.equal(status.db, base);
    assert.equal(status.user, 'Administrator');
    const before = {};
    for (const doctype of ['Company','Translation','GL Entry','Stock Ledger Entry','CRM Lead','Sales Order','Work Order','Scenario Event']) {
      before[doctype] = await api('frappe.client.get_count', {doctype});
    }
    assert.deepEqual(before, {Company:1, Translation:0, 'GL Entry':0, 'Stock Ledger Entry':0, 'CRM Lead':0, 'Sales Order':0, 'Work Order':0, 'Scenario Event':0});
    const cleanup = await api('frappe_debug.demo.snapshot.drop_snapshots');
    assert.equal(cleanup.dropped, 28);
    const empty = await api('frappe_debug.demo.snapshot.snapshot_status');
    assert.deepEqual(empty, {base_db:null, acts:{}});
    const after = {};
    for (const doctype of Object.keys(before)) after[doctype] = await api('frappe.client.get_count', {doctype});
    assert.deepEqual(after, before);
    console.log('PASS returned to clean base and dropped snapshots', JSON.stringify({status, cleanup, registry:empty, counts:after}));
  } finally { await c.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
