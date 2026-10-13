// 逐屏核 v2（TS-022 第 2 步；A21／A22；DEC-032～034）。基于 Spike/P1S6R4-screen-check.js，旧文件不改。
// 用法：node Spike/P1S6R6-screen-check.js <baseUrl> <screens.json> <outDir> [values.json]
//   values.json（可选）：{占位名: 值}，覆盖 screens.json 顶层 variables 的运行期解析结果。
//   环境变量 SCREENS_ONLY=id1,id2 只跑这几屏（复跑用）。
// 启动、登录、截图沿用 Spike/P1S6R4-cdp.cjs（headless Chrome + DevTools 协议，无 npm 依赖）。
//
// screens.json 顶层：
//   allow {词: 理由}、data_selectors [{selector, reason}]、data_patterns [{pattern, reason}]、
//   include_selectors [{selector, reason}]、default_data {词: {doctype, name, reason}}、
//   variables {占位: {from, doctype, filters, order_by, index, value}}、trad_chars_file、screens [...]
// 每屏：{id, stage, state, route|url, sidebar, wait_for, steps, after, extract_root, data_selectors, dialog, note}
//   state ∈ blank／saved／prefilled／dialog／list／report
//   dialog（确认框屏）：{action: "submit"|"cancel", doctype, name, button}
// 输出 <outDir>/result.json：每屏 {id, stage, state, pass, english, traditional, title_issues, default_data,
//   sidebar_title, screenshot, ...}；pass = english、traditional、title_issues 皆空 且 sidebar_ok。
const fs = require('node:fs');
const path = require('node:path');
const {open} = require('./P1S6R4-cdp.cjs');
const {extractVisibleText, judge} = require('./P1S6R6-visible-text.cjs');

const STATES = new Set(['blank', 'saved', 'prefilled', 'dialog', 'list', 'report']);
const [base, screenFile, outDir, valuesFile] = process.argv.slice(2);
if (!base || !screenFile || !outDir) {
  console.error('usage: node Spike/P1S6R6-screen-check.js <baseUrl> <screens.json> <outDir> [values.json]');
  process.exit(2);
}
const spec = JSON.parse(fs.readFileSync(screenFile, 'utf8'));

// ---------- 静态校验（不连站点即可发现的问题，直接退出） ----------
function validateSpec() {
  const problems = [];
  if (Array.isArray(spec.allow)) problems.push('allow must be an object {word: reason}');
  for (const [word, reason] of Object.entries(spec.allow || {})) if (!reason) problems.push(`allow ${word} has no reason`);
  for (const key of ['data_selectors', 'include_selectors']) {
    for (const item of spec[key] || []) if (!item.selector || !item.reason) problems.push(`${key} entry needs selector and reason`);
  }
  for (const item of spec.data_patterns || []) {
    if (!item.pattern || !item.reason) problems.push('data_patterns entry needs pattern and reason');
    else try { new RegExp(item.pattern, 'g'); } catch (e) { problems.push(`bad pattern ${item.pattern}: ${e.message}`); }
  }
  for (const [word, item] of Object.entries(spec.default_data || {})) {
    if (!item || !item.doctype || !item.name || !item.reason) problems.push(`default_data ${word} needs doctype, name, reason`);
  }
  const ids = new Set();
  for (const screen of spec.screens || []) {
    if (!screen.id || ids.has(screen.id)) problems.push(`duplicate or missing id ${screen.id}`);
    ids.add(screen.id);
    if (!STATES.has(screen.state)) problems.push(`${screen.id}: bad state ${screen.state}`);
    if (spec.phases && !spec.phases.some(p => p.id === screen.phase)) problems.push(`${screen.id}: unknown phase ${screen.phase}`);
    if (!screen.route && !screen.url) problems.push(`${screen.id}: needs route or url`);
    if (!screen.dialog && (!screen.wait_for || screen.wait_for === '!!document.body')) problems.push(`${screen.id}: needs a specific wait_for`);
    if (screen.dialog && !['submit', 'cancel'].includes(screen.dialog.action)) problems.push(`${screen.id}: dialog.action must be submit|cancel`);
    if (screen.state === 'prefilled') {
      // 由上游「创建」生成的屏：须经界面点击进入（菜单／按钮），不得用 set_route 直达
      if (/set_route/.test(JSON.stringify(screen.steps || []))) problems.push(`${screen.id}: prefilled screens must use the Create menu, not set_route`);
      if (!(screen.steps || []).some(step => step.menu || step.button || step.click)) problems.push(`${screen.id}: prefilled screen needs a menu/button/click step`);
    }
    for (const name of JSON.stringify(screen).match(/\{\{(\w+)\}\}/g) || []) {
      const key = name.slice(2, -2);
      if (!(spec.variables || {})[key]) problems.push(`${screen.id}: placeholder ${name} not declared in variables`);
    }
  }
  if (problems.length) {
    console.error('screens.json invalid:\n  ' + problems.join('\n  '));
    process.exit(2);
  }
}
validateSpec();
// 只做静态校验、不开浏览器不连站点：SCREENS_VALIDATE_ONLY=1
if (process.env.SCREENS_VALIDATE_ONLY) {
  const counts = {};
  for (const screen of spec.screens) counts[screen.state] = (counts[screen.state] || 0) + 1;
  console.log(JSON.stringify({valid: true, screens: spec.screens.length, by_state: counts, skipped: spec.screens.filter(s => s.skip).map(s => s.id)}));
  process.exit(0);
}

