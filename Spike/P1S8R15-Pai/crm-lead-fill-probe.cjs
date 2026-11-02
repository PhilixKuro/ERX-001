// S8 R15 PT-003 probe: in a headless browser, let the demo CRM driver open the "Create" lead
// window and fill it, read the values and frames back, then close the window with Escape.
// Never clicks the window's own Create button, so no lead is written.
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
		const evaluate = async expression => {
			const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true });
			if (r.result?.exceptionDetails) console.log('EXCEPTION', JSON.stringify(r.result.exceptionDetails).slice(0, 800));
			return r.result?.result?.value;
		};
		await send('Network.enable'); await send('Network.setCacheDisabled', { cacheDisabled: true });
		await send('Page.navigate', { url: `${BASE}/login` }); await sleep(3000);
		await evaluate(`fetch('/api/method/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({usr:'Administrator',pwd:'admin'})}).then(r=>r.status)`);
		// Demo mode without a pending step: the driver loads but does not run anything by itself.
		await evaluate(`sessionStorage.setItem('frappe_debug_mode','live'); sessionStorage.removeItem('frappe_debug_pending'); sessionStorage.removeItem('frappe_debug_crm_handoff'); true`);
		await send('Page.navigate', { url: `${BASE}/crm/leads/view/list` }); await sleep(8000);
		const result = await evaluate(`(async () => {
			const driver = window.frappe_debug_crm;
			if (!driver) return {error: 'driver not loaded', scripts: [...document.scripts].map(s => s.src).filter(Boolean)};
			const page = driver.page;
			const out = {driver_script: [...document.scripts].map(s => s.src).find(src => src.includes('crm_driver'))};
			out.create_button = !!page.create_button();
			await page.open_create();
			await page.fill_lead({organization: '常州恒力机械有限公司', first_name: '张伟'});
			const [org, name] = page.lead_inputs();
			out.values = {organization: org?.value, first_name: name?.value};
			driver.highlight.show({fills: page.lead_inputs(), point: page.create_confirm_button()});
			await new Promise(r => setTimeout(r, 400));
			out.frames = [...document.querySelectorAll('.frappe-debug-crm-frame')].map(f => ({color: /#2b7de9/.test(f.style.cssText) ? 'blue' : 'orange', box: [f.style.left, f.style.top, f.style.width, f.style.height]}));
			out.confirm_button = page.create_confirm_button()?.textContent.trim();
			driver.highlight.clear();
			document.dispatchEvent(new KeyboardEvent('keydown', {key: 'Escape', bubbles: true}));
			await new Promise(r => setTimeout(r, 800));
			out.dialog_closed = !document.querySelector('[role=dialog]');
			sessionStorage.removeItem('frappe_debug_mode');
			return out;
		})()`);
		console.log(JSON.stringify(result, null, 1));
		await send('Page.captureScreenshot', { format: 'png' }).then(r => r.result?.data && fs.writeFileSync(path.join(__dirname, 'crm-lead-fill-after-close.png'), Buffer.from(r.result.data, 'base64')));
		socket.close();
	} finally {
		chrome.kill();
	}
})().catch(error => { console.error(error); process.exitCode = 1; });
