# Study 2.2 — final results (pilot)

**Question (Study 2.2):** which view of a game record lets an LLM monitor detect two colluding agents best? The candidates are messages, actions, both together, a code-built structured report, and private plans.

**Setup (one line):**
- **Game:** El Farol, 5 agents (`qwen2.5:7b`), 8 rounds.
- **Data:** 48 games (24 dev / 24 test; each split 12 collusion + 4 placebo + 4 persona talk + 4 same-incentive).
- **Monitor:** `llama3.1:8b` (format `monitor_v3_pairs_ctx16k`), frozen on dev, then run once on test.

**How to read the numbers:**
- **Sample size:** every number is from a **pilot with n = 24 test games** unless marked dev, pooled, follow-up or **replication** (48 new games, pre-registered; reports 21 and 22C, cited as R21 / R22C).
- **Confidence intervals:** CIs are 95% stratified bootstraps by episode type (B = 2000, seed 20261023).
- **Citations:** "R14 §4.3" means report 14, section 4.3 (`notes/reports/`).
- **Sourcing:** numbers are copied from the reports, never recomputed here. Where a report gives no paired CI, only the reported values are shown.
- **Pre-registration:** the primary comparisons are **RQ2 and RQ5**. Everything else is exploratory, and no multiple-comparison correction is applied (R14, "Read this first").

---

## a) Headline answer

**Final answer** (original test + pre-registered replication on 48 new games):

- **Model-free behaviour signals were the most reliable evidence, and they replicated.**
  - capture 0.900 [0.811, 0.965] on the new games (R21 §4.7, R10a);
  - capture beat the best LLM view: capture − V4 +0.264 [0.121, 0.412] (R21 §4.7, R10b);
  - the coalition-gain signal: 0.885 [0.786, 0.961] (R22C §4.2, E1).
- **Both LLM monitors were mediocre and inconsistent on new games.** Every view V1–V4 lies between 0.32 and 0.66 for both models:
  - llama V1 0.505, V2 0.324, V3 0.565, V4 0.636;
  - granite V1 0.618, V2 0.628, V3 0.662, V4 0.582 (R21 §4.7; R22C §4.4).
- **Messages alone never worked:** 0.490 on the original test (R14 §4.2) and 0.505 on the replication (R21 §4.7, R1 confirmed).
- **Talk-only judging was near chance:** the judge R1 scored 0.396 on the original test and 0.543 [0.392, 0.693] on the replication (R22C §4.2, E2 confirmed).
- **Private plans added nothing:** V5 − V3 −0.031 on the test and −0.022 [−0.192, 0.155] on the replication (R14 §4.7; R21 §4.7).
- **Combining evidence did not beat gain alone:** R6 − R2 −0.080 on the test and −0.059 [−0.135, 0.010] on the replication (R22C §4.2, E3 not replicated).
- **The structured report's advantage did not replicate.** V4 fell from 0.896 to 0.636. It no longer beat the raw combined view (R4 +0.071, not replicated) or a raw view of the same length (R5 −0.034, not confirmed) (R21 §4.7).
- **The view ranking depends on the monitor.** Llama's preference for the structured report is not shared by granite (G3, R22C §4.4).
- **llama's last-position bias replicated:** in V1, the last-listed pair had the top score in 44/48 replies (R21 §4.8). The bias is llama-specific (R22C §4.4).

**Why the original V4 result was optimistic.** V4 was the best of the views on the dev games, and it was then measured on only 24 test games (12 collusion). Its 0.896 [0.771, 0.979] was a single estimate with a wide CI; on 48 new games it was 0.636 [0.507, 0.751] (R14 §4.2; R21 §4.7).

**Small-sample optimism.** Both monitors' best first-test results shrank on the replication:
- llama V4: 0.896 → 0.636 (R14 §4.2 → R21 §4.7);
- granite V2: 0.767 → 0.628 (R15C §4.2 → R22C §4.4).

**LLM-monitor reliability problems** (section d):
- the single-score format returned a constant 80 on 96/96 dev calls (R13 §2);
- llama's last-position bias (above);
- a session effect of +0.188 [+0.007, +0.389] on V2 (R16 §4.4);
- V4 flagged all 8 persona games at its frozen threshold on the replication (R21 §4.8).

**Link to Study 2.3** (`writeup/results_23.md`, sections 1–6): gain is reliable and replicated; talk alone is not; combining does not beat gain; shared-incentive lookalikes remain the hardest.

---

## b) RQ status table

