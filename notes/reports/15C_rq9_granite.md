# 15C — RQ9: a second monitor model (granite3.3:8b) with the frozen format

Date: 2026-10-25 · Task 15C · **Machine C** (MacBook, Apple M4, Ollama 0.40.3)

- **Configuration:** `monitor_v3_pairs_ctx16k_granite` is the frozen `monitor_v3_pairs_ctx16k` (frozen file sha256 `ccc4bf07…f65f`) with **only the model changed**.
- **Design:** 24 test games × V1–V4, sample 0, one run, 96 calls. Nothing was re-scored, and no threshold was used or set.
- **Statistics:** 95% stratified bootstrap by episode type, resampling whole games, B = 2000, seed 20261023. Paired differences share the resample indices.
- **Llama comparison values** come from the frozen test run on machine B (`test_p8`, not on this machine). They are copied from report 14, report 15 §4.3 / §4.6 and report 16 §4.3.

## 1. Goal (from the prompt)

Score the 24 test games × V1–V4 once with granite3.3:8b, using the frozen v3_pairs_ctx16k format, and compare with the primary monitor (llama3.1:8b, report 14):
- AUROC per view, the ranking and Kendall tau-b;
- paired differences;
- per-type AUROCs;
- top-1 pair accuracy;
- a descriptive last-position measure;
- score diagnostics.

Plus one figure, an interpretation and limitations.

## 2. What was built

| File | One line |
|---|---|
| `configs/monitor/manifest_v3_pairs_ctx16k_granite.json` (new) | Copy of the frozen ctx16k manifest. Changes: `model` granite3.3:8b, an added `model_digest` (fd429f23…), `prompt_version`, and `_note` = "RQ9: identical to the frozen monitor_v3_pairs_ctx16k except the model". LF sha256 `d6b38e3f…ac40`. |
| `study_2_2_views/monitor.py` | One additive PROMPTS entry (`monitor_v3_pairs_ctx16k_granite`), plus its comment line. |
| `tests/test_monitor.py` | +3 tests: (1) the 7 existing prompt names produce byte-identical mock requests (hashes recorded before the edit); (2) the manifest diff is exactly {model, model_digest, prompt_version, _note}; (3) the granite request equals the frozen one except `model`. |
| `scratch/p15c_make_config.py` | Builds the manifest. It first asserts that the JSON writer reproduces the frozen file byte for byte, and refuses to overwrite. |
| `scratch/p15c_analysis.py` | All RQ9 numbers → `runs/rq9_granite/results.json`, `tables.md`. |
| `scratch/p15c_figure.py` | `writeup/figures/fig8_rq9_granite.png` |
| `writeup/figures/captions.md` | Figure 8 caption appended. |
| Outputs (not committed) | `runs/rq9_granite/outputs/monitor.jsonl` (96 lines), `manifest.json`, `run_log.txt`, `measure_log.txt`, `measure_ps.txt`, `ps_log.txt`, `results.json`, `tables.md`; cache `cache/llm/m_5acffc7a/` (see §6) |

No frozen file, existing manifest, template, earlier output or report was changed.

## 3. How it was verified (exact commands)

```
git log -1 -- configs/frozen/monitor_frozen.json ; git diff --quiet HEAD -- configs/frozen/monitor_frozen.json configs/monitor/   # read-only
conda run -n collusion-lab python scripts/check_env.py      # NOT READY only for qwen2.5:7b; llama + granite + Ollama MATCH
conda run -n collusion-lab python -B scratch/p15c_make_config.py ; diff configs/monitor/manifest_v3_pairs_ctx16k.json configs/monitor/manifest_v3_pairs_ctx16k_granite.json
conda run -n collusion-lab python -m pytest -q tests/test_monitor.py      # 73 passed
conda run --no-capture-output -n collusion-lab python -u scripts/run_monitor.py --input data/views --views V3 --games g_049148ae36,g_0f33b05330,g_1a50c4f11e --run-id rq9_granite --prompt monitor_v3_pairs_ctx16k_granite
ollama ps
conda run --no-capture-output -n collusion-lab python -u scripts/run_monitor.py --input data/views --views V1,V2,V3,V4 --games <24 test ids> --run-id rq9_granite --prompt monitor_v3_pairs_ctx16k_granite --yes   # started, paused, resumed (§4.1)
conda run -n collusion-lab python -B scratch/p15c_analysis.py
conda run -n collusion-lab python -B scratch/p15c_figure.py              # PNG checked by eye
conda run -n collusion-lab python -m pytest -q                           # 543 passed
```

