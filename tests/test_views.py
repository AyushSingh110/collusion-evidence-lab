"""Tests for study_2_2_views.views (V1-V5 and the three controls)."""
import hashlib
import json
import os
import re
from pathlib import Path

import pytest

from core.clean.cleaner import clean_game
from study_2_2_views import views as V
from study_2_2_views.views import VIEWS, c_length, consistency_score, mismatch_pairs, render_all, render_view

FIX = Path(__file__).parent / "fixtures" / "views"
GOLDEN = FIX / "golden"
PLANTS = json.loads((FIX / "plants.json").read_text(encoding="utf-8"))
SETUP = json.loads((FIX / "setup_texts.json").read_text(encoding="utf-8"))
TYPES = (1, 2, 3, 4)


def _load(t):
    return json.loads((FIX / f"game_type{t}.json").read_text(encoding="utf-8"))


CLEAN = {t: clean_game(_load(t), SETUP)[:2] for t in TYPES}
POOL = [CLEAN[t][0] for t in TYPES]


def render(t, view):
    c, p = CLEAN[t]
    partner = CLEAN[2 if t != 2 else 1][0]
    return render_view(c, view, private=p, partner=partner, pool=POOL, seed=0)


@pytest.mark.parametrize("view", VIEWS)
def test_golden_type1(view):
    """Golden files for every view and control on the Type 1 fixture. Regenerate: UPDATE_GOLDEN=1 pytest."""
    path = GOLDEN / f"type1_{view}.txt"
    text = render(1, view)
    if os.environ.get("UPDATE_GOLDEN") == "1":
        path.parent.mkdir(exist_ok=True)
        path.write_text(text, encoding="utf-8", newline="\n")
    assert text == path.read_text(encoding="utf-8").replace("\r\n", "\n")


@pytest.mark.parametrize("t", TYPES)
@pytest.mark.parametrize("view", VIEWS)
def test_deterministic(t, view):
    assert render(t, view).encode("utf-8") == render(t, view).encode("utf-8")


def _record_texts(rec):
    """Texts that exist in the record but must never reach a non-oracle view."""
    out = []
    for R in rec["rounds"]:
        out += [c["text"] for c in R["channel"]]
        out += [R["history_block"]]
        out += [v["reasoning"] for v in R["stage1"].values() if v["reasoning"]]
        out += [v["reasoning"] for v in R["stage3"].values() if v["reasoning"]]
    out += [f["raw_excerpt"] for f in rec["failures"]]
    out += list(rec["config"]["addenda"].values())
    return out


@pytest.mark.parametrize("t", TYPES)
@pytest.mark.parametrize("view", VIEWS)
def test_planted_items_absent_from_every_view(t, view):
    text = render(t, view)
    for name, plant in PLANTS.items():
        assert plant not in text, f"planted {name} in {view} (type {t})"
    for marker in ("Keep this agreement hidden", "experiment", "deposit", "$-8", "-8", "Zebra plan", "HISTORY OF",
                   "RAW-FAILURE", "PRIVATE NOTE"):
        assert marker not in text, f"{marker!r} in {view} (type {t})"
    rec = _load(t)
    for meta in (rec["game_id"], rec["config"]["variant"], "episode", "Type ", "label", "focal"):
        assert meta not in text
    if view != "V5":
        for s in _record_texts(rec):
            assert s not in text


def test_oracle_has_private_plans_but_no_channel():
    text = render(1, "V5")
    assert "Given our agreement with Agent T, we both go" in text   # Stage 1 plan (allowed in V5)
    assert "Final: GO, sticking with my read of round 2." in text   # Stage 3 reasoning
    assert "Zebra plan" not in text and "Agreed, both go, keep it quiet." not in text


@pytest.mark.parametrize("t", TYPES)
def test_c_length_within_5pct_of_v4(t):
    text, info = c_length(CLEAN[t][0])
    target = len(render(t, "V4"))
    assert info["target"] == target
    if info["unchanged"]:
        assert text == render(t, "V3") and len(text) <= target
    else:
        assert abs(len(text) - target) <= 0.05 * target and info["within_5pct"]
    assert all(line in text for line in render(t, "V3").splitlines() if line.startswith(("Final actions", "Payoffs")))


def test_c_length_unchanged_when_v3_shorter():
    text, info = c_length(CLEAN[1][0], target_chars=10 ** 6)
    assert info["unchanged"] and text == render(1, "V3")


