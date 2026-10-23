const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');
const logdir = path.join(__dirname, '../../frappe-bench/logs');
const fixture = JSON.parse(fs.readFileSync(path.join(logdir, 's8-ts022-fixture.json'), 'utf8'));
(async () => {
 const c = await open('http://s8dev.localhost:6787');
 const api = (method, args={}) => c.evaluate(`frappe.xcall(${JSON.stringify(method)},${JSON.stringify(args)})`);
 const evidence = {};
 try {
  await c.until('!!window.frappe_debug?.demo?.config');
  assert.equal(await c.evaluate('frappe.boot.sitename'),'s8dev.localhost');
  assert.equal(await c.evaluate('frappe.session.user'),'Administrator');
  const registry = await api('frappe_debug.demo.snapshot.snapshot_status');
  evidence.databases = Object.values(registry.acts).flatMap(copies=>Object.values(copies).map(copy=>copy.db));
  assert.equal(evidence.databases.length,12);
  assert(!Object.values(registry.acts).flatMap(Object.values).some(copy=>copy.state==='cloning'));
  assert.equal(registry.base_db,fixture.base_db);
  await c.evaluate('window.__ts022_departing=true');
  try {await c.evaluate('frappe_debug.demo.return_to_base()');} catch(error) {if(!/context|navigat/i.test(error.message))throw error;}
  await c.until('!window.__ts022_departing && !!window.frappe_debug?.demo?.config && !location.pathname.includes("/assets/")');
  assert.equal(await c.evaluate('frappe.boot.sitename'),'s8dev.localhost');
  assert.equal(await c.evaluate('frappe.session.user'),'Administrator');
  evidence.returned = await api('frappe_debug.demo.switch.switch_status');
  assert.deepEqual(evidence.returned,{db:fixture.base_db,user:'Administrator'});
  evidence.progress = await api('frappe_debug.demo.progress.get_progress');
  assert.deepEqual(evidence.progress,fixture.progress);
  evidence.counts = {};
  for(const dt of Object.keys(fixture.counts)) evidence.counts[dt]=await api('frappe.client.get_count',{doctype:dt});
  assert.deepEqual(evidence.counts,fixture.counts);
  evidence.cleanup = await api('frappe_debug.demo.snapshot.drop_snapshots');
  assert.equal(evidence.cleanup.dropped,12);
  evidence.registry = await api('frappe_debug.demo.snapshot.snapshot_status');
  assert.deepEqual(evidence.registry,{base_db:null,acts:{}});
  fs.writeFileSync(path.join(logdir,'s8-ts022-cleanup.json'),JSON.stringify(evidence,null,2));
  await c.screenshot(path.join(logdir,'s8-ts022-cleanup.png'));
  console.log('PASS returned through transit; original progress/counts preserved; 12 snapshots removed; registry empty');
 } finally {await c.close();}
})().catch(error=>{console.error(error.message);process.exitCode=1;});