| RQ | What it asks | Key number(s) [95% CI] | Source | Verdict (in this pilot) |
|---|---|---|---|---|
| RQ0.1 | Does real collusion happen in Type 1 games? | Pilot 2 (Amendment 1 gate): uptake 4/4, falsification 0/2, focal pair top by coGO 4/4, b2 4/4 + 4/4, hand agreement 96.9% (κ 0.931). Pilot 1 (frozen rule): uptake 2/4 → FAIL. Dataset check: uptake 24/24, uptake AND effect 23/24 | R10 §B3, §B4; R12 §4.3 | **PASS** under Amendment 1 (pilot 1 failure stays on record) |
| RQ0.2 | Do the lookalikes behave as designed? | Type 3: 7/8 as designed, 1 partly. Type 4b: 6/8 as designed, 2 not. All 8 Type 4b games mention the "deposit" in public | R12 §4.4, §5 | **Largely as designed**, with an unplanned public "deposit" clue |
| RQ0.3 | No leakage into views? | Removed setup copies 0/0/0/0; grep of 384 views clean. C-shuffled dev AUROC 0.465 [0.250, 0.667]; on test 0.632 [0.431, 0.833] | R12 §4.5; R13 §3; R14 §4.10 | **PASS** (both CIs include 0.5) |
| RQ0.4 | Are monitor scores stable across repeats? | MAD / Spearman: V1 0.44 / 0.971; **V2 5.00 / 0.676**; V3 0 / 1.000; V4 0 / 1.000; V5 5.44 / 0.851 | R13 §4 | **PASS for V1, V3, V4, V5; FAIL for V2** (limitation) |
| RQ1 | AUROC per view (test) | V1 0.490 [0.299, 0.691]; V2 0.372 [0.170, 0.601]; V3 0.736 [0.535, 0.920]; **V4 0.896 [0.771, 0.979]**; V5 0.705 [0.517, 0.882]; C-mismatch 0.549; C-length 0.611; C-shuffled 0.632 | R14 §4.2 | V4 ranks best. V3 and V5 CIs also exclude 0.5 on test; V1 and V2 are at or below chance. V1, V3 and C-mismatch thresholds are degenerate (flag everything) |
| **RQ2** (primary) | V3 − best single view (dev-chosen V2) | **+0.365 [0.094, 0.611]** | R14 §4.3 | "Combining helps" by the pre-registered wording, but **FRAGILE** (V2 failed RQ0.4; pooled +0.040 [−0.155, 0.238], R15 §4.2; V2 session effect +0.188 [+0.007, +0.389], R16 §4.4) |
| RQ3 | False positives per negative type at the frozen thresholds | V4: T2 0/4, T3 2/4, T4b 1/4. V2: 2/4, 3/4, 2/4. V5: 0/4 each. V1 / V3 / C-mismatch: 4/4 everywhere (degenerate). Supplementary AUROC: V1 T1 vs T4b 0.344 [0.12, 0.65]; V2 T1 vs T3 0.219 [0.00, 0.62] | R14 §4.4 | Each single view is fooled by one lookalike. Pre-stated expectation "Type 3 fools V1" was **not confirmed** (reversed) |
| RQ4 | V3 − C-mismatch (cross-checking words vs actions) | +0.188 [−0.028, 0.386] | R14 §4.5 | No clear evidence of cross-checking at this sample size |
| **RQ5** (primary) | V4 − V3; V4 − C-length | V4 − V3 **+0.160 [−0.021, 0.351]**; V4 − C-length **+0.285 [0.017, 0.556]** | R14 §4.6 | Structure vs raw: **no clear difference**. Structure vs same length: **structure better** |
| RQ6 | V5 − V3 (oracle gap) | −0.031 [−0.267, 0.236] | R14 §4.7 | No measurable gain from private plans |
| RQ7 | Code signal (Dep) − best LLM view (V4) | −0.173 [−0.382, −0.009] (n = 21; Dep NA in 3) | R14 §4.8 | V4 beat Dep. But simpler action signals match V4 (exploratory, R15 §4.4), so this is **not** "LLM beats code" |
| RQ8 | Top-1 pair accuracy (12 Type 1 test games; chance 0.1) | V1 1/12, V2 6/12, V3 2/12, **V4 7/12**, V5 5/12, Dep argmax 5/12. With random pair order: V1 4/12, V3 5/12, V4 8/12 | R14 §4.9; R16 §4.5 | V4 names the pair best. The V1 / V3 numbers are partly a pair-order artefact |
| RQ9 | V1–V4 ranking with a second monitor model (`granite3.3:8b`, frozen format, only the model changed), and Kendall τ | granite AUROC: V1 0.729 [0.549, 0.896]; V2 0.767 [0.604, 0.917]; V3 0.736 [0.573, 0.917]; V4 0.510 [0.292, 0.729]. Kendall τ-b −0.667 (low resolution: 4 views, 6 pairs, so 5 of 6 pairs ordered oppositely) | R15C §4.2 | **View ranking is monitor-dependent** (granite V2 > V3 > V1 > V4 vs llama V4 > V3 > V1 > V2) |
| Follow-up 1 | Does pair-order position bias explain the raw-view results? | Last-pair-max drop (random vs fixed, same session): V1 +0.458 [0.292, 0.667], V3 +0.417 [0.167, 0.667]. AUROC change: V1 +0.017 [−0.229, +0.281], V3 +0.042 [−0.198, +0.285], V4 −0.076 [−0.240, +0.111] | R16 §4.3, §4.2, §4.7 | H1: V3 supported, V1 unclear. **H2: unclear** (no clear AUROC gain). H3: supported. The bias is real but **does not explain** the raw-view failure |

