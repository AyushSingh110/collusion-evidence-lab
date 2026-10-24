"""Task 13 lead decision (a): new monitor manifests with num_ctx 16384, SAME templates; old manifests untouched.

  conda run -n collusion-lab python -B scratch/make_ctx16k_manifests.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import CONFIGS, atomic_write_text, read_text_lf  # noqa: E402

D = CONFIGS / "monitor"
for src, dst, version in (("manifest.json", "manifest_v1_ctx16k.json", "monitor_v1_ctx16k"),
                          ("manifest_v3_pairs.json", "manifest_v3_pairs_ctx16k.json", "monitor_v3_pairs_ctx16k")):
    man = json.loads(read_text_lf(D / src))
    old_ctx, old_version = man["num_ctx"], man["prompt_version"]
    man["prompt_version"] = version
    man["num_ctx"] = 16384
    man["_note"] = (f"Task 13 lead decision (a), 2026-10-24: copy of {src} ({old_version}) with num_ctx 16384 instead of "
                    f"{old_ctx}; same template and template_sha256, everything else unchanged. Reason: all 48 dataset V5 "
                    "views exceed num_ctx/2 = 4096 estimated tokens (report 12 §7). The truncation guard stays at "
                    "num_ctx/2 (now 8192). One condition for all views and formats.")
    if (D / dst).exists():
        sys.exit(f"{dst} exists; refusing to overwrite")
    atomic_write_text(D / dst, json.dumps(man, indent=2, ensure_ascii=False) + "\n")
    print("wrote", dst, "from", src, "num_ctx", old_ctx, "->", man["num_ctx"])
