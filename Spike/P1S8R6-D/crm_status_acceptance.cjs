const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');

(async () => {
 const c = await open();
 const results = [];
 try {
  assert.equal(await c.evaluate('frappe.boot.sitename'), 'test.localhost');
  for (const [route, expected] of [
   ['leads', ['新线索','已联系','培育中','合格','已转化','不合格','无效']],
   ['deals', ['需求确认','方案演示','报价','谈判中','待成交','赢单','未成交']],
  ]) {
   await c.navigate(`http://test.localhost:6787/crm/${route}`);
   await c.until("[...document.querySelectorAll('button')].some(button=>button.textContent.trim()==='状态')");
   await c.evaluate("[...document.querySelectorAll('button')].find(button=>button.textContent.trim()==='状态').click(); true");
   await c.until("document.querySelectorAll('[role=option]').length >= 7");
   const options = await c.evaluate("[...document.querySelectorAll('[role=option]')].map(el=>el.textContent.trim())");
   assert(expected.every(label=>options.includes(label)), JSON.stringify({route,options}));
   await c.screenshot(path.join(__dirname,`SL008-crm-${route}-dropdown.png`));
   await c.navigate(`http://test.localhost:6787/crm/${route}/view/kanban`);
   await c.until("document.querySelectorAll('.flex.overflow-x-auto.h-full .flex.items-center.text-base > .text-ink-gray-9').length >= 7");
   await c.pause(300);
   const headers = await c.evaluate("Array.from(document.querySelectorAll('.flex.overflow-x-auto.h-full .flex.items-center.text-base > .text-ink-gray-9')).map(el=>el.textContent.trim())");
   assert(expected.every(label=>headers.includes(label)),JSON.stringify({route,headers}));
   await c.screenshot(path.join(__dirname,`SL008-crm-${route}-kanban.png`));
   results.push({route,options,headers});
  }
  fs.writeFileSync(path.join(__dirname,'../../frappe-bench/logs/s8-ts009-crm-acceptance.json'),JSON.stringify(results,null,2));
  console.log(JSON.stringify(results));
 } finally { await c.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
