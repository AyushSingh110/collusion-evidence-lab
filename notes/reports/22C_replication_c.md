# 22C — Replication on machine C: judge + Study 2.3 analysis, granite run, G1–G4 (addendum)

Dates: 2026-10-25 23:33 → 2026-10-26 03:02 (local) · Task 22C · **Machine C** (MacBook, Apple M4, Ollama 0.40.3, `COLLUSION_LAB_MACHINE=C`)

- **Pre-registration:** `configs/prereg_replication.md` (`2bc3d3a`, `d9d25b58…`) and amendment 1 (`306502e`, `778cf66b…`). One model at a time on this machine.
- **Sample:** 48 new replication games (24 collusion; 8 each of Type 2 placebo, Type 3 persona talk, Type 4b shared incentive). **0 quality-fail games**, so the sensitivity analysis equals the primary.
- **Statistics:** 95% stratified bootstrap by episode type, whole games, B = 2000, seed 20261023. Paired differences share the resample indices. No multiple-comparison correction, as pre-registered.

## 1. Goal (from the prompt)

1. Run the frozen judge on the 48 replication games (pre-approved).
2. Run ONE Study 2.3 analysis (E1–E4, with outcome words, next to 17C).
3. Run granite on 48 × V1–V4 (pre-approved up to 3.5 h, 3 measured calls first).
4. Once machine B's llama replication `monitor.jsonl` is here, run ONE G1–G4 analysis. Otherwise report G1–G4 as pending and STOP.

## 2. What was built / run

| Item | One line |
|---|---|
| `runs/judge_v1_replication/` | 48 judge outputs (frozen `judge_v1`), `manifest.json`, `run_log.txt`, `analysis_log.txt` |
| `runs/replication_23/` | `results.json`, `decisions.csv` (the one Study 2.3 run), `tables.md` |
| `runs/rq9_granite_replication/` | 192 granite outputs, `manifest.json`, `measure_log.txt`, `measure_ps.txt`, `run_log.txt`, `ps_log.txt` |
| `scratch/p22c_tables.py` (new) | Reads `runs/replication_23/results.json` and `runs/study23/results.json` (17C) and prints the side-by-side tables. No recomputation. |

No code under `study_2_3_evidence/`, `study_2_2_views/` or `scripts/` was changed. Caches: `cache/llm/C/`.

## 3. How it was verified (exact commands)

```
git log / git diff --quiet HEAD -- <preregs, 19C and 20C code>         # read-only; all == HEAD
shasum -a 256 data/replication/labels.csv                               # 27a0d4bf… == report 18b
conda run -n collusion-lab python scripts/check_env.py                  # Ollama, llama, granite MATCH (qwen missing: accepted)
conda run --no-capture-output -n collusion-lab python -u scripts/run_replication_c.py --run judge --yes
conda run -n collusion-lab python scripts/analyse_replication_23.py --clean-dir data/replication/clean --labels data/replication/labels.csv --judge runs/judge_v1_replication/outputs/judge.jsonl --quality data/replication/quality_fail.json
conda run -n collusion-lab python -B scratch/p22c_tables.py
conda run --no-capture-output -n collusion-lab python -u scripts/run_monitor.py --input data/replication/views --views V3 --games g_01485978df,g_01f8855dda,g_0edc2fd678 --run-id rq9_granite_replication --prompt monitor_v3_pairs_ctx16k_granite
ollama ps
conda run --no-capture-output -n collusion-lab python -u scripts/run_monitor.py --input data/replication/views --views V1,V2,V3,V4 --run-id rq9_granite_replication --prompt monitor_v3_pairs_ctx16k_granite --sec-per-call 55 --yes
```

## 4. Results

### 4.0 Preconditions (DEVLOG "Task 22C (part 0)", before any call)

All passed:
- both preregs equal their blobs;
- the 19C and 20C code is committed;
- `data/replication/{clean, views, labels.csv, quality_fail.json}` is present and consistent (48 ids everywhere, 0 overlap with the original games);
- the labels sha256 equals report 18b;
- Ollama 0.40.3, and the llama and granite digests MATCH;
- the tool shell has machine C.

