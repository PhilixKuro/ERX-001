const fs = require('node:fs');
const assert = require('node:assert/strict');
const { open } = require('./P1S6R4-cdp.cjs');
const state = JSON.parse(fs.readFileSync('Spike/P1S6R4-part3-state.json', 'utf8'));
const out = { results: [] };
const save = () => fs.writeFileSync('Spike/P1S6R4-opening-ledger.out.json', JSON.stringify(out, null, 2));

(async()=>{
	const c=await open();
	try{
		out.browser=c.browser;
		for(const [doctype,name,opening] of [
			['Stock Reconciliation',state.opening_stock,true],['Journal Entry',state.journals.opening,true],
			['Stock Entry',state.normal_stock,false],['Journal Entry',state.journals.normal,false],
		]){
			const r={doctype,name,opening,pass:false};
			try{
				await c.evaluate(`frappe.set_route('Form',${JSON.stringify(doctype)},${JSON.stringify(name)});true`);
				await c.until(`cur_frm?.doc?.name===${JSON.stringify(name)} && cur_frm.custom_buttons?.[__('${doctype.startsWith('Stock')?'Accounting Ledger':'Ledger'}')] && frappe.request.ajax_count===0`);
				await c.pause(600);
				r.form=await c.evaluate(`({doctype:cur_frm.doc.doctype,name:cur_frm.doc.name,opening:cur_frm.doc.is_opening,purpose:cur_frm.doc.purpose,
					stock_patch:!!erpnext.stock.StockController.prototype.show_general_ledger.__frappe_china_opening_wrapped,
					button:cur_frm.custom_buttons[__('${doctype.startsWith('Stock')?'Accounting Ledger':'Ledger'}')][0].outerHTML})`);
				// Click the actual form button; snapshot filters synchronously before the report consumes them.
				r.filters=await c.evaluate(`(()=>{cur_frm.custom_buttons[__('${doctype.startsWith('Stock')?'Accounting Ledger':'Ledger'}')][0].click();return JSON.parse(JSON.stringify(frappe.route_options))})()`);
				assert.equal(r.filters.voucher_no,name);
				assert.equal(r.filters.show_opening_entries,opening?1:undefined);
				await c.until(`frappe.get_route()[0]==='query-report' && frappe.query_report?.report_name==='General Ledger' && frappe.request.ajax_count===0`);
				await c.pause(500);
				r.rows=await c.evaluate(`(async()=>{const r=await frappe.call({method:'frappe.desk.query_report.run',args:{report_name:'General Ledger',filters:${JSON.stringify(JSON.stringify(r.filters))},ignore_prepared_report:true}});return r.message.result.filter(row=>row.voucher_no===${JSON.stringify(name)}).map(row=>({account:row.account,debit:row.debit,credit:row.credit,voucher_no:row.voucher_no}))})()`);
				assert.ok(r.rows.length>=2,`Expected >=2 ledger rows, got ${r.rows.length}`);
				assert.ok(r.rows.some(x=>x.debit>0)&&r.rows.some(x=>x.credit>0));
				await c.screenshot(`Spike/P1S6R4-ledger-${doctype.replaceAll(' ','-').toLowerCase()}-${opening?'opening':'normal'}.png`);
				r.pass=true;
			}catch(error){r.error=String(error);}
			out.results.push(r);save();console.log(JSON.stringify(r));
		}
		const source=fs.readFileSync('frappe-bench/apps/frappe_china/frappe_china/public/js/desk_patches.js','utf8');
		out.missing_controller=await c.evaluate(`(()=>{const original=erpnext.stock.StockController,warn=console.warn,messages=[];try{delete erpnext.stock.StockController;console.warn=(...args)=>messages.push(args.join(' '));(0,eval)(${JSON.stringify(source)});return {messages,exception:false}}catch(e){return {messages,exception:String(e)}}finally{erpnext.stock.StockController=original;console.warn=warn}})()`);
		assert.equal(out.missing_controller.exception,false);
		assert.equal(out.missing_controller.messages.length,1);
		save();if(out.results.some(r=>!r.pass))process.exitCode=1;
	}finally{c.close();}
})().catch(e=>{out.error=String(e);save();console.error(e);process.exitCode=1;});
