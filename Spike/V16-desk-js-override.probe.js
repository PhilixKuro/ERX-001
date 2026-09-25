/*
 * V-16 probe payload (ASCII only on purpose: Windows/GBK).
 *
 * Injected into the desk page from a minimal throwaway own-app (erx_spike)
 * via `app_include_js`. The SAME file is installed on two routes so one run
 * answers both "does injection work" and "does the bundler keep it":
 *   route A  erx_spike.bundle.js                      -> esbuild + assets.json
 *   route B  /assets/erx_spike/js/V16-raw-probe.js     -> raw, bypasses bundler
 * Each run self-identifies via document.currentScript.src and appends to
 * window.__ERX_V16.runs; the patches install only once (first route wins).
 *
 * What it records, as observed facts only:
 *   tier 1  did this file execute inside the desk page at all
 *   tier 2  at MY parse time, are desk's own classes ALREADY DEFINED
 *           (that is the load-order answer), and does patching them change
 *           real runtime behaviour during desk boot -- measured by whether
 *           the patched methods are actually CALLED after I install them
 *   tier 3  same questions after `bench build`
 *
 * CDP may pre-set window.__ERX_V16_DISABLE_PATCH = true (via
 * Page.addScriptToEvaluateOnNewDocument, which runs before any page script)
 * to get an unpatched baseline in the same browser.
 */
