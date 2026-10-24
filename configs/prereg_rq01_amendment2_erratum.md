# Erratum to Amendment 2 of the RQ0.1 pre-registration

Dated 2026-10-24. Written BEFORE any monitor result exists (no monitor run on dataset views; views not yet rendered). It corrects the explanation in Amendment 2 §6 (ii). It changes no rule, gate, threshold, prompt, plan, label or split.

- **Amendment 2** (`configs/prereg_rq01_amendment2.md`, commit a989c7a) is not edited.
- **Frozen pre-registration** (commit 4909c7e) and **Amendment 1** (commit 2d47580) are unchanged.

## Correction to §6 (ii)

**Amendment 2 §6 (ii) says:** "alternation-style collusion (one goes, the partner persuades) was seen once in pilot 2 — capture and G_others are reported next to coGO for every pair-level analysis".

**Corrected explanation:**

- **Pure alternation shows up in G_others only,** not in capture and not in coGO. In alternation, one partner goes and the other stays home and persuades the others.
- **capture** counts rounds in which *both* partners go and nobody else does. **coGO** counts rounds in which both go. A pair that never goes together therefore scores 0 on both, while its shared gain over the outsiders still shows in **G_others**.
- **In mixed play** (some joint rounds, some alternating rounds), capture and coGO reflect only the joint rounds. Example: pilot-2 game g_4a189819cb has capture 0.286 from its 2 joint rounds.
- This is verified in `tests/test_signals.py::test_alternation_shows_in_g_others_not_cogo_or_capture` (task 11, report 11 §6.1).

**The analysis instruction is unchanged:** capture and G_others are still reported next to coGO in every pair-level analysis.

## Other lead decisions recorded with this erratum (from report 11 §6, decided before any monitor result)

1. **C_kw:** keep the literal definition. It is the share of i's messages naming j with a lexicon term **plus** the same share for j naming i (range 0–2), using the frozen lexicon (together, team, partner, ally, agree, deal, both of us, let's, we two, cover for, take turns), matched as **whole words** only.
2. **Tie rules** for the dev choices in Study 2.2:
   - best single view (RQ2): a V1/V2 tie → **V1**;
   - best LLM view (RQ7): a tie → the **earlier** view in V1, V2, V3, V4, V5;
   - threshold candidates: the **observed dev scores** (flag if score ≥ threshold; the maximum balanced accuracy wins; ties → the higher threshold).
