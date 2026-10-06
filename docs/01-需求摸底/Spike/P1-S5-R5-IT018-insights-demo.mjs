// P1-S5-R5 SB IT-018（R3 Part3 TS-011 第 2～3 步，SL-006 ②③）：演示站 Insights 验收。
//
// 宿主无头 Chrome 经 DevTools 协议驱动（Node 24 自带 WebSocket，不装依赖）：
//   登录 → 打开 /insights 核标题 → 打开数据源列表核 Site DB → 建一个工作簿与查询
//   「Site DB · tabCompany · 计数」→ 执行得 1 → 打开该查询页截图 → 删除工作簿（连带删查询）→ 核无残留。
// 建与执行走的是界面同一批接口：frappe.client.insert（workbook.ts addQuery 的 query.insert()）、
// insights.api.run_doc_method → InsightsQueryv3.execute（查询页「运行」）。
//
//   node P1-S5-R5-IT018-insights-demo.mjs
import { spawn } from "node:child_process";
import { mkdtempSync, readFileSync, rmSync, writeFileSync, existsSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { fileURLToPath } from "node:url";

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const BASE = "http://localhost:8000";
// 不用 URL.pathname：中文目录名会被百分号编码
const OUT = fileURLToPath(new URL("./", import.meta.url));
const TITLE = "_FCT IT-018 验收";
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const failures = [];

function check(label, actual, expected) {
	const ok = JSON.stringify(actual) === JSON.stringify(expected);
	console.log(`[${ok ? "通过" : "失败"}] ${label}：实得 ${JSON.stringify(actual)}，应为 ${JSON.stringify(expected)}`);
	if (!ok) failures.push(label);
}

class Cdp {
	constructor(url) {
		this.ws = new WebSocket(url);
		this.id = 0;
		this.pending = new Map();
		this.ws.onmessage = (e) => {
			const msg = JSON.parse(e.data);
			if (msg.id && this.pending.has(msg.id)) {
				this.pending.get(msg.id)(msg);
				this.pending.delete(msg.id);
			}
		};
	}
	open() {
		return new Promise((r) => (this.ws.onopen = r));
	}
	send(method, params = {}) {
		const id = ++this.id;
		this.ws.send(JSON.stringify({ id, method, params }));
		return new Promise((r) => this.pending.set(id, r));
	}
	async eval(expression) {
		const r = await this.send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
		if (r.result?.exceptionDetails) throw new Error(JSON.stringify(r.result.exceptionDetails));
		return r.result?.result?.value;
	}
	async api(method, body) {
		// 用页面自己的会话与 CSRF 令牌调接口，与界面同源
		return this.eval(`(async () => {
			const r = await fetch("/api/method/${method}", {
				method: "POST",
				headers: { "Content-Type": "application/json", "X-Frappe-CSRF-Token": window.csrf_token || "" },
				body: ${JSON.stringify(JSON.stringify(body))},
			});
			return { status: r.status, body: await r.json() };
		})()`);
	}
	async shot(name) {
		const r = await this.send("Page.captureScreenshot", { format: "png" });
		const path = join(OUT, name);
		writeFileSync(path, Buffer.from(r.result.data, "base64"));
		console.log(`截图：Spike/${name}`);
	}
}

async function waitFor(cdp, expression, ms = 30000) {
	const end = Date.now() + ms;
	while (Date.now() < end) {
		try {
			if (await cdp.eval(expression)) return true;
		} catch {}
		await sleep(500);
	}
	return false;
}

async function main() {
	const profile = mkdtempSync(join(tmpdir(), "erx-it018-"));
	// 调试端口取 0 再读 DevToolsActivePort：写死的端口可能落在 Windows 保留段
	const chrome = spawn(CHROME, [
		"--headless=new", "--remote-debugging-port=0", `--user-data-dir=${profile}`,
		"--no-first-run", "--no-default-browser-check", "--window-size=1440,900", "about:blank",
	]);
	let cdp;
	let workbook;
	try {
		let port;
		for (let i = 0; i < 40 && !port; i++) {
			await sleep(250);
			const f = join(profile, "DevToolsActivePort");
			if (existsSync(f)) port = readFileSync(f, "utf8").split("\n")[0].trim();
		}
		let target;
		for (let i = 0; i < 40 && !target; i++) {
			try {
				target = (await (await fetch(`http://127.0.0.1:${port}/json/list`)).json()).find((t) => t.type === "page");
			} catch {}
			if (!target) await sleep(250);
		}
		cdp = new Cdp(target.webSocketDebuggerUrl);
		await cdp.open();
		await cdp.send("Page.enable");
		await cdp.send("Runtime.enable");
		await cdp.send("Emulation.setDeviceMetricsOverride", { width: 1440, height: 900, deviceScaleFactor: 1, mobile: false });

		console.log("\n== 登录 ==");
		await cdp.send("Page.navigate", { url: `${BASE}/login` });
		await sleep(2000);
		const login = await cdp.eval(
			`fetch("/api/method/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({usr:"Administrator",pwd:"admin"})}).then(r=>r.status)`
		);
		check("登录", login, 200);

		console.log("\n== SL-006 ② 打开 /insights ==");
		const status = await cdp.eval(`fetch("/insights").then(r=>r.status)`);
		check("/insights 返回", status, 200);
		await cdp.send("Page.navigate", { url: `${BASE}/insights` });
		await waitFor(cdp, `document.querySelector("#app") && document.querySelector("#app").innerText.length > 50`);
		await sleep(1500);
		const title = await cdp.eval("document.title");
		console.log(`页面标题：${title}`);
		check("页面标题含 Insights", /insights/i.test(title), true);
		await cdp.shot("P1-S5-R5-IT018-insights-home.png");

		console.log("\n== SL-006 ② 数据源列表有 Site DB ==");
		await cdp.send("Page.navigate", { url: `${BASE}/insights/data-source` });
		// 列表里 Site DB 不显示原名：前端把 is_site_db 且标题为 Site DB 的那条改显 window.location.hostname
		// （insights frontend/src2/data_source/data_source.ts:17），故按记录核、按主机名核界面
		const src = await cdp.api("frappe.client.get_list", {
			doctype: "Insights Data Source v3", fields: ["name", "title", "is_site_db", "status"],
		});
		console.log(`数据源记录：${JSON.stringify(src.body.message)}`);
		check("数据源记录含 Site DB（is_site_db=1、Active）",
			(src.body.message || []).some((s) => s.name === "Site DB" && s.is_site_db === 1 && s.status === "Active"), true);
		const hasSiteDb = await waitFor(cdp, `document.body.innerText.includes(location.hostname) && document.body.innerText.includes("Active")`);
		check("数据源列表显示 Site DB 那一行（标为主机名 localhost）", hasSiteDb, true);
		await sleep(1000);
		await cdp.shot("P1-S5-R5-IT018-data-sources.png");

		// 重跑前清掉上次中断留下的同名工作簿
		const stale = await cdp.api("frappe.client.get_list", {
			doctype: "Insights Workbook", filters: { title: TITLE }, pluck: "name",
		});
		for (const name of stale.body.message || []) {
			await cdp.api("frappe.client.delete", { doctype: "Insights Workbook", name });
			console.log(`清掉上次残留的工作簿 ${name}`);
		}

		console.log("\n== SL-006 ③ 建查询：Site DB · tabCompany · 计数 ==");
		const wb = await cdp.api("frappe.client.insert", { doc: { doctype: "Insights Workbook", title: TITLE } });
		check("建工作簿", wb.status, 200);
		workbook = wb.body.message.name;
		console.log(`工作簿 ${workbook}`);
		const operations = [
			{ type: "source", table: { type: "table", data_source: "Site DB", table_name: "tabCompany" } },
			{
				type: "summarize",
				measures: [{ column_name: "count", data_type: "Integer", aggregation: "count", measure_name: "count_of_rows" }],
				dimensions: [],
			},
		];
		const q = await cdp.api("frappe.client.insert", {
			doc: {
				doctype: "Insights Query v3", title: "tabCompany 行数", workbook,
				use_live_connection: 1, is_builder_query: 1, sort_order: 0,
				operations: JSON.stringify(operations),
			},
		});
		check("建查询", q.status, 200);
		const query = q.body.message.name;
		console.log(`查询 ${query}`);

		// 与查询页同：docs 传整份文档（run_doc_method 用请求体里的文档构造，不重读库）
		const run = await cdp.api("insights.api.run_doc_method", {
			method: "execute",
			docs: q.body.message,
			args: {},
		});
		check("执行查询", run.status, 200);
		if (run.status !== 200) console.log(`报错：${JSON.stringify(run.body).slice(0, 800)}`);
		const result = run.body.message;
		console.log(`SQL：${result?.sql}`);
		console.log(`列：${JSON.stringify(result?.columns?.map((c) => c.name))}；行：${JSON.stringify(result?.rows)}`);
		check("tabCompany 行数", result?.rows?.[0]?.count_of_rows, 1);

		console.log("\n== 在界面打开该查询并截图 ==");
		await cdp.send("Page.navigate", { url: `${BASE}/insights/workbook/${workbook}/query/${query}` });
		const shown = await waitFor(cdp, `document.body.innerText.includes("tabCompany")`, 30000);
		check("查询页显示 tabCompany", shown, true);
		await waitFor(cdp, `/count_of_rows|Count of Rows/i.test(document.body.innerText)`, 20000);
		await sleep(2500);
		await cdp.shot("P1-S5-R5-IT018-query-tabCompany-count.png");
	} finally {
		if (cdp && workbook) {
			console.log("\n== 删除工作簿（on_trash 连带删查询） ==");
			const del = await cdp.api("frappe.client.delete", { doctype: "Insights Workbook", name: workbook });
			check("删工作簿", del.status, 200);
			const left = await cdp.api("frappe.client.get_count", { doctype: "Insights Query v3", filters: { workbook } });
			check("该工作簿下的查询残留", left.body.message, 0);
			const wbLeft = await cdp.api("frappe.client.get_count", { doctype: "Insights Workbook", filters: { title: TITLE } });
			check("同名工作簿残留", wbLeft.body.message, 0);
		}
		chrome.kill();
		await sleep(500);
		rmSync(profile, { recursive: true, force: true });
	}
	console.log(`\n结果：失败 ${failures.length} 项${failures.length ? "：" + failures.join("、") : ""}`);
	process.exit(failures.length ? 1 : 0);
}

main().catch((e) => {
	console.error(e);
	process.exit(1);
});
