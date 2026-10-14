// 只读模拟：把 opening_ledger.js 第 10 行在内存里改为 PE 不带分组删除，看是否生效（不改 app 文件）
// P1-S6-R12 F 分片 3：只读复现——用上游真实的 Page.add_inner_button / remove_inner_button 与
// Form.add_custom_button / remove_custom_button 源码（按行号截取，不改任何文件），跑 opening_ledger.js，
// 看 Journal Entry 与 Payment Entry 的开账总账按钮是否真被替换。
// 运行：node D:/ERX-001/Spike/P1S6R12-F/p3/pe_button_repro.cjs
const fs = require('node:fs');
const vm = require('node:vm');
const { Window } = require('D:/ERX-001/frappe-bench/apps/crm/frontend/node_modules/happy-dom');
const APPS = 'D:/ERX-001/frappe-bench/apps';
const win = new Window();
const $ = require(`${APPS}/frappe/node_modules/jquery/dist/jquery.js`)(win);

const lines = (file, a, b) => fs.readFileSync(file, 'utf8').split(/\r?\n/).slice(a - 1, b).join('\n');
const PAGE = `${APPS}/frappe/frappe/public/js/frappe/ui/page.js`;
const FORM = `${APPS}/frappe/frappe/public/js/frappe/form/form.js`;
// page.js: add_menu_item 349-358、add_dropdown_item 437-512、is_in_group_button_dropdown 545-554、
// get_or_add_inner_group_button / get_inner_group_button 565-587、set_inner_btn_group_as_primary／btn_disable_enable 589-608、
// add_inner_button / remove_inner_button 622-684
const pageSrc = ['class Page {', lines(PAGE, 349, 358), lines(PAGE, 437, 512), lines(PAGE, 545, 554),
  lines(PAGE, 565, 587), lines(PAGE, 589, 608), lines(PAGE, 622, 684), '}'].join('\n');
// form.js: add_custom_button 1540-1549、remove_custom_button 1562-1583
const formSrc = ['class Form {', lines(FORM, 1540, 1549), lines(FORM, 1562, 1583), '}'].join('\n');

const DICT = { Ledger: '会计凭证', View: '查看' };
const ctx = { $, __: (w) => DICT[w] || w, console, encodeURIComponent,
  frappe: { ui: { keys: { get_shortcut_group: () => ({ add() {} }) }, form: {} }, utils: { icon: () => '' } },
  moment: () => ({ format: () => '2026-10-10' }) };
vm.createContext(ctx);
vm.runInContext(`${pageSrc}\n${formSrc}\nthis.Page = Page; this.Form = Form;`, ctx);

function run(doctype) {
  const page = Object.create(ctx.Page.prototype);
  page.inner_toolbar = $('<div class="inner-toolbar hide"></div>');
  page.menu = $('<ul class="menu"></ul>');
  page.menu_btn_group = $('<div class="hide"></div>');
  const frm = Object.create(ctx.Form.prototype);
  frm.page = page; frm.custom_buttons = {};
  frm.doc = { doctype, name: 'X-OPEN', is_opening: 'Yes', docstatus: 1, posting_date: '2026-01-01',
    modified: '2026-10-10', company: 'C', finance_book: '' };
  // 上游原生按钮：照抄 journal_entry.js:80-95 与 payment_entry.js:423-441 的调用形状
  const nativeHandler = () => { ctx.frappe.route_options = { native: true }; };
  frm.add_custom_button(ctx.__('Ledger'), nativeHandler, doctype === 'Journal Entry' ? ctx.__('View') : 'fa fa-table');
  // frappe_china 的 doctype_js（在上游 refresh 之后跑，HT-005）
  const handlers = {};
  ctx.frappe.ui.form.on = (dt, ev) => { handlers[dt] = ev; };
  ctx.frappe.set_route = (...r) => { ctx.route = r; };
  ctx.frappe.route_options = undefined;
  vm.runInContext(fs.readFileSync(`${APPS}/frappe_china/frappe_china/public/js/opening_ledger.js`, 'utf8').replace('frm.remove_custom_button(__("Ledger"), group);', 'frm.remove_custom_button(__("Ledger"), is_journal ? group : undefined);'), ctx);
  handlers[doctype].refresh(frm);
  const buttons = page.inner_toolbar.find('button[data-label], .dropdown-item[data-label]');
  buttons.last().trigger('click');
  const menu = page.menu.find(".menu-item-label").map((i, s) => $(s).text()).get();
  return { doctype, mobile_menu: menu, buttons: buttons.length, where: buttons.map((i, b) => b.tagName).get(),
    route_options_after_click: ctx.frappe.route_options };
}
console.log(JSON.stringify([run('Journal Entry'), run('Payment Entry')], null, 1));