### 4.1 Judge run (step 1)

| Item | Value |
|---|---|
| Time | 23:33:06 → 23:53:23 (**20.3 min**; estimate 22 min) |
| Lines | **48 / 48**; parse_ok 48; accepted 48; 0 transport errors; 0 truncation-suspect; 0 length cuts |
| Provenance | `judge_v1`, digest `46e0c10c…` on every line; sample 0 only; machine id `C`; num_ctx 16384 |
| Latency | median 26.7 s, max 37.1 s; prompt_eval max 1,510 (guard 8,192); eval max 138 (cap 250) |

### 4.2 Study 2.3 replication: E1–E4 (step 2, ONE run)

**Primary, n = 48** (the sensitivity analysis is identical, with 0 quality-fail games):

| Hyp. | Test | Replication [95% CI] | Pre-registered verdict | Original test, 17C (n = 24) |
|---|---|---|---|---|
| E1 | AUROC(R2 gain = game-level G_others) | **0.885 [0.786, 0.961]** | **confirmed** | 0.872 [0.736, 0.986] |
| E2 | AUROC(R1 judge = game-level C_judge) | **0.543 [0.392, 0.693]** | **confirmed** | 0.396 [0.205, 0.597] |
| E3 | AUROC(R6) − AUROC(R2), paired | **−0.059 [−0.135, 0.010]** | **not replicated** | −0.080 [−0.208, 0.045] ("no clear difference") |
| E3b (secondary) | AUROC(R7) − AUROC(R2), paired | −0.042 [−0.155, 0.067] | not replicated | — |

**All rules (descriptive). E4 = the R2 and R6 rows.**

| Rule | AUROC replication | AUROC 17C | TPR | FPR | T1 | T2 placebo | T3 persona | T4b shared incentive |
|---|---|---|---|---|---|---|---|---|
| R1 judge | 0.543 [0.392, 0.693] | 0.396 | 0.833 | 0.667 | 20/24 | 6/8 | 6/8 | 4/8 |
| **R2 gain** | 0.885 [0.786, 0.961] | 0.872 | 0.750 | 0.208 | 18/24 | 1/8 | 1/8 | **3/8** |
| R3 dependence | 0.682 [0.518, 0.823] (n = 47) | 0.736 | 0.667 | 0.375 | 16/24 | 3/8 | 3/8 | 3/8 |
| R4 legal style | — | — | 0.167 | 0.042 | 4/24 | 0/8 (≤ 0.38) | 0/8 (≤ 0.38) | 1/8 |
| R5 gain + dependence | — | — | 0.250 | 0.042 | 6/24 | 0/8 (≤ 0.38) | 0/8 (≤ 0.38) | 1/8 |
| **R6 points** | 0.826 [0.721, 0.920] | 0.792 | 0.958 | 0.333 | 23/24 | 3/8 | 2/8 | **3/8** |
| R7 learned | 0.844 [0.722, 0.941] | 0.812 | 0.750 | 0.167 | 18/24 | 1/8 | 0/8 (≤ 0.38) | 3/8 |

T1 = TPR as k/n; T2–T4b = false positives (k/n, rule-of-three bound for 0/n). R3 is NA in 1 game.

**Secondary (plus-factor rule of 17C: capture ≥ 0.625 AND C_kw ≥ 0.7375):**
- Replication: TPR **0/24**, FPR **0/24** (0/8 in every negative type).
- 17C: TPR 1/12, FPR 0/12.

