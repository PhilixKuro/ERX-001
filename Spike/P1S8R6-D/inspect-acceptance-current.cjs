const {open}=require('../P1S6R4-cdp.cjs');
const fs=require('node:fs');
const acceptance=JSON.parse(fs.readFileSync(require('node:path').join(__dirname,'../../frappe-bench/logs/s8-rehearsal-acceptance.json'),'utf8'));

(async()=>{
 const c=await open('http://s8dev.localhost:6787');
 try {
  const state=await c.evaluate(`(async()=>{const rehearsal=JSON.parse(sessionStorage.getItem('frappe_debug_rehearsal')||'null');return {site:frappe.boot.sitename,user:frappe.session.user,route:location.pathname,segments:(await frappe.xcall('frappe_debug.demo.config.get_demo_config')).segments,scripts:[...document.scripts].map(s=>s.src).filter(x=>x.includes('frappe_debug')),functionsLoaded:frappe_debug?.demo?.business_functions_loaded,functionNames:Object.keys(frappe_debug?.demo?.functions||{}),generation:await frappe.xcall('frappe_debug.scenario.runner.generate_status',{job_id:${JSON.stringify(acceptance.state.job_id)}}),db:await frappe.xcall('frappe_debug.demo.switch.switch_status'),snapshots:await frappe.xcall('frappe_debug.demo.snapshot.snapshot_status'),progress:await frappe.xcall('frappe_debug.demo.progress.get_progress'),body:document.body.innerText.slice(-1600),alerts:[...document.querySelectorAll('.msgprint,.alert')].map(x=>x.innerText).filter(Boolean)}})()`);
  console.log(JSON.stringify(state,null,2));
  await c.navigate('http://s8dev.localhost:6787/desk/sales-order/SAL-ORD-2026-00085');
  await c.until('!!window.cur_frm?.doc?.name',30000);
  const form=await c.evaluate(`(()=>({site:frappe.boot.sitename,user:frappe.session.user,route:location.pathname,doctype:cur_frm.doctype,name:cur_frm.doc.name,docstatus:cur_frm.doc.docstatus,dirty:cur_frm.is_dirty(),doc:cur_frm.doc,alerts:[...document.querySelectorAll('.msgprint,.alert')].map(x=>x.innerText).filter(Boolean),dialogs:window.jQuery('.modal:visible').toArray().map(x=>x.innerText)}))()`);
  console.log(JSON.stringify(form,null,2));
 } finally { await c.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});
