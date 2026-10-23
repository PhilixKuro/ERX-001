const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');
const logdir = path.join(__dirname, '../../frappe-bench/logs');
const fixture = JSON.parse(fs.readFileSync(path.join(logdir, 's8-ts022-fixture.json'), 'utf8'));
const results = [];
(async () => {
 const c = await open('http://s8dev.localhost:6787');
 await c.send('Page.addScriptToEvaluateOnNewDocument',{source:`if(location.pathname.includes('/assets/frappe_debug/demo/transit.html')){const original=window.fetch;window.fetch=async(...args)=>{const response=await original(...args);if(String(args[0]).includes('switch_status')){const identity=(await response.clone().json()).message;sessionStorage.setItem('ts022_first_identity',JSON.stringify(identity));}return response;};}`});
 const api = (method, args={}) => c.evaluate(`frappe.xcall(${JSON.stringify(method)},${JSON.stringify(args)})`);
 const waitReady = async (act, needed = 'both') => {
   const started=Date.now();
   for (;;) {
     const registry=await api('frappe_debug.demo.snapshot.snapshot_status');
     const copies=registry.acts[String(act)];
     assert(copies, `missing act ${act}`);
     for(const copy of Object.values(copies)) assert.notEqual(copy.state,'failed',JSON.stringify(copies));
     if(needed === 'main' ? copies.m.state === 'ready' : needed === 'any' ? [copies.m,copies.b].some(copy=>copy.state==='ready') : copies.m.state==='ready' && copies.b.state==='ready') return (Date.now()-started)/1000;
     if(Date.now()-started>600000) throw Error(`act ${act} refill timeout`);
     await c.pause(2000);
   }
 };
 const switchAct=async(act,purpose)=>{
   const before=await api('frappe_debug.demo.switch.switch_status');
   await c.evaluate('window.__departing_ts022=true');
   if(purpose==='forward') await c.evaluate(`(async()=>{const d=frappe_debug.demo;d.progress.step=d.config.acts[d.progress.act-1].steps.length;await frappe.xcall('frappe_debug.demo.progress.save_progress',{act:d.progress.act,step:d.progress.step,refs:d.progress.refs,scene_date:d.progress.scene_date});})()`);
   await c.until('frappe.request.ajax_count===0');
   const eventStart=c.events.length,started=Date.now();
   try {
     if(purpose==='forward'){
       await c.send('Input.dispatchKeyEvent',{type:'keyDown',key:'ArrowRight',code:'ArrowRight',windowsVirtualKeyCode:39});
       await c.send('Input.dispatchKeyEvent',{type:'keyUp',key:'ArrowRight',code:'ArrowRight',windowsVirtualKeyCode:39});
     }else await c.evaluate(`frappe_debug.demo.switch_act(${act},${JSON.stringify(purpose)})`);
   }catch(e){if(!/context|navigat/i.test(e.message))throw e;}
   const deadline=Date.now()+180000;
   for(;;){
     try {
       const state=await c.evaluate(`({ready:!window.__departing_ts022 && !!window.frappe_debug?.demo?.config && !location.pathname.includes('/assets/'),error:document.getElementById('error')?.textContent,login:location.pathname.includes('/login')})`);
       if(state.error) throw Error(state.error);
       assert(!state.login,'must never navigate to login');
       if(state.ready){
         const expected={5:['List','Work Order'],6:['query-report','Capacity Load'],7:['List','Sales Order'],8:['query-report','Replenishment Strategy Comparison']}[act];
         const ready=await c.evaluate(`(()=>{const r=frappe.get_route(),e=${JSON.stringify(expected)};if(!r||r[0]!==e[0]||r[1]!==e[1]||frappe.request.ajax_count)return false;if([...document.querySelectorAll('.modal.show')].some(x=>x.getBoundingClientRect().height))throw Error('visible error dialog');if(r[0]==='List')return cur_list?.doctype===e[1]&&Array.isArray(cur_list.data);const q=frappe.query_report;return q?.report_name===e[1]&&q.report_settings&&q.filters?.length&&!q.$loading?.is(':visible')&&(Array.isArray(q.data)||q.$message?.is(':visible'));})()`);
         if(ready)break;
       }
     } catch(e){if(!/context|navigat/i.test(e.message))throw e;}
     if(Date.now()>deadline)throw Error('switch UI deadline');
     await c.pause(100);
   }
   const seconds=(Date.now()-started)/1000;
   const state=await c.evaluate(`({site:frappe.boot.sitename,user:frappe.session.user,progress:frappe.boot.frappe_debug_demo,route:frappe.get_route(),url:location.href})`);
   assert.equal(state.site,'s8dev.localhost'); assert.equal(state.user,'Administrator');
   assert.equal(state.progress.act,act);assert.equal(state.progress.step,0);
   assert.deepEqual(state.progress.refs,fixture.refs);
   const db=await api('frappe_debug.demo.switch.switch_status');
   const progress=await api('frappe_debug.demo.progress.get_progress');assert.equal(progress.act,act);assert.equal(progress.step,0);
   const responses=c.events.slice(eventStart).filter(e=>e.method==='Network.responseReceived').map(e=>e.params);
   assert.deepEqual(responses.filter(e=>e.response.url.includes('/api/')&&e.response.status>=400).map(e=>e.response.url),[]);
   const first=responses.find(e=>e.response.url.includes('/api/method/frappe_debug.demo.switch.switch_status'));assert(first);
   const identity=JSON.parse(await c.evaluate("sessionStorage.getItem('ts022_first_identity')"));
   assert.equal(identity.user,'Administrator');assert.equal(identity.db,db.db);
   results.push({from:before.db,act,purpose,seconds,db:db.db,user:db.user,route:state.route,firstRequestUser:identity.user,pageReady:true});
   fs.writeFileSync(path.join(logdir,'s8-ts022-native-strict.json'),JSON.stringify(results,null,2));
   console.log('SWITCH',JSON.stringify(results.at(-1)));
   return seconds;
 };
 try {
   await c.until('!!window.frappe_debug?.demo?.config');
   assert.equal(await c.evaluate('frappe.boot.sitename'),'s8dev.localhost');
   assert.equal(await c.evaluate('frappe.session.user'),'Administrator');
   await c.evaluate(`sessionStorage.setItem('frappe_debug_mode','live');frappe_debug.demo.start()`);
   if(!process.argv.includes('--short')) {
     for(const [source,target] of [[5,6],[7,8]]) {
       for(let n=0;n<5;n++) {
         await waitReady(target,'any');
         const reg=await api('frappe_debug.demo.snapshot.snapshot_status');
         if(reg.acts[String(target)].m.state!=='ready'){await switchAct(target,'restart');await waitReady(target,'main');}
         await waitReady(source,'any');
         await switchAct(source,'jump');
         const seconds=await switchAct(target,'forward');
         assert(seconds<=10,`${source}->${target}: ${seconds}s exceeds 10s`);
       }
     }
   } else {await waitReady(8,'any');await switchAct(8,'jump');}
   await c.evaluate(`frappe_debug.demo.actions.open_doc({doctype:'Sales Order',name:frappe_debug.demo.progress.refs.sales_order})`);
   assert.equal(await c.evaluate('cur_frm.doc.name'),fixture.refs.sales_order);
   console.log('PASS target snapshot reference opens the native Sales Order');
   for(let n=0;n<2;n++){
     const inserted=await api('frappe.client.insert',{doc:{doctype:'ToDo',description:`_FCT TS022 restart ${n}`,status:'Open'}});
     assert(inserted.name);
     const beforeWait=await waitReady(8,'any');
     const seconds=await switchAct(8,'restart');
     const counts={};
     for(const dt of Object.keys(fixture.counts)) counts[dt]=await api('frappe.client.get_count',{doctype:dt});
     assert.deepEqual(counts,fixture.counts);
     results.push({check:'clean_restart',iteration:n+1,seconds,beforeWait,counts});
     const waited=await waitReady(8,'any').catch(async error=>{
       // The currently used copy stays used; wait only for the other copy.
       throw error;
     });
     results.push({check:'refill_wait',seconds:waited});
   }
   await c.screenshot(path.join(logdir,'s8-ts022-native-strict.png'));
   fs.writeFileSync(path.join(logdir,'s8-ts022-native-strict.json'),JSON.stringify(results,null,2));
   console.log('PASS native switch acceptance');
 } catch(error){
   const state=await c.evaluate('({url:location.href,text:document.body.innerText.slice(0,2500)})').catch(()=>null);
   fs.writeFileSync(path.join(logdir,'s8-ts022-strict-failure.json'),JSON.stringify({error:error.message,state,results},null,2));
   await c.screenshot(path.join(logdir,'s8-ts022-strict-failure.png')).catch(()=>{});
   throw error;
 } finally {await c.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
