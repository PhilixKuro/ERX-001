"""For each JS file: list function defs (line) with backend method strings inside; resolve python paths to file:line."""
import re, sys
from pathlib import Path
APPS = Path(r"D:/ERX-001/frappe-bench/apps")
DEF = re.compile(r"^\s*(?:async\s+)?([A-Za-z_][\w]*)\s*(?::\s*(?:async\s+)?function\s*\(|\([^)]*\)\s*\{\s*$|:\s*(?:async\s*)?\(?[\w, ]*\)?\s*=>)")
DEF2 = re.compile(r"^\s*([\w.]+)\s*=\s*(?:async\s+)?function")
METH = re.compile(r"""method:\s*["']([\w.]+)["']|frappe\.(?:x?call)\(\s*["']([\w.]+)["']""")

def resolve(path):
    parts = path.split(".")
    app = parts[0]
    for cut in range(len(parts) - 1, 0, -1):
        mod = APPS / app / Path(*parts[:cut]).with_suffix(".py")
        pkg = APPS / app / Path(*parts[:cut]) / "__init__.py"
        for f in (mod, pkg):
            if f.exists():
                name = parts[cut]
                for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
                    if re.match(rf"\s*def {re.escape(name)}\(", line):
                        return f"{f.relative_to(APPS).as_posix()}:{i}"
                return f"{f.relative_to(APPS).as_posix()}:? ({name})"
    return "?"

for rel in sys.argv[1:]:
    lines = (APPS / rel).read_text(encoding="utf-8").splitlines()
    cur = None
    out = {}
    for i, line in enumerate(lines, 1):
        m = DEF.match(line) or DEF2.match(line)
        if m and m.group(1) not in {"if", "for", "while", "switch", "function", "return", "catch"}:
            cur = f"{m.group(1)}@{i}"
            out.setdefault(cur, [])
        for mm in METH.finditer(line):
            p = mm.group(1) or mm.group(2)
            if cur and "." in p:
                out[cur].append((i, p))
    print(f"##### {rel}")
    for k, v in out.items():
        if v:
            print(k)
            for i, p in v:
                print(f"    {i}: {p} -> {resolve(p)}")
