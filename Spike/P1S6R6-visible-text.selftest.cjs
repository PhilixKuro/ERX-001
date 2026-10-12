// P1S6R6-visible-text.cjs 的离线自测（无 jsdom：纯函数用例 + 手搓假 DOM 跑 extractVisibleText）
// 用法：node Spike/P1S6R6-visible-text.selftest.cjs
const assert = require('node:assert/strict');
const fs = require('node:fs');
const path = require('node:path');
const vt = require('./P1S6R6-visible-text.cjs');

const chars = JSON.parse(fs.readFileSync(path.join(__dirname, 'P1S6R6-trad-chars.json'), 'utf8')).chars;
const allow = new Set(['BOM', 'CNY', 'Frappe China']);
let passed = 0;
function test(name, fn) { fn(); passed++; console.log('ok', name); }

// ---------- 纯函数 ----------
test('字表非空且不含简体常用字', () => {
  assert.ok(chars.length > 100);
  for (const ch of '会计数据单价必是整') assert.ok(!chars.includes(ch), ch);
  for (const ch of '會計數據單價') assert.ok(chars.includes(ch), ch);
});

test('findTraditional 命中繁体、放过简体', () => {
  const entries = [{kind: 'text', value: '必须是整数'}, {kind: 'text', value: '必須是整數'}, {kind: 'placeholder', value: '會計'}];
  assert.deepEqual(vt.findTraditional(entries, chars), ['數', '會', '計', '須'].sort());
  assert.deepEqual(vt.findTraditional([{kind: 'text', value: '会计凭证'}], chars), []);
});

test('findTraditional 空字表报错（防止静默放行）', () => {
  assert.throws(() => vt.findTraditional([{kind: 'text', value: '會'}], ''));
});

test('findEnglish 对 text／placeholder／title 都跑，allow 生效', () => {
  const entries = [
    {kind: 'text', value: '物料 BOM 成本'},
    {kind: 'placeholder', value: 'Search or type a command'},
    {kind: 'title', value: 'Add Row'},
    {kind: 'text', value: '币种 CNY'},
    {kind: 'text', value: 'Frappe China 版本'},
  ];
  assert.deepEqual(vt.findEnglish(entries, allow), ['Add', 'Row', 'Search', 'command', 'or', 'type']);
  assert.deepEqual(vt.findEnglish(entries, allow, ['text']), []);
});

test('findEnglish 不把邮箱当英文词', () => {
  assert.deepEqual(vt.findEnglish([{kind: 'text', value: '联系 admin@example.com'}], allow), []);
});

test('prepareEntries：default_data 命中进单列、不进英文；长词优先', () => {
  const dd = {
    'Standard Selling': {doctype: 'Price List', name: 'Standard Selling', reason: '安装 fixture'},
    'Nos': {doctype: 'UOM', name: 'Nos', reason: '安装 fixture'},
  };
  const entries = [{kind: 'text', value: '价目表 Standard Selling'}, {kind: 'text', value: '单位 Nos'}, {kind: 'text', value: 'Standard'}];
  const r = vt.judge(entries, {allow, chars, dataPatterns: [], defaultData: dd});
  assert.deepEqual(r.english, ['Standard']); // 单独的 Standard 不在默认数据里，照报
  assert.deepEqual(r.default_data.map(h => h.word).sort(), ['Nos', 'Standard Selling']);
  // Nos 不能吃掉 Nosy 之类的词
  const r2 = vt.judge([{kind: 'text', value: 'Nosy'}], {allow, chars, dataPatterns: [], defaultData: dd});
  assert.deepEqual(r2.english, ['Nosy']);
  assert.deepEqual(r2.default_data, []);
});

test('prepareEntries：allow 短语先于 default_data 剥', () => {
  const dd = {China: {doctype: 'Territory', name: 'China', reason: '安装 fixture'}};
  const r = vt.judge([{kind: 'text', value: 'Frappe China 版本'}, {kind: 'text', value: '地区 China'}], {allow, chars, dataPatterns: [], defaultData: dd});
  assert.deepEqual(r.english, []);
  assert.equal(r.default_data.length, 1);
  assert.equal(r.default_data[0].value, '地区 China');
});

test('prepareEntries：data_patterns 剥用户数据', () => {
  const r = vt.judge([{kind: 'text', value: '物料 _S6R6WIRE-01 已保存'}, {kind: 'text', value: 'SAL-ORD-2026-00001'}],
    {allow, chars, dataPatterns: [{pattern: '_S6R6[^\\s，。]*', reason: '造数'}, {pattern: '\\b[A-Z]{2,}(?:-[A-Z]+)*-\\.?\\d{4}-\\d{5}\\b', reason: '单号'}], defaultData: {}});
  assert.deepEqual(r.english, []);
});

test('judge：title 单列 title_issues，不重复进 english／traditional', () => {
  const entries = [{kind: 'text', value: '保存'}, {kind: 'title', value: 'Edit Filters'}, {kind: 'title', value: '刪除'}, {kind: 'title', value: '删除'}];
  const r = vt.judge(entries, {allow, chars, dataPatterns: [], defaultData: {}});
  assert.deepEqual(r.english, []);
  assert.deepEqual(r.traditional, []);
  assert.equal(r.title_issues.length, 2);
  assert.deepEqual(r.title_issues[0], {value: 'Edit Filters', english: ['Edit', 'Filters'], traditional: []});
  assert.deepEqual(r.title_issues[1].traditional, ['刪']);
});

