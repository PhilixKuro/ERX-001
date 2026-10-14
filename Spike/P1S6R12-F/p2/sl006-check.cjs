// 只读：在 vm 沙箱里加载 invoice_list.js 与 desk_patches.js，核 SL-006 三处行为与幂等、边界
const vm = require('vm'), fs = require('fs'), path = require('path');
const APP = 'D:/ERX-001/frappe-bench/apps/frappe_china/frappe_china/public/js';
const msgs = {'Unpaid':'未付','Paid':'已付款','Unpaid:Sales Invoice':'未收款','Paid:Sales Invoice':'已收款',
  'Unpaid:Purchase Invoice':'未付款','Paid:Purchase Invoice':'已付款','On Hold':'临时冻结','Partly Paid':'部分付款',
  'Setup':'基础设置','Setup:Workstation':'调机'};
const __ = (t, r, c) => (c && msgs[`${t}:${c}`]) || msgs[t] || t;
const out = [];
function mk() {
  const listview_settings = {
    'Sales Invoice': { get_indicator(doc){ return [__(doc.status), 'orange', 'status,=,' + doc.status]; }, onload(lv){ lv.calls=(lv.calls||0)+1; return 'orig'; } },
    'Purchase Invoice': { get_indicator(doc){ if (doc.on_hold && !doc.release_date) return [__('On Hold'),'darkgrey']; return [__(doc.status),'orange','status,=,' + doc.status]; }, onload(){ } },
    'Workstation': { get_indicator(doc){ return [__(doc.status), 'blue', 'status,=,' + doc.status]; } },
  };
  return { frappe: { listview_settings, boot:{lang:'zh'}, ui:{}, views:{}, form:{ formatters:{ Data:(v)=> v==null?'':v } } }, __, console:{warn(){}} };
}
const ctx = vm.createContext(mk());
const inv = fs.readFileSync(path.join(APP,'invoice_list.js'),'utf8');
vm.runInContext(inv, ctx); vm.runInContext(inv, ctx); // 重复下发
const S = ctx.frappe.listview_settings;
out.push(['SI Unpaid badge', S['Sales Invoice'].get_indicator({status:'Unpaid'})[0]]);
out.push(['SI Partly Paid badge', S['Sales Invoice'].get_indicator({status:'Partly Paid'})[0]]);
out.push(['PI Unpaid badge', S['Purchase Invoice'].get_indicator({status:'Unpaid'})[0]]);
out.push(['PI On Hold badge', S['Purchase Invoice'].get_indicator({status:'Unpaid',on_hold:1})[0]]);
out.push(['Workstation Setup badge (not wrapped)', S['Workstation'].get_indicator({status:'Setup'})[0]]);
// onload：筛选控件补 context，且重复下发不叠包装
let opts=null; const field={ df:{}, last_options:'x', set_options(){ opts = this.df.context; } };
const lv={ page:{ fields_dict:{ status: field } } };
const r = S['Sales Invoice'].onload(lv);
out.push(['SI onload return delegated', r], ['SI onload orig calls (1=no stacking)', lv.calls], ['SI filter df.context', field.df.context], ['set_options saw context', opts], ['last_options cleared', field.last_options]);
// onload 时无 status 控件
out.push(['SI onload without status field no throw', (()=>{ try{ S['Sales Invoice'].onload({page:{fields_dict:{}}}); return 'ok'; }catch(e){ return 'THROW '+e.message; } })()]);
// Select formatter
const ctx2 = vm.createContext(mk());
vm.runInContext(fs.readFileSync(path.join(APP,'desk_patches.js'),'utf8'), ctx2);
const F = ctx2.frappe.form.formatters.Select;
out.push(['Select SI df.parent', F('Unpaid',{parent:'Sales Invoice'})]);
out.push(['Select doc.doctype fallback', F('Unpaid',{}, null, {doctype:'Sales Invoice'})]);
out.push(['Select no context', F('Unpaid',{})]);
out.push(['Select Workstation Setup', F('Setup',{parent:'Workstation'})]);
out.push(['Select null value', JSON.stringify(F(null,{parent:'Sales Invoice'}))]);
// 无 frappe.form 时整个文件是否抛错（R11 记「留给 F」的 :237 可选链）
const ctx3 = vm.createContext({ frappe:{ boot:{lang:'zh'}, ui:{}, views:{} }, __, console:{warn(){}} });
out.push(['desk_patches.js without frappe.form', (()=>{ try{ vm.runInContext(fs.readFileSync(path.join(APP,'desk_patches.js'),'utf8'), ctx3); return 'ok'; }catch(e){ return 'THROW '+e.constructor.name+': '+e.message; } })()]);
for (const [k,v] of out) console.log(k, '=>', v);
