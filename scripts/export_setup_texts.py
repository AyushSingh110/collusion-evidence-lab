"""Write configs/monitor/setup_texts.json: every setup text agents could echo, for the cleaner's leak scan.

Contents (a JSON list of strings, as render_views.py --setup-texts expects):
  - every addendum file listed in configs/prompts/manifest.json (current v3 and history v2/v1), with {P}
    filled by each agent letter (files without {P} appear once);
  - the private-channel prompts and the brevity line (exact files used by the generator);
  - the fixed text of the Type 4b private history line and the Type 1 private-channel history line.

  conda run -n collusion-lab python scripts/export_setup_texts.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import CONFIGS, atomic_write_text  # noqa: E402
from core.generate import prompts as P  # noqa: E402
from core.generate.elfarol import AGENTS  # noqa: E402

OUT = CONFIGS / "monitor" / "setup_texts.json"
ADDENDUM_PREFIXES = ("alliance_", "placebo_", "persona_", "incentive_", "collusion_hint_")
OTHER_FILES = ("channel_A_v1.txt", "channel_B_v1.txt", "brevity_v1.txt")
PRIVATE_LINES = ("PRIVATE (only you see this) - your real payoffs under your own situation:",
                 "PRIVATE (only you and your partner see this) - private messages in round")


def setup_texts() -> list[str]:
    files = sorted(n for n in P.load_manifest()["sha256"] if n.startswith(ADDENDUM_PREFIXES))
    out: list[str] = []
    for name in files:
        text = P.read_prompt(name)
        fills = [text.replace("{P}", a) for a in AGENTS] if "{P}" in text else [text]
        out += [t for t in fills if t not in out]
    out += [P.read_prompt(n) for n in OTHER_FILES]
    out += list(PRIVATE_LINES)
    return out


def main(argv=None) -> int:
    texts = setup_texts()
    atomic_write_text(OUT, json.dumps(texts, indent=1, ensure_ascii=False) + "\n")
    print(f"wrote {OUT}: {len(texts)} setup texts")
    return 0


if __name__ == "__main__":
    sys.exit(main())
