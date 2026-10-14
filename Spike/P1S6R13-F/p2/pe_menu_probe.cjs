// R13 F p2：沿用 R12 片 3 的上游源码复现法（只读截取 page.js / form.js 源码行），
// 但改点「窄屏菜单」（.hidden-xl 的 page menu）里的两条项，看修后 PE 与 JE 的第一条菜单项
// 是否仍走原生处理函数（不带 show_opening_entries）。不改任何文件。
const fs = require('node:fs');
const vm = require('node:vm');
const { Window } = require('D:/ERX-001/frappe-bench/apps/crm/frontend/node_modules/happy-dom');
const APPS = 'D:/ERX-001/frappe-bench/apps';
const win = new Window();
const $ = require(`${APPS}/frappe/node_modules/jquery/dist/jquery.js`)(win);

const lines = (file, a, b) => fs.readFileSync(file, 'utf8').split(/\r?\n/).slice(a - 1, b).join('\n');
const PAGE = `${APPS}/frappe/frappe/public/js/frappe/ui/page.js`;
const FORM = `${APPS}/frappe/frappe/public/js/frappe/form/form.js`;
const pageSrc = ['class Page {', lines(PAGE, 349, 358), lines(PAGE, 437, 512), lines(PAGE, 545, 554),
	lines(PAGE, 565, 587), lines(PAGE, 589, 608), lines(PAGE, 622, 684), '}'].join('\n');
const formSrc = ['class Form {', lines(FORM, 1540, 1549), lines(FORM, 1562, 1583), '}'].join('\n');

const DICT = { Ledger: '会计凭证', View: '查看' };
const ctx = {
	$, __: (w) => DICT[w] || w, console, encodeURIComponent,
	frappe: { ui: { keys: { get_shortcut_group: () => ({ add() {} }) }, form: {} }, utils: { icon: () => '' } },
	moment: () => ({ format: () => '2026-10-10' }),
};
vm.createContext(ctx);
vm.runInContext(`${pageSrc}\n${formSrc}\nthis.Page = Page; this.Form = Form;`, ctx);

function run(doctype) {
	const page = Object.create(ctx.Page.prototype);
	page.inner_toolbar = $('<div class="inner-toolbar hide"></div>');
	page.menu = $('<ul class="menu"></ul>');
	page.menu_btn_group = $('<div class="hide"></div>');
	const frm = Object.create(ctx.Form.prototype);
	frm.page = page; frm.custom_buttons = {};
	frm.doc = {
		doctype, name: 'X-OPEN', is_opening: 'Yes', docstatus: 1, posting_date: '2026-01-01',
		modified: '2026-10-10', company: 'C', finance_book: '',
	};
	const nativeHandler = () => { ctx.frappe.route_options = { native: true }; };
	frm.add_custom_button(ctx.__('Ledger'), nativeHandler, doctype === 'Journal Entry' ? ctx.__('View') : 'fa fa-table');
	const handlers = {};
	ctx.frappe.ui.form.on = (dt, ev) => { handlers[dt] = ev; };
	ctx.frappe.set_route = (...r) => { ctx.route = r; };
	vm.runInContext(fs.readFileSync(`${APPS}/frappe_china/frappe_china/public/js/opening_ledger.js`, 'utf8'), ctx);
	handlers[doctype].refresh(frm);
	const items = page.menu.find('li > a.grey-link');
	const results = [];
	items.each((i, a) => {
		ctx.frappe.route_options = undefined;
		$(a).trigger('click');
		const ro = ctx.frappe.route_options || {};
		results.push({ idx: i, text: $(a).find('.menu-item-label').text().trim(), native: !!ro.native, show_opening_entries: ro.show_opening_entries ?? null });
	});
	return { doctype, menu_items: results, toolbar_or_group_buttons: page.inner_toolbar.find('button[data-label], .dropdown-item[data-label]').length };
}
console.log(JSON.stringify([run('Journal Entry'), run('Payment Entry')], null, 1));
