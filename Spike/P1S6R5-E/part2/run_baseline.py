import importlib.util, json, sys, subprocess
from pathlib import Path
spec = importlib.util.spec_from_file_location("bl", "D:/ERX-001/Spike/P1S6R4-baseline.py")
bl = importlib.util.module_from_spec(spec); spec.loader.exec_module(bl)
def commits():
    r = {}
    for app in bl.APPS:
        r[app] = subprocess.run(["git","-C",str(bl.ROOT/"apps"/app),"rev-parse","HEAD"],capture_output=True,text=True).stdout.strip()
    return r
bl.commits = commits
sys.argv = ["x", "--out", "D:/ERX-001/Spike/P1S6R5-E/part2/baseline.out.json"]
bl.main()
