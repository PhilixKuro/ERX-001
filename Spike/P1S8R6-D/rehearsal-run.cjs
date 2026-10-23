const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {spawn} = require('node:child_process');
const {open} = require('../P1S6R4-cdp.cjs');

const site = process.argv[2] || 's8ts023preview.localhost';
const operation = process.argv[3] || 'start';
const resumeAct = Number(process.argv[4] || 0);
assert.ok(['s8ts023preview.localhost','s8dev.localhost'].includes(site));
assert.ok(['start','resume','observe','retry'].includes(operation));
const qualityPreview = process.argv.includes('--quality-preview');
assert.ok(!qualityPreview || site === 's8ts023preview.localhost');
const label = site === 's8dev.localhost' ? 'acceptance' : 'preview';
const logs = path.join(__dirname,'../../frappe-bench/logs');
const output = path.join(logs,`s8-rehearsal-${label}.json`);
const evidence = path.join(__dirname,'acts',label);
fs.mkdirSync(evidence,{recursive:true});
const traceFile = path.join(logs,`s8-rehearsal-${label}.log`);
const log = value => { const line=JSON.stringify({at:new Date().toISOString(),...value});console.log(line);fs.appendFileSync(traceFile,line+'\n'); };

// Observation only: wait at each act's natural end while CDP records its screen.
// The browser still executes the actual configured business steps and handoffs.
const instrument = `(() => {
 if(window.__s8Observer)return;window.__s8Observer=true;
 window.__s8Errors=[];window.__s8Routes=[];window.__s8Dialogs=[];
 window.addEventListener('unhandledrejection',e=>window.__s8Errors.push(String(e.reason?.message||e.reason)));
 window.addEventListener('error',e=>window.__s8Errors.push(e.message));
 setInterval(()=>{
  const demo=window.frappe_debug?.demo;
  if(!demo?.rehearsal || !demo.business_functions_loaded)return;
  if(!demo.__s8WaitInstrumented){
   demo.__s8WaitInstrumented=true;const waitFor=demo.wait_for;
   demo.wait_for=async(predicate,ms,description)=>{
    let latest;
    const sample=async()=>{
     const result=await predicate();
     latest={at:Date.now(),description,result,route:location.pathname,doctype:window.cur_frm?.doctype,name:window.cur_frm?.doc?.name,
      is_new:window.cur_frm?.is_new?.(),onload:window.cur_frm?.cscript?.is_onload,supplier:window.cur_frm?.doc?.supplier,
      items:window.cur_frm?.doc?.items?.map(row=>({item_code:row.item_code,qty:row.qty,received_qty:row.received_qty})),
      progress:demo.progress};
     if(description==='等待条件' && demo.progress?.act===3)window.__s8WaitTrace=latest;
     return result;
    };
    try{return await waitFor(sample,ms,description);}
    catch(error){if(description==='等待条件' && demo.progress?.act===3)window.__s8WaitFailure={...latest,error:error.message};throw error;}
   };
  }
  if(!demo.__readyEvidence){
   demo.__readyEvidence=true;const call=demo.call;
   demo.call=async(method,args)=>{
    const result=await call(method,args);
    if(method.endsWith('snapshot_status')){
     const copies=Object.values(result.acts||{}).flatMap(act=>Object.values(act));
     if(copies.length===27 && copies.every(copy=>copy.state==='ready'))sessionStorage.setItem('s8_evidence_ready_registry',JSON.stringify(result));
    }
    return result;
   };
  }
  if(${qualityPreview} && !demo.__previewRPC){
   demo.__previewRPC=true;const call=demo.call;
   demo.call=async(method,args)=>{
    if(!method.endsWith('start_generate'))return call(method,args);
    window.__s8GenerationRequest={...args};
    while(!window.__s8GenerationRequest.result && !window.__s8GenerationRequest.error)await new Promise(r=>setTimeout(r,100));
    const request=window.__s8GenerationRequest;window.__s8GenerationRequest=null;
    if(request.error)throw Error(request.error);return request.result;
   };
  }
  if(!demo.rehearsal.__observed){
   demo.rehearsal.__observed=true;
   const original=demo.rehearsal._play_act;
   demo.rehearsal._play_act=async function(state,act){
    const result=await original.call(this,state,act);
    if(result===demo.HANDOFF)return result;
    const report=window.frappe?.query_report;
    window.__s8Capture={act,route:location.pathname+location.search,sidebar:frappe.app?.sidebar?.current_sidebar,
     progress:demo.progress,form:window.cur_frm?{doctype:cur_frm.doctype,name:cur_frm.doc.name,docstatus:cur_frm.doc.docstatus}:null,
     report:report?.report_name?{name:report.report_name,filters:report.get_filter_values(),rows:report.data}:null,
     dialogs:window.__s8Dialogs,errors:window.__s8Errors,routes:window.__s8Routes};
    const deadline=Date.now()+30000;while(window.__s8Capture && Date.now()<deadline)await new Promise(r=>setTimeout(r,100));
    return result;
   };
   const runStep=demo.run_step;
   demo.run_step=async function(act,index){
    const result=await runStep.call(this,act,index);if(result===demo.HANDOFF)return result;
    const step=demo.config.acts[act-1].steps[index];
    if(step.action==='open_report' || (act===7 && step.fn==='open_previous_month_statement') ||
       (act===1 && index===2) || (act===4 && step.save_as==='plan1') ||
       (act===6 && step.action==='wait') || (act===9 && [2,3].includes(index))){
     const report=frappe.query_report;
     window.__s8Capture={kind:'step',act,step:index+1,route:location.pathname+location.search,progress:demo.progress,
      form:window.cur_frm?{doctype:cur_frm.doctype,name:cur_frm.doc.name,docstatus:cur_frm.doc.docstatus,doc:cur_frm.doc}:null,
      report:report?.report_name?{name:report.report_name,filters:report.get_filter_values(),rows:report.data}:null,
      dialogs:window.__s8Dialogs,body:document.body.innerText.slice(-15000)};
     const end=Date.now()+30000;while(window.__s8Capture && Date.now()<end)await new Promise(r=>setTimeout(r,100));
    }
    return result;
   };
  }
  const route=location.pathname+location.search;
  if(window.__s8Routes.at(-1)!==route)window.__s8Routes.push(route);
  const dialog=window.cur_dialog;
  if(dialog?.$wrapper?.is(':visible')){
   const title=dialog.title||dialog.$wrapper.find('.modal-title').text();
   if(!window.__s8Dialogs.some(d=>d.title===title))window.__s8Dialogs.push({title,text:dialog.$wrapper.text().trim()});
  }
 },50);
})()`;

