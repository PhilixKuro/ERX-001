const fs=require('node:fs');const assert=require('node:assert/strict');const {open}=require('./P1S6R4-cdp.cjs');
(async()=>{const c=await open();const result={rounds:[]};const names=['Account','Warehouse','Cost Center','Company','Employee'];let saved;
try{
 saved=await c.evaluate(`(async()=>{const r={};for(const d of ${JSON.stringify(names)})r[d]=await frappe.model.user_settings.get(d);return r})()`);
 await c.evaluate(`(async()=>{localStorage.clear();for(const d of ${JSON.stringify(names)}){const s=await frappe.model.user_settings.get(d);delete s.last_view;await frappe.model.user_settings.update(d,s)}return true})()`);
 for(const round of ['clean','after-list']){
  if(round==='after-list'){
   for(const d of names){await c.evaluate(`frappe.set_route('List',${JSON.stringify(d)},'List');true`);await c.until(`frappe.get_route()[0]==='List'&&frappe.get_route()[1]===${JSON.stringify(d)}`);await c.pause(500);}
  }
  for(const d of names){
   await c.evaluate(`frappe.app.sidebar.setup('Business Flow');true`);const slug=d.toLowerCase().replaceAll(' ','-');
   await c.evaluate(`document.querySelector('.body-sidebar a[href="/desk/${slug}"]').click();true`);
   await c.until(`frappe.get_route()[1]===${JSON.stringify(d)}&&frappe.request.ajax_count===0`);await c.pause(500);
   const row=await c.evaluate(`({route:frappe.get_route(),nodes:[...document.querySelectorAll('.tree-node')].filter(e=>e.getClientRects().length).length,records:window.cur_list?.data?.length})`);
   assert.equal(row.route[0],['Company','Employee'].includes(d)?'List':'Tree');assert.ok(row.route[0]==='Tree'?row.nodes>0:row.records>0);
   row.doctype=d;row.round=round;result.rounds.push(row);await c.screenshot(`Spike/P1S6R4-tree-${round}-${slug}.png`);
  }
 }
 assert.equal(result.rounds.length,10);console.log(JSON.stringify(result));
}finally{if(saved)await c.evaluate(`(async()=>{for(const [d,s] of Object.entries(${JSON.stringify(saved)}))await frappe.model.user_settings.update(d,s);return true})()`);fs.writeFileSync('Spike/P1S6R4-tree-rounds.json',JSON.stringify(result,null,2));c.close()}
})().catch(e=>{console.error(e);process.exitCode=1});
