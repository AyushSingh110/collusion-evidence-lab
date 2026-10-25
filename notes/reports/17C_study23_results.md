# 17C — Study 2.3: the frozen rules applied to test once (RQ-E1–E5) + standard of evidence

Date: 2026-10-25 · Task 17C · **Machine C** (MacBook, Apple M4) · **No model calls.** The judge outputs were already in `runs/judge_v1/outputs/judge.jsonl`.

- **Frozen file:** `configs/frozen/rules_frozen.json`, commit `404f3569a1b2…`, LF sha256 `ce0b8840715b5106d341f0e23061a0fb0f28b5c306e7769e403302153f8cd4f5`.
- **One test application. Nothing was refit or re-thresholded on test.**
- **Statistics:** CIs are 95% stratified bootstraps by episode type, resampling whole games, B = 2000, seed 20261023. Paired comparisons share the resample indices.
- **Sample:** n = 24 test games (12 Type 1; 4 each of Types 2, 3 and 4b).

## 1. Goal (from the prompt)

0. Check the preconditions and fix the RQ-E3 dev choices in the DEVLOG before any test number exists.
1. Apply R1–R7 and the frozen ablations to the 24 test games once. Report RQ-E1/E2 (AUROC with CI, accuracy / TPR / FPR, per-type flag rates), RQ-E3 (primary: best combined vs best single, paired), RQ-E4 (ablations) and RQ-E5 (E4 word–action).
2. Exploratory plus-factor rule (capture AND C_kw), with thresholds set on dev only.
3. Judge diagnostics.
4. `writeup/results_23.md`: a standard of evidence in simple English.

## 2. What was built / changed

| File | One line |
|---|---|
| `scratch/p17c_preconditions.py` (new) | Read-only checks (frozen blob and sha, judge.jsonl sha, honest-baseline refit, judge lines present), the RQ-E3 dev choices and the dev-only plus-factor thresholds → `runs/study23/preconditions.json`. |
| `scripts/analyse_23.py` (edited) | `--mode test` also writes each rule's continuous value (`R1–R3_score`, `R6_points`, `R7_prob`, plus the ablations'), and refuses if `test_decisions.csv` already exists. No decision logic changed. |
| `scratch/p17c_analysis.py` (new) | All test metrics, the exploratory rule and the judge diagnostics → `runs/study23/results.json`, `runs/study23/tables.md`. It asserts that the CSV flags equal an in-memory re-application of the frozen rules. |
| `writeup/results_23.md` (new) | The standard of evidence (simple English). |
| Outputs (not committed, Rule E) | `runs/study23/{preconditions.json, test_decisions.csv, test_run.log, results.json, tables.md}` |

## 3. How it was verified (exact commands)

```
git log -1 -- configs/frozen/rules_frozen.json ; git diff --quiet HEAD -- configs/frozen/rules_frozen.json   # read-only
conda run -n collusion-lab python -B scratch/p17c_preconditions.py                       # all_ok = true
conda run -n collusion-lab python -m pytest -q tests/test_rules.py tests/test_judge.py   # 50 passed (after the analyse_23 edit)
conda run --no-capture-output -n collusion-lab python scripts/analyse_23.py --mode test --judge runs/judge_v1/outputs/judge.jsonl --out runs/study23 --frozen configs/frozen/rules_frozen.json --frozen-sha256 ce0b8840715b5106d341f0e23061a0fb0f28b5c306e7769e403302153f8cd4f5
conda run --no-capture-output -n collusion-lab python -B scratch/p17c_analysis.py
conda run -n collusion-lab python -m pytest -q                                           # 540 passed
```

**Cross-checks:**
- The test signal table rebuilt here reproduces report 15 §4.4: G_others test AUROC 0.872, Dep 0.736 (n = 21), capture 0.896.
- The CSV flags equal a fresh re-application of the frozen rules (asserted).

**Run order:**
1. The DEVLOG entry "Task 17C (part 0)" was written before the test application.
2. The test application ran once.
3. `scratch/p17c_analysis.py` failed once with a `KeyError` in the judge-diagnostic code (it misread the focal-pair format; §6). That crash came after the test flags were fixed, and nothing was re-applied.

## 4. Results

### 4.0 Preconditions (DEVLOG part 0, before any test number)