const tradFile = path.resolve(path.dirname(path.resolve(screenFile)), spec.trad_chars_file || 'P1S6R6-trad-chars.json');
const tradChars = JSON.parse(fs.readFileSync(tradFile, 'utf8')).chars;
if (!tradChars || !tradChars.length) throw Error('Empty traditional character table: ' + tradFile);
const allow = new Set(Object.keys(spec.allow || {}));
const overrides = valuesFile ? JSON.parse(fs.readFileSync(valuesFile, 'utf8')) : {};
const only = process.env.SCREENS_ONLY ? new Set(process.env.SCREENS_ONLY.split(',').map(s => s.trim())) : null;
// 造数与核屏交替：每个造数步做完，跑 SCREENS_PHASE=<该步> 的屏（screens.json 顶层 phases 定次序）
const phase = process.env.SCREENS_PHASE || null;
if (phase && !(spec.phases || []).some(p => p.id === phase)) { console.error('unknown phase ' + phase); process.exit(2); }
fs.mkdirSync(outDir, {recursive: true});

const js = value => JSON.stringify(value);
const encodeLabel = label => encodeURIComponent(label); // page.js 的 data-label 用 encodeURIComponent

// ---------- 页面内 REST（与浏览器同一会话 cookie） ----------
async function rest(c, url) {
  return c.evaluate(`fetch(${js(url)}, {headers: {Accept: 'application/json'}}).then(async r => ({status: r.status, body: await r.json().catch(() => null)}))`);
}
async function getDoc(c, doctype, name) {
  return rest(c, `/api/resource/${encodeURIComponent(doctype)}/${encodeURIComponent(name)}`);
}

async function checkDefaultData(c) {
  const missing = [];
  for (const [word, item] of Object.entries(spec.default_data || {})) {
    const r = await getDoc(c, item.doctype, item.name);
    if (r.status !== 200) missing.push(`${word} -> ${item.doctype}/${item.name} (HTTP ${r.status})`);
  }
  return missing;
}

