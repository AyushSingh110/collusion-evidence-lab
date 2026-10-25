"""Task 21 copy of scratch/view_checks_t12.py for the REPLICATION views (paths changed; no split, so C-mismatch is
checked within type across the whole set). Original docstring follows.

Task 12 §5 (no model calls): sizes / estimated tokens of all rendered dataset views, C-length and C-mismatch checks,
and a grep-style RQ0.3 check that no view contains setup text, a game id, a variant name or label metadata.

  PYTHONIOENCODING=utf-8 conda run --no-capture-output -n collusion-lab python -B scratch/view_checks_t12.py
"""
import csv
import json
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.clean.leaks import scan_for_leaks  # noqa: E402
from core.config import CONFIGS, REPO_ROOT  # noqa: E402
from study_2_2_views.monitor import PROMPTS, load_config, system_prompt  # noqa: E402

VIEWS = REPO_ROOT / "data" / "replication" / "views"
man = json.loads((VIEWS / "manifest.json").read_text(encoding="utf-8"))
labels = {r["game_id"]: r for r in csv.DictReader(open(REPO_ROOT / "data" / "replication" / "labels.csv", encoding="utf-8"))}
split = None  # task 21: no split (replication prereg section 2)
which = {g: "unsplit" for g in labels}
setup = json.loads((CONFIGS / "monitor" / "setup_texts.json").read_text(encoding="utf-8"))
cfgs = {name: load_config(manifest=PROMPTS[name]) for name in ("monitor_v1", "monitor_v3_pairs")}

# sizes
by_view = defaultdict(list)
for f in man["files"]:
    by_view[f["view"]].append(f)
print("| view | n | chars min / mean / max | est. tokens view max | est. tokens + v1 sys max | + v3_pairs sys max | "
      ">= 4096 (v1) | >= 4096 (v3) |")
for v, fs in by_view.items():
    ch = [f["chars"] for f in fs]
    s1 = len(system_prompt(cfgs["monitor_v1"], v))
    s3 = len(system_prompt(cfgs["monitor_v3_pairs"], v))
    print(f"| {v} | {len(ch)} | {min(ch)} / {st.mean(ch):.0f} / {max(ch)} | {max(ch) / 4:.0f} | {(max(ch) + s1) / 4:.0f} | "
          f"{(max(ch) + s3) / 4:.0f} | {sum((c + s1) / 4 >= 4096 for c in ch)} | {sum((c + s3) / 4 >= 4096 for c in ch)} |")

# C-length
cl = [f["info"] for f in by_view["C-length"]]
print("\nC-length: within ±5%:", sum(1 for i in cl if i.get("within_5pct")), "/", len(cl), "; unchanged (V3 shorter):",
      sum(1 for i in cl if i.get("unchanged")), "; max |dev| %:",
      round(max(abs(i["chars"] - i["target"]) / i["target"] * 100 for i in cl), 2))
# C-mismatch
bad = []
for f in by_view["C-mismatch"]:
    g, p = f["game_id"], f["info"]["partner"]
    if g == p or labels[g]["episode_type"] != labels[p]["episode_type"] or which[g] != which[p]:
        bad.append((g, p))
partners = [f["info"]["partner"] for f in by_view["C-mismatch"]]
print("C-mismatch:", len(by_view["C-mismatch"]), "files; self/other-type/other-split pairs:", bad,
      "; partners distinct:", len(set(partners)) == len(partners))

# RQ0.3 grep-style check over every rendered file
gids = list(labels)
variants = {r["variant"] for r in labels.values()} | {"collusion_v3_hint", "collusion_v4_secrecy", "alliance_v"}
meta_re = re.compile(r"episode|collusion_v|placebo|persona_v|incentive_4b|focal pair|PRIVATE NOTE|only you can see this",
                     re.I)
problems = defaultdict(list)
for f in man["files"]:
    text = (VIEWS / f["path"]).read_text(encoding="utf-8")
    for g in gids:
        if g in text:
            problems["game_id"].append((f["path"], g))
    for v in variants:
        if v in text:
            problems["variant"].append((f["path"], v))
    m = meta_re.search(text)
    if m:
        problems["meta_term"].append((f["path"], m.group(0)))
    copies = [h for h in scan_for_leaks(text, setup) if h["kind"] == "copy8"]
    if copies:
        problems["setup_copy8"].append((f["path"], copies[0]["match"]))
print("\nRQ0.3 grep check over", len(man["files"]), "files:",
      {k: len(v) for k, v in problems.items()} or "no game id, variant name, label/type term, header phrase or 8-word "
                                                    "setup copy in any view")
for k, v in problems.items():
    print("  ", k, v[:5])
flags = [json.loads(x) for x in (REPO_ROOT / "data" / "replication" / "clean" / "leak_flags.jsonl").read_text(encoding="utf-8").splitlines()]
print("flag side file rows:", len(flags), "| fields:", sorted(set().union(*[set(x) for x in flags])) if flags else [])
print("banned-word flags (kept in text by Amendment 2):",
      sorted({(x["match"], x["where"]) for x in flags if x["kind"] == "banned"}))