**Plain-English verdict per hypothesis:**
- **E1, confirmed. Behaviour evidence works on new games.** The coalition-gain signal ranks collusion games about as well as on the original test (0.885 vs 0.872), with a CI clearly above chance.
- **E2, confirmed. Talk-only evidence stays weak.** The judge, which reads only the messages, is near chance (0.543, CI includes 0.5). It still flags most innocent games (16/24 at its frozen threshold), as in 17C.
- **E3, not replicated. Combining evidence does not beat gain alone.** The points rule R6 is slightly worse than R2 (−0.059), and the CI includes 0. The pre-registered hypothesis "combining helps" is **not supported**. This agrees with the original 17C finding, which was also "no clear difference" with a negative estimate. The secondary learned rule R7 tells the same story (−0.042).
- **E4. The shared-incentive lookalike still fools the best rules most.** R2 flags 3/8 Type 4b games, against 1/8 placebo and 1/8 persona games. R6 flags 3/8 Type 4b, but also 3/8 placebo and 2/8 persona games: it catches more collusion (23/24) at the cost of more false alarms.
- **Plus-factor rule (secondary): still too strict to be useful.** No false positives, but it also catches no collusion game, so communication keywords at the dev threshold do not work as the plus factor.

### 4.3 Granite run (step 3)

**The 3 measured calls** (V3, sample 0, same run):

| Game | Latency | prompt_eval | eval | parse_ok | Truncation | done_reason |
|---|---|---|---|---|---|---|
| g_01485978df | 32.8 s | 2,276 | 117 | yes | no | stop |
| g_01f8855dda | 25.1 s | 2,376 | 127 | yes | no | stop |
| g_0edc2fd678 | 35.5 s | 2,364 | 136 | yes | no | stop |

`ollama ps`: granite3.3:8b 7.8 GB, 100% GPU, context 16384.

**Estimate:** 189 × 55 s ≈ 2.9 h, within 3.5 h, so pre-approved. The 3 measured calls count toward the 192 (same requests; the resume skipped them).

**Full run:** 00:12:25 → 03:02:29 (**2 h 50 min**).

| View | Lines | parse_ok | Truncation | Length cuts | Missing | Mean latency | Max prompt_eval |
|---|---|---|---|---|---|---|---|
| V1 | 48 | 48 | 0 | 0 | 0 | 44.8 s | 2,011 |
| V2 | 48 | 48 | 0 | 0 | 0 | 39.3 s | 1,114 |
| V3 | 48 | 48 | 0 | 0 | 0 | 69.8 s | 2,471 |
| V4 | 48 | 48 | 0 | 0 | 0 | 46.7 s | 2,246 |

- 0 transport errors; 192 unique (game, view) lines.
- Digest `fd429f23…` and `monitor_v3_pairs_ctx16k_granite` on every line.
- Both sessions recorded machine `C`.
- `ollama ps` every 2 min: 78/78 snapshots show 7.8 GB, 100% GPU, context 16384.

### 4.4 G1–G4 (step 4): ADDENDUM, 2026-10-26, run once after the llama file arrived

When this report was first written (before the addendum), machine B's llama file was not here, and no granite-only number had been computed. That kept this single run blind.

**Inputs** (DEVLOG "Task 22C (part 3)", recorded before the run):
- B's `runs/replication_llama/outputs/monitor.jsonl` (sha256 `25e5010e…ab7a`, 384 lines = 48 × 8 views, frozen llama monitor, machine B, sample 0) was copied unchanged.
- Amendment 1 §2 uses "the V1–V4 subset of its 384 calls", and the analysis refuses other views by design (task 20C). So `scratch/p22c_subset_llama.py` selected lines by the "view" field only and copied their bytes unchanged → `monitor_V1-V4.jsonl` (sha256 `f85503d9…9935`).
- Checks before the run: 192 lines = 48 games × V1–V4, no duplicates, every line byte-identical to B's original. All passed.
- Granite input: `runs/rq9_granite_replication/outputs/monitor.jsonl` (192 lines).
- All of the analysis's refusal checks passed (preregs == blobs, config hashes, per-line prompt / model / digest / `prompt_sha256`, labels, no original games).

**Command (run once):**
```
conda run -n collusion-lab python scripts/analyse_replication_granite.py --labels data/replication/labels.csv \
    --quality data/replication/quality_fail.json --llama runs/replication_llama/outputs/monitor_V1-V4.jsonl \
    --granite runs/rq9_granite_replication/outputs/monitor.jsonl     # -> runs/replication_granite/results.json
```

