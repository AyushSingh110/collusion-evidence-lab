"""Task 06a Step 0: compare stub vs real scanner hits on the 4 P5 fixtures."""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.clean import cleaner
from core.clean.leaks import scan_for_leaks
fx = ROOT / "tests" / "fixtures" / "views"
setup = json.loads((fx / "setup_texts.json").read_text(encoding="utf-8"))
for t in (1, 2, 3, 4):
    rec = json.loads((fx / f"game_type{t}.json").read_text(encoding="utf-8"))
    for name, scan in (("stub", cleaner.stub_scan_for_leaks), ("real", scan_for_leaks)):
        _, _, hits = cleaner.clean_game(rec, setup, scanner=scan)
        for h in hits:
            if h["kind"] == "leak":
                print(t, name, h["where"], h["round"], h["agent"], [(x["kind"], x["match"]) for x in h["scanner_hits"]], "removed:", len(h["removed"]))
