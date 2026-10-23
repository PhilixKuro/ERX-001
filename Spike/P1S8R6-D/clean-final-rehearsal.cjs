const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {open}=require('../P1S6R4-cdp.cjs');
(async()=>{const c=await open('http://s8dev.localhost:6787');try{
 assert.equal(await c.evaluate('frappe.boot.sitename'),'s8dev.localhost');
 assert.equal(await c.evaluate('frappe.session.user'),'Administrator');
 await c.until('!!window.frappe_debug?.demo?.business_functions_loaded',60000);
 await c.evaluate('frappe_debug.demo.start().then(()=>frappe_debug.demo.return_to_base());true');
 await c.pause(2000);
 await c.until("!!window.frappe_debug?.demo?.business_functions_loaded && location.pathname==='/desk/company'",60000);
 const before=await c.evaluate(`(async()=>({status:await frappe.xcall('frappe_debug.demo.switch.switch_status'),registry:await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status'),progress:await frappe.xcall('frappe_debug.demo.progress.get_progress')}))()`);
 assert.equal(before.status.db,before.registry.base_db);
 await c.evaluate("window.__s8Cleanup={};frappe.xcall('frappe_debug.demo.snapshot.drop_snapshots').then(result=>window.__s8Cleanup={result}).catch(error=>window.__s8Cleanup={error:error.message});true");
 const deadline=Date.now()+20*60*1000;
 let cleanup;
 while(Date.now()<deadline){
  cleanup=await c.evaluate('window.__s8Cleanup');
  if(cleanup.error)throw Error(cleanup.error);
  if(Object.hasOwn(cleanup,'result'))break;
  await c.pause(1000);
 }
 assert.ok(Object.hasOwn(cleanup,'result'),'cleanup timed out');
 const dropped=cleanup.result;
 const after=await c.evaluate(`(async()=>({status:await frappe.xcall('frappe_debug.demo.switch.switch_status'),registry:await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status'),progress:await frappe.xcall('frappe_debug.demo.progress.get_progress')}))()`);
 assert.deepEqual(after.registry.acts,{});assert.equal(after.registry.work_db||null,null);
 assert.deepEqual(after.progress,before.progress);assert.equal(after.status.db,before.status.db);
 fs.writeFileSync(path.join(__dirname,'../../frappe-bench/logs/s8-final-cleanup.json'),JSON.stringify({before,dropped,after},null,2));
 console.log(JSON.stringify({base:after.status.db,dropped,progress:after.progress}));
}finally{await c.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
