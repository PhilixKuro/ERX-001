// R11 E: read-only look at the demo site (no clicks on save/submit; only navigation and DOM reads).
// node demo-readonly.cjs <path-to-P1S6R4-cdp.cjs> <out-dir>
const path = require('node:path');
const fs = require('node:fs');
const { open } = require(path.resolve(process.argv[2]));
const out = process.argv[3];
(async () => {
	const b = await open('http://localhost:8000');
	const res = { browser: b.browser };
	try {
		res.marks = await b.evaluate(`({
			lang: frappe.boot.lang,
			filter: !!frappe.ui.FilterGroup?.prototype.update_filter_button.__frappe_china_filter_title,
			sort: !!frappe.views.ListView?.prototype.get_header_html.__frappe_china_sort_title,
			group: !!frappe.ui.Page?.prototype.add_inner_button.__frappe_china_group_label,
			dialog: !!frappe.ui.Dialog?.prototype.make.__frappe_china_dialog_labels,
			report_class_loaded: !!frappe.views.QueryReport,
			timeline: !!document.__frappe_china_timeline_nulls,
		})`);
		// Work order list, no filter, then route with a filter (URL query only, nothing saved by us)
		await b.navigate('http://localhost:8000/desk/work-order');
		await b.until('!!document.querySelector(".list-row-head")', 30000);
		await b.pause(1500);
		res.wo_nofilter = await b.evaluate(`(() => {
			const btn = document.querySelector('.filter-selector .filter-button, .filter-button');
			const head = document.querySelector('.list-row-head [data-sort-by]');
			return { filter_title: btn?.getAttribute('title') ?? null, filter_text: btn?.innerText.trim(),
				filters: cur_list?.filter_area?.filter_list?.filters?.length,
				subject_sort_title: head?.getAttribute('title'), subject_text: head?.innerText.trim() };
		})()`);
		await b.screenshot(path.join(out, 'demo-work-order-list.png'));
		// Dialog check without opening any real form: construct, read labels, never show
		res.dialog = await b.evaluate(`(() => {
			const d = new frappe.ui.Dialog({ title: __("Fetch Timesheet"), fields: [
				{ label: __("From"), fieldname: "from_time", fieldtype: "Date" },
				{ label: __("To"), fieldname: "to_time", fieldtype: "Date" }] });
			const r = { title: d.title, from: d.fields_dict.from_time.df.label, to: d.fields_dict.to_time.df.label, plain_from: __("From") };
			d.$wrapper.remove();
			return r;
		})()`);
		res.available = await b.evaluate(`({ plain: __("Available"), raven: __("Available", null, "Raven User"), filter0: __("{0} Filter Applied", [0]) })`);
		// General Ledger: default filters only
		await b.navigate('http://localhost:8000/desk/query-report/General Ledger');
		await b.until('!!frappe.query_report && !!document.querySelector(".dt-header, .no-result, .msg-box")', 60000);
		await b.pause(3000);
		res.gl = await b.evaluate(`(() => {
			const cols = (frappe.query_report.columns || []).map(c => c.fieldname);
			const idx = cols.indexOf("voucher_type");
			const heads = [...document.querySelectorAll('.dt-header .dt-cell__content')].map(e => e.innerText.trim()).slice(0, 25);
			const rows = (frappe.query_report.data || []).length;
			return { prepare_columns_marked: !!frappe.views.QueryReport.prototype.prepare_columns.__frappe_china_doctype_columns,
				rows, voucher_type_col_index: idx, heads, company: frappe.query_report.get_filter_value("company") };
		})()`);
		await b.screenshot(path.join(out, 'demo-general-ledger.png'));
	} catch (e) { res.error = String(e.message || e); }
	fs.writeFileSync(path.join(out, 'demo-readonly.json'), JSON.stringify(res, null, 1));
	console.log(JSON.stringify(res, null, 1));
	await b.close();
})();
