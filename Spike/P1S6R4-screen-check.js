const fs = require('node:fs');
const {open} = require('./P1S6R4-cdp.cjs');
const {extractVisibleText, findEnglish} = require('./P1S6R4-visible-text.cjs');
const [base = 'http://test.localhost:6787', screenFile = 'Spike/P1S6R4-screens.json', outDir = 'Spike/P1S6R4-screens'] = process.argv.slice(2);
const spec = JSON.parse(fs.readFileSync(screenFile, 'utf8'));
if (Array.isArray(spec.allow) || Object.values(spec.allow || {}).some(reason => !reason)) throw Error('Each allow entry must have a reason');
const allow = new Set(Object.keys(spec.allow || {}));
fs.mkdirSync(outDir, {recursive: true});
(async () => {
  const c = await open(base), result = [];
  try {
    for (const screen of spec.screens) {
      const row = {id: screen.id, stage: screen.stage, pass: false, english: []};
      try {
        const path = screen.url ? new URL(screen.url).pathname : '/' + screen.route;
        if (path.startsWith('/desk/')) {
          await c.navigate(base+'/desk');
          await c.until('!!document.querySelector(".desktop-icon") && !!window.frappe?.get_route()?.length');
          if(screen.sidebar==='Business Flow') {
            await c.evaluate(`const icon=[...document.querySelectorAll('.desktop-icon')].find(e=>e.innerText.includes('业务流程'));if(!icon)throw Error('Business Flow icon missing');icon.click();true`);
            await c.until(`frappe.app.sidebar.sidebar_title==='Business Flow' && window.cur_list?.doctype==='Company' && !!document.querySelector('.list-row-container')`);
            await c.pause(500);
          } else if(screen.sidebar) await c.evaluate(`frappe.app.sidebar.setup(${JSON.stringify(screen.sidebar)});true`);
          await c.evaluate(`frappe.set_route(${JSON.stringify(decodeURI(path.slice(6)))});true`);
        } else await c.navigate(new URL(path, base).href);
        const expected = /\/new-/.test(path) ? decodeURI(path).replace(/\/new-.*/, '/new-') : decodeURI(path);
        await c.until(`decodeURI(location.pathname).startsWith(${JSON.stringify(expected)})`);
        if (!screen.wait_for || screen.wait_for === '!!document.body') throw Error('Screen needs a specific readiness condition');
        await c.until(screen.wait_for); await c.pause(600);
        for (const step of screen.steps || []) {
          if (step.evaluate) await c.evaluate(step.evaluate);
          else {
            await c.until(`!!document.querySelector(${JSON.stringify(step.selector)})`);
            await c.evaluate(`document.querySelector(${JSON.stringify(step.selector)}).click();true`);
          }
          if (step.wait_for) await c.until(step.wait_for);
        }
        if (!screen.wait_for || screen.wait_for === '!!document.body') throw Error('Screen needs a specific readiness condition');
        await c.until(screen.wait_for); await c.pause(screen.pause || 800);
        row.url = await c.evaluate('location.href');
        row.sidebar_title = await c.evaluate('window.frappe?.app?.sidebar?.sidebar_title || null');
        const exclusions = [...(spec.data_selectors||[]), ...(screen.data_selectors || [])];
        if (exclusions.some(item => !item.selector || !item.reason)) throw Error('Each data exclusion needs selector and reason');
        row.text_entries = await c.evaluate(`(${extractVisibleText.toString()})(${JSON.stringify(exclusions.map(item => item.selector))})`);
        if (!row.text_entries.length) throw Error('No visible UI text captured');
        row.text = row.text_entries.map(item => item.value).join('\n');
        if (/Page not found|Server Error|Traceback/.test(row.text)) throw Error('Error page is not acceptance evidence');
        row.english = findEnglish(row.text_entries, allow);
        row.sidebar_ok = !screen.sidebar || row.sidebar_title === screen.sidebar;
        row.pass = row.english.length === 0 && row.sidebar_ok;
        row.screenshot = `${outDir}/${screen.id}.png`; await c.screenshot(row.screenshot);
      } catch (error) { row.error = String(error); row.screenshot = `${outDir}/${screen.id}-error.png`; await c.screenshot(row.screenshot); }
      result.push(row); fs.writeFileSync(`${outDir}/result.json`, JSON.stringify(result, null, 2));
        console.log(JSON.stringify({id:row.id,pass:row.pass,english:row.english,error:row.error}));
    }
  } finally {c.close();}
  if (result.some(row => !row.pass)) process.exitCode = 1;
})().catch(error => {console.error(error); process.exitCode = 1;});
