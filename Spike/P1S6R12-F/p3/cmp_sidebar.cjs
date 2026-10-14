// P1-S6-R12 F 分片 3：只读比对 business_flow.json ↔ 方案 Part3 TS-010 第 2 步表 ↔ 演示站库内条目
const fs = require('node:fs');
const path = require('node:path');
const json = JSON.parse(fs.readFileSync('D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/workspace_sidebar/business_flow.json', 'utf8'));
const plan = [
  ['S', 'Master Data'], ['DocType', 'Company', 'Company'], ['DocType', 'Global Defaults', 'Global Defaults'], ['DocType', 'Fiscal Year', 'Fiscal Year'],
  ['DocType', 'Chart of Accounts', 'Account'], ['DocType', 'Cost Center', 'Cost Center'], ['DocType', 'Warehouse', 'Warehouse'],
  ['DocType', 'Unit of Measure (UOM)', 'UOM'], ['DocType', 'Item', 'Item'], ['DocType', 'Item Price', 'Item Price'], ['DocType', 'Workstation', 'Workstation'],
  ['DocType', 'Operation', 'Operation'], ['DocType', 'Routing', 'Routing'], ['DocType', 'BOM', 'BOM'], ['DocType', 'Customer', 'Customer'],
  ['DocType', 'Supplier', 'Supplier'], ['DocType', 'Employee', 'Employee'],
  ['S', 'Selling'], ['URL', 'Leads', '/crm/leads'], ['URL', 'Deals', '/crm/deals'], ['URL', 'Dashboard', '/crm/dashboard'],
  ['DocType', 'Quotation', 'Quotation'], ['DocType', 'Sales Order', 'Sales Order'], ['DocType', 'Delivery Note', 'Delivery Note'], ['DocType', 'Sales Invoice', 'Sales Invoice'],
  ['S', 'Buying'], ['DocType', 'Material Request', 'Material Request'], ['DocType', 'Supplier Quotation', 'Supplier Quotation'], ['DocType', 'Purchase Order', 'Purchase Order'],
  ['DocType', 'Purchase Receipt', 'Purchase Receipt'], ['DocType', 'Purchase Invoice', 'Purchase Invoice'],
  ['S', 'Stock'], ['DocType', 'Stock Reconciliation', 'Stock Reconciliation'], ['DocType', 'Quality Inspection', 'Quality Inspection'],
  ['S', 'Manufacturing'], ['DocType', 'Production Plan', 'Production Plan'], ['DocType', 'Work Order', 'Work Order'], ['DocType', 'Stock Entry', 'Stock Entry'], ['DocType', 'Job Card', 'Job Card'],
  ['S', 'Finance'], ['DocType', 'Payment Entry', 'Payment Entry'], ['DocType', 'Journal Entry', 'Journal Entry'], ['Report', 'Accounts Receivable', 'Accounts Receivable'],
  ['Report', 'Accounts Payable', 'Accounts Payable'], ['DocType', 'Month End Closing Voucher', 'Month End Closing Voucher'], ['DocType', 'Cash Flow Worksheet', 'Cash Flow Worksheet'],
  ['DocType', 'Bank Statement Preprocess', 'Bank Statement Preprocess'],
  ['S', 'Reports'], ['Report', '小企业资产负债表', '小企业资产负债表'], ['Report', '小企业利润表', '小企业利润表'], ['Report', '小企业现金流量表', '小企业现金流量表'],
  ['Report', '漏科目检查', '漏科目检查'], ['Report', 'General Ledger', 'General Ledger'], ['Report', 'Stock Ledger', 'Stock Ledger'], ['Report', 'Stock Balance', 'Stock Balance'],
  ['Report', 'Stock and Account Value Comparison', 'Stock and Account Value Comparison'], ['Report', 'BOM Variance Report', 'BOM Variance Report'], ['URL', 'AI Assistant', '/raven'],
];
const out = [];
if (plan.length !== json.items.length) out.push(`plan ${plan.length} vs json ${json.items.length}`);
json.items.forEach((it, i) => {
  const p = plan[i];
  if (!p) return;
  if (p[0] === 'S') {
    const ok = it.type === 'Section Break' && it.label === p[1] && it.link_type === 'DocType' && it.child === 0 && it.indent === 1 && it.collapsible === 1 && it.keep_closed === 0;
    if (!ok) out.push(`#${i + 1} section mismatch ${JSON.stringify(it)}`);
  } else {
    const target = p[0] === 'URL' ? it.url : it.link_to;
    const ok = it.type === 'Link' && it.label === p[1] && it.link_type === p[0] && target === p[2] && it.child === 1 && it.indent === 0 && it.collapsible === 1 && it.keep_closed === 0
      && !('filters' in it) && !('route_options' in it) && (p[0] === 'URL' ? !('link_to' in it) : !('url' in it));
    if (!ok) out.push(`#${i + 1} link mismatch ${JSON.stringify(it)} vs ${JSON.stringify(p)}`);
  }
});
// 库内比对
const tsv = fs.readFileSync(path.join(__dirname, 'demo_items.tsv'), 'utf8').trim().split(/\r?\n/).slice(1).map(l => l.split('\t'));
if (tsv.length !== json.items.length) out.push(`db ${tsv.length} vs json ${json.items.length}`);
tsv.forEach((r, i) => {
  const it = json.items[i] || {};
  const [idx, type, label, lt, link_to, url, child, indent, coll, kc, icon, ro, filters] = r;
  const exp = [String(i + 1), it.type, it.label, it.link_type, it.link_to || '', it.url || '', String(it.child), String(it.indent), String(it.collapsible), String(it.keep_closed), it.icon || '', '', ''];
  const got = [idx, type, label, lt, link_to, url, child, indent, coll, kc, icon, ro === 'NULL' ? '' : ro, filters === 'NULL' ? '' : filters];
  if (JSON.stringify(exp) !== JSON.stringify(got)) out.push(`db row ${i + 1}: ${JSON.stringify(got)} vs ${JSON.stringify(exp)}`);
});
const links = json.items.filter(i => i.type === 'Link');
console.log(JSON.stringify({ items: json.items.length, links: links.length, sections: json.items.length - links.length,
  by_type: links.reduce((a, l) => (a[l.link_type] = (a[l.link_type] || 0) + 1, a), {}),
  doctypes: links.filter(l => l.link_type === 'DocType').map(l => l.link_to),
  reports: links.filter(l => l.link_type === 'Report').map(l => l.link_to),
  problems: out }, null, 1));