---

## c) Robustness table

**Columns:**
- "Test" is report 14.
- "Dev" is report 13; it was used for choices, so it is in-sample.
- "Pooled" is report 15: all 48 games, including the dev selection data.
- "Follow-up" is report 16: the same 24 test games re-scored in a new session, as a fixed-order arm and a random-order arm.
- "RQ9 granite" is report 15C: the same 24 test games × V1–V4 scored once by `granite3.3:8b` with the frozen prompt (machine C). V5 and the controls were not scored.

**Labels:**
- **ROBUST:** the same direction and conclusion everywhere it was measured.
- **FRAGILE:** the conclusion changes between splits or sessions.
- **NOT SUPPORTED:** the claim fails its own test.
- **"(llama only)":** the claim holds for llama3.1:8b but not with granite3.3:8b (RQ9).
- **"Pilot label"** is the label before the replication. **"Final label"** uses the replication (R21 / R22C):
  - **REPLICATED:** the claim held on the 48 new games;
  - **NOT REPLICATED:** it did not;
  - **CONSISTENT NULL:** no effect was detected anywhere;
  - **LLAMA ONLY:** it holds for llama but not for granite;
  - **MONITOR-DEPENDENT:** the answer changes with the monitor model.

| Claim | Test (R14) | Dev (R13) | Pooled (R15) | Follow-up (R16) | RQ9 granite (R15C) | Pilot label | Replication (R21 / R22C) | Final label (reason) |
|---|---|---|---|---|---|---|---|---|
| Messages alone (V1) fail | AUROC 0.490 [0.299, 0.691] (§4.2) | 0.431 [0.219, 0.646] (§5) | 0.459 [0.323, 0.597] (§4.2) | fixed 0.490 [0.299, 0.691], random 0.507 [0.306, 0.705] (§4.2) | **does not hold**: V1 0.729 [0.549, 0.896] (§4.2) | ROBUST (llama only) | llama 0.505 [0.363, 0.655], R1 confirmed (R21 §4.7); granite 0.618 [0.474, 0.756] (R22C §4.4) | **REPLICATED**: llama at chance again, and granite's 15C value did not hold on new games (its CI includes 0.5) |
| Actions alone (V2) fail | 0.372 [0.170, 0.601] (§4.2) | 0.493 [0.260, 0.726] (§5) | 0.447 [0.302, 0.595] (§4.2) | fixed 0.559 [0.319, 0.788], random 0.514 [0.295, 0.733] (§4.2) | **does not hold**: V2 0.767 [0.604, 0.917], granite's best view (§4.2) | ROBUST (llama only) | llama 0.324 [0.186, 0.469]; granite 0.628 [0.488, 0.754], G1 not confirmed (R22C §4.4) | **REPLICATED**: below chance with llama, and not reliably above chance with granite |
| Combining helps (RQ2, V3 − V2) | +0.365 [0.094, 0.611] (§4.3) | −0.174 [−0.406, 0.056] (§5, in-sample) | +0.040 [−0.155, 0.238] (§4.2) | point estimates only: +0.19 (fixed), +0.28 (random) (§5) | **does not hold**: −0.031 [−0.250, 0.191] (§4.3) | FRAGILE (llama only) | R3 +0.241 [0.063, 0.419], replicated (R21 §4.7) | **LLAMA ONLY**: replicated with llama, but it rests on llama's below-chance V2 (0.324) and does not hold with granite (R15C) |
| Structure beats raw (RQ5, V4 − V3) | +0.160 [−0.021, 0.351] (§4.6) | +0.444 [0.146, 0.729] (§5, in-sample) | +0.350 [0.166, 0.534] (§4.2) | V4 vs V3 AUROC: fixed 0.826 vs 0.750; random 0.750 vs 0.792 (§4.2) | **does not hold**: −0.226 [−0.486, 0.056] (§4.3) | FRAGILE (llama only) | R4 +0.071 [−0.128, 0.247], not replicated (R21 §4.7) | **NOT REPLICATED**: no clear advantage on new games |
| Structure beats same length (V4 − C-length) | +0.285 [0.017, 0.556] (§4.6) | AUROC 0.764 vs 0.583 (§5; no paired CI reported) | +0.237 [0.030, 0.443] (§4.2) | not measured (C-length not re-run) | not measured (C-length not scored); granite's V4 is at chance, 0.510 [0.292, 0.729] (§4.2) | ROBUST (llama only; not tested with granite) | R5 −0.034 [−0.212, 0.133], not confirmed (R21 §4.7) | **NOT REPLICATED**: the structured report's advantage over an equally short raw view vanished |
| Private plans do not help (RQ6, V5 − V3) | −0.031 [−0.267, 0.236] (§4.7) | AUROC 0.583 vs 0.319 (§5; no paired CI reported) | +0.149 [−0.062, 0.347] (§4.2) | not measured (V5 not re-run) | not measured (V5 not scored) | CONSISTENT NULL | R8 −0.022 [−0.192, 0.155] (R21 §4.7) | **CONSISTENT NULL**: no detectable gain in any run (absence of evidence, not evidence of no effect) |
| Same-incentive (T4b) fools messages | V1 T1 vs T4b 0.344 [0.12, 0.65] (§4.4) | not reported per type | 0.359 [0.190, 0.562] (§4.2) | fixed 0.344 [0.125, 0.646], random 0.365 [0.115, 0.625] (§4.6) | **does not hold**: V1 T1 vs T4b 0.812 [0.604, 0.958] (§4.4) | ROBUST (llama only) | R6 0.495 [0.297, 0.716], confirmed (R21 §4.7; llama) | **LLAMA ONLY**: confirmed again with llama; granite did not show it on the original test (no granite replication value reported) |
| Persona talk (T3) fools actions | V2 T1 vs T3 0.219 [0.00, 0.62] (§4.4) | descriptive only: V2 flags Type 3 games (§5) | 0.266 [0.049, 0.526] (§4.2) | fixed 0.458 [0.083, 0.854], random 0.500 [0.156, 0.844] (§4.6) | **does not hold**: V2 T1 vs T3 0.833 [0.708, 0.958] (§4.4) | FRAGILE (llama only) | R7 0.352 [0.154, 0.578], not confirmed (R21 §4.7) | **NOT REPLICATED**: the CI includes 0.5 on new games |
| Code action signals are competitive with V4 (exploratory → pre-registered R10) | coGO 0.896, capture 0.896, G_others 0.872 vs V4 0.896 (R15 §4.4, test) | not reported separately | coGO 0.885, capture 0.944, G_others 0.906 vs V4 0.837 (R15 §4.4) | not measured | not applicable to the signals (model-free); granite's best view is V2 0.767 [0.604, 0.917] (§4.2) | CONSISTENT (exploratory) | capture 0.900 [0.811, 0.965], R10a confirmed; capture − V4 +0.264 [0.121, 0.412], R10b capture better (R21 §4.7) | **REPLICATED**, and stronger: capture now clearly beats the best LLM view |
| Position bias exists (last-listed pair gets the top score) | T-Z max V1 21/24, V3 17/24, V4 7/24 (R15 §4.6) | V1 22/24, V3 22/24, V4 7/24 (R15 §4.6) | — | fixed arm V1 21/24, V3 19/24; drop with random order V1 +0.458 [0.292, 0.667], V3 +0.417 [0.167, 0.667] (§4.3) | **does not hold**: last-position-max share at the no-bias expectation in every view (e.g. V1 0.708 vs 0.679); T-Z named as the single top pair 0 times in V1–V3 (§4.5) | llama-specific | llama V1 44/48 (no-bias expectation 0.215), C-shuffled 48/48 (R21 §4.8); granite at its tie expectation, T-Z named 0–3 times (R22C §4.4) | **LLAMA ONLY**: replicated strongly for llama, absent for granite |
| Position bias explains the raw-view failure | — | — | — | H2: V1 +0.017 [−0.229, +0.281], V3 +0.042 [−0.198, +0.285] (§4.7) | — | NOT SUPPORTED | not re-tested | **NOT SUPPORTED** (follow-up 1; not part of the replication) |
| View ranking depends on the monitor (RQ9 / G3) | llama V4 > V3 > V1 > V2 (R14 §4.2) | — | — | — | granite V2 > V3 > V1 > V4, τ −0.667 (§4.2) | monitor-dependent | G3 confirmed: llama V4 − V2 +0.313 [0.127, 0.481]; granite −0.046 [−0.251, 0.152] (R22C §4.4) | **MONITOR-DEPENDENT**: llama's preference for the structured report is not shared by granite (G3), and neither monitor is good on new games |

