const assert=require('node:assert/strict');
const {open}=require('../P1S6R4-cdp.cjs');
(async()=>{const c=await open('http://s8ts023preview.localhost:6787');try{
 assert.equal(await c.evaluate('frappe.boot.sitename'),'s8ts023preview.localhost');
 await c.until('!!frappe_debug?.demo?.business_functions_loaded');
 await c.evaluate(`(async()=>{const demo=frappe_debug.demo;demo.config=await frappe.xcall('frappe_debug.demo.config.get_demo_config');await demo.transit_to_db('_3ba7ba1053a80306',{act:1,route:demo.config.start_route,return_to_base:true})})()`);
 await c.until("frappe.boot.sitename==='s8ts023preview.localhost' && location.pathname.startsWith('/app/')",120000);
 assert.equal(await c.evaluate("frappe.xcall('frappe_debug.demo.switch.switch_status').then(x=>x.db)"),'_3ba7ba1053a80306');
 console.log('Returned to isolated baseline');
}finally{await c.close()}})().catch(e=>{console.error(e);process.exitCode=1});
