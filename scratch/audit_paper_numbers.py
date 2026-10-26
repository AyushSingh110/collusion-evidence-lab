"""Task 25D: check that every number in writeup/paper.tex / paper.md appears verbatim in the source files.

Numbers checked: decimals (0.900, -0.059, 12.5, 2.2e-16 is skipped), k/n counts, percentages.
Sources: the write-up files, README, prereg files, and report 10 (two-rater table). Prints numbers not found.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCES = [*(ROOT / "writeup").glob("*.md"), ROOT / "writeup" / "figures" / "captions.md", ROOT / "README.md",
           *(ROOT / "configs").glob("prereg_*.md"), ROOT / "notes" / "reports" / "10_rq01_status.md"]
src = "\n".join(p.read_text(encoding="utf-8") for p in SOURCES if p.name not in ("paper.md",))
src = src.replace("−", "-")

paper = Path(sys.argv[1]).read_text(encoding="utf-8")
paper = re.sub(r"(?m)^\s*%.*$", "", paper)                 # tex comment lines
paper = re.sub(r"(?<!\\)%.*", "", paper) if sys.argv[1].endswith(".tex") else re.sub(r"<!--.*?-->", "", paper, flags=re.S)
paper = paper.replace("$-$", "-").replace("−", "-")
paper = re.sub(r"\\begin\{verbatim\}.*?\\end\{verbatim\}|```.*?```", "", paper, flags=re.S)

missing = []
for m in sorted(set(re.findall(r"(?<![\w.])-?\+?\d+\.\d+(?![\w.])", paper))):
    if m.lstrip("+") not in src and m not in src:
        missing.append(m)
for m in sorted(set(re.findall(r"\b\d+/\d+\b", paper))):
    if m not in src:
        missing.append(m)
print(f"{sys.argv[1]}: {len(missing)} numbers not found verbatim in sources:", missing)
