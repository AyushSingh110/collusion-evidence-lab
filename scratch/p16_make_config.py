"""Task 16 (Follow-up 1, prereg 496fc28): build configs/monitor/monitor_v3_pairs_rot.txt and
manifest_v3_pairs_ctx16k_rot.json from the frozen v3_pairs files. The template is a byte copy except that the fixed
pair list in the reply example line becomes {pair_scores_example}. No model calls.

  conda run -n collusion-lab python -B scratch/p16_make_config.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.config import CONFIGS, canonical_json, text_file_sha256  # noqa: E402

D = CONFIGS / "monitor"
src = (D / "monitor_v3_pairs.txt").read_bytes()
man = json.loads((D / "manifest_v3_pairs_ctx16k.json").read_text(encoding="utf-8"))
assert text_file_sha256(D / "monitor_v3_pairs.txt") == man["template_sha256"]
fixed = ", ".join(f'"{p}": <0-100>' for p in man["pair_order"]).encode("utf-8")
assert src.count(fixed) == 1, "fixed pair list not found exactly once"
(D / "monitor_v3_pairs_rot.txt").write_bytes(src.replace(fixed, b"{pair_scores_example}"))

rot = dict(man)
rot["_note"] = ("Task 16 Follow-up 1 (prereg configs/prereg_followup1_pair_order.md, commit 496fc28): copy of "
                "manifest_v3_pairs_ctx16k.json; ONLY the pair order changes. The template's reply example line has "
                "{pair_scores_example}, filled per call with the 10 pairs in a permuted order; the pair_scores schema "
                "properties/required use the same order. pair_order below stays canonical (mapping back).")
rot["prompt_version"] = "monitor_v3_pairs_ctx16k_rot"
rot["template"] = "monitor_v3_pairs_rot.txt"
rot["template_sha256"] = text_file_sha256(D / "monitor_v3_pairs_rot.txt")
rot["pair_order_mode"] = "per_call_permutation"
rot["pair_order_rule"] = ('order = list(pair_order); random.Random(int(sha256(f"{game_id}|{view}|followup1")'
                          '.hexdigest(), 16)).shuffle(order)')
rot["pair_order_salt"] = "followup1"
(D / "manifest_v3_pairs_ctx16k_rot.json").write_text(json.dumps(rot, indent=2) + "\n", encoding="utf-8")
print("template sha256", rot["template_sha256"])
print("manifest sha256 (canonical)", __import__("hashlib").sha256(canonical_json(rot).encode()).hexdigest())
