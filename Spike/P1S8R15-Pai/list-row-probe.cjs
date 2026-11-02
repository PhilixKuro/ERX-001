// S8 R15 PT-042 probe 3: does a list row's subject link carry data-name, as the runner's row target assumes?
// Read-only: opens list pages and reads their markup; clicks nothing.
const { spawn } = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://erx.localhost:8000';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-r15-rows-'));
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
		for (const url of ['/desk/replenishment-suggestion?sidebar=Business%20Flow', '/desk/supplier-scorecard?sidebar=Business%20Flow', '/desk/item-price?sidebar=Business%20Flow']) {
			await send('Page.navigate', { url: `${BASE}${url}` }); await sleep(9000);
			console.log(url, JSON.stringify(await evaluate(`(() => {
				const result = cur_list.$result[0];
				const containers = [...result.querySelectorAll('.list-row-container')];
				const first = containers.find(c => !c.querySelector('.list-row-head'));
				const name = cur_list.data[0]?.name;
				return {
					doctype: cur_list.doctype, containers: containers.length, header_rows: containers.filter(c => c.querySelector('.list-row-head')).length,
					first_name: name,
					a_data_name: !!result.querySelector('a[data-name="' + name + '"]'),
					checkbox_data_name: first?.querySelector('.list-row-checkbox')?.getAttribute('data-name'),
					subject_link: first?.querySelector('.list-subject a')?.outerHTML.slice(0, 300),
					first_rect: first?.getBoundingClientRect(),
				};
			})()`), null, 1));
		}
		socket.close();
	} finally {
		chrome.kill();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
