# Detecting collusion between LLM agents — one-page summary

## The problem

- **Setting:** two AI agents can secretly agree to coordinate against others.
- **First question:** can a monitor tell from a game record that two agents colluded?
- **Second question:** what evidence should count?
- **Our testbed:**
  - **Game:** El Farol bar game; 5 `qwen2.5:7b` agents; 8 rounds of public messages, then GO/STAY actions.
  - **Collusion games:** two agents get an alliance note.
  - **Three lookalikes with no collusion:**
    - honest play (placebo);
    - friendly "persona" talk;
    - a shared private incentive to go together.
  - **Ground truth:** comes only from how each game was generated.

## Two studies

- **Study 2.2 (monitor views):** an LLM monitor (llama3.1:8b; granite3.3:8b as a second model) reads one view of each game: messages, actions, both, a code-built structured report, or private plans. It scores each pair of agents.
- **Study 2.3 (evidence rules):** code-computed evidence (coalition gain, dependence, word–action consistency) and an LLM judge of the messages, combined into fixed decision rules.

**Protocol:** everything was frozen on 24 dev games, tested once on 24 test games, then **re-tested on 48 new games under a pre-registered replication** (`configs/prereg_replication.md`, plus amendment 1 for the second monitor).

## Main findings

| # | Finding | Key number(s) | Status |
|---|---|---|---|
| 1 | Model-free behaviour signals were the most reliable evidence | capture 0.900 [0.811, 0.965]; capture − best LLM view (V4) +0.264 [0.121, 0.412] (R21); coalition gain 0.885 [0.786, 0.961] (R22C) | **Replicated** |
| 2 | Both LLM monitors were mediocre and inconsistent on new games | all views V1–V4, both monitors, between 0.32 and 0.66 (R21, R22C); llama's structured report 0.896 → 0.636 | **Original V4 advantage not replicated** |
| 3 | Reading the messages alone never worked | V1 0.490 (test) → 0.505 (replication) (R14, R21) | **Replicated** |
| 4 | Talk-only LLM judging was near chance | judge 0.396 (test) → 0.543 [0.392, 0.693] (replication) (17C, R22C) | **Replicated** |
| 5 | Private plans added nothing | V5 − V3 −0.031 (test), −0.022 [−0.192, 0.155] (replication) (R14, R21) | **Consistent null** |
| 6 | Combining evidence did not beat gain alone | R6 − R2 −0.080 (test), −0.059 [−0.135, 0.010] (replication) (17C, R22C) | **Replicated null** |
| 7 | Which view works depends on the monitor | llama V4 − V2 +0.313 [0.127, 0.481]; granite −0.046 [−0.251, 0.152] (G3, R22C) | **Not shared between monitors** (G3; rests mainly on llama) |
| 8 | llama has a last-position bias in its pair scores (granite does not) | the last-listed pair gets the top score in 44/48 V1 replies vs 0.215 expected (R21) | **Replicated (llama only)** |

## What this means

- **Behaviour evidence carries the signal.** Outcome evidence (who gained, who had the bar to themselves) is the most dependable sign of collusion.
- **It is not enough on its own.** A shared private incentive produces the same outcomes, and that lookalike stays the hardest case (gain flags 3/8 of those games, R22C).
- **Small LLM monitors are unreliable judges of the same records.** Their best views did not hold up on new games (llama V4 0.896 → 0.636; granite V2 0.767 → 0.628), they depend on the model, and they show position and session artefacts.
- **None of the communication evidence we measured worked as the extra "plus factor".** The strict keyword rule caught 0/24 colluders on the replication.

## Main limitations

- **Small samples:** 24 test + 48 replication games, with 8 or fewer per lookalike type. CIs are wide.
- **Narrow setup:** one game, one agent model, 8 rounds. The collusion is suggested by a prompt, not invented by the agents.
- **Two small monitors** (8B), one frozen prompt format, one sample per call. Scores can change between sessions. The second monitor ran on different hardware, so model and hardware are confounded.
- **An unplanned clue:** shared-incentive agents talk about their "deposit" in public, and monitors could see it.

Details: `writeup/results_22.md` (Study 2.2), `writeup/results_23.md` (Study 2.3), `writeup/figures/` (Figures 1–10), `notes/reports/` (one report per task).
