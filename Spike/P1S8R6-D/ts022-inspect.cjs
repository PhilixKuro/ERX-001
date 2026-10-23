const fs = require('node:fs');
const {open}=require('../P1S6R4-cdp.cjs');
(async()=>{const c=await open('http://s8dev.localhost:6787');try{
 await c.until('!!window.frappe_debug?.demo?.config');
 await c.evaluate("frappe.set_route('query-report','Capacity Load')");
 await c.pause(6000);
 console.log(JSON.stringify(await c.evaluate(`({site:frappe.boot.sitename,user:frappe.session.user,route:frappe.get_route(),ajax:frappe.request.ajax_count,report:frappe.query_report&&{name:frappe.query_report.report_name,data:frappe.query_report.data?.length,keys:Object.keys(frappe.query_report),filters:frappe.query_report.get_filter_values()},dialogs:[...document.querySelectorAll('.modal.show')].map(e=>e.innerText),text:document.body.innerText.slice(-1500)})`),null,2));
 await c.screenshot('D:/ERX-001/frappe-bench/logs/s8-ts022-inspect.png');
}finally{await c.close();}})().catch(e=>{console.error(e.message);process.exitCode=1;});
