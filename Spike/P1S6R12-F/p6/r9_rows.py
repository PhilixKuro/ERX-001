import importlib.util, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("prune", ROOT / "Spike/P1S6R6-csv-prune.py")
p = importlib.util.module_from_spec(spec); spec.loader.exec_module(p)
k = p.keep_keys()
keys = ["(Empty)","Add {0}...","Available","Available:Raven User","CN Tax","Inter Company Invoice","JAN","Madam","Manufacturing Setup","Master","Miss","Mrs","Select {0}...","This field is read only and cannot be edited.","To:UOM Conversion Factor","{0} Filter Applied","{0} Filters Applied",
 "Fetch Timesheet","From Date","To Date","Click to sort by {0}","Filter based on {0}","of","Load More","Empty","Select","Search","Raven User","Accounting Ledger","View","Mr","Ms","Dr"]
for key in keys:
    print(repr(key), [n for n, s in k.items() if key in s])
