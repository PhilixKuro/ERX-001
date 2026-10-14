import importlib.util, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("b", ROOT / "Spike/P1S6R4-baseline.py"); b = importlib.util.module_from_spec(spec); spec.loader.exec_module(b)
m, _ = b.merged_dict()
for k in sys.argv[1:]:
    print(repr(k), "=>", repr(m.get(k)))
