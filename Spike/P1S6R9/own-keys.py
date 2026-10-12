"""R9 TS-025 第 4 步：断言 R8 IT-043 的 25 个按键取用的键与 CN Tax 都在清场脚本的 keep_keys()["own"] 里。

宿主 `python -I -X utf8 Spike/P1S6R9/own-keys.py`；通过退出码 0，否则列出缺的键、退出码 1。
"""
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("prune", ROOT / "Spike/P1S6R6-csv-prune.py")
prune = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prune)

expected = {item["key"] for item in json.loads((ROOT / "Spike/P1S6R8-E/sl012/literal_keys.json").read_text(encoding="utf-8"))} | {"CN Tax"}
own = prune.keep_keys()["own"]
missing = sorted(expected - own)
print(f"expected={len(expected)} own={len(own)} missing={missing}")
sys.exit(1 if missing else 0)
