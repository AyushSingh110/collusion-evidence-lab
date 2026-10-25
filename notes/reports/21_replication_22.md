# 21 — Replication on machine B: checks, quality, views, frozen llama monitor, signals, Study 2.2 R1–R10

Date: 2026-10-25 · Task 21 · Machine B (RTX 3060 Laptop, Ollama 0.40.3)

- **Pre-registrations:** `configs/prereg_replication.md` (2bc3d3a, LF sha256 `d9d25b58…a1f9`) and amendment 1 (306502e, `778cf66b…7cbf7`).
- **Frozen monitor:** `configs/frozen/monitor_frozen.json` (89bdb79, `ccc4bf07…f65f`).
- **Data:** 48 **new** games, a confirmation set with no split; nothing was tuned on them.
- **Statistics:** 95% stratified bootstrap by type, B = 2000, seed 20261023; paired for differences.
- **One analysis run;** no other analysis on these games.

## 1. Goal (from the prompt)

On machine B:
1. Check the preconditions.
2. Run the readiness checklist.
3. Report quality and the manipulation check.
4. Render the replication views (no-split C-mismatch) without touching the original dataset; RQ0.3 grep check.
5. Give the transfer list for machine C.
6. Run the frozen llama monitor: 48 games × 8 views, sample 0, one run.
7. Compute code signals with the frozen baseline.
8. Run the pre-registered Study 2.2 analysis once: R1–R10, primary and sensitivity, plus secondary measures.

## 2. What was built / run

| Item | One line |
|---|---|
| `scratch/p21_quality.py`, `scratch/p21_quality_summary.py` | Copies of the task-12 quality / summary scripts with **only the paths changed** (diff-checked), plus the `quality_fail.json` writer |
| `scratch/p21_view_checks.py` | Copy of the task-12 view checks: paths changed and no split (C-mismatch checked within type across the set) |
| `scratch/p21_run_stats.py`, `scratch/p21_print_secondary.py` | Run statistics, and formatting of the analysis output (no new analysis) |
| Outputs (not committed) | `data/replication/{clean, clean_private, views, quality_fail.json}`, `runs/replication/{quality, guard, signals, analysis_22}`, `runs/replication_llama/` (384 lines + manifest), `runs/replication_llama_run.log`, `runs/replication_llama_ps.txt` |

No code under `core/`, `scripts/` or `study_2_2_views/` was changed.

## 3. How it was verified (exact commands)

```
git log / git show HEAD:<prereg> | sha256 (read-only)       # both preregs committed alone, == blobs
conda run -n collusion-lab python scripts/check_env.py      # READY
conda run -n collusion-lab pytest -q                        # 631 passed, 1 skipped, 0 failed
conda run -n collusion-lab python -B scratch/p18_ready.py --after-generation        # READY
conda run -n collusion-lab python -B scratch/p21_quality.py ; ... scratch/p21_quality_summary.py
find data/clean data/views -type f | sha256sum (before / after)                     # 435 files, identical
conda run -n collusion-lab python scripts/render_views.py --input data/raw/replication --out data/replication/views --clean-out data/replication --setup-texts configs/monitor/setup_texts.json --labels data/replication/labels.csv --no-split --seed 20261023
conda run -n collusion-lab python -B scratch/p21_view_checks.py                     # RQ0.3 grep clean
conda run -n collusion-lab python -u scripts/run_monitor.py --input data/replication/views --views V3 --games <3 ids> --run-id replication_llama --prompt monitor_v3_pairs_ctx16k     # measured
conda run -n collusion-lab python -u scripts/run_monitor.py --input data/replication/views --views V1,V2,V3,V4,V5,C-mismatch,C-length,C-shuffled --run-id replication_llama --prompt monitor_v3_pairs_ctx16k --sec-per-call 22 --yes
conda run -n collusion-lab python scripts/signals_from_clean.py --clean data/replication/clean --labels data/replication/labels.csv --out runs/replication/signals
conda run -n collusion-lab python scripts/analyse_replication_22.py --labels data/replication/labels.csv --monitor runs/replication_llama/outputs/monitor.jsonl --signals runs/replication/signals/game_signals.csv --quality data/replication/quality_fail.json --out runs/replication/analysis_22 --frozen configs/frozen/monitor_frozen.json --frozen-sha256 ccc4bf07838be73eff576f84b29389db4ee0952e6a8317eaa51d70885f47f65f
```