// keys：只解析这几个（省略则全部）。已解析的不重查——界面步骤中途建出来的单据（由上游「创建」生成）
// 在用到它的屏开跑前才解析，故 runScreen 前对缺的占位再调一次。
async function resolveVariables(c, values = {}, keys = null) {
  const unresolved = {};
  for (const [key, item] of Object.entries(spec.variables || {})) {
    if (keys && !keys.includes(key)) continue;
    if (key in values) continue;
    if (key in overrides) { values[key] = overrides[key]; continue; }
    if ('value' in item) { values[key] = item.value; continue; }
    if (!item.doctype) { unresolved[key] = 'no doctype/value'; continue; }
    const index = item.index || 0;
    // filters 里可引用先前已解析的占位（按 variables 的声明次序）
    let filtersText = js(item.filters || []);
    const pending = (filtersText.match(/\{\{(\w+)\}\}/g) || []).map(m => m.slice(2, -2)).filter(k => !(k in values));
    if (pending.length) { unresolved[key] = 'depends on unresolved ' + pending.join(','); continue; }
    filtersText = filtersText.replace(/\{\{(\w+)\}\}/g, (_, k) => js(String(values[k])).slice(1, -1));
    const params = new URLSearchParams({
      fields: js(['name']), filters: filtersText,
      order_by: item.order_by || 'creation desc', limit_page_length: String(index + 1),
    });
    const r = await rest(c, `/api/resource/${encodeURIComponent(item.doctype)}?${params}`);
    const rows = r.body?.data || [];
    if (r.status === 200 && rows.length > index) values[key] = rows[index].name;
    else unresolved[key] = `HTTP ${r.status}, ${rows.length} rows`;
  }
  return unresolved;
}

function substitute(screen, values) {
  const missing = new Set();
  const text = JSON.stringify(screen).replace(/\{\{(\w+)\}\}/g, (_, key) => {
    if (!(key in values)) { missing.add(key); return `{{${key}}}`; }
    return JSON.stringify(String(values[key])).slice(1, -1);
  });
  if (missing.size) throw Error('Unresolved placeholders: ' + [...missing].join(', '));
  return JSON.parse(text);
}

// ---------- 页面驱动 ----------
// 找可见元素：selector 加可选文字（字符串或候选数组，完全相等优先、其次包含）
// index：无文字时取第几个可见元素（默认 -1 即最后一个，后打开的对话框在 DOM 后面）
function findExpr(selector, text, index = -1) {
  const texts = text == null ? null : (Array.isArray(text) ? text : [text]);
  return `(() => {
    const vis = e => { const r = e.getBoundingClientRect(); const s = getComputedStyle(e); return r.width > 0 && r.height > 0 && s.visibility !== 'hidden' && s.display !== 'none'; };
    const all = [...document.querySelectorAll(${js(selector)})].filter(vis);
    const texts = ${js(texts)};
    if (!texts) return all.at(${Number(index)}) || null;
    const label = e => (e.innerText || e.textContent || '').replace(/\\s+/g, ' ').trim();
    for (const t of texts) { const hit = all.find(e => label(e) === t); if (hit) return hit; }
    for (const t of texts) { const hit = all.find(e => label(e).includes(t)); if (hit) return hit; }
    return null;
  })()`;
}
// real：用 CDP 鼠标事件点（Radix 下拉菜单在 pointerdown 上打开，element.click() 不触发）
async function click(c, selector, text, timeout, {index = -1, real = false} = {}) {
  const expr = findExpr(selector, text, index);
  await c.until(`!!${expr}`, timeout || 30000);
  if (!real) {
    await c.evaluate(`(() => { const e = ${expr}; e.scrollIntoView({block: 'center'}); e.click(); return true; })()`);
    return;
  }
  const box = await c.evaluate(`(() => { const e = ${expr}; e.scrollIntoView({block: 'center'}); const r = e.getBoundingClientRect(); return {x: r.left + r.width / 2, y: r.top + r.height / 2}; })()`);
  await c.send('Input.dispatchMouseEvent', {type: 'mouseMoved', x: box.x, y: box.y});
  await c.send('Input.dispatchMouseEvent', {type: 'mousePressed', x: box.x, y: box.y, button: 'left', clickCount: 1});
  await c.send('Input.dispatchMouseEvent', {type: 'mouseReleased', x: box.x, y: box.y, button: 'left', clickCount: 1});
}
async function pressKey(c, combo) {
  // 例："Ctrl+K"；CDP 修饰位：Alt=1 Ctrl=2 Meta=4 Shift=8
  const parts = combo.split('+');
  const key = parts.pop();
  const modifiers = parts.reduce((m, p) => m | ({Alt: 1, Ctrl: 2, Control: 2, Meta: 4, Shift: 8}[p] || 0), 0);
  const code = key.length === 1 ? 'Key' + key.toUpperCase() : key;
  const keyValue = key.length === 1 ? key.toLowerCase() : key;
  const vk = key.length === 1 ? key.toUpperCase().charCodeAt(0) : ({Escape: 27, Enter: 13, Tab: 9}[key] || 0);
  for (const type of ['keyDown', 'keyUp']) {
    await c.send('Input.dispatchKeyEvent', {type, modifiers, key: keyValue, code, windowsVirtualKeyCode: vk, nativeVirtualKeyCode: vk});
  }
}

