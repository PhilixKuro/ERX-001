// TS-023 第 6 步（SL-014 ⑤，IT-022）：演示站「应收」两张截图，并数「应收账款」出现次数。
// 用法：node Spike/P1S6R7/ts023/receivable-shots.cjs http://localhost:8000 <outDir>
// ① 科目 Link 下拉：对话框里放一个 Link→Account 字段，按 HDTH 公司过滤，输入「应收」，截下拉。
// ② Account.account_type 选项：新建科目表单，把下拉展开成列表框（size=选项数）后截图；原生下拉弹层截不到。
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../../P1S6R4-cdp.cjs');

const [base, outDir] = process.argv.slice(2);
const COMPANY = '华东弹簧有限公司';
fs.mkdirSync(outDir, {recursive: true});

(async () => {
  const s = await open(base);
  const result = {};
  try {
    // ① Link 下拉
    await s.navigate(`${base}/desk/account`);
    await s.until('!!(window.frappe?.ui?.Dialog && frappe.app?.sidebar)');
    await s.evaluate(`(() => {
      const d = new frappe.ui.Dialog({title: __('Account'), fields: [{fieldname: 'acc', fieldtype: 'Link', options: 'Account', label: __('Account'),
        get_query: () => ({filters: {company: ${JSON.stringify(COMPANY)}, is_group: 0}})}]});
      d.show(); window.__d = d;
    })()`);
    await s.pause(1500);  // 刚 show 即输入时 awesomplete 尚未挂上，下拉不出现
    await s.evaluate(`(() => { const input = __d.fields_dict.acc.$input; input.focus(); input.val('应收'); input.trigger('input'); })()`);
    await s.until(`[...document.querySelectorAll('.modal.show .awesomplete ul [role=option]')].length > 0`, 20000);
    await s.pause(800);
    result.link = await s.evaluate(`(() => {
      const items = [...document.querySelectorAll('.modal.show .awesomplete ul [role=option]')].map(li => li.innerText.replace(/\\s+/g, ' ').trim());
      return {items, exact: items.filter(t => /(^|\\s)应收账款(\\s|$)/.test(t)).length};
    })()`);
    await s.screenshot(path.join(outDir, 'it022-account-link-yingshou.png'));
    await s.evaluate('window.__d.hide()');

    // ② account_type 选项
    await s.navigate(`${base}/desk/account/new-account-1`);
    await s.until('window.cur_frm?.doctype==="Account" && !!cur_frm.fields_dict.account_type && !frappe.dom.freeze_count');
    await s.pause(800);
    result.account_type = await s.evaluate(`(() => {
      const sel = cur_frm.fields_dict.account_type.$input[0];
      const items = [...sel.options].map(o => o.textContent.trim());
      sel.size = sel.options.length; sel.style.height = 'auto'; sel.scrollIntoView({block: 'start'});
      return {items, exact: items.filter(t => t === '应收账款').length};
    })()`);
    await s.pause(500);
    await s.screenshot(path.join(outDir, 'it022-account-type-options.png'));
  } finally {
    s.close();
  }
  fs.writeFileSync(path.join(outDir, 'it022.json'), JSON.stringify(result, null, 2));
  console.log(JSON.stringify(result, null, 1));
})().catch(e => { console.error(e); process.exit(1); });
