// 逐屏核 v2 的取词与判词（TS-022 第 1 步；A21／DEC-033）。
// 基于 Spike/P1S6R4-visible-text.cjs（旧文件不改，供 R4 证据复现）。与旧版的差别：
//   1. extractVisibleText 不再收 aria-label（屏上不可见，DEC-033 不计）；
//      另收 data-original-title（Bootstrap tooltip 初始化后把 title 挪到这里，悬停仍可见）；
//      可传 rootSelector 只取某个容器（确认框屏只取最上层对话框）。
//   2. findTraditional(entries, chars)：浏览器端无 gb2312 编码器，用 P1S6R6-trad-chars.json 的字表比对。
//   3. findEnglish(entries, allow, kinds)：对 text、placeholder、title、selected-option 都跑。
//   4. prepareEntries：先剥掉用户数据（data_patterns）与 ERPNext 自带英文默认数据（default_data），
//      命中的默认数据单独返回，不进英文词。

// ---- 页面内执行（toString 后注入），不得引用外部变量 ----
// includeSelectors：落在 ignored 区域里、但属于界面文案的元素（如列表行里的状态徽标 .indicator-pill）
function extractVisibleText(dataSelectors = [], rootSelector = null, includeSelectors = []) {
  function visible(element) {
    if (!element || element.closest('[hidden],[inert],[aria-hidden="true"],.sr-only')) return false;
    for (let parent = element; parent; parent = parent.parentElement) {
      const style = getComputedStyle(parent);
      if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) return false;
    }
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }
  let root = document.body;
  if (rootSelector) {
    const candidates = [...document.querySelectorAll(rootSelector)].filter(visible);
    if (!candidates.length) throw Error('Extraction root not visible: ' + rootSelector);
    root = candidates[candidates.length - 1]; // 最上层的那个（后打开的在 DOM 后面）
  }
  const ignored = 'script,style,noscript,input,textarea,.like-disabled-input,a[data-doctype],.list-row .list-subject,.list-row .list-row-col:not(.list-actions),.grid-static-col,.awesomplete ul,.datepicker,.flatpickr-calendar';
  const attributeIgnored = 'script,style,noscript,.like-disabled-input,a[data-doctype],.list-row .list-subject,.list-row .list-row-col:not(.list-actions),.grid-static-col,.awesomplete ul,.datepicker,.flatpickr-calendar';
  const excluded = element => dataSelectors.some(selector => element.closest(selector));
  const included = element => includeSelectors.some(selector => element.closest(selector));
  const entries = [];
  const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    const parent = node.parentElement;
    if (!visible(parent) || (parent.closest(ignored) && !included(parent)) || excluded(parent)) continue;
    const value = node.nodeValue.trim();
    if (value) entries.push({kind: 'text', value, tag: parent.tagName});
  }
  // Input values are data; their placeholders and tooltips are interface text. aria-label 不收（DEC-033）。
  const attributes = [['placeholder', 'placeholder'], ['title', 'title'], ['data-original-title', 'title']];
  for (const element of root.querySelectorAll('[placeholder],[title],[data-original-title]')) {
    if (!visible(element) || (element.closest(attributeIgnored) && !included(element)) || excluded(element)) continue;
    const seen = new Set();
    for (const [attribute, kind] of attributes) {
      const value = element.getAttribute(attribute)?.trim();
      if (value && !seen.has(kind + '\u0000' + value)) {
        seen.add(kind + '\u0000' + value);
        entries.push({kind, value, tag: element.tagName});
      }
    }
  }
  for (const select of root.querySelectorAll('select')) {
    if (visible(select) && !excluded(select)) {
      for (const option of select.selectedOptions) {
        if (option.textContent.trim()) entries.push({kind: 'selected-option', value: option.textContent.trim(), tag: 'SELECT'});
      }
    }
  }
  return entries;
}

// ---- Node 端（纯函数） ----
const ALL_KINDS = ['text', 'placeholder', 'title', 'selected-option'];
const escapeRegExp = text => text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');

