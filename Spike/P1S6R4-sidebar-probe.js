const fs=require('node:fs');
const {open}=require('./P1S6R4-cdp.cjs');
(async()=>{const c=await open();try{
 await c.evaluate("frappe.set_route('List','Company');true");await c.pause(1200);
 let start=c.events.length;
 await c.evaluate("frappe.app.sidebar.setup('Business Flow');true");await c.pause(600);
 const requests=()=>c.events.slice(start).filter(x=>x.method==='Network.requestWillBeSent'&&/\/undefined(?:$|\?)/.test(x.params.request.url)).map(x=>x.params.request.url);
 const result={before:{requests:requests(),state:await c.evaluate(`({container_length:frappe.app.sidebar.sidebar_header.dropdown_menu.length,header_images:[...document.querySelectorAll('.sidebar-header img')].map(e=>e.getAttribute('src')),html:frappe.ui.SidebarHeader.prototype.add_app_item.toString()})`)}};
 await c.evaluate(`(()=>{const original=frappe.ui.SidebarHeader.prototype.add_app_item;window.s6OriginalAddAppItem=original;frappe.ui.SidebarHeader.prototype.add_app_item=function(item){if(!this.dropdown_menu?.length)return;return original.apply(this,arguments)};return true})()`);
 start=c.events.length;
 await c.evaluate("frappe.app.sidebar.setup('Business Flow');true");await c.pause(600);
 result.after={requests:requests(),state:await c.evaluate(`({container_length:frappe.app.sidebar.sidebar_header.dropdown_menu.length,header_images:[...document.querySelectorAll('.sidebar-header img')].map(e=>e.getAttribute('src')),visible_menu:frappe.app.sidebar.sidebar_header.wrapper.find('.drop-icon').length})`)};
 fs.writeFileSync('Spike/P1S6R4-sidebar-probe.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));
}finally{c.close()}})().catch(e=>{console.error(e);process.exitCode=1});