def test_mismatch_pairs_derangement_within_type_and_split():
    mapping = {f"g_{i:010x}": (1 + i % 3, "dev" if i % 2 else "test") for i in range(30)}
    mapping["g_lonely0000"] = (4, "dev")
    for seed in (0, 1, 2):
        pairs = mismatch_pairs(mapping, seed)
        assert pairs["g_lonely0000"] is None
        for gid, j in pairs.items():
            if j is not None:
                assert j != gid and mapping[j] == mapping[gid]
        partners = [j for j in pairs.values() if j is not None]
        assert len(partners) == len(set(partners))              # a permutation
    assert mismatch_pairs(mapping, 5) == mismatch_pairs(mapping, 5)


def test_c_mismatch_messages_of_i_actions_of_j():
    c1, c2 = CLEAN[1][0], CLEAN[2][0]
    text = render_view(c1, "C-mismatch", partner=c2)
    assert "I think the bar will be quiet. See you there." in text                  # game 1 message
    assert "Final actions: J GO | M STAY | Q STAY | T STAY | Z STAY" in text         # game 2, round 2 actions
    with pytest.raises(ValueError):
        render_view(c1, "C-mismatch", partner=c1)


def test_c_shuffled_keeps_layout_and_uses_other_games():
    c1 = CLEAN[1][0]
    text = render(1, "C-shuffled")
    lines = [ln for ln in text.splitlines() if " announced " in ln]
    assert len(lines) == sum(len(r.announcements) for r in c1.rounds)
    assert text.count("ROUND ") == c1.n_rounds
    # same speakers in the same order as game 1
    assert [ln.split()[0] for ln in lines] == [a.agent for r in c1.rounds for a in r.announcements]
    # every (stated action, message) comes from another game; game 1's unique message never appears
    donor = {(a.stated_action or "n/a", f'"{a.message}"') for g in POOL if g.game_id != c1.game_id
             for r in g.rounds for a in r.announcements}
    for ln in lines:
        act, msg = ln.split(" announced ", 1)[1].split(":", 1)
        assert (act, msg.strip()) in donor
    assert "I think the bar will be quiet. See you there." not in text
    # each agent's action column equals some agent's column in another game
    rows = [dict(re.findall(r"\b([JMQTZ]) (GO|STAY|n/a)\b", ln)) for ln in text.splitlines()
            if ln.startswith("Final actions")]
    cols = [[row[a] for row in rows] for a in c1.agents]
    donor_cols = {tuple(r.actions[a] or "n/a" for r in g.rounds) for g in POOL if g.game_id != c1.game_id
                  for a in g.agents}
    assert all(tuple(c) in donor_cols for c in cols)


def test_v4_consistency_scale():
    assert [consistency_score(b, 6) for b in (0, 1, 2, 3, 6)] == [0, 1, 3, 5, 10]
    assert consistency_score(2, 20) == 2 and consistency_score(0, 0) is None


def test_v4_mentions_and_quotes():
    text = render(3, "V4")
    assert "Pair M-T: " in text and "M mentions T in 6 msgs, T mentions M in 6 msgs" in text
    assert 'Round 1, M mentions T: "' in text
    assert "(none)" not in text
    assert "MESSAGES IN WHICH A PLAYER MENTIONS ANOTHER PLAYER\n  (none)" in render(1, "V4")


def test_failed_action_shown_as_na_with_note():
    text = render(2, "V2")
    assert "Q n/a" in text and V.NA_NOTE in text
    assert V.NA_NOTE not in render(1, "V2")


def test_render_all_writes_files_and_manifest(tmp_path):
    privates = {CLEAN[t][0].game_id: CLEAN[t][1] for t in TYPES}
    man = render_all(POOL, tmp_path, VIEWS, privates=privates, mapping=None, seed=0)
    assert {s["view"] for s in man["skipped"]} == {"C-mismatch"} and len(man["skipped"]) == 4
    assert len(man["files"]) == 7 * 4
    for f in man["files"]:
        data = (tmp_path / f["path"]).read_bytes()
        assert hashlib.sha256(data).hexdigest() == f["sha256"] and len(data.decode("utf-8")) == f["chars"]
    on_disk = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    assert on_disk == man
    man2 = render_all(POOL, tmp_path / "again", VIEWS, privates=privates, mapping=None, seed=0)
    assert [f["sha256"] for f in man2["files"]] == [f["sha256"] for f in man["files"]]


def test_render_all_c_mismatch_with_mapping(tmp_path):
    mapping = {CLEAN[t][0].game_id: (1, "dev") for t in TYPES}     # pretend same type/split to get partners
    man = render_all(POOL, tmp_path, ["C-mismatch"], mapping=mapping, seed=3)
    assert len(man["files"]) == 4
    assert all(f["info"]["partner"] != f["game_id"] for f in man["files"])
