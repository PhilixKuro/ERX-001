const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');
const logdir=path.join(__dirname,'../../frappe-bench/logs');
const fixture=JSON.parse(fs.readFileSync(path.join(logdir,'s8-ts019-fixture.json'),'utf8'));
const records=[];
const resume=process.argv.includes('--resume');

(async () => {
 const c = await open('http://s8dev.localhost:6787');
 try {
  assert.equal(await c.evaluate('frappe.boot.sitename'), 's8dev.localhost');
  await c.until('!!window.frappe_debug?.demo && (!frappe.boot.frappe_debug_demo.active || !!frappe_debug.demo.config)');
  await c.evaluate(`(async()=>{
   const d=frappe_debug.demo;
   d.register('selftest_clear_items',async()=>{cur_frm.clear_table('items');cur_frm.refresh_field('items');});
   d.register('selftest_check_dates',async(ctx,args)=>{
    const f=ctx.frm(),field=f.doctype==='Sales Order'?'transaction_date':'posting_date';
    if(f.doc[field]!==ctx.scene_date)throw Error(args.kind+': date '+f.doc[field]);
    if(f.fields_dict.set_posting_time&&f.doc.set_posting_time!==1)throw Error('posting flag');
    return {kind:args.kind,date:f.doc[field],flag:f.doc.set_posting_time,name:f.doc.name};
   });
   d.progress=${resume ? 'frappe.boot.frappe_debug_demo' : '{active:false,act:0,step:0,refs:{}}'};
   sessionStorage.setItem('frappe_debug_mode','rehearsal');
   await d.start(${JSON.stringify(fixture.selftest)});
   window.__acceptance=[];
   const original=d.run_step;
   d.run_step=async(...args)=>{
    const result=await original(...args);
    const p=await frappe.db.get_doc('Demo Progress','Demo Progress');
    if(p.act!==d.progress.act||p.step!==d.progress.step)throw Error('persisted progress mismatch');
    window.__acceptance.push({act:p.act,step:p.step,action:result.action,refs:typeof p.refs==='string'?JSON.parse(p.refs):p.refs,route:frappe.get_route(),doctype:window.cur_frm?.doctype,date:cur_frm?.doc?.posting_date||cur_frm?.doc?.transaction_date});
    return result;
   };
  })()`);
  const first=await c.evaluate('frappe_debug.demo.progress.step');
  if(first)records.push(...JSON.parse(fs.readFileSync(path.join(logdir,'s8-ts019-native-actions.json'),'utf8')).filter(r=>r.step<=first));
  if(process.argv.includes('--rehearsal')){
   await c.evaluate('frappe_debug.demo.next()');
   records.push(...await c.evaluate('window.__acceptance'));
   fs.writeFileSync(path.join(logdir,'s8-ts019-native-actions.json'),JSON.stringify(records,null,2));
  }else for(let i=first;i<fixture.selftest.acts[0].steps.length;i++){
   const step=fixture.selftest.acts[0].steps[i];
   console.log('STEP',i+1,step.action,step.doctype||step.field||step.fn||step.button||'');
   await c.evaluate(`frappe_debug.demo.run_step(1,${i})`);
   records.push(await c.evaluate('window.__acceptance.at(-1)'));
   fs.writeFileSync(path.join(logdir,'s8-ts019-native-actions.json'),JSON.stringify(records,null,2));
  }
  assert.equal(new Set(records.map(r=>r.action)).size,13);
  const report=await c.evaluate(`({filters:frappe.query_report.get_filter_values(),state:frappe.query_report.last_ajax?.state(),rows:frappe.query_report.data?.length,messages:[...document.querySelectorAll('.modal.show .modal-body')].map(x=>x.textContent)})`);
  assert.equal(report.filters.from_date,fixture.selftest.dates.D1);assert.equal(report.state,'resolved');assert.equal(report.messages.length,0);
  fs.writeFileSync(path.join(logdir,'s8-ts019-report.json'),JSON.stringify(report,null,2));
  const saved=await c.evaluate(`(async()=>{const r=frappe_debug.demo.progress.refs; const result={};for(const [key,dt] of Object.entries({sales_order:'Sales Order',purchase_order:'Purchase Order',purchase_receipt:'Purchase Receipt',payment_entry:'Payment Entry'})){const doc=await frappe.db.get_doc(dt,r[key]);result[key]={name:doc.name,date:doc.posting_date||doc.transaction_date,flag:doc.set_posting_time,docstatus:doc.docstatus};}return result;})()`);
  for(const [key,doc] of Object.entries(saved)){assert.equal(doc.date,fixture.selftest.dates.D1,key);if(key==='purchase_receipt')assert.equal(doc.flag,1,key);}
  fs.writeFileSync(path.join(logdir,'s8-ts019-saved-docs.json'),JSON.stringify(saved,null,2));
  await c.screenshot(path.join(logdir,'s8-ts019-native-actions.png'));
  console.log('PASS 13 actions, progress after each step, saved dates',JSON.stringify(saved));
 } catch(error){
  await c.pause(500);
  const failures=[];for(const e of c.events.filter(e=>e.method==='Network.responseReceived'&&e.params.response.status>=400&&e.params.response.url.includes('/api/'))){try{failures.push({url:e.params.response.url,...await c.send('Network.getResponseBody',{requestId:e.params.requestId})});}catch{}}
  fs.writeFileSync(path.join(logdir,'s8-ts019-http-errors.json'),JSON.stringify(failures,null,2));
  try{const state=await c.evaluate(`({route:frappe.get_route(),doc:window.cur_frm?.doc,dialog:window.cur_dialog?.$wrapper?.text(),messages:[...document.querySelectorAll('.modal-body,.msgprint')].map(x=>x.textContent),error:window.frappe_debug?.demo?.error?.message})`);fs.writeFileSync(path.join(logdir,'s8-ts019-failure.json'),JSON.stringify({state,events:c.events.filter(e=>e.method==='Runtime.exceptionThrown'||e.method==='Runtime.consoleAPICalled'||e.method==='Network.responseReceived').slice(-35)},null,2));console.error('STATE',JSON.stringify(state));await c.screenshot(path.join(logdir,'s8-ts019-failure.png'));}catch{}
  throw error;
 } finally {await c.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
