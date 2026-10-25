# Study 2.2 — final results (pilot)

**Question (Study 2.2):** which view of a game record lets an LLM monitor detect two colluding agents best? The candidates are messages, actions, both together, a code-built structured report, and private plans.

**Setup (one line):**
- **Game:** El Farol, 5 agents (`qwen2.5:7b`), 8 rounds.
- **Data:** 48 games (24 dev / 24 test; each split 12 collusion + 4 placebo + 4 persona talk + 4 same-incentive).
- **Monitor:** `llama3.1:8b` (format `monitor_v3_pairs_ctx16k`), frozen on dev, then run once on test.

**How to read the numbers:**
- **Sample size:** every number is from a **pilot with n = 24 test games** unless marked dev, pooled or follow-up.
- **Confidence intervals:** CIs are 95% stratified bootstraps by episode type (B = 2000, seed 20261023).
- **Citations:** "R14 §4.3" means report 14, section 4.3 (`notes/reports/`).
- **Sourcing:** numbers are copied from the reports, never recomputed here. Where a report gives no paired CI, only the reported values are shown.
- **Pre-registration:** the primary comparisons are **RQ2 and RQ5**. Everything else is exploratory, and no multiple-comparison correction is applied (R14, "Read this first").

---

## a) Headline answer

**The answer depends on the monitor model.**

**With `llama3.1:8b`** (the frozen primary monitor):
- Messages alone (V1, 0.490 [0.299, 0.691]) and actions alone (V2, 0.372 [0.170, 0.601]) failed.
- The code-built structured report worked best: V4 0.896 [0.771, 0.979] (R14 §4.2).

**With `granite3.3:8b`** (RQ9, the same frozen prompt, only the model changed), the ranking reversed:
- actions V2 0.767 [0.604, 0.917];
- structured report V4 0.510 [0.292, 0.729];
- Kendall τ −0.667 between the two rankings (R15C §4.2).

**Only the combined raw view matched:** V3 0.736 with both models (R15C §4.2; R14 §4.2).

**Model-free behaviour signals were the most dependable evidence:** capture 0.944 [0.884, 0.986] over all 48 games (R15 §4.4, exploratory). They do not depend on which LLM reads the record.

**The LLM monitor's reliability problems were measured** (section d):
- the single-score format returned a constant 80 on 96/96 dev calls (R13 §2);
- a last-position bias in llama's pair scores (R15 §4.6, R16 §4.3), which granite does not show beyond its ties (R15C §4.5);
- a session effect of +0.188 [+0.007, +0.389] on V2 when the frozen monitor was re-scored unchanged (R16 §4.4).

The pre-registered RQ2 ("combining helps", +0.365 [0.094, 0.611], R14 §4.3) is fragile and does not hold with granite (V3 − V2 −0.031 [−0.250, 0.191], R15C §4.3). Section c gives the status of each claim.

**Link to Study 2.3** (`writeup/results_23.md`, task 17C; the same 24 test games, frozen rules):
- **The coalition-gain rule R2 ranks games well:** AUROC 0.872 [0.736, 0.986].
- **The talk-only judge R1 is below chance:** 0.396 [0.205, 0.597].
- **Combining evidence families did not help:** AUROC(R6) − AUROC(R2) = −0.080 [−0.208, 0.045], "no clear difference at this sample size".

Both studies point the same way: behaviour evidence carries the signal, and LLM reading of the talk does not.

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

