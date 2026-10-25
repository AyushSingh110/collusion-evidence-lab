# 16 — Follow-up 1: does pair-order position bias explain the raw-view results?

Date: 2026-10-25 · Task 16 · Machine B (RTX 3060 Laptop, Ollama 0.40.3)

- **Pre-registration:** `configs/prereg_followup1_pair_order.md`, commit `496fc28`, LF sha256 `0d6aaa41…da46e`.
- **Status:** a **pre-registered exploratory follow-up**, reported separately. It **does not replace or change** the primary Study 2.2 results (report 14), the frozen file or any earlier output.
- **Sample:** n = 24 test games (12 collusion; 4 per negative type).
- **Statistics:** CIs are 95% stratified bootstraps by episode type, B = 2000, seed 20261023. Paired comparisons use the same resample indices on the same games.

## 1. Goal (from the prompt)

- **Question:** does the last-position bias in the pair scores (report 15 §4.6) explain why the raw views (V1, V3) did poorly?
- **Method:** re-score the 24 test games × V1–V4 in one session, in two interleaved arms: random pair order vs the frozen fixed order. Compare them (primary), and compare against the original frozen test run (secondary).

## 2. What was built

| File | One line |
|---|---|
| `configs/prereg_followup1_pair_order.md` | Pre-registration (written and committed in part 1, before any call). |
| `configs/monitor/monitor_v3_pairs_rot.txt` | Byte copy of the frozen template. Only the reply example line changes: the pair list becomes `{pair_scores_example}`. LF sha256 `8590e6da…c1a86`. |
| `configs/monitor/manifest_v3_pairs_ctx16k_rot.json` | Copy of the frozen ctx16k manifest. Adds the new template, prompt_version `monitor_v3_pairs_ctx16k_rot` and the permutation rule. File sha256 `e2aecc7f…f9752`. |
| `study_2_2_views/monitor.py` | **Additive** `pair_order=None` option on `system_prompt` / `score_view`; new `permuted_pair_order`, `schema_in_order`, `emitted_key_order`; a PROMPTS entry. With the option off, the request is unchanged (tested). |
| `tests/test_monitor.py` | +6 mock tests (listed in §3). |
| `scratch/p16_make_config.py` | Builds the template and manifest from the frozen files (asserts that exactly one replacement is made). |
| `scratch/p16_run.py` | Interleaved two-arm runner, sample_idx 1; the cell order is saved before the first call; failures are written as data and never re-run. |
| `scratch/p16_analysis.py` | Analysis exactly as pre-registered, plus a `--selftest` mode (the frozen run plays all three arms, so every difference must be 0). |
| `scratch/p16_figure.py` | Figure 7. |
| `writeup/figures/fig7_pair_order_followup.png` + caption appended to `captions.md` | New figure. |

## 3. How it was verified

```
git log -1 -- configs/prereg_followup1_pair_order.md ; git diff --quiet HEAD -- configs/prereg_followup1_pair_order.md   # read-only
conda run -n collusion-lab python -B scratch/p16_make_config.py         # one-line diff vs the frozen template (checked with diff)
conda run -n collusion-lab pytest -q                                    # 490 passed, 0 failed
conda run -n collusion-lab python scripts/check_env.py                  # READY
conda run -n collusion-lab python -u -B scratch/p16_run.py --limit 3    # timing measurement (part of the run)
conda run -n collusion-lab python -u -B scratch/p16_run.py              # the remaining 189 calls
conda run -n collusion-lab python -B scratch/p16_analysis.py --selftest # all differences 0; AUROCs = report 14; LPM = report 15
conda run -n collusion-lab python -B scratch/p16_analysis.py
conda run -n collusion-lab python -B scratch/p16_figure.py
```

**The six new mock tests:**
1. The frozen ctx16k files are pinned by hash.
2. The permutation is deterministic per seed, and every pair appears exactly once.
3. The rot config differs only in pair order: with the canonical order filled in, the prompt is identical to the frozen one.
4. The default request is unchanged when the option is off: same schema, same prompt, no new fields.
5. Mapping back is exact: distinct scores per pair come back under the canonical names.
6. Emitted-order parsing handles bad input.

**Recorded before the first call (DEVLOG part 2a/2b):** the commit and hash of the pre-registration, the template and manifest hashes, and the check that the frozen files are unchanged.

## 4. Results

### 4.1 Run

