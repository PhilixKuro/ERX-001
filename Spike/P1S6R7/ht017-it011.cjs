// TS-019 第 6、7 步：测试站实看 HT-017（带尾空格的 label）与 IT-011（Dr 称谓下拉）。
// node Spike/P1S6R7/ht017-it011.cjs   （测试站须已在 6787 起 serve）
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');

const out = path.join(__dirname, 'ht017-it011');
fs.mkdirSync(out, { recursive: true });

(async () => {
	const c = await open('http://test.localhost:6787');
	const result = {};
	try {
		// HT-017：Accounts Settings 的 role_allowed_to_over_bill 字段 label
		await c.navigate(`${c.base}/desk/accounts-settings`);
		await c.until('!!(window.cur_frm && cur_frm.doctype === "Accounts Settings" && cur_frm.fields_dict.role_allowed_to_over_bill)', 30000);
		result.ht017 = await c.evaluate(`(() => {
			const f = cur_frm.fields_dict.role_allowed_to_over_bill;
			const tab = f.tab && f.tab.label;
			return { lang: frappe.boot.lang, df_label: f.df.label, shown: f.$wrapper.find('.control-label').first().text().trim(), tab };
		})()`);
		await c.evaluate(`(() => {
			const f = cur_frm.fields_dict.role_allowed_to_over_bill;
			if (f.tab) f.tab.set_active();
			f.$wrapper[0].scrollIntoView({ block: 'center' });
			f.$wrapper[0].style.outline = '3px solid red';
		})()`);
		await c.pause(800);
		await c.screenshot(path.join(out, 'ht017-accounts-settings.png'));

		// IT-011：任意带 salutation Link 的表单，下拉搜 Dr，看显示
		await c.navigate(`${c.base}/desk/contact/new`);
		await c.until('!!(window.cur_frm && cur_frm.doctype === "Contact" && cur_frm.fields_dict.salutation)', 30000);
		result.it011_records = await c.evaluate(`frappe.db.get_list('Salutation', { fields: ['name'], limit: 50 }).then(r => r.map(x => x.name))`);
		result.it011_translated = await c.evaluate(`__('Dr')`);
		for (const [tag, query] of [['empty', ''], ['jie', '借'], ['dr', 'Dr']]) {
			await c.evaluate(`(() => { const f = cur_frm.fields_dict.salutation; f.$wrapper[0].scrollIntoView({ block: 'center' }); f.$input.val(${JSON.stringify(query)}); f.$input.focus(); f.$input.trigger('input'); })()`);
			await c.pause(2500);
			result[`it011_dropdown_${tag}`] = await c.evaluate(`Array.from(document.querySelectorAll('ul[role=listbox], .awesomplete ul, .link-field ul, ul.dropdown-menu')).filter(u => u.offsetParent).map(u => ({ cls: u.className, items: Array.from(u.children).map(li => li.innerText.trim()) }))`);
			await c.screenshot(path.join(out, `it011-salutation-${tag}.png`));
			await c.evaluate(`cur_frm.fields_dict.salutation.$input.blur()`);
			await c.pause(500);
		}
	} finally {
		fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(result, null, 1));
		console.log(JSON.stringify(result, null, 1));
		c.close();
	}
})().catch(error => { console.error(error); process.exit(1); });
