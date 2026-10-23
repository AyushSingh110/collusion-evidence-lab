"""Task 04 helper: write the measured v2/v1 addenda from prompts_draft.py into configs/prompts/ verbatim."""
from pathlib import Path
import prompts_draft as P
out = Path(__file__).resolve().parents[1] / "configs" / "prompts"
files = {"alliance_v2.txt": P.ADDENDUM_V2["alliance"], "placebo_v2.txt": P.ADDENDUM_V2["placebo"],
         "persona_v1.txt": P.ADDENDUM["persona"], "incentive_4b_v1.txt": P.ADDENDUM["incentive"],
         "collusion_hint_v1.txt": P.COLLUSION_HINT}
for name, text in files.items():
    (out / name).write_text(text + "\n", encoding="utf-8", newline="\n")
    print(name, len(text))
