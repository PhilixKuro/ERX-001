const { spawn } = require("node:child_process");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const readline = require("node:readline");

const base = "http://test.localhost:6787";
const port = 9336;
const pause = (milliseconds) => new Promise((resolve) => setTimeout(resolve, milliseconds));
let browser;
let socket;
let session;
let sequence = 0;
const pending = new Map();

function send(method, params = {}, sessionId = session) {
	const id = ++sequence;
	return new Promise((resolve, reject) => {
		const timer = setTimeout(() => {
			pending.delete(id);
			reject(new Error(`CDP timeout: ${method}`));
		}, 45000);
		pending.set(id, { resolve, reject, timer });
		socket.send(JSON.stringify({ id, method, params, sessionId }));
	});
}

async function evaluate(expression) {
	const result = await send("Runtime.evaluate", { expression, awaitPromise: true, returnByValue: true });
	if (result.exceptionDetails) throw new Error(JSON.stringify(result.exceptionDetails));
	return result.result.value;
}

async function main() {
	const executable = "C:/Program Files/Google/Chrome/Application/chrome.exe";
	browser = spawn(executable, [
		"--headless=new", "--no-first-run", "--no-default-browser-check",
		`--remote-debugging-port=${port}`,
		`--user-data-dir=${fs.mkdtempSync(path.join(os.tmpdir(), "erx-s6-ui-"))}`,
		"--host-resolver-rules=MAP test.localhost 127.0.0.1",
		"--window-size=1500,1000", "about:blank",
	], { stdio: "ignore", windowsHide: true });
	let version;
	for (let attempt = 0; attempt < 60; attempt++) {
		try {
			version = await (await fetch(`http://127.0.0.1:${port}/json/version`)).json();
			break;
		} catch {
			await pause(250);
		}
	}
	if (!version) throw new Error("Chrome DevTools did not start");
	socket = new WebSocket(version.webSocketDebuggerUrl);
	socket.addEventListener("message", (event) => {
		const message = JSON.parse(event.data);
		const request = pending.get(message.id);
		if (!request) return;
		pending.delete(message.id);
		clearTimeout(request.timer);
		if (message.error) request.reject(new Error(JSON.stringify(message.error)));
		else request.resolve(message.result);
	});
	await new Promise((resolve, reject) => {
		socket.addEventListener("open", resolve);
		socket.addEventListener("error", reject);
	});
	const target = await send("Target.createTarget", { url: "about:blank" });
	session = (await send("Target.attachToTarget", { targetId: target.targetId, flatten: true })).sessionId;
	await send("Page.enable");
	await send("Runtime.enable");
	await send("Network.enable");
	await send("Emulation.setDeviceMetricsOverride", { width: 1500, height: 1000, deviceScaleFactor: 1, mobile: false });
	const login = await fetch("http://127.0.0.1:6787/api/method/login", {
		method: "POST", headers: { "Content-Type": "application/json", Host: "test.localhost" },
		body: JSON.stringify({ usr: "Administrator", pwd: "admin" }),
	});
	if (!login.ok) throw new Error(`Test site login: ${login.status}`);
	const cookie = login.headers.getSetCookie().find((value) => value.startsWith("sid="));
	if (!cookie) throw new Error("Test site session cookie missing");
	await send("Network.setCookie", { name: "sid", value: cookie.split(";")[0].slice(4), domain: "test.localhost", path: "/" });
	await send("Page.navigate", { url: `${base}/desk` });
	for (let attempt = 0; attempt < 90; attempt++) {
		await pause(500);
		if (await evaluate("!!(window.frappe && frappe.boot && frappe.app)")) break;
		if (attempt === 89) throw new Error("Test site desk did not boot");
	}
	console.log(JSON.stringify({ ready: true, base, browser: version.Browser,
		language: await evaluate("frappe.boot.lang"),
	}));
	const input = process.argv[2]
		? fs.readFileSync(process.argv[2], "utf8").split(/\r?\n/).filter(Boolean)
		: readline.createInterface({ input: process.stdin });
	for await (const line of input) {
		try {
			const command = JSON.parse(line);
			if (command.close) break;
			const result = command.expression ? await evaluate(command.expression) : null;
			if (command.wait) await pause(command.wait);
			let screenshot;
			if (command.screenshot) {
				if (!/^P1S6R4-[\w-]+\.png$/.test(command.screenshot)) throw new Error("Unexpected screenshot filename");
				screenshot = path.join(__dirname, command.screenshot);
				const captured = await send("Page.captureScreenshot", { format: "png" });
				fs.writeFileSync(screenshot, Buffer.from(captured.data, "base64"));
			}
			console.log(JSON.stringify({ result, screenshot }));
		} catch (error) {
			process.exitCode = 1;
			console.log(JSON.stringify({ error: String(error) }));
		}
	}
}

main().catch((error) => {
	console.error(String(error));
	process.exitCode = 1;
}).finally(() => {
	socket?.close();
	browser?.kill();
});
