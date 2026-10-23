const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');
const logs = path.join(__dirname, '../../frappe-bench/logs');
const fixture = JSON.parse(fs.readFileSync(path.join(logs, 's8-ts024-browser-fixture.json'), 'utf8'));

(async () => {
  const c = await open('http://s8dev.localhost:6787');
  try {
    if (await c.evaluate('frappe.boot.sitename') !== 's8dev.localhost') throw Error('wrong site');
    await c.evaluate(`frappe.set_route('Form', 'Job Card', ${JSON.stringify(fixture.card_names[2])})`);
    await c.until(`cur_frm?.docname === ${JSON.stringify(fixture.card_names[2])} && !cur_frm.cscript?.is_onload`);
    await c.evaluate(`void (window.__diag=(async () => {
      const d = frappe_debug.demo;
      d.config = await frappe.xcall('frappe_debug.demo.config.get_demo_config');
      const ctx = {...d.context(),refs:{so1:${JSON.stringify(fixture.order)}},scene_date:${JSON.stringify(fixture.scene_date)}};
      const slot = await ctx.call('frappe_debug.demo.functions.job_card_slot',{job_card:cur_frm.doc.name,scene_date:ctx.scene_date});
      let error;
      try { await d.functions.complete_job_card(ctx,{completed_qty:cur_frm.doc.for_quantity}); } catch(e) { error=String(e); }
      const dialog=cur_frm.job_completion_dialog;
      return {slot,error,values:dialog && Object.fromEntries(['for_quantity','completed_qty','pending_qty','process_loss_qty','end_time'].map(key=>[key,dialog.get_value(key)])),doc:{name:cur_frm.doc.name,status:cur_frm.doc.status,time_logs:cur_frm.doc.time_logs}};
    })().catch(error=>({probe_error:String(error)})))`);
    await c.until('window.__diag && window.__diag.then', 1000);
    const report = await c.evaluate('window.__diag');
    fs.writeFileSync(path.join(logs, 's8-ts024-production-ui-field-diagnose.json'), JSON.stringify(report,null,2));
    console.log(JSON.stringify(report));
    process.exitCode = report.error ? 0 : 1;
    return;
    const state = await c.evaluate(`({
      business_functions_loaded: frappe_debug?.demo?.business_functions_loaded,
      function_names: Object.keys(frappe_debug?.demo?.functions || {}),
      scripts: [...document.scripts].map(script => script.src).filter(Boolean),
      route: frappe.get_route(),
      doc: {name:cur_frm.doc.name,docstatus:cur_frm.doc.docstatus,status:cur_frm.doc.status,for_quantity:cur_frm.doc.for_quantity,total_completed_qty:cur_frm.doc.total_completed_qty,process_loss_qty:cur_frm.doc.process_loss_qty,time_logs:cur_frm.doc.time_logs},
      dirty:cur_frm.is_dirty(),
      dialog:cur_dialog?.$wrapper?.text(),
      messages:[...document.querySelectorAll('.modal-body,.msgprint,.alert-danger')].map(x=>x.textContent.trim()).filter(Boolean),
      ajax:frappe.request?.ajax_count,
    })`);
    const submit = await c.evaluate(`(async () => {
      await cur_frm.save('Submit');
      await new Promise(resolve => setTimeout(resolve, 5000));
      return {docstatus:cur_frm.doc.docstatus,status:cur_frm.doc.status,dirty:cur_frm.is_dirty(),ajax:frappe.request?.ajax_count,messages:[...document.querySelectorAll('.modal-body,.msgprint,.alert-danger')].map(x=>x.textContent.trim()).filter(Boolean)};
    })()`);
    state.submit = submit;
    state.events = c.events.filter(event =>
      event.method === 'Runtime.exceptionThrown' ||
      event.method === 'Runtime.consoleAPICalled' ||
      (event.method === 'Network.responseReceived' && event.params?.response?.url?.includes('frappe_debug'))
    ).slice(-30);
    fs.writeFileSync(path.join(logs, 's8-ts024-production-ui-diagnose.json'), JSON.stringify(state,null,2));
    await c.screenshot(path.join(logs, 's8-ts024-production-ui-diagnose.png'));
    console.log(JSON.stringify(state));
  } finally { await c.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