---

## d) Monitor reliability findings

1. **Single-score format collapses to a constant.**
   - Format v1 (one 0–100 score per game) returned **80 in 96/96 dev calls** (R13 §2); synthetic runs showed 15/16 at 80 (R05 §11.3, cited in R13 §2).
   - It was ruled ineligible under the lead's constant-score rule, decided on dev before any test call (R13 §0).
   - Per-pair scoring (v3_pairs) gave 4–10 distinct values per view (R13 §0).
2. **Position / recency bias in the pair list** — llama-specific (RQ9: granite shows no last-position preference beyond ties, R15C §4.5).
   - With the fixed order (J-M … T-Z), the last pair T-Z got the top score in 21/24 V1 and 17/24 V3 test replies, and in 24/24 C-shuffled replies, but in only 7/24 V4 replies (R15 §4.6). T-Z is the true pair in 1 of 12 test collusion games (R15 §4.6).
   - Randomising the order cut this to 10/24 (V1) and 9/24 (V3) (R16 §4.3).
   - In V1 the last-listed pair still gets the top score more often than chance (0.417 [0.250, 0.625] vs an expected 0.217), so V1 has a recency bias beyond the T-Z habit (R16 §4.3, §4.7).
   - The bias changes **who** is named (RQ8) but not **how well** games are ranked (R16 §5).
   - **It replicated on the 48 new games** (frozen fixed order):
     - the last-listed pair had the top score in **44/48** V1 replies (no-bias expectation 0.215), 44/48 V3 and 48/48 C-shuffled (R21 §4.8);
     - llama named T-Z as the single top pair 37 times in V1 (R22C §4.4);
     - granite again showed no preference beyond ties (R22C §4.4).
