// 只读探针：ListView.get_header_html 补丁用 String.prototype.replace(字符串, 字符串)，
// 第二参里的 $& / $` / $' 会被当替换模式解释。构造一个译名含 "$&" 的 label 看结果。
const html = '<span data-sort-by="x"\n\t\ttitle="点击按Cost $& Center排序">X</span>';
const wrong = 'title="点击按Cost $& Center排序"';
const right = 'title="点击按成本$&中心排序"';
const out = html.replace(wrong, right);
console.log(JSON.stringify({out, literal: out.includes(right)}));
