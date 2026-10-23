"""Transports for CachedLLM: the native Ollama HTTP API, and a scripted mock for tests.

Must not import anything from external/ (the harness) - report 01 §8.1.
"""
from __future__ import annotations

import json
import socket
import urllib.error
import urllib.request
from typing import Any, Callable, Optional, Union


class TransportError(Exception):
    """A call that did not return a usable HTTP response. `retryable` decides the retry policy."""

    def __init__(self, message: str, retryable: bool):
        super().__init__(message)
        self.retryable = retryable


class OllamaTransport:
    """POST /api/chat (stream=false), GET /api/version, GET /api/tags."""

    name = "ollama-native"

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")

    def _request(self, path: str, payload: Optional[dict], timeout: float) -> dict[str, Any]:
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(self.base_url + path, data=data,
                                     headers={"Content-Type": "application/json"},
                                     method="GET" if payload is None else "POST")
        try:
            with urllib.request.urlopen(req, timeout=timeout) as resp:
                return json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", "replace")[:300]
            raise TransportError(f"HTTP {e.code}: {body}", retryable=e.code >= 500) from e
        except (urllib.error.URLError, socket.timeout, TimeoutError, ConnectionError) as e:
            raise TransportError(f"{type(e).__name__}: {e}", retryable=True) from e
        except json.JSONDecodeError as e:
            raise TransportError(f"non-JSON response: {e}", retryable=True) from e

    def version(self) -> str:
        return self._request("/api/version", None, 30)["version"]

    def tags(self) -> dict[str, str]:
        """Installed models: tag -> digest."""
        return {m["name"]: m["digest"] for m in self._request("/api/tags", None, 30).get("models", [])}

    def chat(self, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        return self._request("/api/chat", payload, timeout)


MockReply = Union[dict, Exception, Callable[[dict], dict]]


class MockTransport:
    """Scripted transport. `replies` are consumed in order; the last one repeats.

    A reply is an Ollama-shaped response dict, an Exception to raise, or a function payload -> dict.
    """

    name = "ollama-native"  # same key namespace as the real transport

    def __init__(self, version: str, tags: dict[str, str], replies: Optional[list[MockReply]] = None):
        self._version, self._tags = version, dict(tags)
        self.replies = list(replies or [ok_reply('{"choice": "GO", "reasoning": "mock"}')])
        self.calls: list[dict[str, Any]] = []

    def version(self) -> str:
        return self._version

    def tags(self) -> dict[str, str]:
        return dict(self._tags)

    def chat(self, payload: dict[str, Any], timeout: float) -> dict[str, Any]:
        self.calls.append(payload)
        reply = self.replies[min(len(self.calls) - 1, len(self.replies) - 1)]
        if isinstance(reply, Exception):
            raise reply
        return reply(payload) if callable(reply) else reply


def ok_reply(content: str, prompt_eval_count: int = 500, eval_count: int = 60, done_reason: str = "stop") -> dict:
    """An Ollama /api/chat-shaped response (for tests and the mock)."""
    return {"message": {"role": "assistant", "content": content}, "done": True, "done_reason": done_reason,
            "prompt_eval_count": prompt_eval_count, "eval_count": eval_count, "total_duration": 1_000_000_000,
            "load_duration": 0, "prompt_eval_duration": 400_000_000, "eval_duration": 600_000_000}
