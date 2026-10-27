// S8 R8 SB FD-002：Desk 全站「New」等回到官方译文，/crm 页状态仍为中文
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');
(async () => {
 const c = await open();
 const out = {};
 try {
  assert.equal(await c.evaluate('frappe.boot.sitename'), 'test.localhost');
  out.desk = await c.evaluate("({New: __('New'), Qualification: __('Qualification'), Qualified: __('Qualified'), Converted: __('Converted'), Unqualified: __('Unqualified'), Created: __('Created'), CreatedResult: __('Created', null, 'Result Status')})");
  assert.deepEqual(out.desk, {New:'新建',Qualification:'资质',Qualified:'已认证',Converted:'已转换',Unqualified:'未认证',Created:'创建',CreatedResult:'已创建'});
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
   await c.navigate(`http://test.localhost:6787/crm/${route}/view/kanban`);
   await c.until("document.querySelectorAll('.flex.overflow-x-auto.h-full .flex.items-center.text-base > .text-ink-gray-9').length >= 7");
   await c.pause(300);
   const headers = await c.evaluate("Array.from(document.querySelectorAll('.flex.overflow-x-auto.h-full .flex.items-center.text-base > .text-ink-gray-9')).map(el=>el.textContent.trim())");
   assert(expected.every(label=>headers.includes(label)),JSON.stringify({route,headers}));
   await c.screenshot(path.join(__dirname,`fd002-crm-${route}-kanban.png`));
   out[route] = {options, headers};
  }
  out.crmBoot = await c.evaluate("({New: window.translated_messages.New, Qualification: window.translated_messages.Qualification})");
  fs.writeFileSync(path.join(__dirname,'fd002_labels.json'), JSON.stringify(out,null,2));
  console.log(JSON.stringify(out));
 } finally { await c.close(); }
})().catch(error=>{console.error(error);process.exitCode=1;});
