// P1-S8-R3 SA V-06：/crm 独立前端内，注入脚本程序化完成「填字段、点按钮、等保存完成」三类操作，
// 能否稳定完成线索 → 商机转换。两种做法各跑 N 次：
//   A DOM 驱动：在线索页点「转换为商机」→ 弹窗里按占位文字找到两个必填输入框（预期商机价值、预期关闭日期），
//     用原生 value setter + input/change/Enter/blur 事件填值 → 点「转换」→ 等路由跳到 /crm/deals/<id>
//   B 接口驱动：页面内 fetch 调 crm_lead.convert_to_deal（与弹窗同一个方法）→ 用页面自己的 vue-router 跳到商机页
// 每轮先用 REST 新建一条线索；转换后经 REST 读回商机与线索核对。
// 前几次实跑的探针错（已改）：按钮文字是 frappe_china 译名「转换为商机」；/crm 的 csrf 在 window.csrf_token、没有 frappe 全局；
// 生产构建不在 DOM 上挂 Vue 组件实例，故 A 只能走真实输入框。
// 用法（宿主项目根）：node Spike/P1S8R3-SA/V06-crm-convert.cjs [轮数，缺省 5]
const { open } = require('./sa-cdp.cjs');
const N = Number(process.argv[2] || 5);
const BASE = 'http://sa.localhost:6787';
const CLOSE = new Date(Date.now() + 30 * 864e5).toISOString().slice(0, 10);
const BTN = /转换为商机|转为商机|Convert to Deal/;

(async () => {
	const t = await open(BASE);
	const results = [];
	// 页面内调接口：desk 与 /crm 的 csrf 全局不同，两处都兼容
	const call = (method, body) => t.evaluate(`fetch('/api/method/${method}', {method: 'POST', headers: {'Content-Type': 'application/json', 'X-Frappe-CSRF-Token': window.csrf_token || window.frappe?.csrf_token}, body: JSON.stringify(${JSON.stringify(body)})}).then(r => r.json())`);
	const getDoc = (doctype, name) => t.evaluate(`fetch('/api/resource/${encodeURIComponent(doctype)}/' + encodeURIComponent(${JSON.stringify(name)})).then(r => r.json()).then(j => j.data || j)`);
	try {
		for (let i = 1; i <= N; i++) {
			for (const mode of ['A', 'B']) {
				const tag = `${mode}${i}-${Date.now() % 100000}`;
				const r = { mode, i };
				const t0 = Date.now();
				try {
					await t.navigate(`${BASE}/crm/leads/view/list`);
					await t.until('!!window.csrf_token', 30000);
					const lead = (await call('frappe.client.insert', { doc: { doctype: 'CRM Lead', first_name: `SA${tag}`, organization: `SA 客户 ${tag}`, status: 'New' } })).message.name;
					r.lead = lead;
					await t.navigate(`${BASE}/crm/leads/${lead}`);
					await t.until(`[...document.querySelectorAll('button')].some(b => ${BTN}.test(b.textContent))`, 30000);
					if (mode === 'A') {
						await t.evaluate(`[...document.querySelectorAll('button')].find(b => ${BTN}.test(b.textContent)).click()`);
						await t.until(`!!document.querySelector('[role=dialog] input[placeholder="预期关闭日期"]')`, 15000);
						r.filled = await t.evaluate(`(async () => {
							const dlg = document.querySelector('[role=dialog]');
							const pause = ms => new Promise(r => setTimeout(r, ms));
							const fill = async (ph, v) => {
								const el = dlg.querySelector('input[placeholder="' + ph + '"]');
								el.focus(); el.dispatchEvent(new Event('focus', {bubbles: true}));
								Object.getOwnPropertyDescriptor(HTMLInputElement.prototype, 'value').set.call(el, v);
								el.dispatchEvent(new Event('input', {bubbles: true}));
								el.dispatchEvent(new Event('change', {bubbles: true}));
								el.dispatchEvent(new KeyboardEvent('keydown', {key: 'Enter', bubbles: true}));
								el.blur(); el.dispatchEvent(new Event('blur', {bubbles: true}));
								await pause(300);
								return dlg.querySelector('input[placeholder="' + ph + '"]').value;
							};
							return {value: await fill('预期商机价值', '1000'), date: await fill('预期关闭日期', '${CLOSE}')};
						})()`);
						await t.evaluate(`[...document.querySelectorAll('[role=dialog] button')].find(b => /^\\s*(转换|Convert)\\s*$/.test(b.textContent)).click()`);
						r.dialogError = await t.evaluate(`new Promise(r => setTimeout(() => r(document.querySelector('[role=dialog]')?.innerText.match(/.*(必填|required|错误|Error).*/)?.[0] || null), 1500))`);
					} else {
						const resp = await call('crm.fcrm.doctype.crm_lead.crm_lead.convert_to_deal', { lead, deal: { expected_deal_value: 1000, expected_closure_date: CLOSE } });
						r.api = resp.message || resp.exc_type;
						if (!resp.message) throw Error('convert_to_deal 返回 ' + JSON.stringify(resp).slice(0, 200));
						await t.evaluate(`document.querySelector('#app').__vue_app__.config.globalProperties.$router.push(${JSON.stringify('/deals/' + resp.message)})`);
					}
					await t.until(`/\\/crm\\/deals\\/[^/]+$/.test(location.pathname)`, 20000);
					const deal = await t.evaluate('location.pathname.split("/").pop()');
					// 商机页渲染完成：页面正文出现该商机号
					await t.until(`document.body.innerText.includes(location.pathname.split('/').pop())`, 15000);
					r.ms_to_deal_page = Date.now() - t0;
					const d = await getDoc('CRM Deal', deal);
					const l = await getDoc('CRM Lead', lead);
					r.deal = { name: d.name, lead: d.lead, expected_deal_value: d.expected_deal_value, expected_closure_date: d.expected_closure_date };
					r.leadConverted = l.converted;
					r.ok = d.lead === lead && l.converted == 1 && Number(d.expected_deal_value) === 1000 && d.expected_closure_date === CLOSE;
				} catch (e) { r.ok = false; r.error = String(e.message || e).slice(0, 300); r.url = await t.evaluate('location.href').catch(() => null); }
				r.ms = Date.now() - t0;
				results.push(r);
				console.log(JSON.stringify(r));
			}
		}
	} finally {
		const summary = ['A', 'B'].map(m => ({ mode: m, ok: results.filter(r => r.mode === m && r.ok).length, of: results.filter(r => r.mode === m).length }));
		console.log(JSON.stringify({ summary }));
		await t.close();
	}
})();
