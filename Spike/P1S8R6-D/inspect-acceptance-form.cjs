const fs=require('node:fs');
const {open}=require('../P1S6R4-cdp.cjs');

(async()=>{
 const state=JSON.parse(fs.readFileSync(require('node:path').resolve(__dirname,'../../frappe-bench/logs/s8-rehearsal-acceptance.json'),'utf8'));
 const c=await open('http://s8dev.localhost:6787');
 try {
  if(await c.evaluate('frappe.boot.sitename')!=='s8dev.localhost')throw Error('Wrong site');
  await c.navigate(`http://s8dev.localhost:6787${state.route}`);
  await c.until('!!window.cur_frm?.doc?.doctype',30000);
  await c.pause(3000);
  console.log(JSON.stringify(await c.evaluate(`(()=>({site:frappe.boot.sitename,user:frappe.session.user,route:location.pathname,doctype:cur_frm?.doctype,name:cur_frm?.doc?.name,docstatus:cur_frm?.doc?.docstatus,is_new:cur_frm?.is_new?.(),dirty:cur_frm?.is_dirty?.(),onload:cur_frm?.cscript?.is_onload,doc:{supplier:cur_frm?.doc?.supplier,items:cur_frm?.doc?.items?.map(x=>({item_code:x.item_code,qty:x.qty,received_qty:x.received_qty,warehouse:x.warehouse}))},body:document.body.innerText.slice(0,1800),alerts:[...document.querySelectorAll('.msgprint,.alert')].map(x=>x.innerText).filter(Boolean)}))()`),null,2));
 } finally {await c.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