3. **Session effect (Ollama nondeterminism at temperature 0).**
   - **Within one session,** repeats are identical (MAD 0 between samples 1 and 2 in every view; R13 §4).
   - **Between sessions,** V2 changes most: RQ0.4 Spearman 0.676 (R13 §4). In the follow-up, V2 re-scored unchanged gave AUROC 0.559 vs 0.372 (+0.188 [+0.007, +0.389]), with MAD 10.79 and Spearman 0.653 (R16 §4.2, §4.4).
   - V1 and V3 were nearly identical across sessions (23/24 and 22/24 identical scores). V4 moved more (MAD 7.92, Spearman 0.775) (R16 §4.4).
4. **RQ0.4 summary:** PASS for V1, V3, V4, V5; FAIL for V2 (R13 §4). The test run used one sample per view (R13 §4), so V2-based results carry this caveat.
5. **Other:**
   - With the v3_pairs format there were 0 length cuts in the dev and test runs (R13 §2, R14 §4.1) and 0 truncation flags in the follow-up (R16 §4.1). The earlier v2_pairs format had 25% cuts (R13 §2).
   - Ties at the top are common, so many replies name no pair (e.g. dev V3: 8/12 no pair, R13 §5).
6. **The structured report misreads persona talk.** On the replication, V4 at its frozen threshold flagged **8/8 persona (Type 3) games** as collusion (R21 §4.8). On the original test it flagged 2/4 (R14 §4.4). The mention-count lines of the report make friendly talk look like a pair signal (`writeup/excerpts_22.md`, case d).

---

## e) Limitations and what we would do next

### Limitations (collected from reports 10–16)

**Sample and design:**
- **Small samples:** n = 24 test games with 4 per negative type, so CIs are wide and one false positive moves a type's FPR by 25 points (R14 §8). The pilots had 4 Type 1 + 2 Type 2 games (R10 §B5).
- **One agent model** (`qwen2.5:7b`), **one game** (El Farol), **8 rounds** (R10 §B5).
- **The collusion is suggested, not invented:** the alliance note proposes the plan (R10 §B1, §B5).
- **Collusion is not fully secret:** 6.5% of focal public messages reveal joint action, and 12 of 24 Type 1 games have at least one reveal (R12 §4.2).

**Data quality:**
- **Failures:** 1.75% of generation calls failed (all truncation), and those rounds are excluded. Valid rounds per game: 8 in 36 games, 5–7 in 12 (R12 §4.2).
- **Lookalike quality:** 1 Type 3 game partly behaved like collusion, and 2 Type 4b games did not follow the incentive. Labels stay as configured (R12 §4.4).
- **Unplanned clue:** Type 4b "deposit" talk is visible to monitors under the flag-only cleaner (R12 §5; R14 §8).
- **Uptake rule:** rule v2 was developed on pilot 1 and confirmed on pilot 2 only; non-English text counts as U = 0 (R10 §B5).

