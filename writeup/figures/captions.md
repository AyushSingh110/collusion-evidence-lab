# Figure captions (Study 2.2)

**Shared conventions:**
- **Confidence intervals:** 95% stratified bootstraps by episode type (whole games resampled), B = 2000, seed 20261023.
- **Test set:** 24 games (12 collusion; 4 each of placebo, persona talk and same incentive).
- **Monitor:** llama3.1:8b with prompt monitor_v3_pairs_ctx16k, frozen on dev.
- **Re-plots vs exploratory:** Figures 1, 3 and 5 re-plot reported results (report 13 dev, report 14 test). **Figures 2, 4 and 6 are exploratory, not pre-registered** (report 15).

**Figure 1 — `fig1_auroc_by_view_test.png`. How well each view separates collusion games (test set).**
- Shows test AUROC per view with 95% CIs (n = 24); the dashed line is chance (0.5). Dark bars are the five views and grey bars the three controls.
- Only the structured report (V4, 0.90 [0.77, 0.98]) has a CI clearly above chance.
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
- Report 15 §6 shows that several views favour the last-listed pair (T-Z), which can raise or lower these accuracies depending on how often T-Z is the true pair.

**Figure 6 — `fig6_code_signals_vs_V4.png`. Simple code signals vs the LLM monitor on the structured report (V4)** *(exploratory, not pre-registered).*
- Shows AUROC with 95% CIs of the game-level maximum (over the 10 pairs) of five code signals and of V4. Results are for test (n = 24) and for all 48 games pooled.
- Dep is NA in 3 games, so its n is 21 on test and 45 pooled. Its honest baseline was fitted on the 4 dev Type 2 games only.
- The action-based signals coGO, capture and G_others match V4 (all ≈ 0.87–0.94). The keyword and dependence signals (C_kw, Dep) are weaker. The pooled numbers include the dev games used for selection.
