const assert=require('node:assert/strict');
const fs=require('node:fs');
const path=require('node:path');
const {open}=require('../P1S6R4-cdp.cjs');
const logdir=path.join(__dirname,'../../frappe-bench/logs');
const fixture=JSON.parse(fs.readFileSync(path.join(logdir,'s8-ts019-fixture.json'),'utf8'));
const saved={};
(async()=>{
 const c=await open('http://s8dev.localhost:6787');
 const key=async(name,code,modifiers=0)=>{await c.send('Input.dispatchKeyEvent',{type:'rawKeyDown',key:name,windowsVirtualKeyCode:code,modifiers});await c.send('Input.dispatchKeyEvent',{type:'keyUp',key:name,windowsVirtualKeyCode:code,modifiers});};
 try{
  assert.equal(await c.evaluate('frappe.boot.sitename'),'s8dev.localhost');
  await c.until('!!frappe_debug.demo.config');
  saved.progress=await c.evaluate('frappe_debug.demo.progress');
  assert(saved.progress.refs.sales_order);assert(saved.progress.refs.purchase_order);
  saved.documents=await c.evaluate(`(async()=>{const p=frappe_debug.demo.progress,r={};for(const [key,dt] of Object.entries({sales_order:'Sales Order',purchase_order:'Purchase Order',purchase_receipt:'Purchase Receipt',payment_entry:'Payment Entry'})){const doc=await frappe.db.get_doc(dt,p.refs[key]);r[key]={name:doc.name,date:doc.posting_date||doc.transaction_date,flag:doc.set_posting_time};}return r;})()`);
  for(const [key,doc]of Object.entries(saved.documents)){assert.equal(doc.date,fixture.selftest.dates.D1,key);if(key==='purchase_receipt')assert.equal(doc.flag,1);}
  await c.evaluate(`(async()=>{
   const d=frappe_debug.demo;
   const cfg=${JSON.stringify(fixture.selftest)};cfg.acts[0].steps=[{action:'open_doc',doctype:'Sales Order',name:'${'${ref.sales_order}'}'},{action:'wait',until:'cur_frm.doc.name === ctx.refs.sales_order'}];
   d.register('selftest_clear_items',async()=>{});d.register('selftest_check_dates',async()=>{});
   await d.start(cfg);await d.begin_act(1);await d.next();
  })()`);
  saved.reference=await c.evaluate('cur_frm.doc.name');assert.equal(saved.reference,saved.progress.refs.sales_order);
  await c.evaluate('window.__previous_page=true');
  await c.send('Page.reload',{});
  await c.until('!window.__previous_page && !!window.frappe?.boot?.frappe_debug_demo && !!window.frappe_debug?.demo?.config');
  saved.reloaded=await c.evaluate('frappe.boot.frappe_debug_demo');
  assert.equal(saved.reloaded.refs.sales_order,saved.progress.refs.sales_order);assert.equal(saved.reloaded.step,2);
  saved.preflight=await c.evaluate(`(()=>{const d=frappe_debug.demo,result=[];for(const step of [{action:'unknown_action'},{action:'call',fn:'unknown_function'}]){try{d.validate({acts:[{steps:[step]}]});throw Error('accepted invalid');}catch(error){if(!error.message.includes('第 1 幕第 1 步'))throw error;result.push(error.message);}}return result;})()`);
  await c.evaluate(`(async()=>{const d=frappe_debug.demo;window.__ticks=0;window.__switches=[];d.register('selftest_tick',async()=>++window.__ticks);d.switch_act=async(...args)=>window.__switches.push(args);const cfg=${JSON.stringify(fixture.selftest)};cfg.acts[0].steps=[{action:'call',fn:'selftest_tick',say:'连续执行一'},{action:'call',fn:'selftest_tick',say:'讲解暂停',pause:'presenter'},{action:'call',fn:'selftest_tick',say:'继续执行二',pause:'presenter'}];await d.start(cfg);await d.begin_act(1);sessionStorage.setItem('frappe_debug_mode','live');await d.actions.open_doc({doctype:'Sales Order',name:d.progress.refs.sales_order});const input=document.createElement('input');input.id='selftest-focus';document.body.appendChild(input);input.focus();})()`);
  await key('ArrowRight',39);await c.pause(300);assert.equal(await c.evaluate('__ticks'),0);
  await c.evaluate('document.getElementById("selftest-focus").blur()');await key('ArrowRight',39);await c.until('__ticks===2 && !frappe_debug.demo.busy');
  saved.pause=await c.evaluate('({ticks:__ticks,step:frappe_debug.demo.progress.step,say:frappe_debug.demo.panel.say.textContent})');assert.equal(saved.pause.step,2);
  await key('h',72,1);assert.equal(await c.evaluate('frappe_debug.demo.panel.hidden'),true);
  await key('h',72,1);assert.equal(await c.evaluate('frappe_debug.demo.panel.hidden'),false);
  await key('ArrowRight',39);await c.until('__ticks===3 && !frappe_debug.demo.busy');
  await key('r',82,1);for(let n=1;n<=9;n++)await key(String(n),48+n,1);
  saved.switches=await c.evaluate('__switches');assert.equal(saved.switches.length,10);
  saved.keyboard=await c.evaluate(`({keys:Object.fromEntries(['right','alt+h','alt+r',...Array.from({length:9},(_,i)=>'alt+'+(i+1))].map(key=>[key,frappe.ui.keys.handlers[key]?.length])),visible_alts:[...document.querySelectorAll('.alt-underline')].filter(x=>$(x).is(':visible')&&/^[hr]$/i.test(x.textContent)).map(x=>x.parentElement.textContent),route:frappe.get_route(),panel:frappe_debug.demo.panel.textContent})`);
  for(const count of Object.values(saved.keyboard.keys))assert.equal(count,1);
  await c.screenshot(path.join(logdir,'s8-ts019-controls.png'));
  await c.evaluate(`(async()=>{const p=${JSON.stringify(saved.progress)};await frappe.xcall('frappe_debug.demo.progress.save_progress',{act:p.act,step:p.step,refs:p.refs,scene_date:p.scene_date});sessionStorage.removeItem('frappe_debug_mode');})()`);
  fs.writeFileSync(path.join(logdir,'s8-ts019-controls.json'),JSON.stringify(saved,null,2));console.log('PASS refresh refs, input guard, pause, right, alt+h, alt+r, alt+1..9',JSON.stringify(saved.keyboard));
 }finally{await c.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
