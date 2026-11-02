// S8 R15 PT-067 probe (from PT-052 probe 2): render act 9's real calculation result (from a dry run on a9_b, rolled back)
// with the page's own show_replenishment_result and measure it. Calls no server method that writes.// Read-only: opens a submitted job card and reads the DOM; clicks nothing.
const { spawn } = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://erx.localhost:8000';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-r15-msgxl-'));
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
		const result = fs.readFileSync(path.join(__dirname, 'act9-calc-result.json'), 'utf8');
		console.log(JSON.stringify(await evaluate(`fetch('/assets/frappe_china/js/replenishment_suggestion_list.js?' + Date.now()).then(r => r.text()).then(src => {
			const show = new Function('frappe', src + '; return show_replenishment_result;')(frappe);
			show(${result});
			return new Promise(r => setTimeout(() => { const d = frappe.msg_dialog; const content = d.$wrapper.find('.modal-content')[0], tab = d.$wrapper.find('table')[0], box = tab.parentElement;
				const c = content.getBoundingClientRect(), tb = tab.getBoundingClientRect();
				const cols = [...tab.querySelectorAll('thead th')].map(th => [th.textContent, Math.round(th.getBoundingClientRect().width)]);
				const out = { xl: d.$wrapper.find('.modal-dialog').hasClass('modal-xl'), content_width: Math.round(c.width), table: [Math.round(tb.left), Math.round(tb.right)], content: [Math.round(c.left), Math.round(c.right)], scrolls: box.scrollWidth > box.clientWidth, cols, rule_cells: [...tab.querySelectorAll('tbody tr')].slice(0, 6).map(tr => tr.cells[2].textContent) };
				d.hide(); setTimeout(() => { out.xl_after_hide = d.$wrapper.find('.modal-dialog').hasClass('modal-xl'); r(out); }, 800); }, 1500));
		})`)));
		socket.close();
	} finally {
		chrome.kill();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