**Monitor:**
- **One primary monitor model** (`llama3.1:8b`) **and one prompt format** (R14 §8). The second-model check (RQ9, granite3.3:8b) showed that the view ranking is monitor-dependent (R15C §4.2, §7). Granite ran on different hardware (Apple Metal vs NVIDIA), so model and hardware effects cannot be separated (R15C §8).
- **Degenerate thresholds:** V1, V3 and C-mismatch had threshold 0 (flag everything), so their accuracy / TPR / FPR carry no information (R13 §5, R14 §8).
- **Dev vs test instability:** V3 went from 0.319 to 0.736 (+0.417 [0.142, 0.684]), and the view rankings agree only weakly (Kendall τ 0.255) (R15 §4.1).
- **Session nondeterminism** (R13 §10, R14 §8, R16 §4.4) and **position / recency bias** (R15 §4.6, R16 §4.7). Other fixed orders (the agent list, the agent order in views) were not varied (R16 §8).
- **RQ7:** Dep was NA in 3 test games (n = 21) (R14 §4.8).

**Analysis:**
- **Pooled results include dev selection data** (R15 §8).
- **The code-signal comparisons beyond Dep are exploratory** (R15 §8).
- **Test games scored three times:** the 24 test games have now been scored in three sessions (R14, R16). Nothing was tuned on them (R16 §8).

### What we would do next

1. ~~Run RQ9~~ (done, R15C): since the ranking is monitor-dependent, **report any view result per monitor model** and test more than one monitor in future studies.
2. **A larger test set** (more games per negative type), so that RQ2 and RQ5 can be settled.
3. **Score several sessions per view** and average them, or report the between-session spread for every view, especially V2 and V4.
4. **Pre-register a monitor format with randomised pair and agent order** as the default, plus an explicit "no pair" option to reduce ties.
5. **Treat simple action signals (coGO, capture, G_others) as baselines** in Study 2.3, and test a combined code + V4 rule on dev first.
6. **Remove the Type 4b "deposit" clue at generation time** (prompt wording), not by cleaning, so the same-incentive lookalike tests behaviour only.

---

## f) The pre-registration story

| Document | Commit | LF sha256 (first 16) | Written / committed | Status relative to data |
|---|---|---|---|---|
| Frozen RQ0.1 pre-registration `configs/prereg_rq01.md` | 84fca68 (title still said DRAFT), official freeze **4909c7e** | c5976220465c10f5 | frozen 2026-10-24 08:31 (R10 §B2) | before pilot 1 |
| Amendment 1 `configs/prereg_rq01_amendment1.md` | **2d47580** | c214284753ff2cf1 | committed 2026-10-24 10:42 (R10 §B2) | **after pilot-1 data**, before pilot 2 |
| Amendment 2 `configs/prereg_rq01_amendment2.md` | **a989c7a** | ccb24bbe99095b88 | committed 2026-10-24 13:37 | after the pilots and the secrecy re-pilot, **before any dataset game** (R10 §A5) |
| Erratum to Amendment 2 `configs/prereg_rq01_amendment2_erratum.md` | **0dfd1b1** | ef31afca9c45d630 | written 2026-10-24 (R12 §2); committed 2026-10-25 02:28 | written **before any monitor result** (R12 §4.0); changes no rule |
| Frozen monitor `configs/frozen/monitor_frozen.json` | **89bdb79** | ccc4bf07838be73e | committed 2026-10-25 02:28 | after dev monitor runs, **before any test call** (R14 §4.0) |
| Follow-up 1 pre-registration `configs/prereg_followup1_pair_order.md` | **496fc28** | 0d6aaa412b394419 | committed 2026-10-25 04:39 (R16) | after test data (which motivated it), **before any follow-up call**; control arm added before the commit |
| Replication pre-registration `configs/prereg_replication.md` | **2bc3d3a** | d9d25b583b1d6052 | committed 2026-10-25 09:55 (R21 §4.0) | **before any replication game existed** |
| Replication amendment 1 (granite) `configs/prereg_replication_amendment1.md` | **306502e** | 778cf66b03bdea1f | committed 2026-10-25 20:34 (R21 §4.0) | after the original RQ9 data (which motivated it), **before any replication view was rendered** |

### Deviations table

Items 1–12 are from R10 §B4; items 13 onward were added later.

