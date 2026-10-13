// E R11 只读：演示站 CRM 页读 lang／翻页文字；另在 about:blank 用真实 ListFooter 结构跑 independent_app_labels.js 的 DOM 部分。
// 宿主 `node Spike/P1S6R11-E/crm-csv/crm_live.cjs`；不点任何保存／提交，只读 DOM。截图写本目录。
const fs = require('node:fs');
const path = require('node:path');
const { open } = require('../../P1S6R4-cdp.cjs');
const OUT = __dirname;
const JS = fs.readFileSync(path.resolve(__dirname, '../../../frappe-bench/apps/frappe_china/frappe_china/public/js/independent_app_labels.js'), 'utf8');

(async () => {
	const c = await open('http://localhost:8000');
	const out = { browser: c.browser };
	try {
		for (const [name, route] of [['leads', '/crm/leads/view/list'], ['dashboard', '/crm/dashboard'], ['lead-detail', '/crm/leads/CRM-LEAD-2026-00001']]) {
			await c.navigate(c.base + route);
			await c.until('!!document.querySelector("#app") && document.body.innerText.trim().length > 50', 30000).catch(() => {});
			await c.pause(4000);
			out[name] = await c.evaluate(`(() => {
				const html = document.documentElement.outerHTML.slice(0, 120);
				const pager = [...document.querySelectorAll('div')].filter(d => d.children.length === 3 && /^[\\d,]+$/.test(d.children[0].textContent.trim()) && /^[\\d,]+$/.test(d.children[2].textContent.trim())).map(d => [...d.children].map(x => x.textContent.trim()));
				const buttons = [...document.querySelectorAll('button')].map(b => b.textContent.trim()).filter(t => /load more|加载更多/i.test(t));
				const panel = document.querySelector('.sections.flex.flex-col.overflow-y-auto');
				const ph = panel ? [...panel.querySelectorAll('[placeholder]')].map(e => e.getAttribute('placeholder')) : null;
				const phText = panel ? [...panel.querySelectorAll('*')].filter(e => e.children.length === 0 && /\\.\\.\\.$|……$/.test(e.textContent.trim())).map(e => e.textContent.trim()) : null;
				return { lang: document.documentElement.lang, htmlHead: html, pager, buttons, marker: !!window.__chinaIndependentLabels, panelPlaceholders: ph, panelPlaceholderTexts: phText };
			})()`);
			await c.screenshot(path.join(OUT, `live-${name}.png`));
		}
		// DOM 模拟：真实 ListFooter 结构（frappe-ui ListFooter.vue:2-26，Button 无 tooltip 时根即 <button>）
		await c.navigate('about:blank');
		const messages = { of: '/', 'Load More': '加载更多', Empty: '空', Select: '单选', 'Select {0}...': '选择{0}……' };
		out.sim = await c.evaluate(`(async () => {
			document.body.innerHTML = '<script type="application/json" id="china-ui-labels"></' + 'script><div id="app"></div>';
			document.getElementById('china-ui-labels').textContent = ${JSON.stringify(JSON.stringify({ lang: 'zh', app: 'crm', messages }))};
			const app = document.getElementById('app');
			const footer = (withButton) => '<div class="flex justify-between gap-2"><div class="tabs"><button>20</button><button>50</button></div><div class="flex items-center">' + (withButton ? '<button><span>Load More</span></button><div class="mx-3 h-[80%] border-l"></div>' : '') + '<div class="flex items-center gap-1"><div>20</div><div>of</div><div>22</div></div></div></div>';
			app.innerHTML = '<section id="a">' + footer(true) + '</section><section id="b">' + footer(false) + '</section>'
				+ '<section id="c"><div class="row"><div>Board</div><div>of</div><div>Directors</div></div><div class="row"><div>12</div><div>of</div><div>x</div></div></section>'
				+ '<section id="d"><div class="dataimport"><button><span> Load More </span></button></div></section>'
				+ '<section id="e"><div class="kanban"><div><div>3</div><div>of</div><div>9</div></div></div><div><button>Load More</button></div></section>'
				+ '<section id="f"><div class="sections flex flex-col overflow-y-auto"><span>单选 Lead Owner...</span><input placeholder="单选 Lead Owner..."></div><div class="outside"><span>单选 Lead Owner...</span></div></section>';
			window.__ = k => ({ 'Lead Owner': '线索负责人' })[k] || k;
			const s = document.createElement('script'); s.textContent = ${JSON.stringify(JS)}; document.body.appendChild(s);
			await new Promise(r => setTimeout(r, 50));
			const snap = () => ({
				a: document.querySelector('#a').innerText.replace(/\\s+/g, ' ').trim(),
				b: document.querySelector('#b').innerText.replace(/\\s+/g, ' ').trim(),
				c: document.querySelector('#c').innerText.replace(/\\s+/g, ' ').trim(),
				d: document.querySelector('#d').innerText.trim(),
				e: document.querySelector('#e').innerText.replace(/\\s+/g, ' ').trim(),
				f_in: document.querySelector('#f .sections span').textContent + ' | ' + document.querySelector('#f input').getAttribute('placeholder'),
				f_out: document.querySelector('#f .outside span').textContent,
			});
			const initial = snap();
			// 晚到的按钮：b 区 of 已是 /，再插入 Load More（模拟 v-if showLoadMore 变真）
			const right = document.querySelector('#b .flex.items-center');
			const btn = document.createElement('button'); btn.innerHTML = '<span>Load More</span>';
			right.insertBefore(btn, right.firstChild);
			await new Promise(r => setTimeout(r, 50));
			const late = snap().b;
			// 行数更新：20 → 22，按钮消失后再出现
			return { initial, late };
		})()`);
	} catch (e) { out.error = String(e && e.stack || e); }
	fs.writeFileSync(path.join(OUT, 'crm_live.json'), JSON.stringify(out, null, 1));
	console.log(JSON.stringify(out, null, 1));
	await c.close();
})();