(function () {
	var P = (window.__ERX_V16 = window.__ERX_V16 || {});
	P.runs = P.runs || [];
	P.marks = P.marks || [];
	P.patched_by = P.patched_by || null;

	var my_src = "(unknown)";
	try {
		if (document.currentScript && document.currentScript.src) my_src = document.currentScript.src;
	} catch (e0) {}

	function mark(m) {
		P.marks.push(m);
		try {
			console.log("[ERX-V16] " + m);
		} catch (e) {}
	}

	function resolve(path) {
		var parts = path.split(".");
		var cur = window;
		for (var i = 0; i < parts.length; i++) {
			if (cur === null || cur === undefined) return undefined;
			cur = cur[parts[i]];
		}
		return cur;
	}

	/* ---------- tier 1 + load order: what exists at MY parse time ---------- */
	var srcs = [];
	var tags = document.querySelectorAll("script[src]");
	for (var i = 0; i < tags.length; i++) srcs.push(tags[i].getAttribute("src"));

	var targets = [
		"frappe",
		"frappe.boot",
		"frappe.ui",
		"frappe.ui.Sidebar",
		"frappe.ui.SidebarHeader",
		"frappe.ui.SidebarHeader.prototype.get_icon_for_menu_item",
		"frappe.ui.SidebarHeader.prototype.add_app_item",
		"frappe.views",
		"frappe.views.ListView",
		"frappe.ui.form.Form",
		"frappe.utils.desktop_icon",
		"frappe.router",
		"frappe.app",
		"frappe.ready",
		"erpnext",
		/* BOUNDARY probes: desk pulls these in on demand via frappe.require,
		 * they are NOT in the 9 upfront bundles. If they are undefined at my
		 * parse time, a parse-time prototype patch cannot reach them -- that is
		 * a hard limit of the app_include_js override technique, so measure it
		 * rather than assume it. */
		"frappe.views.KanbanView",
		"frappe.views.CalendarView",
		"frappe.views.GanttView",
		"frappe.ui.FileUploader",
		"frappe.form_builder",
		"frappe.ui.FormBuilder",
		"frappe.views.QueryReport",
		"frappe.PrintPreview"
	];
	var at_parse = {};
	for (var j = 0; j < targets.length; j++) at_parse[targets[j]] = typeof resolve(targets[j]);

	var run = {
		src: my_src,
		t_parse: Date.now(),
		readyState: document.readyState,
		script_tags_in_dom_at_parse: srcs.length,
		script_srcs_at_parse: srcs,
		at_parse: at_parse,
		patch_disabled: !!window.__ERX_V16_DISABLE_PATCH,
		installed_patches_here: false
	};
	P.runs.push(run);

	mark("run src=" + my_src);
	mark("run readyState=" + run.readyState + " script_tags=" + run.script_tags_in_dom_at_parse);
	mark("run defined_at_parse=" + JSON.stringify(at_parse));

	if (run.patch_disabled) {
		mark("baseline run (patching disabled), no patch installed");
		return;
	}
	if (P.patched_by) {
		mark("patches already installed by " + P.patched_by + ", this run only records order");
		return;
	}

	/* ---------- tier 2: patch already-defined desk code ---------- */
	P.a = { target: "frappe.ui.SidebarHeader.prototype.get_icon_for_menu_item", installed: false, calls: 0, err: null };
	P.b = { target: "frappe.utils.desktop_icon", installed: false, calls: 0, err: null };
	P.c = {
		target: "frappe.ui.SidebarHeader.prototype.add_app_item",
		installed: false,
		calls: 0,
		err: null,
		first_call_dt_ms: null,
		items: []
	};

	/* (a) replace a prototype METHOD on a class desk already defined.
	 * Shaped like the LG-074 fix: upstream writes item.icon_html, but the
	 * dropdown markup in add_app_item reads item.icon / item.icon_url only,
	 * so item.icon_url stays undefined and the <img src> becomes "/undefined".
	 * Here we write item.icon instead and watch whether /undefined stops. */
	try {
		var SH = resolve("frappe.ui.SidebarHeader");
		if (SH && SH.prototype && typeof SH.prototype.get_icon_for_menu_item === "function") {
			var orig_gi = SH.prototype.get_icon_for_menu_item;
			P.a.orig_src_head = String(orig_gi).replace(/\s+/g, " ").slice(0, 80);
			SH.prototype.get_icon_for_menu_item = function (icon, item) {
				P.a.calls++;
				var url = frappe.utils.get_desktop_icon(icon.label, frappe.boot.desktop_icon_style);
				if (url) {
					item.icon_url = url;
				} else {
					item.icon = "folder-normal";
				}
			};
			P.a.installed = true;
		} else {
			P.a.err = "not a function at my parse time (typeof=" + at_parse[P.a.target] + ")";
		}
	} catch (ea) {
		P.a.err = String(ea);
	}

	/* (b) replace a plain namespaced FUNCTION (wrap, keep original) */
	try {
		if (window.frappe && frappe.utils && typeof frappe.utils.desktop_icon === "function") {
			var orig_di = frappe.utils.desktop_icon;
			frappe.utils.desktop_icon = function () {
				P.b.calls++;
				return orig_di.apply(this, arguments);
			};
			P.b.installed = true;
		} else {
			P.b.err = "not a function at my parse time";
		}
	} catch (eb) {
		P.b.err = String(eb);
	}

	/* (c) wrap a RENDER method: proves the patch is live during desk boot and
	 * captures what upstream actually hands the markup. first_call_dt_ms tells
	 * us whether the sidebar is built after my script or before it. */
	try {
		var SH2 = resolve("frappe.ui.SidebarHeader");
		if (SH2 && SH2.prototype && typeof SH2.prototype.add_app_item === "function") {
			var orig_aa = SH2.prototype.add_app_item;
			SH2.prototype.add_app_item = function (item) {
				P.c.calls++;
				if (P.c.first_call_dt_ms === null) P.c.first_call_dt_ms = Date.now() - run.t_parse;
				if (P.c.items.length < 12) {
					P.c.items.push({
						label: item && item.label,
						icon: item && item.icon,
						icon_url: item && item.icon_url,
						icon_html_type: item ? typeof item.icon_html : "n/a"
					});
				}
				return orig_aa.apply(this, arguments);
			};
			P.c.installed = true;
		} else {
			P.c.err = "not a function at my parse time";
		}
	} catch (ec) {
		P.c.err = String(ec);
	}

	run.installed_patches_here = P.a.installed || P.b.installed || P.c.installed;
	if (run.installed_patches_here) P.patched_by = my_src;

	mark("patch a installed=" + P.a.installed + " err=" + P.a.err);
	mark("patch b installed=" + P.b.installed + " err=" + P.b.err);
	mark("patch c installed=" + P.c.installed + " err=" + P.c.err);

	/* (d) BOUNDARY: patch a class that exists at parse time but is only
	 * INSTANTIATED later, on an SPA route change. Desk is a single-page app,
	 * so a demo-control patch (CR-008) must survive route changes, not just
	 * first paint. Counting calls after frappe.set_route proves that. */
	P.d = { target: "frappe.views.ListView.prototype.setup_defaults", installed: false, calls: 0, err: null };
	try {
		var LV = resolve("frappe.views.ListView");
		if (LV && LV.prototype && typeof LV.prototype.setup_defaults === "function") {
			var orig_sd = LV.prototype.setup_defaults;
			LV.prototype.setup_defaults = function () {
				P.d.calls++;
				try {
					P.d.last_doctype = this.doctype;
				} catch (e) {}
				return orig_sd.apply(this, arguments);
			};
			P.d.installed = true;
		} else {
			P.d.err = "not a function at my parse time (typeof=" + at_parse["frappe.views.ListView"] + ")";
		}
	} catch (ed2) {
		P.d.err = String(ed2);
	}

	/* (e) BOUNDARY: the negative case. frappe.app is the Application INSTANCE
	 * and is constructed after this script runs, so an instance-level patch
	 * cannot be installed at parse time. Record the typeof rather than
	 * asserting -- this is the fact that decides whether a wait hook is
	 * needed for instance-level overrides. */
	P.e = {
		target: "frappe.app (instance) at parse time",
		typeof_at_parse: at_parse["frappe.app"],
		patchable_at_parse: at_parse["frappe.app"] === "object"
	};

	/* (f) which wait hooks actually fire on desk? frappe.ready is the
	 * documented one for WEBSITE pages; record whether it ever fires here,
	 * plus router change events (the SPA hook) and DOMContentLoaded. */
	P.hooks = { ready_fired_dt_ms: null, dom_ready_dt_ms: null, route_changes: 0, routes: [] };
	try {
		if (window.frappe && typeof frappe.ready === "function") {
			frappe.ready(function () {
				P.hooks.ready_fired_dt_ms = Date.now() - run.t_parse;
				mark("frappe.ready fired at +" + P.hooks.ready_fired_dt_ms + "ms");
			});
		}
	} catch (ef) {}
	try {
		document.addEventListener("DOMContentLoaded", function () {
			P.hooks.dom_ready_dt_ms = Date.now() - run.t_parse;
			mark("DOMContentLoaded at +" + P.hooks.dom_ready_dt_ms + "ms");
		});
	} catch (eg) {}
	/* frappe.router exists only after desk boots; poll briefly to attach */
	(function attach_router(tries) {
		try {
			if (window.frappe && frappe.router && typeof frappe.router.on === "function") {
				frappe.router.on("change", function () {
					P.hooks.route_changes++;
					try {
						P.hooks.routes.push((frappe.get_route() || []).join("/"));
					} catch (e) {}
				});
				P.hooks.router_attached_dt_ms = Date.now() - run.t_parse;
				mark("router listener attached at +" + P.hooks.router_attached_dt_ms + "ms");
				return;
			}
		} catch (e) {}
		if (tries > 0) setTimeout(function () { attach_router(tries - 1); }, 100);
	})(100);

	mark("patch d installed=" + P.d.installed + " err=" + P.d.err);
	mark("frappe.app typeof at parse=" + P.e.typeof_at_parse);
	mark("probe end for " + my_src);
})();
