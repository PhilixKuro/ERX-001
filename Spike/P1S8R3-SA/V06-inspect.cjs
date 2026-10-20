// P1-S8-R3 SA V-06 辅助：看 /crm 页面的 csrf 全局、线索页「转换为商机」弹窗的 DOM 与 Vue 组件挂载点
const { open } = require('./sa-cdp.cjs');
(async () => {
	const t = await open('http://sa.localhost:6787');
	try {
		await t.navigate('http://sa.localhost:6787/crm/leads/CRM-LEAD-2026-00012');
		await t.until(`[...document.querySelectorAll('button')].some(b => /转换为商机/.test(b.textContent))`, 30000);
		const g = await t.evaluate(`({csrf_window: typeof window.csrf_token, csrf_frappe: typeof window.frappe, keys: Object.keys(window).filter(k => /csrf|frappe|boot/i.test(k))})`);
		console.log(JSON.stringify(g));
		await t.evaluate(`[...document.querySelectorAll('button')].find(b => /转换为商机/.test(b.textContent)).click()`);
		await t.pause(3000);
		console.log(JSON.stringify(await t.evaluate(`(() => {
			const dlgs = [...document.querySelectorAll('[role=dialog], [data-dialog], .fixed')];
			const d = document.querySelector('[role=dialog]');
			let comp = null;
			for (let x = d?.querySelector('button'); x && !comp; x = x.parentElement) { const c = x.__vueParentComponent; for (let p = c; p; p = p.parent) { if (p.setupState && 'existingContact' in p.setupState) { comp = p; break; } } }
			const chain = []; for (let p = d?.querySelector('button')?.__vueParentComponent; p && chain.length < 12; p = p.parent) chain.push(p.type?.__name || p.type?.name || '?');
			return {dialogs: dlgs.length, roleDialog: !!d, buttons: d ? [...d.querySelectorAll('button')].map(b => b.textContent.trim()) : [],
				labels: d ? [...d.querySelectorAll('label, span, div')].filter(e => e.children.length === 0).map(e => e.textContent.trim()).filter(Boolean).slice(0, 40) : [],
				inputs: d ? [...d.querySelectorAll('input, textarea')].map(i => ({type: i.type, ph: i.placeholder, v: i.value})) : [],
				compFound: !!comp, chain, vueKeys: d ? Object.keys(d.querySelector('button') || {}).filter(k => k.startsWith('__vue')) : []};
		})()`), null, 1));
	} finally { await t.close(); }
})();
