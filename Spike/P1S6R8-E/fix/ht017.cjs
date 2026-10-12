// R8 IT-040：重拍 HT-017。role_allowed_to_over_bill 有 depends_on over_billing_allowance > 0，
// 测试站该值为 0 故字段隐藏。只在表单内存里 set_value 让字段显示，不保存、不写库。
// node Spike/P1S6R8-E/fix/ht017.cjs   （测试站须已在 6787 起 serve）
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../../P1S6R4-cdp.cjs');

const out = path.join(__dirname, 'ht017');
fs.mkdirSync(out, { recursive: true });

(async () => {
	const c = await open('http://test.localhost:6787');
	const result = {};
	try {
		await c.navigate(`${c.base}/desk/accounts-settings`);
		await c.until('!!(window.cur_frm && cur_frm.doctype === "Accounts Settings" && cur_frm.fields_dict.role_allowed_to_over_bill)', 30000);
		result.before = await c.evaluate(`({ allowance: cur_frm.doc.over_billing_allowance, visible: cur_frm.fields_dict.role_allowed_to_over_bill.$wrapper.is(':visible') })`);
		await c.evaluate(`cur_frm.set_value('over_billing_allowance', 10)`);
		await c.pause(1500);
		result.after = await c.evaluate(`(() => {
			const f = cur_frm.fields_dict.role_allowed_to_over_bill;
			if (f.tab) f.tab.set_active();
			f.$wrapper[0].scrollIntoView({ block: 'center' });
			f.$wrapper[0].style.outline = '3px solid red';
			return { lang: frappe.boot.lang, df_label: f.df.label, shown: f.$wrapper.find('.control-label').first().text().trim(), visible: f.$wrapper.is(':visible'), dirty: cur_frm.is_dirty() };
		})()`);
		await c.pause(800);
		await c.screenshot(path.join(out, 'ht017-accounts-settings.png'));
		// 丢弃内存改动：重载文档，不保存
		await c.evaluate(`cur_frm.reload_doc()`);
		await c.pause(1500);
		result.reloaded = await c.evaluate(`({ allowance: cur_frm.doc.over_billing_allowance, dirty: cur_frm.is_dirty() })`);
	} finally {
		fs.writeFileSync(path.join(out, 'result.json'), JSON.stringify(result, null, 1));
		console.log(JSON.stringify(result, null, 1));
		c.close();
	}
})().catch(error => { console.error(error); process.exit(1); });