| Item | Value |
|---|---|
| Calls | **192** (96 random-order + 96 fixed-order). Measurement 04:45:05–04:46:22 IST (3 calls, part of the run), then 04:46:45–05:50:07 IST (189 calls): **≈ 65 min** in one Ollama session, interleaved per cell. |
| Failures | **0** transport errors, **0** parse failures, **0** truncation flags, **0** missing scores (both arms) |
| Key order written by the model | **96/96** in each arm, the order it was shown (so the schema order did reach the model) |
| Mean latency | random 20.4 s, fixed 20.0 s |
| `ollama ps` (32 samples) | `llama3.1:8b 7.3 GB 43%/57% CPU/GPU 16384` throughout |
| Estimate vs actual | estimated ~68 min; pre-approved ≤ 90 min |

### 4.2 AUROC per view

| View | Random order (same session) | Fixed order (same session) | Frozen test run (report 14) |
|---|---|---|---|
| V1 | 0.507 [0.306, 0.705] | 0.490 [0.299, 0.691] | 0.490 [0.299, 0.691] |
| V2 | 0.514 [0.295, 0.733] | 0.559 [0.319, 0.788] | 0.372 [0.170, 0.601] |
| V3 | 0.792 [0.604, 0.944] | 0.750 [0.552, 0.924] | 0.736 [0.535, 0.920] |
| V4 | 0.750 [0.580, 0.913] | 0.826 [0.667, 0.938] | 0.896 [0.771, 0.979] |

**Paired AUROC differences** (n = 24 in every comparison, 0 cells dropped):

| View | Random − fixed (**PRIMARY**) | Random − frozen (secondary) | Fixed − frozen (session effect) |
|---|---|---|---|
| V1 | +0.017 [−0.229, +0.281] | +0.017 [−0.229, +0.281] | +0.000 [+0.000, +0.000] |
| V2 | −0.045 [−0.333, +0.257] | +0.142 [−0.156, +0.427] | **+0.188 [+0.007, +0.389]** |
| V3 | +0.042 [−0.198, +0.285] | +0.056 [−0.188, +0.295] | +0.014 [+0.000, +0.052] |
| V4 | −0.076 [−0.240, +0.111] | −0.146 [−0.333, +0.059] | −0.069 [−0.194, +0.038] |

### 4.3 Last-position-max share (LPM)

LPM is the share of replies in which the last-listed pair gets the top score, ties included. The **no-bias expectation** is the mean of (pairs tied at the top) / 10.

| View | LPM random [CI] | No-bias exp. (random) | LPM fixed | LPM frozen | Drop fixed → random (**PRIMARY**) | Drop frozen → random (secondary) | T-Z has the top score: random / fixed / frozen |
|---|---|---|---|---|---|---|---|
| V1 | 10/24 = 0.417 [0.250, 0.625] | 0.217 | 21/24 | 21/24 | **+0.458 [+0.292, +0.667]** | +0.458 [+0.292, +0.667] | 7 / 21 / 21 |
| V2 | 11/24 = 0.458 [0.250, 0.667] | 0.479 | 16/24 | 14/24 | +0.208 [−0.084, +0.542] | +0.125 [−0.167, +0.417] | 12 / 16 / 14 |
| V3 | 9/24 = 0.375 [0.208, 0.542] | 0.304 | 19/24 | 17/24 | **+0.417 [+0.167, +0.667]** | +0.333 [+0.125, +0.542] | 9 / 19 / 17 |
| V4 | 6/24 = 0.250 [0.125, 0.375] | 0.292 | 6/24 | 7/24 | +0.000 [−0.125, +0.125] | +0.042 [−0.083, +0.167] | 9 / 6 / 7 |

### 4.4 Session effect (descriptive): fixed order re-scored vs the frozen test run

Scores were compared per game between the same-session fixed arm (sample_idx 1) and the original frozen run (sample_idx 0).

| View | AUROC fixed − frozen | Mean absolute difference | Spearman | Identical scores |
|---|---|---|---|---|
| V1 | +0.000 [+0.000, +0.000] | 0.21 | 1.000 | 23/24 |
| V2 | **+0.188 [+0.007, +0.389]** | **10.79** | **0.653** | 19/24 |
| V3 | +0.014 [+0.000, +0.052] | 0.54 | 0.987 | 22/24 |
| V4 | −0.069 [−0.194, +0.038] | 7.92 | 0.775 | 18/24 |

### 4.5 Top-1 pair accuracy (12 Type 1 games; chance 1/10)

| View | Random | Fixed | Frozen |
|---|---|---|---|
| V1 | **4/12** (no pair 2) | 1/12 (2) | 1/12 (2) |
| V2 | 5/12 (5) | 5/12 (3) | 6/12 (5) |
| V3 | **5/12** (2) | 2/12 (4) | 2/12 (3) |
| V4 | 8/12 (2) | 8/12 (1) | 7/12 (2) |

