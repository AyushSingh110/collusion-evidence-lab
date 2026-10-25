# 18c — Additive Study 2.2 code for the replication

Date: 2026-10-25 · Task 18c · Machine B · **No model calls** (generation was running on the GPU). **Nothing under `data/raw/replication/` and no replication output was read.** No generator file and nothing in `study_2_3_evidence/` was edited.

## 1. Goal (from the prompt)

Build the code that the replication pre-registration (§2, §3, §5) needs, all additive, with earlier behaviour proven byte-identical:
1. One-group C-mismatch for a set without a split.
2. A split-free analysis entry point computing R1–R10 and the secondary measures exactly as pre-registered, with refusal checks.
3. Code signals from replication CleanGames with the original honest baseline loaded from a file, never refitted.
4. Synthetic tests for every rule branch, the refusals and the pairing.
5. A post-generation readiness checklist (not run on real data).

## 2. What was built

| File | One line |
|---|---|
| `scripts/render_views.py` (edited, additive) | New `--no-split` + `load_mapping_unsplit(labels)`: every game maps to (type, "unsplit"), so the existing `mismatch_pairs` draws partners within type across the whole set, never self. Needs `--labels`, refuses `--split`. The default path is untouched. |
| `core/evidence/signals.py` (edited, additive) | New `load_honest_baseline(path)`: reads a fitted baseline (flat JSON or the `honest_baseline` key of `rules_frozen.json`) and returns it with its source (path, LF sha256, key). Nothing existing changed. |
| `scripts/signals_from_clean.py` (new) | Pair and game signal tables for a folder of CleanGames with a loaded baseline (default `configs/frozen/rules_frozen.json`); writes `baseline_source.json` (`refitted: false`). Refuses a non-empty `--out` or missing CleanGames. |
| `study_2_2_views/replication.py` (new) | R1–R10 (`SPEC` + `RULES`): each rule maps "CI above / includes / below" to the pre-registered outcome words, and "undetermined (no CI)" when there is no CI. Also `evaluate`, `hypotheses`, and `secondary` (other code signals incl. T1 vs T4b, top-1 pair accuracy incl. Dep argmax, frozen-threshold metrics + FP per type with degenerate labels, last-position-max share + no-bias expectation, V3 − C-mismatch and V3 − V1). |
| `scripts/analyse_replication_22.py` (new) | CLI: primary on all games, sensitivity without quality-fail games (`{"quality_fail": [...]}`). Refusal checks listed below. Writes the JSON, two hypothesis CSVs and `summary.md`. |
| `scratch/p18_ready.py` (new) | Prints the checklist by default. With `--after-generation` it checks complete valid records (no partials or extras, machines as planned), merge_check OK, and that the labels file equals the plan's labels. |
| `tests/test_replication22.py` (new) | 53 tests (§3). |

**`analyse_replication_22.py` refuses unless:**
- the monitor holds sample 0 only;
- the frozen monitor file matches its sha256 `ccc4bf07…` (via the existing `check_frozen`, which also checks the prompt version);
- the monitor digest equals the frozen digest;
- the prereg equals its committed blob (read-only `git show HEAD:`) **and** `d9d25b58…`;
- no labelled game is in `data/labels.csv`;
- the monitor covers every game × 8 views;
- the signals cover exactly the labelled games;
- the quality file lists only labelled games;
- `--out` is new or empty.

## 3. How it was verified

```
conda run -n collusion-lab pytest -q tests/test_replication22.py         # 53 passed (regression tests ran, none skipped)
conda run -n collusion-lab pytest -q                                     # 631 passed, 1 skipped (machine C's 17C test: its local outputs are not on B)
conda run -n collusion-lab python scripts/signals_from_clean.py --clean data/clean --labels data/labels.csv --out <scratchpad>/sig18c
cmp <scratchpad>/sig18c/game_signals.csv runs/p8_signals/game_signals.csv   # identical
cmp <scratchpad>/sig18c/pair_signals.csv runs/p8_signals/pair_signals.csv   # identical
conda run -n collusion-lab python -B scratch/p18_ready.py                # prints the checklist only
```

**Synthetic tests:**
- Every outcome branch of R1–R10b (33 parametrised cases), plus the boundary (a CI touching the reference "includes" it) and the no-CI case.
- End-to-end `evaluate` with constructed scores reaching confirmed / not confirmed / replicated / not replicated / reversed / below chance / pass / fail / comparable / undetermined.
- Missing scores dropped and counted; the secondary measures; the baseline loader.
- One-group C-mismatch: never self, within type, a permutation, deterministic; `--no-split` argument validation.
- `check_prereg`: blob differs / hash differs / not committed → refused; the real prereg passes.
- Analysis refusals: wrong frozen sha, wrong digest, sample 1, wrong prompt version, a missing view, overlap with the original dataset, non-empty out (CLI exit 2).
- The readiness script reads nothing without the flag.