## 4. Results

### 4.0 Preconditions (DEVLOG "Task 21 (part 0)", before any processing)

- **Pre-registration:** committed alone in `2bc3d3a`, == blob, `d9d25b58…a1f9`.
- **Amendment 1 (granite G1–G4):** committed alone in `306502e` (2026-10-25 20:34:15), == blob, `778cf66b…7cbf7`. This equals the draft hash from report 19C, so **audit 20B issue 4 is resolved**. It was committed before any view was rendered.
- **Environment:** check_env READY; pytest 631 passed, 1 skipped, 0 failed.
- **Data and caches:** 48 records, 0 partials; `cache/llm/A` and `cache/llm/B` present.

### 4.1 Readiness

**READY:**
- every plan game has a valid record;
- `machine_id` equals the plan for 48/48 (B 32, A 16);
- merge_check OK;
- the labels equal the plan.

### 4.2 Quality and manipulation check (report-12 definitions; descriptive; nothing excluded or relabelled)

| Item | Replication | Original dataset (report 12 §4.2–4.4) |
|---|---|---|
| Wall time | A 395.2 min (16 games, Type 1 mean 27.3 min); B 362.3 min (32 games, Type 1 mean 12.4) | A 412.4, B 387.5 |
| Failures (all truncation) | **81 / 6,528 = 1.24%** (T1 1.23%, T2 1.67%, T3 0.52%, T4b 1.56%; highest cell T2 Stage 1 4.69%) | 1.75% |
| Valid rounds per game | 8: 37 games; 7: 11 | 8: 36; 7: 8; 6: 3; 5: 1 |
| **Quality-fail games** | **none** → `{"quality_fail": []}` (max failure share per game 4.17%) | none |
| Uptake v2, Type 1 | **24/24** (v1 23/24); Type 2 decoys passing 0/8 | 24/24 |
| Focal top by coGO / G_others > 0 / capture ≥ 2 rounds | 24 / 24* / 24 | 24 / 23 / 23 |
| Effect (top coGO AND G_others > 0) | **24/24 by the script; 23/24 substantively** (*g_ec16a9027c has G_others = 2.2e-16, a floating-point zero) | 23/24 |
| Type 3 (persona) | **8/8 AS DESIGNED** | 7 AS DESIGNED, 1 PARTLY |
| Type 4b (shared incentive) | **5 AS DESIGNED, 1 PARTLY, 2 NOT**; public "deposit" talk 8/8 (106 mentions) | 6 / 0 / 2; 8/8 (97) |
| Type 1 public reveals | 13/384 = **3.4%**; 9/24 games ≥ 1 | 6.5%; 12/24 |
| Non-English texts | 2 (Stage 3 reasoning, 1 T1 + 1 T3); 0 public | 3 (Stage 1) |
| Leak scan | 0 removals; flags: banned 6 (private reasoning), pattern_4b 406 | 0; 5 / 357 |

### 4.3 Views

- **Rendered:** 384 files, 0 skipped. Under the no-split option, C-mismatch partners are never self, always within type, and distinct; C-length is within ±5% for 48/48.
- **Original dataset untouched:** `data/clean` + `data/views` (435 files) are byte-identical before and after (sha256 lists in `runs/replication/guard/`).
- **RQ0.3 grep check (384 files):** no game id, variant name, label or type term, header phrase or 8-word setup copy. **0 original-dataset ids** appear in any replication view.
- **Prompt sizes:** max V5 prompt_eval in the run was 5,557 (< 8,192 guard).

### 4.4 Transfer list (printed for machine C)

