import copy

import pytest

from core.schema import GameRecord, LLMResult, validate_game
from tests.conftest import valid_record


def test_valid_fixture_has_no_errors():
    assert validate_game(valid_record()) == []


def test_record_roundtrips_through_dataclass():
    rec = valid_record()
    assert validate_game(GameRecord.from_dict(rec).to_dict()) == []


def _mutate(fn):
    rec = copy.deepcopy(valid_record())
    fn(rec)
    return validate_game(rec)


@pytest.mark.parametrize("name,fn,needle", [
    ("bad game id", lambda r: r.update(game_id="game-1"), "game_id"),
    ("missing stage3 agent", lambda r: r["rounds"][0]["stage3"].pop("Z"), "stage3"),
    ("None action marked parse_ok", lambda r: r["rounds"][1]["stage3"]["Q"].update(parse_ok=True), "parse_ok"),
    ("failure without failures[] entry", lambda r: r.update(failures=[]), "failures[]"),
    ("imputed flag missing on failure", lambda r: r["rounds"][1]["stage3"]["Q"].update(imputed=False), "imputed"),
    ("round count mismatch", lambda r: r["rounds"].pop(), "n_rounds"),
    ("invalid action", lambda r: r["rounds"][0]["stage1"]["J"].update(intended_action="MAYBE"), "invalid action"),
    ("n_go inconsistent", lambda r: r["rounds"][0]["outcome"].update(n_go=3), "n_go"),
    ("focal pair not distinct", lambda r: r["config"].update(focal_pair=["M", "M"]), "focal_pair"),
    ("channel in non-type-1 game", lambda r: r["config"].update(episode_type=2), "private channel"),
    ("stage2 speaker missing", lambda r: r["rounds"][0]["stage2"].pop(), "stage2"),
])
def test_planted_errors_are_caught(name, fn, needle):
    errs = _mutate(fn)
    assert errs and any(needle in e for e in errs), (name, errs)


def test_llm_result_meta():
    r = LLMResult("k", False, "{}", {}, None, 10, 5, {}, "stop", 1.0, False, "qwen2.5:7b", "d", "0.40.3", "A",
                  "2026-10-24T00:00:00Z", None, [{"attempt": 1, "ok": True}])
    m = r.meta("stage1")
    assert m.cache_key == "k" and m.purpose == "stage1" and m.attempts == 1
