"""Tests for scripts/labels_from_plan.py (task 18b): labels-only writer for a plan. Mock plans only, no model calls."""
import pytest

from core.labels import LABELS_PATH, label_from_config, labels_csv_text, read_labels
from core.plan import load_plan, make_plan
from core.split import SPLIT_PATH
from scripts import labels_from_plan as lfp


@pytest.fixture
def plan(tmp_path):
    return make_plan("mock_rep", 777, {1: 4, 2: 2, 3: 1, 4: 1}, ["A", "B"], 8, out_dir=tmp_path)


def test_labels_equal_label_from_config(plan, tmp_path):
    out = tmp_path / "rep" / "labels.csv"
    labels = lfp.write_labels_only(plan, out)
    expected = [label_from_config({"game_id": e.game_id, "episode_type": e.episode_type, "focal_pair": e.focal_pair,
                                   "variant": e.variant, "synthetic": False}) for e in load_plan(plan)]
    assert sorted(labels, key=lambda x: x.game_id) == sorted(expected, key=lambda x: x.game_id)
    assert sorted(read_labels(out), key=lambda x: x.game_id) == sorted(expected, key=lambda x: x.game_id)
    assert [lb.collusion for lb in labels] == [int(lb.episode_type == 1) for lb in labels]
    assert {t: sum(lb.episode_type == t for lb in labels) for t in (1, 2, 3, 4)} == {1: 4, 2: 2, 3: 1, 4: 1}


def test_output_format_identical_to_core_writer(plan, tmp_path):
    out = tmp_path / "labels.csv"
    labels = lfp.write_labels_only(plan, out)
    assert out.read_text(encoding="utf-8") == labels_csv_text(labels)
    assert out.read_bytes().count(b"\r") == 0                                  # LF, like data/labels.csv


@pytest.mark.parametrize("protected", [LABELS_PATH, SPLIT_PATH])
def test_refuses_protected_paths(plan, protected, monkeypatch):
    before = protected.read_bytes() if protected.exists() else None
    with pytest.raises(PermissionError):
        lfp.write_labels_only(plan, protected)
    assert lfp.main(["--plan", str(plan), "--out", str(protected)]) == 1
    assert (protected.read_bytes() if protected.exists() else None) == before  # untouched


def test_refuses_protected_path_given_relatively(plan, tmp_path):
    protected = tmp_path / "x" / "labels.csv"
    protected.parent.mkdir()
    with pytest.raises(PermissionError):
        lfp.write_labels_only(plan, tmp_path / "x" / ".." / "x" / "labels.csv", protected=(protected,))
    assert not protected.exists()


@pytest.mark.skipif(lfp.os.name != "nt", reason="case-insensitive paths only on Windows")
def test_refuses_protected_path_in_other_case(plan, tmp_path):
    protected = tmp_path / "labels.csv"
    with pytest.raises(PermissionError):
        lfp.write_labels_only(plan, tmp_path / "LABELS.CSV", protected=(protected,))
    assert not protected.exists()


def test_refuses_overwrite(plan, tmp_path):
    out = tmp_path / "labels.csv"
    lfp.write_labels_only(plan, out)
    first = out.read_bytes()
    with pytest.raises(FileExistsError):
        lfp.write_labels_only(plan, out)                                       # even with identical content
    assert lfp.main(["--plan", str(plan), "--out", str(out)]) == 1
    assert out.read_bytes() == first


def test_refuses_without_out(plan):
    with pytest.raises(SystemExit):
        lfp.main(["--plan", str(plan)])


def test_never_writes_a_split(plan, tmp_path):
    out = tmp_path / "rep" / "labels.csv"
    assert lfp.main(["--plan", str(plan), "--out", str(out)]) == 0
    assert sorted(p.name for p in out.parent.iterdir()) == ["labels.csv"]
