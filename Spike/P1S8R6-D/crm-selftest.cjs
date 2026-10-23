const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {open}=require('../P1S6R4-cdp.cjs');
const logdir=path.join(__dirname,'../../frappe-bench/logs');
const results=[];
(async()=>{
 const c=await open('http://s8dev.localhost:6787');
 try{
  assert.equal(await c.evaluate('frappe.boot.sitename'),'s8dev.localhost');
  const initial=await c.evaluate('frappe.boot.frappe_debug_demo');
  for(let i=0;i<10;i++){
   await c.navigate(c.base+'/desk');
   await c.until('!!window.frappe?.boot && !!window.frappe_debug?.demo');
   assert.equal(await c.evaluate('frappe.boot.sitename'),'s8dev.localhost');
   const lead=await c.evaluate(`frappe.xcall('frappe.client.insert',{doc:{doctype:'CRM Lead',first_name:'_FCT-TS020-${i}-'+Date.now(),organization:'_FCT-TS020-'+Date.now(),status:'New'}}).then(d=>d.name)`);
   const pending={lead,expected_deal_value:1000+i,expected_closure_date:'2026-01-14',save_as:'crm_selftest',refs:initial.refs||{},act:1,step:i,scene_date:'2026-01-07'};
   await c.evaluate(`sessionStorage.setItem('frappe_debug_mode','rehearsal');sessionStorage.removeItem('frappe_debug_result');sessionStorage.setItem('frappe_debug_pending',${JSON.stringify(JSON.stringify(pending))})`);
   await c.navigate(c.base+'/crm/leads/'+encodeURIComponent(lead));
   await c.until('!!sessionStorage.getItem("frappe_debug_result")',45000);
   const result=await c.evaluate('JSON.parse(sessionStorage.getItem("frappe_debug_result"))');
   if(result.error)throw Error(result.error);
   const docs=await c.evaluate(`Promise.all([fetch('/api/resource/CRM%20Deal/'+encodeURIComponent(${JSON.stringify(result.name)})).then(r=>r.json()).then(j=>j.data),fetch('/api/resource/CRM%20Lead/'+encodeURIComponent(${JSON.stringify(lead)})).then(r=>r.json()).then(j=>j.data)])`);
   assert.equal(docs[0].lead,lead);assert.equal(Number(docs[0].expected_deal_value),1000+i);assert.equal(docs[0].expected_closure_date,pending.expected_closure_date);assert.equal(docs[1].converted,1);
   results.push({i:i+1,lead,...result});console.log(JSON.stringify(results.at(-1)));
   fs.writeFileSync(path.join(logdir,'s8-ts020-conversions.json'),JSON.stringify(results,null,2));
   if(i===0)await c.screenshot(path.join(logdir,'s8-ts020-conversion.png'));
  }
  await c.navigate(c.base+'/desk');await c.until('!!window.frappe?.boot?.frappe_debug_demo');
  const after=await c.evaluate('frappe.boot.frappe_debug_demo');
  assert.equal(after.refs.crm_selftest,results.at(-1).name);assert.equal(after.step,10);
  assert.equal(after.refs.sales_order,initial.refs.sales_order);
  const sources=await c.evaluate(`(async()=>{const out={};for(const lang of ['zh','en']){const response=await fetch('/crm?_lang='+lang);const html=await response.text();out[lang]={status:response.status,language:new DOMParser().parseFromString(html,'text/html').documentElement.lang,driver:html.split('/assets/frappe_debug/js/demo/crm_driver.js').length-1,china:html.includes('id="china-ui-labels"')};}return out;})()`);
  for(const language of ['zh','en']){assert.equal(sources[language].status,200);assert.equal(sources[language].driver,1);assert.equal(sources[language].language,language);}assert.equal(sources.zh.china,true);assert.equal(sources.en.china,false);
  fs.writeFileSync(path.join(logdir,'s8-ts020-sources.json'),JSON.stringify({sources,after},null,2));
  await c.evaluate(`(async()=>{const p=${JSON.stringify(initial)};await frappe.xcall('frappe_debug.demo.progress.save_progress',{act:p.act||1,step:p.step||0,refs:p.refs,scene_date:p.scene_date||'2026-01-07'});sessionStorage.removeItem('frappe_debug_mode');})()`);
  console.log('PASS 10 conversions, persisted CRM refs across Desk, bilingual injection',JSON.stringify(sources));
 }catch(error){try{await c.screenshot(path.join(logdir,'s8-ts020-failure.png'));fs.writeFileSync(path.join(logdir,'s8-ts020-failure.json'),JSON.stringify({url:await c.evaluate('location.href'),body:await c.evaluate('document.body.innerText'),events:c.events.slice(-50)},null,2));}catch{}throw error;}
 finally{await c.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
