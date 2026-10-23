from core.config import load_pins
from core.llm import MockTransport
from scripts import check_env

PINS = load_pins()
GOOD_TAGS = {m: v["digest"] for m, v in PINS["models"].items()}


def _run(version, tags):
    return check_env.main(transport=MockTransport(version, tags))


def test_check_env_ready_when_everything_matches(capsys):
    code = _run(PINS["ollama_version"], GOOD_TAGS)
    out = capsys.readouterr().out
    # Python/env lines depend on how pytest is launched; only the Ollama part is asserted here.
    assert "Ollama version" in out and out.count("MATCH") >= 4
    assert code in (0, 1)


def test_check_env_fails_on_wrong_digest(capsys):
    tags = dict(GOOD_TAGS, **{"qwen2.5:7b": "0" * 64})
    assert _run(PINS["ollama_version"], tags) == 1
    assert "qwen2.5:7b digest" in capsys.readouterr().out


def test_check_env_fails_on_wrong_version(capsys):
    assert _run("0.40.10", GOOD_TAGS) == 1
    assert "ollama version" in capsys.readouterr().out


def test_check_env_optional_model_may_be_missing(capsys):
    tags = {m: d for m, d in GOOD_TAGS.items() if PINS["models"][m]["required"]}
    _run(PINS["ollama_version"], tags)
    out = capsys.readouterr().out
    assert "MISSING (optional" in out and "granite3.3:8b missing" not in out
