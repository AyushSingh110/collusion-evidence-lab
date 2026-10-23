import copy

import pytest

from core.labels import label_from_config, read_labels, write_labels
from core.schema import Label
from core.split import load_split, make_split

BASE_CFG = {"game_id": "g_0000000001", "episode_type": 1, "variant": "alliance_v2", "focal_pair": ["M", "T"],
            "agents": ["J", "M", "Q", "T", "Z"], "agent_model": "qwen2.5:7b", "temperature": 1.0, "n_rounds": 6,
            "game_seed": 1, "synthetic": False, "addenda": {"M": "alliance_v2"}, "private_channel": {"enabled": True}}


@pytest.mark.parametrize("et,expected", [(1, 1), (2, 0), (3, 0), (4, 0)])
def test_label_depends_on_episode_type(et, expected):
    assert label_from_config(dict(BASE_CFG, episode_type=et)).collusion == expected


@pytest.mark.parametrize("et", [1, 2, 3, 4])
def test_other_fields_never_change_the_label(et):
    base = label_from_config(dict(BASE_CFG, episode_type=et))
    mutations = {"variant": "x", "focal_pair": ["J", "Q"], "agent_model": "other", "temperature": 0.0,
                 "n_rounds": 99, "game_seed": 12345, "synthetic": True, "addenda": {},
                 "private_channel": {"enabled": False}, "agents": ["A", "B"]}
    for k, v in mutations.items():
        lb = label_from_config(dict(copy.deepcopy(BASE_CFG), episode_type=et, **{k: v}))
        assert (lb.collusion, lb.episode_type) == (base.collusion, base.episode_type), k


def test_invalid_episode_type_raises():
    with pytest.raises(ValueError):
        label_from_config(dict(BASE_CFG, episode_type=5))


def _labels(counts={1: 24, 2: 8, 3: 8, 4: 8}):
    out, i = [], 0
    for t, n in counts.items():
        for _ in range(n):
            out.append(Label(f"g_{i:010x}", t, int(t == 1), ["M", "T"], "v", False))
            i += 1
    return out


def test_write_labels_roundtrip_and_refuses_different_overwrite(tmp_path):
    p = tmp_path / "labels.csv"
    labels = _labels({1: 2, 2: 2})
    write_labels(labels, p)
    assert read_labels(p) == sorted(labels, key=lambda x: x.game_id)
    write_labels(labels, p)  # identical content is fine
    with pytest.raises(FileExistsError):
        write_labels(labels[:-1], p)


def test_split_deterministic_stratified_disjoint_covering(tmp_path):
    labels = _labels()
    s1 = make_split(labels, seed=20261023, path=tmp_path / "a.json")
    s2 = make_split(labels, seed=20261023, path=tmp_path / "b.json")
    assert (s1.dev, s1.test) == (s2.dev, s2.test)
    assert not set(s1.dev) & set(s1.test)
    assert set(s1.dev) | set(s1.test) == {lb.game_id for lb in labels}
    t_of = {lb.game_id: lb.episode_type for lb in labels}
    for t, n in {1: 24, 2: 8, 3: 8, 4: 8}.items():
        assert sum(t_of[g] == t for g in s1.dev) == n // 2
    s3 = make_split(labels, seed=1, path=tmp_path / "c.json")
    assert s3.dev != s1.dev  # a different seed gives a different (still stratified) split


def test_split_refuses_to_overwrite_and_loads(tmp_path):
    p = tmp_path / "split.json"
    s = make_split(_labels(), seed=3, path=p)
    with pytest.raises(FileExistsError):
        make_split(_labels(), seed=3, path=p)
    loaded = load_split(p)
    assert loaded.dev == s.dev and loaded.labels_sha256 == s.labels_sha256 and len(s.labels_sha256) == 64