## 4. Results

### 4.0 Preconditions (DEVLOG "Task 15C (part 0)", before any model call)

| Check | Result |
|---|---|
| Ollama / llama3.1:8b / granite3.3:8b | 0.40.3 / `46e0c10c…` / `fd429f23b909…f1f7`: all **MATCH**. `check_env` is NOT READY only because qwen2.5:7b is missing (accepted). |
| Frozen file | == HEAD blob, commit `89bdb79`, LF sha256 **`ccc4bf07838be73eff576f84b29389db4ee0952e6a8317eaa51d70885f47f65f`** |
| `manifest_v3_pairs_ctx16k.json` | LF sha256 `81e88222…7311` == frozen; template `fa6e62e7…3d87` |
| Views / labels / split | V1–V4: 48/48 each; labels sha256 `20849152…146e` == split; 24 test games |
| Machine state | `ollama ps` empty; 13C/17C committed; working tree clean |

### 4.1 Measurement and run

**The 3 measured calls** (test, V3, sample 0):

| Game | Latency | prompt_eval | eval | parse_ok | Truncation | done_reason |
|---|---|---|---|---|---|---|
| g_049148ae36 | 54.9 s | 2,399 | 121 | yes | no | stop |
| g_0f33b05330 | 51.3 s | 2,237 | 116 | yes | no | stop |
| g_1a50c4f11e | 59.1 s | 2,367 | 138 | yes | no | stop |

`ollama ps`: granite3.3:8b 7.8 GB, 100% GPU, context 16384.

**These are run requests:** they went to run `rq9_granite` as sample 0 with the frozen seed rule, so they count toward the 96, and the resume skipped them.

**Estimate shown:** 93 × 55 s ≈ 85 min, so pre-approved (≤ 90).

**Pause:** the live V1 calls took 65–92 s, projecting about 100–115 min. **The run was paused at 10:24:00, after 11/96 calls, to ask for the user's OK.** The user said "OK resume". The resumed session ran **10:30:06 → 11:49:38** and wrote the remaining 85 calls. The pause re-scored nothing; the request in flight at the pause had produced no output.

| View | Lines | parse_ok | Truncation | Length cuts | Missing scores | Mean latency | Max prompt_eval |
|---|---|---|---|---|---|---|---|
| V1 | 24 | 24 | 0 | 0 | 0 | 68.4 s | 1,975 |
| V2 | 24 | 24 | 0 | 0 | 0 | 37.4 s | 1,118 |
| V3 | 24 | 24 | 0 | 0 | 0 | 62.9 s | 2,458 |
| V4 | 24 | 24 | 0 | 0 | 0 | 45.8 s | 2,317 |

- 0 transport errors.
- `ollama ps` every 2 min: 41/41 snapshots show 7.8 GB, 100% GPU, context 16384.
- The sessions in `manifest.json` both record git HEAD `68b9211` and digest `fd429f23…`.

### 4.2 AUROC per view and ranking

| View | granite3.3:8b [CI] | llama3.1:8b (report 14) [CI] |
|---|---|---|
| V1 messages | 0.729 [0.549, 0.896] | 0.490 [0.299, 0.691] |
| V2 actions | **0.767 [0.604, 0.917]** | 0.372 [0.170, 0.601] |
| V3 combined | 0.736 [0.573, 0.917] | 0.736 [0.535, 0.920] |
| V4 structured | 0.510 [0.292, 0.729] | **0.896 [0.771, 0.979]** |

**Rankings:**
- granite: **V2 > V3 > V1 > V4**;
- llama: **V4 > V3 > V1 > V2**.

**Kendall tau-b = −0.667.**

