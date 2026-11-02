// S8 R15 PT-059 probe: once shown, does the draft Job Card's open arrow stay visible, where is it, and is the
// loaded runner the new one? Read-only: reads the DOM; clicks nothing.// Read-only: opens a submitted job card and reads the DOM; clicks nothing.
const { spawn } = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://erx.localhost:8000';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-r15-arrow-'));
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
		const draft = await evaluate(`frappe.db.get_list('Job Card',{filters:{docstatus:0},fields:['name'],limit:1}).then(r=>r[0]?.name)`);
		await evaluate(`frappe.set_route('Form','Job Card',${JSON.stringify(draft)})`); await sleep(5000);
		console.log(draft, JSON.stringify(await evaluate(`(async () => { const f = cur_frm.fields_dict.work_order; const w = f.$wrapper[0];
			const arrow = () => { const a = w.querySelector('.btn-open'); const r = a.getBoundingClientRect(); return { visible: $(a).is(':visible'), href: a.getAttribute('href'), box: [Math.round(r.left), Math.round(r.top), Math.round(r.width), Math.round(r.height)] }; };
			f.show_link_and_clear_buttons(); const at0 = arrow();
			await new Promise(r => setTimeout(r, 1500)); const at1500 = arrow();
			const runner = [...document.scripts].map(s => s.src).filter(s => /frappe_debug|demo/.test(s));
			return { at0, at1500, runner }; })()`)));
		socket.close();
	} finally {
		chrome.kill();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