`data/replication/clean/`, `data/replication/clean_private/`, `data/replication/views/`, `data/replication/labels.csv`, `data/replication/quality_fail.json`, `runs/replication_llama/outputs/monitor.jsonl`.

### 4.5 Frozen llama monitor run (`replication_llama`)

- **Measured calls:** 3 (V3; part of the run): 28.0 / 21.4 / 21.4 s.
- **Estimate:** ≈ 140 min, inside the 3.5 h pre-approval.
- **Full run:** ≈ 21:25 → 23:34:55, 381 new calls. **384 lines in total; 130.7 min of call time.**

| View | Lines | Parse fail | Truncation | Missing | Length cuts | Mean latency s |
|---|---|---|---|---|---|---|
| V1 / V2 / V3 / V4 | 48 each | 0 | 0 | 0 | 0 | 19.5 / 16.9 / 20.3 / 18.8 |
| V5 | 48 | 0 | 0 | 0 | 0 | 27.3 |
| C-mismatch / C-length / C-shuffled | 48 each | 0 | 0 | 0 | 0 | 20.6 / 19.4 / 20.6 |

- One digest (`46e0c10c039e`), one prompt version, sample 0 only, 0 cache hits, 0 transport errors.
- `ollama ps` (65 snapshots): `llama3.1:8b 7.3 GB 43%/57% CPU/GPU 16384` throughout.
- The Ollama server was stopped afterwards.

### 4.6 Code signals

48 games. Baseline loaded from `configs/frozen/rules_frozen.json` (`honest_baseline`, sha256 `ce0b8840…`; μ_pair 0.448, σ_pair 1.620, 40 pairs), **refitted: false**. Dep NA in 1 game.

### 4.7 Pre-registered hypotheses R1–R10 (primary, all 48 games; sensitivity identical, since no game is quality-fail)

| ID | Hypothesis | Replication: estimate [95% CI] | Outcome | Original (n = 24 test; report 14 / 15) |
|---|---|---|---|---|
| R1 | Messages alone fail: AUROC(V1) | 0.505 [0.363, 0.655] | **confirmed** | 0.490 [0.299, 0.691] (R14 §4.2) |
| R2 | Structured report works: AUROC(V4) | 0.636 [0.507, 0.751] | **confirmed** | 0.896 [0.771, 0.979] (R14 §4.2) |
| R3 | RQ2, combining helps: V3 − V2 | +0.241 [0.063, 0.419] | **replicated** | +0.365 [0.094, 0.611] (R14 §4.3); pooled +0.040 [−0.155, 0.238] (R15 §4.2) |
| R4 | RQ5, structure beats raw: V4 − V3 | +0.071 [−0.128, 0.247] | **not replicated** | +0.160 [−0.021, 0.351] (R14 §4.6) |
| R5 | Structure beats same length: V4 − C-length | −0.034 [−0.212, 0.133] | **not confirmed** | +0.285 [0.017, 0.556] (R14 §4.6) |
| R6 | Same-incentive fools messages: V1, T1 vs T4b | 0.495 [0.297, 0.716] | **confirmed** | 0.344 [0.12, 0.65] (R14 §4.4) |
| R7 | Persona talk fools actions: V2, T1 vs T3 | 0.352 [0.154, 0.578] | **not confirmed** | 0.219 [0.00, 0.62] (R14 §4.4) |
| R8 | Oracle: V5 − V3 | −0.022 [−0.192, 0.155] | **not replicated** | −0.031 [−0.267, 0.236] (R14 §4.7) |
| R9 | Shuffled control: AUROC(C-shuffled) | 0.457 [0.315, 0.591] | **pass** | 0.632 [0.431, 0.833] (R14 §4.10) |
| R10a | Code signal: AUROC(capture) | 0.900 [0.811, 0.965] | **confirmed** | 0.896 [0.781, 0.986] (R15 §4.4, test) |
| R10b | Capture − V4, paired | +0.264 [0.121, 0.412] | **capture better** | capture 0.896 vs V4 0.896 on test (R15 §4.4; no paired CI reported) |