**Resolution warning:** with 4 views there are only 6 view pairs, so without ties tau can only be −1, −2/3, −1/3, 0, 1/3, 2/3 or 1. −0.667 means 5 of 6 pairs are ordered oppositely. Both models agree only that V3 sits above V1. Read the two AUROC columns, not the tau.

### 4.3 Paired differences within granite (descriptive)

| Difference | granite [CI] | llama [CI] (report 14 / 15 §4.3) |
|---|---|---|
| V3 − V2 | −0.031 [−0.250, 0.191] | +0.365 [0.094, 0.611] |
| V4 − V3 | −0.226 [−0.486, 0.056] | +0.160 [−0.021, 0.351] |
| V3 − V1 | +0.007 [−0.136, 0.153] | +0.247 [0.024, 0.476] |

- None of granite's CIs excludes 0.
- Two of report 14's directions are reversed with granite: V3 − V2 and V4 − V3.

### 4.4 Per-type AUROC (Type 1 vs each negative type) and mean score per type

| View | T1 vs T2 | T1 vs T3 | T1 vs T4b | llama T2 / T3 / T4b | Mean T1/T2/T3/T4b, granite | Mean, llama |
|---|---|---|---|---|---|---|
| V1 | 0.812 [0.614, 0.958] | 0.562 [0.208, 0.875] | **0.812** [0.604, 0.958] | 0.385 / 0.740 / **0.344** | 72.5 / 22.5 / 50.0 / 22.5 | 72.9 / 73.5 / 24.5 / 88.5 |
| V2 | 0.833 [0.708, 0.958] | **0.833** [0.708, 0.958] | 0.635 [0.354, 0.875] | 0.438 / **0.219** / 0.458 | 47.5 / 0.0 / 0.0 / 25.0 | 50.8 / 45.0 / 72.0 / 47.5 |
| V3 | 0.792 [0.667, 0.917] | 0.625 [0.302, 0.875] | 0.792 [0.667, 0.917] | 0.667 / 0.917 / 0.625 | 41.7 / 0.0 / 25.0 / 0.0 | 70.5 / 39.5 / 0.0 / 63.8 |
| V4 | 0.385 [0.083, 0.729] | 0.542 [0.250, 0.813] | 0.604 [0.250, 0.917] | 1.000 / 0.792 / 0.896 | 24.4 / 30.0 / 7.0 / 5.0 | 79.2 / 10.0 / 55.0 / 35.0 |

**Report 14's "each single view is fooled by one lookalike" does not repeat with granite:**
- granite's V1 is **not** fooled by the shared-incentive games: 0.812 vs llama's 0.344;
- granite's V2 is **not** fooled by the persona games: 0.833 vs 0.219.

Granite's V1 and V3 are weakest against the persona games (0.56, 0.63). Its V4 is weak against every type.

### 4.5 Top-1 pair (12 Type 1 test games, chance 1/10), last-position measure, score diagnostics

| View | Top-1 granite | No pair named: Type 1 (all 24) | Top-1 llama | **LPM granite** | No-bias expectation (granite) | **LPM llama** (report 16 §4.3) |
|---|---|---|---|---|---|---|
| V1 | 3/12 | 8 (20) | 1/12 | 17/24 = 0.708 | 0.679 | 21/24 = 0.875 |
| V2 | 3/12 | 7 (17) | 6/12 | 15/24 = 0.625 | 0.671 | 14/24 = 0.583 |
| V3 | 2/12 | 9 (21) | 2/12 | 18/24 = 0.750 | 0.792 | 17/24 = 0.708 |
| V4 | 6/12 | 6 (13) | 7/12 | 11/24 = 0.458 | 0.429 | 7/24 = 0.292 |

LPM = the share of replies where T-Z (last in the fixed list) has the maximum score, ties included. The no-bias expectation is the mean over replies of (pairs tied at the max) / 10.

