function extractVisibleText(dataSelectors = []) {
  function visible(element) {
    if (!element || element.closest('[hidden],[inert],[aria-hidden="true"],.sr-only')) return false;
    for (let parent = element; parent; parent = parent.parentElement) {
      const style = getComputedStyle(parent);
      if (style.display === 'none' || style.visibility === 'hidden' || Number(style.opacity) === 0) return false;
    }
    const rect = element.getBoundingClientRect();
    return rect.width > 0 && rect.height > 0;
  }
  const ignored = 'script,style,noscript,input,textarea,.like-disabled-input,a[data-doctype],.list-row .list-subject,.list-row .list-row-col:not(.list-actions),.grid-static-col,.awesomplete ul,.datepicker,.flatpickr-calendar';
  const entries = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  let node;
  while ((node = walker.nextNode())) {
    const parent = node.parentElement;
    if (!visible(parent) || parent.closest(ignored) || dataSelectors.some(selector => parent.closest(selector))) continue;
    const value = node.nodeValue.trim();
    if (value) entries.push({kind: 'text', value, tag: parent.tagName});
  }
  for (const element of document.querySelectorAll('[placeholder],[title],[aria-label]')) {
    // Input values are data; their placeholders and tooltips are interface text.
    const attributeIgnored = 'script,style,noscript,.like-disabled-input,a[data-doctype],.list-row .list-subject,.list-row .list-row-col:not(.list-actions),.grid-static-col,.awesomplete ul,.datepicker,.flatpickr-calendar';
    if (!visible(element) || element.closest(attributeIgnored) || dataSelectors.some(selector => element.closest(selector))) continue;
    for (const key of ['placeholder', 'title', 'aria-label']) {
      const value = element.getAttribute(key)?.trim();
      if (value) entries.push({kind: key, value, tag: element.tagName});
    }
  }
  for (const select of document.querySelectorAll('select')) {
    if (visible(select) && !dataSelectors.some(selector => select.closest(selector))) {
      for (const option of select.selectedOptions) {
        if (option.textContent.trim()) entries.push({kind: 'selected-option', value: option.textContent.trim(), tag: 'SELECT'});
      }
    }
  }
  return entries;
}
function findEnglish(entries, allow) {
  const words = new Set();
  for (const {value} of entries) {
    let uiValue=value.replace(/[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}/gi, '');
    for(const phrase of allow) if(/[ /]/.test(phrase)) uiValue=uiValue.replaceAll(phrase,'');
    for (const match of uiValue.match(/[A-Za-z][A-Za-z0-9-]{1,}/g) || []) {
      if (!allow.has(match)) words.add(match);
    }
  }
  return [...words].sort();
}
module.exports = {extractVisibleText, findEnglish};
