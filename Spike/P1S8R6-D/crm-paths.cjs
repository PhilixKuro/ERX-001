const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {open}=require('../P1S6R4-cdp.cjs');
const logdir=path.join(__dirname,'../../frappe-bench/logs');
(async()=>{
 const c=await open('http://s8dev.localhost:6787');
 try{
  assert.equal(await c.evaluate('frappe.boot.sitename'),'s8dev.localhost');
  await c.evaluate(`sessionStorage.removeItem('frappe_debug_pending');sessionStorage.removeItem('frappe_debug_mode')`);
  const sources=await c.evaluate(`(async()=>{const result={};for(const lang of ['zh','en']){const response=await fetch('/crm?_lang='+lang);const html=await response.text();result[lang]={status:response.status,language:new DOMParser().parseFromString(html,'text/html').documentElement.lang,driver:html.split('/assets/frappe_debug/js/demo/crm_driver.js').length-1,china:html.includes('id="china-ui-labels"')};}return result;})()`);
  for(const lang of ['zh','en']){assert.equal(sources[lang].status,200);assert.equal(sources[lang].driver,1);assert.equal(sources[lang].language,lang);}assert(sources.zh.china);assert(!sources.en.china);
  fs.writeFileSync(path.join(logdir,'s8-ts020-sources-verified.json'),JSON.stringify(sources,null,2));
  const lead=await c.evaluate(`frappe.xcall('frappe.client.insert',{doc:{doctype:'CRM Lead',first_name:'_FCT-TS020-API-'+Date.now(),organization:'_FCT-TS020-API-'+Date.now(),status:'New'}}).then(d=>d.name)`);
  await c.navigate(c.base+'/crm/leads/'+encodeURIComponent(lead));
  await c.until('!!window.frappe_debug_crm && !!window.csrf_token');
  const pending={lead,expected_deal_value:2077,expected_closure_date:'2026-01-14'};
  const result=await c.evaluate(`(async()=>{const result=await frappe_debug_crm.convert(${JSON.stringify(pending)},{...frappe_debug_crm.page,read:async()=>({})});await frappe_debug_crm.page.navigate_deal(result.name);return result;})()`);
  assert.equal(result.via,'api');
  const doc=await c.evaluate(`fetch('/api/resource/CRM%20Deal/'+encodeURIComponent(${JSON.stringify(result.name)})).then(r=>r.json()).then(j=>j.data)`);
  assert.equal(doc.lead,lead);assert.equal(doc.expected_deal_value,2077);assert.equal(doc.expected_closure_date,'2026-01-14');
  await c.screenshot(path.join(logdir,'s8-ts020-api.png'));
  fs.writeFileSync(path.join(logdir,'s8-ts020-api.json'),JSON.stringify({lead,result,doc},null,2));
  console.log('PASS actual zh/en pages and real modal-close/API fallback',JSON.stringify({sources,lead,result}));
 }catch(error){try{fs.writeFileSync(path.join(logdir,'s8-ts020-paths-failure.json'),JSON.stringify({body:await c.evaluate('document.body.innerText'),url:await c.evaluate('location.href')},null,2));await c.screenshot(path.join(logdir,'s8-ts020-paths-failure.png'));}catch{}throw error;}finally{await c.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
