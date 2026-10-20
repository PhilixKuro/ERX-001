// P1-S8-R3 SA V-09：彩排模式「每到幕首存快照」——由前端触发存快照，在一年数据量下耗时是否 ≤ 60 秒。两种快照形态各 3 次：
//   bench：bench backup（与 docker/backup.sh 同一条命令，出 .sql.gz）
//   clone：整库复制成一个新库（V-01 ② 换库要用的形态）
// 用法（宿主项目根，6787 已起 sa_serve.py）：node Spike/P1S8R3-SA/V09-browser-backup.cjs [bench|clone，缺省两种都跑]
const { open } = require('./sa-cdp.cjs');
const BASE = 'http://sa.localhost:6787';

(async () => {
	const t = await open(BASE);
	const rows = [];
	try {
		const csrf = await t.evaluate('frappe.csrf_token');
		const gl = await t.evaluate(`fetch('/api/method/frappe.sa_probe.marker').then(r => r.json()).then(j => j.message.gl)`);
		for (const mode of (process.argv[2] ? [process.argv[2]] : ['bench', 'clone'])) {
			for (let i = 1; i <= 3; i++) {
				const t0 = Date.now();
				const r = await t.evaluate(`fetch('/api/method/frappe.sa_probe.backup_now', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': ${JSON.stringify(csrf)}}, body: JSON.stringify({mode: '${mode}'})}).then(async r => ({status: r.status, body: (await r.json()).message}))`);
				rows.push({ mode, i, gl, ms_browser: Date.now() - t0, ...r });
				console.log(JSON.stringify(rows.at(-1)));
			}
		}
	} finally {
		console.log(JSON.stringify({ summary: ['bench', 'clone'].map(m => ({ mode: m, ok: rows.filter(r => r.mode === m && r.body?.ok).length, ms_browser: rows.filter(r => r.mode === m).map(r => r.ms_browser) })) }));
		await t.close();
	}
})();
