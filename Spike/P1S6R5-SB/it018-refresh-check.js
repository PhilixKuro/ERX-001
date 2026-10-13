// R5 IT-018：P1S6R4-refresh-check.js 的副本，只改输入输出路径，免得覆盖 R4 留档
const fs=require('node:fs');
const assert=require('node:assert/strict');
const {execFile}=require('node:child_process');
const {promisify}=require('node:util');
const {open}=require('../P1S6R4-cdp.cjs');
const exec=promisify(execFile);
const mode=process.argv[2]||'bom';
const state=JSON.parse(fs.readFileSync('Spike/P1S6R5-SB/it018/part3-state.json','utf8'));
const file=`Spike/P1S6R5-SB/it018/refresh-${mode}.json`;
const report={mode,steps:[]};
const save=()=>fs.writeFileSync(file,JSON.stringify(report,null,2));

(async()=>{
 const c=await open(mode==='tax'?'http://erx.localhost:8000':undefined);
 try{
  report.browser=c.browser;
  await c.until('frappe.realtime.socket?.connected');
  const {stdout}=await exec('docker',['exec','-u','frappe','-w','/workspace/frappe-bench','erx001-frappe-1',
   '/home/frappe/.local/bin/bench','--site',mode==='tax'?'erx.localhost':'test.localhost','execute','frappe_china.realtime_check.run','--kwargs','{"timeout":10}']);
  report.realtime=stdout;assert.match(stdout,/"ok":\s*true/);save();
  // Dismiss only the connectivity-check alert before taking UI evidence.
  await c.evaluate(`document.querySelectorAll('.alert').forEach(e=>e.remove());true`);
  if(mode==='bom'){
   await c.evaluate(`frappe.new_doc('BOM');true`);
   await c.until(`cur_frm?.doctype==='BOM'&&cur_frm.doc.__islocal`);
   report.preparation=await c.evaluate(`(async()=>{const s=${JSON.stringify(state)};await cur_frm.set_value({company:s.company,item:s.items[1],quantity:1,with_operations:1});
    cur_frm.clear_table('items');const raw=cur_frm.add_child('items',{item_code:s.items[0],qty:1,rate:10,uom:'Nos',stock_uom:'Nos',conversion_factor:1,stock_qty:1});
    await frappe.model.set_value(raw.doctype,raw.name,'item_code',s.items[0]);
    cur_frm.clear_table('operations');cur_frm.add_child('operations',{operation:s.operation,workstation:s.workstation,time_in_mins:10,hour_rate:60,base_hour_rate:60});
    cur_frm.refresh_fields();const original=frappe.model.set_value;window.s6SetValueCalls=[];window.s6OriginalSetValue=original;frappe.model.set_value=function(...args){window.s6SetValueCalls.push(args.slice(0,4));return original.apply(this,args)};return {dirty:cur_frm.is_dirty(),items:cur_frm.doc.items.length,operations:cur_frm.doc.operations.length}})()`);
   await c.evaluate(`cur_frm.page.btn_primary[0].click();true`);
   await c.until(`cur_frm?.doctype==='BOM'&&!cur_frm.doc.__islocal&&frappe.request.ajax_count===0`,45000);
   await c.pause(1200);
   report.result=await c.evaluate(`({name:cur_frm.doc.name,unsaved:cur_frm.doc.__unsaved||0,dirty:cur_frm.is_dirty(),primary:cur_frm.page.btn_primary.text(),disabled:cur_frm.page.btn_primary.prop('disabled'),calls:window.s6SetValueCalls})`);
   report.reproduced=report.result.primary.trim()!==await c.evaluate(`__('Submit')`);
   await c.screenshot('Spike/P1S6R5-SB/it018/refresh-bom-saved.png');
   await c.evaluate(`frappe.model.set_value=window.s6OriginalSetValue;true`);
  }else if(mode==='job'){
   assert.ok(state.job_card,'Work order preparation required');
   await c.evaluate(`frappe.set_route('Form','Job Card',${JSON.stringify(state.job_card)});true`);
   await c.until(`cur_frm?.doc?.name===${JSON.stringify(state.job_card)}&&document.querySelector('.jcd-btn-start')&&frappe.request.ajax_count===0`);
   async function snapshot(label){
    const value=await c.evaluate(`(async()=>{const r=await frappe.call({method:'frappe.client.get',args:{doctype:'Job Card',name:${JSON.stringify(state.job_card)}}});return {state:cur_frm.doc.status,paused:cur_frm.doc.is_paused,dirty:cur_frm.is_dirty(),timer:document.querySelector('.jcd-stopwatch')?.innerText,buttons:[...document.querySelectorAll('[class*="jcd-btn-"]')].map(e=>e.className),logs:r.message.time_logs.map(x=>({name:x.name,idx:x.idx,employee:x.employee,from_time:x.from_time,to_time:x.to_time,completed_qty:x.completed_qty}))}})()`);
    value.label=label;report.steps.push(value);save();await c.screenshot(`Spike/P1S6R5-SB/it018/refresh-job-${label}.png`);
   }
   await c.evaluate(`document.querySelector('.jcd-btn-start').click();true`);
   await c.until(`!!window.cur_dialog?.fields_dict?.employees`);
   await c.evaluate(`(async()=>{await cur_dialog.set_value('employees',[{employee:${JSON.stringify(state.employee)}}]);cur_dialog.get_primary_btn()[0].click();return true})()`);
   await c.until(`!!document.querySelector('.jcd-btn-pause')&&frappe.request.ajax_count===0`);
   await c.pause(1000);await snapshot('start');
   await c.evaluate(`document.querySelector('.jcd-btn-pause').click();true`);
   await c.until(`!!document.querySelector('.jcd-btn-resume')&&frappe.request.ajax_count===0`);
   await snapshot('pause');
   await c.evaluate(`document.querySelector('.jcd-btn-resume').click();true`);
   await c.until(`!!document.querySelector('.jcd-btn-pause')&&frappe.request.ajax_count===0`);
   await c.pause(1000);await snapshot('resume');
   await c.evaluate(`document.querySelector('.jcd-btn-complete').click();true`);
   await c.until(`!!cur_frm.job_completion_dialog?.fields_dict?.completed_qty`);
   await c.evaluate(`(async()=>{await cur_frm.job_completion_dialog.set_value('completed_qty',1);cur_frm.job_completion_dialog.get_primary_btn()[0].click();return true})()`);
   await c.until(`cur_frm.doc.total_completed_qty===1&&cur_frm.doc.time_logs.every(r=>r.to_time)&&frappe.request.ajax_count===0`,30000);
   await snapshot('complete');
   report.reproduced=report.steps.some(x=>x.logs.some(r=>r.name.startsWith('new-'))||new Set(x.logs.map(r=>r.idx)).size!==x.logs.length||x.logs.some(r=>!r.from_time));
  }else if(mode==='tax'){
   const start=c.events.length;
   await c.evaluate(`frappe.set_route('List','Sales Taxes and Charges Template');true`);
   await c.until(`cur_list?.doctype==='Sales Taxes and Charges Template'&&frappe.request.ajax_count===0`);
   report.result=await c.evaluate(`({route:frappe.get_route(),records:cur_list.data.length,text:document.body.innerText.slice(-1500)})`);
   report.requests=c.events.slice(start).filter(x=>x.method==='Network.requestWillBeSent'&&/frappe.desk.reportview/.test(x.params.request.url)).map(x=>x.params.request.url);
   report.reproduced=report.result.records===0;
   await c.screenshot('Spike/P1S6R5-SB/it018/refresh-tax-demo.png');
  }
  save();console.log(JSON.stringify(report));
 }finally{c.close();}
})().catch(error=>{report.error=String(error);save();console.error(error);process.exitCode=1});