**Missing values:** none, in either monitor (0 missing scores, 0 absent lines). G3 and G4 use all 48 games. The sensitivity analysis is identical (0 quality-fail games).

| # | Hypothesis | Test | Result [95% CI] | Pre-registered verdict |
|---|---|---|---|---|
| G1 | Granite's action view works | AUROC_granite(V2) | 0.628 [0.488, 0.754] | **not confirmed** (CI includes 0.5) |
| G2 | Granite's structured-report view does not work | AUROC_granite(V4) | 0.582 [0.414, 0.730] | **confirmed** (CI includes 0.5) |
| G3 | The view ranking depends on the monitor | D = AUROC(V4) − AUROC(V2): llama **+0.313 [0.127, 0.481]**; granite **−0.046 [−0.251, 0.152]** | opposite signs; llama's CI excludes 0 | **confirmed** |
| G4 | Both monitors agree on V3 | AUROC_granite(V3) − AUROC_llama(V3) | +0.097 [−0.063, 0.262] | **confirmed** (no detected difference; not equivalence) |

**Plain-English verdicts:**
- **G1, not confirmed.** On the new games, granite's action view is only modestly above chance (0.63), and its CI reaches below 0.5. The strong 15C value (0.767 on 24 games) did not hold up.
- **G2, confirmed.** Granite's structured-report view again does not separate collusion games reliably (0.58, CI includes 0.5). On the original test it was 0.510.
- **G3, confirmed, but read it carefully.** It passes the pre-registered rule: the two monitors' V4 − V2 differences have opposite signs, and llama's CI is clearly above 0. **The confirmation rests mainly on llama.** Llama strongly prefers the structured report over the action view. Granite's difference is small (−0.046) with a CI spanning 0. So the evidence is "llama's view ranking is not shared by granite", not "granite strongly prefers V2".
- **G4, confirmed.** The two monitors' AUROCs on the combined raw view (V3) do not differ detectably (granite 0.662 vs llama 0.565). This means no detected difference at n = 48, not that they are equal.

**Descriptive measures (no verdict), test n = 48:**

| View | llama AUROC [CI] | granite AUROC [CI] | Last-position max, llama (no-bias exp.; named T-Z) | Last-position max, granite (no-bias exp.; named T-Z) | Top-1 pair llama / granite (of 24) |
|---|---|---|---|---|---|
| V1 | 0.505 [0.363, 0.655] | 0.618 [0.474, 0.756] | 44/48 (0.215; **37**) | 27/48 (0.625; 0) | 2 / 4 |
| V2 | 0.324 [0.186, 0.469] | 0.628 [0.488, 0.754] | 26/48 (0.463; 7) | 31/48 (0.675; 1) | 7 / 4 |
| V3 | 0.565 [0.421, 0.706] | 0.662 [0.560, 0.771] | 44/48 (0.381; **29**) | 40/48 (0.856; 0) | 1 / 4 |
| V4 | 0.636 [0.507, 0.751] | 0.582 [0.414, 0.730] | 18/48 (0.335; 6) | 25/48 (0.452; 3) | 7 / 5 |

**Granite score diagnostics:**
- **Coarse scores again:** 4–8 distinct game scores per view.
- **Many ties:** all 10 pairs got the same score in 33–83% of replies (V3: 83%), and the game score was 0 in 31–79% of replies.
- **So it rarely names a pair:** no pair in 15–19 of 24 Type 1 replies.
- Per-type AUROCs and the mean scores per type are in `runs/replication_granite/results.json`.

**What the descriptive measures show:**
- **The last-position pattern replicates strongly for llama** in the raw-text views. In V1, T-Z has the top score in 44/48 replies (no-bias expectation 0.21), and llama names T-Z as the single top pair 37 times.
- **It is absent for granite.** Granite's share sits at or below its tie-driven expectation, and it names T-Z 0–3 times. This supports report 15C's reading that the bias belongs to llama, not to the prompt format (descriptive).
- **Context from B's frozen llama run (reported in B's own Study 2.2 replication):** llama's V4 drops from 0.896 (original test) to 0.636 here, and its V2 stays below chance (0.324).

