const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {open}=require('../P1S6R4-cdp.cjs');
const logs=path.join(__dirname,'../../frappe-bench/logs');
const lastAct=Number(process.argv[2] || 5);
(async()=>{
 const c=await open('http://s8ts023preview.localhost:6787');
 try {
  assert.equal(await c.evaluate('frappe.boot.sitename'),'s8ts023preview.localhost');
  await c.evaluate(`sessionStorage.setItem('frappe_debug_mode','live'); sessionStorage.removeItem('frappe_debug_rehearsal');`);
  const previousFile=path.join(logs,'s8-ts024-preview-ui.json');
  if(fs.existsSync(previousFile)){
   const saved=JSON.parse(fs.readFileSync(previousFile,'utf8'));
    const resumeRoute = saved.progress?.act === 2 && saved.progress?.refs?.mr1
     ? '/desk/material-request/'+saved.progress.refs.mr1 : saved.route;
    if(resumeRoute?.startsWith('/desk/')) {
    await c.navigate('http://s8ts023preview.localhost:6787'+resumeRoute);
    await c.until("!!window.frappe?.boot?.sitename && !!window.cur_frm?.doc && !cur_frm.cscript?.is_onload && !frappe.ajax_count",120000);
    await c.pause(1500);
   }
  }
  let previous='', started=Date.now();
  while(Date.now()-started<7200000){
   try {
    const current=await c.evaluate(`(async()=>{
     const crm=JSON.parse(sessionStorage.getItem('frappe_debug_result') || 'null');
     if(crm?.error) return {error:crm.error};
     if(!window.frappe?.boot?.sitename) return {route:location.pathname,loading:true};
     if(frappe.boot.sitename!=='s8ts023preview.localhost') throw Error('Wrong site');
     const demo=window.frappe_debug?.demo;
     if(!demo?.business_functions_loaded) return {loading:true};
     if(!demo.config) {if(!window.previewStarting){window.previewStarting=true;demo.start().then(()=>window.previewStarting=false,error=>window.previewError=error.message);} return {loading:true};}
     return {progress:demo.progress,steps:demo.config.acts[demo.progress.act-1]?.steps.length,route:location.pathname,busy:window.previewBusy,error:window.previewError};
    })()`);
    if(current.error) throw Error(current.error);
    if(current.loading){await c.pause(500);continue;}
    const p=current.progress;
    fs.writeFileSync(path.join(logs,'s8-ts024-preview-ui.json'),JSON.stringify(current,null,2));
    const signature=p.act+':'+p.step;
    if(signature!==previous){console.log(JSON.stringify(current));previous=signature;}
    if(!current.busy){
     if(p.step>=current.steps){
      await c.screenshot(path.join(logs,`s8-ts024-preview-act${p.act}.png`));
      if(p.act>=lastAct){console.log('PASS preview acts through '+lastAct);return;}
      await c.evaluate(`frappe_debug.demo.begin_act(${p.act+1})`);
     }else{
      await c.evaluate(`window.previewBusy=true; frappe_debug.demo.run_step(${p.act},${p.step}).then(()=>window.previewBusy=false,error=>{window.previewError=error.message;window.previewBusy=false;}); true`);
     }
    }
    await c.pause(500);
   } catch(error){
    if(/context was destroyed|Cannot find context|Inspected target navigated/.test(error.message)){await c.pause(500);continue;}
    throw error;
   }
  }
  throw Error('Preview exceeded the two-hour limit');
 }catch(error){await c.screenshot(path.join(logs,'s8-ts024-preview-failed.png'));throw error;}
 finally{await c.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