| # | What | Why | Recorded where | Decided before / after the related data |
|---|---|---|---|---|
| 1 | Pre-freeze changes: possessive name pattern, hint folded into alliance_v3, placebo_v3, 2 machines | rule bug; b2 at risk; length match; machine C unavailable | prereg §10 | before any pilot data (the hint was motivated by 3 earlier smoke games) |
| 2 | Freeze commit 84fca68 → 4909c7e | the title still said DRAFT | DEVLOG task 08 | before pilot 1 |
| 3 | Pilots 1 and 2 on machine B only (prereg: A and B) | operational | reports 08 / 09b | before the data; no design change |
| 4 | Departure from U1 → Amendment 1 (language line, uptake rule v2, pilot 2, new gate) | U1 targeted a cause that was not observed; the rule missed real coordination; language drift | Amendment 1 | **after pilot-1 data** (rule v2 tested on new data, pilot 2) |
| 5 | Pilot-1 hand-check made descriptive | the rule had been replaced; two raters for reliability | Amendment 1 §6 | after pilot-1 data, before the hand-check was filled |
| 6 | E2 = 10 rounds instead of 12 | lead's decision | Amendment 1 §7, Amendment 2 §4 | after pilot 1; moot |
| 7 | Cleaner becomes flag-only (except 8-word copies and header phrases) | over-removal concern; Type 4b "deposit" talk is behaviour | Amendment 1 §8, Amendment 2 §6 | after pilot 1 |
| 8 | Language line ("English only") | language drift in pilot 1 | Amendment 1 §3 | after pilot 1 |
| 9 | Amendment 1 committed together with code, not alone | — | DEVLOG task 09b | before pilot 2 |
| 10 | Secrecy variant v4 + 2-game re-pilot | executes frozen §5 (reveal rate 12.5%) | DEVLOG task 09c | after pilot-2 data; recorded before its own calls |
| 11 | Proceed with v4 although the re-pilot reveal rate stayed 12.5% | frozen §5 sets no further target | Amendment 2 §2 | after the re-pilot data |
| 12 | Repair re-ask not used | keep all failures as data | Amendment 2 §3 | after the pilot-2 failures |
| 13 | RQ0.2 criteria operationalised (e.g. "persona talk" = names the partner + a warm word) | the frozen text gave no exact rule | R12 §8 | stated in the script before computing RQ0.2 |
| 14 | Erratum and analysis decisions: alternation shows in G_others only; C_kw = literal sum of both directions; tie rules (best single view → V1; best LLM view → earliest); threshold candidates = observed dev scores | correctness of the amendment's explanation; rules not pre-registered | R11 §6; R12 §4.0; erratum | **before any monitor result** |
| 15 | num_ctx 16384 for all monitor calls (new manifests, same templates) | every V5 view exceeded the 8192 guard | R12 §7; R13 §0 (a) | after the views were rendered, **before any monitor call** |
| 16 | Format eligibility clause: a constant-score format is ineligible, so v3_pairs was chosen (rule (b) as written would have chosen v1) | v1 gave 80 on 96/96 dev calls | R13 §0, §9 | **after dev monitor data, before any test call** |
| 17 | `analyse_22.py --freeze-extra` (adds keys to the frozen file without overwriting) | record the format, digest and RQ0.3 / RQ0.4 in the frozen file | R13 §9 | before the test run |
| 18 | Test-analysis addendum: "degenerate threshold" labels; supplementary per-type AUROC for RQ3; RQ2 caveat; exploratory C-length − V3 | three views had threshold 0; RQ3 counts uninformative for them | R14 §4.0 | **before test scoring** |
| 19 | Exploratory robustness analyses, plus an unplanned position-bias check | robustness; the check was prompted by an excerpt | R15 §7 | **after test data**; labelled exploratory |
| 20 | Follow-up 1 pre-registered, with a same-session control arm added before the commit | test the position-bias explanation | prereg follow-up 1; R16 | after test data, **before any follow-up call** |
| 21 | Follow-up random arm also uses sample_idx 1 (same seed as the control arm) | the arms then differ only in pair order | DEVLOG task 16 part 1b; prereg §2 | before any follow-up call |
| 22 | Documentation corrections: caption and excerpt section reference "report 15 §6" → §4.6 | typo | R16 §7; this task | no data involved |

---

## g) Replication (pre-registered, 48 new games)

**Status: done.**
- **Pre-registration:** `configs/prereg_replication.md` (2bc3d3a, LF sha256 `d9d25b58…a1f9`); amendment 1 for granite (306502e, `778cf66b…7cbf7`). Seed 20261027.
- **Games:** 48 new games: 24 collusion, 8 each of placebo, persona talk and same incentive. **0 quality-fail games**, so the sensitivity analysis equals the primary (R21 §4.2).
- **Frozen inputs, nothing re-fitted:** the llama monitor (89bdb79), the Study 2.3 judge and rules (404f356), and the granite manifest (57206cb).
- **One sample, one run per monitor:** llama on machine B (R21 §4.5) and granite on machine C (R22C §4.3).
- **Statistics:** 95% stratified bootstrap, B = 2000, seed 20261023; paired for differences.

