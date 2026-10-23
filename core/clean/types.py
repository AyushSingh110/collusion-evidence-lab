"""CleanGame / CleanPrivate: the only inputs views and the monitor may see (report 00 §5, §11.1).

The classes use __slots__, so no attribute outside the whitelist can be set, and from_dict
rejects unknown keys instead of ignoring them.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, fields
from typing import Any, Optional


def _strict(cls, d: dict[str, Any]) -> dict[str, Any]:
    names = {f.name for f in fields(cls)}
    extra = set(d) - names
    if extra:
        raise ValueError(f"{cls.__name__}: fields outside the whitelist: {sorted(extra)}")
    return d


@dataclass(slots=True)
class CleanAnnouncement:
    agent: str
    position: int
    stated_action: Optional[str]     # GO / STAY / None (parse failure)
    message: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CleanAnnouncement":
        return cls(**_strict(cls, d))


@dataclass(slots=True)
class CleanRound:
    round: int
    announcements: list[CleanAnnouncement]
    actions: dict[str, Optional[str]]  # None = failed / imputed decision
    valid: bool                        # all final actions parsed and none imputed
    payoffs_public: dict[str, int]     # standard rules, recomputed by the cleaner

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CleanRound":
        d = dict(_strict(cls, d))
        d["announcements"] = [CleanAnnouncement.from_dict(a) for a in d["announcements"]]
        return cls(**d)


@dataclass(slots=True)
class CleanGame:
    game_id: str
    agents: list[str]
    n_rounds: int
    rules_text: str
    rounds: list[CleanRound]
    leak_scan: dict[str, int]          # {"hits": n, "redactions": n}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CleanGame":
        d = dict(_strict(cls, d))
        d["rounds"] = [CleanRound.from_dict(r) for r in d["rounds"]]
        return cls(**d)


@dataclass(slots=True)
class PrivateStage1:
    intended_action: Optional[str]
    reasoning: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PrivateStage1":
        return cls(**_strict(cls, d))


@dataclass(slots=True)
class PrivateStage3:
    reasoning: str

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "PrivateStage3":
        return cls(**_strict(cls, d))


@dataclass(slots=True)
class CleanPrivateRound:
    round: int
    stage1: dict[str, PrivateStage1]
    stage3: dict[str, PrivateStage3]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CleanPrivateRound":
        d = dict(_strict(cls, d))
        d["stage1"] = {a: PrivateStage1.from_dict(v) for a, v in d["stage1"].items()}
        d["stage3"] = {a: PrivateStage3.from_dict(v) for a, v in d["stage3"].items()}
        return cls(**d)


@dataclass(slots=True)
class CleanPrivate:
    """Stage 1 plan (intended action + reasoning) and Stage 3 reasoning only. Never channel messages."""
    game_id: str
    rounds: list[CleanPrivateRound]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "CleanPrivate":
        d = dict(_strict(cls, d))
        d["rounds"] = [CleanPrivateRound.from_dict(r) for r in d["rounds"]]
        return cls(**d)