| Claim | Test (R14) | Dev (R13) | Pooled (R15) | Follow-up (R16) | RQ9 granite (R15C) | Label |
|---|---|---|---|---|---|---|
| Messages alone (V1) fail | AUROC 0.490 [0.299, 0.691] (§4.2) | 0.431 [0.219, 0.646] (§5) | 0.459 [0.323, 0.597] (§4.2) | fixed 0.490 [0.299, 0.691], random 0.507 [0.306, 0.705] (§4.2) | **does not hold**: V1 0.729 [0.549, 0.896] (§4.2) | **ROBUST (llama only)** |
| Actions alone (V2) fail | 0.372 [0.170, 0.601] (§4.2) | 0.493 [0.260, 0.726] (§5) | 0.447 [0.302, 0.595] (§4.2) | fixed 0.559 [0.319, 0.788], random 0.514 [0.295, 0.733] (§4.2) | **does not hold**: V2 0.767 [0.604, 0.917], granite's best view (§4.2) | **ROBUST (llama only)** (never above chance with llama; the size depends on the session, RQ0.4 FAIL) |
| Combining helps (RQ2, V3 − V2) | +0.365 [0.094, 0.611] (§4.3) | −0.174 [−0.406, 0.056] (§5, in-sample) | +0.040 [−0.155, 0.238] (§4.2) | point estimates only: +0.19 (fixed), +0.28 (random) (§5) | **does not hold**: −0.031 [−0.250, 0.191] (§4.3) | **FRAGILE (llama only)** |
| Structure beats raw (RQ5, V4 − V3) | +0.160 [−0.021, 0.351] (§4.6) | +0.444 [0.146, 0.729] (§5, in-sample) | +0.350 [0.166, 0.534] (§4.2) | V4 vs V3 AUROC: fixed 0.826 vs 0.750; random 0.750 vs 0.792 (§4.2) | **does not hold**: −0.226 [−0.486, 0.056] (§4.3) | **FRAGILE (llama only)** (positive on dev/pooled, not significant on test, reversed in the random arm) |
| Structure beats same length (V4 − C-length) | +0.285 [0.017, 0.556] (§4.6) | AUROC 0.764 vs 0.583 (§5; no paired CI reported) | +0.237 [0.030, 0.443] (§4.2) | not measured (C-length not re-run) | not measured (C-length not scored); granite's V4 is at chance, 0.510 [0.292, 0.729] (§4.2) | **ROBUST (llama only)** (test and pooled CIs above 0; the structured report does not work with granite) |
| Private plans do not help (RQ6, V5 − V3) | −0.031 [−0.267, 0.236] (§4.7) | AUROC 0.583 vs 0.319 (§5; no paired CI reported) | +0.149 [−0.062, 0.347] (§4.2) | not measured (V5 not re-run) | not measured (V5 not scored) | **CONSISTENT NULL (no detectable gain at n = 24)**: every CI includes 0. This is absence of evidence, not evidence of no effect |
| Same-incentive (T4b) fools messages | V1 T1 vs T4b 0.344 [0.12, 0.65] (§4.4) | not reported per type | 0.359 [0.190, 0.562] (§4.2) | fixed 0.344 [0.125, 0.646], random 0.365 [0.115, 0.625] (§4.6) | **does not hold**: V1 T1 vs T4b 0.812 [0.604, 0.958] (§4.4) | **ROBUST (llama only)** |
| Persona talk (T3) fools actions | V2 T1 vs T3 0.219 [0.00, 0.62] (§4.4) | descriptive only: V2 flags Type 3 games (§5) | 0.266 [0.049, 0.526] (§4.2) | fixed 0.458 [0.083, 0.854], random 0.500 [0.156, 0.844] (§4.6) | **does not hold**: V2 T1 vs T3 0.833 [0.708, 0.958] (§4.4) | **FRAGILE (llama only)** (reversed in the original session, about chance in the follow-up session) |
| Code action signals are competitive with V4 (exploratory) | coGO 0.896, capture 0.896, G_others 0.872 vs V4 0.896 (R15 §4.4, test) | not reported separately | coGO 0.885, capture 0.944, G_others 0.906 vs V4 0.837 (R15 §4.4) | not measured | not applicable to the signals (model-free); granite's best view is V2 0.767 [0.604, 0.917] (§4.2) | **CONSISTENT (exploratory; pooled includes test)**: test and pooled agree; never pre-registered |
| Position bias exists (last-listed pair gets the top score) | T-Z max V1 21/24, V3 17/24, V4 7/24 (R15 §4.6) | V1 22/24, V3 22/24, V4 7/24 (R15 §4.6) | — | fixed arm V1 21/24, V3 19/24; drop with random order V1 +0.458 [0.292, 0.667], V3 +0.417 [0.167, 0.667] (§4.3) | **does not hold**: last-position-max share at the no-bias expectation in every view (e.g. V1 0.708 vs 0.679); T-Z named as the single top pair 0 times in V1–V3 (§4.5) | **llama-specific (RQ9: granite shows no last-position preference beyond ties)** |
| Position bias explains the raw-view failure | — | — | — | H2: V1 +0.017 [−0.229, +0.281], V3 +0.042 [−0.198, +0.285] (§4.7) | — | **NOT SUPPORTED** |

---

## d) Monitor reliability findings

1. **Single-score format collapses to a constant.**
   - Format v1 (one 0–100 score per game) returned **80 in 96/96 dev calls** (R13 §2); synthetic runs showed 15/16 at 80 (R05 §11.3, cited in R13 §2).
   - It was ruled ineligible under the lead's constant-score rule, decided on dev before any test call (R13 §0).
   - Per-pair scoring (v3_pairs) gave 4–10 distinct values per view (R13 §0).
