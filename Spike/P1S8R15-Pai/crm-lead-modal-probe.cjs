// S8 R15 PT-003 probe: open the CRM "Create" lead window in a headless browser and dump
// the dialog roots and input placeholders the demo driver relies on. Read-only: it never
// clicks the window's own Create button.
const { spawn } = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://erx.localhost:8000';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-r15-probe-'));
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
		const evaluate = async expression => { const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true }); if (!r.result?.result || r.result.exceptionDetails) console.log('EVAL', JSON.stringify(r).slice(0, 600)); return r.result?.result; };
		await send('Page.navigate', { url: `${BASE}/login` }); await sleep(3000);
		await evaluate(`fetch('/api/method/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usr:'Administrator',pwd:'admin'})}).then(r=>r.status)`);
		await send('Page.navigate', { url: `${BASE}/crm/leads/view/list` }); await sleep(8000);
		const before = await evaluate(`(() => ({
			url: location.href,
			dialogs: [...document.querySelectorAll('[role=dialog]')].map(e => ({tag: e.tagName, cls: String(e.className).slice(0, 120), visible: !!e.offsetParent || getComputedStyle(e).position === 'fixed', text: e.innerText.slice(0, 80)})),
			create_buttons: [...document.querySelectorAll('button')].filter(b => b.textContent.trim() === '创建').map(b => ({inDialog: !!b.closest('[role=dialog]'), html: b.outerHTML.slice(0, 160)})),
		}))()`);
		console.log('BEFORE', JSON.stringify(before.value, null, 1));
		await evaluate(`[...document.querySelectorAll('button')].find(b => b.textContent.trim() === '创建' && !b.closest('[role=dialog]')).click()`);
		await sleep(3000);
		const after = await evaluate(`(() => {
			const first = document.querySelector('[role=dialog]');
			return {
				dialogs: [...document.querySelectorAll('[role=dialog]')].map(e => ({tag: e.tagName, cls: String(e.className).slice(0, 120), inputs: e.querySelectorAll('input').length, text: e.innerText.slice(0, 60)})),
				first_dialog_inputs: [...(first?.querySelectorAll('input') || [])].map(i => i.placeholder),
				all_inputs: [...document.querySelectorAll('input')].map(i => ({placeholder: i.placeholder, inDialog: !!i.closest('[role=dialog]'), type: i.type})),
				labels: [...document.querySelectorAll('.field')].map(f => f.innerText.split('\\n')[0]).slice(0, 20),
			};
		})()`);
		console.log('AFTER', JSON.stringify(after.value, null, 1));
		socket.close();
	} finally {
		chrome.kill();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
