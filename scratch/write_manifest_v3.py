"""Task 06a: rewrite configs/prompts/manifest.json (hashes of all files + measured qwen2.5:7b token counts incl. v3)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.generate.prompts import write_manifest
doc = write_manifest({"alliance_v2.txt": 101, "placebo_v2.txt": 107, "persona_v1.txt": 84, "incentive_4b_v1.txt": 83,
                      "collusion_hint_v1.txt": 29, "alliance_v3.txt": 130, "placebo_v3.txt": 139})
print(doc)
