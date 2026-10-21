// SL-007⑤: item tables, clickable items, escaping and empty output.
const { test } = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vm = require('node:vm');
function setup() {
  const messages = [], links = [];
  const escape = value => String(value ?? '').replaceAll('&', '&amp;').replaceAll('<', '&lt;').replaceAll('>', '&gt;');
  const frappe = { listview_settings: {}, provide() {}, utils: { escape_html: escape,
    get_form_link(dt, code, html) { links.push([dt,code,html]); return '<a href=/desk/item/' + encodeURIComponent(code) + '>' + escape(code) + '</a>'; } },
    msgprint(message) { messages.push(message); } };
  const ctx = { frappe, frappe_china: { replenishment: {} }, __: key => key };
  const file = process.env.REPLENISHMENT_RESULT_SOURCE || path.join(__dirname, '../../frappe-bench/apps/frappe_china/frappe_china/public/js/replenishment_suggestion_list.js');
  vm.createContext(ctx); vm.runInContext(fs.readFileSync(file,'utf8'),ctx);
  return { ctx,messages,links };
}
test('calculation renders linked item tables with old new outcome and reason', () => {
  const s=setup();
  s.ctx.show_replenishment_result({ok:true,companies:{'Company A':[
    {step:'safety_stock',processed:1,skipped:0,problems:[],changes:[{item_code:'WIRE',warehouse:null,field:'safety_stock',old:2,new:4.12855,outcome:'updated',reason:'Raw issues only'}]},
    {step:'reorder_level',processed:1,skipped:0,problems:[],changes:[{item_code:'WIRE',warehouse:'RAW',field:'warehouse_reorder_level',old:5,new:35.482311,outcome:'updated',reason:'Lead time 7'}]},
    {step:'suggestions',processed:0,skipped:0,problems:[],changes:[{item_code:'WIRE',warehouse:'RAW',field:'suggested_qty',old:null,new:null,outcome:'not_triggered',reason:'30 above 20'}]},
  ],'Company B':[{step:'suggestions',processed:0,skipped:0,problems:[],changes:[]}]}});
  const html=s.messages[0].message;
  assert.equal((html.match(/<table/g) || []).length, 1, 'all three steps share one company table');
  for(const text of ['<table','Company A','Company B','/desk/item/WIRE','RAW','4.12855','35.482311','30 above 20','No changes']) assert.ok(html.includes(text),text);
  assert.ok(s.links.some(([dt,code,html])=>dt==='Item' && code==='WIRE' && html===true));
  assert.ok(html.includes('Safety Stock') && html.includes('Reorder Level') && html.includes('Suggested Qty'));
});
test('calculation escapes company warehouse reasons and problems while keeping item links', () => {
  const s=setup();
  s.ctx.show_replenishment_result({ok:false,companies:{'<img onerror=company>':[{step:'suggestions',processed:0,skipped:1,problems:['<script>problem</script>'],changes:[{item_code:'<img onerror=item>',warehouse:'<img onerror=warehouse>',field:'suggested_qty',old:0,new:0,outcome:'skipped',reason:'<img onerror=reason>'}]}]}});
  const html=s.messages[0].message;
  assert.ok(!html.includes('<img') && !html.includes('<script>'));
  assert.ok(html.includes('&lt;script&gt;problem&lt;/script&gt;')); assert.ok(html.includes('<a href='));
});
test('calculation shows no changes for empty details and keeps problems visible', () => {
  const s=setup();
  s.ctx.show_replenishment_result({ok:false,companies:{CO:[{step:'safety_stock',processed:0,skipped:1,changes:[],problems:['Bad lead time']}]}});
  assert.ok(s.messages[0].message.includes('No changes')); assert.ok(s.messages[0].message.includes('Bad lead time')); assert.equal(s.messages[0].indicator,'orange');
});
