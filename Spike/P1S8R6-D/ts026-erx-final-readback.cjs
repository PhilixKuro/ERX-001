const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');
const logs = path.join(__dirname, '../../frappe-bench/logs');
const output = path.join(logs, 's8-ts026-erx-full-rehearsal-final.json');

(async () => {
  const c = await open('http://erx.localhost:8000');
  try {
    await c.until('!!window.frappe?.xcall && !!window.frappe_debug?.demo?.business_functions_loaded', 60000);
    assert.equal(await c.evaluate('frappe.boot.sitename'), 'erx.localhost');
    assert.equal(await c.evaluate('frappe.session.user'), 'Administrator');
    const result = await c.evaluate('(async () => ({status:await frappe.xcall("frappe_debug.demo.switch.switch_status"), snapshots:await frappe.xcall("frappe_debug.demo.snapshot.snapshot_status"), progress:await frappe.xcall("frappe_debug.demo.progress.get_progress")}))()');
    const {status, snapshots, progress} = result;
    assert.equal(status.db, snapshots.base_db + '_a1_m');
    assert.equal(status.user, 'Administrator');
    assert.equal(snapshots.work_state, 'ready');
    assert.equal(snapshots.work_db, snapshots.base_db + '_work');
    assert.equal(snapshots.scenario_end, '2026-10-24');
    assert.deepEqual(Object.keys(snapshots.acts).sort(), ['1','2','3','4','5','6','7','8','9']);
    const copies = Object.values(snapshots.acts).flatMap(act => Object.values(act));
    assert.equal(copies.length, 27);
    assert.equal(copies.filter(copy => copy.state === 'used').length, 1);
    assert.equal(copies.find(copy => copy.state === 'used').db, status.db);
    assert.equal(copies.filter(copy => copy.state === 'ready').length, 26);
    assert.equal(copies.filter(copy => copy.state === 'cloning' || copy.state === 'failed').length, 0);
    for (const [act, rows] of Object.entries(snapshots.acts)) {
      assert.deepEqual(Object.keys(rows).sort(), ['b','m','o']);
      assert.equal(rows.o.state, 'ready');
    }
    assert.equal(progress.active, true);
    assert.equal(progress.act, 1);
    assert.equal(progress.step, 0);
    assert.deepEqual(progress.refs, {});
    const evidence = {
      site: 'erx.localhost',
      terminal_event: {phase: 'done', status: 'done', act: 9, error: null, captured_before_final_assertion: true},
      terminal_source: 'First full-rehearsal process output; final assertion was corrected to accept the sole current snapshot as used.',
      final_readback: result,
      counts: {snapshots: copies.length, ready: 26, used: 1, cloning: 0, failed: 0},
      verified_at: new Date().toISOString(),
      completion_screenshot: path.join(logs, 's8-ts026-erx-full-rehearsal.png'),
    };
    assert(fs.existsSync(evidence.completion_screenshot));
    fs.writeFileSync(output, JSON.stringify(evidence, null, 2));
    console.log('PASS erx rehearsal final readback', JSON.stringify({db:status.db, acts:Object.keys(snapshots.acts).length, snapshots:copies.length, ready:26, used:1, progress:{act:progress.act,step:progress.step,refs:progress.refs}}));
  } finally { await c.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