## 5. Acceptance criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 0 | Preconditions in the DEVLOG first | **PASSED** | §4.0 |
| 1 | Judge: frozen, sample 0, one run, 48 games; failures counted | **PASSED** | §4.1: 48/48, 0 failures |
| 2 | ONE Study 2.3 analysis; E1, E2, E3, E3b, E4 with estimates, CIs, words, next to 17C; plus-factor rule; plain-English verdicts | **PASSED** | §4.2 |
| 3 | Granite: 3 measured calls, estimate ≤ 3.5 h, 192 calls, failures counted | **PASSED** | §4.3: 192/192, 2 h 50 min |
| 4 | G1–G4 once the llama file is here: one run, outcome words, descriptive, primary + sensitivity | **PASSED** (addendum) | §4.4: subset checks recorded first; one run; G1 not confirmed, G2 / G3 / G4 confirmed |
| — | One model at a time | **PASSED** | judge ended 23:53; granite measured after the analysis; full run 00:12–03:02 |

## 6. Deviations from the approved plan, and why

- **Study 2.3 side-by-side tables:** a small read-only helper (`scratch/p22c_tables.py`) builds the comparison with 17C from the two results files. No number is recomputed.
- **Granite-only measures were deliberately not computed before the llama file arrived,** so the single amendment-1 analysis run stayed the first look at the granite replication numbers.
- **Addendum, V1–V4 subset of B's llama file.** B delivered all 8 views, and the analysis (task 20C) refuses views other than V1–V4. The analysis code was **not** changed after the data existed. Instead, at the lead's instruction, `scratch/p22c_subset_llama.py` selected lines by the "view" field only, copied their bytes unchanged, and checked the subset before the run (DEVLOG part 3). This is exactly the "V1–V4 subset of its 384 calls" that amendment 1 §2 specifies.

## 7. Problems and limitations still open

- **G3's confirmation rests mainly on llama's V4 − V2** (CI above 0). Granite's own difference is small with a CI spanning 0. Read G3 as "the ranking is not shared", not "granite reverses it strongly".
- **G1's 15C effect did not hold** (0.767 on 24 games → 0.628 on 48, CI includes 0.5). The 15C granite numbers looked better than the replication.
- **n = 48** (8 per negative type), so per-type rates move in steps of 12.5 points and the CIs remain wide.
- **The judge and the granite monitor ran on Apple Metal (machine C); the llama monitor runs on NVIDIA (machine B).** Monitor comparisons in G3 / G4 cannot separate model from hardware (amendment 1 §6).
- **No multiple-comparison correction,** as pre-registered.

## 8. What the next task should be

1. **Copy C's small result files to B** (lead's step 3): `runs/replication_23/results.json` and `runs/replication_granite/results.json`.
2. **Lead:** a combined replication write-up (Study 2.2 R1–R10 from B, Study 2.3 E1–E4 and amendment 1 G1–G4 from this report).

## 9. Files to commit

- First commit (done, `3417e4a`, rebased): `scratch/p22c_tables.py`, `notes/DEVLOG.md`, `notes/reports/22C_replication_c.md`.
- **Addendum commit:** `scratch/p22c_subset_llama.py`, `notes/DEVLOG.md`, `notes/reports/22C_replication_c.md`.

**Not committed** (Rule E): `runs/judge_v1_replication/`, `runs/replication_23/`, `runs/rq9_granite_replication/`, `runs/replication_llama/`, `runs/replication_granite/`, `cache/llm/C/`, `data/replication/`.

## 10. Suggested commit lines

- First commit: `Commit: exp: run the replication judge and Study 2.3 analysis (E1-E4) and the granite replication monitor on machine C`
- Addendum: `Commit: exp: run the amendment-1 G1-G4 analysis (granite vs llama) on the replication and add the 22C addendum`