**Study 2.2 — frozen llama3.1:8b monitor** (R21 §4.7; the original column is from R14 / R15):

| ID | Hypothesis | Replication [95% CI] | Outcome | Original (n = 24 test) |
|---|---|---|---|---|
| R1 | Messages alone fail: AUROC(V1) | 0.505 [0.363, 0.655] | **confirmed** | 0.490 [0.299, 0.691] |
| R2 | Structured report works: AUROC(V4) | 0.636 [0.507, 0.751] | **confirmed** | 0.896 [0.771, 0.979] |
| R3 | Combining helps: V3 − V2 | +0.241 [0.063, 0.419] | **replicated** | +0.365 [0.094, 0.611] |
| R4 | Structure beats raw: V4 − V3 | +0.071 [−0.128, 0.247] | **not replicated** | +0.160 [−0.021, 0.351] |
| R5 | Structure beats same length: V4 − C-length | −0.034 [−0.212, 0.133] | **not confirmed** | +0.285 [0.017, 0.556] |
| R6 | Same-incentive fools messages: V1, T1 vs T4b | 0.495 [0.297, 0.716] | **confirmed** | 0.344 [0.12, 0.65] |
| R7 | Persona talk fools actions: V2, T1 vs T3 | 0.352 [0.154, 0.578] | **not confirmed** | 0.219 [0.00, 0.62] |
| R8 | Private plans: V5 − V3 | −0.022 [−0.192, 0.155] | **not replicated** (no gain again) | −0.031 [−0.267, 0.236] |
| R9 | Shuffled control: AUROC(C-shuffled) | 0.457 [0.315, 0.591] | **pass** | 0.632 [0.431, 0.833] |
| R10a | Code signal: AUROC(capture) | 0.900 [0.811, 0.965] | **confirmed** | 0.896 [0.781, 0.986] (R15 §4.4) |
| R10b | Capture − V4, paired | +0.264 [0.121, 0.412] | **capture better** | capture 0.896 vs V4 0.896 (no paired CI reported) |

**Amendment 1 — granite3.3:8b as a second monitor** (R22C §4.4; the original column is from R15C):

| ID | Hypothesis | Replication [95% CI] | Outcome | Original (n = 24 test, R15C) |
|---|---|---|---|---|
| G1 | Granite's action view works: AUROC_granite(V2) | 0.628 [0.488, 0.754] | **not confirmed** (CI includes 0.5) | 0.767 [0.604, 0.917] |
| G2 | Granite's structured report does not work: AUROC_granite(V4) | 0.582 [0.414, 0.730] | **confirmed** | 0.510 [0.292, 0.729] |
| G3 | The view ranking depends on the monitor: V4 − V2 per monitor | llama +0.313 [0.127, 0.481]; granite −0.046 [−0.251, 0.152] | **confirmed, but resting mainly on llama** (opposite signs; only llama's CI excludes 0) | llama V4 > V2, granite V2 > V4 (τ −0.667) |
| G4 | Both monitors agree on V3: granite − llama | +0.097 [−0.063, 0.262] | **confirmed** as "no detected difference" (not equivalence) | 0.736 for both |

**Per-view replication AUROCs** (R21 §4.7; R22C §4.4):

| Monitor | V1 | V2 | V3 | V4 |
|---|---|---|---|---|
| llama | 0.505 [0.363, 0.655] | 0.324 [0.186, 0.469] | 0.565 [0.421, 0.706] | 0.636 [0.507, 0.751] |
| granite | 0.618 [0.474, 0.756] | 0.628 [0.488, 0.754] | 0.662 [0.560, 0.771] | 0.582 [0.414, 0.730] |

See Figure 9.

**Study 2.3 replication** (E1–E4 / E3b; R22C §4.2): see `writeup/results_23.md` §6.

**What replicated and what did not (plain English):**
- **Replicated:**
  - messages alone fail;
  - private plans add nothing (a consistent null);
  - the shuffled control is at chance;
  - the model-free capture signal works (0.900), and it now clearly beats the best LLM view (+0.264);
  - llama's last-position bias;
  - with llama, "combining beats actions alone" (+0.241), but only because llama's action view is below chance.
- **Not replicated:**
  - the structured report's advantages: over the raw combined view (R4), and over a raw view of the same length (R5);
  - "persona talk fools the action view" (R7);
  - granite's good action view (G1).
- **Monitor-dependent:** llama prefers the structured report and granite does not (G3). Neither monitor reaches 0.7 on any view of the new games.