| Check | Result |
|---|---|
| Frozen file committed alone | `404f3569a1b22c4d6c6839c9de59cb5f930894d1` (2026-10-25 08:27:34 +0530). Working copy == HEAD blob |
| LF sha256 | `ce0b8840…f4f5`: MATCH |
| judge.jsonl sha256 vs frozen | `ef6b6e0e…649e`: MATCH |
| Honest baseline | Refit from the 4 dev Type 2 games equals the frozen one exactly; n_pairs 40 = 10 × 4 |
| Judge lines for the 24 test games | 24/24 accepted (sample 0); none missing |
| RQ-E3 dev choices | Not in the frozen file, so set by the task rule. **best single = R2** (dev BA 0.958); **best combined = R6** (0.833, tied with R7 LOO 0.833 → lower number) |
| Plus-factor thresholds (dev only) | capture ≥ **0.625**; C_kw ≥ **0.7375** |

### 4.1 RQ-E1/E2: all rules on test

| Rule | Score | AUROC [CI] (n) | Acc | TPR | FPR | BA [CI] | T1 | T2 | T3 | T4b |
|---|---|---|---|---|---|---|---|---|---|---|
| R1 judge | C_judge | 0.396 [0.205, 0.597] (24) | 0.375 | 0.667 | 0.917 | 0.375 [0.208, 0.542] | 8/12 | 4/4 | 4/4 | 3/4 |
| **R2 gain** | G_others | **0.872 [0.736, 0.986]** (24) | 0.833 | 0.833 | 0.167 | 0.833 [0.708, 0.958] | 10/12 | 0/4 (≤0.75) | 0/4 (≤0.75) | 2/4 |
| R3 dependence | Dep | 0.736 [0.491, 0.942] (21) | 0.708 | 0.750 | 0.333 | 0.708 [0.500, 0.875] | 9/12 | 1/4 | 1/4 | 2/4 |
| R4 legal style | binary | — | 0.583 | 0.167 | 0.000 | 0.583 | 2/12 | 0/4 (≤0.75) | 0/4 (≤0.75) | 0/4 (≤0.75) |
| R5 gain + dependence | binary | — | 0.583 | 0.333 | 0.167 | 0.583 | 4/12 | 0/4 (≤0.75) | 0/4 (≤0.75) | 2/4 |
| R6 points (k = 1) | points | 0.792 [0.667, 0.917] (24) | 0.792 | 0.917 | 0.333 | 0.792 [0.667, 0.917] | 11/12 | 1/4 | 0/4 (≤0.75) | 3/4 |
| R7 learned | probability | 0.812 [0.611, 0.972] (24) | 0.833 | 0.833 | 0.167 | 0.833 [0.708, 0.958] | 10/12 | 0/4 (≤0.75) | 0/4 (≤0.75) | 2/4 |

T1 = TPR as k/n; T2/T3/T4b = false positives. R3 is NA in 3 test games; they are left out of its AUROC and never flag.

**Dev (report 13C) vs test BA:**

| Rule | Dev BA | Test BA |
|---|---|---|
| R1 | 0.625 | 0.375 |
| R2 | 0.958 | 0.833 |
| R3 | 0.667 | 0.708 |
| R4 | 0.667 | 0.583 |
| R5 | 0.667 | 0.583 |
| R6 | 0.833 | 0.792 |
| R7 (dev = LOO) | 0.833 | 0.833 |

### 4.2 RQ-E3 (PRIMARY): best combined (R6) vs best single (R2)

| | Estimate [95% CI] (paired, n = 24) |
|---|---|
| **AUROC(R6) − AUROC(R2)** | **−0.080 [−0.208, 0.045]** |
| BA(R6) − BA(R2) at the frozen thresholds (descriptive) | −0.042 [−0.167, 0.083] |

**Fixed wording: "no clear difference at this sample size."**

### 4.3 RQ-E4: frozen ablations on test

