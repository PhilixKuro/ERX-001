const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {open}=require('../P1S6R4-cdp.cjs');
const logdir=path.join(__dirname,'../../frappe-bench/logs');
const apiMode=process.argv.includes('--api');
const evidence=apiMode?'s8-ts020-return-api':'s8-ts020-return';
(async()=>{
 const c=await open('http://s8dev.localhost:6787');let initial;
 try{
  assert.equal(await c.evaluate('frappe.boot.sitename'),'s8dev.localhost');
  initial=await c.evaluate('frappe.boot.frappe_debug_demo');
  const lead=await c.evaluate(`frappe.xcall('frappe.client.insert',{doc:{doctype:'CRM Lead',first_name:'_FCT-TS020-RETURN-'+Date.now(),organization:'_FCT-TS020-RETURN-'+Date.now(),status:'New'}}).then(d=>d.name)`);
  const pending={lead,expected_deal_value:2088,expected_closure_date:'2026-01-14',save_as:'crm_return',refs:initial.refs,act:1,step:0,scene_date:'2026-01-07',return_route:'/desk'};
  await c.evaluate(`sessionStorage.setItem('frappe_debug_mode','rehearsal');sessionStorage.removeItem('frappe_debug_result');sessionStorage.removeItem('frappe_debug_pending')`);
  if(!apiMode)await c.evaluate(`sessionStorage.setItem('frappe_debug_pending',${JSON.stringify(JSON.stringify(pending))})`);
  await c.navigate(c.base+'/crm/leads/'+encodeURIComponent(lead));
  if(apiMode){
   await c.until('!!window.frappe_debug_crm && !!window.csrf_token');
   await c.evaluate(`sessionStorage.setItem('frappe_debug_pending',${JSON.stringify(JSON.stringify(pending))});frappe_debug_crm.page.read=async()=>({});frappe_debug_crm.run_pending().catch(error=>console.error(error));undefined`);
  }
  await c.until(`location.pathname.startsWith('/desk') && !!window.frappe?.boot?.frappe_debug_demo && !!window.frappe_debug?.demo`,45000);
  assert.equal(await c.evaluate('frappe.boot.sitename'),'s8dev.localhost');
  const result=await c.evaluate('JSON.parse(sessionStorage.getItem("frappe_debug_result"))');
  assert(!result.error,JSON.stringify(result));assert.equal(result.via,apiMode?'api':'ui');
  const progress=await c.evaluate('frappe.boot.frappe_debug_demo');
  assert.equal(progress.step,1);assert.equal(progress.refs.crm_return,result.name);
  assert.equal(progress.refs.sales_order,initial.refs.sales_order);
  await c.evaluate(`frappe_debug.demo.actions.open_doc({doctype:'CRM Deal',name:frappe.boot.frappe_debug_demo.refs.crm_return,timeout:30})`);
  const doc=await c.evaluate('cur_frm.doc');
  assert.equal(doc.name,result.name);assert.equal(doc.lead,lead);assert.equal(doc.expected_deal_value,2088);assert.equal(doc.expected_closure_date,pending.expected_closure_date);
  await c.screenshot(path.join(logdir,evidence+'.png'));
  fs.writeFileSync(path.join(logdir,evidence+'.json'),JSON.stringify({lead,result,progress,doc},null,2));
  console.log('PASS conversion, automatic Desk return and open_doc using persisted CRM ref',JSON.stringify({lead,result}));
 }catch(error){
  fs.writeFileSync(path.join(logdir,evidence+'-failure.json'),JSON.stringify({url:await c.evaluate('location.href'),body:await c.evaluate('document.body.innerText'),result:await c.evaluate('sessionStorage.getItem("frappe_debug_result")'),events:c.events.slice(-40)},null,2));
  await c.screenshot(path.join(logdir,evidence+'-failure.png'));throw error;
 }finally{
  try{if(initial){await c.navigate(c.base+'/desk');await c.until('!!window.frappe?.boot');assert.equal(await c.evaluate('frappe.boot.sitename'),'s8dev.localhost');await c.evaluate(`frappe.xcall('frappe_debug.demo.progress.save_progress',${JSON.stringify({act:initial.act||1,step:initial.step||0,refs:initial.refs,scene_date:initial.scene_date||'2026-01-07'})})`);await c.evaluate(`sessionStorage.removeItem('frappe_debug_mode');sessionStorage.removeItem('frappe_debug_pending')`);}}finally{await c.close();}
 }
})().catch(error=>{console.error(error);process.exitCode=1;});
