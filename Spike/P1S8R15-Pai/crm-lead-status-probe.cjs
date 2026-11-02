// S8 R15 step 24 probe: open the CRM "Create lead" dialog on erx and s8r9 and read whether the
// status field got its default. Read-only: opens the dialog, reads it, closes it; never submits.
const { spawn } = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
	for (const BASE of ['http://erx.localhost:8000', 'http://s8r9.localhost:6787']) {
		const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-r15-crmstatus-'));
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
				if (r.result?.exceptionDetails) console.log('EXCEPTION', JSON.stringify(r.result.exceptionDetails).slice(0, 500));
				return r.result?.result?.value;
			};
			await send('Page.navigate', { url: `${BASE}/login` }); await sleep(3000);
			await evaluate(`fetch('/api/method/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usr:'Administrator',pwd:'admin'})}).then(r=>r.status)`);
			const statuses = await evaluate(`fetch('/api/method/frappe.client.get_list',{method:'POST',headers:{'Content-Type':'application/json','X-Frappe-CSRF-Token':'x'},body:JSON.stringify({doctype:'CRM Lead Status',fields:['name','position'],order_by:'position asc'})}).then(r=>r.json()).then(j=>j.message)`);
			const db = await evaluate(`fetch('/api/method/frappe_debug.demo.switch.switch_status',{method:'POST'}).then(r=>r.json()).then(j=>j.message?.db)`);
			await send('Page.navigate', { url: `${BASE}/crm/leads/view/list` }); await sleep(8000);
			await evaluate(`[...document.querySelectorAll('button')].find(b => ['创建','Create'].includes(b.textContent.trim()))?.click(); true`); await sleep(4000);
			const dialog = await evaluate(`(() => { const d = document.querySelector('[role=dialog]'); if (!d) return null;
				const field = [...d.querySelectorAll('label, .text-sm, span')].find(e => /^状态|^Status/.test(e.textContent.trim()))?.closest('div')?.parentElement;
				return { status_area: field?.textContent.replace(/\\s+/g, ' ').slice(0, 80), buttons: [...d.querySelectorAll('button')].map(b => b.textContent.trim()).filter(Boolean).slice(0, 12) }; })()`);
			console.log(BASE, 'db', db, 'statuses', JSON.stringify(statuses?.map(s => s.name)), 'dialog', JSON.stringify(dialog));
			socket.close();
		} finally {
			chrome.kill();
		}
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
