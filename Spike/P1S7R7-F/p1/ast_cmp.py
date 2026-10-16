"""比对 39b2cec^ 与 39b2cec 每个 .py 的 AST（去 docstring 无关，排序 import）。"""
import ast, subprocess, sys
repo = sys.argv[1]
files = subprocess.run(["git","-C",repo,"show","--name-only","--format=","39b2cec"],capture_output=True,text=True).stdout.split()
def norm(src):
    t = ast.parse(src)
    # 把模块级与函数内的 import 语句按 dump 排序（只针对连续 import 块）
    class S(ast.NodeTransformer):
        def generic_visit(self, node):
            super().generic_visit(node)
            for f in ("body","orelse","finalbody"):
                b = getattr(node,f,None)
                if isinstance(b,list):
                    imps=[n for n in b if isinstance(n,(ast.Import,ast.ImportFrom))]
                    rest=[n for n in b if not isinstance(n,(ast.Import,ast.ImportFrom))]
                    for n in imps:
                        n.names=sorted(n.names,key=lambda a:(a.name,a.asname or ""))
                    setattr(node,f,sorted(imps,key=ast.dump)+rest) if imps else None
            return node
    return ast.dump(S().visit(t), include_attributes=False)
diff=[]
for f in files:
    if not f.endswith(".py"): continue
    a = subprocess.run(["git","-C",repo,"show",f"39b2cec^:{f}"],capture_output=True).stdout.decode("utf-8")
    b = subprocess.run(["git","-C",repo,"show",f"39b2cec:{f}"],capture_output=True).stdout.decode("utf-8")
    if norm(a)!=norm(b): diff.append(f)
print("files",len(files),"ast-different",len(diff))
for f in diff: print(" ",f)
