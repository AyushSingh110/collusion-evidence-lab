"""Tests for core.clean (CleanGame/CleanPrivate types and the whitelist cleaner)."""
import copy
import json
import sys
from pathlib import Path

import pytest

from core.clean import cleaner
from core.clean.cleaner import clean_game, redact, resolve_scanner, standard_payoffs, stub_scan_for_leaks
from core.clean.types import CleanAnnouncement, CleanGame, CleanPrivate

FIX = Path(__file__).parent / "fixtures" / "views"
PLANTS = json.loads((FIX / "plants.json").read_text(encoding="utf-8"))
SETUP = json.loads((FIX / "setup_texts.json").read_text(encoding="utf-8"))


def record(t):
    return json.loads((FIX / f"game_type{t}.json").read_text(encoding="utf-8"))


def cleaned(t, **kw):
    return clean_game(record(t), SETUP, **kw)


GAME_KEYS = {"game_id", "agents", "n_rounds", "rules_text", "rounds", "leak_scan"}
ROUND_KEYS = {"round", "announcements", "actions", "valid", "payoffs_public"}
ANN_KEYS = {"agent", "position", "stated_action", "message"}
PRIV_KEYS, PRIV_ROUND_KEYS = {"game_id", "rounds"}, {"round", "stage1", "stage3"}


@pytest.mark.parametrize("t", [1, 2, 3, 4])
def test_whitelist_property(t):
    c, p, _ = cleaned(t)
    d, pd = c.to_dict(), p.to_dict()
    assert set(d) == GAME_KEYS and set(d["leak_scan"]) == {"hits", "redactions"}
    for r in d["rounds"]:
        assert set(r) == ROUND_KEYS
        assert all(set(a) == ANN_KEYS for a in r["announcements"])
        assert set(r["actions"]) == set(d["agents"]) and set(r["payoffs_public"]) == set(d["agents"])
    assert set(pd) == PRIV_KEYS
    for r in pd["rounds"]:
        assert set(r) == PRIV_ROUND_KEYS
        assert all(set(v) == {"intended_action", "reasoning"} for v in r["stage1"].values())
        assert all(set(v) == {"reasoning"} for v in r["stage3"].values())


def test_types_reject_fields_outside_whitelist():
    c, p, _ = cleaned(1)
    with pytest.raises(AttributeError):
        c.config = {}                                   # __slots__
    with pytest.raises(ValueError):
        CleanGame.from_dict({**c.to_dict(), "labels": "x"})
    bad = c.to_dict()
    bad["rounds"][0]["channel"] = []
    with pytest.raises(ValueError):
        CleanGame.from_dict(bad)
    with pytest.raises(ValueError):
        CleanAnnouncement.from_dict({"agent": "J", "position": 0, "stated_action": "GO", "message": "", "call": "c"})
    assert CleanGame.from_dict(c.to_dict()) == c and CleanPrivate.from_dict(p.to_dict()) == p


def _dump(*objs):
    return json.dumps([o.to_dict() for o in objs], ensure_ascii=False)


@pytest.mark.parametrize("t", [1, 2, 3, 4])
def test_planted_items_absent_from_clean_game_and_private(t):
    c, p, _ = cleaned(t)
    game, both = _dump(c), _dump(c, p)
    for name, text in PLANTS.items():
        assert text not in both, f"planted {name} reached CleanGame/CleanPrivate (type {t})"
    for marker in ("Keep this agreement hidden", "experiment", "deposit", "$-8", "Zebra plan",
                   "HISTORY OF PREVIOUS ROUNDS", "real payoff", "RAW-FAILURE", "PRIVATE NOTE", "alliance_v2"):
        assert marker not in both
    assert "-8" not in game


def test_leak_counts_per_fixture():
    got = {t: cleaned(t)[0].leak_scan for t in (1, 2, 3, 4)}
    # type 1: addendum copy matches 2 setup texts (both {P} fills) -> 2 hits, 1 sentence removed
    # type 4 (with P2's real scanner): "$-8" is ONE hit (dollar_minus_8; minus_8 skips a minus right after "$"),
    # plus "deposit" in the private sentence and "deposit" in the public one -> 3 hits, same 2 sentences
    # removed. The P5 local stub counted "$-8" twice ("-8" and "$-8") -> 4.
    assert got == {1: {"hits": 2, "redactions": 1}, 2: {"hits": 1, "redactions": 1},
                   3: {"hits": 0, "redactions": 0}, 4: {"hits": 3, "redactions": 2}}


