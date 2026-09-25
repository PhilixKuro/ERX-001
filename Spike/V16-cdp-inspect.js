/*
 * V-16 follow-up: evaluate a fixed set of expressions inside the live desk
 * page and print the answers. Separate from V16-cdp-run.js so the main probe
 * stays untouched.
 *
 *   node D:\ERX-001\Spike\V16-cdp-inspect.js
 *
 * Two facts this settles, both needed for the "verify to the boundary"
 * requirement (SA-probe spec discipline 3):
 *
 * 1. WHICH desk code is actually defined when an own-app script parses.
 *    The 9 bundles in frappe's own app_include_js are upfront, but desk also
 *    pulls bundles on demand via frappe.require (kanban, form builder, print
 *    ...). Anything not yet required is NOT patchable at parse time -- that is
 *    a hard boundary on the override technique, so it must be measured, not
 *    assumed.
 *
 * 2. WHERE the /desk/undefined request really comes from. The probe patched
 *    get_icon_for_menu_item and it WAS called, yet /desk/undefined appeared
 *    identically in the patched and the unpatched baseline run -- so that is
 *    not the producing path. set_header_icon builds `<img src=${...}>` from
 *    get_default_icon() -> frappe.boot.app_data[0].app_logo_url; read the real
 *    value instead of guessing.
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
const PORT = 9240;
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));

class CDP {
	constructor(wsUrl) {
		this.ws = new WebSocket(wsUrl);
		this.id = 0;
		this.pending = new Map();
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
			}
		});
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
	const profile = fs.mkdtempSync(path.join(os.tmpdir(), "erx-v16i-"));
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
	let cdp;
	try {
		const v = await httpJson(`http://127.0.0.1:${PORT}/json/version`);
		cdp = new CDP(v.webSocketDebuggerUrl);
		await cdp.ready;
		const { targetId } = await cdp.send("Target.createTarget", { url: "about:blank" });
		const { sessionId: S } = await cdp.send("Target.attachToTarget", { targetId, flatten: true });
		await cdp.send("Page.enable", {}, S);
		await cdp.send("Runtime.enable", {}, S);

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

		const expr = `JSON.stringify({
			/* 1. lazily-required vs upfront: what the own-app script could patch */
			upfront_defined: {
				"frappe.ui.SidebarHeader": typeof (frappe.ui||{}).SidebarHeader,
				"frappe.views.ListView": typeof (frappe.views||{}).ListView,
				"frappe.ui.form.Form": typeof ((frappe.ui||{}).form||{}).Form,
				"frappe.views.ReportView": typeof (frappe.views||{}).ReportView,
				"frappe.router": typeof frappe.router
			},
			lazy_defined_now: {
				"frappe.views.KanbanView": typeof (frappe.views||{}).KanbanView,
				"frappe.ui.FileUploader": typeof (frappe.ui||{}).FileUploader,
				"frappe.views.GanttView": typeof (frappe.views||{}).GanttView,
				"frappe.views.CalendarView": typeof (frappe.views||{}).CalendarView,
				"frappe.form_builder": typeof frappe.form_builder,
				"frappe.ui.FormBuilder": typeof ((frappe.ui||{})).FormBuilder
			},
			/* 2. the real /desk/undefined source */
			app_data_len: (frappe.boot.app_data||[]).length,
			app_data0: (frappe.boot.app_data||[])[0] || null,
			app_logo_url_boot: frappe.boot.app_logo_url,
			header_icon_live: (function(){
				try { return frappe.app.sidebar.sidebar_header.header_icon; } catch(e){ return 'err:'+e; }
			})(),
			sidebar_title: (function(){
				try { return frappe.app.sidebar.sidebar_title; } catch(e){ return 'err:'+e; }
			})(),
			desktop_icon_match: (function(){
				try {
					var t = frappe.app.sidebar.sidebar_title;
					var f = frappe.boot.desktop_icons.find(function(x){ return x.label===t && x.hidden!=1; });
					return f ? {label:f.label, logo_url:f.logo_url} : null;
				} catch(e){ return 'err:'+e; }
			})(),
			imgs_with_undefined_src: Array.from(document.querySelectorAll('img'))
				.map(function(i){ return i.getAttribute('src'); })
				.filter(function(s){ return s===null || s==='undefined' || /undefined/.test(s||''); }),
			header_logo_html: (function(){
				var el = document.querySelector('.header-logo');
				return el ? el.innerHTML.slice(0,200) : null;
			})()
		})`;
		const out = await cdp.send("Runtime.evaluate", { expression: expr, returnByValue: true }, S);
		const data = JSON.parse(out.result.value);
		console.log(JSON.stringify(data, null, 2));

		/* now force a lazy bundle to load, and re-check: proves the lazy classes
		 * become patchable only AFTER frappe.require pulls them in */
		await cdp.send(
			"Runtime.evaluate",
			{ expression: `frappe.set_route('List','Item','Kanban')`, returnByValue: true },
			S
		);
		await sleep(6000);
		const out2 = await cdp.send(
			"Runtime.evaluate",
			{
				expression: `JSON.stringify({
					route: (frappe.get_route()||[]).join('/'),
					KanbanView_after: typeof (frappe.views||{}).KanbanView,
					FileUploader_after: typeof (frappe.ui||{}).FileUploader
				})`,
				returnByValue: true,
			},
			S
		);
		console.log("after forcing a lazy view:", out2.result.value);
	} catch (e) {
		console.log("ERR", String(e));
	} finally {
		if (cdp) cdp.close();
		try {
			chrome.kill();
		} catch (e) {}
	}
})();
