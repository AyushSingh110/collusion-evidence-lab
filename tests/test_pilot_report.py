import csv

import pytest

from core.generate.runner import run_game
from core.plan import load_plan, make_plan
from scripts import pilot_report
from tests.genmock import PINS, defaults, mock_llm


@pytest.fixture
def pilot(tmp_path):
    plan = make_plan("pilot", 31337, {1: 4, 2: 2, 3: 1, 4: 1}, ["A", "B"], 4, out_dir=tmp_path / "plans")
    cache = tmp_path / "cache"
    for m in ("A", "B"):
        llm, _ = mock_llm(tmp_path, machine_id=m, cache_dir=cache)
        for e in load_plan(plan):
            if e.machine == m:
                run_game(e, llm, run_defaults=defaults(), raw_dir=tmp_path / "raw" / m, machine=m)
    return plan, tmp_path / "raw", cache, tmp_path / "out"


def test_report_writes_all_outputs(pilot):
    plan, raw, cache, out = pilot
    code, text = pilot_report.build_report(plan, raw, cache, out, PINS)
    assert code == 0
    for name in ("pilot_table.csv", "handcheck_uptake.csv", "pilot_summary.md"):
        assert (out / name).exists()
    with open(out / "pilot_table.csv", encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    assert len(rows) == 8 and set(r["machine"] for r in rows) == {"A", "B"} and all(r["min"] != "" for r in rows)
    with open(out / "handcheck_uptake.csv", encoding="utf-8") as f:
        hand = list(csv.DictReader(f))
    assert len(hand) == 6 * 2 * 4                         # (4 Type 1 + 2 Type 2) x 2 focal agents x 4 rounds
    assert all(h["U_hand"] == "" for h in hand) and {h["type"] for h in hand} == {"1", "2"}
    t1 = [h for h in hand if h["type"] == "1"]
    assert all("both go" in h["channel_texts"].lower() for h in t1)   # the exact channel text the rule read
    for k in ("(a) uptake", "falsification", "b1", "b2", "Public-reveal rate", "Leak-scanner hits per type",
              "Failures per type", "Minutes per game per machine", "Null percentiles"):
        assert k in text


def test_report_refuses_when_a_game_is_missing(pilot):
    plan, raw, cache, out = pilot
    next((raw / "B").glob("*.json")).unlink()
    code, text = pilot_report.build_report(plan, raw, cache, out, PINS)
    assert code == 1 and "REFUSED" in text and "missing record" in text
    assert not (out / "pilot_summary.md").exists()


def test_gate_counts_on_mock_pilot(pilot):
    plan, raw, cache, out = pilot
    _, text = pilot_report.build_report(plan, raw, cache, out, PINS)
    # mock channel says "Let's both go to the bar" every round -> all 4 Type 1 pass uptake; Type 2 has no channel
    assert "| (a) uptake, Type 1 | 4/4 |" in text and "| falsification, Type 2 | 0/2 |" in text


def _write(path, pairs):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=pilot_report.HAND_COLUMNS)
        w.writeheader()
        for i, (u, h) in enumerate(pairs):
            w.writerow({"game_id": f"g{i}", "type": 1, "agent": "M", "round": i + 1, "channel_texts": "", "stage1_reasoning": "",
                        "channel_joint": u, "plan_partner": 0, "U": u, "U_hand": h})


def test_handcheck_agreement_pass_and_fail(tmp_path):
    p = tmp_path / "h.csv"
    _write(p, [(1, 1)] * 8 + [(1, 0), (0, 1)])           # 8/10 = 80% -> pass
    r = pilot_report.handcheck_agreement(p)
    assert (r["agree"], r["filled"], r["agreement"], r["pass"]) == (8, 10, 0.8, True)
    assert pilot_report.main(["--handcheck", str(p)]) == 0
    _write(p, [(1, 1)] * 7 + [(1, 0)] * 3)               # 70% -> not passed
    assert pilot_report.handcheck_agreement(p)["pass"] is False
    assert pilot_report.main(["--handcheck", str(p)]) == 1


def test_handcheck_needs_all_cells_filled(tmp_path):
    p = tmp_path / "h.csv"
    _write(p, [(1, 1)] * 9 + [(1, "")])
    r = pilot_report.handcheck_agreement(p)
    assert r["missing"] == 1 and r["agreement"] == 1.0 and r["pass"] is False


def test_handcheck_rejects_bad_values(tmp_path):
    p = tmp_path / "h.csv"
    _write(p, [(1, "yes")])
    with pytest.raises(ValueError):
        pilot_report.handcheck_agreement(p)


# --------------------------------------------------------------- amendment 1: --rule v2 / --amendment1

def test_rule_v1_default_unchanged_and_v2_writes_separate_files(pilot):
    plan, raw, cache, out = pilot
    _, text_v1 = pilot_report.build_report(plan, raw, cache, out, PINS)
    before = {n: (out / n).read_bytes() for n in ("pilot_table.csv", "handcheck_uptake.csv", "pilot_summary.md")}
    _, text_v1b = pilot_report.build_report(plan, raw, cache, out, PINS, rule="v1")
    assert text_v1b == text_v1                                   # explicit --rule v1 == default
    code, text_v2 = pilot_report.build_report(plan, raw, cache, out, PINS, rule="v2")
    assert code == 0
    for n, b in before.items():                                  # v1 outputs never overwritten
        assert (out / n).read_bytes() == b
    for n in ("pilot_table_v2.csv", "handcheck_uptake_v2.csv", "pilot_summary_v2.md"):
        assert (out / n).exists()
    assert "uptake v2 (rule)" in text_v2 and "DESCRIPTIVE ONLY" in text_v2 and "amendment1" in text_v2
    assert "Games with any non-English text" in text_v2
    with open(out / "handcheck_uptake_v2.csv", encoding="utf-8") as f:
        hand = list(csv.DictReader(f))
    assert list(hand[0]) == pilot_report.HAND_COLUMNS_V2 and len(hand) == 6 * 2 * 4


def test_amendment1_mode_is_gate_only_for_pilot2_seed(pilot, tmp_path):
    import json
    plan, raw, cache, out = pilot
    _, text = pilot_report.build_report(plan, raw, cache, out, PINS, amendment1=True)
    assert "DESCRIPTIVE ONLY" in text and (out / "pilot_summary_amendment1.md").exists()   # seed 31337 != 20261025
    doc = json.loads(plan.read_text(encoding="utf-8"))
    doc["master_seed"] = pilot_report.AMENDMENT1_PILOT2_SEED   # only the label check reads it
    plan2 = tmp_path / "plan2.json"
    plan2.write_text(json.dumps(doc), encoding="utf-8")
    _, text2 = pilot_report.build_report(plan2, raw, cache, out, PINS, amendment1=True)
    assert "DESCRIPTIVE ONLY" not in text2 and "amendment-1 gate" in text2
