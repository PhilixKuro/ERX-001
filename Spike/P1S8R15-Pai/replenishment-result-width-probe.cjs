// S8 R15 PT-052 probe: does a seven-column result table with sample rows stay inside the wide message box?
// Only opens a message box with made-up rows; calls no server method that writes.// Read-only: opens a submitted job card and reads the DOM; clicks nothing.
const { spawn } = require('node:child_process');
const fs = require('node:fs'), os = require('node:os'), path = require('node:path');
const CHROME = 'C:/Program Files/Google/Chrome/Application/chrome.exe';
const BASE = 'http://erx.localhost:8000';
const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-r15-msgwidth-'));
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
		for (const [label, numbers, wrap] of [['old', ['752.620949211', '1538.083560322', '2160.412135479'], false], ['new', ['752.62', '1,538.08', '2,160.41'], true]]) {
			console.log(label, JSON.stringify(await evaluate(`(() => {
				const cell = ${JSON.stringify(numbers)};
				const row = n => '<tr><td>' + frappe.utils.get_form_link('Item', 'WIRE-65MN-3.0', true) + '</td><td>仓库 - HDTH</td><td>再订货点</td><td>' + n + '</td><td>' + n + '</td><td>已更新</td><td>计划量 420.3 低于再订货点 1538.08，按经济订货量出建议</td></tr>';
				const table = '<table class="table table-bordered"><thead><tr><th>物料</th><th>仓库</th><th>字段</th><th>原值</th><th>新值</th><th>结果</th><th>原因</th></tr></thead><tbody>' + cell.map(row).join('') + '</tbody></table>';
				const message = ${wrap} ? '<div class="table-responsive">' + table.replace('table-bordered', 'table-bordered small') + '</div>' : table;
				const d = frappe.msgprint({ title: 'probe', message, wide: true });
				return new Promise(r => setTimeout(() => { const body = d.$wrapper.find('.modal-body')[0], content = d.$wrapper.find('.modal-content')[0], tab = d.$wrapper.find('table')[0];
					const out = { content: Math.round(content.getBoundingClientRect().width), body_client: body.clientWidth, table: Math.round(tab.getBoundingClientRect().width), table_right: Math.round(tab.getBoundingClientRect().right), content_right: Math.round(content.getBoundingClientRect().right), scroll: tab.parentElement.scrollWidth > tab.parentElement.clientWidth };
					d.hide(); r(out); }, 1500));
			})()`)));
			await sleep(1000);
		}
		socket.close();
	} finally {
		chrome.kill();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
