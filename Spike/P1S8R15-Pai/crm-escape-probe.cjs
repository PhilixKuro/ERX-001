// S8 R15 step 24: try Escape on the stuck CRM dialog: document first, then the focused element.
// Usage: node peek-rehearsal.cjs <user-data-dir>   (attaches over DevTools; clicks nothing)
const fs = require('node:fs'), path = require('node:path');
(async () => {
	const port = fs.readFileSync(path.join(process.argv[2], 'DevToolsActivePort'), 'utf8').split('\n')[0];
	const pages = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).filter(t => t.type === 'page');
	console.log('pages', JSON.stringify(pages.map(p => p.url)));
	const socket = new WebSocket(pages[0].webSocketDebuggerUrl);
	await new Promise((resolve, reject) => { socket.addEventListener('open', resolve); socket.addEventListener('error', reject); });
	let id = 0; const waiting = new Map();
	socket.addEventListener('message', event => { const data = JSON.parse(event.data); waiting.get(data.id)?.(data); waiting.delete(data.id); });
	const send = (method, params = {}) => new Promise(resolve => { const n = ++id; waiting.set(n, resolve); socket.send(JSON.stringify({ id: n, method, params })); });
	const run = async expression => (await send('Runtime.evaluate', { returnByValue: true, awaitPromise: true, expression })).result?.result?.value;
	console.log('active', await run(`document.activeElement?.tagName + ' ' + (document.activeElement?.placeholder || document.activeElement?.className || '').slice(0, 60)`));
	await run(`document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', bubbles: true })); true`);
	await new Promise(r => setTimeout(r, 1500));
	console.log('after document Escape', await run(`!!document.querySelector('[role=dialog]')`));
	await run(`(document.activeElement || document.body).dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape', code: 'Escape', keyCode: 27, bubbles: true })); true`);
	await new Promise(r => setTimeout(r, 1500));
	console.log('after focused Escape', await run(`!!document.querySelector('[role=dialog]')`));
	await send('Input.dispatchKeyEvent', { type: 'keyDown', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 }); await send('Input.dispatchKeyEvent', { type: 'keyUp', key: 'Escape', code: 'Escape', windowsVirtualKeyCode: 27 });
	await new Promise(r => setTimeout(r, 1500));
	console.log('after real Escape', await run(`!!document.querySelector('[role=dialog]')`));
	const shot = await send('Page.captureScreenshot', { format: 'png' });
	if (shot.result?.data) fs.writeFileSync(path.join(__dirname, 'peek-rehearsal.png'), Buffer.from(shot.result.data, 'base64'));
	socket.close();
})().catch(error => { console.error(error); process.exitCode = 1; });
