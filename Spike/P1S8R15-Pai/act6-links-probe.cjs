// S8 R15 PT-048 probe: the links act 6 would click — a Job Card list's work order column, the
// Job Card form's work order link, the Work Order form's sales order link, and the Connections
// entries on Sales Order and Work Order forms (are they on a tab that is not active?).
// Read-only: opens lists and forms and reads the DOM; clicks nothing.
const { spawn } = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://erx.localhost:8000';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-r15-links-'));
	const chrome = spawn(CHROME, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${profile}`, '--window-size=1440,900', 'about:blank'], { stdio: 'ignore' });
	try {
		let port;
		for (let i = 0; i < 100 && !port; i++) { try { port = fs.readFileSync(path.join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0]; } catch { await sleep(100); } }
		const target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find(t => t.type === 'page');
		const socket = new WebSocket(target.webSocketDebuggerUrl);
		await new Promise((resolve, reject) => { socket.addEventListener('open', resolve); socket.addEventListener('error', reject); });
		let id = 0; const waiting = new Map();
		socket.addEventListener('message', event => { const data = JSON.parse(event.data); waiting.get(data.id)?.(data); waiting.delete(data.id); });
		const send = (method, params = {}) => new Promise(resolve => { const n = ++id; waiting.set(n, resolve); socket.send(JSON.stringify({ id: n, method, params })); });
		const evaluate = async expression => {
			const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
			if (r.result?.exceptionDetails) console.log('EXCEPTION', JSON.stringify(r.result.exceptionDetails).slice(0, 800));
			return r.result?.result?.value;
		};
		await send('Network.enable'); await send('Network.setCacheDisabled', { cacheDisabled: true });
		await send('Page.navigate', { url: `${BASE}/login` }); await sleep(3000);
		await evaluate(`fetch('/api/method/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usr:'Administrator',pwd:'admin'})}).then(r=>r.status)`);
		await send('Page.navigate', { url: `${BASE}/desk/job-card?sidebar=Business%20Flow` }); await sleep(9000);
		const card = await evaluate(`frappe.db.get_list('Job Card',{filters:{docstatus:1},fields:['name','work_order'],limit:1}).then(r=>r[0])`);
		const order = await evaluate(`frappe.db.get_value('Work Order',${JSON.stringify(card.work_order)},'sales_order').then(r=>r.message.sales_order)`);
		console.log('ids', JSON.stringify({ card, order }));
		console.log('list', JSON.stringify(await evaluate(`(() => { const row = [...cur_list.$result[0].querySelectorAll('.list-row-container')].find(c => !c.querySelector('.list-row-head'));
			return { sort: cur_list.sort_by + ' ' + cur_list.sort_order, page_length: cur_list.page_length,
				work_order_cell: row?.querySelector('[data-filter^="work_order"]')?.outerHTML?.slice(0, 300) || [...(row?.querySelectorAll('.list-row-col') || [])].map(e => e.innerHTML.replace(/\\s+/g, ' ').slice(0, 160)) }; })()`)));
		const field_link = (doctype, name, field) => evaluate(`frappe.set_route('Form', ${JSON.stringify(doctype)}, ${JSON.stringify(name)}).then(() => new Promise(r => setTimeout(r, 5000))).then(() => {
			const w = cur_frm.fields_dict[${JSON.stringify(field)}]?.$wrapper?.[0];
			return { link: w?.querySelector('a[href]')?.outerHTML?.slice(0, 220), button: !!w?.querySelector('button'), visible: !!w && $(w).is(':visible') };
		})`);
		console.log('job card work_order', JSON.stringify(await field_link('Job Card', card.name, 'work_order')));
		console.log('work order sales_order', JSON.stringify(await field_link('Work Order', card.work_order, 'sales_order')));
		const connection = doctype => `(() => { const link = cur_frm.dashboard?.transactions_area?.find('.document-link[data-doctype=' + JSON.stringify(${JSON.stringify(doctype)}) + '] .badge-link')[0];
			const pane = link?.closest('.tab-pane'); const tab = pane && document.querySelector('[data-toggle="tab"][href="#' + pane.id + '"], .nav-link[aria-controls="' + pane.id + '"]');
			return { found: !!link, visible: !!link && $(link).is(':visible'), pane: pane?.id, pane_active: pane?.classList.contains('active') || pane?.classList.contains('show'),
				tab: tab?.outerHTML?.slice(0, 200), connections_tab: !!cur_frm.layout?.tabs?.find(t => t.df?.fieldname === '__dashboard' || /connections/i.test(t.df?.fieldname || '')) ,
				tabs: (cur_frm.layout?.tabs || []).map(t => t.df?.fieldname + ':' + t.is_active?.()) }; })()`;
		await evaluate(`frappe.set_route('Form', 'Sales Order', ${JSON.stringify(order)})`); await sleep(5000);
		console.log('sales order -> Work Order', JSON.stringify(await evaluate(connection('Work Order'))));
		await evaluate(`frappe.set_route('Form', 'Work Order', ${JSON.stringify(card.work_order)})`); await sleep(5000);
		console.log('work order -> Job Card', JSON.stringify(await evaluate(connection('Job Card'))));
		socket.close();
	} finally {
		chrome.kill();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
