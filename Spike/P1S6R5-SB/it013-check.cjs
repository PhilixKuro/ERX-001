// R5 IT-013：发票三处裸渲染点逐轮取证。用法：node Spike/P1S6R5-SB/it013-check.cjs <round>
// 每轮：销售、采购各一张列表（徽标）、列表「状态」标准筛选（选项文字＋选中 Unpaid 后的显示）、表单只读 status
const fs = require('node:fs');
const { open } = require('../P1S6R4-cdp.cjs');
const round = process.argv[2] || 'patched';
const OUT = `Spike/P1S6R5-SB/it013/${round}`;
fs.mkdirSync(OUT, { recursive: true });
const CASES = [
  { dt: 'Sales Invoice', slug: 'sales-invoice', form: 'ACC-SINV-2026-00004', rows: ['ACC-SINV-2026-00004', 'ACC-SINV-2026-00002'] },
  { dt: 'Purchase Invoice', slug: 'purchase-invoice', form: 'ACC-PINV-2026-00006', rows: ['ACC-PINV-2026-00006', 'ACC-PINV-2026-00002', 'ACC-PINV-2026-00004'] },
];
(async () => {
  const c = await open();
  const report = { round, cases: [] };
  try {
    report.marks = await c.evaluate(`({select_formatter: String(frappe.form.formatters.Select).includes('parent')})`);
    for (const k of CASES) {
      const row = { doctype: k.dt };
      // 列表徽标
      await c.evaluate(`frappe.set_route('List', ${JSON.stringify(k.dt)}, 'List');true`);
      await c.until(`cur_list?.doctype===${JSON.stringify(k.dt)} && cur_list.data?.length>0 && frappe.request.ajax_count===0`, 30000);
      await c.pause(1200);
      row.wrapped = await c.evaluate(`({indicator: !!frappe.listview_settings[${JSON.stringify(k.dt)}]?.__frappe_china_wrapped, filter: !!frappe.listview_settings[${JSON.stringify(k.dt)}]?.__frappe_china_filter_wrapped, states: (frappe.get_meta(${JSON.stringify(k.dt)}).states||[]).map(s=>s.title+'/'+s.color), status_context: frappe.get_meta(${JSON.stringify(k.dt)}).fields.find(f=>f.fieldname==='status')?.context || null})`);
      row.badges = await c.evaluate(`Object.fromEntries(${JSON.stringify(k.rows)}.map(n => {
        const r = [...document.querySelectorAll('.list-row-container')].find(e => e.querySelector('[data-name="'+n+'"]'));
        const ind = r?.querySelector('.indicator-pill');
        return [n, ind ? {text: ind.innerText.trim(), color: [...ind.classList].filter(x => !['indicator-pill','ellipsis','no-indicator-dot'].includes(x)).join(' '), filter: ind.getAttribute('data-filter')} : null];
      }))`);
      await c.screenshot(`${OUT}/${k.slug}-list.png`);
      // 标准筛选「状态」：控件 df、选项文字，选中 Unpaid 后控件显示
      row.filter = await c.evaluate(`(() => {
        const f = cur_list.page.fields_dict.status; if (!f) return null;
        const opts = [...f.$input[0].options].map(o => ({value: o.value, text: o.text}));
        return {df_context: f.df.context || null, unpaid: opts.find(o => o.value==='Unpaid')?.text, paid: opts.find(o => o.value==='Paid')?.text, overdue: opts.find(o => o.value==='Overdue')?.text};
      })()`);
      await c.evaluate(`cur_list.page.fields_dict.status.set_value('Unpaid');true`);
      await c.pause(1500);
      row.filter_selected = await c.evaluate(`(() => {const s = cur_list.page.fields_dict.status.$input[0]; return {value: s.value, shown: s.options[s.selectedIndex]?.text}})()`);
      await c.screenshot(`${OUT}/${k.slug}-filter.png`);
      await c.evaluate(`cur_list.page.fields_dict.status.set_value('');true`);
      await c.pause(800);
      // 表单只读 status（在「更多信息」页签）与表头徽标
      await c.evaluate(`frappe.set_route('Form', ${JSON.stringify(k.dt)}, ${JSON.stringify(k.form)});true`);
      await c.until(`cur_frm?.doc?.name===${JSON.stringify(k.form)} && frappe.request.ajax_count===0`, 30000);
      await c.pause(1000);
      await c.evaluate(`(() => {const t = document.querySelector('.form-tabs .nav-link[data-fieldname="more_info_tab"]'); if (t) t.click(); return true})()`);
      await c.pause(800);
      row.form = await c.evaluate(`(() => {
        // 隐藏的列表页也留在 DOM 里，故取本表单自己的控件，不用全页选择器
        const ctl = cur_frm.fields_dict.status?.wrapper;
        return {status: cur_frm.doc.status, field: ctl?.querySelector('.control-value')?.innerText.trim() ?? null,
          label: ctl?.querySelector('.control-label')?.innerText.trim() ?? null,
          header: [...cur_frm.page.wrapper[0].querySelectorAll('.page-head .indicator-pill')].map(e => e.innerText.trim()).filter(Boolean)};
      })()`);
      await c.evaluate(`cur_frm.fields_dict.status?.wrapper?.scrollIntoView({block:'center'});true`);
      await c.pause(300);
      await c.screenshot(`${OUT}/${k.slug}-form.png`);
      report.cases.push(row);
    }
  } finally {
    fs.writeFileSync(`${OUT}/result.json`, JSON.stringify(report, null, 2));
    await c.close();
  }
  console.log(JSON.stringify(report));
})().catch(e => { console.error(e); process.exitCode = 1; });
