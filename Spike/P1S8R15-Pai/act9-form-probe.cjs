// S8 R15 PT-042/043 probe 4: can act 9's click targets on forms be found, and what does a
// Supplier Scorecard form show? Read-only: opens forms and reads the DOM; clicks nothing.
const { spawn } = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://erx.localhost:8000';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-r15-forms-'));
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
		await send('Page.navigate', { url: `${BASE}/desk/replenishment-suggestion?sidebar=Business%20Flow` }); await sleep(9000);
		const adopted = await evaluate(`frappe.db.get_list('Replenishment Suggestion',{filters:{status:'Adopted',material_request:['is','set']},fields:['name','material_request'],order_by:'creation desc',limit:1}).then(r=>r[0])`);
		console.log('adopted', JSON.stringify(adopted));
		const open = async (doctype, name) => { await evaluate(`frappe.set_route('Form',${JSON.stringify(doctype)},${JSON.stringify(name)})`); await sleep(5000); };
		if (adopted) {
			await open('Replenishment Suggestion', adopted.name);
			console.log('RS form', JSON.stringify(await evaluate(`(() => {
				const w = cur_frm.fields_dict.material_request?.$wrapper?.[0];
				return { button: !!w?.querySelector('button'), link: w?.querySelector('a[href]')?.outerHTML?.slice(0, 200), html: w?.innerHTML?.replace(/\\s+/g,' ').slice(0, 400),
					actions_group: !!cur_frm.page.inner_toolbar?.find('.inner-group-button[data-label="' + encodeURIComponent(__('Actions')) + '"] button')[0] };
			})()`), null, 1));
			await open('Material Request', adopted.material_request);
			console.log('MR form', JSON.stringify(await evaluate(`(() => ({ docstatus: cur_frm.doc.docstatus,
				create_group: !!cur_frm.page.inner_toolbar?.find('.inner-group-button[data-label="' + encodeURIComponent(__('Create')) + '"] button')[0],
				groups: cur_frm.page.inner_toolbar?.find('.inner-group-button').toArray().map(e => decodeURIComponent(e.dataset.label)) }))()`), null, 1));
		}
		for (const supplier of ['钢丝供应商04', '钢丝供应商03']) {
			await open('Supplier Scorecard', supplier);
			console.log(supplier, JSON.stringify(await evaluate(`(() => {
				const f = name => { const field = cur_frm.fields_dict[name]; const w = field?.$wrapper?.[0];
					return { visible: !!w && $(w).is(':visible'), tab_active: field?.tab ? field.tab.is_active?.() : null, collapsed: field?.section?.is_collapsed?.() ?? null, rect: w ? (({width,height}) => ({width: Math.round(width), height: Math.round(height)}))(w.getBoundingClientRect()) : null }; };
				return { score: cur_frm.doc.supplier_score, status: cur_frm.doc.status,
					fields: Object.fromEntries(['supplier_score','status','period','weighting_function','standings','criteria'].map(n => [n, f(n)])),
					dashboard: !!document.querySelector('.form-dashboard .heatmap, .form-dashboard-section .frappe-chart, .form-heatmap'),
					criteria_cols: [...(cur_frm.fields_dict.criteria?.$wrapper?.[0]?.querySelectorAll('.grid-heading-row .static-area') || [])].map(e => e.textContent.trim()),
					standing_cols: [...(cur_frm.fields_dict.standings?.$wrapper?.[0]?.querySelectorAll('.grid-heading-row .static-area') || [])].map(e => e.textContent.trim()) };
			})()`), null, 1));
		}
		socket.close();
	} finally {
		chrome.kill();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
