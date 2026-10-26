"""Task 27: rename "Study 2.2" -> "Study 1" and "Study 2.3" -> "Study 2" in the paper (text only, not numbers)."""
import re
import sys
from pathlib import Path

p = Path(sys.argv[1])
t = p.read_text(encoding="utf-8")
n0 = len(re.findall(r"Study(~|\s)2\.[23]", t))
t = re.sub(r"Study(~|\s)2\.2", r"Study\g<1>1", t)
t = re.sub(r"Study(~|\s)2\.3", r"Study\g<1>2", t)
p.write_text(t, encoding="utf-8", newline="\n")
print(p.name, "replaced", n0)
print("left (2.2/2.3 not part of a number):", re.findall(r".{25}(?<![\d.])2\.[23](?![\d]).{10}", t))
