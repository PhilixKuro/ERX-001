/*
 * V-16 follow-up 2: find the real producer of the /desk/undefined request, and
 * separate "pre-existing LG-074 symptom" from "artifact my test app created".
 *
 *   node D:\ERX-001\Spike\V16-cdp-trace-undefined.js
 *
 * Why this file exists: the probe patched get_icon_for_menu_item, the patch WAS
 * called (17x), yet /desk/undefined appeared in the patched run AND in the
 * unpatched baseline run in equal number. So that method is not the producer.
 * Rather than reason about it, ask the browser: enable async stack traces and
 * print the initiator of any request whose URL contains "undefined".
 *
 * It also dumps every app_data entry with its app_logo_url. My throwaway
 * erx_spike app necessarily appears in the app switcher, so its entry has to be
 * shown separately -- otherwise a 404 it causes could be misread as LG-074.
 */

const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

const CHROME =
	[
		"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
		"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
	].find((p) => fs.existsSync(p)) || null;

const SITE_HOST = "erx.localhost";
const BASE = `http://${SITE_HOST}:8000`;
const PORT = 9250;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class CDP {
	constructor(wsUrl) {
		this.ws = new WebSocket(wsUrl);
		this.id = 0;
		this.pending = new Map();
		this.listeners = [];
		this.ready = new Promise((res, rej) => {
			this.ws.addEventListener("open", res);
			this.ws.addEventListener("error", rej);
		});
		this.ws.addEventListener("message", (ev) => {
			const m = JSON.parse(ev.data);
			if (m.id && this.pending.has(m.id)) {
				const { resolve, reject } = this.pending.get(m.id);
				this.pending.delete(m.id);
				m.error ? reject(new Error(JSON.stringify(m.error))) : resolve(m.result);
			} else if (m.method) this.listeners.forEach((f) => f(m));
		});
	}
	on(f) {
		this.listeners.push(f);
	}
	send(method, params = {}, sessionId) {
		const id = ++this.id;
		const p = { id, method, params };
		if (sessionId) p.sessionId = sessionId;
		this.ws.send(JSON.stringify(p));
		return new Promise((res, rej) => this.pending.set(id, { resolve: res, reject: rej }));
	}
	close() {
		try {
			this.ws.close();
		} catch (e) {}
	}
}

async function httpJson(url, tries = 60) {
	for (let i = 0; i < tries; i++) {
		try {
			const r = await fetch(url);
			if (r.ok) return await r.json();
		} catch (e) {}
		await sleep(250);
	}
	throw new Error("devtools endpoint down");
}

(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), "erx-v16t-"));
	const chrome = spawn(
		CHROME,
		[
			`--remote-debugging-port=${PORT}`,
			`--user-data-dir=${profile}`,
			"--headless=new",
			"--no-first-run",
			"--no-default-browser-check",
			"--disable-gpu",
			`--host-resolver-rules=MAP ${SITE_HOST} 127.0.0.1`,
			"about:blank",
		],
		{ stdio: "ignore" }
	);
	const hits = [];
	let cdp;
	try {
		const v = await httpJson(`http://127.0.0.1:${PORT}/json/version`);
		cdp = new CDP(v.webSocketDebuggerUrl);
		await cdp.ready;
		const { targetId } = await cdp.send("Target.createTarget", { url: "about:blank" });
		const { sessionId: S } = await cdp.send("Target.attachToTarget", { targetId, flatten: true });
		await cdp.send("Page.enable", {}, S);
		await cdp.send("Runtime.enable", {}, S);
		await cdp.send("Network.enable", {}, S);
		/* async stack traces so the initiator points at real app code */
		await cdp.send("Debugger.enable", {}, S).catch(() => {});
		await cdp.send("Debugger.setAsyncCallStackDepth", { maxDepth: 32 }, S).catch(() => {});

		cdp.on((m) => {
			if (m.sessionId !== S) return;
			if (m.method === "Network.requestWillBeSent" && /undefined/.test(m.params.request.url)) {
				const init = m.params.initiator || {};
				hits.push({
					url: m.params.request.url,
					type: m.params.type,
					initiator_type: init.type,
					initiator_url: init.url,
					stack: (init.stack?.callFrames || []).slice(0, 8).map(
						(f) => `${f.functionName || "(anon)"} @ ${f.url}:${f.lineNumber + 1}`
					),
				});
			}
		});

		const login = await fetch("http://127.0.0.1:8000/api/method/login", {
			method: "POST",
			headers: { "Content-Type": "application/json", host: SITE_HOST },
			body: JSON.stringify({ usr: "Administrator", pwd: "admin" }),
		});
		const sid = (login.headers.getSetCookie?.() || [])
			.map((c) => c.split(";")[0])
			.find((c) => c.startsWith("sid="));
		if (sid) {
			const [name, value] = sid.split("=");
			await cdp.send("Network.setCookie", { name, value, domain: SITE_HOST, path: "/" }, S);
		}

		await cdp.send("Page.navigate", { url: `${BASE}/desk/` }, S);
		for (let i = 0; i < 40; i++) {
			await sleep(500);
			const r = await cdp.send(
				"Runtime.evaluate",
				{ expression: "!!(window.frappe && frappe.app)", returnByValue: true },
				S
			);
			if (r.result.value && i > 4) break;
		}
		/* open the app switcher: that builds the per-app <img src=icon_url> */
		await cdp.send(
			"Runtime.evaluate",
			{
				expression: `(function(){ try { frappe.app.sidebar.sidebar_header.toggle_dropdown_menu(); return 'ok'; } catch(e){ return 'err:'+e; } })()`,
				returnByValue: true,
			},
			S
		);
		await sleep(3000);

		const dump = await cdp.send(
			"Runtime.evaluate",
			{
				expression: `JSON.stringify({
					app_data: (frappe.boot.app_data||[]).map(function(a){
						return {app_name:a.app_name, app_title:a.app_title, app_logo_url:a.app_logo_url, app_route:a.app_route};
					}),
					dropdown: Array.from(document.querySelectorAll('.dropdown-menu-item')).map(function(d){
						var img = d.querySelector('img');
						return {
							name: d.getAttribute('data-name'),
							route: d.getAttribute('data-app-route'),
							img_src: img ? img.getAttribute('src') : null
						};
					}),
					imgs_bad: Array.from(document.querySelectorAll('img')).map(function(i){ return i.getAttribute('src'); })
						.filter(function(s){ return s==='undefined' || s===null || /undefined/.test(s||''); })
				})`,
				returnByValue: true,
			},
			S
		);
		console.log("=== app_data / dropdown / bad imgs ===");
		console.log(JSON.stringify(JSON.parse(dump.result.value), null, 2));
	} catch (e) {
		console.log("ERR", String(e));
	} finally {
		if (cdp) cdp.close();
		try {
			chrome.kill();
		} catch (e) {}
	}
	console.log("\n=== requests containing 'undefined' (" + hits.length + ") ===");
	console.log(JSON.stringify(hits, null, 2));
})();
