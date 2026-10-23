const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('../P1S6R4-cdp.cjs');
(async()=>{
 const c=await open('http://s8dev.localhost:6787');
 try {
  assert.equal(await c.evaluate('frappe.boot.sitename'),'s8dev.localhost');
  assert.equal(await c.evaluate('frappe.session.user'),'Administrator');
  await c.until('!!window.frappe_debug?.demo?.config');
  await c.evaluate("frappe.set_route('demo-rehearsal')");
  await c.until("[...document.querySelectorAll('button')].some(x=>x.textContent.trim()==='清理快照库' && x.getBoundingClientRect().height>0) && document.body.innerText.includes('演示彩排')");
  const title=await c.evaluate('document.body.innerText');
  assert.match(title,/演示彩排/);assert.match(title,/回到演示前/);
  await c.evaluate("[...document.querySelectorAll('button')].find(x=>x.textContent.trim()==='清理快照库').click()");
  await c.until("document.body.innerText.includes('已清理 0 个快照库')");
  await c.evaluate('frappe.hide_msgprint()');
  await c.evaluate("window.__ts022_return=false;frappe_debug.demo.return_to_base=async()=>{window.__ts022_return=true};[...document.querySelectorAll('button')].find(x=>x.textContent.trim()==='回到演示前').click()");
  await c.until('window.__ts022_return');
  const roles=await c.evaluate("frappe.xcall('frappe.client.get',{doctype:'Page',name:'demo-rehearsal'}).then(x=>x.roles.map(r=>r.role))");
  assert.deepEqual(roles,['System Manager']);
  await c.screenshot(path.join(__dirname,'../../frappe-bench/logs/s8-ts022-page.png'));
  fs.writeFileSync(path.join(__dirname,'../../frappe-bench/logs/s8-ts022-page.json'),JSON.stringify({site:'s8dev.localhost',buttons:true,cleanupDropped:0,returnDelegated:true,roles},null,2));
  console.log('PASS native Page registration, System Manager role, cleanup count and return button delegation');
 }finally{await c.close();}
})().catch(e=>{console.error(e.message);process.exitCode=1});