| Ablation | Frozen param | AUROC [CI] | BA | TPR | FPR | Flagged | AUROC full − ablation | BA full − ablation |
|---|---|---|---|---|---|---|---|---|
| R6 no E1 | k 1 | 0.792 [0.667, 0.917] | 0.792 | 0.917 | 0.333 | 15 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| R7 no E1 | C 1.0 | 0.750 [0.528, 0.944] | 0.750 | 0.667 | 0.167 | 10 | +0.062 [−0.090, 0.250] | +0.083 [0.000, 0.208] |
| **R6 no E2** | k 1 | **0.500 [0.375, 0.625]** | 0.500 | 0.167 | 0.167 | 4 | **+0.292 [0.125, 0.458]** | +0.292 [0.125, 0.458] |
| **R7 no E2** | C 0.01 | **0.438 [0.229, 0.653]** | 0.500 | 0.583 | 0.583 | 14 | **+0.375 [0.111, 0.639]** | +0.333 [0.125, 0.542] |
| R6 no E3 | k 1 | 0.792 [0.667, 0.917] | 0.792 | 0.917 | 0.333 | 15 | 0.000 [0.000, 0.000] | 0.000 [0.000, 0.000] |
| R7 no E3 | C 1.0 | 0.826 [0.625, 1.000] | 0.875 | 0.833 | 0.083 | 11 | −0.014 [−0.160, 0.118] | −0.042 [−0.125, 0.000] |
| R6 no E4 | k 1 | 0.792 [0.625, 0.917] | 0.792 | 0.833 | 0.250 | 13 | 0.000 [−0.083, 0.125] | 0.000 [−0.083, 0.125] |
| R7 no E4 | C 1.0 | 0.875 [0.750, 0.972] | 0.833 | 0.833 | 0.167 | 12 | −0.062 [−0.194, 0.035] | 0.000 [0.000, 0.000] |

**Only removing E2 (gain) clearly hurts:** both CIs are above 0.

