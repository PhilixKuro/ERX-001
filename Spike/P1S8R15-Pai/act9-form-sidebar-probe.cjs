// S8 R15 PT-042/043 probe 5: on act 9's form pages, are the sidebar entries visible (or does the
// runner wait 5s and fall back to a route)? What does the Supplier Scorecard heatmap look like?
// Read-only: opens forms and reads the DOM; clicks nothing.
const { spawn } = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://erx.localhost:8000';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-r15-sidebar-'));
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
		const sidebar = `(() => {
			const anchors = [...document.querySelectorAll('.item-anchor')];
			const look = name => { const a = anchors.find(x => [name, __(name)].includes(x.querySelector?.('.sidebar-item-label')?.textContent.trim())); return a ? $(a).is(':visible') : 'missing'; };
			return { route: frappe.get_route_str(), sidebar: frappe.app.sidebar?.sidebar_title, item_price: look('Item Price'), scorecard: look('Supplier Scorecard'), material_request: look('Material Request') };
		})()`;
		const mr = await evaluate(`frappe.db.get_list('Material Request',{fields:['name'],order_by:'creation desc',limit:1}).then(r=>r[0]?.name)`);
		for (const [doctype, name] of [['Material Request', mr], ['Supplier Scorecard', '钢丝供应商04'], ['Supplier Scorecard', '钢丝供应商03']]) {
			await evaluate(`frappe.set_route('Form',${JSON.stringify(doctype)},${JSON.stringify(name)})`); await sleep(5000);
			console.log(doctype, name, JSON.stringify(await evaluate(sidebar)));
		}
		console.log('heatmap', JSON.stringify(await evaluate(`(() => {
			const area = cur_frm.dashboard.heatmap_area;
			const wrapper = area?.wrapper?.[0] || area?.[0];
			const box = wrapper?.getBoundingClientRect?.();
			return { keys: Object.keys(area || {}).slice(0, 12), visible: !!wrapper && $(wrapper).is(':visible'), box: box && { top: Math.round(box.top), height: Math.round(box.height), width: Math.round(box.width) },
				svg: !!wrapper?.querySelector('svg'), message: wrapper?.querySelector('.heatmap-message')?.textContent.trim(),
				in_page: !!wrapper?.closest('.page-container') && wrapper.closest('.page-container').id };
		})()`)));
		socket.close();
	} finally {
		chrome.kill();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