### 4.6 Supplementary per-type AUROC (Type 1 vs each negative type)

| View | Arm | T1 vs T2 | T1 vs T3 | T1 vs T4b |
|---|---|---|---|---|
| V1 | random | 0.438 [0.115, 0.792] | 0.719 [0.469, 0.938] | 0.365 [0.115, 0.625] |
| V1 | fixed | 0.385 [0.125, 0.740] | 0.740 [0.385, 1.000] | 0.344 [0.125, 0.646] |
| V1 | frozen | 0.385 [0.125, 0.740] | 0.740 [0.385, 1.000] | 0.344 [0.125, 0.646] |
| V2 | random | 0.521 [0.167, 0.834] | 0.500 [0.156, 0.844] | 0.521 [0.188, 0.844] |
| V2 | fixed | 0.708 [0.385, 0.958] | 0.458 [0.083, 0.854] | 0.510 [0.167, 0.854] |
| V2 | frozen | 0.438 [0.000, 0.833] | 0.219 [0.000, 0.625] | 0.458 [0.125, 0.812] |
| V3 | random | 0.719 [0.438, 0.958] | 0.896 [0.708, 1.000] | 0.760 [0.542, 0.938] |
| V3 | fixed | 0.677 [0.302, 0.959] | 0.917 [0.792, 1.000] | 0.656 [0.375, 0.917] |
| V3 | frozen | 0.667 [0.271, 0.959] | 0.917 [0.792, 1.000] | 0.625 [0.302, 0.917] |
| V4 | random | 0.948 [0.812, 1.000] | 0.458 [0.083, 0.854] | 0.844 [0.656, 0.990] |
| V4 | fixed | 0.896 [0.688, 1.000] | 0.688 [0.458, 0.896] | 0.896 [0.688, 1.000] |
| V4 | frozen | 1.000 [1.000, 1.000] | 0.792 [0.542, 1.000] | 0.896 [0.688, 1.000] |

### 4.7 Verdicts (decision rules of prereg §4; primary = random vs fixed, same session)

| Hypothesis | View | Primary | Secondary | Plain English |
|---|---|---|---|---|
| **H1** last-position bias disappears | V1 | **UNCLEAR** (drops, but stays above chance) | unclear | Randomising cut the last-pair effect from 21/24 to 10/24 (−0.46 [−0.67, −0.29]). But the last-listed pair still gets the top score more often than chance (0.42, CI [0.25, 0.63] vs 0.22 expected). V1 has a real **recency bias**, not only a T-Z habit. |
| **H1** | V3 | **SUPPORTED** | supported | 19/24 → 9/24 (−0.42 [−0.67, −0.17]); the random-arm share (0.38) is within the CI of chance (0.30). |
| **H2** raw-view AUROC rises | V1 | **UNCLEAR** | unclear | +0.017 [−0.229, +0.281]: essentially no change. Removing the order cue does **not** make messages-only work. |
| **H2** | V3 | **UNCLEAR** | unclear | +0.042 [−0.198, +0.285]: a small, non-significant rise. |
| **H3** V4 changes little | V4 | **SUPPORTED** | supported | −0.076 [−0.240, +0.111]: the CI includes 0. V4 hardly shows the bias at all (LPM 6/24 in both arms). |

Primary and secondary agree for every hypothesis.

## 5. What this means for reading report 14 (RQ1–RQ3)

1. **The position bias was real, but it is not why the raw views failed.**
   - With random order, the T-Z pattern goes away (V1: T-Z gets the top score in 21 → 7 of 24; V3: 19 → 9).
   - But V1's AUROC stays at chance (0.51) and V3's barely moves.
   - So report 14's RQ1 reading stands: messages alone (V1) do not rank games, and the reason is the content, not the pair order.
   - What the bias *did* distort is **who** gets named. With random order, V1 names the true pair in 4/12 games (vs 1/12) and V3 in 5/12 (vs 2/12). Report 14's RQ8 numbers for V1 and V3 are partly an order artefact.
2. **RQ2 needs a stronger caveat: the session effect hits V2 most.**
   - In this session the **unchanged** frozen V2 scored AUROC 0.559 (vs 0.372 in report 14). That is +0.188 [+0.007, +0.389], with score Spearman 0.653 and MAD 10.8, matching V2's RQ0.4 failure.
   - Report 14's "combining helps" (V3 − V2 = +0.365) rests partly on an unlucky V2 session.
   - As point estimates only (not pre-registered here), V3 − V2 is +0.19 in the fixed same-session arm and +0.28 in the random arm. The direction is the same; the size is smaller.
   - V1 and V3 are almost perfectly reproducible across sessions (23/24 and 22/24 identical scores).
