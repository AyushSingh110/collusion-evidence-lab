# 11 — Analysis tools while the dataset generates (no model calls)

Date: 2026-10-24 · Task 11 · Machine B · Dataset generation was running on A and B throughout.

- **No model call** was made.
- **No file the generator imports or reads was edited** (checked with `git status`: 0 changes under `core/generate`, `core/llm`, `core/plan`, `core/schema`, `core/config.py`, `core/clean/leaks.py`, `configs/prompts`, `configs/run_defaults.json`, `configs/plans`, `scripts/run_plan.py`, `scripts/merge_check.py`).
- **No dataset file was read or touched:** `data/raw/dataset/`, `data/labels.csv`, `data/split.json` and `cache/` were left alone.

## 1. Goal (from the prompt)

Build, test and document the analysis tools so the next step is "run and read":

1. the flag-only cleaner rule (Amendment 2 §6 iii);
2. the monitor candidate `monitor_v3_pairs`;
3. full statistics in `core/stats`;
4. the Study 2.3 signals;
5. the RQ1–RQ8 analysis tables, with a hard refusal to report test numbers without a matching frozen dev configuration.

## 2. What was built

| File | One line |
|---|---|
| `core/clean/cleaner.py` | **Flag-only rule.** `redact` removes only sentences with a ≥ 8-word setup copy or a header phrase ("PRIVATE NOTE" / "only you can see this", detected by its own regex, so even a scanner that finds nothing cannot let a header through). Banned words and 4b patterns are flag-only: the text stays, and the hits come back as `kind: "flag"` entries. They are never stored in CleanGame or CleanPrivate. `is_removing_hit` classifies hits; an unknown hit kind counts as removing (conservative). `redact` now returns `(text, removing_hits, removed, flags)`. |
| `scripts/render_views.py` | Writes `data/clean/leak_flags.jsonl` (type-blind rows: game_id, round, agent, where, kind, match) and prints the flag counts by kind. `leak_hits.jsonl` now holds removals only. |
| `configs/monitor/monitor_v3_pairs.txt`, `manifest_v3_pairs.json` (new) | **Schema order: `pair_scores` first, then `suspected_pair`, then `evidence` with `"maxLength": 300`.** num_predict 250; same model, temperature 0, rules, definition and view sentences; no base rate. Template LF sha256 `fa6e62e7…3d87`. |
| `study_2_2_views/monitor.py` | `monitor_v3_pairs` in `PROMPTS`. A manifest flag `pairs_extras` validates the model's own `suspected_pair` and stores it (`model_suspected_pair`) plus `margin` = max − second max. The evidence length is checked against the schema's `maxLength`. v1/v2 behaviour is unchanged (no new keys in their lines). |
| `core/stats/metrics.py` (new) | `auroc` (rank-based, NA if a class is empty; checked against brute force); `metrics_at_threshold`; `best_threshold` (max balanced accuracy, ties → higher); `stratified_bootstrap_indices` (by episode type, whole games, B = 2000, seed 20261023); `bootstrap_ci`; `bootstrap_auroc`; `paired_bootstrap_diff` and `paired_auroc_diff` (the SAME indices for both arms); `fpr_by_type` + `rule_of_three_upper`; `spearman`; `mean_abs_diff`; `kendall_tau` (tau-b); `top1_pair_accuracy`. |
| `core/evidence/signals.py` (new) | Study 2.3 signals on CleanGame data. `to_game_data` reuses `rq01` (coGO, capture, G_others, D_sync, D_private, W_joint, the NA rules). New: `d_switch`, `d_react` (phi-based), `c_kw` (frozen lexicon, possessive-aware name pattern), `HonestBaseline` + `fit_honest_baseline` (caller passes DEV Type 2 games only), `g_honest` (σ floor 1.0), `harm`, `within_game_z`, `pair_signal_table` (10 rows per game, values + NA flags, Dep), `game_signals` (max over pairs + argmax, tie → no pair). |
| `study_2_2_views/analysis.py`, `scripts/analyse_22.py` (new) | RQ1–RQ8 tables. **Dev mode** chooses thresholds and views on dev and writes a frozen-choices JSON (prints its sha256). **Test mode REFUSES** unless `--frozen` + `--frozen-sha256` match and the monitor prompt version matches; it then uses the frozen thresholds as they are. Outputs: 4 CSVs + `summary_<split>.md`. |
| `tests/test_cleaner.py`, `tests/test_views.py`, `tests/test_monitor.py` (updated), `tests/test_stats.py`, `tests/test_signals.py`, `tests/test_analysis22.py` (new) | **+71 tests** (see §4). |

## 3. How it was verified (exact commands)