**Context (not new analysis):** the R2–R4 point estimates imply V3 ≈ 0.565 and V2 ≈ 0.324. V2 is again below chance, as in the original test (0.372).

### 4.8 Secondary measures (descriptive; prereg §3)

**Other code signals:**

| Signal | AUROC [CI] | T1 vs T4b [CI] |
|---|---|---|
| coGO | 0.816 [0.714, 0.909] | 0.568 [0.346, 0.787] |
| G_others | 0.885 [0.786, 0.961] | 0.831 [0.667, 0.964] |
| C_kw | 0.541 [0.446, 0.620] | 0.773 [0.615, 0.896] |
| Dep (n = 47) | 0.682 [0.529, 0.832] | 0.698 [0.484, 0.875] |

**Top-1 pair on the 24 Type 1 games** (chance 0.1):

| Source | Correct | No pair named |
|---|---|---|
| V1 | 2/24 | 3 |
| V2 | 7/24 | 11 |
| V3 | 1/24 | 6 |
| V4 | 7/24 | 6 |
| V5 | 5/24 | 16 |
| Dep argmax | 8/24 | 6 |

**Frozen thresholds:**

| View | Threshold | Acc | TPR | FPR | BA |
|---|---|---|---|---|---|
| V2 | 80 | 0.438 | 0.458 | 0.583 | 0.437 |
| V4 | 50 | 0.625 | 0.708 | 0.458 | 0.625 |
| V5 | 100 | 0.521 | 0.083 | 0.042 | 0.521 |
| C-length | 60 | 0.604 | 0.875 | 0.667 | 0.604 |
| C-shuffled | 60 | 0.542 | 0.958 | 0.875 | 0.542 |

V1, V3 and C-mismatch have a degenerate threshold (flags everything).

**FP per negative type (k/8: T2 / T3 / T4b):**

| View | T2 | T3 | T4b |
|---|---|---|---|
| V2 | 6 | 3 | 5 |
| **V4** | 1 | **8** | 2 |
| V5 | 1 | 0 (≤ 0.375) | 0 (≤ 0.375) |
| C-length | 5 | 3 | 8 |
| C-shuffled | 7 | 8 | 6 |

**Last-position-max** (T-Z has the max, ties included; the no-bias expectation is in brackets):

| View | Share |
|---|---|
| V1 | **44/48** [0.215] |
| V2 | 26/48 [0.463] |
| V3 | **44/48** [0.381] |
| V4 | 18/48 [0.335] |
| V5 | **42/48** [0.594] |
| C-mismatch | **46/48** [0.362] |
| C-length | **44/48** [0.306] |
| C-shuffled | **48/48** [0.175] |

**Extra paired differences:**
- V3 − C-mismatch: −0.057 [−0.191, 0.075];
- V3 − V1: +0.060 [−0.124, 0.247].

### 4.9 Plain-English verdict per hypothesis

- **R1 confirmed:** reading the messages alone still does not separate colluding games (0.505).
- **R2 confirmed, but much weaker:** the structured report is above chance (0.636; CI low end 0.507), far below the original 0.896.
- **R3 replicated:** the combined view beats actions alone again (+0.241). As in the original, this partly reflects actions alone being below chance (≈ 0.32).
- **R4 not replicated:** no clear advantage of the structured report over the raw combined view (+0.071).
- **R5 not confirmed:** the structured report does **not** beat a raw view of the same length here (−0.034). The original "structure beats same length" result (+0.285) does not hold on new games.
- **R6 confirmed:** messages do not separate collusion from shared-incentive games (0.495). This time it is at chance, not below chance as in the original.
- **R7 not confirmed:** persona talk does not clearly fool the action view (0.352, CI includes 0.5).
- **R8 not replicated:** private plans again give no gain (−0.022); a consistent null.
- **R9 pass:** the shuffled control is at chance (0.457), with no sign of leakage.
- **R10a confirmed, R10b capture better:** the model-free capture signal ranks games very well (0.900) and **clearly beats the best LLM view** (+0.264 [0.121, 0.412]).