3. **RQ3:**
   - "Same-incentive games fool messages" is **stable** across all three arms (V1 T1 vs T4b 0.34–0.37).
   - "Persona talk fools actions" is **not** stable: V2 T1 vs T3 was 0.22 in report 14 but 0.46–0.50 here, i.e. about chance rather than reversed.
   - V4 against persona talk falls from 0.79 (frozen) to 0.69 (fixed) to 0.46 (random), with wide CIs. V4's resistance to persona talk is less solid than report 14 suggested.
4. **V4 is no longer clearly ahead of V3 outside report 14's session.**
   - V4 is best in the frozen run (0.90) and the fixed arm (0.83). In the random arm, V3 (0.79) is above V4 (0.75).
   - The CIs overlap everywhere. V4's point estimate moves by up to 0.15 between arms, and report 14's 0.896 is at the upper end of what this monitor gives on these games.
   - This fits report 14's RQ5 (V4 − V3 not significant) and does not support reading V4 as clearly superior to V3.

## 6. Acceptance / checklist

| Item | Status | Evidence |
|---|---|---|
| Pre-registration committed before any call; commit + sha256 in the DEVLOG first | **PASSED** | DEVLOG part 2a (496fc28, 0d6aaa41…) |
| check_env READY; pytest 0 failed; the 4 requested mock tests (plus 2 more) | **PASSED** | 490 passed |
| Measured 3 calls; estimate within the pre-approval (≤ 90 min) | **PASSED** | ~21.5 s/call → ~68 min est.; ≈ 65 min actual |
| 192 calls, one session, interleaved; failures as missing, not retried | **PASSED** | §4.1 (0 failures) |
| Analysis exactly as pre-registered; verdict per hypothesis | **PASSED** | §4.2–4.7; self-test reproduces report 14/15 numbers |
| What it means for RQ1–RQ3 | **PASSED** | §5 |
| Figure 7 + caption | **PASSED** | `writeup/figures/fig7_pair_order_followup.png`, `captions.md` |
| Frozen file, primary results and earlier outputs unchanged | **PASSED** | frozen template/manifest hashes pinned in tests; new outputs only under `runs/followup1/` |

## 7. Deviations

- **None from the pre-registration.**
- **Additions beyond the prereg** (descriptive or quality checks):
  - the emitted key order is checked (96/96 equal to the presented order);
  - a `--selftest` mode in the analysis;
  - the V3 − V2 point estimates in §5.2, labelled not pre-registered, with no CI.
- **Two caption fixes in `writeup/figures/captions.md`** while appending Figure 7:
  - the Figure 5 caption cited "report 15 §6"; it is now §4.6;
  - the Figure 7 main-result line now says "random − fixed".
- **Not fixed:** `writeup/excerpts_22.md` has the same "report 15 §6" typo (case (c)). That file is outside this task's allowed files, so it is left for the lead.

## 8. Problems and limitations still open

- **n = 24:** only large changes are detectable. The H2 verdicts are "unclear", not "no effect".
- **Residual bias:** randomising the pair list leaves a residual last-position bias in V1 (H1 unclear). Other fixed orders (the agent list "J, M, Q, T and Z", the agent order inside views) were not varied.
- **Within-session drift:** not excluded, but interleaving spreads it over both arms.
- **These games have now been scored three times.** Nothing was tuned on them.

## 9. Next task (suggestion)

- Study 2.3 decision rules (R1–R7) on the same split, with thresholds chosen on dev.
- For the write-up:
  - report 14 stays primary;
  - add report 16 as the follow-up that (a) rules out pair order as the cause of V1's failure, (b) shows the RQ8 V1/V3 numbers were order-affected, (c) quantifies V2's session sensitivity.

## 10. Files to commit (the pre-registration is already committed)

- `configs/monitor/monitor_v3_pairs_rot.txt`, `configs/monitor/manifest_v3_pairs_ctx16k_rot.json`
- `study_2_2_views/monitor.py`, `tests/test_monitor.py`
- `scratch/p16_make_config.py`, `scratch/p16_run.py`, `scratch/p16_analysis.py`, `scratch/p16_figure.py`
- `writeup/figures/fig7_pair_order_followup.png`, `writeup/figures/captions.md`
- `notes/DEVLOG.md`, `notes/reports/16_followup_pair_order.md`

**Not committed** (Rule E): `runs/followup1/` (rot.jsonl, fixed.jsonl, run_order.json, manifest.json, analysis.json, tables.md), `runs/followup1_run.log`, `runs/followup1_ps.txt`, `cache/`.

## 11. Commit line

`Commit: exp: run pre-registered follow-up 1 (pair-order randomisation with same-session control) and report results`
