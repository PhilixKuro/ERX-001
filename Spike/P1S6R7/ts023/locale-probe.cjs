// 验 CN¥／Nov 是否来自无头浏览器的英文区域：同一页面在 en-US 与 zh-CN 下各取一次
const {open} = require('../../P1S6R4-cdp.cjs');
(async () => {
  const s = await open('http://localhost:8000');
  try {
    for (const locale of [null, 'zh-CN']) {
      if (locale) await s.send('Emulation.setLocaleOverride', {locale});
      for (const url of ['/crm/deals/view/list', '/crm/dashboard']) {
        await s.navigate('http://localhost:8000' + url); await s.pause(6000);
        const t = await s.evaluate(`JSON.stringify({lang: navigator.language, intl: Intl.NumberFormat().resolvedOptions().locale, cny: (document.body.innerText.match(/[A-Z]*¥\s?[\d.,]+/g)||[]).slice(0,3), nov: [...document.querySelectorAll('svg text')].map(e=>e.textContent).filter(x=>/Nov|11月|十一月/.test(x)).slice(0,3)})`);
        console.log(locale || 'default', url, t);
      }
    }
  } finally { s.close(); }
})();