const FORM_IDLE = '!frappe.dom.freeze_count && !frappe.ui.form.is_saving';
async function runStep(c, step) {
  if (step.evaluate) await c.evaluate(step.evaluate);
  else if (step.menu) {
    // 「创建」等分组按钮：.inner-group-button[data-label=encodeURIComponent(组名)] > button，菜单项 .dropdown-item（page.js:565-585、622-649）
    const groups = Array.isArray(step.menu) ? step.menu : [step.menu];
    const groupSelector = groups.map(g => `.page-actions .inner-group-button[data-label="${encodeLabel(g)}"] > button`).join(',');
    await click(c, groupSelector, null, step.timeout);
    await c.until(`!!${findExpr('.page-actions .inner-group-button .dropdown-menu.show .dropdown-item', step.item)}`, step.timeout || 10000);
    await click(c, '.page-actions .inner-group-button .dropdown-menu.show .dropdown-item', step.item, step.timeout);
  } else if (step.open_menu) {
    // 只展开分组菜单、不点项（核菜单本身的文案，如销售订单「状态」菜单里的「关闭」）
    const groups = Array.isArray(step.open_menu) ? step.open_menu : [step.open_menu];
    await click(c, groups.map(g => `.page-actions .inner-group-button[data-label="${encodeLabel(g)}"] > button`).join(','), null, step.timeout);
    await c.until(`!!document.querySelector('.page-actions .inner-group-button .dropdown-menu.show')`, step.timeout || 10000);
  } else if (step.button) {
    // 不分组的自定义按钮（工单「开始」「完成」）：.custom-actions > button[data-label]（page.js:651-664）
    await click(c, '.page-actions .custom-actions > button, .page-actions .custom-actions > .btn', step.button, step.timeout);
  } else if (step.primary) {
    // 主按钮（保存／提交／新建）：.page-actions .primary-action（page.html:85；toolbar.js:799-845）
    await click(c, '.page-actions .primary-action', step.primary, step.timeout);
  } else if (step.secondary) {
    await click(c, '.page-actions .btn-secondary', step.secondary, step.timeout);
  } else if (step.dialog_primary) {
    await click(c, '.modal.show .modal-footer .btn-modal-primary', step.dialog_primary === true ? null : step.dialog_primary, step.timeout);
  } else if (step.dialog_close) {
    await click(c, '.modal.show .btn-modal-close', null, step.timeout);
    await c.until(`!document.querySelector('.modal.show')`, 10000);
  } else if (step.dialog_fill) {
    await c.until('!!window.cur_dialog', 10000);
    await c.evaluate(`Promise.resolve(cur_dialog.set_value(${js(step.dialog_fill)}, ${step.value_expr || js(step.value)})).then(() => true)`);
  } else if (step.fill) {
    // 表单填值：头字段 cur_frm.set_value；子表行 frappe.model.set_value
    if (step.table) await c.evaluate(`(() => { const row = (cur_frm.doc[${js(step.table)}] || [])[${step.row || 0}]; if (!row) throw Error('row missing'); return frappe.model.set_value(row.doctype, row.name, ${js(step.fill)}, ${js(step.value)}).then(() => true); })()`);
    else {
      // value_expr：页面内求值的表达式（如 frappe.datetime.add_days(frappe.datetime.get_today(), 1)）
      const valueExpr = step.value_expr || js(step.value);
      await c.evaluate(`Promise.resolve(cur_frm.set_value(${js(step.fill)}, ${valueExpr})).then(() => true)`);
    }
  } else if (step.field_button) {
    // Button 型字段：.frappe-control[data-fieldname=…] button
    await click(c, `.frappe-control[data-fieldname="${step.field_button}"] button`, null, step.timeout);
  } else if (step.tab) {
    await click(c, `.form-tabs-list .nav-link[data-fieldname="${step.tab}"]`, null, step.timeout);
  } else if (step.scroll_to) {
    await c.evaluate(`(() => { cur_frm.scroll_to_field(${js(step.scroll_to)}); return true; })()`);
  } else if (step.sidebar_item) {
    await click(c, '.body-sidebar .sidebar-item-container .item-anchor', step.sidebar_item, step.timeout);
  } else if (step.key) await pressKey(c, step.key);
  else if (step.click) await click(c, step.click, step.text, step.timeout, {index: step.index ?? -1, real: !!step.real});
  if (step.wait_for) await c.until(step.wait_for, step.timeout || 30000);
  if (step.save_wait) await c.until(`!!window.cur_frm && !cur_frm.is_new() && !cur_frm.is_dirty() && ${FORM_IDLE}`, step.timeout || 60000);
  await c.pause(step.pause || 300);
}

