const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');

const logdir = path.join(__dirname, '../../frappe-bench/logs');
const baseDb = process.argv[2];
assert(baseDb && /^[A-Za-z0-9_]+$/.test(baseDb));

(async () => {
  const c = await open('http://s8dev.localhost:6787');
  const results = [];
  try {
    assert.equal(await c.evaluate('frappe.boot.sitename'), 's8dev.localhost');
    assert.equal(await c.evaluate('frappe.session.user'), 'Administrator');
    const initial = await c.evaluate("frappe.xcall('frappe_debug.demo.switch.switch_status')");
    assert.equal(initial.db, baseDb);
    assert.equal(initial.user, 'Administrator');

    const original = `${baseDb}_a1_o`;
    const originalRejected = await c.evaluate(`frappe.xcall('frappe_debug.demo.switch.switch_to_db',{db_name:${JSON.stringify(original)}}).then(()=>false,()=>true)`);
    assert.equal(originalRejected, true, 'original snapshot must never be a switch target');
    results.push({check: 'original_rejected', passed: originalRejected});

    const switched = await c.evaluate(`frappe.xcall('frappe_debug.demo.switch.switch_to_db',{db_name:${JSON.stringify(`${baseDb}_a1_m`)}})`);
    assert.equal(switched.status, 'switched');
    const afterSwitch = await c.evaluate("frappe.xcall('frappe_debug.demo.switch.switch_status')");
    assert.deepEqual(afterSwitch, {db: `${baseDb}_a1_m`, user: 'Administrator'});
    results.push({check: 'session_copied_to_main', ...afterSwitch});

    const cleanupBlocked = await c.evaluate("frappe.xcall('frappe_debug.demo.snapshot.drop_snapshots').then(()=>false,()=>true)");
    assert.equal(cleanupBlocked, true, 'cleanup must refuse while connected to a snapshot database');
    results.push({check: 'cleanup_blocked_on_snapshot', passed: cleanupBlocked});

    const returned = await c.evaluate(`frappe.xcall('frappe_debug.demo.switch.switch_to_db',{db_name:${JSON.stringify(baseDb)}})`);
    assert.equal(returned.status, 'switched');
    const afterReturn = await c.evaluate("frappe.xcall('frappe_debug.demo.switch.switch_status')");
    assert.deepEqual(afterReturn, {db: baseDb, user: 'Administrator'});
    results.push({check: 'returned_to_base', ...afterReturn});

    const cleanup = await c.evaluate("frappe.xcall('frappe_debug.demo.snapshot.drop_snapshots')");
    assert.equal(cleanup.dropped, 3);
    const empty = await c.evaluate("frappe.xcall('frappe_debug.demo.snapshot.snapshot_status')");
    assert.deepEqual(empty, {base_db: null, acts: {}});
    results.push({check: 'snapshots_cleaned', cleanup, registry: empty});
    fs.writeFileSync(path.join(logdir, 's8-ts021-native.json'), JSON.stringify(results, null, 2));
    await c.screenshot(path.join(logdir, 's8-ts021-native.png'));
    console.log('PASS TS021 native snapshot, protected switch, session carry, return and cleanup', JSON.stringify(results));
  } catch (error) {
    fs.writeFileSync(path.join(logdir, 's8-ts021-native-failure.json'), JSON.stringify({
      error: error.message,
      state: await c.evaluate(`({site:frappe.boot.sitename,user:frappe.session.user,url:location.href})`),
      results,
    }, null, 2));
    throw error;
  } finally {
    try {
      const status = await c.evaluate("frappe.xcall('frappe_debug.demo.switch.switch_status')");
      if (status.db !== baseDb) {
        await c.evaluate(`frappe.xcall('frappe_debug.demo.switch.switch_to_db',{db_name:${JSON.stringify(baseDb)}})`);
      }
    } finally {
      await c.close();
    }
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
