/*
 * V-16 harness: drive real Chrome headless over CDP and report what the
 * injected own-app script actually did inside the desk page.
 *
 * Runs on the WINDOWS HOST (node 24 has a global WebSocket, so no npm deps):
 *   node D:\ERX-001\Spike\V16-cdp-run.js <label> [--baseline]
 *
 * "Does injection load" and "is the load order before/after desk" can be read
 * off the HTML, but "the override actually takes effect" cannot -- it needs a
 * JS engine. That is what this file is for (play-spike discipline 5: take the
 * observed fact, not the guess).
 *
 * --baseline pre-sets window.__ERX_V16_DISABLE_PATCH via
 * Page.addScriptToEvaluateOnNewDocument (runs before ANY page script), giving
 * an unpatched control run in the same browser and the same session.
 *
 * Collected per run: console lines from the probe, every failed/"undefined"
 * request the page made, and the window.__ERX_V16 record dumped from the page.
 * Written to Spike/V16-out/<label>.json.
 */

const { spawn } = require("child_process");
const fs = require("fs");
const path = require("path");
const os = require("os");

const LABEL = process.argv[2] || "run";
const BASELINE = process.argv.includes("--baseline");

const CHROME =
	[
		"C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
		"C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe",
	].find((p) => fs.existsSync(p)) || null;

const SITE_HOST = "erx.localhost";
const BASE = `http://${SITE_HOST}:8000`;
const OUT_DIR = path.join(__dirname, "V16-out");
const PORT = 9222 + (BASELINE ? 1 : 0);

if (!CHROME) {
	console.error("no chrome/edge found");
	process.exit(2);
}
fs.mkdirSync(OUT_DIR, { recursive: true });

/* ------------------------- tiny CDP client ------------------------- */
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
			const msg = JSON.parse(ev.data);
			if (msg.id && this.pending.has(msg.id)) {
				const { resolve, reject } = this.pending.get(msg.id);
				this.pending.delete(msg.id);
				msg.error ? reject(new Error(JSON.stringify(msg.error))) : resolve(msg.result);
			} else if (msg.method) {
				this.listeners.forEach((fn) => fn(msg));
			}
		});
	}
	on(fn) {
		this.listeners.push(fn);
	}
	send(method, params = {}, sessionId) {
		const id = ++this.id;
		const payload = { id, method, params };
		if (sessionId) payload.sessionId = sessionId;
		this.ws.send(JSON.stringify(payload));
		return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
	}
	close() {
		try {
			this.ws.close();
		} catch (e) {}
	}
}

const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

async function httpJson(url, tries = 60) {
	for (let i = 0; i < tries; i++) {
		try {
			const r = await fetch(url);
			if (r.ok) return await r.json();
		} catch (e) {}
		await sleep(250);
	}
	throw new Error("chrome devtools endpoint never came up: " + url);
}

