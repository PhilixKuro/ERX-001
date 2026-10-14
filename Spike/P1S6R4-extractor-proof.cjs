const assert = require('node:assert/strict');
const fs = require('node:fs');
const {open} = require('./P1S6R4-cdp.cjs');
const {extractVisibleText, findEnglish} = require('./P1S6R4-visible-text.cjs');
(async () => {
  const c = await open('http://erx.localhost:8000');
  try {
    await c.navigate('about:blank');
    await c.evaluate(`document.body.innerHTML='<div>DirectLabel <b>nested</b></div><input value="UserValue" placeholder="MissingPlaceholder" title="MissingTitle"><div style="opacity:0"><button>HiddenAncestor</button></div><div style="display:none">HiddenDisplay</div><div class="like-disabled-input">RecordData</div><div class="grid-row"><button>ChildTableAction</button><div class="grid-static-col">ChildRecord</div></div><select><option>MissingOption</option></select>';true`);
    const entries = await c.evaluate(`(${extractVisibleText.toString()})()`);
    const words = findEnglish(entries, new Set());
    for (const word of ['DirectLabel', 'nested', 'MissingPlaceholder', 'MissingTitle', 'ChildTableAction']) assert.ok(words.includes(word), word);
    assert.ok(words.includes('MissingOption'));
    for (const word of ['UserValue', 'HiddenAncestor', 'HiddenDisplay', 'RecordData', 'ChildRecord']) assert.ok(!words.includes(word), word);
    assert.deepEqual(findEnglish([{value:'PDF UTF-8 person@example.com'}], new Set(['PDF','UTF-8'])), []);
    fs.writeFileSync('Spike/P1S6R4-extractor-proof.json', JSON.stringify({pass:true, included:words, entries},null,2));
    console.log('Extractor positive/negative assertions passed');
  } finally {c.close();}
})().catch(error => {console.error(error);process.exitCode=1;});