| View | Distinct game scores | Min–max | SD | Share at view max | Share game score 0 | Share all 10 pairs equal | Named pairs (count) |
|---|---|---|---|---|---|---|---|
| V1 | 3 {0, 90, 100} | 0–100 | 48.0 | 0.333 | 0.458 | 0.583 | J-M 4 |
| V2 | 4 {0, 10, 90, 100} | 0–100 | 40.9 | 0.042 | 0.583 | 0.625 | J-M 7 |
| V3 | 4 {0, 10, 90, 100} | 0–100 | 41.5 | 0.167 | 0.667 | 0.750 | J-M 3 |
| V4 | 6 {0, 8, 9, 10, 80, 100} | 0–100 | 29.9 | 0.042 | 0.292 | 0.333 | J-M 3, J-Z 2, T-Z 2, Q-T 1, M-Z 1, M-Q 1, J-T 1 |

**Reading (descriptive, no verdict):**
- **Granite's scores are coarse, close to a yes/no answer.** Each view uses 3–6 distinct game scores, and in 33–75% of replies all 10 pairs get the same score (mostly all 0). So it names a pair in only 4–11 of 24 replies.
- **Its LPM is at its no-bias expectation in every view** (within 0.05). The high values come from ties, not from preferring T-Z.
- **Granite names T-Z as the single top pair 0 times in V1–V3 and twice in V4.** Llama named T-Z 15 / 5 / 9 / 2 times in V1–V4 in the frozen run (report 15 §4.6).
- **The strong last-position pattern therefore looks like a property of llama, not of the prompt format.**
- **Possible first-position preference, unresolved:** in V1–V3 every pair granite names is J-M, the first pair (14 replies). 9 of those 14 are games whose focal pair really is J-M (3 of the 12 Type 1 test games and 1 Type 4b game). With so few named pairs, this cannot be separated from correct detection.

## 5. Acceptance criteria

| # | Criterion | Status | Evidence |
|---|---|---|---|
| 0 | Preconditions re-confirmed and in the DEVLOG before any model call | **PASSED** | §4.0; DEVLOG "Task 15C (part 0)" |
| 1 | Granite manifest = copy, only model/digest/version/note; registry entry only; byte-identical test; manifest-diff test | **PASSED** | `diff` output; 3 new tests; `monitor.py` diff is 1 entry + comment |
| 2 | 3 measured calls with all measures + `ollama ps`; no parse failure or length cut | **PASSED** | §4.1 |
| 2 | Estimate; ≤ 90 min pre-approved, else wait for OK | **PASSED** | Estimated 85 min; paused when the live pace projected > 90; resumed only after the user's OK |
| 3 | 96 calls, sample 0, one run, no re-scoring, missing values counted | **PASSED** | 96/96 parse_ok, 0 missing; 3 measured calls counted (same requests) |
| 4 | AUROC + CI, ranking, tau-b with resolution note, both columns | **PASSED** | §4.2 |
| 4 | Paired V3−V2, V4−V3, V3−V1 | **PASSED** | §4.3 |
| 4 | Per-type AUROCs + mean score per type | **PASSED** | §4.4 |
| 4 | Top-1 and ties; LPM with no-bias expectation vs llama; score diagnostics | **PASSED** | §4.5 |
| 5 | Figure 8 + caption | **PASSED** | PNG checked by eye; caption appended |
| 6 | Interpretation and limitations | **PASSED** | §7, §8 |
| — | Time box ~2 h | **PARTIAL** | The model run alone took ≈ 92 min of call time over three sessions plus a 6-min pause; the task overran the box |

## 6. Deviations from the approved plan, and why

1. **Machine id.** `COLLUSION_LAB_MACHINE=C` is exported in `~/.zshrc`, but the non-interactive shell the tools use did not load it. Consequences:
   - both run sessions record `machine_id` **`m_5acffc7a`** (the hostname-based fallback), not `C`;
   - the cache shard is `cache/llm/m_5acffc7a/` (96 granite entries), not `cache/llm/C/`;
   - the results are unaffected, because the digest is pinned and checked, and the gpu field says Apple Silicon.

   It is recorded here and not edited after the fact. The lead may want to move or alias the shard.
