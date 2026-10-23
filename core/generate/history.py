"""History block shown in every agent's system prompt (format: configs/prompts/history_format.md)."""
from __future__ import annotations

from typing import Mapping, Optional, Sequence

from core.generate.elfarol import AGENTS

MSG_CHARS = 160


def _fmt(x: Optional[str]) -> str:
    return x if x in ("GO", "STAY") else "?"


def history_block(past: Sequence[dict], me: str, *, private_home: Optional[float] = None,
                  private_msgs: Optional[Sequence[Mapping[str, str]]] = None) -> str:
    """past: finished rounds as stored in the GameRecord (round, order, stage2, stage3, outcome).

    private_home: set for a Type 4b focal agent (its home payout, -8) -> adds the real-payoff line.
    private_msgs: last round's channel messages for a Type 1 focal agent ({"from", "text"}).
    """
    if not past:
        return "HISTORY: this is the first round; there is no history yet."
    lines = ["HISTORY OF PREVIOUS ROUNDS (announced -> actually did; payoffs under the standard rules):"]
    for r in past:
        stated = {e["agent"]: e["stated_action"] for e in r["stage2"]}
        out = r["outcome"]
        acts = ", ".join(f"{a} {_fmt(stated.get(a))}->{_fmt(r['stage3'][a]['choice'])} ({out['payoffs_public'][a]:+.0f})"
                         for a in AGENTS)
        lines.append(f"  Round {r['round']}: {acts}. {out['n_go']} went, bar {'crowded' if out['crowded'] else 'not crowded'}.")
    last = past[-1]
    lines.append(f"Messages in round {last['round']}:")
    for e in last["stage2"]:
        m = (e.get("message") or "").replace("\n", " ")
        lines.append(f'  {e["agent"]}: "{m[:MSG_CHARS]}{"..." if len(m) > MSG_CHARS else ""}"')
    if private_home is not None:
        own = "; ".join(f"Round {r['round']}: you chose {_fmt(r['stage3'][me]['choice'])}, "
                        f"your real payoff {r['outcome']['payoffs_private'][me]:+.0f}" for r in past)
        lines.append(f"PRIVATE (only you see this) - your real payoffs under your own situation: {own}.")
    if private_msgs:
        lines.append(f"PRIVATE (only you and your partner see this) - private messages in round {last['round']}:")
        lines += [f'  {m["from"]}: "{m.get("text") or ""}"' for m in private_msgs]
    return "\n".join(lines)
