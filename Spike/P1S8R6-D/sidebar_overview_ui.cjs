const assert = require('node:assert/strict');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');

(async () => {
 const c = await open();
 try {
  assert.equal(await c.evaluate('frappe.boot.sitename'), 'test.localhost');
  await c.send('Emulation.setDeviceMetricsOverride', {width:1500,height:2800,deviceScaleFactor:1,mobile:false});
  await c.navigate(c.base+'/desk/manufacturing-settings/Manufacturing%20Settings?sidebar=Business%20Flow');
  await c.until("window.cur_frm?.doctype==='Manufacturing Settings' && frappe.app.sidebar.sidebar_title==='Business Flow' && !frappe.request.ajax_count",30000);
  assert.equal(await c.evaluate('frappe.boot.sitename'), 'test.localhost');
  const labels = await c.evaluate("Array.from(document.querySelectorAll('.body-sidebar a[href]')).map(x=>x.innerText.trim())");
  for (const label of ['假期列表','质检参数','质检模板','批号','薪资结构','薪资结构分配','库存设置','生产设置','补货建议','供应商评分卡','计件汇总单','产能负荷','过程统计控制图','过程控制图','补货策略对比']) {
   assert(labels.includes(label),label);
  }
  await c.send('Page.bringToFront');
  await c.pause(800);
  await c.screenshot(path.join(__dirname,'SL009-sidebar-overview.png'));
  console.log(JSON.stringify({site:'test.localhost',all15:true,labels}));
 } finally {await c.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
