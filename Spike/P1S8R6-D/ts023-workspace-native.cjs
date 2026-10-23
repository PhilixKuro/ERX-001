const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');

const logdir = path.join(__dirname, '../../frappe-bench/logs');
const doctypeNames = ['ToDo', 'Sales Order', 'Purchase Order', 'CRM Lead'];

(async () => {
  const c = await open('http://s8dev.localhost:6787');
  const api = (method, args = {}) => c.evaluate(`fetch('/api/method/${method}', {
    method: 'POST', credentials: 'same-origin',
    headers: {'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': sessionStorage.getItem('frappe_debug_csrf') || window.frappe?.csrf_token || ''},
    body: JSON.stringify(${JSON.stringify(args)}),
  }).then(async response => {
    const data = await response.json();
    if (!response.ok || data.exc) throw Error(data.exception || data._server_messages || ('HTTP ' + response.status));
    return data.message;
  })`);
  const evidence = {site: 's8dev.localhost', user: null};
  let baseDb;
  let prepared = false;
  try {
    assert.equal(await c.evaluate('frappe.boot.sitename'), 's8dev.localhost');
    evidence.user = await c.evaluate('frappe.session.user');
    assert.equal(evidence.user, 'Administrator');

    const beforeStatus = await api('frappe_debug.demo.switch.switch_status');
    baseDb = beforeStatus.db;
    evidence.base_db = baseDb;
    assert.deepEqual(await api('frappe_debug.demo.snapshot.snapshot_status'), {base_db: null, acts: {}});
    evidence.progress_before = await api('frappe_debug.demo.progress.get_progress');
    evidence.counts_before = {};
    for (const doctype of doctypeNames) {
      evidence.counts_before[doctype] = await api('frappe.client.get_count', {doctype});
    }

    evidence.prepare = await api('frappe_debug.demo.workspace.prepare_work');
    prepared = true;
    assert.equal(evidence.prepare.db, `${baseDb}_work`);
    assert.equal(evidence.prepare.status, 'cloning');

    const cloneDeadline = Date.now() + 10 * 60 * 1000;
    while (Date.now() < cloneDeadline) {
      evidence.registry_during_clone = await api('frappe_debug.demo.snapshot.snapshot_status');
      if (evidence.registry_during_clone.work_state === 'ready') break;
      if (evidence.registry_during_clone.work_state === 'failed') throw Error('工作库克隆失败');
      await new Promise(resolve => setTimeout(resolve, 2000));
    }
    assert.equal(evidence.registry_during_clone.work_state, 'ready', 'work clone did not finish within 10 minutes');

    const transit = async (db, returning) => {
      const purpose = returning ? 'return' : 'switch_db';
      const payload = {
        act: 1,
        purpose,
        route: '/desk',
        db,
        return_to_base: returning,
        csrf: await c.evaluate('frappe.csrf_token'),
      };
      await c.evaluate(`(() => {
        const payload = ${JSON.stringify(payload)};
        sessionStorage.setItem('frappe_debug_transit', JSON.stringify(payload));
        sessionStorage.setItem('frappe_debug_csrf', payload.csrf);
        location.assign('/assets/frappe_debug/demo/transit.html?act=1&purpose=${purpose}');
      })()`);
      await c.until("window.frappe?.boot?.sitename === 's8dev.localhost' && window.frappe?.session?.user === 'Administrator' && location.pathname.startsWith('/desk')", 120000);
      const status = await api('frappe_debug.demo.switch.switch_status');
      assert.deepEqual(status, {db, user: 'Administrator'});
      return status;
    };

    evidence.to_work = await transit(evidence.prepare.db, false);
    evidence.progress_in_work = await api('frappe_debug.demo.progress.get_progress');
    assert.deepEqual(evidence.progress_in_work, evidence.progress_before);
    evidence.counts_in_work = {};
    for (const doctype of doctypeNames) {
      evidence.counts_in_work[doctype] = await api('frappe.client.get_count', {doctype});
    }
    assert.deepEqual(evidence.counts_in_work, evidence.counts_before);

    evidence.to_base = await transit(baseDb, true);
    evidence.progress_after_return = await api('frappe_debug.demo.progress.get_progress');
    assert.deepEqual(evidence.progress_after_return, evidence.progress_before);
    evidence.cleanup = await api('frappe_debug.demo.snapshot.drop_snapshots');
    assert.equal(evidence.cleanup.dropped, 1);
    evidence.registry_after_cleanup = await api('frappe_debug.demo.snapshot.snapshot_status');
    assert.deepEqual(evidence.registry_after_cleanup, {base_db: null, acts: {}});
    evidence.progress_after_cleanup = await api('frappe_debug.demo.progress.get_progress');
    assert.deepEqual(evidence.progress_after_cleanup, evidence.progress_before);
    fs.writeFileSync(path.join(logdir, 's8-ts023-workspace-native.json'), JSON.stringify(evidence, null, 2));
    await c.screenshot(path.join(logdir, 's8-ts023-workspace-native.png'));
    console.log('PASS native work clone, transit to work and base, protected cleanup, unchanged base progress and counts');
  } catch (error) {
    evidence.error = error.message;
    try {
      evidence.failure_status = await api('frappe_debug.demo.switch.switch_status');
      evidence.failure_registry = await api('frappe_debug.demo.snapshot.snapshot_status');
    } catch (cleanupError) {
      evidence.cleanup_error = cleanupError.message;
    }
    fs.writeFileSync(path.join(logdir, 's8-ts023-workspace-native-failure.json'), JSON.stringify(evidence, null, 2));
    throw error;
  } finally {
    if (prepared) {
      try {
        const status = await api('frappe_debug.demo.switch.switch_status');
        if (status.db !== baseDb) await api('frappe_debug.demo.switch.switch_to_db', {db_name: baseDb});
        const registry = await api('frappe_debug.demo.snapshot.snapshot_status');
        if (registry.base_db && registry.work_db) await api('frappe_debug.demo.snapshot.drop_snapshots');
      } finally {
        await c.close();
      }
    } else {
      await c.close();
    }
  }
})().catch(error => {
  console.error(error);
  process.exitCode = 1;
});
