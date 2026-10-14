const fs=require('node:fs');const{open}=require('./P1S6R4-cdp.cjs');const{extractVisibleText,findEnglish}=require('./P1S6R4-visible-text.cjs');
const state=JSON.parse(fs.readFileSync('Spike/P1S6R4-closed-loop.json','utf8')),spec=JSON.parse(fs.readFileSync('Spike/P1S6R4-screens.json','utf8'));
const out='Spike/P1S6R4-screens-loop',filter=process.argv[2];fs.mkdirSync(out,{recursive:true});
(async()=>{const c=await open('http://erx.localhost:8000'),report=[];async function capture(id,dt){
 const exclusions=[...(spec.data_selectors||[]).map(x=>x.selector),'.form-details','.form-sidebar .document-followers','.form-sidebar .form-assignments','[data-fieldname="bom_no"] .control-value','[data-fieldname="item"] .control-value'];
 // Exact document identifiers are data, including generated Job Card names.
 const entries=await c.evaluate(`(${extractVisibleText.toString()})(${JSON.stringify(exclusions)})`);const english=findEnglish(entries,new Set([...Object.keys(spec.allow),...state.docs.map(([dt,name])=>name),...(state.job_cards||[])]));
 const row={id,doctype:dt,url:await c.evaluate('decodeURI(location.href)'),english,pass:!english.length,sidebar_title:await c.evaluate('frappe.app.sidebar.sidebar_title'),entries,screenshot:`${out}/${id}.png`};await c.screenshot(row.screenshot);report.push(row);fs.writeFileSync(`${out}/result-${filter||'masters'}.json`,JSON.stringify(report,null,2));console.log(JSON.stringify({id,english,pass:row.pass}));
 }
 try{await c.evaluate(`frappe.set_route('desktop');true`);await c.until(`!!document.querySelector('.desktop-icon')`);await c.evaluate(`[...document.querySelectorAll('.desktop-icon')].find(e=>e.innerText.includes('业务流程')).click();true`);await c.until(`frappe.app.sidebar.sidebar_title==='Business Flow' && window.cur_list?.doctype==='Company' && !!document.querySelector('.list-row-container')`);await c.pause(500);
 const docs=filter==='job_cards'?state.job_cards.map(name=>['Job Card',name]):state.docs.filter(([dt,name])=>filter?name===state[filter]:!['Warehouse'].includes(dt));
 if(!docs.length)throw Error(`No acceptance document found for ${filter}`);
 for(const[dt,name]of docs){
  await c.evaluate(`frappe.set_route('Form',${JSON.stringify(dt)},${JSON.stringify(name)});true`);await c.until(`cur_frm?.doctype===${JSON.stringify(dt)} && cur_frm.doc.name===${JSON.stringify(name)} && !frappe.dom.freeze_count`);await c.pause(600);
  const id=(Object.keys(state).find(k=>state[k]===name)||name).replace(/[\\/:]/g,'-');await capture(id+'-form',dt);
  const required={Item:['details','uom_tab','inventory_section','manufacturing'],BOM:['production_item_tab','costing','more_info_tab'],Company:['accounts_tab','stock_tab']};
  const tabs=required[dt]||[];
  for(const tab of tabs){await c.evaluate(`document.querySelector('.nav-link[data-fieldname="${tab}"]').click();true`);await c.pause(150);await capture(id+'-'+tab,dt);}
  await c.evaluate(`cur_frm.layout.tabs[0]?.set_active();true`);
  if(await c.evaluate('cur_frm.doc.docstatus===0')){
   await c.evaluate(`cur_frm.save();true`);await c.until('!frappe.dom.freeze_count');await c.pause(800);await capture(id+'-saved',dt);
   if(await c.evaluate('!!cur_frm.meta.is_submittable')){
    await c.evaluate('cur_frm.savesubmit();true');await c.until(`!!document.querySelector('.modal.show,.modal.in')`);await capture(id+'-submit-confirm',dt);await c.evaluate(`frappe.hide_msgprint();$('.modal').modal('hide');true`);
   }
  }else if(await c.evaluate('cur_frm.doc.docstatus===1 && !cur_frm.meta.is_single')){
   await c.evaluate('cur_frm.savecancel();true');await c.pause(300);await capture(id+'-cancel-confirm',dt);await c.evaluate(`frappe.hide_msgprint();$('.modal').modal('hide');true`);
  }
 }
 }catch(e){await c.screenshot(out+'/failure.png');const failure={error:String(e),state:await c.evaluate(`({url:location.href,doc:window.cur_frm?.doc?.name,doctype:window.cur_frm?.doctype,freeze:frappe.dom.freeze_count,body:document.body.innerText.slice(-3500)})`),exceptions:c.events.filter(e=>e.method==='Runtime.exceptionThrown').slice(-10)};fs.writeFileSync(`${out}/failure-${filter||'masters'}.json`,JSON.stringify(failure,null,2));console.log(JSON.stringify(failure,null,2));throw e;}finally{c.close()}})().catch(e=>{console.error(e);process.exitCode=1});
