const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');

const logs = path.join(__dirname, '../../frappe-bench/logs');
const output = path.join(logs, 's8-ts023-preview-full-rehearsal.json');

(async () => {
  const c = await open('http://s8ts023preview.localhost:6787');
  try {
    assert.equal(await c.evaluate('frappe.boot.sitename'), 's8ts023preview.localhost');
    assert.equal(await c.evaluate('frappe.session.user'), 'Administrator');
    const baseline = await c.evaluate(`(async () => ({
      switch: await frappe.xcall('frappe_debug.demo.switch.switch_status'),
      snapshots: await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status'),
    }))()`);
    assert.deepEqual(baseline.snapshots.acts || {}, {});
    assert.equal(baseline.switch.db, baseline.snapshots.base_db);
    await c.evaluate(`(async()=>{
      const demo=frappe_debug.demo;
      const config=await frappe.xcall('frappe_debug.demo.config.get_demo_config');
      demo.validate(config); demo.config=config;
      const existing=await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status');
      const prepared=existing.work_db?{db:existing.work_db}:await frappe.xcall('frappe_debug.demo.workspace.prepare_work');
      const state={phase:'switch_work',act:1,status:'running',started:Date.now(),timings:[],logs:[],base_db:${JSON.stringify(baseline.switch.db)},work_db:prepared.db};
      sessionStorage.setItem('frappe_debug_mode','rehearsal');
      sessionStorage.setItem('frappe_debug_rehearsal',JSON.stringify(state));
      await demo.rehearsal._wait_clones(state);
      await demo.transit_to_db(prepared.db,{act:1,route:config.start_route});
    })().catch(error=>window.previewStartError=error.message);true`);
    await c.until("!!window.previewStartError || JSON.parse(sessionStorage.getItem('frappe_debug_rehearsal') || 'null')?.status === 'running'", 120000);
    if (await c.evaluate('window.previewStartError')) throw Error(await c.evaluate('window.previewStartError'));
    const deadline = Date.now() + 8 * 60 * 60 * 1000;
    let last = '';
    while (Date.now() < deadline) {
      await c.until('!!window.frappe?.boot?.sitename', 120000);
      assert.equal(await c.evaluate('frappe.boot.sitename'), 's8ts023preview.localhost');
      const state = await c.evaluate(`(async () => ({
        state: JSON.parse(sessionStorage.getItem('frappe_debug_rehearsal') || 'null'),
        db: (await frappe.xcall('frappe_debug.demo.switch.switch_status')).db,
        snapshots: await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status'),
        progress: await frappe.xcall('frappe_debug.demo.progress.get_progress'),
      }))()`);
      fs.writeFileSync(output, JSON.stringify({baseline, ...state, observed_at: new Date().toISOString()}, null, 2));
      const signature = `${state.state?.phase}:${state.state?.act}:${state.state?.status}:${state.state?.error || ''}`;
      if (signature !== last) {
        console.log(JSON.stringify({phase:state.state?.phase,act:state.state?.act,status:state.state?.status,db:state.db,work_state:state.snapshots.work_state,acts:Object.keys(state.snapshots.acts || {}).length,error:state.state?.error || null}));
        last = signature;
      }
      if (state.state?.status === 'failed' || state.state?.status === 'done') break;
      await c.pause(5000);
    }
    const final = JSON.parse(fs.readFileSync(output, 'utf8'));
    await c.screenshot(path.join(logs, 's8-ts023-preview-full-rehearsal.png'));
    if (final.state?.status !== 'done') throw Error(final.state?.error || '整场隔离彩排未在限定时间内完成');
    console.log('PASS isolated full rehearsal', JSON.stringify({total_seconds:final.state.total_seconds,timings:final.state.timings.length,registry:final.snapshots}));
  } finally { await c.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
