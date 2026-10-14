import sys, json
a=open(sys.argv[1],'rb').read(); b=open(sys.argv[2],'rb').read()
for n,x in (('old',a),('new',b)):
    print(n, len(x), 'crlf', x.count(b'\r\n'), 'lf_only', x.count(b'\n')-x.count(b'\r\n'), 'ends_nl', x.endswith(b'\n'))
print('json equal:', json.loads(a)==json.loads(b))
print('bytes equal ignoring CR/trailing nl:', a.replace(b'\r\n',b'\n').rstrip(b'\n')==b.replace(b'\r\n',b'\n').rstrip(b'\n'))
