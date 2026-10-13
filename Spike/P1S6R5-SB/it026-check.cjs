// R5 IT-026 实页取证：总账列内筛选框 title，初次渲染与表头重绘后；OUT 指定输出子目录
const fs = require('node:fs');
const { open } = require('../P1S6R4-cdp.cjs');
const OUT = `Spike/P1S6R5-SB/it026/${process.argv[2] || 'hooked'}`;
fs.mkdirSync(OUT, { recursive: true });
const COMPANY = '_S6R6 测试公司';
(async () => {
  const c = await open();
  const report = { out: OUT };
  try {
    const q = new URLSearchParams({ company: COMPANY, from_date: '2026-10-01', to_date: '2026-10-31', categorize_by: 'Categorize by Voucher (Consolidated)' });
    await c.navigate(`${c.base}/desk/query-report/General Ledger?${q}`);
    await c.until(`frappe.query_report?.report_name==="General Ledger" && !!document.querySelector('.datatable .dt-row-filter input.dt-filter')`, 60000);
    await c.pause(1500);
    const read = `[...document.querySelectorAll('.datatable .dt-row-filter input.dt-filter')].map(e => e.getAttribute('title')).filter(Boolean)`;
    report.lang = await c.evaluate('frappe.boot.lang');
    report.marker = await c.evaluate('!!document.__frappe_china_datatable_titles');
    report.initial = await c.evaluate(read);
    // 表头整块重绘（columnmanager.js:33-46 refreshHeader，排序／移列走的同一处）
    await c.evaluate(`frappe.query_report.datatable.columnmanager.refreshHeader();true`);
    await c.pause(500);
    report.after_refresh = await c.evaluate(read);
    report.same_nodes_replaced = await c.evaluate(`!document.querySelector('.datatable .dt-row-filter input.dt-filter')?.__frappe_china_filter_title === false`);
    // 显示筛选行后截图，悬停提示读数见 json
    await c.evaluate(`frappe.query_report.datatable.columnmanager.toggleFilter(true);true`);
    await c.pause(500);
    await c.screenshot(`${OUT}/general-ledger.png`);
    report.console = c.events.filter(e => e.method === 'Runtime.consoleAPICalled').map(e => e.params.args.map(a => a.value).join(' ')).filter(t => t.includes('[frappe_china]'));
    report.english_left = [...report.initial, ...report.after_refresh].filter(t => t.startsWith('Filter based on')).length;
  } finally {
    fs.writeFileSync(`${OUT}/result.json`, JSON.stringify(report, null, 2));
    await c.close();
  }
  console.log(JSON.stringify(report));
})().catch(e => { console.error(e); process.exitCode = 1; });
