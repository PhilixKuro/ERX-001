// P1-S8-R3 SA V-02：由浏览器发起的 whitelisted 请求触发恢复时，请求能否正常返回、或以「后台任务＋前端轮询」拿到完成信号，
// 服务端进程不因换库／恢复而报错退出。三种触发各跑若干轮：
//   S 换库（V-01 ②的做法）：同步请求内改 db_name——V01b-V03-switch.cjs 已跑 15 轮，这里不重复，只在汇总里引用
//   R 同步全量恢复：请求内跑完 bench restore（一年数据约 46 秒）才返回
//   Q 后台任务全量恢复：请求只入队（正式 RQ worker，queue=long），前端每秒轮询状态文件
// 每轮之后：记 web 服务进程号是否没变、服务是否仍应答、以演示账号登录后 desk 是否可用。
// 用法（宿主项目根，6787 已起 sa_serve.py）：node Spike/P1S8R3-SA/V02-browser-restore.cjs [轮数，缺省 2]
const { open } = require('./sa-cdp.cjs');
const N = Number(process.argv[2] || 2);
const BASE = 'http://sa.localhost:6787';
const SQL = '/workspace/Spike/P1S8R3-SA/snap/year.sql.gz';
const ROUTE = '/desk/sales-order';

(async () => {
	const t = await open(BASE);
	const rows = [];
	const ready = `!!(window.frappe?.boot && frappe.session?.user === 'Administrator' && location.pathname === ${JSON.stringify(ROUTE)} && document.querySelector('.frappe-list, .list-row, .no-result'))`;
	const marker = () => t.evaluate(`fetch('/api/method/frappe.sa_probe.marker').then(r => r.json()).then(j => j.message).catch(e => ({error: String(e)}))`);
	const post = (method, body, csrf) => t.evaluate(`fetch('/api/method/${method}', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': ${JSON.stringify(csrf)}}, body: JSON.stringify(${JSON.stringify(body)})}).then(async r => ({status: r.status, body: await r.json().then(j => j.message || j.exc_type).catch(() => null)})).catch(e => ({error: String(e)}))`);
	try {
		await t.navigate(BASE + ROUTE);
		await t.until(ready, 30000);
		const pid0 = (await marker()).pid;
		rows.push({ phase: 'start', pid: pid0 });
		console.log(JSON.stringify(rows.at(-1)));
		for (let i = 1; i <= N; i++) {
			for (const mode of ['R', 'Q']) {
				const r = { mode, i };
				const t0 = Date.now();
				try {
					await t.navigate(BASE + ROUTE);
					await t.until(ready, 30000);
					const csrf = await t.evaluate('frappe.csrf_token');
					// 离开 desk（代替「快进中」遮罩页），免得 desk 后台轮询在恢复期间清掉 cookie
					await t.navigate(BASE + '/api/method/frappe.sa_probe.status_file');
					await t.until(`location.pathname.endsWith('status_file') && !window.frappe`, 10000);
					if (mode === 'R') {
						r.resp = await post('frappe.sa_probe.restore_sync', { sql: SQL }, csrf);
						r.ms_request_returned = Date.now() - t0;
						r.done_signal = r.resp?.body?.state;
					} else {
						r.resp = await post('frappe.sa_probe.restore_async', { sql: SQL }, csrf);
						r.ms_request_returned = Date.now() - t0;
						// 轮询：状态文件 state 由 queued → done/failed；记下轮询期间应答失败的次数
						r.poll_fail = 0; r.polls = 0;
						for (;;) {
							await t.pause(1000);
							r.polls++;
							const s = await t.evaluate(`fetch('/api/method/frappe.sa_probe.status_file').then(r => r.ok ? r.json().then(j => j.message) : {http: r.status}).catch(e => ({error: String(e)}))`);
							if (s.http || s.error) { r.poll_fail++; r.last_poll_error = s; }
							else if (s.state === 'done' || s.state === 'failed') { r.done_signal = s.state; r.job = s; break; }
							if (Date.now() - t0 > 600000) throw Error('10 分钟内没等到完成信号');
						}
					}
					r.ms_done_signal = Date.now() - t0;
					// 恢复替换了 tabSessions：以演示账号登录再回 desk
					r.login = await t.evaluate(`fetch('/api/method/login', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({usr: 'Administrator', pwd: 'admin'})}).then(r => r.status)`);
					await t.navigate(BASE + ROUTE);
					await t.until(ready, 60000);
					r.ms_page_ready = Date.now() - t0;
					const m = await marker();
					r.after = { pid: m.pid, db: m.connected_db, user: m.user, gl: m.gl, marker: m.marker };
					r.same_server_process = m.pid === pid0;
					r.ok = r.done_signal === 'done' && r.same_server_process && m.user === 'Administrator' && m.gl === 5959;
				} catch (e) { r.ok = false; r.error = String(e.message || e).slice(0, 300); r.url = await t.evaluate('location.href').catch(() => null); }
				rows.push(r);
				console.log(JSON.stringify(r));
			}
		}
	} finally {
		const sum = ['R', 'Q'].map(m => { const x = rows.filter(r => r.mode === m); return { mode: m, ok: x.filter(r => r.ok).length, of: x.length,
			ms_request_returned: x.map(r => r.ms_request_returned), ms_page_ready: x.map(r => r.ms_page_ready) }; });
		console.log(JSON.stringify({ summary: sum }));
		await t.close();
	}
})();
