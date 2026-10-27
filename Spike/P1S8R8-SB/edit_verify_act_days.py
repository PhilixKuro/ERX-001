"""S8 R8 SB: four verify checks cover generator documents only (user ruling A, 2026-10-27).

The act days (D1, D2, E) carry documents the presenter writes live; those are excluded here and
tracked as SH-P1S8022. Apply only after FD-013 finishes (bench serve auto-reloads on .py edits).
"""

import os

ROOT = "d:/ERX-001/frappe-bench/apps/frappe_debug/frappe_debug"
CRLF, LF = chr(13) + chr(10), chr(10)


def edit(rel, pairs):
	path = os.path.join(ROOT, rel)
	with open(path, encoding="utf-8", newline="") as handle:
		text = handle.read()
	crlf = CRLF in text
	text = text.replace(CRLF, LF)
	for old, new in pairs:
		if new in text:
			continue
		assert text.count(old) == 1, (rel, old[:80])
		text = text.replace(old, new)
	if crlf:
		text = text.replace(LF, CRLF)
	with open(path, "w", encoding="utf-8", newline="") as handle:
		handle.write(text)


edit(
	"scenario/verify.py",
	[
		(
			'''	employee_collisions = frappe.db.sql(
		"""select a.employee, a.parent left_card, b.parent right_card, a.from_time
		from `tabJob Card Time Log` a
		join `tabJob Card Time Log` b on a.name < b.name and a.employee = b.employee
		and a.parent <> b.parent and a.from_time < b.to_time and a.to_time > b.from_time
		where a.parenttype='Job Card' and b.parenttype='Job Card' and a.employee is not null
		and a.from_time between %s and %s limit 20""",
		(sc.S, sc.E),
		as_dict=True,
	)''',
			'''	# SH-P1S8022: the act days carry live presenter documents; these four checks cover the generator
	act_days = tuple(act_scene_days(sc))
	employee_collisions = frappe.db.sql(
		"""select a.employee, a.parent left_card, b.parent right_card, a.from_time
		from `tabJob Card Time Log` a
		join `tabJob Card Time Log` b on a.name < b.name and a.employee = b.employee
		and a.parent <> b.parent and a.from_time < b.to_time and a.to_time > b.from_time
		where a.parenttype='Job Card' and b.parenttype='Job Card' and a.employee is not null
		and a.from_time between %s and %s
		and date(a.from_time) not in %s and date(b.from_time) not in %s limit 20""",
		(sc.S, sc.E, act_days, act_days),
		as_dict=True,
	)''',
		),
		(
			'''		where jc.company=%s and jc.docstatus=1 and log.parentfield='time_logs'
		group by jc.name having round(sum(log.time_in_mins), 2) <> round(jc.time_required, 2)
		limit 20""",
		(company,),
		as_dict=True,
	)''',
			'''		where jc.company=%s and jc.docstatus=1 and log.parentfield='time_logs'
		group by jc.name having round(sum(log.time_in_mins), 2) <> round(jc.time_required, 2)
		and date(min(log.from_time)) not in %s
		limit 20""",
		(company, act_days),
		as_dict=True,
	)''',
		),
		(
			'''		"""select distinct customer_name from `tabSales Order`
		where company=%s and docstatus=1 and transaction_date between %s and %s""",
		(company, sc.S, sc.E),
		pluck=True,
	)''',
			'''		"""select distinct customer_name from `tabSales Order`
		where company=%s and docstatus=1 and transaction_date between %s and %s
		and transaction_date not in %s""",
		(company, sc.S, sc.E, act_days),
		pluck=True,
	)''',
		),
		(
			'''			"""select deal.status, count(*) from `tabCRM Deal` deal
			where exists (select 1 from `tabQuotation` q where q.crm_deal = deal.name
			and q.company=%s and q.docstatus=1)
			group by deal.status""",
			(company,),''',
			'''			"""select deal.status, count(*) from `tabCRM Deal` deal
			where exists (select 1 from `tabQuotation` q where q.crm_deal = deal.name
			and q.company=%s and q.docstatus=1 and q.transaction_date not in %s)
			group by deal.status""",
			(company, act_days),''',
		),
		(
			'''		join `tabSales Order` so on so.name = soi.parent and so.docstatus=1
		where deal.status <> 'Won'""",
		(company,),
	)[0][0]''',
			'''		join `tabSales Order` so on so.name = soi.parent and so.docstatus=1
		where deal.status <> 'Won' and q.transaction_date not in %s""",
		(company, act_days),
	)[0][0]''',
		),
		(
			'''def verify(sc) -> dict:''',
			'''def act_scene_days(sc) -> list:
	"""Scene dates the nine acts are played on; their documents are written live (SH-P1S8022)."""
	return sorted({sc.D1, sc.D2, sc.E})


def verify(sc) -> dict:''',
		),
	],
)

edit(
	"tests/test_scenario_support.py",
	[
		(
			'''	def test_clear_admin_list_filters_preserves_other_settings_and_other_users(self):''',
			'''	def test_act_scene_days_are_the_three_live_dates(self):
		"""SH-P1S8022：现场单据按这三天排除，生成器自己的单据照核。"""
		from types import SimpleNamespace

		from frappe_debug.scenario.verify import act_scene_days

		sc = SimpleNamespace(D1=date(2026, 1, 7), D2=date(2026, 4, 1), E=date(2026, 10, 27))
		self.assertEqual(act_scene_days(sc), [date(2026, 1, 7), date(2026, 4, 1), date(2026, 10, 27)])

	def test_clear_admin_list_filters_preserves_other_settings_and_other_users(self):''',
		)
	],
)
print("ok")