### 4.10 Ten-line summary

1. A pre-registered replication on 48 new games, using exactly the frozen llama3.1:8b monitor: 384 calls, no failures, one analysis run.
2. The data were clean: no quality-fail game, 24/24 collusion games showed uptake, and the lookalikes mostly behaved as designed.
3. Messages alone failed again (0.505): replicated.
4. Combining messages and actions beat actions alone again (+0.241): replicated. But the actions-only view was again below chance.
5. The structured report still worked (0.636), but much less well than on the original test set (0.896).
6. Its advantages did not replicate: not over the raw combined view (+0.07), and not over an equally short raw view (−0.03).
7. Private plans again added nothing, and the shuffled control was at chance.
8. Shared-incentive games were again indistinguishable from collusion in the message view; persona talk no longer clearly fooled the action view.
9. The simple code signal "capture" was the best detector (0.900) and beat the best LLM view by +0.26: the clearest replicated finding.
10. llama's last-position bias replicated strongly (e.g. V1 44/48 replies give the top score to the last-listed pair), and V4 flagged all 8 persona games at its frozen threshold.

## 5. Acceptance criteria

| Step | Status | Evidence |
|---|---|---|
| 0 Preconditions in the DEVLOG first; amendment committed before rendering | **PASSED** | §4.0 |
| 1 Readiness READY | **PASSED** | §4.1 |
| 2 Quality + manipulation check + quality_fail.json | **PASSED** | §4.2 |
| 3 Render without touching data/clean, data/views; RQ0.3 grep check | **PASSED** | §4.3 |
| 4 Transfer list printed | **PASSED** | §4.4 |
| 5 Frozen monitor, 384 calls, measured first, ≤ 3.5 h, failures counted | **PASSED** | §4.5 (0 failures, ≈ 131 min) |
| 6 Signals with the frozen baseline (refitted: false) | **PASSED** | §4.6 |
| 7 One analysis run; R1–R10 next to the originals; secondary; verdicts; 10-line summary | **PASSED** | §4.7–4.10 |

## 6. Deviations

- **The G_others float-zero game** is reported both ways (24/24 by the frozen task-12 rule, 23/24 substantively). The rule was not changed.
- **Quality and view checks** use path-only copies of the task-12 scripts (new scratch files) rather than editing them.
- **§4.7 "context" line:** V2 and V3 point estimates are derived by subtracting reported estimates (no new analysis, no CI).

## 7. Open problems and limitations

- **One session, one sample per view** (session effects: report 16 §4.4). n = 48 (24 positives, 8 per negative type).
- **The llama monitor's last-position bias is still present** in this frozen configuration (by design: the replication tests the frozen system).
- **Still to come on machine C:** the judge run plus E1–E4/E3b (Study 2.3), and the granite G1–G4 run, after the transfer and the lead's OK. The llama V1–V4 scores for G3 / G4 are in `runs/replication_llama/outputs/monitor.jsonl`.
- **The write-up** (`results_22.md` §g, README) still says TBD; updating it is a separate task.

## 8. Next task

1. Transfer the files (§4.4) to machine C.
2. Run the judge and granite on C (with the lead's OK), then the Study 2.3 and G1–G4 analyses.
3. Update the write-up with the replication results.

## 9. Files to commit

- `scratch/p21_quality.py`, `scratch/p21_quality_summary.py`, `scratch/p21_view_checks.py`, `scratch/p21_run_stats.py`, `scratch/p21_print_secondary.py`
- `notes/DEVLOG.md`, `notes/reports/21_replication_22.md`

**Not committed** (Rule E): `data/replication/*`, `runs/replication/*`, `runs/replication_llama/*`, the run logs, `cache/`.

## 10. Commit line

`Commit: exp: run the Study 2.2 replication on 48 new games (frozen llama monitor) and report R1-R10`
