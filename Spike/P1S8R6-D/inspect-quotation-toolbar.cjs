const {open}=require('../P1S6R4-cdp.cjs');

(async()=>{
 const c=await open('http://s8dev.localhost:6787');
 try {
  assertSite(await c.evaluate('frappe.boot.sitename'));
  await c.navigate('http://s8dev.localhost:6787/desk/quotation/SAL-QTN-2026-00085');
  await c.until('!!window.cur_frm?.doc?.name',30000);
  await c.until('cur_frm.doc.docstatus===1',30000);
  const dom=await c.evaluate(`(()=>({site:frappe.boot.sitename,user:frappe.session.user,docstatus:cur_frm.doc.docstatus,dicts:Object.keys(cur_frm.page).filter(k=>/toolbar|menu|primary/i.test(k)),groups:[...document.querySelectorAll('.inner-group-button')].map(x=>({label:x.dataset.label,text:x.innerText,html:x.outerHTML.slice(0,1000)})),headers:[...document.querySelectorAll('.page-head,.page-actions,.page-form')].map(x=>({cls:x.className,html:x.outerHTML.slice(0,6000)})),inner:cur_frm.page.inner_toolbar?.$wrapper?.[0]?.outerHTML?.slice(0,5000),menu:cur_frm.page.menu?.$wrapper?.[0]?.outerHTML?.slice(0,3000),buttons:[...document.querySelectorAll('.page-actions button')].map(x=>({text:x.innerText,title:x.title,cls:x.className}))}))()`);
  console.log(JSON.stringify(dom,null,2));
 } finally { await c.close(); }
})().catch(e=>{console.error(e);process.exitCode=1;});

function assertSite(site){if(site!=='s8dev.localhost')throw Error('Wrong site: '+site);}
