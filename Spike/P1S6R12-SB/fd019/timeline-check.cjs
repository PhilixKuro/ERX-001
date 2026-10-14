// R12 SB FD-019：测试站 6787 实页核时间线选择器。
// 给一张单据加一条带 <b>null</b> 的评论，开表单读：修改记录里的 null 是否改为「（空）」，评论卡片里的 null 是否原样。
// 用法（项目根）：node Spike/P1S6R12-SB/fd019/timeline-check.cjs <round> <doctype> <name>
// 评论由本脚本建、读完即删（按返回的 name 删）。
const fs = require('node:fs');
const { open } = require('../../P1S6R4-cdp.cjs');
const [round = 'patched', doctype, name] = process.argv.slice(2);
const OUT = `Spike/P1S6R12-SB/fd019/${round}`;
fs.mkdirSync(OUT, { recursive: true });
(async () => {
	const c = await open();
	const report = { round, doctype, name };
	try {
		report.comment = await c.evaluate(`frappe.xcall('frappe.desk.form.utils.add_comment', {
			reference_doctype: ${JSON.stringify(doctype)}, reference_name: ${JSON.stringify(name)},
			content: '<p>FD-019 probe <b>null</b></p>', comment_email: 'Administrator', comment_by: 'Administrator'}).then(r => r.name)`);
		await c.evaluate(`frappe.set_route('Form', ${JSON.stringify(doctype)}, ${JSON.stringify(name)});true`);
		await c.until(`cur_frm?.doc?.name===${JSON.stringify(name)} && frappe.request.ajax_count===0`, 30000);
		await c.evaluate(`cur_frm.reload_doc();true`);
		await c.until(`!!document.querySelector('.new-timeline .timeline-content.frappe-card') && frappe.request.ajax_count===0`, 30000);
		await c.pause(2000);
		report.read = await c.evaluate(`(() => {
			const wrap = cur_frm.timeline.timeline_wrapper[0];
			const cards = [...wrap.querySelectorAll('.timeline-content.frappe-card')].filter(e => e.innerText.includes('FD-019 probe'));
			const versions = [...wrap.querySelectorAll('.timeline-content:not(.frappe-card) b')].map(b => b.textContent);
			return {
				card_bold: cards.flatMap(e => [...e.querySelectorAll('b')].map(b => b.textContent)),
				version_bold_null: versions.filter(t => t === 'null' || t === 'undefined').length,
				version_bold_empty: versions.filter(t => t === __('(Empty)')).length,
			};
		})()`);
		await c.evaluate(`document.querySelector('.new-timeline .frappe-card')?.scrollIntoView();true`);
		await c.pause(500);
		await c.screenshot(`${OUT}/timeline.png`);
	} finally {
		if (report.comment) {
			report.deleted = await c.evaluate(`frappe.xcall('frappe.client.delete', {doctype: 'Comment', name: ${JSON.stringify(report.comment)}}).then(() => true)`);
		}
		fs.writeFileSync(`${OUT}/result.json`, JSON.stringify(report, null, 1));
		console.log(JSON.stringify(report, null, 1));
		await c.close();
	}
})().catch(e => { console.error(e); process.exit(1); });
