const { spawn, spawnSync } = require('node:child_process');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const pause = ms => new Promise(r => setTimeout(r, ms));

// 每次 open() 建一个临时配置目录（%TEMP%\erx-s6-cdp-*，一个约 80 MB）。以前只 kill 不删，
// 2026-10-13 累积 227 个、10.7 GB，是宿主 C 盘写满的原因之一。现在 close() 时删；调用方没等 close()
// 就 process.exit() 的，由下面的 exit 钩子同步兜底。
const live = new Map(); // profile → browser
function killTree(browser) {
	if (browser.exitCode !== null || browser.signalCode !== null) return;
	// Windows 上 kill() 只结束主进程，渲染、GPU 子进程还占着配置目录里的文件，故按进程树结束
	if (process.platform === 'win32') spawnSync('taskkill', ['/pid', String(browser.pid), '/T', '/F'], { stdio: 'ignore', windowsHide: true });
	else browser.kill();
}
// 同步删、自己重试：进程刚被结束时 Windows 还没放开文件句柄（EPERM／EBUSY），exit 钩子里又不能 await，
// 故用 Atomics.wait 同步等，最多约 6 秒
const sleepSync = ms => Atomics.wait(new Int32Array(new SharedArrayBuffer(4)), 0, 0, ms);
function removeProfile(profile) {
	let error;
	for (let i = 0; i < 30; i++) {
		try { fs.rmSync(profile, { recursive: true, force: true }); error = null; break; }
		catch (e) { error = e; sleepSync(200); }
	}
	// 删不掉要报出来：以前静默留下，没人发现
	if (error) console.error(`[cdp] 临时目录没删掉 ${profile}: ${error.code || error.message}`);
	live.delete(profile);
}
process.on('exit', () => { for (const [profile, browser] of live) { killTree(browser); removeProfile(profile); } });
async function shutdown(profile, browser) {
	if (!live.has(profile)) return;
	const exited = browser.exitCode !== null ? null : new Promise(r => browser.once('exit', r));
	killTree(browser);
	if (exited) await Promise.race([exited, pause(5000)]);
	removeProfile(profile);
}

// P1-S8-R3 SA：由 Spike/P1S6R4-cdp.cjs 复制，只改了站点映射与缺省地址（sa.localhost:6787）
async function open(base = 'http://sa.localhost:6787') {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), 'erx-s8sa-cdp-'));
	const browser = spawn('C:/Program Files/Google/Chrome/Application/chrome.exe', [
		'--headless=new', '--no-first-run', '--no-default-browser-check',
		'--remote-debugging-port=0', `--user-data-dir=${profile}`,
		'--host-resolver-rules=MAP sa.localhost 127.0.0.1',
		'--window-size=1500,1000', 'about:blank',
	], { stdio: 'ignore', windowsHide: true });
	live.set(profile, browser);
	let port;
	for (let i = 0; i < 100; i++) {
		try { port = fs.readFileSync(path.join(profile, 'DevToolsActivePort'), 'utf8').split('\n')[0]; break; }
		catch { await pause(150); }
	}
	if (!port) { await shutdown(profile, browser); throw Error('Chrome did not start'); }
	const version = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
	const socket = new WebSocket(version.webSocketDebuggerUrl);
	const pending = new Map();
	const events = [];
	let seq = 0, session;
	socket.addEventListener('message', ({ data }) => {
		const message = JSON.parse(data);
		if (!message.id) { events.push(message); return; }
		const item = pending.get(message.id);
		if (!item) return;
		pending.delete(message.id); clearTimeout(item.timer);
		message.error ? item.reject(Error(JSON.stringify(message.error))) : item.resolve(message.result);
	});
	await new Promise((resolve, reject) => { socket.addEventListener('open', resolve); socket.addEventListener('error', reject); });
	function send(method, params = {}, sid = session) {
		const id = ++seq;
		return new Promise((resolve, reject) => {
			const timer = setTimeout(() => { pending.delete(id); reject(Error(`CDP timeout ${method}`)); }, 300000);  // SA：由 60 秒放宽到 300 秒，V-09 整库复制有超过 60 秒的一次
			pending.set(id, { resolve, reject, timer });
			socket.send(JSON.stringify({ id, method, params, sessionId: sid }));
		});
	}
	async function evaluate(expression, sid = session) {
		const r = await send('Runtime.evaluate', { expression, awaitPromise: true, returnByValue: true, userGesture: true }, sid);
		if (r.exceptionDetails) throw Error(JSON.stringify(r.exceptionDetails));
		return r.result.value;
	}
	async function until(expression, timeout = 30000, sid = session) {
		const end = Date.now() + timeout;
		while (Date.now() < end) { if (await evaluate(expression, sid)) return; await pause(200); }
		throw Error(`Condition timed out: ${expression}`);
	}
	async function screenshot(filename, sid = session) {
		const r = await send('Page.captureScreenshot', { format: 'png' }, sid);
		fs.writeFileSync(filename, Buffer.from(r.data, 'base64'));
	}
	async function navigate(url, sid = session) {
		await send('Page.navigate', { url }, sid);
		await until('document.readyState === "complete"', 30000, sid);
	}
	try {
		const target = await send('Target.createTarget', { url: 'about:blank' });
		session = (await send('Target.attachToTarget', { targetId: target.targetId, flatten: true })).sessionId;
		await send('Page.enable'); await send('Runtime.enable'); await send('Network.enable');
		await send('Emulation.setDeviceMetricsOverride', { width: 1500, height: 1000, deviceScaleFactor: 1, mobile: false });
		const url = new URL(base);
		const login = await fetch(`http://127.0.0.1:${url.port || 80}/api/method/login`, {
			method: 'POST', headers: { 'Content-Type': 'application/json', Host: url.host },
			body: JSON.stringify({ usr: 'Administrator', pwd: 'admin' }),
		});
		if (!login.ok) throw Error(`Login failed ${login.status}`);
		const cookie = login.headers.getSetCookie().find(x => x.startsWith('sid='));
		if (!cookie) throw Error('Missing session cookie');
		await send('Network.setCookie', { name: 'sid', value: cookie.split(';')[0].slice(4), domain: url.hostname, path: '/' });
		await send('Page.navigate', { url: `${base}/desk` });
		await until('!!(window.frappe?.boot && frappe.app?.sidebar)');
		return { base, browser: version.Browser, events, send, evaluate, until, screenshot, navigate, pause,
			// 返回 Promise；不 await 也行，进程会等它删完目录才退出
			close() { socket.close(); return shutdown(profile, browser); },
		};
	} catch (error) { socket.close(); await shutdown(profile, browser); throw error; }
}
module.exports = { open };
