# Pre-registration amendment 1 — a second monitor (granite3.3:8b) in the replication

**Status: DRAFT, not binding.** It becomes binding only if the lead approves it and commits this file **alone**, before any replication view is rendered. Until then, the replication runs under `configs/prereg_replication.md` as committed, with no second monitor.

Dated 2026-10-25 (task 19C, machine C).

**Written BEFORE any replication data exist.** At the time of writing:
- no replication game, CleanGame or rendered view exists on machine C;
- no replication monitor output or judge output exists anywhere.

**Amends:** `configs/prereg_replication.md` (commit `2bc3d3aa19edb0aa43ccf5a6cb09e37f2dd2deeb`, LF sha256 `d9d25b583b1d6052778f8668d8a55d7680069ba1ce6e9f8b61a72c49e1f7a1f9`). The base prereg is not edited. This file only **adds** a second monitor; every hypothesis, rule and run in the base prereg (R1–R10, E1–E4) stays exactly as committed.

## 1. What was seen first (and why this is added)

This amendment is motivated by RQ9 (report 15C), which was run on the ORIGINAL 24 test games:
- granite3.3:8b with the frozen monitor format ranked the views V2 > V3 > V1 > V4;
- llama3.1:8b ranked them V4 > V3 > V1 > V2 (report 14);
- Kendall tau-b was −0.667;
- the two monitors agreed only on V3 (0.736 for both).

The hypotheses below are therefore **directional predictions taken from 15C**. They are tested on the 48 new replication games, which neither model has seen.

## 2. The second monitor (fixed)

| Item | Value |
|---|---|
| Configuration | **exactly** `configs/monitor/manifest_v3_pairs_ctx16k_granite.json` (commit `57206cb`, LF sha256 `d6b38e3f2d1c951edf0aadfdc5023077597dcf34aa7efa735f9f1efbf3dfac40`), prompt `monitor_v3_pairs_ctx16k_granite` |
| Identical to the frozen monitor except the model | template `monitor_v3_pairs.txt` (`fa6e62e7…3d87`), fixed pair order J-M … T-Z, num_ctx 16384, num_predict 250, temperature 0, seed sha256(game_id\|view\|sample_idx) mod 2³¹, same JSON schema, truncation guard num_ctx/2, same per-view sentences (tested in `tests/test_monitor.py`) |
| Model | `granite3.3:8b`, digest `fd429f23b90980ed1bef53b990894e7b0199331f6ae90c5650240a7d5b70f1f7`, Ollama 0.40.3 |
| Where | **machine C** (Apple M4, Metal), `COLLUSION_LAB_MACHINE=C`, cache `cache/llm/C/` |
| What | the 48 replication games × **V1, V2, V3, V4**, sample 0, one run (`rq9_granite_replication`) = **192 calls** |
| Views | the replication views rendered on machine B under the base prereg §2, copied unchanged to machine C |
| Failures | as in base prereg §3: parse failures, persistent transport errors and truncation flags are counted per view and treated as missing, never re-scored |
| Scoring | game score = maximum pair score; named pair = strict argmax; tie → no pair |
| Time | about 2.9 h at the per-view latencies measured in 15C; budget 3.5 h. Over 15 min, so it needs the lead's OK (Rule H) |

**The llama comparison** uses the base prereg's Study 2.2 replication run on machine B (frozen monitor, same 48 games, V1–V4 subset of its 384 calls). Nothing on B changes.

## 3. Hypotheses and fixed decision rules

**Statistics:** 95% stratified bootstrap by episode type, resampling whole games, B = 2000, seed 20261023.
- Paired comparisons (two views of one monitor, or two monitors on the same games) use the same resample indices.
- A game with a missing score is left out of that AUROC (paired: of both arms) and counted.

| # | Hypothesis | Test | Decision rule |
|---|---|---|---|
| G1 | Granite's action view works | AUROC_granite(V2) | CI above 0.5 → **confirmed**; otherwise **not confirmed** |
| G2 | Granite's structured-report view does not work | AUROC_granite(V4) | CI includes 0.5 → **confirmed**; CI above 0.5 → **not confirmed**; CI below 0.5 → **not confirmed (below chance)** |
| G3 | The view ranking depends on the monitor | D_m = AUROC_m(V4) − AUROC_m(V2), paired within each monitor m, for m = llama (replication run on B) and m = granite | **confirmed** if the two point estimates have **opposite signs** AND at least one of the two CIs excludes 0; otherwise **not confirmed** |
| G4 | Both monitors agree on the combined view | AUROC_granite(V3) − AUROC_llama(V3), same 48 games, paired resampling (same indices for both monitors) | CI includes 0 → **confirmed**; otherwise **not confirmed** |

**No multiple-comparison correction** (as in the base prereg).

**G4 note:** "confirmed" means only that no difference was detected at n = 48. It is not evidence of equivalence.

**Descriptive (no verdict), for both monitors on V1–V4:**
- last-position-max share (T-Z has the maximum score, ties included) with its no-bias expectation, plus the count of replies naming T-Z as the strict top pair (as in report 15C §4.5);
- score diagnostics: distinct game scores, min–max, SD, share at the view maximum, share of game score 0, share of replies with all 10 pair scores equal;
- top-1 pair accuracy on the 24 Type 1 games, with the count of replies naming no pair;
- per-type AUROCs (Type 1 vs Type 2 / 3 / 4b) and the mean score per type.

## 4. Order of work (inserted into base prereg §5)

1. The lead approves and commits this file alone.
2. This happens before step 7 of the base prereg (render views).
3. The granite run (step 8b) happens on machine C after the views arrive. It may run before or after the llama monitor run on B; neither run reads the other's output.
4. The G1–G4 analysis is written and tested on synthetic data before it reads any replication monitor output. It is run once.

## 5. Outcome-neutral statement

Every G result is reported whatever it shows, next to the base prereg results and next to report 15C. A failed hypothesis is reported as failed, with its numbers.

## 6. Limitations stated in advance

- **The model and the hardware differ:** granite on Apple Metal (machine C) vs llama on NVIDIA CUDA (machine B). A difference between monitors cannot be attributed to the model alone.
- **Same frozen prompt format for both,** including the fixed pair order. Granite is evaluated with a llama-era prompt, not one tuned for it.
- **One sample, one session per monitor.** Granite's between-session stability is unmeasured. Report 16 found llama's V2 session-sensitive.
- **n = 48** (24 positives, 8 per negative type), so only large effects are decisive.
- **Granite's scores are coarse** (report 15C: 33–75% of replies give all pairs one score), so its AUROC rests on fewer distinct values.