async function safeEvaluate(c,expression) {
 for(let i=0;i<30;i++){
  try {return await c.evaluate(expression);}
  catch(error){if(!/context.*destroy|Cannot find context|Inspected target navigated/i.test(error.message))throw error;await c.pause(300);}
 }
 throw Error('Browser navigation did not settle');
}

(async()=>{
 let c;
 for(let i=0;i<6;i++){
  try{c=await open(`http://${site}:6787`);break;}catch(error){if(i===5)throw error;await new Promise(r=>setTimeout(r,2000));}
 }
 try{
  assert.equal(await c.evaluate('frappe.boot.sitename'),site);
  assert.equal(await c.evaluate('frappe.session.user'),'Administrator');
  await c.send('Network.setCacheDisabled',{cacheDisabled:true});
  await c.send('Page.addScriptToEvaluateOnNewDocument',{source:instrument});
  await c.evaluate(instrument);
  const captureAjax = `(() => {
   if (!window.jQuery || window.__s8AjaxCapture) return;
   window.__s8AjaxCapture = [];
   jQuery(document).ajaxError((event, xhr, settings) => {
    if (settings.url?.includes('savedocs')) window.__s8AjaxCapture.push({url:settings.url,status:xhr.status,response:xhr.responseText,data:settings.data});
   });
  })()`;
  await c.send('Page.addScriptToEvaluateOnNewDocument',{source:`setInterval(()=>{${captureAjax}},100)`});
  await c.evaluate(captureAjax);
  await c.until('!!window.frappe_debug?.demo?.business_functions_loaded',60000);
  let previous=operation==='start'?null:JSON.parse(fs.readFileSync(output,'utf8'));
  if(operation==='start'){
   const baseline=await c.evaluate(`(async()=>({current:await frappe_debug.demo.call('frappe_debug.demo.switch.switch_status'),snapshots:await frappe_debug.demo.call('frappe_debug.demo.snapshot.snapshot_status')}))()`);
   assert.deepEqual(baseline.snapshots.acts||{},{});assert.equal(baseline.snapshots.work_db||null,null);
   log({event:'baseline',...baseline});
   if(site==='s8dev.localhost'){
    await c.evaluate("frappe.set_route('demo-rehearsal')");
    await c.until("Array.from(document.querySelectorAll('button')).some(b=>b.textContent.trim()==='开始整场预跑')",60000);
    await c.evaluate("Array.from(document.querySelectorAll('button')).find(b=>b.textContent.trim()==='开始整场预跑').click()");
   }else{
    await c.evaluate(`(async()=>{
     const demo=frappe_debug.demo,config=await demo.call('frappe_debug.demo.config.get_demo_config');
     demo.validate(config);demo.config=config;
     const prepared=await demo.call('frappe_debug.demo.workspace.prepare_work');
     const state={phase:'switch_work',act:1,status:'running',started:Date.now(),timings:[],logs:[],base_db:${JSON.stringify(baseline.current.db)},work_db:prepared.db};
     sessionStorage.setItem('frappe_debug_mode','rehearsal');sessionStorage.setItem('frappe_debug_rehearsal',JSON.stringify(state));
     await demo.rehearsal.continue();
    })().catch(e=>window.__s8StartError=e?.message||String(e));true`);
   }
  }else{
   await c.evaluate(`sessionStorage.setItem('frappe_debug_rehearsal',${JSON.stringify(JSON.stringify(previous.state))});sessionStorage.setItem('frappe_debug_mode','rehearsal');true`);
   if(operation==='retry')await c.evaluate("(()=>{const s=JSON.parse(sessionStorage.getItem('frappe_debug_rehearsal'));s.status='running';s.error=null;s.job_id=null;sessionStorage.setItem('frappe_debug_rehearsal',JSON.stringify(s));})()");
   await c.evaluate(`(async()=>{await frappe_debug.demo.start();await frappe_debug.demo.rehearsal.${operation==='resume'?`resume(${resumeAct})`:'continue()'};})().catch(e=>window.__s8StartError=e?.message||String(e));true`);
   if(operation==='resume')await c.until("!!window.__s8StartError || JSON.parse(sessionStorage.getItem('frappe_debug_rehearsal')||'null')?.status==='running'",60000);
  }
  let last='',lastHeartbeat=0;
  const deadline=Date.now()+8*60*60*1000;
  while(Date.now()<deadline){
   const generation=await safeEvaluate(c,'window.__s8GenerationRequest && !window.__s8GenerationRequest.result ? window.__s8GenerationRequest : null');
   if(generation){
    const job_id='s8-quality-preview-'+Date.now();
    const args=['compose','-f','docker/compose.yaml','exec','-T','-w','/workspace/frappe-bench','frappe','env/bin/python','/workspace/Spike/P1S8R6-D/quality-preview-segment.py',site,generation.from_date,generation.to_date,job_id];
    const child=spawn('docker',args,{cwd:path.resolve(__dirname,'../..'),windowsHide:true});
    const segmentLog=fs.createWriteStream(path.join(logs,job_id+'.log'));
    child.stdout.pipe(segmentLog);child.stderr.pipe(segmentLog);let buffer='';
    await new Promise((resolve,reject)=>{
     child.stdout.on('data',chunk=>{buffer+=chunk;if(buffer.includes('"started"'))resolve();});
     child.on('error',reject);child.on('exit',code=>{if(!buffer.includes('"started"'))reject(Error('Preview generator exited '+code+': '+buffer.slice(-1000)));});
    });
    await safeEvaluate(c,`window.__s8GenerationRequest.result={job_id:${JSON.stringify(job_id)}};true`);
    log({event:'preview-generation',job_id,...generation});
   }
   const capture=await safeEvaluate(c,'window.__s8Capture || null');
   if(capture){
    const filename=capture.kind==='step'?`act${capture.act}-step${capture.step}`:`act${capture.act}`;
    await c.screenshot(path.join(evidence,filename+'.png'));
    fs.writeFileSync(path.join(evidence,filename+'.json'),JSON.stringify(capture,null,2));
    log({event:capture.kind==='step'?'checkpoint':'act-complete',act:capture.act,step:capture.step,form:capture.form?{doctype:capture.form.doctype,name:capture.form.name}:null,report:capture.report?{name:capture.report.name,rows:capture.report.rows?.length}:null});
    if(process.argv.includes('--stop-after-act4') && capture.kind!=='step' && capture.act===4){log({event:'resume-act4-verified'});return;}
    await safeEvaluate(c,'window.__s8Capture=null');
   }
   const local=await safeEvaluate(c,`({state:JSON.parse(sessionStorage.getItem('frappe_debug_rehearsal')||'null'),site:window.frappe?.boot?.sitename,route:location.pathname,start_error:window.__s8StartError||null,progress:window.frappe_debug?.demo?.progress,errors:window.__s8Errors,wait_trace:window.__s8WaitTrace||null,wait_failure:window.__s8WaitFailure||null,transit_error:document.getElementById('error')?.textContent})`);
   if(local.site)assert.equal(local.site,site);
   const signature=JSON.stringify([local.state?.phase,local.state?.act,local.state?.status,local.progress?.step,local.state?.error]);
   if(signature!==last || Date.now()-lastHeartbeat>60000){
    last=signature;lastHeartbeat=Date.now();
    log({event:'progress',phase:local.state?.phase,act:local.state?.act,status:local.state?.status,step:local.progress?.step,route:local.route,error:local.state?.error||local.start_error||local.transit_error||null});
   }
   if(local.state){
    previous={...(previous||{}),...local,observed_at:new Date().toISOString()};fs.writeFileSync(output,JSON.stringify(previous,null,2));
   }
   if(local.start_error||local.transit_error)throw Error(local.start_error||local.transit_error);
   if(local.state?.status==='failed')throw Error(local.state.error);
   if(local.state?.status==='done'){
    let final;const settle=Date.now()+120000;
    while(Date.now()<settle){
     if(await safeEvaluate(c,'!!window.frappe_debug?.demo?.call')){
      final=await safeEvaluate(c,`(async()=>({db:await frappe_debug.demo.call('frappe_debug.demo.switch.switch_status'),snapshots:await frappe_debug.demo.call('frappe_debug.demo.snapshot.snapshot_status'),progress:await frappe_debug.demo.call('frappe_debug.demo.progress.get_progress'),mode:sessionStorage.getItem('frappe_debug_mode'),ready_registry:JSON.parse(sessionStorage.getItem('s8_evidence_ready_registry')||'null')}))()`);
      if(final.db.db.endsWith('_a1_m') && final.progress.act===1 && final.progress.step===0 && final.mode==='live')break;
     }
     await c.pause(500);
    }
    assert.ok(final?.db?.db.endsWith('_a1_m'),'must finish in act-one main database');
    previous={...previous,...final};fs.writeFileSync(output,JSON.stringify(previous,null,2));
    await c.screenshot(path.join(evidence,'final.png'));log({event:'done',...final,total_seconds:local.state.total_seconds});break;
   }
   await c.pause(700);
  }
  assert.equal(previous?.state?.status,'done');
 }catch(error){
  const failure = await safeEvaluate(c,`({ajax:window.__s8AjaxCapture,dialogs:window.__s8Dialogs,body:document.body.innerText,form:window.cur_frm?.doc})`).catch(e=>({capture_error:e.message}));
  fs.writeFileSync(path.join(logs,`s8-rehearsal-${label}-failure.json`),JSON.stringify(failure,null,2));
  log({event:'failure',message:error.message});await c.screenshot(path.join(evidence,'failure.png')).catch(()=>{});throw error;
 }finally{await c.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