async function openScreen(c, screen) {
  // 上一屏可能留下未保存的新单（预填态）：非 developer_mode 下 form.js:1499 挂了 beforeunload，会挡住导航
  try {
    await c.evaluate(`(() => { try { if (window.cur_frm?.beforeUnloadListener) removeEventListener('beforeunload', cur_frm.beforeUnloadListener, {capture: true}); window.onbeforeunload = null; } catch (e) {} return true; })()`);
  } catch {}
  const target = screen.url ? new URL(screen.url, base) : null;
  const pathName = target ? target.pathname : '/' + screen.route;
  if (pathName.startsWith('/desk')) {
    await c.navigate(base + '/desk');
    await c.until('!!document.querySelector(".desktop-icon") && !!window.frappe?.get_route()?.length');
    if (screen.sidebar === 'Business Flow') {
      // 与演示同一入口：首页点「业务流程」图标进自有侧栏（P1S6R4 同法）
      await c.evaluate(`(() => { const icon = [...document.querySelectorAll('.desktop-icon')].find(e => e.innerText.includes('业务流程')); if (!icon) throw Error('Business Flow icon missing'); icon.click(); return true; })()`);
      await c.until(`frappe.app.sidebar.sidebar_title === 'Business Flow' && !!window.frappe?.get_route()?.length`);
      await c.pause(500);
    } else if (screen.sidebar) await c.evaluate(`frappe.app.sidebar.setup(${js(screen.sidebar)}); true`);
    const deskPath = decodeURI(pathName).replace(/^\/desk\/?/, '');
    if (deskPath) {
      await c.evaluate(`frappe.set_route(${js(deskPath)}); true`); // 打开本屏的起点页；「创建」类屏在 steps 里经菜单进下游
      const expected = /\/new-/.test(deskPath) ? '/desk/' + deskPath.replace(/\/new-.*/, '/new-') : '/desk/' + deskPath;
      await c.until(`decodeURI(location.pathname).startsWith(${js(expected)})`);
    }
  } else await c.navigate(target ? target.href : new URL(pathName, base).href);
}

