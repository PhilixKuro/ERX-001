import sys

sys.path.insert(0, r"D:\ERX-001\Spike\P1S7R7-F\fix")
from repl import apply

A = r"D:\ERX-001\frappe-bench\apps\frappe_china\frappe_china"
apply(
	A + r"\install.py",
	[
		(
			'ALERT_TITLE: Final[str] = "frappe_china override self-check failed"',
			'ALERT_TITLE_SOURCE: Final[str] = "frappe_china override self-check failed"',
		),
		(
			"\n\n# Backward-compatible import for older local tests; new code must call the function.\n"
			"WHITELIST_TARGETS: Final[tuple[str, ...]] = override_targets()\n",
			"",
		),
		(
			'\t\t\tf"装载顺序不对：frappe_china 之后只能是 {list(TAIL_APPS[1:])}，实际 {order}"\n'
			'\t\t\tf"（排在它后面的：{after_china}）"',
			'\t\t\tf"装载顺序不对：应为 {target_app_order(order)}，实际 {order}"\n'
			'\t\t\tf"（frappe_china 之后只能是 {list(TAIL_APPS[1:])}，现排在它后面的：{after_china}）"',
		),
		(
			"\tif not failed:\n\t\tprint(PASS_MESSAGE)\n\t\treturn\n\n",
			"\tif not failed:\n\t\tprint(PASS_MESSAGE)\n"
			"\t\t# 通过时的提示（如站上无中式公司）只打印，不告警（总纲偏离 17）\n"
			"\t\tfor problem in problems:\n\t\t\tprint(f\"  {problem}\")\n\t\treturn\n\n"
			'\ttitle = frappe._(ALERT_TITLE_SOURCE, lang="zh")\n',
		),
		('print(f"{ALERT_TITLE}: {message}")', 'print(f"{title}: {message}")'),
		("frappe.log_error(title=frappe._(ALERT_TITLE), message=message)", "frappe.log_error(title=title, message=message)"),
		('print(f"{ALERT_TITLE}: unable to write Error Log")', 'print(f"{title}: unable to write Error Log")'),
		('"subject": frappe._(ALERT_TITLE),', '"subject": title,'),
		('print(f"{ALERT_TITLE}: unable to write Notification Log")', 'print(f"{title}: unable to write Notification Log")'),
	],
)
apply(
	A + r"\tests\test_install.py",
	[
		(
			"from frappe_china.install import WHITELIST_TARGETS, check_app_order",
			"from frappe_china.install import check_app_order, override_targets\n\n\t\ttargets = override_targets()",
		),
		("for key in WHITELIST_TARGETS", "for key in targets"),
		("hooks[WHITELIST_TARGETS[0]]", "hooks[targets[0]]"),
		('result["overrides"][WHITELIST_TARGETS[0]]', 'result["overrides"][targets[0]]'),
	],
)
print("done")
