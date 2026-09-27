# Helper: rewrite a probe source so every non-ASCII char becomes a \uXXXX escape.
# Keeps the probe sources ASCII-only (the ERX-001 method rule) without me having to
# hand-type escapes that the editing tool re-renders as literal CJK.
#
# Safe because in this project's probe sources every non-ASCII char sits either inside
# a normal (non-raw, non-bytes) double-quoted string literal -- where \uXXXX is the
# equivalent escape -- or inside a # comment, where the text is inert either way.
#
# Usage: python V31-asciify.py <file> [<file> ...]

import sys

for path in sys.argv[1:]:
    with open(path, encoding="utf-8") as f:
        src = f.read()
    out = []
    for ch in src:
        if ord(ch) < 128:
            out.append(ch)
        else:
            out.append("\\u%04X" % ord(ch))
    new = "".join(out)
    with open(path, "w", encoding="ascii", newline="\n") as f:
        f.write(new)
    print("%s: %d chars -> %d chars, non-ascii now %d"
          % (path, len(src), len(new), sum(1 for c in new if ord(c) > 127)))
    compile(new, path, "exec")
    print("  compiles OK")
