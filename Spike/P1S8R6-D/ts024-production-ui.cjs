const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');
const logs = path.join(__dirname, '../../frappe-bench/logs');
const fixture = JSON.parse(fs.readFileSync(path.join(logs, 's8-ts024-browser-fixture.json'), 'utf8'));
(async () => {
  const c = await open('http://s8dev.localhost:6787');
  try {
    assert.equal(await c.evaluate('frappe.boot.sitename'), 's8dev.localhost');
    await c.until('!!window.frappe_debug?.demo?.functions?.complete_job_card');
    await c.evaluate(`(async () => {
      const d = frappe_debug.demo;
      d.config = await frappe.xcall('frappe_debug.demo.config.get_demo_config');
      await d.actions.open_doc({doctype: 'Job Card', name: ${JSON.stringify(fixture.card_names[1])}});
      window.__production = {state: 'running'};
      d.functions.report_remaining_job_cards({...d.context(), refs: {so1: ${JSON.stringify(fixture.order)}}, scene_date: ${JSON.stringify(fixture.scene_date)}}, {order_ref:'so1'})
        .then(() => window.__production={state:'done',doc:cur_frm.doc})
        .catch(error => window.__production={state:'failed',error:String(error),doc:cur_frm.doc});
    })()`);
    await c.until('__production.state !== "running"', 120000);
    const result = await c.evaluate('__production');
    fs.writeFileSync(path.join(logs, 's8-ts024-production-ui.json'), JSON.stringify(result,null,2));
    await c.screenshot(path.join(logs, 's8-ts024-production-ui.png'));
    assert.equal(result.state, 'done', result.error);
    assert.equal(result.doc.docstatus, 1);
    assert.equal(result.doc.total_completed_qty, 1199.299);
    assert.equal(result.doc.process_loss_qty, 0);
    assert.ok(result.doc.time_logs.every(row => row.from_time.startsWith(fixture.scene_date) && row.to_time.startsWith(fixture.scene_date)));
    console.log('PASS', JSON.stringify({name:result.doc.name,qty:result.doc.total_completed_qty,loss:result.doc.process_loss_qty,time_logs:result.doc.time_logs}));
  } finally { await c.close(); }
})().catch(error => {console.error(error);process.exitCode=1;});
