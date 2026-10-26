"""Task 25D: cheap structural lint for writeup/paper.tex (no LaTeX installed): braces, brackets, environments,
non-ASCII characters, unescaped % after digits, unescaped _ / & / # outside math, verbatim and comments."""
import re
import sys
from pathlib import Path

src = Path(sys.argv[1]).read_text(encoding="utf-8")
# drop verbatim blocks and comments
body = re.sub(r"\\begin\{verbatim\}.*?\\end\{verbatim\}", "", src, flags=re.S)
body = "\n".join(re.sub(r"(?<!\\)%.*", "", line) for line in body.splitlines())
print("braces", body.count("{") - body.count("\\{"), body.count("}") - body.count("\\}"))
for env in sorted(set(re.findall(r"\\begin\{(\w+\*?)\}", body))):
    b, e = body.count("\\begin{%s}" % env), body.count("\\end{%s}" % env)
    if b != e:
        print("ENV MISMATCH", env, b, e)
print("non-ASCII:", sorted(set(c for c in body if ord(c) > 127)))
text_only = re.sub(r"\$[^$]*\$", "", body)                       # crude: drop inline math
text_only = re.sub(r"\\(texttt|url|href|label|ref|includegraphics|cite|graphicspath|bibitem)\{[^}]*\}", "", text_only)
for i, line in enumerate(text_only.splitlines(), 1):
    for ch in ("_", "#"):
        if re.search(r"(?<!\\)" + re.escape(ch), line):
            print(f"unescaped {ch!r} line {i}: {line.strip()[:90]}")
envs_with_amp = ("tabular", "tabularx", "longtable", "align")
depth = 0
for i, line in enumerate(body.splitlines(), 1):
    if re.search(r"\\begin\{(%s)\}" % "|".join(envs_with_amp), line):
        depth += 1
    if re.search(r"\\end\{(%s)\}" % "|".join(envs_with_amp), line):
        depth -= 1
    if depth == 0 and re.search(r"(?<!\\)&", line):
        print(f"bare & outside table line {i}: {line.strip()[:90]}")
for m in re.finditer(r"\\ref\{([^}]*)\}", body):
    if "\\label{%s}" % m.group(1) not in body:
        print("missing label", m.group(1))
for m in re.finditer(r"\\cite\{([^}]*)\}", body):
    for k in m.group(1).split(","):
        if "\\bibitem{%s}" % k.strip() not in body:
            print("missing bibitem", k)
for m in re.finditer(r"\\includegraphics(?:\[[^]]*\])?\{([^}]*)\}", body):
    p = Path(sys.argv[1]).parent / "figures" / m.group(1)
    print("figure", m.group(1), "OK" if p.exists() else "MISSING")
