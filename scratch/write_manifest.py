"""Task 04 helper: (re)write configs/prompts/manifest.json. Token counts are the report 01 measurements (qwen2.5:7b)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.generate.prompts import write_manifest
doc = write_manifest({"alliance_v2.txt": 101, "placebo_v2.txt": 107, "persona_v1.txt": 84,
                      "incentive_4b_v1.txt": 83, "collusion_hint_v1.txt": 29})
for k, v in doc["sha256"].items():
    print(k, v[:16])
