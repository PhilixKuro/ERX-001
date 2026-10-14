import subprocess, sys, re, pathlib
root = pathlib.Path(sys.argv[1])
files = subprocess.run(["git","-C",str(root),"ls-files"],capture_output=True,text=True).stdout.split()
for f in files:
    p = root/f
    if not p.is_file(): continue
    b = p.read_bytes()
    if b.startswith(b"\xef\xbb\xbf"):
        print("BOM", f)
    if f.endswith(".py"):
        t = b.decode("utf-8","replace")
        sp = len(re.findall(r"(?m)^    \S", t)); tab = len(re.findall(r"(?m)^\t", t))
        if sp and not tab: print("SPACES", f, sp)
    if b"\r\n" in b: print("CRLF", f)
