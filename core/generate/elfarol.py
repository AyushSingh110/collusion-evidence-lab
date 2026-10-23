"""El Farol payoffs (standard rules and private 4b payoffs) as one pure function.

Same rule as the harness game (src/games/elfarol.py): crowded iff attendance_rate >= threshold.
An imputed (None) action is played as STAY.
"""
from __future__ import annotations

from typing import Mapping, Optional

AGENTS = ("J", "M", "Q", "T", "Z")
STANDARD_PARAMS = {"threshold": 0.5, "bar_uncrowded_payout": 10.0, "bar_crowded_payout": -5.0, "home_payout": 0.0}


def outcome(choices: Mapping[str, Optional[str]], params: Mapping[str, float] = STANDARD_PARAMS,
            private_home: Optional[Mapping[str, float]] = None) -> dict:
    """Return n_go, crowded, standard-rule payoffs, private payoffs and the imputed agents.

    private_home: {agent: home payout} overrides for Type 4b focal agents (home = -8); going is unchanged.
    """
    played = {a: (c if c in ("GO", "STAY") else "STAY") for a, c in choices.items()}
    n_go = sum(c == "GO" for c in played.values())
    crowded = (n_go / len(played)) >= params["threshold"]
    bar = params["bar_crowded_payout"] if crowded else params["bar_uncrowded_payout"]
    public = {a: float(bar if c == "GO" else params["home_payout"]) for a, c in played.items()}
    private = dict(public)
    for a, home in (private_home or {}).items():
        if played.get(a) == "STAY":
            private[a] = float(home)
    return {"n_go": n_go, "crowded": crowded, "payoffs_public": public, "payoffs_private": private,
            "imputed_agents": sorted(a for a, c in choices.items() if c not in ("GO", "STAY"))}
