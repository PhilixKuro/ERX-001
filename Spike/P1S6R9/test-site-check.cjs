// R9 TS-035 测试站实页核：九屏截图 + 每屏一行读数，另核 HT-021（补丁标记、无告警）。
// 用法：node Spike/P1S6R9/test-site-check.cjs [baseUrl] [outDir]
//   默认 http://test.localhost:6787、Spike/P1S6R9/test-site/
//   SCREENS_ONLY=1,3,5 只跑这几屏（撤钩反证用）
// 登录与截图沿用 Spike/P1S6R4-cdp.cjs。第 2 屏须先跑 ts035-data.py setup。
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');

const base = process.argv[2] || 'http://test.localhost:6787';
const outDir = process.argv[3] || path.join(__dirname, 'test-site');
const only = process.env.SCREENS_ONLY ? new Set(process.env.SCREENS_ONLY.split(',').map(s => s.trim())) : null;
fs.mkdirSync(outDir, {recursive: true});
const js = v => JSON.stringify(v);
const COMPANY = '_S6R6 测试公司';

// 可见元素查找（同 P1S6R6-screen-check.js 的 findExpr）
function findExpr(selector, text) {
  const texts = text == null ? null : (Array.isArray(text) ? text : [text]);
  return `(() => {
    const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
    const all = [...document.querySelectorAll(${js(selector)})].filter(vis);
    const texts = ${js(texts)};
    if (!texts) return all.at(-1) || null;
    const label = e => (e.innerText || e.textContent || '').replace(/\\s+/g, ' ').trim();
    for (const t of texts) { const hit = all.find(e => label(e) === t); if (hit) return hit; }
    for (const t of texts) { const hit = all.find(e => label(e).includes(t)); if (hit) return hit; }
    return null;
  })()`;
}
async function click(c, selector, text, {timeout = 30000, real = false} = {}) {
  const expr = findExpr(selector, text);
  await c.until(`!!${expr}`, timeout);
  if (!real) { await c.evaluate(`(() => { const e = ${expr}; e.scrollIntoView({block: 'center'}); e.click(); return true; })()`); return; }
  const box = await c.evaluate(`(() => { const e = ${expr}; e.scrollIntoView({block: 'center'}); const r = e.getBoundingClientRect(); return {x: r.left + r.width / 2, y: r.top + r.height / 2}; })()`);
  for (const type of ['mouseMoved', 'mousePressed', 'mouseReleased'])
    await c.send('Input.dispatchMouseEvent', {type, x: box.x, y: box.y, button: 'left', clickCount: 1});
}
const formReady = doctype => `window.cur_frm?.doctype===${js(doctype)} && !cur_frm.is_new?.() && !!cur_frm.fields_dict && !frappe.dom.freeze_count`;
const settle = c => c.pause(1500);

