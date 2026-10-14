// 只读探针：在 happy-dom 里加载 independent_app_labels.js（CRM 配置），量首轮处理耗时并核翻页改写结果。
// 用法：node perf_probe.cjs <happy-dom 包目录> <脚本路径> <行数>
const path = require('path');
const fs = require('fs');
const {Window} = require(path.resolve(process.argv[2]));
const src = fs.readFileSync(process.argv[3], 'utf8');
const rows = Number(process.argv[4] || 100);
const w = new Window({url: 'http://localhost/crm'});
const d = w.document;
const row = (i) => `<div class="row"><div class="c"><div><div><span>Lead ${i}</span></div></div></div>` +
	Array.from({length: 10}, (_, j) => `<div class="c"><div><div>v${i}-${j}</div></div></div>`).join('') + '</div>';
d.body.innerHTML = `<div id="app"><div class="list">${Array.from({length: rows}, (_, i) => row(i)).join('')}</div>` +
	`<div class="flex justify-between gap-2"><div class="flex items-center"><button>Load More</button><div class="mx-3"></div>` +
	`<div class="flex items-center gap-1"><div>${rows}</div><div>of</div><div>${rows * 2}</div></div></div></div></div>` +
	`<script id="china-ui-labels" type="application/json">${JSON.stringify({app: 'crm', lang: 'zh', messages: {of: '/', 'Load More': '加载更多', Select: '单选', 'Select {0}...': '选择{0}……'}})}</script>`;
const t0 = performance.now();
w.eval(src);
const t1 = performance.now();
const pager = [...d.querySelectorAll('.gap-1 > div')].map((n) => n.textContent);
const btn = d.querySelector('button').textContent;
console.log(JSON.stringify({rows, divs: d.querySelectorAll('div').length, initial_ms: +(t1 - t0).toFixed(1), pager, btn}));
w.happyDOM.close();