(async () => {
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), "erx-v16-"));
	const chrome = spawn(
		CHROME,
		[
			`--remote-debugging-port=${PORT}`,
			`--user-data-dir=${profile}`,
			"--headless=new",
			"--no-first-run",
			"--no-default-browser-check",
			"--disable-extensions",
			"--disable-gpu",
			/* erx.localhost has no DNS entry on the host; map it at the browser */
			`--host-resolver-rules=MAP ${SITE_HOST} 127.0.0.1`,
			"--window-size=1400,900",
			"about:blank",
		],
		{ stdio: "ignore" }
	);

	const result = {
		label: LABEL,
		baseline: BASELINE,
		started: new Date().toISOString(),
		chrome: CHROME,
		console: [],
		failed_requests: [],
		undefined_requests: [],
		all_script_requests: [],
		probe: null,
		errors: [],
	};

	let cdp;
	try {
		const version = await httpJson(`http://127.0.0.1:${PORT}/json/version`);
		result.chrome_version = version["Browser"];
		cdp = new CDP(version.webSocketDebuggerUrl);
		await cdp.ready;

		const { targetId } = await cdp.send("Target.createTarget", { url: "about:blank" });
		const { sessionId } = await cdp.send("Target.attachToTarget", { targetId, flatten: true });
		const S = sessionId;

		cdp.on((msg) => {
			if (msg.sessionId !== S) return;
			if (msg.method === "Runtime.consoleAPICalled") {
				const text = (msg.params.args || [])
					.map((a) => (a.value !== undefined ? String(a.value) : a.description || a.type))
					.join(" ");
				if (/\[ERX-V16/.test(text)) result.console.push(text);
			}
			if (msg.method === "Runtime.exceptionThrown") {
				result.errors.push(
					msg.params.exceptionDetails.exception?.description ||
						msg.params.exceptionDetails.text
				);
			}
			if (msg.method === "Network.requestWillBeSent") {
				const u = msg.params.request.url;
				if (/\.js(\?|$)/.test(u)) result.all_script_requests.push(u);
				if (/\/undefined(\?|$)|\/undefined\//.test(u)) result.undefined_requests.push(u);
			}
			if (msg.method === "Network.loadingFailed") {
				result.failed_requests.push({ id: msg.params.requestId, err: msg.params.errorText });
			}
			if (msg.method === "Network.responseReceived") {
				const { url, status } = msg.params.response;
				if (status >= 400) result.failed_requests.push({ url, status });
			}
		});

		await cdp.send("Page.enable", {}, S);
		await cdp.send("Runtime.enable", {}, S);
		await cdp.send("Network.enable", {}, S);

		if (BASELINE) {
			await cdp.send(
				"Page.addScriptToEvaluateOnNewDocument",
				{ source: "window.__ERX_V16_DISABLE_PATCH = true;" },
				S
			);
		}

		/* Log in via the API to get a sid, then navigate the browser to /desk/
		 * so the desk page boots exactly as a user's would.
		 * NOTE (observed): node's fetch cannot resolve "erx.localhost"
		 * (getaddrinfo ENOTFOUND) -- Chrome only reaches it because of the
		 * --host-resolver-rules flag above. So the API call goes to 127.0.0.1
		 * with an explicit Host header, while the browser uses the real name
		 * (needed for the sid cookie domain to match). */
		const login = await fetch(`http://127.0.0.1:8000/api/method/login`, {
			method: "POST",
			headers: { "Content-Type": "application/json", host: SITE_HOST },
			body: JSON.stringify({ usr: "Administrator", pwd: "admin" }),
		});
		const sid = (login.headers.getSetCookie?.() || [])
			.map((c) => c.split(";")[0])
			.find((c) => c.startsWith("sid="));
		result.login_status = login.status;
		result.sid_found = !!sid;
		if (sid) {
			const [name, value] = sid.split("=");
			await cdp.send(
				"Network.setCookie",
				{ name, value, domain: SITE_HOST, path: "/" },
				S
			);
		}

		await cdp.send("Page.navigate", { url: `${BASE}/desk/` }, S);

		/* wait until the sidebar has actually rendered (that is what exercises
		 * the patched methods), or until a hard timeout */
		let settled = null;
		for (let i = 0; i < 60; i++) {
			await sleep(500);
			const r = await cdp.send(
				"Runtime.evaluate",
				{
					expression: `JSON.stringify({
						ready: document.readyState,
						has_probe: !!window.__ERX_V16,
						runs: (window.__ERX_V16 && window.__ERX_V16.runs || []).length,
						app_ready: !!(window.frappe && frappe.app),
						sidebar_items: document.querySelectorAll('.dropdown-menu-item, .sidebar-item-container').length,
						c_calls: (window.__ERX_V16 && window.__ERX_V16.c && window.__ERX_V16.c.calls) || 0
					})`,
					returnByValue: true,
				},
				S
			);
			settled = JSON.parse(r.result.value);
			if (settled.app_ready && (settled.c_calls > 0 || settled.sidebar_items > 0) && i > 4) break;
		}
		result.settle = settled;

		/* open the app switcher dropdown: that is the code path that builds the
		 * <img src="${item.icon_url}"> markup behind the /undefined requests */
		await cdp.send(
			"Runtime.evaluate",
			{
				expression: `(function(){
					try {
						var t = document.querySelector('.app-switcher-dropdown, .sidebar-header, [class*="app-switcher"]');
						if (t) { t.click(); return 'clicked:' + t.className; }
						if (window.frappe && frappe.app && frappe.app.sidebar && frappe.app.sidebar.sidebar_header) {
							frappe.app.sidebar.sidebar_header.toggle_dropdown_menu();
							return 'called toggle_dropdown_menu()';
						}
						return 'no target found';
					} catch (e) { return 'err: ' + e; }
				})()`,
				returnByValue: true,
			},
			S
		);
		result.dropdown_action = true;
		await sleep(2500);

		/* BOUNDARY: desk is an SPA. Drive a client-side route change into a
		 * list view and check the patches still fire (patch d counts
		 * ListView.setup_defaults). This is what CR-008 demo control needs:
		 * an override that survives navigation, not just first paint. */
		await cdp.send(
			"Runtime.evaluate",
			{
				expression: `(function(){ try { frappe.set_route('List','Item'); return 'set_route List/Item'; } catch(e){ return 'err: '+e; } })()`,
				returnByValue: true,
			},
			S
		);
		for (let i = 0; i < 40; i++) {
			await sleep(500);
			const r = await cdp.send(
				"Runtime.evaluate",
				{
					expression: `JSON.stringify({ route: (frappe.get_route()||[]).join('/'), d_calls: (window.__ERX_V16 && window.__ERX_V16.d && window.__ERX_V16.d.calls) || 0 })`,
					returnByValue: true,
				},
				S
			);
			result.after_route = JSON.parse(r.result.value);
			if (result.after_route.d_calls > 0) break;
		}

		/* second hop, to a tree-backed doctype (EN-001 shape) */
		await cdp.send(
			"Runtime.evaluate",
			{
				expression: `(function(){ try { frappe.set_route('List','Account'); return 'ok'; } catch(e){ return 'err: '+e; } })()`,
				returnByValue: true,
			},
			S
		);
		await sleep(3000);
		const r2 = await cdp.send(
			"Runtime.evaluate",
			{
				expression: `JSON.stringify({ route: (frappe.get_route()||[]).join('/'), d_calls: (window.__ERX_V16 && window.__ERX_V16.d && window.__ERX_V16.d.calls) || 0, route_changes: (window.__ERX_V16 && window.__ERX_V16.hooks && window.__ERX_V16.hooks.route_changes) || 0 })`,
				returnByValue: true,
			},
			S
		);
		result.after_route2 = JSON.parse(r2.result.value);

		const dump = await cdp.send(
			"Runtime.evaluate",
			{
				expression: `JSON.stringify({
					probe: window.__ERX_V16 || null,
					dom: {
						img_undefined: Array.from(document.querySelectorAll('img')).filter(function(i){
							return /\\/undefined$/.test(i.getAttribute('src') || '');
						}).length,
						dropdown_items: document.querySelectorAll('.dropdown-menu-item').length,
						sidebar_icons: document.querySelectorAll('.sidebar-item-icon').length
					},
					scripts_in_dom: Array.from(document.querySelectorAll('script[src]')).map(function(s){ return s.getAttribute('src'); })
				})`,
				returnByValue: true,
			},
			S
		);
		const parsed = JSON.parse(dump.result.value);
		result.probe = parsed.probe;
		result.dom = parsed.dom;
		result.scripts_in_dom = parsed.scripts_in_dom;
	} catch (e) {
		result.errors.push("harness: " + String(e));
	} finally {
		if (cdp) cdp.close();
		try {
			chrome.kill();
		} catch (e) {}
	}

	result.finished = new Date().toISOString();
	const out = path.join(OUT_DIR, `${LABEL}.json`);
	fs.writeFileSync(out, JSON.stringify(result, null, 2), "utf8");

	/* terse console summary; the json holds everything */
	const p = result.probe;
	console.log("=== V-16 run:", LABEL, BASELINE ? "(BASELINE, no patch)" : "(patching)", "===");
	console.log("chrome:", result.chrome_version, "| login:", result.login_status, "| sid:", result.sid_found);
	console.log("probe present:", !!p, "| runs:", p && p.runs ? p.runs.length : 0);
	if (p && p.runs) {
		p.runs.forEach((r, i) => {
			console.log(`  run[${i}] src=${r.src}`);
			console.log(`    readyState=${r.readyState} script_tags_in_dom=${r.script_tags_in_dom_at_parse} installed_here=${r.installed_patches_here}`);
			console.log(`    SidebarHeader=${r.at_parse["frappe.ui.SidebarHeader"]} get_icon_for_menu_item=${r.at_parse["frappe.ui.SidebarHeader.prototype.get_icon_for_menu_item"]} frappe.app=${r.at_parse["frappe.app"]} erpnext=${r.at_parse["erpnext"]}`);
		});
	}
	if (p) {
		console.log("  patch a:", JSON.stringify({ installed: p.a && p.a.installed, calls: p.a && p.a.calls, err: p.a && p.a.err }));
		console.log("  patch b:", JSON.stringify({ installed: p.b && p.b.installed, calls: p.b && p.b.calls, err: p.b && p.b.err }));
		console.log("  patch c:", JSON.stringify({ installed: p.c && p.c.installed, calls: p.c && p.c.calls, first_call_dt_ms: p.c && p.c.first_call_dt_ms, err: p.c && p.c.err }));
		if (p.c && p.c.items) console.log("  items seen by add_app_item:", JSON.stringify(p.c.items));
		console.log("  patch d (SPA route boundary):", JSON.stringify({ installed: p.d && p.d.installed, calls: p.d && p.d.calls, last_doctype: p.d && p.d.last_doctype, err: p.d && p.d.err }));
		console.log("  frappe.app at parse:", JSON.stringify(p.e));
		console.log("  wait hooks:", JSON.stringify(p.hooks));
	}
	console.log("after route hop 1:", JSON.stringify(result.after_route));
	console.log("after route hop 2:", JSON.stringify(result.after_route2));
	console.log("dom:", JSON.stringify(result.dom));
	console.log("undefined requests:", result.undefined_requests.length, JSON.stringify(result.undefined_requests.slice(0, 5)));
	console.log("failed requests:", JSON.stringify(result.failed_requests.slice(0, 8)));
	console.log("scripts in dom:", JSON.stringify(result.scripts_in_dom));
	if (result.errors.length) console.log("errors:", JSON.stringify(result.errors.slice(0, 5)));
	console.log("json ->", out);
})();