const screens = [
  {id: '1', name: 'work-order-list-filter', async run(c) {
    await c.navigate(`${base}/desk/work-order?company=${encodeURIComponent(COMPANY)}`);
    await c.until(`cur_list?.doctype==="Work Order" && !!document.querySelector('.list-row-container, .no-result') && cur_list.filter_area?.get?.().length===1`);
    await settle(c);
    return c.evaluate(`({
      filter_count: cur_list.filter_area.get().length,
      filter_button_title: document.querySelector('.filter-selector .filter-button')?.getAttribute('title'),
      filter_button_class_primary_light: document.querySelector('.filter-selector .filter-button')?.classList.contains('btn-primary-light'),
      subject_sort_title: document.querySelector('.list-row-head [data-sort-by]')?.getAttribute('title'),
      subject_label: document.querySelector('.list-row-head [data-sort-by]')?.innerText.trim(),
    })`);
  }},
  {id: '2', name: 'purchase-invoice-create-menu', async run(c) {
    await c.navigate(`${base}/desk/purchase-invoice/ACC-PINV-2026-00006`);
    await c.until(formReady('Purchase Invoice'));
    const groups = ['Create', '创建'].map(g => `.page-actions .inner-group-button[data-label="${encodeURIComponent(g)}"] > button`).join(',');
    await c.until(`!!document.querySelector('.page-actions .inner-group-button .dropdown-item[data-label="${encodeURIComponent('公司间销售发票')}"], .page-actions .inner-group-button .dropdown-item[data-label="Inter%20Company%20Invoice"]')`, 30000).catch(() => {});
    await click(c, groups);
    await c.until(`!!document.querySelector('.page-actions .inner-group-button .dropdown-menu.show')`);
    await settle(c);
    return c.evaluate(`({
      items: [...document.querySelectorAll('.page-actions .inner-group-button .dropdown-menu.show .dropdown-item')].map(e => ({text: e.innerText.trim(), data_label: decodeURIComponent(e.getAttribute('data-label') || '')})),
      mobile_menu: [...document.querySelectorAll('.page-actions .menu-btn-group .dropdown-item, .standard-actions .dropdown-item')].map(e => e.innerText.trim()).filter(t => t.includes('>')),
    })`);
  }},
  {id: '3a', name: 'general-ledger', async run(c) {
    const q = new URLSearchParams({company: COMPANY, from_date: '2026-10-01', to_date: '2026-10-31', categorize_by: 'Categorize by Voucher (Consolidated)'});
    await c.navigate(`${base}/desk/query-report/General Ledger?${q}`);
    await c.until(`frappe.query_report?.report_name==="General Ledger" && (frappe.query_report.data||[]).length>0 && !!document.querySelector('.dt-scrollable .dt-row')`, 60000);
    await settle(c);
    return reportReadout(c, ['voucher_type', 'against_voucher_type', 'party_type']);
  }},
  {id: '3b', name: 'stock-ledger', async run(c) {
    const q = new URLSearchParams({company: COMPANY, from_date: '2026-10-01', to_date: '2026-10-31'});
    await c.navigate(`${base}/desk/query-report/Stock Ledger?${q}`);
    await c.until(`frappe.query_report?.report_name==="Stock Ledger" && (frappe.query_report.data||[]).length>0 && !!document.querySelector('.dt-scrollable .dt-row')`, 60000);
    await settle(c);
    return reportReadout(c, ['voucher_type']);
  }},
  {id: '4', name: 'timeline-empty', async run(c) {
    await c.navigate(`${base}/desk/work-order/MFG-WO-2026-00003`);
    await c.until(formReady('Work Order'));
    await c.until(`!!document.querySelector('.new-timeline .timeline-content b')`, 30000);
    await settle(c);
    await c.evaluate(`(() => { const e = [...document.querySelectorAll('.new-timeline .timeline-content')].find(n => /计划结束日期|planned/i.test(n.innerText)) || document.querySelector('.new-timeline'); e.scrollIntoView({block: 'center'}); return true; })()`);
    await c.pause(500);
    return c.evaluate(`(() => {
      const bolds = [...document.querySelectorAll('.new-timeline .timeline-content b')].map(b => b.textContent);
      const row = [...document.querySelectorAll('.new-timeline .timeline-content')].map(n => n.innerText.replace(/\\s+/g, ' ').trim()).find(t => t.includes('（空）'));
      return {empty_count: bolds.filter(t => t === '（空）').length, null_count: bolds.filter(t => t === 'null' || t === 'undefined').length, sample_row: row || null};
    })()`);
  }},
  {id: '5', name: 'fetch-timesheet-dialog', async run(c) {
    await c.navigate(`${base}/desk/sales-invoice/ACC-SINV-2026-00003`);
    await c.until(formReady('Sales Invoice'));
    const group = await c.evaluate(`__("Get Items From")`);
    const sel = [group, 'Get Items From'].map(g => `.page-actions .inner-group-button[data-label="${encodeURIComponent(g)}"] > button`).join(',');
    await click(c, sel);
    await c.until(`!!document.querySelector('.page-actions .inner-group-button .dropdown-menu.show')`);
    await click(c, '.page-actions .inner-group-button .dropdown-menu.show .dropdown-item', [await c.evaluate(`__("Timesheet")`), 'Timesheet']);
    await c.until(`!!document.querySelector('.modal.show [data-fieldname="from_time"]')`);
    await settle(c);
    return c.evaluate(`(() => {
      const label = f => document.querySelector('.modal.show .frappe-control[data-fieldname="' + f + '"] .control-label')?.innerText.trim();
      return {title: document.querySelector('.modal.show .modal-title')?.innerText.trim(), from_time: label('from_time'), to_time: label('to_time'), item_code: label('item_code'), project: label('project')};
    })()`);
  }, cleanup: c => c.evaluate(`document.querySelectorAll('.modal.show .btn-modal-close').forEach(b => b.click()); true`)},
  {id: '6a', name: 'raven-profile-status', async run(c) {
    // 桌面版无 /raven/profile 路由（那是移动端页），设置对话框经头像菜单 → 设置打开（NavUserMenu.tsx:104）
    await c.navigate(`${base}/raven`);
    await c.until(`!!document.body.innerText.trim() && !document.querySelector('.animate-spin') && !!document.querySelector('[data-sidebar] button, aside button, nav button')`, 60000);
    await settle(c);
    const avatar = await c.evaluate(`(() => {
      const btns = [...document.querySelectorAll('button')].filter(b => b.querySelector('img, [class*="avatar" i], span[class*="rounded"]'));
      const vis = b => { const r = b.getBoundingClientRect(); return r.width > 0 && r.left < 80; };
      const hit = btns.filter(vis).sort((a, b) => b.getBoundingClientRect().top - a.getBoundingClientRect().top)[0];
      if (!hit) return null; hit.setAttribute('data-ts035', 'avatar'); return true;
    })()`);
    if (!avatar) throw Error('Raven avatar button not found');
    await click(c, 'button[data-ts035="avatar"]', null, {real: true});
    await c.until(`!!document.querySelector('[role="menuitem"]')`, 10000);
    // 用户菜单里的状态子菜单（StatusSubMenu）
    await click(c, '[role="menuitem"]', [await c.evaluate(`frappe._messages?.["Status"] || "Status"`), 'Status'], {real: true});
    await c.until(`!!document.querySelector('[role="menuitemradio"]')`, 10000).catch(() => {});
    await c.pause(500);
    const menu_status = await c.evaluate(`[...document.querySelectorAll('[role="menuitemradio"]')].map(e => e.innerText.trim())`);
    await c.screenshot(path.join(outDir, '6a-raven-user-menu-status.png'));
    await click(c, '[role="menuitem"]', [await c.evaluate(`frappe._messages?.["Settings"] || "Settings"`), 'Settings'], {real: true});
    await c.until(`!!document.querySelector('[role="dialog"] button[role="combobox"]')`, 20000);
    await settle(c);
    const before = {menu_status, ...await c.evaluate(`({messages_available: frappe._messages?.["Available"], context_row: frappe._messages?.["Available:Raven User"], trigger: document.querySelector('[role="dialog"] button[role="combobox"]')?.innerText.trim()})`)};
    await click(c, '[role="dialog"] button[role="combobox"]', null, {real: true});
    await c.until(`!!document.querySelector('[role="option"]')`, 10000);
    await c.pause(500);
    const options = await c.evaluate(`[...document.querySelectorAll('[role="option"]')].map(e => e.innerText.trim())`);
    return {...before, options};
  }, cleanup: c => c.send('Input.dispatchKeyEvent', {type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27})},
  {id: '6b', name: 'desk-raven-user-form', async run(c) {
    await c.navigate(`${base}/desk/raven-user/Administrator`);
    await c.until(formReady('Raven User'));
    await c.evaluate(`(() => { const f = cur_frm.fields_dict.availability_status; f.wrapper.scrollIntoView({block: 'center'}); return true; })()`);
    await settle(c);
    return c.evaluate(`({
      options: [...(cur_frm.fields_dict.availability_status.$input?.[0]?.options || [])].map(o => ({value: o.value, text: o.text})),
      formatter_available: frappe.format("Available", {fieldtype: "Select", parent: "Raven User", options: "\\nAvailable"}),
      plain_available: __("Available"),
    })`);
  }},
  {id: '7a', name: 'crm-dashboard', async run(c) {
    await c.navigate(`${base}/crm/dashboard`);
    // frappe-ui ECharts.vue:27 用 svg 渲染器，轴标签是 svg <text>
    await c.until(`!!document.body.innerText.trim() && !document.querySelector('.animate-spin, .loading-indicator') && !!document.querySelector('[_echarts_instance_] svg text')`, 60000);
    await c.pause(3000);
    return c.evaluate(`(() => {
      const charts = [...document.querySelectorAll('[_echarts_instance_]')];
      const texts = charts.flatMap(el => [...el.querySelectorAll('svg text')].map(t => t.textContent.trim())).filter(Boolean);
      const monthish = texts.filter(t => /[A-Z][a-z]{2}|\\d+月/.test(t));
      return {html_lang: document.documentElement.lang, echarts_charts: charts.length, axis_month_like: [...new Set(monthish)].slice(0, 12),
        english_month_abbr: [...new Set(texts.filter(t => /\\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\\b/.test(t)))],
        empty_texts: [...document.querySelectorAll('[class*="min-h-[300px]"] *, [class*="max-h-[140px]"] *')].map(e => e.childNodes.length === 1 && e.firstChild.nodeType === 3 ? e.textContent.trim() : '').filter(t => /^(Empty|空)( \\(|$)/.test(t)).slice(0, 5)};
    })()`);
  }},
  {id: '7b', name: 'crm-leads-list', async run(c) {
    await c.navigate(`${base}/crm/leads`);
    await c.until(`!!document.body.innerText.trim() && !document.querySelector('.animate-spin, .loading-indicator')`, 60000);
    await c.pause(2500);
    return c.evaluate(`(() => {
      const divs = [...document.querySelectorAll('div')].filter(d => d.children.length === 3 && /^[\\d,]+$/.test(d.children[0].textContent.trim()) && /^[\\d,]+$/.test(d.children[2].textContent.trim()));
      return {pager: divs.map(d => [...d.children].map(x => x.textContent.trim()).join(' ')).slice(0, 3),
        load_more: [...document.querySelectorAll('button')].map(b => b.textContent.trim()).filter(t => t === 'Load More' || t === '加载更多')};
    })()`);
  }},
  {id: '7c', name: 'crm-lead-detail-sidepanel', async run(c) {
    await c.navigate(`${base}/crm/leads/CRM-LEAD-2026-00001`);
    await c.until(`!!document.querySelector('.sections.flex.flex-col.overflow-y-auto')`, 60000);
    await c.pause(2500);
    return c.evaluate(`(() => {
      const panel = document.querySelector('.sections.flex.flex-col.overflow-y-auto');
      const texts = [], walker = document.createTreeWalker(panel, NodeFilter.SHOW_TEXT);
      let n; while ((n = walker.nextNode())) { const t = n.nodeValue.trim(); if (t.endsWith('...') || t.endsWith('……')) texts.push(t); }
      const placeholders = [...panel.querySelectorAll('[placeholder]')].map(e => e.getAttribute('placeholder')).filter(Boolean);
      return {placeholder_texts: [...new Set(texts)], placeholder_attrs: [...new Set(placeholders)], english_left: [...new Set([...texts, ...placeholders])].filter(t => /^(Add|Select) /.test(t))};
    })()`);
  }},
  {id: '8', name: 'contact-salutation', async run(c) {
    await c.navigate(`${base}/desk/contact/CRM Administrator`);
    await c.until(formReady('Contact'));
    await c.evaluate(`(() => { const f = cur_frm.fields_dict.salutation; f.wrapper.scrollIntoView({block: 'center'}); f.$input.focus(); f.$input.val(''); f.$input.trigger('input'); return true; })()`);
    // awesomplete 的下拉项是 ul 里的 li（link.js:265 起，项内 div[role=option]）
    const ITEMS = `.frappe-control[data-fieldname="salutation"] .awesomplete ul [role="option"]`;
    await c.until(`document.querySelectorAll(${js(ITEMS)}).length >= 5`, 15000);
    await c.pause(800);
    return c.evaluate(`(() => {
      const options = [...document.querySelectorAll(${js(ITEMS)})].map(li => (li.querySelector("strong")?.innerText || li.innerText).split('\\n')[0].trim()).filter(t => t && !/^(创建|高级搜索|Create|Advanced)/.test(t));
      return {options, duplicates: options.filter((t, i) => options.indexOf(t) !== i)};
    })()`);
  }, cleanup: c => c.evaluate(`cur_frm?.fields_dict?.salutation?.$input?.blur(); true`)},
  {id: '9', name: 'workstation-available', async run(c) {
    await c.navigate(`${base}/desk/workstation/_S6R6 验收工站`);
    await c.until(formReady('Workstation'));
    await settle(c);
    // 无 context 的 Available 唯一演示面渲染点是 workstation.js:513（原料对话框列标签，须有进行中的作业卡）；
    // 此处读同一调用 __("Available") 的结果，并与 Raven User 的 context 行对照
    return c.evaluate(`({plain_available: __("Available"), raven_context: __("Available", null, "Raven User"), workstation_status_options: (cur_frm.fields_dict.status?.df.options || '').split('\\n').map(o => __(o, null, 'Workstation'))})`);
  }},
];

