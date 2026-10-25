# 20C — G1–G4 analysis code for the granite replication (amendment 1)

Date: 2026-10-25 · Task 20C · **Machine C** · **No model calls.** No replication data exists on this machine, and none was read or waited for. No frozen file, manifest, existing module, generator file or `study_2_3_evidence/*` was changed.

## 1. Goal (from the prompt)

Write and test, **before any replication monitor output exists**, the one-run analysis of amendment 1:
- G1–G4 with their fixed decision rules, plus the descriptive measures;
- primary on all games, sensitivity without the quality-fail games;
- refusal checks run before anything is computed;
- synthetic tests, plus a reproduction of report 15C.

Then print the later run order.

## 2. What was built

| File | One line |
|---|---|
| `study_2_2_views/replication_granite.py` (new, additive) | The G1/G2/G4 rules, built with machine B's `_rule` outcome mapper (same wording conventions as the Study 2.2 replication). `verdict_g3` (opposite signs AND at least one CI excludes 0). `hypotheses` (G1–G4) and `descriptive`, per monitor and view. The precondition checks are `check_committed`, `check_configs`, `load_lines` and `load_quality`. |
| `scripts/analyse_replication_granite.py` (new) | One-run CLI with all refusals; primary and sensitivity → `results.json`. `--plan` prints the later run order. |
| `tests/test_replication_granite.py` (new) | 44 tests (§3). |

**Statistics:** 95% stratified bootstrap by type, whole games, B = 2000, seed 20261023.
- Each comparison uses the games where all its scores are present; the rest are counted as `dropped`.
- So both arms of a paired comparison use the same resample indices: two views of one monitor in G3, two monitors on one view in G4.
- G3 uses **one common game set** for both monitors, so D_llama and D_granite are computed on identical resamples.

**Refusals** (raised before any number is computed):
1. The base prereg or the amendment differs from its committed blob, or from its recorded LF sha256 (`d9d25b58…`, `778cf66b…`). A file that isn't committed is also refused.
2. The frozen monitor file is not `ccc4bf07…`, or the llama manifest differs from the frozen record.
3. The granite manifest is not `d6b38e3f…ac40`, or its digest differs.
4. A llama line is not `monitor_v3_pairs_ctx16k` / `llama3.1:8b` / `46e0c10c…`, or a granite line is not `monitor_v3_pairs_ctx16k_granite` / `granite3.3:8b` / `fd429f23…`.
5. A line's `prompt_sha256` is not the system prompt built from the committed manifest for its view. This ties every line to the exact manifest and template content.
6. A view other than V1–V4, a sample other than 0, or a duplicate line.
7. A game id outside the replication labels file, or any ORIGINAL dataset game (`data/labels.csv`).
8. A quality file not in the form `{"quality_fail": [...]}`, or one listing unlabelled ids.
9. An earlier `results.json` exists (no second run).

**Failures are data:** absent lines (persistent transport errors) and lines with no score are counted as missing per view, never fatal and never re-scored (amendment 1 §2).

## 3. How it was verified (exact commands)

```
git log -- configs/prereg_replication.md configs/prereg_replication_amendment1.md ; git diff --quiet HEAD -- <both>   # read-only
conda run -n collusion-lab python -m pytest -q -rs tests/test_replication_granite.py      # 44 passed, 0 skipped
conda run -n collusion-lab python -m pytest -v tests/test_replication_granite.py -k 15c   # PASSED
conda run -n collusion-lab python scripts/analyse_replication_granite.py --plan           # run order (§4.2)
conda run -n collusion-lab python -m pytest -q -rs                                        # 672 passed, 4 skipped (all machine-B data tests)
```

**The 44 tests:**

1. **Every outcome branch, including CI bounds exactly at the reference:**
   - G1: above → confirmed; lower bound exactly 0.5 → not confirmed; includes; below; no CI → undetermined.
   - G2: includes, including bounds exactly at 0.5 → confirmed; above → not confirmed; below → not confirmed (below chance).
   - G4: includes, including bounds exactly at 0 → confirmed; above or below → not confirmed.
   - G3: opposite signs with the llama CI or the granite CI excluding 0 → confirmed; opposite signs with both CIs including 0, or **CIs touching 0 exactly** → not confirmed; same sign → not confirmed; a zero estimate → not confirmed; no CI → undetermined.
2. **End-to-end `hypotheses`:** an all-confirmed set; a set giving G1 not confirmed (AUROC exactly 0.5, CI [0.5, 0.5]), G2 below chance and G4 not confirmed.
3. **Paired-index sharing:** identical llama and granite scores give G4 = 0.0 [0.0, 0.0] and identical D_llama / D_granite including their CIs. This is only possible when both arms use the same resamples.
4. **Missing values:** a parse failure and an absent line are dropped and counted (G1, G3, G4, descriptive).
5. **Descriptive measures:**
   - last-position max with ties, where all pairs equal gives a no-bias expectation of 1.0, and a strict T-Z top gives 0.1;
   - the count of replies naming T-Z;
   - score diagnostics;
   - top-1 accuracy and the count of replies with no named pair.
6. **Refusals:**
   - 10 bad-line cases (two wrong digests, two wrong prompt versions, wrong model, wrong `prompt_sha256`, sample 1, view V5, an unlabelled game, a duplicate);
   - an original dataset game;
   - prereg / amendment: blob differs, not committed, sha mismatch;
   - the frozen-file sha and the granite-manifest sha;
   - quality format and unknown ids;
   - a second run via the CLI. The first run used the real git and the real committed preregs, and it worked.
