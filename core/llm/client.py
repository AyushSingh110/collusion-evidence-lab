"""CachedLLM: every LLM call in the project goes through here (Rule G caching, Rule H pinning).

- Start-up pin check: refuses to run unless the Ollama version and every needed model digest
  match configs/pins.json.
- All generation options are required keyword arguments (no silent defaults, Rule H num_ctx).
- Cache: cache/llm/<machine_id>/<aa>/<sha256>.json, atomic writes; lookups also search other
  machines' shards so merged caches are reused.
- Transport errors: at most len(retry_delays) retries, each attempt logged. Parse failures are
  NOT retried (failures are data). Transport failures are returned but not cached.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
import platform
import shutil
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional, Sequence

from core.config import atomic_write_text, canonical_json, sha256_of
from core.llm.transport import TransportError
from core.schema import LLMResult

log = logging.getLogger("core.llm")


class PinError(RuntimeError):
    """Ollama version or a model digest does not match configs/pins.json."""


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def gpu_name() -> str:
    exe = shutil.which("nvidia-smi")
    if exe:
        try:
            out = subprocess.run([exe, "--query-gpu=name", "--format=csv,noheader"], capture_output=True,
                                 text=True, timeout=10).stdout.strip()
            if out:
                return out.splitlines()[0]
        except (OSError, subprocess.SubprocessError):
            pass
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        return "Apple Silicon"
    return "unknown"


def default_machine_id() -> str:
    """COLLUSION_LAB_MACHINE (e.g. 'A') if set, else a short hash of the host name."""
    env = os.environ.get("COLLUSION_LAB_MACHINE", "").strip()
    if env:
        return env
    return "m_" + hashlib.sha256(platform.node().encode("utf-8")).hexdigest()[:8]


def check_pins(transport, pins: dict[str, Any], models: Sequence[str]) -> dict[str, str]:
    """Raise PinError unless the server version and each model digest match the pins.

    Returns {model_tag: digest} for the checked models.
    """
    want_v = pins["ollama_version"]
    got_v = transport.version()
    if got_v != want_v:
        raise PinError(f"Ollama version {got_v!r} != pinned {want_v!r}")
    installed = transport.tags()
    out = {}
    for m in models:
        if m not in pins["models"]:
            raise PinError(f"model {m!r} is not in configs/pins.json")
        want = pins["models"][m]["digest"]
        got = installed.get(m)
        if got is None:
            raise PinError(f"model {m!r} is not installed (ollama pull {m})")
        if got != want:
            raise PinError(f"model {m!r} digest {got[:12]}... != pinned {want[:12]}...")
        out[m] = got
    return out


def cache_key(*, transport: str, model_tag: str, model_digest: str, messages: list[dict[str, str]],
              format_schema: Optional[dict], num_ctx: int, num_predict: int, temperature: float, seed: int,
              sample_idx: int) -> str:
    return sha256_of({
        "transport": transport, "model_tag": model_tag, "model_digest": model_digest, "messages": messages,
        "format_schema_sha256": None if format_schema is None else sha256_of(format_schema),
        "num_ctx": num_ctx, "num_predict": num_predict, "temperature": temperature, "seed": seed,
        "sample_idx": sample_idx,
    })


class CachedLLM:
    def __init__(self, *, transport, pins: dict[str, Any], models: Sequence[str], cache_dir: Path,
                 machine_id: Optional[str] = None, gpu: Optional[str] = None, timeout_s: float = 600.0,
                 retry_delays_s: Sequence[float] = (5.0, 20.0), keep_alive: str = "30m",
                 sleep: Callable[[float], None] = time.sleep):
        self.transport = transport
        self.pins = pins
        self.digests = check_pins(transport, pins, models)  # refuses to start on any mismatch
        self.ollama_version = pins["ollama_version"]
        self.cache_dir = Path(cache_dir)
        self.machine_id = machine_id or default_machine_id()
        self.timeout_s = timeout_s
        self.retry_delays_s = tuple(retry_delays_s)
        self.keep_alive = keep_alive
        self._sleep = sleep
        self.gpu = gpu if gpu is not None else gpu_name()

    # -- cache -----------------------------------------------------------------
    def _path(self, key: str, machine_id: Optional[str] = None) -> Path:
        return self.cache_dir / (machine_id or self.machine_id) / key[:2] / f"{key}.json"

    def _lookup(self, key: str) -> Optional[dict[str, Any]]:
        own = self._path(key)
        if own.exists():
            return json.loads(own.read_text(encoding="utf-8"))
        if self.cache_dir.exists():
            for p in self.cache_dir.glob(f"*/{key[:2]}/{key}.json"):
                return json.loads(p.read_text(encoding="utf-8"))
        return None

    # -- main entry ------------------------------------------------------------
    def complete(self, *, model: str, messages: list[dict[str, str]], format_schema: Optional[dict],
                 num_ctx: int, num_predict: int, temperature: float, seed: int, sample_idx: int,
                 purpose: str) -> LLMResult:
        if model not in self.digests:
            raise PinError(f"model {model!r} was not pin-checked at start-up (pass it in models=[...])")
        digest = self.digests[model]
        key = cache_key(transport=self.transport.name, model_tag=model, model_digest=digest, messages=messages,
                        format_schema=format_schema, num_ctx=num_ctx, num_predict=num_predict,
                        temperature=temperature, seed=seed, sample_idx=sample_idx)
        hit = self._lookup(key)
        if hit is not None:
            res = LLMResult.from_dict(hit["result"])
            res.cache_hit = True
            return res

        payload = {"model": model, "messages": messages, "stream": False, "keep_alive": self.keep_alive,
                   "options": {"num_ctx": num_ctx, "num_predict": num_predict, "temperature": temperature,
                               "seed": seed}}
        if format_schema is not None:
            payload["format"] = format_schema

        attempts: list[dict[str, Any]] = []
        body, latency, error = None, None, None
        for attempt in range(len(self.retry_delays_s) + 1):
            t0 = time.monotonic()
            try:
                body = self.transport.chat(payload, timeout=self.timeout_s)
                latency = round(time.monotonic() - t0, 3)
                attempts.append({"attempt": attempt + 1, "ok": True, "latency_s": latency})
                error = None
                break
            except TransportError as e:
                error = str(e)
                rec = {"attempt": attempt + 1, "ok": False, "error": error, "retryable": e.retryable,
                       "latency_s": round(time.monotonic() - t0, 3)}
                attempts.append(rec)
                if not e.retryable or attempt == len(self.retry_delays_s):
                    log.warning("LLM call %s (%s) failed for good after %d attempt(s): %s", key[:12], purpose,
                                attempt + 1, error)
                    break
                delay = self.retry_delays_s[attempt]
                rec["retry_after_s"] = delay
                log.warning("LLM call %s (%s) attempt %d failed (%s); retrying in %ss", key[:12], purpose,
                            attempt + 1, error, delay)
                self._sleep(delay)

        if body is None:  # transport failure: returned as data, not cached (a later run may try again)
            return LLMResult(key, False, None, None, None, None, None, {}, None, None, False, model, digest,
                             self.ollama_version, self.machine_id, utc_now(), error, attempts)

        content = (body.get("message") or {}).get("content")
        parsed, parse_error = None, None
        if format_schema is not None:  # parse once; a parse failure is NOT retried
            try:
                parsed = json.loads(content or "")
                if not isinstance(parsed, dict):
                    parsed, parse_error = None, f"JSON is {type(parsed).__name__}, not an object"
            except json.JSONDecodeError as e:
                parse_error = f"JSONDecodeError: {e}"
        pec, done_reason = body.get("prompt_eval_count"), body.get("done_reason")
        truncation_suspect = (pec is not None and pec >= num_ctx / 2) or done_reason == "length"
        res = LLMResult(
            cache_key=key, cache_hit=False, content=content, parsed=parsed, parse_error=parse_error,
            prompt_eval_count=pec, eval_count=body.get("eval_count"),
            durations_ns={k: body.get(k) for k in ("total_duration", "load_duration", "prompt_eval_duration",
                                                    "eval_duration")},
            done_reason=done_reason, latency_s=latency, truncation_suspect=bool(truncation_suspect),
            model_tag=model, model_digest=digest, ollama_version=self.ollama_version, machine_id=self.machine_id,
            created_utc=utc_now(), error=None, attempts=attempts)
        entry = {"key": key, "purpose": purpose, "sample_idx": sample_idx, "request": payload, "raw_response": body,
                 "result": res.to_dict(), "gpu": self.gpu}
        atomic_write_text(self._path(key), canonical_json(entry))
        return res
