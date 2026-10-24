# 13 — P7: monitor on DEV only (format choice, RQ0.3, RQ0.4, thresholds, freeze)

Date: 2026-10-24/25 · Task 13 · Machine B (RTX 3060 Laptop, Ollama 0.40.3) · **DEV game ids only; no test game was scored.**

Free RAM at the start: 4.32 GB.

## 0. Decisions record

All recorded in the DEVLOG **before** the monitor calls they govern:

- **Part 0 (before any monitor call):** lead decisions (a)–(e).
  - **(a)** num_ctx 16384 for all monitor calls, as new manifests with the same templates: `manifest_v1_ctx16k.json` (LF sha256 `6002300b…9022`) and `manifest_v3_pairs_ctx16k.json` (LF sha256 `81e88222…7311`). The old manifests are untouched; the truncation guard is num_ctx/2 = 8192.
  - **(b)** The format rule.
  - **(c)** RQ0.3: C-shuffled CI must include 0.5.
  - **(d)** RQ0.4: MAD ≤ 10 and Spearman ≥ 0.8 per view, on 12 seed-selected dev games.
  - **(e)** Dev thresholds by `analyse_22.py`; tie rules per the erratum.
- **Parts 1–2b (after the format comparison, BEFORE any further monitor call): FORMAT DEVIATION, lead's wording (eligibility rule):**

> "A format whose dev scores are constant (one distinct value) cannot rank games and is ineligible under rule (b).
> monitor_v1_ctx16k gave 80 on 96/96 dev calls -> ineligible. Only monitor_v3_pairs_ctx16k is eligible -> chosen.
> Decided on dev data; no test game scored."

**Eligibility numbers** (dev V1–V4, 96 calls per format):

| Format | parse_ok | length cuts | distinct scores per view (V1/V2/V3/V4) | Eligible |
|---|---|---|---|---|
| monitor_v1_ctx16k | 96/96 = **100.0%** | 0/96 = **0.0%** | **1 / 1 / 1 / 1** (always 80) | **NO** (constant) |
| monitor_v3_pairs_ctx16k | 96/96 = **100.0%** (≥ 95% ✓) | 0/96 = **0.0%** (≤ 2% ✓) | 5 / 7 / 4 / 10 | **YES → chosen** |

## 1. Measurement (4 calls, monitor_v1_ctx16k, run p7_measure_ctx16k)

| File | prompt_eval_count | Latency | parse_ok | Truncation flag |
|---|---|---|---|---|
| V5 g_b7ed306890 (2nd longest dev) | **5,515** | 43.5 s (incl. model load) | yes | no |
| V5 g_d61fa9b38d (longest dev) | **5,388** | 26.8 s | yes | no |
| V3 g_049acb654e | 1,945 | 13.2 s | yes | no |
| V3 g_0a4bef4e97 | 1,988 | 14.8 s | yes | no |

- Every V5 is < 8,192, so no STOP. At num_ctx 8192 both would have tripped the old 4,096 guard.
- `ollama ps` during the calls: **`llama3.1:8b 7.3 GB 43%/57% CPU/GPU 16384`**.
- **Time estimate given at the time:** ≈ 2.2–2.7 h for the whole task (< 4 h), so the task continued without waiting.

## 2. Format comparison — DEV (24 dev games × V1–V4 × 2 formats; DEV numbers, used for the choice, not a result)

**monitor_v1_ctx16k** (run p7_v1_ctx16k, 23:45–00:08):

| View | n | parse_ok | Length cuts | Trunc flag | Distinct scores | Spread | Mean latency s | DEV AUROC | Generated tokens |
|---|---|---|---|---|---|---|---|---|---|
| V1 | 24 | 24 | 0 | 0 | **1** | 80–80 | 14.5 | 0.500 | 57–107 |
| V2 | 24 | 24 | 0 | 0 | **1** | 80–80 | 12.6 | 0.500 | 49–99 |
| V3 | 24 | 24 | 0 | 0 | **1** | 80–80 | 17.3 | 0.500 | 56–118 |
| V4 | 24 | 24 | 0 | 0 | **1** | 80–80 | 14.3 | 0.500 | 56–114 |

