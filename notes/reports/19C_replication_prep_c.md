# 19C — Replication preparation on machine C: machine-id fix, Study 2.3 replication code, DRAFT amendment (granite)

Date: 2026-10-25 · Task 19C · **Machine C** (MacBook, Apple M4)

- **No model calls.**
- **No replication data read:** none exists on this machine (`data/replication/` and `data/raw/replication/` are absent).
- No committed prereg, frozen file, manifest, `study_2_2_views/*` or generator file was changed.

## 1. Goal (from the prompt)

1. Make `COLLUSION_LAB_MACHINE=C` visible to non-interactive shells (`~/.zshenv`), and prove it.
2. Write Study 2.3 replication code. It applies the frozen rules to any game set and computes prereg §4 exactly: E1, E2, E3, E3b, E4, primary and sensitivity, plus the 17C plus-factor rule as secondary. It uses the frozen honest baseline. Tests use synthetic data, plus a reproduction of 17C.
3. Draft (not binding) an amendment adding granite3.3:8b as a second replication monitor, with G1–G4.
4. Print a dry-run plan for machine C.

## 2. What was built

| File | One line |
|---|---|
| `~/.zshenv` (new, outside the repo) | `export COLLUSION_LAB_MACHINE=C` (`~/.zshrc` unchanged). |
| `study_2_3_evidence/replication.py` (new) | Additive. Contains: `check_prereg` (LF sha256 + equality with the committed blob); `frozen_baseline` (from the frozen file, never refit); `build_games` (pair tables with C_judge); `apply` (wraps `rules.apply_frozen` for any ids; refuses a sha mismatch and frozen-dev ids); the decision rules `verdict_e1` / `verdict_e2` / `verdict_diff` with the prereg wording; `analyse_set` (E1, E2, E3 = R6 − R2, E3b = R7 − R2, E4, all rules' flags per type, secondary plus-factor rule); `analyse_replication` (primary + sensitivity); `read_quality_fail`. |
| `scripts/analyse_replication_23.py` (new) | CLI for the one replication analysis. It refuses before computing anything if: the prereg ≠ blob or its sha256 differs; the frozen file's sha256 differs; judge lines are not judge_v1 with the frozen digest; a judge line is outside the label set; a clean file is missing; an earlier `results.json` exists. Writes `decisions.csv` and `results.json`. |
| `scripts/run_replication_c.py` (new, thin wrapper) | Default: prints the machine-C plan. `--run judge --yes` runs `judge.run_judge` on the replication label ids (`run_judge.py` only accepts split ids); it refuses unless the machine is C, the labels and clean files exist and the prereg matches. The granite command is printed only once the amendment is committed. |
| `tests/test_replication_23.py` (new) | 27 tests (§3). |
| `configs/prereg_replication_amendment1.md` (new, **DRAFT**) | Second monitor granite (exact 15C manifest), 48 × V1–V4 = 192 calls on C, G1–G4 with decision rules, descriptive measures, order of work, limitations. LF sha256 `778cf66b03bdea1f27a121aed59962ae5f95ea2e21c6f9fd3902b08f8bc7cbf7`. |

`rules.py`, `judge.py` and `scripts/analyse_23.py` are unchanged.

## 3. How it was verified (exact commands)

```
git log -1 -- configs/prereg_replication.md ; git diff --quiet HEAD -- configs/prereg_replication.md          # read-only
zsh -c 'echo $COLLUSION_LAB_MACHINE'                                                                            # C
conda run -n collusion-lab python -c "import os; print(os.environ.get('COLLUSION_LAB_MACHINE'))"                # C
conda run -n collusion-lab python -m pytest -q tests/test_replication_23.py                                     # 27 passed
conda run -n collusion-lab python -m pytest -rs -v tests/test_replication_23.py -k 17c                          # PASSED (not skipped)
conda run -n collusion-lab python scripts/run_replication_c.py                                                  # dry-run plan (§4.4)
conda run -n collusion-lab python scripts/run_replication_c.py --run judge                                      # REFUSED: no labels file
conda run -n collusion-lab python -m pytest -q                                                                  # 578 passed, 1 skipped (Windows-only test)
```

**The 27 tests:**

1. **Every decision branch:**
   - E1: confirmed / not confirmed, including a lower bound exactly 0.5;
   - E2: confirmed (CI includes 0.5, including the edges) / confirmed (below chance) / not confirmed;
   - E3: replicated / not replicated (including a bound exactly 0) / reversed;
   - no CI → refusal.
2. **`analyse_set` on synthetic decisions:**
   - E1 confirmed, E2 confirmed, E3 and E3b reversed;
   - E2 below chance, E1 not confirmed, E3 replicated;
   - E4 k/n with the rule-of-three bound; the plus-factor rule flags Type 1 but not Type 4b (capture without keywords);
   - NA scores are counted and left out;
   - sensitivity with, without and with an empty quality file, and with unknown ids (refused); quality-file formats.
3. **Refusals:**
   - prereg: wrong sha, missing file, working copy ≠ blob (a CRLF blob is accepted);
   - frozen file: wrong sha256;
   - frozen dev ids in the set;
   - the script: wrong frozen sha, wrong prereg sha, foreign judge digest, a second run (nothing is written on refusal);
   - the wrapper: not machine C, no labels file, prereg mismatch; it never prints the granite command before the amendment is committed.
4. **Baseline is loaded, not refit:** `fit_honest_baseline` is monkeypatched to fail, in the unit test and in the end-to-end script run. G_honest is computed with the frozen μ / σ, and `results.json` records the frozen baseline.
5. **End to end:** 16 synthetic games with new ids, the real committed frozen file and prereg, one missing judge line (counted, R1 NA), a quality file (sensitivity n = 15).
6. **Earlier behaviour reproduced (report 17C):** on the 24 original test games with the existing local files, every flag and continuous score equals `runs/study23/test_decisions.csv`. The AUROC estimates and CIs of R1, R2, R3, R6, R7, the R6 − R2 estimate and CI, every per-type k/n and the plus-factor per-type table equal `runs/study23/results.json` (abs 1e-12).

   On these 17C inputs the new wording gives E3 = "not replicated", the replication wording for 17C's "no clear difference". The test is skipped where those uncommitted files are absent; on machine C it ran and passed.

## 4. Results

### 4.1 Preconditions (DEVLOG "Task 19C (part 0)", written before any code)

`configs/prereg_replication.md`:
- committed alone in `2bc3d3aa19edb0aa43ccf5a6cb09e37f2dd2deeb` (2026-10-25 09:55:12 +0530);
- working copy == blob;
- LF sha256 `d9d25b583b1d6052778f8668d8a55d7680069ba1ce6e9f8b61a72c49e1f7a1f9`.

### 4.2 Machine-id fix

| Check | Output |
|---|---|
| `zsh -c 'echo $COLLUSION_LAB_MACHINE'` (fresh, non-interactive) | `C` |
| `conda run -n collusion-lab python -c "…os.environ.get('COLLUSION_LAB_MACHINE')"` | `C` |
| A new tool-shell call (`echo $COLLUSION_LAB_MACHINE`) | `C` |
| The tool shell that wrote the file (environment taken before) | empty, as expected; later calls see `C` |

`cache/llm/m_5acffc7a/` (96 entries) holds the task 15C granite calls and was left untouched.

### 4.3 Analysis contract (what `analyse_replication_23.py` computes)

| Item | Definition (prereg §4) |
|---|---|
| E1 | AUROC(R2 score = game-max G_others), CI above 0.5 → confirmed, else not confirmed |
| E2 | AUROC(R1 score = game-max C_judge): includes 0.5 → confirmed; below → confirmed (below chance); above → not confirmed |
| E3 | AUROC(R6 points) − AUROC(R2), paired: above 0 → replicated; includes 0 → not replicated; below 0 → reversed |
| E3b (secondary) | AUROC(R7 probability) − AUROC(R2), same wording |
| E4 (descriptive) | flag k/n per type for R2 and R6, with the rule-of-three bound for 0/n (all rules' per-type tables are also stored) |
| Primary / sensitivity | all games / without the quality-fail ids from the quality file |
| Secondary | plus-factor rule of 17C (capture ≥ 0.625 AND C_kw ≥ 0.7375), TPR / FPR / per type |
| Baseline | the frozen file's `honest_baseline` (μ 0.448, σ 1.620, 40 pairs), never refit |

### 4.4 Dry-run plan for machine C (printed, NOT run)

| Step | Needs | Command | Estimate |
|---|---|---|---|
| Files from B | `data/replication/clean/` (CleanGames; B renders with `--clean-out data/replication`), `data/replication/views/` (V1–V4, granite only), `data/replication/labels.csv` (sha256 `27a0d4bf…` in report 18b), `data/replication/quality_fail.json` | — | — |
| 1. Judge | clean + labels | `python -u scripts/run_replication_c.py --run judge --yes` → `runs/judge_v1_replication/` | 48 × 27.5 s ≈ **22 min** (13C median; budget ~25 min) |
| 2. Analysis | judge output + quality file | `python scripts/analyse_replication_23.py --clean-dir data/replication/clean --labels data/replication/labels.csv --judge runs/judge_v1_replication/outputs/judge.jsonl --quality data/replication/quality_fail.json` | seconds |
| 3. Granite (only if the amendment is committed) | views V1–V4 | `python -u scripts/run_monitor.py --input data/replication/views --views V1,V2,V3,V4 --run-id rq9_granite_replication --prompt monitor_v3_pairs_ctx16k_granite --sec-per-call 55 --yes` | 192 calls; 15C per-view means → **172 min ≈ 2.9 h** (budget ~3.5 h) |

Both model steps are over 15 min, so each needs the lead's OK (Rule H).

## 5. Acceptance criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 0 | Prereg commit + LF sha256 in the DEVLOG first | **PASSED** | §4.1 |
| 1 | `~/.zshenv` set; `zsh -c` and `conda run` print C; old shard untouched and recorded | **PASSED** | §4.2; DEVLOG |
| 2 | Frozen rules applied to any ids with any judge / labels file; never refit; refuses on frozen-sha or prereg-blob mismatch | **PASSED** | `replication.apply`, `check_prereg`; tests |
| 2 | Script computes exactly prereg §4 (E1, E2, E3, E3b, E4), primary + sensitivity, plus-factor rule secondary | **PASSED** | §4.3 |
| 2 | Code signals with the original frozen baseline | **PASSED** | `frozen_baseline`; monkeypatched-refit tests |
| 2 | Synthetic tests: every outcome branch, refusals, baseline loaded not refit | **PASSED** | 27 tests |
| 2 | Earlier behaviour byte-identical, proven by reproducing 17C's test tables | **PASSED** | `test_reproduces_17c_test_tables` (ran on C); `rules.py` / `judge.py` / `analyse_23.py` unchanged |
| 3 | Draft amendment: dated, before any replication data, exact granite manifest, 192 calls on C, G1–G4 decision rules, descriptive, limitation, STOP | **PASSED** | `configs/prereg_replication_amendment1.md` (not committed) |
| 4 | Dry-run plan with files, judge and granite commands and estimates | **PASSED** | §4.4 |
| — | No model calls; no replication data read; only allowed files | **PASSED** | `git status` |
| — | Time box ~2 h | **PASSED** | about 1 h |

## 6. Deviations from the approved plan, and why

1. **G2 has a full outcome map.** The task gives "CI includes 0.5 → confirmed". The draft adds "above 0.5 → not confirmed" and "below 0.5 → not confirmed (below chance)" so every outcome has a fixed label, as in the base prereg.
2. **The G4 note** ("confirmed" = no detected difference, not equivalence) was added to prevent over-reading.
3. **Quality-file format.** The prereg names no format, so this code fixes one: a JSON list of ids, or `{"quality_fail": [...]}`. Machine B must write it in that form, or C converts the quality report into it (no relabelling).
4. **Assumed paths** for the replication data on C: `data/replication/clean`, `data/replication/views`, `data/replication/quality_fail.json`. These are defaults and can be overridden by options.
5. **The wrapper only runs the judge.** The granite part only prints its command, and only once the amendment is committed, because granite needs the lead's decision and OK.
6. **Extra safety refusal:** the analysis refuses any game id that is a frozen DEV game, since the rules were fitted on those.

## 7. Problems and limitations still open

- **The amendment is a DRAFT** and changes nothing until the lead commits it alone, before rendering.
- **The 17C reproduction test** only runs where the uncommitted 17C outputs exist (machine C).
- **The quality file and folder layout must be agreed with machine B** (§6.3–4).
- **The llama inputs for G3 / G4** come from machine B's replication monitor output. The G1–G4 analysis code is not written yet (base prereg order of work: it is written and tested before reading monitor output; that is a later task, if the amendment is approved).

## 8. What the next task should be

1. **Lead:** review the draft amendment. If approved, commit it **alone**, before any replication view is rendered.
2. **Lead:** commit the code files of this task.
3. **Machine B:** generation, merge, quality, rendering (base prereg §5), then transfer the files in §4.4 to C.
4. **Machine C:** judge run (≈ 22 min, after the OK), then the one analysis run. If the amendment is approved: the G1–G4 analysis code (synthetic tests first), then the granite run (≈ 2.9 h, after the OK).

## 9. Files to commit

**Code and notes (now):**
- `study_2_3_evidence/replication.py`
- `scripts/analyse_replication_23.py`, `scripts/run_replication_c.py`
- `tests/test_replication_23.py`
- `notes/DEVLOG.md`, `notes/reports/19C_replication_prep_c.md`

**Separately, NOT to be committed until the lead approves (then alone):**
- `configs/prereg_replication_amendment1.md`

**Never committed:** `~/.zshenv` (outside the repo), `cache/llm/m_5acffc7a/` (Rule E).

## 10. Suggested commit line

`Commit: feat: add Study 2.3 replication analysis and machine-C runner (frozen rules, any game set, no refit)`
