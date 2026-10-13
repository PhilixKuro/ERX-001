// R5 IT-027 渲染级复核：Sales User（非管理员）在测试站打开 CRM，核适配生效、缓存与模块次序。
// 用法：node Spike/P1S6R5-SB/it027-check.cjs <label> [--block]   label 作输出子目录
const fs = require('node:fs');
const { open } = require('../P1S6R4-cdp.cjs');
const label = process.argv[2] || 'zh';
const block = process.argv.includes('--block');
const OUT = `Spike/P1S6R5-SB/it027/${label}`;
fs.mkdirSync(OUT, { recursive: true });
const USER = '_fct_s6_crm_probe@example.com', PWD = 'S6CrmProbe2026';
const LEAD = 'CRM-LEAD-2026-00001';
// 在页面任何脚本之前装好：记录适配脚本标记出现、#app 首次有子节点的先后
const ORDER_PROBE = `(() => {
  const log = window.__s6Order = [];
  let flagged = false;
  const tick = () => {
    if (!flagged && window.__chinaIndependentLabels) { flagged = true; log.push(['adapter', performance.now()]); }
    const app = document.getElementById('app');
    if (app && app.firstElementChild && !log.some(x => x[0] === 'app-mounted')) log.push(['app-mounted', performance.now()]);
    if (log.length < 2) requestAnimationFrame(tick);
  };
  document.addEventListener('readystatechange', () => log.push(['ready:' + document.readyState, performance.now()]));
  requestAnimationFrame(tick);
  new MutationObserver(tick).observe(document, { subtree: true, childList: true });
})();`;
(async () => {
  const c = await open();
  const report = { label, block, user: USER, pages: [] };
  try {
    // 换成探针用户的会话
    await c.send('Network.clearBrowserCookies');
    const login = await fetch('http://127.0.0.1:6787/api/method/login', { method: 'POST', headers: { 'Content-Type': 'application/json', Host: 'test.localhost:6787' }, body: JSON.stringify({ usr: USER, pwd: PWD }) });
    if (!login.ok) throw Error(`probe login ${login.status}`);
    const sid = login.headers.getSetCookie().find(x => x.startsWith('sid=')).split(';')[0].slice(4);
    await c.send('Network.setCookie', { name: 'sid', value: sid, domain: 'test.localhost', path: '/' });
    await c.send('Page.addScriptToEvaluateOnNewDocument', { source: ORDER_PROBE });
    await c.send('Network.setBlockedURLs', { urls: block ? ['*frappe_china/js/independent_app_labels.js*'] : [] });
    // 服务端：同一会话连取两次 HTML，核无缓存串味（crm.py no_cache=1）
    const html = [];
    for (let i = 0; i < 2; i++) {
      const r = await fetch('http://127.0.0.1:6787/crm/leads', { headers: { Host: 'test.localhost:6787', Cookie: `sid=${sid}` } });
      const body = await r.text();
      html.push({ status: r.status, cache_control: r.headers.get('cache-control'), config: body.includes('id="china-ui-labels"'), lang: (body.match(/<html[^>]*lang="(\w+)"/) || [])[1],
        module_before_adapter: body.indexOf('type="module"') > -1 && body.indexOf('type="module"') < body.indexOf('independent_app_labels.js') });
    }
    report.html = html;
    const pages = [
      { id: 'leads', path: '/crm/leads', ready: `!!document.querySelector('#app [class*="list"], #app table, #app .flex')` },
      { id: 'lead-detail', path: `/crm/leads/${LEAD}`, ready: `!!document.querySelector('.sections.flex.flex-col.overflow-y-auto')` },
      { id: 'dashboard', path: '/crm/dashboard', ready: `!!document.querySelector('#app')` },
    ];
    for (const p of pages) {
      const start = c.events.length;
      await c.navigate(`${c.base}${p.path}`);
      await c.until(p.ready, 30000).catch(() => {});
      await c.pause(2500);
      const row = await c.evaluate(`(() => {
        const side = document.querySelector('.sections.flex.flex-col.overflow-y-auto');
        const placeholders = side ? [...side.querySelectorAll('input[placeholder], button, [placeholder]')].map(e => e.getAttribute('placeholder') || e.innerText).filter(Boolean) : [];
        const body = document.body.innerText;
        return {
          url: location.pathname, roles: window.frappe?.boot?.user?.roles?.length ?? null,
          html_lang: document.documentElement.lang, config: !!document.getElementById('china-ui-labels'),
          adapter: !!window.__chinaIndependentLabels, order: window.__s6Order,
          scripts: [...document.scripts].map(s => s.type === 'module' ? 'module:' + (s.src.split('/').pop()) : (s.src ? s.src.split('/').pop() : (s.id || 'inline'))),
          english_hits: ['Getting started', 'Start now', 'Load More', 'Select ', 'Add ', ' of '].filter(w => body.includes(w)),
          placeholder_english: placeholders.filter(t => /^(Add|Select) /.test(t)),
          placeholder_sample: placeholders.slice(0, 6),
          forbidden: /You do not have permission|Not Permitted|403/.test(body),
        };
      })()`);
      row.id = p.id;
      row.console = c.events.slice(start).filter(e => e.method === 'Runtime.consoleAPICalled').map(e => e.params.args.map(a => a.value ?? a.description).join(' ')).filter(t => t.includes('[frappe_china]'));
      row.status = c.events.slice(start).filter(e => e.method === 'Network.responseReceived' && e.params.type === 'Document').map(e => e.params.response.status);
      await c.screenshot(`${OUT}/${p.id}.png`);
      report.pages.push(row);
    }
  } finally {
    fs.writeFileSync(`${OUT}/result.json`, JSON.stringify(report, null, 2));
    await c.close();
  }
  console.log(JSON.stringify(report.html), JSON.stringify(report.pages.map(p => ({ id: p.id, url: p.url, lang: p.html_lang, config: p.config, adapter: p.adapter, order: p.order, en: p.english_hits, ph_en: p.placeholder_english, forbidden: p.forbidden, status: p.status, console: p.console }))));
})().catch(e => { console.error(e); process.exitCode = 1; });
