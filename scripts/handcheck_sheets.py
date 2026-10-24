"""Amendment 1: retro-application of uptake rule v2 to pilot 1 + blinded two-rater hand-check sheets.

  conda run -n collusion-lab python scripts/handcheck_sheets.py --raw-dir data/raw/pilot \
      --translations runs/pilot/translations_en.json --out runs/pilot

Writes (no model calls):
  uptake_v2_retro.csv        rule v1 and v2 per cell, DESCRIPTIVE ONLY (not the gate; pilot 1 = development data)
  handcheck_blind_R1.csv     row_id, channel_texts, stage1_reasoning, translation_en, U_hand (no game id, no type,
  handcheck_blind_R2.csv     no rule output); identical content, rows shuffled with a fixed seed
  handcheck_key.csv          row_id -> game_id, type, agent, round, U_v1, U_v2 (keep away from the raters)
Cells: the 2 focal agents x every round of each Type 1 and Type 2 game (as the frozen hand-check).
"""
from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from core.config import REPO_ROOT  # noqa: E402
from core.evidence import rq01  # noqa: E402

SEED = 20261024
TRANSLATION_COL = "translation_en (assistant translation)"
BLIND_COLUMNS = ["row_id", "channel_texts", "stage1_reasoning", TRANSLATION_COL, "U_hand"]
KEY_COLUMNS = ["row_id", "game_id", "type", "agent", "round", "U_v1", "U_v2"]
RETRO_COLUMNS = ["game_id", "type", "agent", "round", "channel_joint_v1", "channel_v2", "plan_partner",
                 "non_english", "U_v1", "U_v2", "status"]
RETRO_STATUS = "descriptive_retro_not_gate"


def build_cells(records: list[dict]) -> list[dict]:
    """One cell per focal agent per round of every Type 1 / Type 2 game, with rule v1 and v2 outputs."""
    cells = []
    for rec in sorted(records, key=lambda r: r["game_id"]):
        g, lab = rq01.from_record(rec), rq01.labels_from_record(rec)
        if lab.episode_type not in (1, 2):
            continue
        focal = rq01.norm_pair(lab.focal_pair, g.agents)
        v1 = {(c["round"], c["agent"]): c for c in rq01.uptake_cells(g, focal)}
        v2 = {(c["round"], c["agent"]): c for c in rq01.uptake_cells_v2(g, focal)}
        for r in g.rounds:
            for a in focal:
                ch = [c.get("text") or "" for c in r.channel if c.get("from") == a]
                c1, c2 = v1[(r.round, a)], v2[(r.round, a)]
                cells.append({"game_id": g.game_id, "type": lab.episode_type, "agent": a, "round": r.round,
                              "channel_list": ch, "channel_texts": " || ".join(ch),
                              "stage1_reasoning": r.stage1_reasoning.get(a) or "",
                              "channel_joint_v1": int(c1["channel_joint"]), "channel_v2": int(c2["channel_v2"]),
                              "plan_partner": int(c2["plan_partner"]), "non_english": int(c2["non_english"]),
                              "U_v1": int(c1["U"]), "U_v2": int(c2["U"])})
    return cells


def retro_rows(cells: list[dict]) -> list[dict]:
    return [{**{k: c[k] for k in RETRO_COLUMNS if k != "status"}, "status": RETRO_STATUS} for c in cells]


def translation_for(cell: dict, translations: dict[str, str]) -> str:
    """English translation of every non-English text in the cell ('' if all texts are English)."""
    parts = []
    for label, texts in (("channel", cell["channel_list"]), ("plan", [cell["stage1_reasoning"]])):
        for t in texts:
            if t and rq01.is_non_english(t):
                if t not in translations:
                    raise KeyError(f"no translation for a non-English text in {cell['game_id']} R{cell['round']} "
                                   f"{cell['agent']}: {t[:40]}")
                parts.append(f"[{label}] {translations[t]}")
    return " || ".join(parts)


def blind_rows(cells: list[dict], translations: dict[str, str], seed: int = SEED) -> tuple[list[dict], list[dict]]:
    """Shuffled blinded rows (no game id, type or rule output) and the separate key."""
    rng = random.Random(seed)
    order = list(range(len(cells)))
    rng.shuffle(order)
    ids: set[str] = set()
    sheet, key = [], []
    for i in order:
        c = cells[i]
        rid = f"h{rng.getrandbits(32):08x}"
        while rid in ids:
            rid = f"h{rng.getrandbits(32):08x}"
        ids.add(rid)
        sheet.append({"row_id": rid, "channel_texts": c["channel_texts"], "stage1_reasoning": c["stage1_reasoning"],
                      TRANSLATION_COL: translation_for(c, translations), "U_hand": ""})
        key.append({"row_id": rid, "game_id": c["game_id"], "type": c["type"], "agent": c["agent"],
                    "round": c["round"], "U_v1": c["U_v1"], "U_v2": c["U_v2"]})
    return sheet, key


def write_csv(path: Path, columns: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=columns)
        w.writeheader()
        w.writerows(rows)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raw-dir", type=Path, default=REPO_ROOT / "data" / "raw" / "pilot")
    ap.add_argument("--translations", type=Path, default=REPO_ROOT / "runs" / "pilot" / "translations_en.json")
    ap.add_argument("--out", type=Path, default=REPO_ROOT / "runs" / "pilot")
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(argv)
    records = [json.loads(p.read_text(encoding="utf-8")) for p in sorted(a.raw_dir.glob("*.json"))
               if not p.name.endswith(".partial.json")]
    translations = json.loads(a.translations.read_text(encoding="utf-8"))["translations"]
    cells = build_cells(records)
    sheet, key = blind_rows(cells, translations, a.seed)
    write_csv(a.out / "uptake_v2_retro.csv", RETRO_COLUMNS, retro_rows(cells))
    write_csv(a.out / "handcheck_blind_R1.csv", BLIND_COLUMNS, sheet)
    write_csv(a.out / "handcheck_blind_R2.csv", BLIND_COLUMNS, sheet)
    write_csv(a.out / "handcheck_key.csv", KEY_COLUMNS, key)
    n_tr = sum(1 for r in sheet if r[TRANSLATION_COL])
    print(f"{len(cells)} cells from {len({c['game_id'] for c in cells})} games; {n_tr} rows with an assistant translation; "
          f"rule v1 U=1: {sum(c['U_v1'] for c in cells)}, rule v2 U=1: {sum(c['U_v2'] for c in cells)}, "
          f"non-English cells: {sum(c['non_english'] for c in cells)}. Wrote {a.out}/uptake_v2_retro.csv, "
          f"handcheck_blind_R1.csv, handcheck_blind_R2.csv, handcheck_key.csv")
    return 0


if __name__ == "__main__":
    sys.exit(main())