// ---------- 手搓假 DOM 跑 extractVisibleText ----------
function makeDom(spec) {
  // spec: {tag, attrs, style, text, children, rect}
  const all = [];
  function build(s, parent) {
    const el = {
      tagName: s.tag.toUpperCase(), parentElement: parent, attrs: s.attrs || {}, style: s.style || {},
      rect: s.rect || {width: 10, height: 10}, children: [], textNodes: [], selectedOptions: s.selectedOptions || [],
      getAttribute(name) { return name in this.attrs ? this.attrs[name] : null; },
      getBoundingClientRect() { return this.rect; },
      matches(sel) { return matches(this, sel); },
      closest(sel) { for (let e = this; e; e = e.parentElement) if (matches(e, sel)) return e; return null; },
      querySelectorAll(sel) { return descendants(this).filter(e => matches(e, sel)); },
    };
    all.push(el);
    if (s.text) el.textNodes.push({nodeValue: s.text, parentElement: el});
    for (const c of s.children || []) el.children.push(build(c, el));
    return el;
  }
  function descendants(el) { return el.children.flatMap(c => [c, ...descendants(c)]); }
  // 只支持本测试用到的选择器：tag、.class、[attr]、[attr="v"]，逗号分隔、复合
  function matches(el, selector) {
    return selector.split(',').map(s => s.trim()).some(simple => {
      if (simple.includes(' ')) { // 后代选择器：只支持两段
        const [a, b] = simple.split(/\s+/);
        if (!matches(el, b)) return false;
        for (let p = el.parentElement; p; p = p.parentElement) if (matches(p, a)) return true;
        return false;
      }
      const notMatch = simple.match(/:not\((.*)\)$/);
      if (notMatch) { if (matches(el, notMatch[1])) return false; simple = simple.slice(0, notMatch.index); }
      const re = /([a-zA-Z][\w-]*)|\.([\w-]+)|\[([\w-]+)(?:="([^"]*)")?\]/g;
      let m, ok = true, consumed = 0;
      while ((m = re.exec(simple))) {
        consumed += m[0].length;
        if (m[1]) ok = ok && el.tagName === m[1].toUpperCase();
        else if (m[2]) ok = ok && (el.attrs.class || '').split(/\s+/).includes(m[2]);
        else if (m[3]) ok = ok && (m[4] === undefined ? m[3] in el.attrs : el.attrs[m[3]] === m[4]);
      }
      return ok && consumed === simple.length && simple.length > 0;
    });
  }
  const body = build(spec, null);
  const textNodes = all.flatMap(e => e.textNodes);
  return {
    body,
    document: {
      body,
      querySelectorAll: sel => [body, ...descendants(body)].filter(e => matches(e, sel)),
      createTreeWalker(root) {
        const nodes = [root, ...descendants(root)].flatMap(e => e.textNodes);
        let i = 0;
        return {nextNode: () => nodes[i++] || null};
      },
    },
    getComputedStyle: el => ({display: el.style.display || 'block', visibility: el.style.visibility || 'visible', opacity: el.style.opacity ?? '1'}),
    NodeFilter: {SHOW_TEXT: 4},
    textNodes,
  };
}

function runExtract(dom, ...args) {
  // 与注入页面同样：toString 后在给定全局下执行
  const fn = new Function('document', 'getComputedStyle', 'NodeFilter', `return (${vt.extractVisibleText.toString()})(...arguments[3]);`);
  return fn(dom.document, dom.getComputedStyle, dom.NodeFilter, args);
}

const page = {
  tag: 'body', children: [
    {tag: 'button', attrs: {class: 'btn', title: 'Save', 'aria-label': 'Save document'}, text: '保存'},
    {tag: 'span', attrs: {'aria-label': 'Hidden Label'}, text: '提示'},
    {tag: 'input', attrs: {placeholder: 'Search'}},
    {tag: 'div', style: {display: 'none'}, children: [{tag: 'span', text: 'Hidden English'}]},
    {tag: 'a', attrs: {'data-doctype': 'Item'}, text: 'ITEM-001'},
    {tag: 'div', attrs: {class: 'sidebar-user-button'}, text: 'Administrator'},
    {tag: 'span', attrs: {'data-original-title': 'Tooltip Text'}, text: '图标'},
    {tag: 'span', rect: {width: 0, height: 0}, text: 'Zero Size'},
    {tag: 'div', attrs: {class: 'modal show'}, children: [{tag: 'p', attrs: {class: 'frappe-confirm-message'}, text: '确认提交？'}, {tag: 'button', text: '否'}]},
  ],
};

test('extractVisibleText：不收 aria-label，收 title／placeholder／data-original-title', () => {
  const dom = makeDom(page);
  const entries = runExtract(dom, ['.sidebar-user-button']);
  const values = entries.map(e => `${e.kind}:${e.value}`);
  assert.ok(values.includes('text:保存'));
  assert.ok(values.includes('title:Save'));
  assert.ok(values.includes('placeholder:Search'));
  assert.ok(values.includes('title:Tooltip Text'));
  assert.ok(!values.some(v => v.includes('Save document') || v.includes('Hidden Label')), 'aria-label 不应被收');
  assert.ok(!values.some(v => v.includes('Hidden English')), '隐藏元素不应被收');
  assert.ok(!values.some(v => v.includes('ITEM-001')), '记录链接是数据');
  assert.ok(!values.some(v => v.includes('Administrator')), 'data_selectors 生效');
  assert.ok(!values.some(v => v.includes('Zero Size')), '零尺寸元素不收');
});

test('extractVisibleText：rootSelector 只取对话框', () => {
  const dom = makeDom(page);
  const entries = runExtract(dom, [], '.modal.show');
  assert.deepEqual(entries.map(e => e.value), ['确认提交？', '否']);
  assert.throws(() => runExtract(dom, [], '.no-such-root'));
});

console.log(`${passed} tests passed`);
