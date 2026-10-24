"""Line endings can never change a hash or a model input (task 08, CRLF checkouts on Windows)."""
import pytest

from core.clean import leaks
from core.config import CONFIGS, normalize_newlines, read_text_lf, text_file_sha256
from core.generate import prompts as P
from core.generate import runner

PROMPT_FILES = P.prompt_files()


def _copy_dir(src, dst, eol):
    """Copy a folder; text files rewritten with the given line ending (LF content first)."""
    dst.mkdir(parents=True)
    for p in src.iterdir():
        if p.is_file():
            text = normalize_newlines(p.read_bytes().decode("utf-8"))
            (dst / p.name).write_bytes(text.replace("\n", eol).encode("utf-8"))
    return dst


@pytest.fixture
def prompt_dirs(tmp_path):
    return {eol: _copy_dir(P.PROMPTS_DIR, tmp_path / name, eol) for name, eol in (("lf", "\n"), ("crlf", "\r\n"),
                                                                                    ("cr", "\r"))}


def _use(monkeypatch, d):
    monkeypatch.setattr(P, "PROMPTS_DIR", d)
    monkeypatch.setattr(P, "MANIFEST", d / "manifest.json")


@pytest.mark.parametrize("text,want", [("a\r\nb", "a\nb"), ("a\rb", "a\nb"), ("a\nb", "a\nb"),
                                       ("a\r\n\r\nb\r", "a\n\nb\n"), ("", "")])
def test_normalize_newlines(text, want):
    assert normalize_newlines(text) == want


def test_copies_really_differ_on_disk(prompt_dirs):
    """Sanity: the copies really differ on disk (so the next tests are meaningful)."""
    name = "alliance_v3.txt"
    raw = {eol: (d / name).read_bytes() for eol, d in prompt_dirs.items()}
    assert raw["\r\n"] != raw["\n"] and b"\r\n" in raw["\r\n"] and b"\r\n" not in raw["\n"]


@pytest.mark.parametrize("name", PROMPT_FILES)
def test_prompt_sha256_same_for_lf_crlf_cr_and_equals_manifest(prompt_dirs, name):
    man = P.load_manifest()["sha256"]
    hashes = {eol: text_file_sha256(d / name) for eol, d in prompt_dirs.items()}
    assert len(set(hashes.values())) == 1
    assert hashes["\n"] == man[name]


def test_repo_checkout_matches_manifest():
    """Whatever line endings this checkout has, every prompt file matches configs/prompts/manifest.json."""
    man = P.load_manifest()["sha256"]
    assert sorted(man) == PROMPT_FILES
    assert {n: P.file_sha256(n) for n in PROMPT_FILES} == man


def test_manifest_check_passes_on_crlf_copies(prompt_dirs, monkeypatch):
    for d in prompt_dirs.values():
        _use(monkeypatch, d)
        assert runner.check_manifest() == P.load_manifest()["sha256"]


def _built_inputs():
    hist = "HISTORY OF PREVIOUS ROUNDS (announced -> actually did):\n  Round 1: J STAY->STAY (+0)."
    brev = P.read_prompt("brevity_v1.txt")
    out = {}
    for t in (1, 2, 3, 4):
        add = P.addendum_text(t, "T")
        out[f"addendum{t}"] = add
        out[f"stage1_{t}"] = P.stage1("M", hist, add, brev)[:2]
        out[f"chanA_{t}"] = P.channel("M", "T", 3, "A", [{"from": "T", "text": "hi"}], hist, add, brev)[:2]
        out[f"chanB_{t}"] = P.channel("M", "T", 3, "B", [], hist, add, brev,
                                      announcements=[{"name": "J", "stated_action": "GO", "message": "x"}])[:2]
    out["files"] = {n: P.read_prompt(n) for n in PROMPT_FILES}
    return out


def test_built_prompts_identical_for_lf_crlf_cr(prompt_dirs, monkeypatch):
    built = {}
    for eol, d in prompt_dirs.items():
        _use(monkeypatch, d)
        built[eol] = _built_inputs()
    assert built["\r\n"] == built["\n"] and built["\r"] == built["\n"]
    def strings(x):
        if isinstance(x, str):
            yield x
        elif isinstance(x, dict):
            for v in x.values():
                yield from strings(v)
        else:
            for v in x:
                yield from strings(v)
    assert not any("\r" in s for s in strings(built["\r\n"]))     # no stray CR in any model input


def test_setup_texts_identical_for_lf_and_crlf(prompt_dirs, monkeypatch):
    rec = {"config": {"episode_type": 1, "focal_pair": ["M", "T"], "brevity": True}}
    got = {}
    for eol, d in prompt_dirs.items():
        _use(monkeypatch, d)
        got[eol] = leaks.setup_texts_for(rec)
    assert got["\r\n"] == got["\n"] == got["\r"]


def test_monitor_template_crlf(tmp_path):
    from study_2_2_views.monitor import PROMPTS, load_config
    for eol in ("\n", "\r\n"):
        d = _copy_dir(CONFIGS / "monitor", tmp_path / f"m{len(eol)}", eol)
        for name in PROMPTS.values():
            assert load_config(d, name) == load_config(manifest=name)


def test_read_text_lf(tmp_path):
    p = tmp_path / "x.txt"
    p.write_bytes("a\r\nb\rc\n".encode("utf-8"))
    assert read_text_lf(p) == "a\nb\nc\n"
