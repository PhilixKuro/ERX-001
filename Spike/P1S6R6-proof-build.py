"""SL-014 ⑥ 判别力整链反证的屏清单（宿主 python -I -X utf8 跑，产出 Spike/P1S6R6-screens-proof.json）。
三屏各对应一种造出的失败：
  proof-sidebar     自有侧栏加一条英文 label 条目（不加 csv）→ 应报 english 含 Zzproof
  proof-traditional csv 把 Business Flow 临时改成繁体「業務流程」→ 应报 traditional 含 業
  proof-title       页面上给主按钮设英文 title → 应报 title_issues
造失败与恢复由 Spike/P1S6R6-proof-plant.py 做。"""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
spec = json.loads((ROOT / "Spike/P1S6R6-screens.json").read_text(encoding="utf-8"))
BF = "Business Flow"
screens = [
	{"id": "proof-sidebar", "stage": "反证", "state": "list", "route": "desk/company", "sidebar": BF,
	 "wait_for": "cur_list?.doctype==='Company'", "extract_root": ".body-sidebar",
	 "note": "自有侧栏加英文条目 Zzproof Entry"},
	{"id": "proof-traditional", "stage": "反证", "state": "list", "route": "desk/company", "sidebar": None,
	 "wait_for": "cur_list?.doctype==='Company'", "extract_root": ".body-sidebar",
	 "steps": [{"evaluate": "frappe.app.sidebar.setup(\"Business Flow\"); true", "pause": 1500}],
	 "note": "csv 把 Business Flow 改繁体"},
	{"id": "proof-title", "stage": "反证", "state": "saved", "route": "desk/company/{{company}}", "sidebar": BF,
	 "wait_for": 'window.cur_frm?.doctype==="Company" && !!cur_frm.fields_dict && !frappe.dom.freeze_count',
	 "steps": [{"evaluate": "cur_frm.page.wrapper[0].querySelector('.title-text').setAttribute('title','Save this document'); true"}],
	 "note": "当前表单标题的 title 属性临时设英文（只改页面、不落库）"},
]
proof = {k: spec[k] for k in ("allow", "data_selectors", "data_patterns", "default_data", "trad_chars_file")}
proof["variables"] = {"company": spec["variables"]["company"]} if "company" in spec["variables"] else {"company": {"from": "values.json"}}
proof["screens"] = screens
(ROOT / "Spike/P1S6R6-screens-proof.json").write_text(json.dumps(proof, ensure_ascii=False, indent=1), encoding="utf-8")
print(len(screens), "proof screens")
