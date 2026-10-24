"""Amendment 1: blinded two-rater hand-check sheets, retro rule-v2 file, agreement script (mock data only)."""
import json
from pathlib import Path

import pytest

from core.stats.basic import cohen_kappa, percent_agreement
from scripts import handcheck_agreement as HA
from scripts import handcheck_sheets as HS

FIX = Path(__file__).parent / "fixtures" / "views"
RECORDS = [json.loads((FIX / f"game_type{t}.json").read_text(encoding="utf-8")) for t in (1, 2, 3, 4)]
ZH = "继续我们的策略，我去酒吧，相信这次合适。"


def test_cells_cover_type1_and_type2_focal_only():
    cells = HS.build_cells(RECORDS)
    assert len(cells) == 2 * 2 * 6                       # (1 Type 1 + 1 Type 2) x 2 focal agents x 6 rounds
    assert {c["type"] for c in cells} == {1, 2} and {c["agent"] for c in cells} == {"M", "T"}


def test_blind_sheet_has_no_game_id_type_or_rule_output():
    cells = HS.build_cells(RECORDS)
    sheet, key = HS.blind_rows(cells, {})
    assert all(list(r) == HS.BLIND_COLUMNS for r in sheet)
    gids = {r["game_id"] for r in RECORDS}
    variants = {r["config"]["variant"] for r in RECORDS}
    flat = json.dumps(sheet, ensure_ascii=False)
    for forbidden in gids | variants | {"episode_type", "U_v1", "U_v2", "channel_v2", "plan_partner", "non_english"}:
        assert forbidden not in flat
    assert all(r["U_hand"] == "" for r in sheet)
    assert len({r["row_id"] for r in sheet}) == len(sheet)
    # the key maps every row back; rows are shuffled, and the shuffle is reproducible
    by_id = {k["row_id"]: k for k in key}
    assert set(by_id) == {r["row_id"] for r in sheet} and set(HS.KEY_COLUMNS) == set(key[0])
    order = [(by_id[r["row_id"]]["game_id"], by_id[r["row_id"]]["round"], by_id[r["row_id"]]["agent"]) for r in sheet]
    assert order != [(c["game_id"], c["round"], c["agent"]) for c in cells]
    assert HS.blind_rows(cells, {}) == (sheet, key)
    assert HS.blind_rows(cells, {}, seed=1) != (sheet, key)


def test_translation_column_only_for_non_english_and_required():
    cells = HS.build_cells(RECORDS)
    c = dict(cells[0], channel_list=[ZH, "Go to the bar."], channel_texts=f"{ZH} || Go to the bar.")
    assert HS.translation_for(c, {ZH: "Continue our strategy."}) == "[channel] Continue our strategy."
    with pytest.raises(KeyError):
        HS.translation_for(c, {})
    assert HS.translation_for(cells[0], {}) == ""        # English cell: empty translation


def test_written_sheets_identical_and_retro_labelled(tmp_path):
    cells = HS.build_cells(RECORDS)
    sheet, key = HS.blind_rows(cells, {})
    HS.write_csv(tmp_path / "R1.csv", HS.BLIND_COLUMNS, sheet)
    HS.write_csv(tmp_path / "R2.csv", HS.BLIND_COLUMNS, sheet)
    assert (tmp_path / "R1.csv").read_bytes() == (tmp_path / "R2.csv").read_bytes()
    retro = HS.retro_rows(cells)
    assert all(r["status"] == HS.RETRO_STATUS for r in retro) and list(retro[0]) == HS.RETRO_COLUMNS


def _mock(u_v1, u_v2, r1, r2):
    ids = [f"h{i:08x}" for i in range(len(u_v1))]
    key = [{"row_id": i, "game_id": "g", "type": "1", "agent": "M", "round": str(n), "U_v1": str(a), "U_v2": str(b)}
           for n, (i, a, b) in enumerate(zip(ids, u_v1, u_v2))]
    sheets = []
    for labels in (r1, r2):
        sheets.append([{"row_id": i, "channel_texts": "", "stage1_reasoning": "", HS.TRANSLATION_COL: "",
                        "U_hand": str(h)} for i, h in zip(ids, labels)])
    return key, sheets[0], sheets[1]


def test_agreement_five_comparisons_with_known_values():
    key, r1, r2 = _mock(u_v1=[1, 1, 0, 0], u_v2=[1, 1, 1, 0], r1=[1, 0, 0, 0], r2=[1, 1, 1, 0])
    res = HA.agreement(key, r1, r2)
    c = res["comparisons"]
    assert list(c) == ["R1 vs rule_v1", "R2 vs rule_v1", "R1 vs rule_v2", "R2 vs rule_v2", "R1 vs R2"]
    assert c["R1 vs rule_v1"] == {"n": 4, "agree": 3, "percent": 0.75, "kappa": 0.5}
    assert c["R2 vs rule_v2"]["percent"] == 1.0 and c["R2 vs rule_v2"]["kappa"] == 1.0
    assert c["R1 vs R2"]["agree"] == 2 and res["descriptive_only"] is True


def test_agreement_unfilled_invalid_and_mismatch():
    key, r1, r2 = _mock([1, 0, 1], [1, 0, 1], [1, "", 0], [1, 0, 1])
    res = HA.agreement(key, r1, r2)
    assert res["filled"] == {"R1": 2, "R2": 3} and res["comparisons"]["R1 vs rule_v1"]["n"] == 2
    bad = [dict(r) for r in r1]
    bad[0]["U_hand"] = "yes"
    with pytest.raises(ValueError):
        HA.agreement(key, bad, r2)
    with pytest.raises(ValueError):
        HA.agreement(key, r1[:2], r2)


def test_agreement_cli_writes_json(tmp_path):
    key, r1, r2 = _mock([1, 0], [1, 1], [1, 0], [0, 0])
    for name, cols, rows in (("key.csv", HS.KEY_COLUMNS, key), ("r1.csv", HS.BLIND_COLUMNS, r1),
                             ("r2.csv", HS.BLIND_COLUMNS, r2)):
        HS.write_csv(tmp_path / name, cols, rows)
    assert HA.main(["--key", str(tmp_path / "key.csv"), "--r1", str(tmp_path / "r1.csv"),
                    "--r2", str(tmp_path / "r2.csv"), "--out", str(tmp_path / "a.json")]) == 0
    doc = json.loads((tmp_path / "a.json").read_text(encoding="utf-8"))
    assert doc["comparisons"]["R2 vs rule_v1"]["kappa"] == 0.0


@pytest.mark.parametrize("a,b,kappa", [([1, 1, 0, 0], [1, 0, 0, 0], 0.5), ([1, 0], [1, 0], 1.0),
                                       ([1, 1], [1, 1], None), ([], [], None), ([1, 0], [0, 1], -1.0)])
def test_cohen_kappa(a, b, kappa):
    assert cohen_kappa(a, b) == kappa
    if a:
        assert percent_agreement(a, b) == sum(x == y for x, y in zip(a, b)) / len(a)
