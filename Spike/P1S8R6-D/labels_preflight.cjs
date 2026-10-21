const { open } = require('../P1S6R4-cdp.cjs');
(async () => {
 const c = await open();
 try {
  const state = await c.evaluate(`JSON.stringify({site:frappe.boot.sitename,lang:frappe.boot.lang,actions:frappe.boot.success_action})`);
  if (JSON.parse(state).site !== 'test.localhost') throw Error('Wrong site');
  console.log(state);
  const success = await c.evaluate(`(() => {
   const action = Object.create(frappe.ui.form.SuccessAction.prototype);
   action.form = {doctype:'Purchase Receipt'};
   action.setting = {ref_doctype:'Purchase Receipt',message:'Purchase Receipt has been submitted successfully',first_success_message:'Purchase Receipt has been submitted successfully',next_actions:'',action_timeout:30};
   frappe.db.get_list = () => Promise.resolve([]);
   action.show_alert();
   return JSON.stringify({patched:!!action.show_alert.__frappe_china_success_message,setting:action.setting});
  })()`);
  await c.until("document.body.innerText.includes('已成功提交采购入库')");
  const successText = await c.evaluate(`document.body.innerText.includes('已成功提交采购入库')`);
  if (!successText || !JSON.parse(success).patched) throw Error('Submitted success message was not translated');
  console.log(success);
  await c.screenshot(require('node:path').join(__dirname,'SL008-submit-success.png'));
  await c.navigate('http://test.localhost:6787/crm/deals/view/kanban');
  await c.pause(3000);
  const stages = await c.evaluate("Array.from(document.querySelectorAll('.flex.items-center.text-base > *')).map(el => el.textContent.trim()).filter(Boolean)");
  console.log(JSON.stringify({stages,config:await c.evaluate("document.getElementById('china-ui-labels')?.textContent?.slice(0,500)"),app:await c.evaluate("document.querySelector('#app')?.innerText?.slice(-250)")}));
  for (const value of ['需求确认','方案演示','报价','谈判中','待成交','赢单','未成交']) if (!stages.includes(value)) throw Error('Missing translated stage: '+value);
  if (['Qualification','Demo/Making','Proposal/Quotation','Negotiation','Ready to Close','Won','Lost'].some(value=>stages.includes(value))) throw Error('English CRM status remains');
  console.log(JSON.stringify({crm_status_headers:stages}));
  await c.screenshot(require('node:path').join(__dirname,'SL008-crm-deals-kanban.png'));
  await c.navigate('http://test.localhost:6787/desk');
  await c.until('!!(window.frappe?.boot && frappe.app?.sidebar)');
  await c.evaluate(`frappe.set_route('query-report','SPC Control Chart')`);
  await c.until(`frappe.query_report?.report_name === 'SPC Control Chart' && !!frappe.query_report.get_filter('item_code')`);
  console.log(await c.evaluate(`JSON.stringify({translations:['Date','Quality Inspection','Subgroup Size','Subgroup Mean','Subgroup Range','Triggered Rules','Subgroups','SPC Readings','Rejected Readings','Signal Points','Insufficient samples; for reference only'].map(k=>[k,__(k)]),prepared:frappe.query_report.report_doc.prepared_report})`));
  await c.screenshot(require('node:path').join(__dirname,'SL008-spc-before.png'));
 } finally {await c.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