async function capture(c, screen, row) {
  const exclusions = [...(spec.data_selectors || []), ...(screen.data_selectors || [])];
  const includes = [...(spec.include_selectors || []), ...(screen.include_selectors || [])].map(item => item.selector);
  const root = screen.extract_root || (screen.state === 'dialog' ? '.modal.show' : null);
  row.url = await c.evaluate('location.href');
  row.sidebar_title = await c.evaluate('window.frappe?.app?.sidebar?.sidebar_title || null');
  row.text_entries = await c.evaluate(`(${extractVisibleText.toString()})(${js(exclusions.map(item => item.selector))}, ${js(root)}, ${js(includes)})`);
  if (!row.text_entries.length) throw Error('No visible UI text captured');
  const text = row.text_entries.map(item => item.value).join('\n');
  if (/Page not found|Server Error|Traceback|找不到页面|服务器错误/.test(text)) throw Error('Error page is not acceptance evidence');
  const verdict = judge(row.text_entries, {allow, chars: tradChars, dataPatterns: spec.data_patterns || [], defaultData: spec.default_data || {}});
  row.english = verdict.english;
  row.traditional = verdict.traditional;
  row.traditional_samples = verdict.traditional_samples;
  row.title_issues = verdict.title_issues;
  const seen = new Set();
  row.default_data = verdict.default_data.filter(hit => !seen.has(hit.word) && seen.add(hit.word))
    .map(({word, doctype, name, reason}) => ({word, doctype, name, reason}));
  row.sidebar_ok = !screen.sidebar || row.sidebar_title === screen.sidebar;
  row.pass = !row.english.length && !row.traditional.length && !row.title_issues.length && row.sidebar_ok;
  row.screenshot = `${outDir}/${screen.id}.png`;
  await c.screenshot(row.screenshot);
}

// 确认框屏（A22）：点「提交」或「取消」→ 等 .modal.show → 截图 → 点「否」→ REST 查 docstatus 不变
async function runDialog(c, screen, row) {
  const d = screen.dialog;
  const before = await getDoc(c, d.doctype, d.name);
  if (before.status !== 200) throw Error(`${d.doctype}/${d.name} not found (HTTP ${before.status})`);
  row.docstatus_before = before.body.data.docstatus;
  const want = d.action === 'submit' ? 0 : 1;
  if (row.docstatus_before !== want) throw Error(`${d.action} dialog needs docstatus ${want}, got ${row.docstatus_before}`);
  await c.until(`window.cur_frm?.doctype === ${js(d.doctype)} && cur_frm.doc.name === ${js(d.name)} && !cur_frm.is_dirty() && ${FORM_IDLE}`, 60000);
  await c.pause(600);
  // 提交：primary-action（toolbar.js:829-845 → form.js:898-903 savesubmit → frappe.confirm）
  // 取消：.btn-secondary（toolbar.js:806-810 → form.js:943-967 savecancel；有已提交下游时走 _cancel_all 对话框，form.js:971-1040）
  if (d.action === 'submit') await click(c, '.page-actions .primary-action', d.button || '提交');
  else await click(c, '.page-actions .btn-secondary', d.button || '取消');
  await c.until(`!!document.querySelector('.modal.show') && !frappe.dom.freeze_count`, 30000);
  await c.pause(500);
  row.dialog_kind = await c.evaluate(`(() => { const m = [...document.querySelectorAll('.modal.show')].pop(); const no = m.querySelector('.btn-modal-secondary'); return m.querySelector('.frappe-confirm-message') && no && !no.classList.contains('hide') ? 'confirm' : 'other'; })()`);
  await capture(c, screen, row);
  // 关框：frappe.confirm 的「否」是 .btn-modal-secondary（messages.js:43-44；dom.js:363）；其余对话框点右上叉 .btn-modal-close（dom.js:352）
  if (row.dialog_kind === 'confirm') await click(c, '.modal.show .modal-footer .btn-modal-secondary', d.no_label || '否');
  else await click(c, '.modal.show .btn-modal-close');
  await c.until(`!document.querySelector('.modal.show')`, 15000);
  await c.pause(1500);
  const after = await getDoc(c, d.doctype, d.name);
  row.docstatus_after = after.status === 200 ? after.body.data.docstatus : null;
  row.docstatus_ok = row.docstatus_after === row.docstatus_before;
  // kind_expected（R9 TS-036，HT-026）：confirm＝普通确认框，cancel_all＝「取消所有单据」对话框（判为 other）；不写则不查
  if (screen.kind_expected) {
    row.kind_expected = screen.kind_expected;
    row.kind_ok = row.dialog_kind === ({confirm: 'confirm', cancel_all: 'other'}[screen.kind_expected]);
    if (!row.kind_ok) row.pass = false;
  }
}

