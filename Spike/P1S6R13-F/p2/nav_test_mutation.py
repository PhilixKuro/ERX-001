# R13 F p2：把 test_business_flow_navigation 里纯 json 的四条断言照抄到宿主上，
# 对 business_flow.json 的副本打变异，看哪些变异能被现有断言杀掉（不跑 bench，不动受管文件）。
import copy, json, re, sys
from pathlib import Path

root = Path(sys.argv[1])
app = root / "frappe-bench/apps/frappe_china/frappe_china"
test_src = (app / "tests/test_business_flow_navigation.py").read_text(encoding="utf-8")
import ast

EXPECTED_LINKS = [tuple(x) for x in ast.literal_eval(re.search(r"EXPECTED_LINKS = (\[.*?\n\])", test_src, re.S).group(1))]
SECTIONS = ["Master Data", "Selling", "Buying", "Stock", "Manufacturing", "Finance", "Reports"]
icon = json.loads((app / "desktop_icon/business_flow.json").read_text(encoding="utf-8"))
base = json.loads((app / "workspace_sidebar/business_flow.json").read_text(encoding="utf-8"))


def assertions(data):
	"""返回失败的断言名列表"""
	bad = []
	if data["module"] != "CN Tax":
		bad.append("module")
	if [i["label"] for i in data["items"] if i["type"] == "Section Break"] != SECTIONS:
		bad.append("sections_order")
	labels = [i["label"] for i in data["items"] if i["type"] == "Link"]
	if len(labels) != len(set(labels)):
		bad.append("unique_labels")
	if sum(i["link_type"] == "URL" for i in data["items"]) != 4:
		bad.append("url_count")
	links = [(i["label"], i["link_type"], i.get("link_to") or i.get("url")) for i in data["items"] if i["type"] == "Link"]
	if links != EXPECTED_LINKS:
		bad.append("links_match_plan")
	if icon["label"] != data["title"] or icon["link_to"] != data["name"]:
		bad.append("icon_label_equals_title")
	return bad


def mut_move_section(d):
	"""把 Selling 分节断点往后移一位：分节顺序与条目顺序都不变，归属变了"""
	items = d["items"]
	i = next(k for k, it in enumerate(items) if it["type"] == "Section Break" and it["label"] == "Selling")
	items[i], items[i + 1] = items[i + 1], items[i]
	return d


def mut_swap_links(d):
	items = d["items"]
	idx = [k for k, it in enumerate(items) if it["type"] == "Link"]
	a, b = idx[0], idx[1]
	items[a], items[b] = items[b], items[a]
	return d


def mut_drop_link(d):
	items = d["items"]
	k = next(k for k, it in enumerate(items) if it["type"] == "Link")
	del items[k]
	return d


def mut_change_link_to(d):
	for it in d["items"]:
		if it["type"] == "Link" and it["label"] == "Chart of Accounts":
			it["link_to"] = "Account Tree"
			break
	return d


def mut_url_to_doctype(d):
	for it in d["items"]:
		if it.get("link_type") == "URL":
			it["link_type"] = "DocType"
			it["link_to"] = it.pop("url")
			break
	return d


def mut_title(d):
	d["title"] = "Business Flows"
	return d


def mut_module(d):
	d["module"] = "Core"
	return d


print("基线失败断言:", assertions(copy.deepcopy(base)))
for name, fn in [
	("分节断点后移一位（Quotation 落入 Master Data）", mut_move_section),
	("同节内两条目换序", mut_swap_links),
	("删一个条目", mut_drop_link),
	("改一个 link_to", mut_change_link_to),
	("URL 项改成 DocType 项", mut_url_to_doctype),
	("改侧栏 title", mut_title),
	("改 module", mut_module),
]:
	bad = assertions(fn(copy.deepcopy(base)))
	print(f"{'[杀死]' if bad else '[存活]'} {name}: 失败断言={bad}")
