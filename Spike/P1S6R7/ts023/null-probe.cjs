// 定位逐屏核命中的 <b>null</b>：取其父链与邻近文字、是否可见
const {open} = require('../../P1S6R4-cdp.cjs');
const [base, ...routes] = process.argv.slice(2);
(async () => {
  const s = await open(base);
  try {
    for (const r of routes) {
      await s.navigate(`${base}/${r}`);
      await s.until('window.cur_frm && !frappe.dom.freeze_count', 30000); await s.pause(2500);
      console.log('##', r, await s.evaluate(`JSON.stringify([...document.querySelectorAll('b')].filter(b=>b.textContent.trim()==='null').map(b=>{const p=b.closest('.frappe-control,.form-dashboard-section,.indicator-pill,.dropdown-item,li,.alert')||b.parentElement; const rect=b.getBoundingClientRect(); return {visible: rect.width>0&&rect.height>0, ctl: p.getAttribute('data-fieldname')||p.className.slice(0,60), text: (p.innerText||p.textContent).replace(/\s+/g,' ').slice(0,200), html: b.parentElement.outerHTML.slice(0,300)}}))`));
    }
  } finally { s.close(); }
})();
