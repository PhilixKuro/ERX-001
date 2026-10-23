const fs=require('node:fs');
const path=require('node:path');
const assert=require('node:assert/strict');
const {open}=require('../P1S6R4-cdp.cjs');

(async()=>{
 const root=path.resolve(__dirname,'../..');
 const plan=JSON.parse(fs.readFileSync(path.join(root,'frappe-bench/sites/s8dev.localhost/private/frappe_debug/quality-plan.json'),'utf8'));
 const c=await open('http://s8dev.localhost:6787');
 try{
  assert.equal(await c.evaluate('frappe.boot.sitename'),'s8dev.localhost');
  assert.equal(await c.evaluate("frappe.session.user"),'Administrator');
  const site=await c.evaluate("frappe.xcall('frappe_debug.demo.switch.switch_status')");
  assert.ok(site.db.endsWith('_work'));
  const doc=await c.evaluate("frappe.xcall('frappe.client.get',{doctype:'Quality Inspection',name:'MAT-QA-2026-00884'})");
  const key=JSON.stringify([doc.report_date,doc.reference_type,doc.reference_name,doc.item_code]);
  const expected=plan.manifest[key]||null;
  console.log(JSON.stringify({db:site.db,doc:{name:doc.name,docstatus:doc.docstatus,report_date:doc.report_date,reference_type:doc.reference_type,reference_name:doc.reference_name,item_code:doc.item_code,readings:doc.readings?.map(row=>({specification:row.specification,min_value:row.min_value,max_value:row.max_value,values:[1,2,3,4,5].map(i=>row[`reading_${i}`])}))},key,expected,manifest_size:Object.keys(plan.manifest).length},null,2));
 }finally{await c.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
