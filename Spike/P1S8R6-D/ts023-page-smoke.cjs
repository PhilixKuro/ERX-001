const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');

const logdir = path.join(__dirname, '../../frappe-bench/logs');

(async () => {
  const c = await open('http://s8dev.localhost:6787');
  try {
    assert.equal(await c.evaluate('frappe.boot.sitename'), 's8dev.localhost');
    assert.equal(await c.evaluate('frappe.session.user'), 'Administrator');
    await c.until('!!window.frappe_debug?.demo?.config');
    const before = await c.evaluate("Promise.all([frappe.xcall('frappe_debug.demo.switch.switch_status'),frappe.xcall('frappe_debug.demo.snapshot.snapshot_status')])");
    assert.deepEqual(before[1].acts || {}, {});
    assert.equal(before[1].work_db || null, null);
    await c.evaluate("frappe.set_route('demo-rehearsal')");
    await c.until("document.body.innerText.includes('场景、分段与幕状态') && document.body.innerText.includes('开始整场预跑')");
    const visible = await c.evaluate('document.body.innerText');
    assert.match(visible, /从当前幕续跑/);
    assert.match(visible, /回到演示前/);
    const detail = await c.evaluate("document.getElementById('frappe-debug-rehearsal-detail').textContent");
    assert.match(detail, /dates/);
    assert.match(detail, /segments/);
    assert.match(detail, /snapshots/);
    const after = await c.evaluate("frappe.xcall('frappe_debug.demo.switch.switch_status')");
    assert.deepEqual(after, before[0]);
    const evidence = {site:'s8dev.localhost',user:'Administrator',db:after.db,buttons:['开始整场预跑','从当前幕续跑','回到演示前','清理快照库'],registry:before[1],details:true,writesStarted:false};
    fs.writeFileSync(path.join(logdir, 's8-ts023-page-smoke.json'), JSON.stringify(evidence, null, 2));
    await c.screenshot(path.join(logdir, 's8-ts023-page-smoke.png'));
    console.log(JSON.stringify(evidence));
  } finally {
    await c.close();
  }
})().catch(error => {
  console.error(error.message);
  process.exitCode = 1;
});