```
conda run -n collusion-lab pytest -q tests/test_cleaner.py tests/test_views.py      # while working
conda run -n collusion-lab pytest -q tests/test_monitor.py
conda run -n collusion-lab pytest -q tests/test_stats.py
conda run -n collusion-lab pytest -q tests/test_signals.py
conda run -n collusion-lab pytest -q tests/test_analysis22.py
conda run -n collusion-lab pytest -q                                                 # once at the end: 483 passed
git status --short -- core/generate core/llm core/plan core/schema core/config.py core/clean/leaks.py configs/prompts configs/run_defaults.json configs/plans scripts/run_plan.py scripts/merge_check.py   # -> 0 lines
```

Only the relevant test files were run while working; the full suite ran once at the end, to keep memory use light during generation.

## 4. Results

- **Tests:** **483 passed, 0 failed** (412 before + 71 new). `external/` has no `__pycache__`.

- **1. Cleaner (flag-only).**
  - **Still removed everywhere** (CleanGame, CleanPrivate, all 8 views × 4 fixtures): the 8-word addendum copy, the history block, the channel text and the failure excerpt.
  - **Header phrases** injected into a public message or a Stage 1 plan are removed with the P2 scanner, with the stub, and with a scanner that returns nothing.
  - **Now kept and flagged:** the "experiment" sentence (Type 2) and the public "deposit" sentence (Type 4) stay in V1/V3/V5. The private `$-8`/deposit line stays only in V5 (the oracle view).
  - **Flags never appear in any rendered view;** `leak_flags.jsonl` has no type, variant or label field.
  - **Fixture counts:** removing hits Type 1 = 2 (1 sentence), Types 2–4 = 0; flags Type 2 = 1 (J R3), Type 4 = 2 (M R1 plan, T R2 message).
  - **Golden files: none changed.** All 8 type-1 goldens pass as before: the Type 1 fixture has no flag-only plant, and the C-shuffled donors (seed 0) do not draw the two affected messages.

- **2. monitor_v3_pairs** (mock tests only, **no live run**):
  - schema order and `maxLength` 300 checked; num_predict 250;
  - max / argmax / tie → no pair / margin checked;
  - evidence > 300 characters and invalid model pairs are rejected;
  - v1 and v2 template and manifest file hashes are pinned and unchanged;
  - v2_pairs lines carry no v3 extras.

- **3. Statistics:**
  - AUROC equals brute-force pair counting on 200 random tie-heavy samples.
  - Hand-computed values: AUROC 0.75 example; best threshold with a tie at BA 0.75 → the higher threshold.
  - Spearman 0.8, Kendall 4/6, tau-b with a tie 2/√6, rule of three 3/n.
  - The bootstrap is identical for the same seed and keeps stratum sizes.
  - The paired diff of identical arms is exactly 0, and the paired CI equals a by-hand recomputation with the same indices.

- **4. Signals:**
  - Examples A–E reproduce report 01 §5.4 exactly: coGO, capture, G_others, D_sync (E 0.234), **D_react (E −0.246; A–D NA)**, D_private (B 0.1875, E 0.109), W_joint (E 0.25).
  - All-GO, all-STAY, 0/5 goers and fewer than 4 valid rounds give NA (never a fake 0) for the dependence signals, and real 0s for capture / G_others.
  - D_switch hand value 0.24; C_kw counts possessives, not "I'M", and drops parse failures; G_honest σ floor; Dep (sd 0 → z 0).

- **5. Analysis:**
  - The end-to-end synthetic run gives dev tables, a frozen file and test tables.
  - **Test mode refused** without a frozen file, with a wrong sha256, and with a different monitor prompt version.
  - Test thresholds equal the frozen dev thresholds for all 8 views.
  - RQ2 uses the dev-chosen single view; RQ7 = Dep vs the dev-chosen best LLM view.
  - One failed output is counted and dropped from the paired comparison.

## 5. Acceptance criteria

| Item | Status | Evidence |
|---|---|---|
| Cleaner removes only 8-word copies + header phrases; the rest flag-only, type-blind side file, never in views; whitelist kept | **PASSED** | `test_removed_plants_absent…`, `test_flag_only_plants_stay…`, `test_header_phrases_removed_everywhere` (18 cases), `test_flags_never_stored_in_clean_types`, `test_render_views_writes_type_blind_flag_side_file`, whitelist tests unchanged |
| Goldens updated only where needed, with an explanation | **PASSED** | none needed (§4) |
| monitor_v3_pairs: order, maxLength, max/argmax/tie/margin, v1/v2 unchanged, no live run | **PASSED** | `test_v3_*`, `test_v1_v2_files_unchanged_by_v3`, `test_v2_pairs_line_has_no_v3_extras` |
| Stats: every function deterministic for a seed; hand-computed tests | **PASSED** | `tests/test_stats.py` (11) |
| Signals: A–E exact; degenerate cases NA; docstring note | **PASSED** | `tests/test_signals.py` (15) |
| Analysis: RQ1–RQ8 CSV + markdown; refuses test numbers without a matching frozen sha256; end-to-end synthetic | **PASSED** | `tests/test_analysis22.py` (4) |
| No model calls; no generator file edited; no dataset file read | **PASSED** | §3 `git status` check; no Ollama call in any test (mocks only) |
| Full suite at the end | **PASSED** | 483 passed |