def test_redaction_keeps_rest_of_message():
    c, _, hits = cleaned(1)
    msg = next(a.message for a in c.rounds[1].announcements if a.agent == "M")
    assert msg == "I think the bar will be quiet. See you there."
    assert hits[0]["removed"] == [PLANTS["addendum_copy"]]


@pytest.mark.parametrize("t", [1, 2, 3, 4])
def test_payoffs_are_standard_rules(t):
    c, _, hits = cleaned(t)
    for r in c.rounds:
        assert r.payoffs_public == standard_payoffs(r.actions)
        assert set(r.payoffs_public.values()) <= {10, -5, 0}
    assert not [h for h in hits if h["kind"] == "payoff_mismatch"]


def test_payoff_mismatch_is_reported():
    rec = record(4)
    for R in rec["rounds"]:
        R["outcome"]["payoffs_public"] = R["outcome"]["payoffs_private"]   # a generator bug leaking -8
    c, _, hits = clean_game(rec, SETUP)
    mism = [h for h in hits if h["kind"] == "payoff_mismatch"]
    assert len(mism) == 1 and mism[0]["round"] == 6        # only round 6 has a focal STAY
    assert all(-8 not in r.payoffs_public.values() for r in c.rounds)


def test_imputed_action_stays_none_and_round_invalid():
    c, p, _ = cleaned(2)
    r4 = c.rounds[3]
    assert r4.actions["Q"] is None and r4.valid is False
    assert all(r.valid for r in c.rounds if r.round != 4)
    assert r4.payoffs_public["Q"] == 0                      # played as STAY in the game


def test_unknown_fields_ignored():
    rec = record(3)
    rec["wall_s"], rec["machine"], rec["new_p2_field"] = 1.0, "B", {"x": 1}
    rec["rounds"][0]["extra"] = "EXTRA-FIELD-TEXT"
    c, _, _ = clean_game(rec, SETUP)
    assert "EXTRA-FIELD-TEXT" not in _dump(c) and "new_p2_field" not in _dump(c)


def test_given_scanner_is_used():
    seen = []

    def scan(text, setup, banned):
        seen.append(text)
        return [{"kind": "test"}] if "Bar for me" in text else []

    c, _, hits = cleaned(1, scanner=scan)
    assert seen and all("Bar for me" not in a.message for r in c.rounds for a in r.announcements)
    assert hits and resolve_scanner(scan) == (scan, "given")


def test_scanner_falls_back_to_stub(monkeypatch):
    monkeypatch.setitem(sys.modules, "core.clean.leaks", None)   # import fails
    assert resolve_scanner() == (stub_scan_for_leaks, "local_stub")


@pytest.mark.parametrize("text,kind", [
    ("Staying home costs me −8 tonight.", "payoff4b"), ("I'd lose -$8.", "payoff4b"), ("It pays $-8 for me.", "payoff4b"),
    ("My real payoff differs.", "payoff4b"), ("This is a weird experiment.", "banned"),
    ("Only you can see this, right?", "banned"),
])
def test_stub_checks_hit(text, kind):
    assert kind in {h["kind"] for h in stub_scan_for_leaks(text, SETUP, cleaner.BANNED_TERMS)}


@pytest.mark.parametrize("text", ["The bar paid -5 last round.", "I got $10, then $0.", "18 people? No, 5 of us.",
                                  "Round 3-5 were calm.", "I'm going, see you there."])
def test_stub_no_false_hit_on_normal_text(text):
    assert stub_scan_for_leaks(text, SETUP, cleaner.BANNED_TERMS) == []


def test_copy_spanning_two_sentences_removes_both():
    # each half alone is < 8 copied words; together they are 11 consecutive words of the alliance addendum
    a, b = "The combined payout of you.", "And Agent T over all rounds."
    assert not stub_scan_for_leaks(a, SETUP, cleaner.BANNED_TERMS)
    assert not stub_scan_for_leaks(b, SETUP, cleaner.BANNED_TERMS)
    out, hits, removed = redact(f"Hello all. {a} {b} Going tonight.", stub_scan_for_leaks, SETUP, cleaner.BANNED_TERMS)
    assert hits and removed == [a, b] and out == "Hello all. Going tonight."
    assert stub_scan_for_leaks(out, SETUP, cleaner.BANNED_TERMS) == []