2. **One killed session record.** Pausing with `pkill -f scripts/run_monitor.py` also killed the wrapping shell, so the first full-run session (8 calls, 10:14–10:24) has no entry in `manifest.json`. Its 8 lines are in `monitor.jsonl` and in `run_log.txt`.
3. **`model_digest` is an added field.** The frozen manifest has no digest field; the pin check itself still uses `configs/pins.json`.
4. **The LPM no-bias expectation is shown for granite only.** Report 16 §4.3 gives the expectation for llama's random-order arm, not for the frozen run.
5. **Extra descriptive counts** (named pair = T-Z, named-pair distribution, J-M vs focal) were added because the ties-included LPM alone could not separate tie inflation from a position preference.

## 7. Interpretation (plain English)

**Does the ranking of views hold with a second model? No.**
- With granite, the action view (V2) and the message view (V1) rank collusion games as well as the combined view (V3), at about 0.73–0.77.
- The structured report (V4), clearly the best view with llama (0.896), is at chance with granite (0.510).
- The only number that is the same for both models is V3, the combined raw view, at 0.736.

**Findings from report 14 that look monitor-specific (they change with the model):**
- **V4 is the best view.** Granite rarely gives high scores on V4 (Type 1 mean 24) and spreads its few named pairs across many pairs.
- **"Combining helps" (RQ2, V3 > V2).** With granite, V3 − V2 = −0.03.
- **Messages alone and actions alone are at or below chance.** With granite they are about 0.73 and 0.77.
- **Which lookalike fools which view.** Granite's V1 is not fooled by the shared-incentive games, and its V2 is not fooled by the persona games.
- **The last-position pattern.** It looks llama-specific: granite shows none beyond its ties.

**What looks view-specific (it holds across both models):**
- V3 (messages + actions together) gives a moderate, similar ranking (0.736) with both models.
- Neither model reaches high AUROC on every view, so no view is "safe" regardless of the monitor.

**Overall:** the Study 2.2 view ranking depends on the monitor model. Report 14's conclusions should be read as "for llama3.1:8b with this prompt", not as properties of the views.

## 8. Limitations

- **Different model AND different hardware:**
  - granite on Apple Metal (machine C, M4);
  - llama on NVIDIA CUDA (machine B, RTX 3060 Laptop, 43% CPU / 57% GPU).

  Differences cannot be attributed to the model alone.
- **n = 24 test games** (12 collusion, 4 per lookalike type). The CIs are wide, and per-type AUROCs rest on 4 negatives each.
- **One sample, one session.** Report 16 showed that llama's V2 changed a lot between sessions; granite's session stability is unmeasured.
- **Same frozen prompt format,** including the fixed pair order J-M … T-Z and llama-era wording. Granite may do better with a prompt tuned for it, but none was tried (that would be a new configuration).
- **Granite's coarse scores** (many all-equal replies) make AUROC sensitive to a handful of games and leave few named pairs for top-1 and position measures.
- **The llama values** were copied from reports 14–16 and not recomputed here (`test_p8` is on machine B).

## 9. What the next task should be

1. Lead: commit this task (§10) and decide the provenance fix for the `m_5acffc7a` cache shard and machine id (§6.1).
2. Then the Study 2.3 replication code on this machine (per the addendum, a later task), following the replication pre-registration (report 18a).
3. Write-up: report Study 2.2's view ranking as monitor-dependent (RQ9), with Figure 8 next to Figure 1.

## 10. Files to commit

- `configs/monitor/manifest_v3_pairs_ctx16k_granite.json`
- `study_2_2_views/monitor.py`, `tests/test_monitor.py`
- `scratch/p15c_make_config.py`, `scratch/p15c_analysis.py`, `scratch/p15c_figure.py`
- `writeup/figures/fig8_rq9_granite.png`, `writeup/figures/captions.md`
- `notes/DEVLOG.md`, `notes/reports/15C_rq9_granite.md`

**Not committed** (Rule E): `runs/rq9_granite/`, `cache/llm/m_5acffc7a/`.

## 11. Suggested commit line

`Commit: exp: run RQ9 second monitor (granite3.3:8b, frozen format) on 24 test games x V1-V4 and report`
