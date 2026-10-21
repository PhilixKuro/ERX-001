const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../P1S6R4-cdp.cjs');

(async () => {
 const c = await open();
 try {
  assert.equal(await c.evaluate('frappe.boot.sitename'), 'test.localhost');
  const result = {site: 'test.localhost'};
  await c.navigate(c.base+'/desk/employee/new?sidebar=Business%20Flow');
  await c.until("window.cur_frm?.doctype==='Employee' && cur_frm.fields_dict.gender?.$input?.length",30000);
  assert.equal(await c.evaluate('frappe.boot.sitename'), 'test.localhost');
  await c.evaluate("(()=>{const field=cur_frm.fields_dict.gender;field.$input[0].scrollIntoView({block:'center'});field.$input.val('').focus();field.on_input();return true;})()");
  await c.until("cur_frm.fields_dict.gender.awesomplete?.ul?.getBoundingClientRect().height>0 && cur_frm.fields_dict.gender.awesomplete._list?.length>=7",30000);
  result.genders = await c.evaluate("Array.from(cur_frm.fields_dict.gender.awesomplete.ul.querySelectorAll('[role=option] strong')).map(x=>x.innerText)");
  assert(result.genders.includes('男性') && result.genders.includes('女'), JSON.stringify(result.genders));
  assert(result.genders.length >= 7);
  assert(result.genders.every(label=>/[\u4e00-\u9fff]/.test(label)),JSON.stringify(result.genders));
  await c.send('Page.bringToFront');
  await c.pause(600);
  await c.screenshot(path.join(__dirname,'SL010-employee-gender.png'));
  await c.navigate(c.base+'/desk/stock-settings/Stock%20Settings?sidebar=Business%20Flow');
  await c.until("window.cur_frm?.doctype==='Stock Settings' && !frappe.request.ajax_count",30000);
  result.batch_enabled = await c.evaluate('cur_frm.doc.enable_serial_and_batch_no_for_item');
  assert.equal(result.batch_enabled,1);
  await c.evaluate("cur_frm.fields_dict.enable_serial_and_batch_no_for_item.$wrapper[0].scrollIntoView({block:'center'}); true");
  await c.pause(600);
  await c.screenshot(path.join(__dirname,'SL010-batch-setting.png'));
  await c.navigate(c.base+'/desk/user/Administrator?sidebar=Business%20Flow');
  await c.until("window.cur_frm?.doctype==='User' && cur_frm.doc.name==='Administrator' && !frappe.request.ajax_count",30000);
  result.administrator = await c.evaluate("({first_name:cur_frm.doc.first_name,full_name:frappe.session.user_fullname,visible:document.body.innerText.includes('演示管理员')})");
  assert.equal(result.administrator.first_name,'演示管理员');
  assert.equal(result.administrator.full_name,'演示管理员');
  assert(result.administrator.visible);
  result.administrator.sidebar_name = await c.evaluate("document.querySelector('.sidebar-user-button .avatar-name-email')?.innerText");
  assert(result.administrator.sidebar_name?.includes('演示管理员'));
  await c.evaluate("cur_frm.fields_dict.first_name.$wrapper[0].scrollIntoView({block:'center'}); true");
  await c.pause(600);
  await c.screenshot(path.join(__dirname,'SL010-administrator-name.png'));
  fs.writeFileSync(path.join(__dirname,'../../frappe-bench/logs/s8-demo-prerequisites-ui.json'),JSON.stringify(result,null,2));
  console.log(JSON.stringify(result));
 } finally {await c.close();}
})().catch(error=>{console.error(error);process.exitCode=1;});