(async () => {
  const c = await open(base), result = [];
  let fatal = false;
  try {
    const missing = await checkDefaultData(c);
    if (missing.length) {
      console.error('default_data records do not exist (not a free-form whitelist):\n  ' + missing.join('\n  '));
      fatal = true;
      return;
    }
    const values = {};
    const unresolved = await resolveVariables(c, values);
    console.log(JSON.stringify({variables: Object.keys(values).length, unresolved_at_start: Object.keys(unresolved)}));
    for (const raw of spec.screens) {
      if (only && !only.has(raw.id)) continue;
      if (phase && raw.phase !== phase) continue;
      // skip：确认无法成屏的（理由写在 screens.json），pass 记 null、不计入退出码，回执须逐条列出
      if (raw.skip) { result.push({id: raw.id, stage: raw.stage, state: raw.state, pass: null, skipped: raw.skip, english: [], traditional: [], title_issues: [], default_data: [], sidebar_title: null, screenshot: null}); continue; }
      const row = {id: raw.id, stage: raw.stage, state: raw.state, pass: false, english: [], traditional: [], title_issues: [], default_data: [], sidebar_title: null, screenshot: null};
      try {
        const needed = [...new Set((JSON.stringify(raw).match(/\{\{(\w+)\}\}/g) || []).map(m => m.slice(2, -2)))];
        if (needed.some(key => !(key in values))) Object.assign(unresolved, (await resolveVariables(c, values, needed)));
        for (const key of needed) if (key in values) delete unresolved[key];
        const screen = substitute(raw, values);
        await openScreen(c, screen);
        if (screen.wait_for) { await c.until(screen.wait_for, screen.timeout || 30000); await c.pause(600); }
        for (const step of screen.steps || []) await runStep(c, step);
        if (screen.dialog) await runDialog(c, screen, row);
        else {
          if (screen.ready) await c.until(screen.ready, screen.timeout || 30000);
          await c.pause(screen.pause || 800);
          await capture(c, screen, row);
        }
        for (const step of screen.after || []) await runStep(c, step);
      } catch (error) {
        row.pass = false;
        row.error = String(error);
        row.screenshot = `${outDir}/${raw.id}-error.png`;
        try { await c.screenshot(row.screenshot); } catch {}
        try { await c.evaluate(`document.querySelectorAll('.modal.show .btn-modal-close').forEach(b => b.click()); true`); } catch {}
      }
      // HIT_ENTRIES=1：留下含命中词的原始条目，供逐屏定性（TS-023）
      if (process.env.HIT_ENTRIES && row.text_entries && !row.pass) {
        const words = [...row.english, ...row.traditional];
        row.hit_entries = row.text_entries.filter(e => words.some(w => (e.value || '').includes(w)) || row.title_issues.some(t => t.value === e.value));
      }
      delete row.text_entries;
      result.push(row);
      fs.writeFileSync(`${outDir}/result.json`, JSON.stringify(result, null, 2));
      fs.writeFileSync(`${outDir}/variables.json`, JSON.stringify({values, unresolved}, null, 2));
      console.log(JSON.stringify({id: row.id, state: row.state, pass: row.pass, english: row.english, traditional: row.traditional, title_issues: row.title_issues.length, default_data: row.default_data.map(d => d.word), sidebar_title: row.sidebar_title, docstatus_ok: row.docstatus_ok, dialog_kind: row.dialog_kind, kind_ok: row.kind_ok, error: row.error}));
    }
  } finally { c.close(); }
  if (fatal || result.some(row => (!row.skipped && !row.pass) || row.docstatus_ok === false)) process.exitCode = 1;
})().catch(error => { console.error(error); process.exitCode = 1; });