7. **`--plan`** prints the run order.
8. **Report 15C reproduced (granite-only measures):** on the 24 original test games, from `runs/rq9_granite/outputs/monitor.jsonl`:
   - the AUROC and CI per view equal `runs/rq9_granite/results.json` (to the 4-decimal rounding);
   - the AUROCs are 0.7292 / 0.7674 / 0.7361 / 0.5104, as in report 15C §4.2;
   - the last-position-max k and top-1 correct counts are equal too.

   The test is skipped where those local files are absent; on C it ran and passed.

## 4. Results

### 4.1 Preconditions (DEVLOG "Task 20C (part 0)", written before any code)

| File | Commit (alone) | LF sha256 | == blob |
|---|---|---|---|
| `configs/prereg_replication.md` | `2bc3d3aa19edb0aa43ccf5a6cb09e37f2dd2deeb` (09:55:12) | `d9d25b58…a1f9` | yes |
| `configs/prereg_replication_amendment1.md` | `306502e7011995bca72e5c83c64d4b99aa1931c7` (20:34:15) | `778cf66b…c7bf7` | yes |

**Machine B confirmed to the lead, before the amendment commit, that no replication view had been rendered and no replication game content had been looked at.**

**History:** a first attempt at this task stopped at this precondition because the amendment was not committed yet. Nothing was written then.

### 4.2 Run order for later (printed by `--plan`, NOT run)

1. **(a) Machine B delivers:**
   - `data/replication/clean/`, `data/replication/views/` (V1–V4);
   - `data/replication/labels.csv`, `data/replication/quality_fail.json` (`{"quality_fail": [...]}`);
   - **B's replication `monitor.jsonl`** (frozen llama monitor; only V1–V4 are read here).
2. **(b) Judge on C:** 48 calls, about 22 min, **needs the lead's OK**. `scripts/run_replication_c.py --run judge --yes`
3. **(c) Granite on C:** 192 calls, about 2.9 h (budget 3.5 h), **needs the lead's OK**. `scripts/run_monitor.py --input data/replication/views --views V1,V2,V3,V4 --run-id rq9_granite_replication --prompt monitor_v3_pairs_ctx16k_granite --sec-per-call 55 --yes`
4. **(d) One run each:** `analyse_replication_23.py` (Study 2.3) and `analyse_replication_granite.py` (G1–G4).

## 5. Acceptance criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 0 | Both preregs committed and equal to their blobs; commits + LF sha256 in the DEVLOG first; STOP if not | **PASSED** | §4.1; the first attempt stopped correctly |
| 1 | G1–G4 exactly as amendment 1 (G2 full map, G3 sign + CI condition, G4 paired across monitors) + every descriptive measure; stratified bootstrap B 2000, seed 20261023, shared indices; primary + sensitivity | **PASSED** | §2; tests 1–5, 8 |
| 2 | Every listed refusal, before computing anything | **PASSED** | §2 list; test 6 |
| 3 | Synthetic tests: every branch incl. bounds at 0.5 / 0; refusals; paired-index sharing; 15C reproduction (skip if absent) | **PASSED** | 44 passed; the 15C test ran on C |
| 4 | Run order printed, not run | **PASSED** | §4.2 |
| — | No model calls; only allowed files | **PASSED** | `git status`: the three new files + DEVLOG + this report |
| — | Time box ~1.5 h | **PASSED** | about 1 h |

## 6. Deviations from the approved plan, and why

1. **Line-to-config check by `prompt_sha256`.** The task asks for refusing lines "not from" each configuration, citing the manifest sha256. Monitor lines don't carry the manifest file hash, so each line's system-prompt hash is checked against the prompt built from the committed manifest (plus prompt version, model and digest), and the manifest file hashes are checked separately. This is stricter than a version-name check.
2. **Reuse of machine B's code.** The outcome mapper `_rule` / `UNDETERMINED` and `load_labels` come from `study_2_2_views.replication` / `.analysis`, imported and not edited, so G-wording and label parsing match the Study 2.2 replication.
3. **"Undetermined (no CI)"** is used for any G rule without a CI (B's convention). The amendment has no wording for that case.
4. **A G3 / G4 zero estimate:** a zero point estimate has no sign, so G3 is "not confirmed" in that case.

## 7. Problems and limitations still open

- **The real input formats are untested.** B's replication `monitor.jsonl` is assumed to have the same line format as `run_monitor.py` writes (it does on B for the original test run, `test_p8`). If B's lines lack `prompt_sha256` or `model`, the analysis refuses, and that would need a decision, not a silent fallback.
- **The 15C reproduction only runs where the uncommitted RQ9 outputs exist (machine C).**
- **The DEVLOG is still CRLF on machine B** (report 18b §7, lead's decision). On C it is LF.

## 8. What the next task should be

1. **Lead:** commit this task (§9).
2. **Machine B:** render the replication views (now allowed: the amendment is committed), run the quality report and the frozen llama monitor, and deliver the §4.2(a) files to C.
3. **Machine C, after the lead's OK:** the judge (≈ 22 min), then granite (≈ 2.9 h), then one run of each analysis.

## 9. Files to commit

- `study_2_2_views/replication_granite.py`
- `scripts/analyse_replication_granite.py`
- `tests/test_replication_granite.py`
- `notes/DEVLOG.md`, `notes/reports/20C_granite_replication_code.md`

## 10. Suggested commit line

`Commit: feat: add amendment-1 G1-G4 analysis for the granite replication (one run, refusals, synthetic tests)`
