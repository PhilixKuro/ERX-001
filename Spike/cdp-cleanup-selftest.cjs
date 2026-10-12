// P1S6R4-cdp.cjs 临时目录清理自测：起本地假站点（login 回 sid，/desk 给出 frappe.boot 与 sidebar），
// 分别走 close()、不 close 直接 process.exit()、登录失败三条路径，各看 %TEMP%\erx-s6-cdp-* 是否删净。
// 用法：node Spike/cdp-cleanup-selftest.cjs        （父进程，逐个起子进程跑三条路径）
const http = require('node:http');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');
const { spawn } = require('node:child_process');
const count = () => fs.readdirSync(os.tmpdir()).filter(n => n.startsWith('erx-s6-cdp-')).length;

const mode = process.argv[2];
if (mode) {
	const { open } = require('./P1S6R4-cdp.cjs');
	(async () => {
		const c = await open(`http://test.localhost:${process.argv[3]}`);
		if (mode === 'close') await c.close();
		else if (mode === 'exit') process.exit(0);
	})().catch(e => { console.log('open failed:', e.message); process.exitCode = mode === 'fail' ? 0 : 1; });
	return;
}

const server = http.createServer((req, res) => {
	if (req.url === '/api/method/login') { res.setHeader('Set-Cookie', 'sid=selftest; Path=/'); res.end('{}'); return; }
	if (req.url === '/api/method/login-fail') { res.statusCode = 401; res.end(); return; }
	res.setHeader('Content-Type', 'text/html');
	res.end('<script>window.frappe={boot:{lang:"zh"},app:{sidebar:{}}}</script>');
});
// 子进程须异步起：spawnSync 会卡住本进程的事件循环，假站点就答不了子进程的请求
function run(m, port) {
	return new Promise(resolve => {
		const child = spawn(process.execPath, [__filename, m, String(port)], { stdio: ['ignore', 'pipe', 'pipe'] });
		let out = '';
		child.stdout.on('data', d => { out += d; });
		child.stderr.on('data', d => { out += d; });
		const timer = setTimeout(() => child.kill(), 60000);
		child.on('exit', code => { clearTimeout(timer); resolve({ code, out }); });
	});
}
server.listen(0, '127.0.0.1', async () => {
	const port = server.address().port;
	const results = [];
	for (const m of ['close', 'exit', 'fail']) {
		const before = count();
		// fail：换一个没在监听的端口，登录 fetch 失败
		const r = await run(m, m === 'fail' ? 1 : port);
		const after = count();
		results.push({ mode: m, exit: r.code, before, after, ok: r.code === 0 && after === before, out: r.out.trim().slice(0, 120) });
	}
	server.close();
	for (const x of results) console.log(JSON.stringify(x));
	process.exitCode = results.every(x => x.ok) ? 0 : 1;
	console.log(results.every(x => x.ok) ? 'ALL OK' : 'FAILED');
});