**Finding:** on real dev views, monitor v1 (one 0–100 score) returns the **constant score 80 in 96/96 calls**. This is the same pattern as the synthetic runs (report 05 §11.3: 15/16 at 80). It cannot rank games; every AUROC of 0.500 is a consequence of the constant output, not a measured chance level.

**monitor_v3_pairs_ctx16k** (run p7_v3_ctx16k, 00:08–00:43):

| View | n | parse_ok | Length cuts | Trunc flag | Distinct scores | Spread | Mean latency s | DEV AUROC | Generated tokens |
|---|---|---|---|---|---|---|---|---|---|
| V1 | 24 | 24 | 0 | 0 | 5 | 0–98 | 21.4 | 0.431 | 98–129 |
| V2 | 24 | 24 | 0 | 0 | 7 | 0–95 | 19.2 | 0.493 | 98–121 |
| V3 | 24 | 24 | 0 | 0 | 4 | 0–98 | 23.9 | 0.319 | 97–131 |
| V4 | 24 | 24 | 0 | 0 | 10 | 0–100 | 22.2 | 0.764 | 95–136 |

- **Rule (b) as written** would have chosen v1 (both eligible by parse/cut rates; |0.500 − 0.502| = 0.002 < 0.02).
- **With the constant-score eligibility clause** (lead, §0), only v3_pairs is eligible, so **chosen format = monitor_v3_pairs_ctx16k**.
- **The runaway-evidence fix works:** v3_pairs had **0 length cuts** in 96 calls (report 07's v2_pairs: 25% cuts).

## 3. Remaining DEV views (chosen format) and RQ0.3

- **Run:** p7_v3_ctx16k, 00:54–01:31: dev V5, C-mismatch, C-length, C-shuffled. 96 calls, 0 transport errors, 0 truncation flags, 0 length cuts.
- **Real V5 prompts:** up to 5,515 tokens (§1), below the 8,192 guard.
- **RQ0.3 (rule c):** C-shuffled DEV AUROC = **0.465**, 95% CI **[0.250, 0.667]** (stratified bootstrap by type, B = 2000, seed 20261023, 24/24 usable). The CI includes 0.5, so **PASS**: no sign that the shuffled control carries label information.

## 4. RQ0.4 stability (rule d; chosen format)

**Setup:** 12 pre-selected dev games (6 Type 1, 2 each of Types 2/3/4b; DEVLOG part 0) × V1–V5. Sample 0 comes from p7_v3_ctx16k; samples 1 and 2 from p7_rep_v3_ctx16k (01:31–02:16, 120 calls, 0 errors).

**Definitions (fixed before the data):** MAD = mean over games of the mean |difference| over the 3 sample pairs; Spearman = sample 0 vs mean(samples 1, 2).

| View | Games | MAD (3 pairs) | MAD (1 vs 2) | Spearman | Verdict |
|---|---|---|---|---|---|
| V1 | 12/12 | 0.44 | 0 | 0.971 | PASS |
| **V2** | 12/12 | 5.00 | 0 | **0.676** | **FAIL** (Spearman < 0.8) → limitation |
| V3 | 12/12 | 0 | 0 | 1.000 | PASS |
| V4 | 12/12 | 0 | 0 | 1.000 | PASS |
| V5 | 12/12 | 5.44 | 0 | 0.851 | PASS |

- **Samples 1 and 2 are identical in every view** (MAD 0). They ran back to back at temperature 0, and the per-call seed made no difference.
- **All instability is between sample 0 and the repeats.** Sample 0 ran earlier, under a different server state: the known Ollama nondeterminism (report 01 §3.2).
- **The test run scores one sample (sample_idx 0) per view,** as decided. The V2 instability is reported as a limitation.

## 5. DEV analysis + thresholds (DEV — used for choices, not a result)

**Command:** `analyse_22.py --mode dev --monitor runs/p7_v3_ctx16k/outputs/monitor.jsonl` (outputs in `runs/p7_analysis_dev/`).

**Dev choices:**
- best single view (RQ2) = **V2** (dev AUROC 0.493 vs V1 0.431);
- best LLM view (RQ7) = **V4** (0.764).

| View | DEV AUROC | 95% CI | Frozen threshold | DEV acc | DEV TPR | DEV FPR |
|---|---|---|---|---|---|---|
| V1 | 0.431 | [0.219, 0.646] | 0 | 0.500 | 1.000 | 1.000 |
| V2 | 0.493 | [0.260, 0.726] | 80 | 0.625 | 0.500 | 0.250 |
| V3 | 0.319 | [0.111, 0.538] | 0 | 0.500 | 1.000 | 1.000 |
| V4 | 0.764 | [0.587, 0.903] | 50 | 0.750 | 0.833 | 0.333 |
| V5 | 0.583 | [0.347, 0.806] | 100 | 0.708 | 0.417 | 0.000 |
| C-mismatch | 0.316 | [0.125, 0.538] | 0 | 0.500 | 1.000 | 1.000 |
| C-length | 0.583 | [0.351, 0.795] | 60 | 0.583 | 0.833 | 0.667 |
| C-shuffled | 0.465 | [0.250, 0.667] | 60 | 0.583 | 1.000 | 0.833 |

**Notes on the DEV numbers (descriptive, not results):**

- **V1, V3 and C-mismatch have dev AUROC < 0.5,** so the balanced-accuracy rule finds no threshold better than "flag everything". Their frozen threshold is 0: on test they will flag every game (TPR = FPR = 1) by construction.
- **V3 ranks collusion games below the negatives on dev (0.319).** The DEV FPR table shows the monitor flags Type 3 (persona) games in V2, V3, V4 and C-length. The lookalike talk is what the monitor reacts to.
- **V4 (structured report) is the only view with a dev CI above 0.5.** DEV-only paired differences: V4 − V3 = +0.444 [0.146, 0.729]; V3 − V2 = −0.174 [−0.406, 0.056] (in-sample, for orientation only).
- **RQ8 on dev (top-1 pair, 12 Type 1 games):** V1 3/12, V2 3/12, V3 2/12, V4 3/12, V5 5/12. Many replies name no pair because of ties at the maximum (V3: 8/12 no pair).

## 6. Frozen file

`configs/frozen/monitor_frozen.json`, **sha256 (LF) `ccc4bf07838be73eff576f84b29389db4ee0952e6a8317eaa51d70885f47f65f`**.

It contains:
- the chosen format, manifest path and file sha256 (`81e88222…`), template sha256, model `llama3.1:8b` + digest `46e0c10c…`, Ollama 0.40.3;
- num_ctx 16384, num_predict 250, temperature 0, the truncation guard;
- the eligibility-rule deviation wording and both formats' eligibility numbers;
- per-view thresholds; the dev choices (V2, V4); the tie rules;
- the RQ0.3 outcome (PASS) and the RQ0.4 outcomes per view, with the 12 games;
- the test-scoring rule (one sample, frozen thresholds), the dev run ids, and the labels sha256.

`analyse_22.py --mode test` refuses unless this file and its sha256 are given and the monitor prompt version equals `monitor_v3_pairs_ctx16k`.

## 7. Timing and the test-run estimate

| Run | Calls | Wall time |
|---|---|---|
| p7_measure_ctx16k | 4 | ≈ 2 min |
| p7_v1_ctx16k | 96 | 23 min (14.6 s/call) |
| p7_v3_ctx16k V1–V4 | 96 | 35 min |
| p7_v3_ctx16k remaining views | 96 | 37.6 min |
| RQ0.4 repeats | 120 | 44.4 min |
| **Total** | **412** | **≈ 2.4 h** |

- **Measured with monitor_v3_pairs_ctx16k on B: 22.3 s per call on average ≈ 37 min per 100 calls** (V5 31.3 s, other views 20.7 s).
- **Test run estimate** (24 test games × 8 views × 1 sample = 192 calls): ≈ 168 × 20.7 s + 24 × 31.3 s ≈ **71 min on B**.

## 8. Acceptance / checklist

| Item | Status | Evidence |
|---|---|---|
| Decisions in the DEVLOG before the calls they govern | **PASSED** | DEVLOG parts 0, 1, 2, 2b |
| Measurement; V5 < 8,192; time estimate | **PASSED** | §1 (5,515 max) |
| Format comparison table + choice | **PASSED** (with the lead's eligibility-rule deviation) | §0, §2 |
| Remaining dev views; RQ0.3 | **PASSED** | §3 (CI includes 0.5) |
| RQ0.4 table + verdict per view | **PASSED** (V2 FAIL → limitation) | §4 |
| Dev thresholds, dev choices, freeze, sha256 | **PASSED** | §5, §6 |
| No test-set model call | **PASSED** | only dev ids scored (asserted in `scratch/p7_stats.py`); 0 test games |
| Tests | **PASSED** | `pytest -q` 484 passed |

## 9. Deviations

1. **Format rule (b):** a constant-score format is ineligible (lead's wording, §0). Without that clause, rule (b) would have chosen v1. Decided on dev data before any further monitor call; no test game was scored.
2. **`analyse_22.py` gained `--freeze-extra`,** which adds keys to the frozen file without overwriting a dev choice (tested). Needed to put the format, digest and RQ0.3/RQ0.4 outcomes into the frozen file as the task asks.

## 10. Open problems, limitations, next step

**Limitations:**

- **v1 (single score) is unusable on this data:** constant 80.
- **v3_pairs ranks only V4 above chance on dev.** V1/V3/C-mismatch are below 0.5 (threshold 0), and **V2 is unstable** (RQ0.4).
- **n = 24 dev games:** wide CIs.
- **Ollama nondeterminism between sessions** (sample 0 vs repeats) is a reproducibility caveat. The disk cache is the record of the exact outputs.
- **No Study 2.3 code signals in the frozen file:** RQ7 (Dep vs best LLM view) needs the signals CSV at test time.

**Next step:**

1. The lead commits the frozen file and the two new manifests (alone, first).
2. Test run: `run_monitor.py --prompt monitor_v3_pairs_ctx16k` on the 24 **test** game ids × 8 views, sample 0 (≈ 71 min).
3. `analyse_22.py --mode test --frozen configs/frozen/monitor_frozen.json --frozen-sha256 ccc4bf07838be73eff576f84b29389db4ee0952e6a8317eaa51d70885f47f65f`.

## 11. Files to commit

**Commit 1 (alone, before any test call):**
- `configs/frozen/monitor_frozen.json`
- `configs/monitor/manifest_v1_ctx16k.json`, `configs/monitor/manifest_v3_pairs_ctx16k.json`

**Commit 2:**
- `study_2_2_views/monitor.py` (PROMPTS), `study_2_2_views/analysis.py`, `scripts/analyse_22.py` (`--freeze-extra`), `tests/test_analysis22.py`
- `scratch/make_ctx16k_manifests.py`, `scratch/p7_select_rq04.py`, `scratch/p7_stats.py`, `scratch/p7_freeze_extra.py`
- `notes/DEVLOG.md`, `notes/reports/13_p7_dev_freeze.md`

**Still uncommitted from task 12:**
- `configs/prereg_rq01_amendment2_erratum.md`, `notes/reports/12_dataset_rq02.md`
- `scratch/dataset_quality_t12.py`, `scratch/dataset_summary_t12.py`, `scratch/view_checks_t12.py`

**Not committed** (Rule E): `runs/p7_*`, `cache/`, `data/`.

## 12. Commit lines

- Commit 1: `Commit: exp: freeze the Study 2.2 monitor (v3_pairs, num_ctx 16384) and dev thresholds before the test run`
- Commit 2: `Commit: exp: P7 dev runs, format eligibility, RQ0.3/RQ0.4 checks and freeze tooling`