**Regression proofs on the original data (earlier behaviour byte-identical):**
1. The default `render_views` on `data/raw/dataset` with the original task-12 arguments gives a manifest **equal** to `data/views/manifest.json`. All **384 view files** and **48 clean files** are byte-identical.
2. `analyse_22 --mode test` (frozen file + sha) regenerates `rq1_per_view_test.csv`, `rq2_rq4_rq5_rq6_rq7_paired_test.csv`, `rq3_fpr_by_type_test.csv` and `rq8_top1_pair_test.csv` **byte-identical** to `runs/test_p8/`.
3. The new replication module, run on the report-14 test set, reproduces report 14's numbers to 4 decimals:
   - R1 = V1 0.490, R2 = V4 0.896, R9 = C-shuffled 0.632 (estimates and CIs);
   - R3 = +0.365 [0.094, 0.611] → "replicated"; R4 = +0.160 [−0.021, 0.351] → "not replicated"; R5; R8.
4. `signals_from_clean.py` with the **loaded** baseline reproduces task 14's game and pair signal tables byte-identically (task 14 fitted the same baseline on dev Type 2).

## 4. Results

- **Tests:** 53 new tests pass; the full suite has 631 passed, 1 skipped (not ours).
- **Model calls:** 0.
- **Replication data:** none read.

## 5. Acceptance criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 1 | render_views no-split option; within type, never self, seed 20261023; default unchanged | **PASSED** | pairing tests; regression proof 1 |
| 2 | Split-free analysis: R1–R10 + outcome maps + all §3 secondary; primary + sensitivity; frozen thresholds only for secondary; refusals | **PASSED** | §2; refusal tests; regression proof 3 |
| 3 | Signals with the ORIGINAL baseline loaded from a file; source recorded; never refitted | **PASSED** | `load_honest_baseline`, `baseline_source.json`; regression proof 4 |
| 4 | Synthetic tests: every branch, refusals, one-group pairing | **PASSED** | 53 tests |
| 5 | Readiness checklist script, not run on real data | **PASSED** | prints the checklist only |
| — | Earlier behaviour byte-identical (dataset views, report 14 tables) | **PASSED** | regression proofs 1–2 |
| — | No model calls; no generator / study_2_3 edits; no replication data read | **PASSED** | `git status`: two additive edits + new files |

## 6. Deviations and decisions

1. **Outcome words for R2 / R10a "below":** the prereg gives "confirmed / otherwise not confirmed". A CI below 0.5 is coded "not confirmed", and the estimate shows the direction. The same applies to R9 "above / below" → "fail".
2. **Last-position-max:** in the fixed order the last pair is T-Z, so it is computed as the T-Z-max share, with ties included and the no-bias expectation counting ties (as in report 16 §4.3).
3. **Degenerate threshold label:** a frozen threshold ≤ 0 flags everything (V1, V3, C-mismatch).
4. **Quality input format:** `{"quality_fail": [game ids]}`. It will be written by the replication quality step (report 12-style).
5. **A test file in the repo now reads real data** (regression proofs). Those tests skip automatically on machines without `data/raw/dataset` or `runs/test_p8`.

## 7. Open problems

- Study 2.3 (machine C) still needs its own split-free entry point and rules application to new ids (not in scope; machine C owns `study_2_3_evidence/`).
- The replication quality-file writer (`quality_fail` list) is not built yet. Report 12's scratch script is the template.

## 8. Next task

After generation:
1. `python -B scratch/p18_ready.py --after-generation` → READY.
2. Quality report and `quality.json`.
3. `render_views.py --input data/raw/replication --out data/replication/views --clean-out data/replication --setup-texts configs/monitor/setup_texts.json --labels data/replication/labels.csv --no-split --seed 20261023`, then the RQ0.3 grep check.
4. Monitor run on B (384 calls ≈ 141 min; needs the lead's OK).
5. `signals_from_clean.py`.
6. `analyse_replication_22.py`.

## 9. Files to commit

- `scripts/render_views.py`, `core/evidence/signals.py`
- `scripts/signals_from_clean.py`, `scripts/analyse_replication_22.py`, `study_2_2_views/replication.py`
- `scratch/p18_ready.py`, `tests/test_replication22.py`
- `notes/DEVLOG.md`, `notes/reports/18c_replication_code_22.md`

## 10. Commit line

`Commit: feat: add split-free Study 2.2 replication analysis, one-group C-mismatch and frozen-baseline signals`