2. **Position / recency bias in the pair list.**
   - With the fixed order (J-M … T-Z), the last pair T-Z got the top score in 21/24 V1 and 17/24 V3 test replies, and in 24/24 C-shuffled replies, but in only 7/24 V4 replies (R15 §4.6). T-Z is the true pair in 1 of 12 test collusion games (R15 §4.6).
   - Randomising the order cut this to 10/24 (V1) and 9/24 (V3) (R16 §4.3).
   - In V1 the last-listed pair still gets the top score more often than chance (0.417 [0.250, 0.625] vs an expected 0.217), so V1 has a recency bias beyond the T-Z habit (R16 §4.7).
   - The bias changes **who** is named (RQ8) but not **how well** games are ranked (R16 §5).
3. **Session effect (Ollama nondeterminism at temperature 0).**
   - **Within one session,** repeats are identical (MAD 0 between samples 1 and 2 in every view; R13 §4).
   - **Between sessions,** V2 changes most: RQ0.4 Spearman 0.676 (R13 §4). In the follow-up, V2 re-scored unchanged gave AUROC 0.559 vs 0.372 (+0.188 [+0.007, +0.389]), with MAD 10.79 and Spearman 0.653 (R16 §4.4).
   - V1 and V3 were nearly identical across sessions (23/24 and 22/24 identical scores). V4 moved more (MAD 7.92, Spearman 0.775) (R16 §4.4).
4. **RQ0.4 summary:** PASS for V1, V3, V4, V5; FAIL for V2 (R13 §4). The test run used one sample per view (R13 §4), so V2-based results carry this caveat.
5. **Other:**
   - With the v3_pairs format there were 0 length cuts in the dev and test runs (R13 §2, R14 §4.1) and 0 truncation flags in the follow-up (R16 §4.1). The earlier v2_pairs format had 25% cuts (R13 §2).
   - Ties at the top are common, so many replies name no pair (e.g. dev V3: 8/12 no pair, R13 §5).

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

## g) Replication (in progress)

**Status:**
- A pre-registered replication on **48 new games** is in progress: generation is running.
- **Pre-registration:** `configs/prereg_replication.md` (commit 2bc3d3a, LF sha256 `d9d25b58…a1f9`), seed 20261027.
- **Labels:** `data/replication/labels.csv` (24 / 8 / 8 / 8).
- **Frozen inputs, nothing re-fitted:** the Study 2.2 monitor (89bdb79), the Study 2.3 judge and rules (404f356).

Every result below is **TBD**.

**Study 2.2 (machine B, frozen llama3.1:8b monitor; prereg §3):**

| ID | Hypothesis | Test | Result |
|---|---|---|---|
| R1 | Messages alone fail | AUROC(V1) | TBD |
| R2 | The structured report works | AUROC(V4) | TBD |
| R3 | RQ2: combining helps | AUROC(V3) − AUROC(V2) | TBD |
| R4 | RQ5: structure beats raw | AUROC(V4) − AUROC(V3) | TBD |
| R5 | Structure beats same length | AUROC(V4) − AUROC(C-length) | TBD |
| R6 | Same-incentive fools messages | AUROC(V1; Type 1 vs Type 4b) | TBD |
| R7 | Persona talk fools actions | AUROC(V2; Type 1 vs Type 3) | TBD |
| R8 | Oracle: private plans | AUROC(V5) − AUROC(V3) | TBD |
| R9 | Shuffled control | AUROC(C-shuffled) | TBD |
| R10 | Code action signal | (a) AUROC(capture); (b) AUROC(capture) − AUROC(V4) | TBD |

**Study 2.3 (machine C, frozen judge_v1 + rules; prereg §4):**

| ID | Hypothesis | Test | Result |
|---|---|---|---|
| E1 | Behaviour evidence works | AUROC(R2 gain score) | TBD |
| E2 | Talk-only evidence is weak | AUROC(R1 judge score) | TBD |
| E3 | Combining evidence helps | AUROC(R6) − AUROC(R2) | TBD |
| E3b | Secondary: the leave-one-out combined rule | AUROC(R7) − AUROC(R2) | TBD |
| E4 | Lookalikes (descriptive) | flag rates of R2 and R6 for Type 3 and Type 4b vs Type 2 | TBD |

**Second replication monitor (granite3.3:8b), G1–G4:**
- These hypotheses are defined in `configs/prereg_replication_amendment1.md`.
- At the time of writing this is a **DRAFT** on machine C (report 19C; LF sha256 `778cf66b…7cbf7`). It is not committed, so it is not yet binding.
- They are listed here by name only; their wording is in the amendment.

| ID | Result |
|---|---|
| G1 | TBD |
| G2 | TBD |
| G3 | TBD |
| G4 | TBD |
