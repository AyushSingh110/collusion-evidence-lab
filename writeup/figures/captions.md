# Figure captions (Study 2.2)

**Shared conventions:**
- **Confidence intervals:** 95% stratified bootstraps by episode type (whole games resampled), B = 2000, seed 20261023.
- **Test set:** 24 games (12 collusion; 4 each of placebo, persona talk and same incentive).
- **Monitor:** llama3.1:8b with prompt monitor_v3_pairs_ctx16k, frozen on dev.
- **Re-plots vs exploratory:** Figures 1, 3 and 5 re-plot reported results (report 13 dev, report 14 test). **Figures 2, 4 and 6 are exploratory, not pre-registered** (report 15).

**Figure 1 — `fig1_auroc_by_view_test.png`. How well each view separates collusion games (test set).**
- Shows test AUROC per view with 95% CIs (n = 24); the dashed line is chance (0.5). Dark bars are the five views and grey bars the three controls.
- V4 has the highest AUROC (0.90 [0.77, 0.98]); the CIs of V3 and V5 also exclude chance.
- V1, V3 and C-mismatch have a degenerate frozen threshold of 0, which flags every game. Their threshold metrics carry no information, but their AUROC (shown) is threshold-free.

**Figure 2 — `fig2_per_type_scores_test.png`. Monitor score per test game by episode type** *(exploratory, not pre-registered).*
- Each dot is one test game; the black bar is the type mean. There are 12 Type 1 games and 4 games of each negative type.
- Persona-talk games (T3) score high in the actions view (V2). Same-incentive games (T4b) score highest of all in the messages view (V1).
- V4 is the only view where every collusion game (T1) scores above every placebo game (T2).

**Figure 3 — `fig3_roc_V1_V2_V3_V4_test.png`. ROC curves, test set.**
- Shows ROC curves for the four public views on the 24 test games; scores are coarse (few distinct values), so the curves have few steps.
- V4 reaches TPR 1.0 at FPR 0.25. V2 lies mostly below the diagonal (AUROC 0.37).
- No CIs are drawn. See Figure 1 or report 14 §4.2 for them.

**Figure 4 — `fig4_dev_vs_test_auroc.png`. Dev vs test AUROC per view** *(exploratory, not pre-registered).*
- Shows AUROC with 95% CIs on the 24 dev games (grey) and the 24 test games (dark), same frozen monitor configuration. Dev was used to choose the format and thresholds.
- The order of the views agrees only weakly between splits (Kendall tau-b 0.26). V3 changes most (0.32 → 0.74; unpaired difference +0.42 [0.14, 0.68]).
- V4 is the best view on both splits.

**Figure 5 — `fig5_rq8_pair_accuracy.png`. Who is the colluding pair? (top-1 accuracy).**
- Shows the share of the 12 collusion games per split in which the monitor's named pair (or the code signal's argmax pair) equals the true pair. The dashed line is chance, 1 in 10 pairs.
- No CIs are drawn: with n = 12, one game is 8 points.
- The Dep code signal was not computed on dev in report 13 ("n/a").
- Report 15 §4.6 shows that several views favour the last-listed pair (T-Z), which can raise or lower these accuracies depending on how often T-Z is the true pair.

**Figure 6 — `fig6_code_signals_vs_V4.png`. Simple code signals vs the LLM monitor on the structured report (V4)** *(exploratory, not pre-registered).*
- Shows AUROC with 95% CIs of the game-level maximum (over the 10 pairs) of five code signals and of V4. Results are for test (n = 24) and for all 48 games pooled.
- Dep is NA in 3 games, so its n is 21 on test and 45 pooled. Its honest baseline was fitted on the 4 dev Type 2 games only.
- The action-based signals coGO, capture and G_others match V4 (all ≈ 0.87–0.94). The keyword and dependence signals (C_kw, Dep) are weaker. The pooled numbers include the dev games used for selection.

**Figure 7 — `fig7_pair_order_followup.png`. Follow-up 1: randomising the order of the 10 pairs** *(pre-registered follow-up, commit 496fc28; reported separately in report 16; it does not change report 14).*
- **Arms:** the 24 test games × V1–V4 were scored in three arms.
  - Grey: fixed pair order, original test run (report 14).
  - Dark: fixed pair order, re-scored in the follow-up session.
  - Red: random pair order per call, the same session, interleaved with the dark arm.
- **Left panel:** AUROC with 95% CIs (stratified bootstrap, B = 2000, seed 20261023).
- **Right panel:** the share of replies in which the last-listed pair gets the top score; the black ticks show the share expected with no position bias (allowing for ties).
- **Main result:** randomising the order cuts the last-position effect in V1 (21/24 → 10/24) and V3 (19/24 → 9/24) but changes no view's AUROC clearly (all random − fixed paired CIs include 0).

**Figure 8 — `fig8_rq9_granite.png`. RQ9: the same frozen monitor prompt with a second model (granite3.3:8b)** *(task 15C, machine C; test set n = 24, one sample, one session).*
- **Left:** test AUROC per view with 95% CIs (stratified bootstrap, B = 2000, seed 20261023): llama3.1:8b from the frozen test run (report 14, machine B, NVIDIA) vs granite3.3:8b (Apple M4). The ranking of the views does not carry over (Kendall tau-b −0.67, a coarse measure with 4 views): only V3 is the same (0.736 for both), and V4, best with llama, is at chance with granite.
- **Right:** share of replies in which the last-listed pair (T-Z) has the top score, ties included; the black ticks show granite's no-bias expectation given its many ties (most granite replies give all pairs the same score). Granite sits at its expectation in every view and names T-Z as the single top pair only twice (V4), so the strong last-position pattern looks specific to llama, not to the prompt format.

**Figure 9 — `fig9_replication_22.png`. Study 2.2: original test vs pre-registered replication** *(replication pre-registered: `configs/prereg_replication.md`, 2bc3d3a, and amendment 1, 306502e; frozen prompts; one sample per call, one run per monitor).*
- **Series:** AUROC with 95% CIs (stratified bootstrap, B = 2000, seed 20261023).
  - Grey: llama3.1:8b on the original 24 test games (report 14 §4.2).
  - Dark: llama on the 48 replication games (report 21 §4.7; V2 / V3 from report 22C §4.4).
  - Red: granite3.3:8b on the same 48 games (report 22C §4.4).
- **Capture:** the model-free capture signal (test: report 15 §4.4; replication: report 21 §4.7, R10a).
- **Views not shown:** V5 and the controls; their replication AUROCs are not in the reports except C-shuffled, which passed (R9, 0.457).
- **Main result:** the structured report's original 0.896 shrank to 0.636. No LLM view of either monitor reaches 0.7 on the new games, while capture stays at about 0.90.

**Figure 10 — `fig10_replication_23.png`. Study 2.3: frozen decision rules, original test vs replication** *(pre-registered: `configs/prereg_replication.md` §4; frozen rules `ce0b8840…`, not refit; one judge sample).*
- **Series:** AUROC with 95% CIs.
  - Grey: the 24 original test games (report 17C, as in `writeup/results_23.md` §1–2; values copied from the report, since that results file is on machine C).
  - Dark: the 48 replication games (report 22C §4.2, from `runs/replication_23/results.json`).
- **Not shown:** R4 and R5 are binary rules, so they have no AUROC.
- **Main result:** the gain rule R2 replicates (0.872 → 0.885), and the talk-only judge R1 stays near chance (0.396 → 0.543). The combined rules R6 / R7 do not beat R2.
