const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');

const logs = path.join(__dirname, '../../frappe-bench/logs');
const output = path.join(logs, 's8-ts023-full-rehearsal.json');

(async () => {
  const c = await open('http://s8dev.localhost:6787');
  try {
    assert.equal(await c.evaluate('frappe.boot.sitename'), 's8dev.localhost');
    assert.equal(await c.evaluate('frappe.session.user'), 'Administrator');
    const initial = await c.evaluate(`(async () => ({
      status: await frappe.xcall('frappe_debug.demo.switch.switch_status'),
      snapshots: await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status'),
      progress: await frappe.xcall('frappe_debug.demo.progress.get_progress'),
    }))()`);
    assert.deepEqual(initial.snapshots.acts || {}, {});
    assert.equal(initial.snapshots.work_db || null, null);
    await c.evaluate("frappe.set_route('demo-rehearsal')");
    await c.until("!!window.frappe_debug?.demo?.rehearsal && document.body.innerText.includes('开始整场预跑')");
    await c.evaluate(`document.querySelectorAll('button').forEach(button => {
      if (button.textContent.trim() === '开始整场预跑') button.click();
    })`);
    const deadline = Date.now() + 8 * 60 * 60 * 1000;
    let last = '';
    await c.until("!!window.frappe?.boot?.sitename", 120000);
    while (Date.now() < deadline) {
      await c.until("!!window.frappe?.boot?.sitename", 120000);
      const state = await c.evaluate(`(async () => ({
        state: JSON.parse(sessionStorage.getItem('frappe_debug_rehearsal') || 'null'),
        db: (await frappe.xcall('frappe_debug.demo.switch.switch_status')).db,
        snapshots: await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status'),
        progress: await frappe.xcall('frappe_debug.demo.progress.get_progress'),
      }))()`);
      fs.writeFileSync(output, JSON.stringify({initial, ...state, observed_at: new Date().toISOString()}, null, 2));
      const signature = `${state.state?.phase}:${state.state?.act}:${state.state?.status}:${state.state?.error || ''}`;
      if (signature !== last) {
        console.log(JSON.stringify({phase:state.state?.phase,act:state.state?.act,status:state.state?.status,db:state.db,work_state:state.snapshots.work_state,acts:Object.keys(state.snapshots.acts || {}).length,error:state.state?.error || null}));
        last = signature;
      }
      if (state.state?.status === 'failed' || state.state?.status === 'done') break;
      await c.pause(5000);
    }
    const final = JSON.parse(fs.readFileSync(output, 'utf8'));
    await c.screenshot(path.join(logs, 's8-ts023-full-rehearsal.png'));
    if (final.state?.status !== 'done') throw Error(final.state?.error || '预跑未在限定时间内完成');
    console.log('PASS full rehearsal', JSON.stringify({total_seconds:final.state.total_seconds,timings:final.state.timings.length,registry:final.snapshots}));
  } finally {
    await c.close();
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
