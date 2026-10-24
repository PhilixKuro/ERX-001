const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');
const logdir = path.join(__dirname, '../../frappe-bench/logs');
const evidence = { site: 'erx.localhost', reports: [] };

(async () => {
  const rehearsal = JSON.parse(fs.readFileSync(path.join(logdir, 's8-ts026-erx-full-rehearsal-final.json'), 'utf8'));
  assert.equal(rehearsal.terminal_event.status, 'done');
  const c = await open('http://erx.localhost:8000');
  const api = (method, args = {}) => c.evaluate('frappe.xcall(' + JSON.stringify(method) + ', ' + JSON.stringify(args) + ')');
  try {
    await c.until('!!window.frappe_debug?.demo?.config', 60000);
    assert.equal(await c.evaluate('frappe.boot.sitename'), evidence.site);
    assert.equal(await c.evaluate('frappe.session.user'), 'Administrator');
    const initial = await api('frappe_debug.demo.snapshot.snapshot_status');
    assert.equal(initial.base_db, rehearsal.final_readback.snapshots.base_db);
    evidence.base_db = initial.base_db;
    let currentProgress = await api('frappe_debug.demo.progress.get_progress');
    for (const act of [7, 8]) {
      if (currentProgress.act !== act) {
        await c.evaluate('window.__lg001_departing = true');
        try { await c.evaluate('frappe_debug.demo.switch_act(' + act + ', "jump")'); }
        catch (error) { if (!/context|navigat/i.test(error.message)) throw error; }
        await c.until('!window.__lg001_departing && !!window.frappe_debug?.demo?.config && !location.pathname.includes("/assets/")', 120000);
      }
      assert.equal(await c.evaluate('frappe.boot.sitename'), evidence.site);
      const status = await api('frappe_debug.demo.switch.switch_status');
      assert.equal(status.user, 'Administrator');
      assert([initial.base_db + '_a' + act + '_m', initial.base_db + '_a' + act + '_b'].includes(status.db));
      const progress = await api('frappe_debug.demo.progress.get_progress');
      assert.equal(progress.act, act);
      assert.equal(progress.step, 0);
      currentProgress = progress;
      const filters = await api('frappe_debug.demo.functions.previous_month_filters', {as_of_date: progress.scene_date, company: '华东弹簧有限公司'});
      delete filters.period_type;
      const closing = await api('frappe.client.get_list', {doctype: 'Month End Closing Voucher', filters: {...filters, docstatus: 1}, fields: ['name', 'fiscal_year', 'month', 'docstatus']});
      const year = Number(filters.fiscal_year);
      const monthEnd = new Date(year, Number(filters.month), 0).toISOString().slice(0, 10);
      const mappedNumbers = ['1400', '4001', '400101', '400102', '400103', '400199', '4101', '410103', '410199', '4401', '4403'];
      const mappedAccounts = await api('frappe.client.get_list', {doctype: 'Account', filters: {company: '华东弹簧有限公司', account_number: ['in', mappedNumbers]}, fields: ['name', 'account_number', 'account_name', 'is_group', 'root_type', 'account_type'], limit_page_length: 100});
      const glBalances = [];
      const relevantAccount = mappedAccounts.find(account => String(account.account_number) === '410199');
      const costEntries = [];
      for (let start = 0; ; start += 5000) {
        const entries = await api('frappe.client.get_list', {doctype: 'GL Entry', filters: {company: '华东弹簧有限公司', posting_date: ['<=', monthEnd], is_cancelled: 0, account: ['in', mappedAccounts.map(account => account.name)]}, fields: ['account', 'debit', 'credit', 'posting_date', 'voucher_type', 'voucher_no'], limit_start: start, limit_page_length: 5000, order_by: 'name asc'});
        for (const entry of entries) {
          const balance = glBalances.find(item => item.account === entry.account);
          if (balance) {
            balance.debit += Number(entry.debit || 0);
            balance.credit += Number(entry.credit || 0);
          } else {
            glBalances.push({account: entry.account, debit: Number(entry.debit || 0), credit: Number(entry.credit || 0)});
          }
          if (entry.account === relevantAccount?.name) costEntries.push(entry);
        }
        if (entries.length < 5000) break;
      }
      const costBySource = new Map();
      const costByVoucher = new Map();
      for (const entry of costEntries) {
        const key = `${entry.posting_date.slice(0, 7)} ${entry.voucher_type}`;
        const amount = costBySource.get(key) || {period: entry.posting_date.slice(0, 7), voucher_type: entry.voucher_type, debit: 0, credit: 0, vouchers: new Set()};
        amount.debit += Number(entry.debit || 0);
        amount.credit += Number(entry.credit || 0);
        amount.vouchers.add(entry.voucher_no);
        costBySource.set(key, amount);
        const voucher = costByVoucher.get(entry.voucher_no) || {name: entry.voucher_no, posting_date: entry.posting_date, debit: 0, credit: 0};
        voucher.debit += Number(entry.debit || 0);
        voucher.credit += Number(entry.credit || 0);
        costByVoucher.set(entry.voucher_no, voucher);
      }
      const costExamples = [...costByVoucher.values()].sort((a,b) => b.credit - a.credit).slice(0, 30);
      const stockEntries = await api('frappe.client.get_list', {doctype: 'Stock Entry', filters: {name: ['in', costExamples.map(entry => entry.name)]}, fields: ['name', 'purpose', 'fg_completed_qty', 'total_outgoing_value', 'total_incoming_value', 'total_additional_costs'], limit_page_length: 100});
      const largestStockEntry = stockEntries.sort((a,b) => Number(b.total_additional_costs || 0) - Number(a.total_additional_costs || 0))[0];
      const stockEntryDetail = largestStockEntry ? await api('frappe.client.get', {doctype: 'Stock Entry', name: largestStockEntry.name}) : null;
      const workOrderDetail = stockEntryDetail?.work_order ? await api('frappe.client.get', {doctype: 'Work Order', name: stockEntryDetail.work_order}) : null;
      const workstationNames = [...new Set((workOrderDetail?.operations || []).map(operation => operation.workstation).filter(Boolean))];
      const workstationDetails = [];
      for (const name of workstationNames) workstationDetails.push(await api('frappe.client.get', {doctype: 'Workstation', name}));
      const bomDetail = workOrderDetail?.bom_no ? await api('frappe.client.get', {doctype: 'BOM', name: workOrderDetail.bom_no}) : null;
      await c.evaluate('frappe_debug.demo.actions.open_report({report:"小企业资产负债表", filters:' + JSON.stringify(filters) + ', timeout:60})');
      await c.until('frappe.query_report?.report_name === "小企业资产负债表" && frappe.query_report.raw_data?.result?.length > 0 && frappe.request.ajax_count === 0', 60000);
      const data = await c.evaluate('({filters:frappe.query_report.get_filter_values(), raw:frappe.query_report.raw_data, text:document.body.innerText})');
      assert.equal(String(data.filters.month), String(filters.month));
      assert.equal(data.filters.fiscal_year, filters.fiscal_year);
      const rows = data.raw.result.filter(row => [9,10,11,12,13].includes(Number(row.a_no)));
      assert.equal(rows.length, 5);
      const inventory = rows.find(row => Number(row.a_no) === 9);
      const components = rows.filter(row => Number(row.a_no) !== 9);
      const closeSum = components.reduce((sum, row) => sum + Number(row.a_close || 0), 0);
      const openSum = components.reduce((sum, row) => sum + Number(row.a_open || 0), 0);
      const expected = Number(inventory.a_close || 0) + 0.005 < closeSum || Number(inventory.a_open || 0) + 0.005 < openSum;
      const warning = /勾稽提示：第 9 行/.test(data.raw.message || '');
      assert.equal(warning, expected, 'Inventory warning must match reported amounts');
      const closingNote = /尚未结转/.test(data.raw.message || '');
      assert.equal(closingNote, closing.length === 0, 'Report closing note must match closing voucher records');
      const screenshot = path.join(__dirname, 'acts/acceptance/ts026-erx-act' + act + '-balance-sheet.png');
      await c.screenshot(screenshot);
      evidence.reports.push({act, db:status.db, progress, filters, closing, closing_note:closingNote, rows, components_close:closeSum, components_open:openSum, mapped_accounts: mappedAccounts.map(account => ({...account, ...(glBalances.find(balance => balance.account === account.name) || {debit: 0, credit: 0})})), cost_account_sources: [...costBySource.values()].map(source => ({...source, vouchers: source.vouchers.size})).sort((a,b) => b.credit - a.credit), cost_examples: costExamples.map(entry => ({...entry, ...(stockEntries.find(stock => stock.name === entry.name) || {})})), largest_stock_entry: stockEntryDetail, work_order: workOrderDetail, bom: bomDetail, workstation_details: workstationDetails, ph_p1039:warning, message:data.raw.message || null, report_summary:data.raw.report_summary, screenshot, observed_at:new Date().toISOString()});
      fs.writeFileSync(path.join(logdir, 's8-ts026-erx-balance-sheet.json'), JSON.stringify(evidence, null, 2));
      console.log(JSON.stringify({act, db:status.db, filters, ph_p1039:warning, message:data.raw.message || null}));
    }
    console.log('PASS both snapshot balance sheets inspected');
  } finally { await c.close(); }
})().catch(error => { console.error(error); process.exitCode = 1; });