// 剥掉用户数据与默认数据。dataPatterns: [{pattern, reason}]（正则源串）；defaultData: {词: {doctype, name, reason}}
// 返回 {entries: 剥过的副本, defaultHits: [{word, doctype, name, reason, kind, value}]}
function prepareEntries(entries, {dataPatterns = [], defaultData = {}, allow = []} = {}) {
  const regexes = dataPatterns.map(item => new RegExp(item.pattern, 'g'));
  // 含空格或斜杠的 allow 短语（如 "Frappe China"）先剥，免得其中的词被当成默认数据
  const allowPhrases = [...(allow instanceof Set ? allow : new Set(allow || []))].filter(phrase => /[ /]/.test(phrase));
  // 长词先剥，免得 "Standard Selling" 被 "Standard" 拆开
  const phrases = Object.keys(defaultData).sort((a, b) => b.length - a.length)
    .map(word => [word, new RegExp(`(^|[^A-Za-z0-9])${escapeRegExp(word)}(?![A-Za-z0-9])`, 'g')]);
  const defaultHits = [];
  const out = entries.map(entry => {
    let value = entry.value;
    for (const regex of regexes) value = value.replace(regex, ' ');
    for (const phrase of allowPhrases) value = value.replaceAll(phrase, ' ');
    for (const [word, regex] of phrases) {
      if (regex.test(value)) {
        defaultHits.push({word, ...defaultData[word], kind: entry.kind, value: entry.value});
        regex.lastIndex = 0;
        value = value.replace(regex, '$1 ');
      }
      regex.lastIndex = 0;
    }
    return {...entry, value};
  });
  return {entries: out, defaultHits};
}

function findEnglish(entries, allow, kinds = ALL_KINDS) {
  const allowSet = allow instanceof Set ? allow : new Set(allow || []);
  const words = new Set();
  for (const {kind, value} of entries) {
    if (!kinds.includes(kind)) continue;
    let uiValue = value.replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '');
    for (const phrase of allowSet) if (/[ /]/.test(phrase)) uiValue = uiValue.replaceAll(phrase, '');
    for (const match of uiValue.match(/[A-Za-z][A-Za-z0-9-]{1,}/g) || []) {
      if (!allowSet.has(match)) words.add(match);
    }
  }
  return [...words].sort();
}

// chars：字表字符串或 Set（P1S6R6-trad-chars.json 的 chars）。返回命中的繁体字（去重、排序）
function findTraditional(entries, chars, kinds = ALL_KINDS) {
  const table = chars instanceof Set ? chars : new Set([...(chars || '')]);
  if (!table.size) throw Error('Traditional character table is empty');
  const found = new Set();
  for (const {kind, value} of entries) {
    if (!kinds.includes(kind)) continue;
    for (const ch of value) if (table.has(ch)) found.add(ch);
  }
  return [...found].sort();
}

// title 属性单列（A21 第三类）：每条带英文词或繁体字的 title 记一项
function findTitleIssues(entries, allow, chars) {
  const issues = [];
  const seen = new Set();
  for (const entry of entries) {
    if (entry.kind !== 'title' || seen.has(entry.value)) continue;
    seen.add(entry.value);
    const english = findEnglish([entry], allow, ['title']);
    const traditional = findTraditional([entry], chars, ['title']);
    if (english.length || traditional.length) issues.push({value: entry.value, english, traditional});
  }
  return issues;
}

// 汇总：英文词、繁体只计非 title 条目；title 条目单列 title_issues
function judge(entries, {allow, chars, dataPatterns, defaultData}) {
  const prepared = prepareEntries(entries, {dataPatterns, defaultData, allow});
  const bodyKinds = ALL_KINDS.filter(kind => kind !== 'title');
  const traditional = findTraditional(prepared.entries, chars, bodyKinds);
  return {
    english: findEnglish(prepared.entries, allow, bodyKinds),
    traditional,
    traditional_samples: traditional.length
      ? [...new Set(entries.filter(e => e.kind !== 'title' && traditional.some(ch => e.value.includes(ch))).map(e => e.value))].slice(0, 10)
      : [],
    title_issues: findTitleIssues(prepared.entries, allow, chars),
    default_data: prepared.defaultHits,
  };
}

module.exports = {extractVisibleText, prepareEntries, findEnglish, findTraditional, findTitleIssues, judge, ALL_KINDS};
