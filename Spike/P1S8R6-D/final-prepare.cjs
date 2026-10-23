const assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const {open}=require('../P1S6R4-cdp.cjs');
(async()=>{const c=await open('http://s8dev.localhost:6787');try{
 assert.equal(await c.evaluate('frappe.boot.sitename'),'s8dev.localhost');
 assert.equal(await c.evaluate('frappe.session.user'),'Administrator');
 await c.until('!!window.frappe_debug?.demo?.business_functions_loaded',60000);
 const registry=await c.evaluate("frappe.xcall('frappe_debug.demo.snapshot.snapshot_status')");
 await c.evaluate(`frappe_debug.demo.start().then(()=>frappe_debug.demo.transit_to_db(${JSON.stringify(registry.work_db)},{route:'/desk/company'}));true`);
 await c.pause(2000);await c.until("!!window.frappe_debug?.demo?.business_functions_loaded && location.pathname==='/desk/company'",60000);
 const evidence=await c.evaluate(`(async()=>{
 const status=await frappe.xcall('frappe_debug.demo.switch.switch_status');
 if(!status.db.endsWith('_work')||frappe.session.user!=='Administrator')throw Error('Wrong work database');
 const suggestion=await frappe.db.get_doc('Replenishment Suggestion','RS-2026-00159');
 const mr=await frappe.db.get_doc('Material Request','MAT-MR-2026-00155');
 const prices=await frappe.db.get_list('Item Price',{filters:{item_code:'WIRE-65MN-3.0',buying:1},fields:['name','supplier','valid_from','valid_upto','price_list_rate'],order_by:'valid_from desc',limit:100});
 const scores=await frappe.db.get_list('Supplier Scorecard',{fields:['name','supplier','supplier_score'],limit:100});
 const account=await frappe.db.get_value('Account',{company:'华东弹簧有限公司',account_number:'1409'},'name');
 const doc=await frappe.db.get_doc('Account',account.message.name);doc.account_type='Stock';await frappe.xcall('frappe.client.save',{doc});
 await frappe_debug.demo.actions.open_report({report:'Stock and Account Value Comparison',filters:{company:'华东弹簧有限公司',as_on_date:'2026-01-07'}});
 return {status,suggestion,mr,prices,scores,stock_report:{filters:frappe.query_report.get_filter_values(),rows:frappe.query_report.data}};
 })()`);
 fs.writeFileSync(path.join(__dirname,'../../frappe-bench/logs/s8-ts024-business-readback.json'),JSON.stringify(evidence,null,2));
 assert.equal(evidence.stock_report.rows.length,0);
 assert.equal(evidence.mr.items[0].qty,evidence.suggestion.suggested_qty);
 console.log(JSON.stringify({stock_differences:0,suggested:evidence.suggestion.suggested_qty,adopted:evidence.mr.items[0].qty,prices:evidence.prices.length,suppliers:evidence.scores.length}));
}finally{await c.close();}})().catch(e=>{console.error(e);process.exitCode=1;});
