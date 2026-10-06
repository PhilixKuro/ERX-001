// P1-S5-R5 SB IT-024（本机基线，R3 Part4 SL-008 ①后半）：本机浏览器打开桌面页后跑 realtime_check.run()。
//
// 用宿主的无头 Chrome，经 DevTools 协议驱动（Node 24 自带 WebSocket，不装依赖）：
//   登录 → 打开 /desk → 核 realtime_check.js 已加载、socket 已连 → 宿主跑 bench execute run() → 核页面弹出提示。
// 另跑两次对照：页面关闭时 run() 应失败；停 realtime-proxy 时 run() 应失败（④ 反证的本机版）。
//
//   node P1-S5-R5-IT024-local-baseline.mjs
import { spawn, spawnSync } from "node:child_process";
import { mkdtempSync, rmSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";

const CHROME = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const BASE = "http://localhost:8000";
const PORT = 9333;
const DOCKER_DIR = new URL("../../../docker/", import.meta.url).pathname.replace(/^\/([A-Za-z]:)/, "$1");
const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
const failures = [];

function check(label, actual, expected) {
	const ok = JSON.stringify(actual) === JSON.stringify(expected);
	console.log(`[${ok ? "通过" : "失败"}] ${label}：实得 ${JSON.stringify(actual)}，应为 ${JSON.stringify(expected)}`);
	if (!ok) failures.push(label);
}

function compose(args) {
	const r = spawnSync("docker", ["compose", ...args], {
		cwd: DOCKER_DIR,
		encoding: "utf8",
		env: { ...process.env, MSYS_NO_PATHCONV: "1" },
	});
	return (r.stdout || "") + (r.stderr || "");
}

function runCheck(timeout) {
	// 计划原文（TS-013 第 2 步）的命令；输出原样打出
	const out = compose([
		"exec", "-T", "-w", "/workspace/frappe-bench", "frappe",
		"bench", "--site", "erx.localhost", "execute", "frappe_china.realtime_check.run",
		"--kwargs", JSON.stringify({ user: "Administrator", timeout }),
	]);
	console.log(out.trim().split("\n").map((l) => "    | " + l).join("\n"));
	const m = out.match(/\{[\s\S]*\}\s*$/);
	return m ? JSON.parse(m[0]) : { ok: null };
}

class Cdp {
	constructor(url) {
		this.ws = new WebSocket(url);
		this.id = 0;
		this.pending = new Map();
		this.events = [];
		this.ws.onmessage = (e) => {
			const msg = JSON.parse(e.data);
			if (msg.id && this.pending.has(msg.id)) {
				this.pending.get(msg.id)(msg);
				this.pending.delete(msg.id);
			} else if (msg.method) this.events.push(msg);
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
		return r.result?.result?.value;
	}
}

async function waitFor(cdp, expression, ms = 30000) {
	const end = Date.now() + ms;
	while (Date.now() < end) {
		if (await cdp.eval(expression)) return true;
		await sleep(500);
	}
	return false;
}

async function main() {
	const profile = mkdtempSync(join(tmpdir(), "erx-it024-"));
	const chrome = spawn(CHROME, [
		"--headless=new", `--remote-debugging-port=${PORT}`, `--user-data-dir=${profile}`,
		"--no-first-run", "--no-default-browser-check", "about:blank",
	]);
	try {
		let target;
		for (let i = 0; i < 40 && !target; i++) {
			await sleep(250);
			try {
				target = (await (await fetch(`http://127.0.0.1:${PORT}/json/list`)).json()).find((t) => t.type === "page");
			} catch {}
		}
		const cdp = new Cdp(target.webSocketDebuggerUrl);
		await cdp.open();
		await cdp.send("Page.enable");
		await cdp.send("Network.enable");
		await cdp.send("Runtime.enable");

		console.log("\n== 对照 A：没有打开的桌面页 ==");
		check("无桌面页时 run() 失败", runCheck(5).ok, false);

		console.log("\n== 登录并打开桌面页 ==");
		await cdp.send("Page.navigate", { url: `${BASE}/login` });
		await sleep(2000);
		const login = await cdp.eval(
			`fetch("/api/method/login",{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({usr:"Administrator",pwd:"admin"})}).then(r=>r.status)`
		);
		check("登录", login, 200);
		cdp.events.length = 0;
		await cdp.send("Page.navigate", { url: `${BASE}/desk` });
		const booted = await waitFor(cdp, "!!(window.frappe && frappe.boot && frappe.realtime && frappe.realtime.socket && frappe.realtime.socket.connected)");
		check("桌面页加载且实时 socket 已连", booted, true);
		const urls = cdp.events.filter((e) => e.method === "Network.responseReceived").map((e) => e.params.response.url);
		const js = urls.filter((u) => u.includes("realtime_check"));
		console.log(`realtime_check.js 请求：${JSON.stringify(js)}`);
		check("realtime_check.js 已加载（网络面板）", js.length > 0, true);
		const socketUrl = urls.find((u) => u.includes("/socket.io/"));
		console.log(`实时连接地址：${socketUrl}`);
		check("实时连接走宿主 9100（经 realtime-proxy）", !!socketUrl && new URL(socketUrl).port === "9100", true);

		await cdp.eval(`window.__alerts=[];const _sa=frappe.show_alert;frappe.show_alert=function(m,...a){window.__alerts.push(typeof m==="string"?m:m.message);return _sa.call(this,m,...a)};true`);

		console.log("\n== SL-008 ①：本机桌面页打开时 run() ==");
		const ok = runCheck(30);
		check("run() 通过", ok.ok, true);
		await sleep(500);
		const alerts = await cdp.eval("window.__alerts");
		console.log(`页面提示：${JSON.stringify(alerts)}`);
		check("页面弹出含本次 token 的提示", (alerts || []).some((a) => ok.token && a.includes(ok.token)), true);

		console.log("\n== 对照 B：停 realtime-proxy（本机版反证） ==");
		console.log(compose(["stop", "realtime-proxy"]).trim());
		await sleep(2000);
		check("proxy 停止时 run() 失败", runCheck(5).ok, false);
		console.log(compose(["start", "realtime-proxy"]).trim());
		// 前端 socket 只重连 3 次（frappe socketio_client.js reconnectionAttempts: 3），断开超过几秒即放弃；
		// 方案 TS-013 第 6 步「必要时刷新」即指此。先等自动重连，不成再刷新，两种结果都记下。
		const auto = await waitFor(cdp, "frappe.realtime.socket.connected", 15000);
		console.log(`proxy 恢复后 15 秒内自动重连：${auto}（停机约 10 秒，超过 3 次重连的窗口时为 false）`);
		if (!auto) {
			await cdp.send("Page.reload");
			check("刷新后 socket 重连", await waitFor(cdp, "!!(window.frappe && frappe.realtime && frappe.realtime.socket && frappe.realtime.socket.connected)"), true);
		}
		check("proxy 恢复后 run() 通过", runCheck(30).ok, true);
	} finally {
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
