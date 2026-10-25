"""Task 15C (RQ9): build configs/monitor/manifest_v3_pairs_ctx16k_granite.json from the frozen ctx16k manifest.

  conda run -n collusion-lab python -B scratch/p15c_make_config.py

Only model, model_digest (added; the pinned digest from configs/pins.json), prompt_version and the note change.
Asserts that the JSON writer reproduces the frozen file byte for byte first, so the copy differs only in those fields.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import CONFIGS, load_pins, text_file_sha256  # noqa: E402

SRC = CONFIGS / "monitor" / "manifest_v3_pairs_ctx16k.json"
DST = CONFIGS / "monitor" / "manifest_v3_pairs_ctx16k_granite.json"
MODEL = "granite3.3:8b"


def dump(d):
    return json.dumps(d, indent=2, ensure_ascii=False) + "\n"


assert text_file_sha256(SRC) == "81e88222707e7771740f470fb04ee2463a7cd5e9aae1ba805b684fb4bbc07311"
src_text = SRC.read_text(encoding="utf-8").replace("\r\n", "\n")
man = json.loads(src_text)
assert dump(man) == src_text, "writer does not reproduce the frozen manifest byte for byte"
if DST.exists():
    raise SystemExit(f"{DST} exists; not overwritten")

new = {}
for k, v in man.items():
    if k == "_note":
        v = "RQ9: identical to the frozen monitor_v3_pairs_ctx16k except the model"
    elif k == "prompt_version":
        v = "monitor_v3_pairs_ctx16k_granite"
    new[k] = v
    if k == "model":
        new[k] = MODEL
        new["model_digest"] = load_pins()["models"][MODEL]["digest"]
DST.write_text(dump(new), encoding="utf-8", newline="\n")
print(f"{DST}  LF sha256 {text_file_sha256(DST)}")
