"""Task 14 §0 preconditions (read-only, no model calls): frozen file fields vs manifest / pins, and proof that no
test game has been scored by any monitor run so far.

  conda run -n collusion-lab python -B scratch/p8_preconditions.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import REPO_ROOT, load_pins, text_file_sha256  # noqa: E402
from study_2_2_views.monitor import PROMPTS, load_config  # noqa: E402

fz = json.load(open(REPO_ROOT / "configs/frozen/monitor_frozen.json", encoding="utf-8"))
man_path = REPO_ROOT / fz["format_manifest"]
cfg = load_config(manifest=PROMPTS[fz["format_choice"]])
pins = load_pins()
checks = {
    "format_choice": fz["format_choice"],
    "manifest_file_sha256 (disk) == frozen.format_manifest_file_sha256":
        text_file_sha256(man_path) == fz["format_manifest_file_sha256"],
    "manifest_file_sha256 (disk) == frozen.monitor_manifest_sha256": text_file_sha256(man_path) == fz["monitor_manifest_sha256"],
    "template_sha256 == frozen": cfg.template_sha256 == fz["template_sha256"],
    "num_ctx manifest == frozen (16384)": cfg.num_ctx == fz["num_ctx"] == 16384,
    "model digest pins == frozen": pins["models"][cfg.model]["digest"] == fz["model_digest"],
    "ollama pin == frozen": pins["ollama_version"] == fz["ollama_version"],
    "prompt_versions": fz["prompt_versions"],
    "thresholds": {v: x["threshold"] for v, x in fz["per_view"].items()},
    "rq03_pass": fz["rq03_c_shuffled"]["pass"],
}
test = set(json.load(open(REPO_ROOT / "data/split.json", encoding="utf-8"))["test"])
hits = []
for f in (REPO_ROOT / "runs").rglob("monitor.jsonl"):
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.strip() and json.loads(line)["game_id"] in test:
            hits.append(str(f))
            break
for f in (REPO_ROOT / "runs").rglob("errors.jsonl"):
    for line in f.read_text(encoding="utf-8").splitlines():
        if line.strip() and json.loads(line).get("game_id") in test:
            hits.append(str(f))
            break
checks["monitor outputs containing a test game"] = hits
checks["test run dir runs/test_p8 exists"] = (REPO_ROOT / "runs/test_p8").exists()
print(json.dumps(checks, indent=1))
