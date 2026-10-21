const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');
const root = path.join(__dirname, '../../frappe-bench/logs');
const fixture = JSON.parse(fs.readFileSync(path.join(root, 's8-strategy-ui-fixture.json'), 'utf8'));

(async () => {
 const c = await open();
 const result = {site: 'test.localhost'};
 try {
  assert.equal(await c.evaluate('frappe.boot.sitename'), fixture.site);
  await c.navigate(c.base+'/desk/query-report/Replenishment%20Strategy%20Comparison');
  await c.until("window.frappe?.boot?.sitename==='test.localhost' && document.title==='补货策略对比'",30000);
  await c.until("frappe.query_report?.report_name==='Replenishment Strategy Comparison' && frappe.query_report.filters?.length===8", 30000);
  await c.evaluate('frappe.query_report.set_filter_value(' + JSON.stringify(fixture.filters) + '); true');
  await c.pause(600);
  await c.evaluate('frappe.query_report.refresh(); true');
  await c.until('frappe.query_report.data?.length===3', 30000);
  result.report = await c.evaluate("({columns:frappe.query_report.columns.map(x=>x.label),rows:frappe.query_report.data,chart:frappe.query_report.chart?.data||frappe.query_report.chart_options?.data,prepared:frappe.query_report.report_doc.prepared_report,svg:document.querySelector('.chart-container')?.innerHTML})");
  assert.deepEqual(result.report.columns, ['时间段','起','止','天数','平均库存金额','采购次数','库存相关总成本','缺料次数']);
  assert.deepEqual(result.report.rows.map(x=>x.avg_value), [880,1050,900]);
  assert.deepEqual(result.report.rows.map(x=>x.po_count), [2,1,0]);
  assert.equal(result.report.prepared, 0);
  assert(result.report.svg?.includes('svg'), 'Three-period cost chart must render');
  await c.send('Page.bringToFront');
  await c.until("document.querySelector('.chart-container svg')?.getBoundingClientRect().height > 0 && document.body.innerText.includes('平均库存金额')");
  await c.evaluate('new Promise(resolve=>requestAnimationFrame(()=>requestAnimationFrame(resolve)))');
  await c.pause(800);
  await c.screenshot(path.join(__dirname,'SL009-strategy-comparison.png'));
  delete result.report.svg;
  await c.send('Page.navigate',{url:c.base+'/desk/quotation/new?sidebar=Business%20Flow'});
  await c.until("window.cur_frm?.doctype==='Quotation'",30000);
  assert.equal(await c.evaluate('frappe.boot.sitename'), fixture.site);
  result.quotation = await c.evaluate("({route:frappe.get_route(),sidebar:frappe.app.sidebar?.current_sidebar||frappe.app.sidebar?.sidebar_name,body:document.body.innerText,links:Array.from(document.querySelectorAll('a[href]')).filter(a=>a.closest('.layout-side-section, .workspace-sidebar, .body-sidebar')).map(a=>({text:a.innerText,href:a.getAttribute('href')}))})");
  assert.equal(await c.evaluate('frappe.app.sidebar.sidebar_title'), 'Business Flow');
  await c.pause(500);
  await c.screenshot(path.join(__dirname,'SL009-quotation-business-flow.png'));
  result.opened = [];
  const targets = ['holiday-list','quality-inspection-parameter','quality-inspection-template','batch',
   'replenishment-suggestion','supplier-scorecard','piece-rate-summary',
   'query-report/Capacity Load','query-report/SPC Control Chart','spc-chart',
   'query-report/Replenishment Strategy Comparison','salary-structure','salary-structure-assignment',
   'stock-settings','manufacturing-settings'];
  for (const target of targets) {
   await c.evaluate("frappe.app.sidebar.setup('Business Flow'); true");
   const wanted = '/desk/' + target;
   const click = await c.evaluate('(()=>{const a=Array.from(document.querySelectorAll(\'.body-sidebar a[href]\')).find(a=>decodeURI(a.getAttribute(\'href\')).split(\'/\').slice(0,3).join(\'/\')===' + JSON.stringify(wanted.split('/').slice(0,3).join('/')) + ' && decodeURI(a.getAttribute(\'href\')).startsWith(' + JSON.stringify(wanted) + ')); if(!a) return null;const result={text:a.innerText,href:decodeURI(a.getAttribute(\'href\'))};a.click();return result;})()');
   assert(click, 'Missing actual sidebar link '+target);
   await c.until('decodeURI(location.pathname)===' + JSON.stringify(click.href), 30000);
   await c.until('frappe.after_ajax ? frappe.request.ajax_count===0 : true',30000);
   await c.pause(200);
   const page = await c.evaluate("({route:frappe.get_route(),title:document.title,errors:Array.from(document.querySelectorAll('.msgprint')).filter(x=>x.offsetParent).map(x=>x.innerText)})");
   assert(!page.errors.some(text=>/not found|not permitted|找不到|无权/.test(text)),JSON.stringify(page));
   result.opened.push({target,label:click,...page});
  }
  await c.evaluate("frappe.app.sidebar.setup('Business Flow'); true");
  await c.pause(500);
  await c.screenshot(path.join(__dirname,'SL009-sidebar-overview.png'));
  const sidebar = await c.evaluate("frappe.boot.workspace_sidebar_item?.['Business Flow'] || frappe.boot.workspace_sidebar_items?.['Business Flow'] || null");
  result.sidebar = sidebar;
  fs.writeFileSync(path.join(root,'s8-strategy-sidebar-ui.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify({report:result.report,opened:result.opened}));
 } finally {await c.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