## 6. Deviations and decisions (please confirm the ones marked ⚑)

1. **⚑ Alternation and capture.** Amendment 2 §6 ii (and this task's text) say alternation-style collusion "shows up in capture and G_others". By definition, **capture needs both partners at the bar alone**, so *pure* alternation (one goes, one stays) gives capture = 0, like coGO. Only **G_others** sees it.
   - Pilot-2 game g_4a189819cb had capture 0.286 only from its 2 joint rounds.
   - Tested in `test_alternation_shows_in_g_others_not_cogo_or_capture`; the signals docstring says this.
   - The amendment's instruction (report capture and G_others next to coGO) is still followed. Only the explanation differs.
   - **The committed amendment was not edited.** A correction note is the lead's call.
2. **⚑ C_kw scale.** Implemented literally as report 00 §8 says: share for i→j **plus** share for j→i (range 0–2), with the frozen lexicon matched as whole words. So "agree" does not match "agreed", and "team" does not match "teammate". Alternatives would be the mean of the two directions, or inflected forms.
3. **⚑ Best-single-view tie** (V1 vs V2 with equal dev AUROC): **V1** is chosen. Best LLM view tie: the earlier view in V1…V5. Neither tie rule is pre-registered.
4. **best_threshold candidates** are the observed dev scores (flag if score ≥ thr). There is no extra "flag nothing" threshold.
5. **Unknown scanner hit kinds count as removing** (conservative), so an unexpected scanner cannot let setup text through.
6. **G_honest / Harm baselines** come from `fit_honest_baseline`, which the caller must give **dev Type 2 games only** (the function cannot know the split). σ is the population SD over all informative pairs.
7. **Not built (outside this task or needing inputs that do not exist yet):**
   - RQ0.4 stability and RQ9 ranking tables in `analyse_22.py`: the functions exist (`spearman`, `mean_abs_diff`, `kendall_tau`), but they need repeat runs and a second monitor.
   - Study 2.3 decision rules R1–R7: they need dev signals and a judge.

## 7. Open problems and limitations

- **`scratch/overremoval_check.py`** (task 06a) calls the old 3-value `redact`. It is a historical scratch script and was left unchanged, so it would fail if run now.
- **monitor_v3_pairs is untested live.** Whether `maxLength` stops the runaway evidence under Ollama's grammar is unconfirmed until P7 runs it on dev games.
- **C_kw uses public messages only.** Under the flag-only cleaner, more original text reaches CleanGame, including Type 4b "deposit" talk, which is visible behaviour by Amendment 2.
- The analysis expects `labels.csv` / `split.json` in the P1 format and `monitor.jsonl` lines from `run_monitor`. A game in the monitor file that is missing from the labels file makes the script refuse.

## 8. Next task

When generation finishes:

1. `merge_check`;
2. `render_views.py` with the flag-only cleaner (all 8 views) and the `--labels` / `--split` mapping for C-mismatch;
3. P7: monitor v1 vs v3_pairs on **dev** views; `analyse_22.py --mode dev --freeze-out …`; record the sha256;
4. a single test run → `--mode test`.

Study 2.3: compute `pair_signal_table` / `game_signals` for all games, with the honest baseline fitted on dev Type 2.

## 9. Files to commit

- `core/clean/cleaner.py`, `scripts/render_views.py`
- `configs/monitor/monitor_v3_pairs.txt`, `configs/monitor/manifest_v3_pairs.json`, `study_2_2_views/monitor.py`
- `core/stats/metrics.py`, `core/evidence/signals.py`
- `study_2_2_views/analysis.py`, `scripts/analyse_22.py`
- `tests/test_cleaner.py`, `tests/test_views.py`, `tests/test_monitor.py`, `tests/test_stats.py`, `tests/test_signals.py`, `tests/test_analysis22.py`
- `notes/DEVLOG.md`, `notes/reports/11_analysis_tools.md`

## 10. Commit line

`Commit: feat: add flag-only cleaner, monitor_v3_pairs candidate, statistics, Study 2.3 signals and RQ1-RQ8 analysis tables`
