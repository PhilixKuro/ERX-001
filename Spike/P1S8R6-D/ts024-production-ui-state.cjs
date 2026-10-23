const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');
const logs = path.join(__dirname, '../../frappe-bench/logs');
const fixture = JSON.parse(fs.readFileSync(path.join(logs, 's8-ts024-browser-fixture.json'), 'utf8'));

(async () => {
  const c = await open('http://s8dev.localhost:6787');
  try {
    const state = await c.evaluate(`({
      site: frappe.boot.sitename,
      functions: Object.keys(frappe_debug.demo.functions),
      functionSource: String(frappe_debug.demo.functions.report_remaining_job_cards),
      scripts: [...document.scripts].map(script => script.src).filter(src => src.includes('frappe_debug')),
    })`);
    if (state.site !== 's8dev.localhost') throw Error(`wrong site ${state.site}`);
    const cards = await c.evaluate(`frappe.db.get_list('Job Card', {filters:{work_order:${JSON.stringify(fixture.work_order)}},fields:['name','for_quantity','total_completed_qty','process_loss_qty','docstatus','status'],limit:20})`);
    const report = {state, cards};
    fs.writeFileSync(path.join(logs, 's8-ts024-production-ui-state.json'), JSON.stringify(report,null,2));
    console.log(JSON.stringify({site:state.site,functionCount:state.functions.length,skipZero:state.functionSource.includes('remaining <= 1e-6'),cards}));
  } finally { await c.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
