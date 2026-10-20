// P1-S8-R3 SA V-01 ② 与 V-03：浏览器内发起「只改站点 db_name 指向预导好的库」，量到页面可用的耗时，并比较两种回界面做法。
//   做法①（V-03 ①）：换库不带会话 → 页面检测到掉线 → 页面内以演示账号 POST /api/method/login → 跳到指定路由
//   做法②（V-03 ②）：换库前把当前会话行抄进目标库 → 页面直接刷新到指定路由，不登录
// 两份预导库 _s1、_s2 交替切，各 N 轮；每轮记：换库请求耗时、首次读到新库标记、页面在指定路由就绪（frappe.boot 有、用户是 Administrator）。
// 用法（宿主项目根，6787 已起 sa_serve.py）：node Spike/P1S8R3-SA/V01b-V03-switch.cjs [轮数，缺省 4]
const { open } = require('./sa-cdp.cjs');
const N = Number(process.argv[2] || 4);
const BASE = 'http://sa.localhost:6787';
const SRC = '_b8fff8768a271240';
const ROUTE = '/desk/sales-order';

(async () => {
	const t = await open(BASE);
	const rows = [];
	const ready = `!!(window.frappe?.boot && frappe.session?.user === 'Administrator' && location.pathname === ${JSON.stringify(ROUTE)} && document.querySelector('.frappe-list, .list-row, .no-result'))`;
	const marker = () => t.evaluate(`fetch('/api/method/frappe.sa_probe.marker').then(r => r.json()).then(j => j.message)`);
	try {
		await t.navigate(BASE + ROUTE);
		await t.until(ready, 30000);
		rows.push({ phase: 'start', marker: await marker() });
		console.log(JSON.stringify(rows.at(-1)));
		for (let i = 1; i <= N; i++) {
			for (const way of [1, 2]) {
				const target = `${SRC}_${(i + way) % 2 ? 's1' : 's2'}`;
				const r = { way, i, target };
				const t0 = Date.now();
				try {
					// 先停掉 desk 页面自身的后台请求：第 1 次实跑时，desk 在换库期间继续轮询、拿到 403 后按「会话过期」清了 cookie，
					// 把随后登录拿到的 sid 冲掉（V01b-V03-switch.out 第 1 轮）。这里把页面停在同源的一个无脚本地址上，代替将来的「快进中」遮罩页。
					const csrf = await t.evaluate('frappe.csrf_token');
					await t.navigate(BASE + '/api/method/frappe.sa_probe.status_file');
					await t.until(`location.pathname.endsWith('status_file') && !window.frappe`, 10000);
					// 发起换库：与将来的「快进」按钮同一条请求路径（页面内 fetch whitelisted 方法、带 csrf）
					r.switch = await t.evaluate(`fetch('/api/method/frappe.sa_probe.switch', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': ${JSON.stringify(csrf)}}, body: JSON.stringify({db_name: ${JSON.stringify(target)}, carry_session: ${way === 2 ? 1 : 0}})}).then(async r => ({status: r.status, body: (await r.json()).message}))`);
					r.ms_switch_returned = Date.now() - t0;
					// 首次读到新库标记
					for (;;) { const m = await marker(); if (m.connected_db === target) { r.after = m; break; } if (Date.now() - t0 > 30000) throw Error('30 秒内没读到新库'); await t.pause(100); }
					r.ms_new_db_seen = Date.now() - t0;
					if (way === 1) {
						// 做法①：页面内以演示账号登录，再跳路由
						r.login = await t.evaluate(`fetch('/api/method/login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({usr: 'Administrator', pwd: 'admin'})}).then(r => r.status)`);
					}
					await t.navigate(BASE + ROUTE);
					await t.until(ready, 30000);
					r.ms_page_ready = Date.now() - t0;
					const m = await marker();
					r.ok = m.connected_db === target && m.user === 'Administrator';
					r.final = { db: m.connected_db, user: m.user, marker: m.marker, gl: m.gl, pid: m.pid };
					r.url = await t.evaluate('location.pathname');
				} catch (e) { r.ok = false; r.error = String(e.message || e).slice(0, 300); r.url = await t.evaluate('location.href').catch(() => null); }
				rows.push(r);
				console.log(JSON.stringify(r));
			}
		}
		// 收尾：切回原库
		await t.evaluate(`fetch('/api/method/frappe.sa_probe.switch', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': frappe.csrf_token}, body: JSON.stringify({db_name: '${SRC}', carry_session: 1})}).then(r => r.status)`);
	} finally {
		const sum = [1, 2].map(w => { const x = rows.filter(r => r.way === w); const ok = x.filter(r => r.ok); return { way: w, ok: ok.length, of: x.length,
			max_page_ready_ms: ok.length ? Math.max(...ok.map(r => r.ms_page_ready)) : null, max_switch_ms: ok.length ? Math.max(...ok.map(r => r.ms_switch_returned)) : null }; });
		console.log(JSON.stringify({ summary: sum, pids: [...new Set(rows.map(r => r.final?.pid).filter(Boolean))] }));
		await t.close();
	}
})();