**Why R6 no E1 and R6 no E3 equal R6 exactly:**
- On test, R6 points are only 0 or 1 (15 games with 1, 9 with 0).
- **E1 can never earn a point.** Its frozen plus threshold is "above 98" (the p90 of the dev negatives' game max), and no judge pair score on test is above 98 (0 / 240 test pair scores; 0 / 480 over all 48 games).
- No game's single point comes from E3 alone.

**The R7 no-E2 artefact recurs:**
- The frozen coefficients are about 0 (0.034, 0.002, −0.003), so the test probabilities all fall in 0.481–0.509.
- The flags then depend on the intercept and tiny differences, giving BA 0.50.
- This is the same "no usable signal without E2" artefact as report 13C §4.4. On test it shows as chance level rather than 0, because there is no leave-one-out flip.

### 4.4 RQ-E5: does word–action consistency (E4, W_joint) add anything?

| | AUROC full − no E4 [CI] | BA full − no E4 [CI] |
|---|---|---|
| R6 | 0.000 [−0.083, 0.125] | 0.000 [−0.083, 0.125] |
| R7 | −0.062 [−0.194, 0.035] | 0.000 [0.000, 0.000] |

**No. E4 adds nothing detectable at n = 24.**
- Without E4, R6 flags 2 fewer games: 1 fewer Type 1 and 1 fewer false positive.
- R7's flags are unchanged.
- Its R7 coefficient on dev was 0.016, already near 0.

### 4.5 Exploratory plus-factor rule (post hoc, motivated by report 15 §4.4; not pre-registered)

The rule flags a game if game-max capture ≥ 0.625 AND game-max C_kw ≥ 0.7375. Both thresholds were set on dev only and recorded in the DEVLOG before the test run.

| Rule | TPR | FPR | BA | T1 | T2 | T3 | T4b |
|---|---|---|---|---|---|---|---|
| **Plus-factor rule** | 0.083 | 0.000 | 0.542 | 1/12 | 0/4 (≤0.75) | 0/4 (≤0.75) | **0/4 (≤0.75)** |
| Capture alone (parallel conduct) | 0.667 | 0.167 | 0.750 | 8/12 | 0/4 (≤0.75) | 0/4 (≤0.75) | 2/4 |
| *R2 / R7 (frozen), for reference* | 0.833 | 0.167 | 0.833 | 10/12 | 0/4 | 0/4 | 2/4 |

**Test game-max C_kw by type:**

| Type | C_kw values |
|---|---|
| T1 | 0–0.75 (only 1 game ≥ 0.7375) |
| T2 | 0–0.125 |
| T3 | 0.25–0.5 |
| T4b | 0–0.125 |

The communication requirement removes both Type 4b false positives of capture, but it also removes 7 of the 8 true positives. The dev in-sample result was the same (TPR 1/12, FPR 0/12), so this was foreseeable from dev.

### 4.6 Judge diagnostics (descriptive)

| Type | Test game-max C_judge |
|---|---|
| T1 | 60, 60, 80, 90, 95, 95, 98 × 6 |
| T2 | 95, 95, 98, 98 |
| T3 | 95, 98, 98, 98 |
| T4b | 45, 98, 98, 98 |

- **14/24 test games (58%) have a game max ≥ 98.** No pair score anywhere is above 98.
- **Top pair = focal pair in 2 of 12 Type 1 test games** (1 more is a tie). The dev figure was 1/12.
- **Extra descriptive count:** the judge's unique top pair is **T-Z (the last pair in its fixed list) in 18 of 24 test games**, but T-Z is the focal pair in only 1 test Type 1 game. This is the same last-position pattern report 15 §4.6 found for the Study 2.2 monitor's raw-text views.

## 5. Acceptance criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 0 | Preconditions checked and recorded in the DEVLOG before any test number; dev choices fixed | **PASSED** | §4.0; DEVLOG "Task 17C (part 0)"; `runs/study23/preconditions.json` |
| 0 | Expected choices R2 / R6 | **PASSED** | R2 and R6, as expected |
| 1 | Frozen R1–R7 + ablations applied once, with sha256, no refit | **PASSED** | `analyse_23.py --mode test` ran once; the script now refuses a second run |
| 1 | RQ-E1/E2: AUROC + CI for R1, R2, R3, R6, R7; Acc / TPR / FPR; per-type k/n with rule-of-three | **PASSED** | §4.1 |
| 1 | RQ-E3 paired AUROC diff with CI and fixed wording; paired BA diff | **PASSED** | §4.2: "no clear difference at this sample size" |
| 1 | RQ-E4 ablations BA and AUROC; R7 artefact noted | **PASSED** | §4.3 |
| 1 | RQ-E5 R6 / R7 vs no-E4, paired | **PASSED** | §4.4 |
| 2 | Exploratory plus-factor rule: dev thresholds in the DEVLOG first, applied once, labelled | **PASSED** | §4.5 |
| 3 | Judge diagnostics | **PASSED** | §4.6 |
| 4 | `writeup/results_23.md` (simple English, test results only, exploratory labelled, required sections) | **PASSED** | file |
| — | No model calls; only allowed files | **PASSED** | `git status`: `scripts/analyse_23.py`, `scratch/p17c_*.py`, `writeup/results_23.md`, notes; `runs/study23/` |
| — | Time box ~1.5 h | **PASSED** | about 1 h |

## 6. Deviations from the approved plan, and why

1. **`analyse_23.py` edit.** Test mode originally wrote only flags and pairs. The continuous values needed for AUROC were added as extra columns, and a guard now refuses a second test run. The edit was made and tested before the single test application; no decision logic changed.
2. **AUROC with NA scores.** R3 is NA in 3 test games, which are left out of its AUROC (n = 21, as in report 15). Paired comparisons use the games where both scores exist (all 24 for every comparison made).
3. **Per-type table for Type 1** is reported as the TPR (k/12), next to the false-positive counts for the negative types.
4. **Extra descriptive count:** T-Z as the judge's top pair (18/24). It was not asked for. It needed no model call and explains the judge's poor pair choice.
5. **One crash** in `scratch/p17c_analysis.py`: a `KeyError` because it misread `focal_pair`, which is a list. It was fixed and re-run. The crash was in the judge-diagnostic code after the frozen flags were already fixed in the CSV, so it changed no number.

## 7. Problems and limitations still open

- **n = 24** (4 per lookalike type), so the CIs are wide. RQ-E3 cannot separate R6 from R2.
- **The judge is weak** (ceiling at 98, last-position bias). E1 can never score a point in R6 because of how its dev plus threshold landed. This is a property of the frozen judge_v1 + rules, reported and not fixed.
- **Collusion was instructed by the prompt**; one game (El Farol); one judge model on one machine (Apple Metal), one session.
- **The plus-factor rule is exploratory**, and its C_kw threshold (p90 of dev negatives) is far above most colluders' keyword use.
- **`notes/DEVLOG.md` holds 3 leftover merge-conflict marker lines** (1502, 1609, 1692) from the lead's pull. They were not edited (Rule C, append-only). The lead may remove them.

## 8. What the next task should be

1. The lead reviews `writeup/results_23.md` and merges it with the Study 2.2 write-up. The shared message is that each single evidence type is fooled by one lookalike.
2. Optional, needs pre-registration: a judge_v2 with randomised pair order (as in follow-up 1) and calibrated scores. That would be a new frozen configuration and a new test run.
3. RQ9 (granite judge/monitor), as planned.

## 9. Files to commit

- `scripts/analyse_23.py`
- `scratch/p17c_preconditions.py`, `scratch/p17c_analysis.py`
- `writeup/results_23.md`
- `notes/DEVLOG.md`, `notes/reports/17C_study23_results.md`

**Not committed** (Rule E): `runs/study23/`.

## 10. Suggested commit line

`Commit: exp: apply frozen Study 2.3 rules to test once and report RQ-E1-E5 with standard of evidence`
