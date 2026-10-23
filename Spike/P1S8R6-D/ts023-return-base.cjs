const {open} = require('../P1S6R4-cdp.cjs');
(async () => {
  const c = await open('http://s8dev.localhost:6787');
  try {
    if (await c.evaluate('frappe.boot.sitename') !== 's8dev.localhost') throw Error('wrong site');
    const progress = await c.evaluate("frappe.xcall('frappe_debug.demo.progress.get_progress')");
    const target = progress.base_db;
    if (!target) throw Error('base db missing');
    await c.evaluate(`frappe.xcall('frappe_debug.demo.switch.switch_to_db',{db_name:${JSON.stringify(target)}})`);
    await c.evaluate("location.assign('/desk')");
    await c.until("!!window.frappe?.boot?.sitename && frappe.session.user === 'Administrator'",120000);
    console.log(await c.evaluate("frappe.xcall('frappe_debug.demo.switch.switch_status')"));
  } finally { await c.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
