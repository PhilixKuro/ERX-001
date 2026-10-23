const assert = require('node:assert/strict');
const {open} = require('../P1S6R4-cdp.cjs');
(async () => {
  const c = await open('http://s8dev.localhost:6787');
  try {
    assert.equal(await c.evaluate('frappe.boot.sitename'), 's8dev.localhost');
    assert.equal(await c.evaluate('frappe.session.user'), 'Administrator');
    const result = await c.evaluate("fetch('/assets/frappe_debug/demo/transit.html').then(async r=>({status:r.status,html:(await r.text()).includes('正在切换演示数据')}))");
    assert.equal(result.status, 200);
    assert.equal(result.html, true);
    console.log('PASS HT-018 static transit page', result);
  } finally { await c.close(); }
})().catch(e=>{console.error(e.message);process.exitCode=1;});