async function reportReadout(c, fields) {
  return c.evaluate(`(() => {
    // datatable 的 colIndex 含行号、勾选列，且隐藏列不渲染，故按 datatable 自己的列表找下标
    const dtCols = frappe.query_report.datatable.getColumns();
    const colIndex = f => dtCols.find(c => (c.docfield?.fieldname || c.id) === f)?.colIndex;
    const out = {};
    for (const f of ${js(fields)}) {
      const i = colIndex(f);
      if (i == null) { out[f] = 'column missing'; continue; }
      const cells = [...document.querySelectorAll('.dt-scrollable .dt-cell[data-col-index="' + i + '"] .dt-cell__content')].map(e => e.innerText.trim()).filter(Boolean);
      out[f] = {shown: [...new Set(cells)].slice(0, 8), data: [...new Set(frappe.query_report.data.map(r => r[f]).filter(Boolean))].slice(0, 8)};
    }
    const vn = colIndex('voucher_no');
    const link = vn == null ? null : document.querySelector('.dt-scrollable .dt-cell[data-col-index="' + vn + '"] a[href]');
    out.voucher_no_href = link?.getAttribute('href') || null;
    return out;
  })()`);
}

(async () => {
  const c = await open(base);
  const results = [];
  try {
    const marks = await c.evaluate(`({
      boot_lang: frappe.boot.lang,
      filter_title: !!frappe.ui.FilterGroup?.prototype.update_filter_button?.__frappe_china_filter_title,
      sort_title: !!frappe.views.ListView?.prototype.get_header_html?.__frappe_china_sort_title,
      group_label: !!frappe.ui.Page?.prototype.add_inner_button?.__frappe_china_group_label,
      doctype_columns: !!frappe.views.QueryReport?.prototype.prepare_columns?.__frappe_china_doctype_columns,
      dialog_labels: !!frappe.ui.Dialog?.prototype.make?.__frappe_china_dialog_labels,
      timeline_observer: !!document.__frappe_china_timeline_nulls,
      desk_patches_loaded: [...document.scripts].some(s => /desk_patches/.test(s.src)),
    })`);
    results.push({id: 'HT-021-marks', readout: marks});
    console.log(JSON.stringify(results[0]));
    for (const screen of screens) {
      if (only && !only.has(screen.id) && !only.has(screen.id.replace(/[a-z]$/, ''))) continue;
      const row = {id: screen.id, name: screen.name, screenshot: `${screen.id}-${screen.name}.png`};
      try { row.readout = await screen.run(c); }
      catch (error) { row.error = String(error.message || error).slice(0, 400); }
      try { await c.screenshot(path.join(outDir, row.screenshot)); } catch (error) { row.screenshot_error = String(error); }
      if (screen.cleanup) try { await screen.cleanup(c); } catch {}
      results.push(row);
      console.log(JSON.stringify(row));
    }
    const warnings = c.events.filter(e => e.method === 'Runtime.consoleAPICalled' && ['warning', 'error'].includes(e.params.type))
      .map(e => ({type: e.params.type, text: e.params.args.map(a => a.value ?? a.description ?? '').join(' ').slice(0, 300)}));
    const china = warnings.filter(w => w.text.includes('[frappe_china]'));
    results.push({id: 'console', frappe_china_warnings: china, other_warning_count: warnings.length - china.length});
    console.log(JSON.stringify(results.at(-1)));
  } finally {
    fs.writeFileSync(path.join(outDir, process.env.RESULT_NAME || 'result.json'), JSON.stringify({base, browser: c.browser, at: new Date().toISOString(), results}, null, 1));
    c.close();
  }
})().catch(error => { console.error(error); process.exitCode = 1; });
