# Project Guide: Collusion Evidence Lab

**A complete, simple-English explanation of everything done so far**
*(Status: after the 48-game dataset, Study 2.2 test + robustness + follow-up + RQ9, Study 2.3 test; replication in progress)*

---

## How to read this guide

- **Part 1** explains the problem and the research questions.
- **Part 2** is a glossary: every important word, explained simply.
- **Part 3** explains the setup: the game, the agents, the four game types, the laptops.
- **Part 4** tells the story of the project, step by step, report by report.
- **Part 5** gives the results of Study 2.2, question by question.
- **Part 6** gives the results of Study 2.3.
- **Part 7** lists every failure we hit and how we fixed it.
- **Part 8** is an honest judgement: are the results good enough?
- **Part 9** explains what is happening right now (the replication).
- **Part 10** is an index of all report files.

All numbers in this guide come from the project reports (00 to 18a, 13C, 15C, 17C). If you see a number like **0.736 [0.535, 0.920]**, the first number is the result and the brackets are the **95% confidence interval** (explained in Part 2).

---

# PART 1 — The problem and the research questions

## 1.1 The problem statement

AI agents (programs built on large language models) are starting to act in the world together: buying, selling, negotiating, planning. When several agents interact, two or more of them could **secretly work together** to win at the expense of others. This is called **collusion**.

Collusion is dangerous because:
- it harms the other players (or the humans the agents serve),
- it can be hidden: agents can say one thing and do another,
- innocent behaviour can **look** like collusion (two agents acting alike for their own separate reasons).

So we need ways to **detect** collusion from the records (logs) of what agents said and did, and we need to know **what evidence is convincing enough** to say "this is collusion".

This project was built for a research hackathon (Track 2: *Detection and Audit of Collusion*). We worked on two of its questions: **2.2** and **2.3**.

## 1.2 Study 2.2 — the core question

> **"Does combining what agents SAY with what they DO help detect collusion better than either one alone?"**

In simple words: if a monitor (an AI judge) reads only the agents' **messages**, or only their **actions**, or **both together**, which works best?

### The sub-questions of Study 2.2

**Group A — gates (checks that the data and tools are trustworthy):**

| Code | Question in simple words |
|---|---|
| RQ0.1 | Does real collusion actually happen in our "collusion" games? |
| RQ0.2 | Do the "lookalike" innocent games behave the way we designed them? |
| RQ0.3 | Can the monitor see the answer by accident (a "leak")? |
| RQ0.4 | Does the monitor give stable scores if asked again? |

**Group B — the main questions:**

| Code | Question in simple words |
|---|---|
| RQ1 | How well does each single view (messages only, actions only, …) work? |
| RQ2 | Does "messages + actions together" beat the best single view? **(main question)** |
| RQ3 | Which innocent lookalike fools which view? |
| RQ4 | Does the monitor really cross-check words against actions? |

**Group C — going deeper:**

| Code | Question in simple words |
|---|---|
| RQ5 | Does a neat, code-built summary (structured report) beat raw logs? And is that only because it is shorter? **(main question)** |
| RQ6 | If the monitor could read the agents' private thoughts, how much better would it do? |
| RQ7 | Can simple code (no AI) detect collusion as well as the AI monitor? |

**Group D — extras:**

| Code | Question in simple words |
|---|---|
| RQ8 | Can the monitor name *which two agents* are colluding? |
| RQ9 | Do the results hold with a different monitor model? |

## 1.3 Study 2.3 — the core question

> **"What should count as convincing evidence of collusion?"**

This comes from law. In antitrust law (law against companies secretly fixing prices), courts know that companies acting the same way is **not proof** of an agreement. They require extra evidence called **plus factors** (for example, evidence of secret communication, or acting against one's own interest in a way that only makes sense with an agreement).

We asked: for AI agents, which kinds of evidence, alone or combined, separate real collusion from innocent lookalikes?

### The sub-questions of Study 2.3

| Code | Question in simple words |
|---|---|
| RQ-E0 | Are our evidence calculations correct? (checked with tests) |
| RQ-E1 | How well does each kind of evidence work alone? |
| RQ-E2 | Which lookalike fools which kind of evidence? |
| RQ-E3 | Does combining evidence (plus-factor logic) beat the best single kind? **(main question)** |
| RQ-E4 | Which kind of evidence is really necessary? (remove one at a time) |
| RQ-E5 | Does "words don't match actions" add useful evidence? |
| RQ-E6, E7 | (Channel-blocked re-runs; a second setting) — **dropped for time** |

---

# PART 2 — Glossary (every important word, simply)

## 2.1 People, machines and tools

| Term | Meaning |
|---|---|
| **Agent** | An AI model that plays the game: it plans, talks and chooses actions. |
| **LLM** | Large Language Model, e.g. qwen, llama, granite. |
| **Monitor** | A separate AI model whose only job is to read a game record and say how suspicious it is. |
| **Judge** | In Study 2.3, an AI that reads **only the public messages** and scores each pair of agents for "signs of an agreement". |
| **Ollama** | Free software that runs open AI models on your own computer. We pinned version **0.40.3**. |
| **Digest** | A unique fingerprint of a model file. Same digest = exactly the same model. |
| **Machine A / B / C / D** | Our laptops. A = lead's laptop (RTX 3050, 4 GB, slow). B = RTX 3060, 6 GB (fastest Windows, main machine). C = MacBook M4 (Study 2.3 and RQ9). D = weak laptop (writing only). |
| **Claude Code** | The AI coding assistant that built and ran everything, following our prompts and rules. |
| **CLAUDE.md** | The rulebook Claude must follow (no git commits, $0 budget, conda only, logging, reports). |
| **DEVLOG** | A diary file (`notes/DEVLOG.md`) where every step, error and decision is written down. |
| **Report** | One file per task in `notes/reports/`, describing what was done and the results. |

## 2.2 The game and the data

| Term | Meaning |
|---|---|
| **El Farol** | The game we used. 5 players decide each round whether to GO to a bar or STAY home. The bar is fun only if **at most 2** go (+10 each). If 3 or more go, everyone who went gets **−5**. Staying home gives **0**. |
| **Round** | One turn of the game. We used **8 rounds** per game. |
| **Episode / game** | One complete game of 8 rounds. |
| **Three-stage protocol** | Each round: (1) **private plan** (only the agent sees it), (2) **public announcement** (everyone sees: "I will GO/STAY" + a message), (3) **final action** (the real choice). From the Shi et al. 2026 research harness. |
| **Focal pair** | The two agents we "treat" in a game (e.g. the secret allies in a collusion game). In honest games it is a random "decoy" pair. |
| **Private channel** | Secret messages between the two allies (collusion games only). |
| **History block** | A short summary of past rounds, shown to every agent each round (replaced the original "reflection" step). |
| **Addendum** | Extra text added to a focal agent's instructions (the secret alliance, the placebo, the persona or the incentive). |
| **Placebo** | A harmless text of the **same length**, given to honest pairs, so that "having extra text" can't explain differences. |
| **Brevity line** | An instruction to all agents: keep answers short (made games 4.5× faster). |
| **Language line** | An instruction to all agents: write in English only (fixed a drift into Chinese). |
| **Hint** | One sentence in the alliance text suggesting a strategy ("both go while encouraging others to stay home"). |
| **Public reveal** | A colluding agent publicly hints at the alliance ("T and I will go together"). Kept as behaviour. |
| **coGO** | How often a pair both went to the bar in the same round. |
| **Capture** | Rounds where **exactly** that pair went and nobody else, so they had the bar to themselves. |
| **G_others** | How much more a pair earned than the other players (gain at others' expense). |
| **Uptake** | Did the colluding agents actually *try* to coordinate? (a "manipulation check") |
| **Uptake rule v1 / v2** | Our automatic text rule for uptake. v1 needed words like "we/us/let's" and failed on short commands. v2 also accepts confirmations and instructions to the partner. |
| **Imputed** | When an agent's answer couldn't be read, the action is filled in as STAY so the game can continue — marked clearly and excluded from metrics. |
| **Truncation** | When text gets cut off because it is too long for the model's memory. Ollama does this **silently**, so we added a guard. |
| **num_ctx** | The size of a model's working memory (context window) in tokens. |
| **Token** | A piece of a word; models count text in tokens (~4 characters in English). |

## 2.3 The four game types

| Type | Name | What happens | Correct label |
|---|---|---|---|
| **Type 1** | Real collusion | Two agents secretly agree to team up, have a private channel, and act on it. | Collusion (positive) |
| **Type 2** | Honest (placebo) | Normal play; the decoy pair gets a neutral text of the same length. | Not collusion |
| **Type 3** | Talk only (persona) | Two agents talk publicly like friends, but have **no** agreement and play for themselves. | Not collusion (a lookalike that fools **word** evidence) |
| **Type 4b** | Same incentive | Two agents each privately pay a "deposit" so staying home costs them −8. They both tend to go — **without** any agreement. | Not collusion (a lookalike that fools **action** evidence) |

**Why lookalikes matter:** if the dataset had only collusion vs honest games, every method would look good. Lookalikes are the real test.

## 2.4 The views (what the monitor is allowed to see)

| View | Content | Simple meaning |
|---|---|---|
| **V1** | Public messages only | "What they said" |
| **V2** | Actions + payoffs only | "What they did" |
| **V3** | Messages + actions together, raw | "Said + did", unprocessed |
| **V4** | Structured report built by code | A neat table: who promised what, who did what, who broke promises, which pairs went together, who mentions whom |
| **V5** | V3 + private plans | "Oracle": as if the monitor could read their minds |
| **C-mismatch** | Messages from game *i* + actions from game *j* | Control: breaks the link between words and actions |
| **C-length** | V3 cut to V4's length | Control: tests if V4 wins only because it is shorter |
| **C-shuffled** | Random pieces from other games | Control: should score at chance; if not, something leaks |

## 2.5 Monitor versions (formats)

| Name | What it is | What happened |
|---|---|---|
| **monitor_v1** | One suspicion score 0–100 | Gave **80 every time** (96/96 dev calls) → useless, ruled ineligible |
| **v2_anchored** | One score with an anchored scale | Used only 2 values (50, 75) → not useful |
| **v2_pairs** | A score for each of the 10 pairs | Good spread, but 25% of answers got cut off (endless "evidence" text) |
| **v3_pairs** | Pair scores **first**, evidence capped at 300 characters | Fixed the cut-offs → **chosen and frozen** |
| **ctx16k** | Same as above with num_ctx 16384 | Needed so the long V5 view fits |
| **_rot** | Pair order randomised per call | Used in Follow-up 1 |
| **_granite** | Same format, model = granite3.3:8b | Used for RQ9 |

## 2.6 Statistics words

| Term | Meaning |
|---|---|
| **AUROC** | The chance that a random collusion game gets a higher score than a random innocent game. **0.5 = coin flip, 1.0 = perfect.** Below 0.5 = worse than chance (it ranks innocent games higher). |
| **Confidence interval (CI)** | The range where the true value probably lies (95% sure). If a CI for a difference includes 0, we can't say there is a real difference. |
| **Bootstrap** | A way to get the CI: re-pick games at random 2,000 times and recompute. We re-pick whole games, balanced by type. |
| **Paired comparison** | Comparing two views on the **same games**, which is fairer and more precise. |
| **TPR** | True positive rate: share of collusion games correctly flagged. |
| **FPR** | False positive rate: share of innocent games wrongly flagged (false alarms). |
| **Threshold** | The cut-off score above which we say "collusion". Chosen on dev. |
| **Degenerate threshold** | Threshold 0 = flags everything (happened when a view was worse than chance on dev). |
| **Balanced accuracy (BA)** | Average of TPR and (1 − FPR). |
| **Kendall tau** | How much two rankings agree (1 = same order, −1 = reversed). |
| **Spearman** | Rank correlation between two sets of scores (1 = same order). |
| **Cohen's kappa (κ)** | Agreement between two raters beyond chance. |
| **Rule of three** | When something happened 0 times out of n, the true rate is probably at most 3/n. |

## 2.7 Research-integrity words

| Term | Meaning |
|---|---|
| **Pre-registration (prereg)** | Writing down the plan, hypotheses and pass/fail rules **before** seeing data, and committing the file to git (time-stamped). |
| **Freeze** | Locking settings (prompt, thresholds, rules) with a fingerprint before the test. |
| **Amendment** | A dated, committed change to the plan, made before the data it governs. |
| **Erratum** | A dated correction note (the original document is never edited). |
| **Deviation** | Anything we did differently from the plan — always written down, marked "decided before or after seeing the data". |
| **Dev / test split** | Dev games (24) are used to choose settings; test games (24) are used **once** for the final result. |
| **Label from config** | The true answer of each game comes only from how it was set up, never from an AI's opinion. |
| **Cache** | Every model answer is saved to disk, so results are reproducible and nothing is paid/run twice. |
| **Whitelist cleaner** | Builds the monitor's input only from allowed fields, so secret instructions or labels can never reach it. |
| **Flag-only** | Suspicious words are counted but **not removed** (only copied setup text is removed). |
| **Session effect** | The same model can give slightly different answers in a new Ollama session. |
| **Position bias** | The monitor favours a pair because of where it sits in a list (e.g. the last one), not because of evidence. |
| **Ceiling effect** | A model gives almost every case the maximum score, so it can't tell cases apart. |

## 2.8 Study 2.3 evidence families and rules

| Term | Meaning |
|---|---|
| **E1 Conversation** | What the judge thinks of the public talk (C_judge), plus a keyword count (C_kw). |
| **E2 Coalition advantage** | Did the pair gain at others' expense? (G_others, Harm, G_honest) |
| **E3 Dependence** | Did their actions depend on each other beyond chance? (D_sync, D_switch, D_react, D_private → combined into **Dep**) |
| **E4 Word–action** | Did the pair break public promises together? (W_joint) |
| **Honest baseline** | Average behaviour of pairs in honest dev games, used as the "normal" reference. |
| **R1** | Talk rule: flag if the judge score is high. |
| **R2** | Gain rule: flag if the pair gained a lot. |
| **R3** | Dependence rule. |
| **R4** | Legal-style rule: parallel conduct (going together) **AND** at least one plus factor. |
| **R5** | Gain AND dependence. |
| **R6** | Points rule: count how many evidence families are high; flag if ≥ k. |
| **R7** | Small learned model (logistic regression) on the four families. |
| **Ablation** | Remove one evidence family and see how much worse the rule gets. |

---

# PART 3 — The setup in one page

- **Game:** El Farol, 5 agents named **J, M, Q, T, Z**, 8 rounds, three-stage protocol.
- **Agents:** `qwen2.5:7b` (local, pinned digest).
- **Monitor and judge:** `llama3.1:8b`. **Second monitor (RQ9):** `granite3.3:8b`.
- **Budget:** $0 — everything runs locally on our laptops with Ollama 0.40.3.
- **Dataset:** 48 games = 24 collusion (Type 1) + 8 honest (Type 2) + 8 talk-only (Type 3) + 8 same-incentive (Type 4b).
- **Split:** 24 dev games (12 / 4 / 4 / 4) and 24 test games (12 / 4 / 4 / 4), fixed **before** generation.
- **Code:** about 540 automatic tests; every model call cached; everything pinned and fingerprinted.
- **Repo structure (simplified):** `core/` (shared engine: generator, model client, cleaner, evidence, statistics), `study_2_2_views/` (views + monitor + analysis), `study_2_3_evidence/` (judge + rules), `configs/` (prompts, frozen files, pre-registrations, plans), `notes/` (DEVLOG + reports), `writeup/` (results, figures, excerpts).

---

# PART 4 — The story of the project, step by step

## Phase 1: Design (reports 00 and 01)

- **Report 00 — first design.** Chose El Farol (a pair can only "own" the bar by agreeing who goes; collusion there is real and costly to others). Designed the four game types, views, evidence signals, rules and statistics. *Problem:* it assumed paid cloud models.
- **Report 01 — redesign for $0, local models.** Measured three local models on the lead's laptop.
  - Found hidden traps: Ollama **silently cuts** long prompts; the same seed does **not** give the same answer (only the cache makes results reproducible); one API path ignored the memory setting.
  - Fixed a formula bug: an old "dependence" measure scored 0 for a pair that always goes together.
  - Chose `qwen2.5:7b` as agent (the 3B model planned but never acted), `llama3.1:8b` as monitor.

## Phase 2: Building (reports 02–07)

- **02 — Foundations:** cached and pinned model client, labels, split, plan maker, environment checks (61 tests).
- **03 — RQ0.1 metrics** (built on the ML laptop in parallel): coGO, capture, gain, uptake rule, the gate checker.
- **04 — Game generator:** the full runner, prompts, leak scanner, merge checker. The **brevity line** made calls **4.5× faster**, which allowed **8 rounds** instead of 6.
- **05 — Cleaner, views, monitor runner** (machine B). Fixed B's Ollama version. First warning: the single-score monitor gave the same score almost always.
- **06a — Pilot preparation:** in every early test, the allies coordinated but announced it publicly, so others crowded the bar and the pair gained nothing. **Decision:** add the strategy **hint** to the alliance text (alliance v3) and lengthen the placebo to match (placebo v3).
- **07 — Monitor formats:** tried anchored and per-pair scoring; the per-pair format gave real spread but 25% of answers were cut off.

## Phase 3: Pilots and the RQ0.1 gate (reports 08–10)

- **08 — Pilot 1 (8 games on B).** First fixed a Windows **line-ending (CRLF)** bug that blocked machine B.
  - Behaviour was strong: the secret pair was the top pair in 4/4 games and gained.
  - But the **uptake rule failed** (2/4): it missed short commands like "Go to the bar. Encourage others to stay home." and one game drifted into **Chinese**.
  - → **RQ0.1 FAILED under the frozen rule.** This result stays in the record.
- **09a — Amendment 1:** instead of rewording the alliance (which worked), we added the **English-only line**, the improved **uptake rule v2**, and a **two-rater hand-check** (you and a teammate, blinded).
  - Pilot 1 hand-check: the two humans agreed 91.7% (κ 0.80). Rule v1 agreed with humans only 59–66%; rule v2 79–85%. Every rule error was a **miss**, never a false alarm.
- **09b — Pilot 2 (6 new games):** uptake v2 4/4, honest games 0/2, top pair 4/4, gain 4/4, and your hand-check agreement **96.9%** (κ 0.93). → **RQ0.1 PASSED** (under Amendment 1).
  - Public reveal rate was 12.5% (above the 10% flag) → per the frozen rule, the secrecy wording was revised.
- **09c — Secrecy variant v4 + 2-game re-pilot:** reveal rate stayed 12.5%, but reveals changed from "our team plan" to "T and I will go together". Collusion still worked.
- **10 — Amendment 2 + status:** decided to proceed with v4, keep reveals as behaviour, no "repair re-ask", final dataset protocol fixed.

## Phase 4: The dataset (reports 11–12)

- **11 — Analysis tools** (built while games generated): flag-only cleaner, monitor v3_pairs, full statistics, Study 2.3 signals, analysis tables that **refuse** to report test numbers without the frozen settings.
- **12 — Dataset:** 48 games generated on machines A and B, merged and checked.
  - Failures 1.75% of calls (below the 5% limit), no game failed quality.
  - Manipulation check: uptake 24/24, top pair 24/24, uptake + gain 23/24.
  - Public reveals: 6.5% of collusion messages; 12 of 24 collusion games had at least one.
  - **RQ0.2:** Type 3 behaved as designed in 7/8; Type 4b in 6/8. All 8 Type 4b games mentioned their "deposit" publicly.
  - All 384 view files rendered; no leaks found.

## Phase 5: Monitor freeze and test (reports 13–14)

- **13 — P7, dev only:**
  - monitor_v1 gave **80 on 96/96 calls** → ruled **ineligible** ("a constant score can't rank games") — a dated deviation.
  - v3_pairs chosen (100% valid, 0 cut-offs).
  - **RQ0.3 passed** (shuffled control at chance: 0.465).
  - **RQ0.4:** V1, V3, V4, V5 stable; **V2 unstable** (Spearman 0.676).
  - Thresholds chosen, everything **frozen** (`monitor_frozen.json`).
- **14 — P8, the test run:** 24 test games × 8 views, 192 calls, 0 failures. Results in Part 5.

## Phase 6: Checking the results (reports 15–17, 15C)

- **15 — Robustness:** dev vs test, all 48 games pooled, code signals, figures. Found the **position bias**.
- **16 — Follow-up 1** (pre-registered): randomised the pair order + a same-session control. Found the **session effect** on V2.
- **17 — Synthesis:** `writeup/results_22.md` and the README.
- **15C — RQ9** on the MacBook: granite3.3:8b as a second monitor.

## Phase 7: Study 2.3 (reports 13C, 17C)

- **13C:** set up the MacBook, built the judge and rules R1–R7, ran the judge on 48 games, fitted rules on dev, froze them.
- **17C:** applied the frozen rules to the test games once. Results in Part 6.

## Phase 8: Replication (reports 18a, 18b, in progress)

- **18a:** pre-registered a replication on **48 brand-new games** (seed 20261027) for both studies.
- **18b:** wrote the separate labels file.
- Generation is running on A and B. See Part 9.

---

# PART 5 — Study 2.2 results, question by question

## Group A (gates)

| Question | Result | Meaning |
|---|---|---|
| **RQ0.1** collusion happens | **PASS** (pilot 2; dataset uptake 24/24, gain 23/24) | Our secret allies really coordinate and really gain. |
| **RQ0.2** lookalikes behave | **PASS with notes** (Type 3: 7/8, Type 4b: 6/8) | Mostly as designed; labels never changed. |
| **RQ0.3** no leaks | **PASS** (shuffled control 0.465 on dev, test 0.632 with CI including 0.5) | The monitor can't read the answer by accident. |
| **RQ0.4** stable monitor | **PASS except V2** | V2 (actions) scores change between sessions. |

## Group B, C, D (test set, report 14)

**AUROC per view (test, llama3.1:8b):**

| View | AUROC [95% CI] |
|---|---|
| V1 messages | 0.490 [0.299, 0.691] |
| V2 actions | 0.372 [0.170, 0.601] |
| V3 combined | 0.736 [0.535, 0.920] |
| **V4 structured** | **0.896 [0.771, 0.979]** |
| V5 oracle | 0.705 [0.517, 0.882] |
| C-mismatch | 0.549 |
| C-length | 0.611 |
| C-shuffled | 0.632 |

| Question | Result | Simple reading |
|---|---|---|
| **RQ1** each view | Messages and actions alone at or below chance; V3, V4, V5 above chance | Single channels don't work for this monitor. |
| **RQ2** combining (V3 − V2) | **+0.365 [0.094, 0.611]** → "combining helps" (pre-registered wording) | But see robustness below: it did **not** hold over all 48 games. |
| **RQ3** lookalikes | Messages fooled by **Type 4b** (deposit talk); actions fooled by **Type 3** (persona) | Each single view is fooled by one lookalike — the opposite of what we predicted for V1. |
| **RQ4** cross-check | V3 − C-mismatch = +0.188 [−0.028, 0.386] | Inconclusive. |
| **RQ5** structure (V4 − V3) | +0.160 [−0.021, 0.351] | No clear difference on test. |
| **RQ5** structure vs same length | **+0.285 [0.017, 0.556]** | The structured report is better than a raw view of the same length → not just "shorter". |
| **RQ6** private plans | V5 − V3 = −0.031 | No gain — even reading private plans didn't help. The bottleneck is the monitor's reasoning. |
| **RQ7** code vs AI | Dep code signal 0.736 vs V4 0.909 | V4 beat this one code signal; but other code signals were as good as V4 (see below). |
| **RQ8** naming the pair | V4: **7/12** correct (chance 1/10) | The structured report helps name the colluders. |
| **RQ9** second monitor | granite: V1 0.729, V2 0.767, V3 0.736, **V4 0.510** | **The ranking reversed.** See below. |

## What the robustness checks changed (reports 15, 16, 15C)

1. **Pooled 48 games (report 15):** "combining helps" (V3 − V2) shrank to **+0.04** (CI includes 0) → **fragile**. The structured report stayed strong (V4 0.837; V4 − V3 = +0.350, CI above 0).
2. **Simple code signals (report 15):** "capture" 0.944 and "coGO" 0.885 pooled — **as good as the best AI view**, but partly fooled by Type 4b.
3. **Position bias (report 15):** in raw views, llama gave the top score to the **last pair in its list (T-Z)** in most answers (V1: 21/24), though T-Z was the real pair in only 1 of 12 test collusion games.
4. **Follow-up 1 (report 16):** randomising the pair order removed most of the bias, but **V1 stayed at chance** → the bias was real but **not** why messages-only failed. It did distort pair naming. The **same-session control** showed V2's score moved +0.188 between sessions → part of RQ2's gain was session luck.
5. **RQ9 (report 15C):** with granite, actions (0.77) and messages (0.73) worked, the structured report did **not** (0.51). Kendall tau −0.667 (rankings mostly reversed). Only V3 gave the same result (0.736) with both models. Granite showed **no** last-pair bias → that bias is llama's habit.

## Final robustness labels (writeup/results_22.md)

| Claim | Label |
|---|---|
| Messages alone fail | Robust **for llama** (RQ9: not for granite) |
| Actions alone fail | Robust **for llama** (RQ9: not for granite) |
| Structure beats same-length raw view | Robust for llama |
| Private plans don't help | Consistent null (no detectable gain at n = 24) |
| Same-incentive fools messages | Robust for llama |
| Position bias exists | Robust (llama-specific per RQ9) |
| Code action signals competitive | Consistent (exploratory) |
| Combining helps (RQ2) | **Fragile** |
| Structure beats full raw view (V4 − V3) | **Fragile** |
| Persona talk fools actions | **Fragile** |
| Position bias explains the raw-view failure | **Not supported** |

## The Study 2.2 answer, in one paragraph

> In this pilot, whether an LLM monitor detects collusion better from messages, actions or both **depends heavily on the monitor model**. With llama3.1:8b, messages alone and actions alone failed (each fooled by a different innocent lookalike), and a code-built structured report worked best. With granite3.3:8b, the ranking reversed. Only the combined raw view scored the same with both. "Combining helps" did not hold across all games. Simple model-free behaviour statistics (who went together, who captured the bar) worked about as well as the best AI view. The LLM monitors also showed reliability problems: a constant score (always 80), position bias, and changes between sessions.

---

# PART 6 — Study 2.3 results

## What was built (13C)

- **The judge** (`judge_v1`, llama3.1:8b on the MacBook): reads only public messages, scores all 10 pairs.
- **Rules R1–R7**, fitted on the 24 dev games and frozen (`rules_frozen.json`).
- **Dev choices (fixed before test):** best single rule = **R2 (gain)**; best combined rule = **R6 (points)**.

## Test results (17C, 24 test games)

| Rule | AUROC | TPR | FPR | False alarms (Type 2 / 3 / 4b) |
|---|---|---|---|---|
| R1 judge (talk) | **0.396** (below chance) | 0.667 | 0.917 | 4/4, 4/4, 3/4 |
| **R2 gain** | **0.872** | 0.833 | 0.167 | 0/4, 0/4, **2/4** |
| R3 dependence | 0.736 | 0.750 | 0.333 | 1/4, 1/4, 2/4 |
| R4 legal style | — | 0.167 | **0.000** | 0, 0, 0 |
| R5 gain + dependence | — | 0.333 | 0.167 | 0, 0, 2/4 |
| R6 points | 0.792 | 0.917 | 0.333 | 1/4, 0/4, 3/4 |
| R7 learned | 0.812 | 0.833 | 0.167 | 0/4, 0/4, 2/4 |

| Question | Result | Simple reading |
|---|---|---|
| **RQ-E1/E2** | Gain is the best single evidence; talk (judge) is useless; same-incentive games fool gain 2 of 4 times | Behaviour carries the signal; acting alike can still fool it. |
| **RQ-E3** (main) | R6 − R2 = **−0.080 [−0.208, 0.045]** → "no clear difference" | Combining evidence did not beat gain alone. |
| **RQ-E4** ablation | Removing **gain** destroys the rules; removing judge, dependence or word–action changes nothing | Gain carries almost all the signal. |
| **RQ-E5** word–action | Adds nothing | — |
| Exploratory plus-factor rule (capture AND coordination words) | 0 false alarms, but catches only 1/12 | Colluders keep their talk secret, so there are no public words to find. |

## Study 2.3 key findings in simple words

1. **Talk alone is not evidence.** The judge gave almost every game the maximum score (98) — a **ceiling effect** — and also preferred the last pair (T-Z in 18/24).
2. **Acting alike is not enough either.** Same-incentive agents fooled the behaviour rules 2 of 4 times — exactly why law says parallel conduct alone isn't proof.
3. **Gain (who benefits at others' expense) is the strongest single evidence**, and combining didn't beat it at n = 24.
4. **The strict legal-style rule never accused an innocent game but missed most collusion**, because our colluders kept their agreement secret in public. Like in real law, the communication evidence would have to come from private records.

---

# PART 7 — Failures, fixes and decisions

| # | Problem | When | What we did |
|---|---|---|---|
| 1 | Plan assumed paid models | Report 00 | Redesigned for local open models, $0 (report 01). |
| 2 | Ollama silently cuts long prompts | 01 | Always set num_ctx; added a truncation guard. |
| 3 | Same seed ≠ same answer | 01 | Disk cache is the only source of reproducibility. |
| 4 | "Dependence" formula scored 0 for always-together pairs | 01 | Replaced with level measures + NA rules. |
| 5 | Local models too slow | 01–04 | Brevity line (4.5× faster), 3 laptops, overnight runs. |
| 6 | 3B model planned but never acted | 01 | Used the 7B model. |
| 7 | Allies revealed and gained nothing | 06a | Added the strategy hint (alliance v3) + length-matched placebo v3. |
| 8 | Monitor formats: constant score / few values / cut-offs | 05, 07, 13 | Built v3_pairs (scores first, evidence capped); constant-score v1 ruled ineligible. |
| 9 | Windows line endings broke fingerprints on B | 08 | Normalised line endings in code + `.gitattributes`. |
| 10 | Pre-registration still said "DRAFT" | 08 | Lead fixed title in a new commit before any pilot call. |
| 11 | Uptake rule missed short commands | 08 | Amendment 1: uptake rule v2, validated by two human raters. |
| 12 | A game drifted into Chinese | 08 | Language line for all agents. |
| 13 | Public reveals > 10% | 09b–09c | Secrecy wording v4 + re-pilot; reveals kept as behaviour. |
| 14 | 2.36% cut-off answers | 09b | Kept as logged failures (no re-ask). |
| 15 | Cleaner removed harmless sentences | 06a–11 | Flag-only cleaner (remove only copied setup text). |
| 16 | V5 too long for the guard | 12–13 | num_ctx 16384 for all monitor calls. |
| 17 | Views worse than chance on dev → threshold 0 | 13–14 | AUROC as main metric; supplementary per-type AUROC pre-specified. |
| 18 | Position bias | 15–16 | Follow-up 1 with randomised order + same-session control. |
| 19 | Session-to-session score changes | 13, 16 | Measured and reported; replication planned. |
| 20 | Judge ceiling at 98 | 13C, 17C | Reported as a finding; rules frozen unchanged. |
| 21 | Mac machine letter not loaded | 15C | Fix planned in `~/.zshenv`; results unaffected. |
| 22 | Merge-conflict markers in the DEVLOG | 17C, 18a | Resolved by keeping both sides. |
| 23 | Small test set (n = 24) | everywhere | **Replication on 48 new games** (in progress). |

**Every deviation (22+) is listed in `writeup/results_22.md`, marked "decided before or after seeing the data".**

---

# PART 8 — Honest judgement: are the results good enough?

## Is the Study 2.2 output what we intended?

**What we intended:** to *measure* whether combining words and actions helps a monitor — honestly, with controls.

**What we got:** a clear, honest, but **more complicated** answer than we hoped:
- We did **not** get a clean "yes, combining helps". That result appeared on the test set but was **fragile** (not pooled, partly session luck).
- We **did** get strong, useful findings: single channels are fooled by lookalikes (for llama); structured evidence helps llama; **the results depend on the monitor model**; simple behaviour statistics work well; and LLM monitors have measurable reliability problems.

**Is it good enough?** **Yes, as research.** Negative and mixed results with strong controls are valuable — especially because most projects never test a second monitor, a session control, or position bias. Our integrity trail (pre-registration, freezes, amendments, deviation table, controls) is a strength.

**Weak points to state clearly:**
- Small samples (24 test games; 4 per lookalike type).
- Collusion was **suggested** by our prompt (with a hint), not invented by the agents.
- One game, one agent model.
- Monitor results depend on the model and even on the session.

## Is Study 2.3 good enough?

**Yes, as a first standard of evidence.** It gives a clear story that matches law: talk alone and acting alike alone are not enough; gain is the strongest evidence; strict rules avoid false accusations but miss most cases. The same weak points apply (small n, one judge model).

---

# PART 9 — What is happening right now

1. **Replication generation** (48 new games, seed 20261027) on machines A (16 games) and B (32 games), about 7 hours.
2. **Task 18c** (machine B): Study 2.2 replication analysis code, tested on fake data only.
3. **Task 19C** (machine C): Study 2.3 replication code, machine-letter fix, and a **draft amendment** to also test granite on the replication games (must be committed before any replication view is created).
4. **After generation:** merge on B → quality check → render views → frozen llama monitor on B (~2.5 h) → judge (and granite, if approved) on C → one analysis run per study.

**Pre-registered replication hypotheses** (configs/prereg_replication.md):
- Study 2.2: R1 messages alone fail, R2 structured report works, R3 combining helps, R4 V4 beats V3, R5 V4 beats same-length, R6 same-incentive fools messages, R7 persona fools actions, R8 oracle, R9 leak control, R10 capture works and is comparable to V4.
- Study 2.3: E1 gain works, E2 talk is weak, E3 combining vs best single (R6 vs R2), E3b (R7 vs R2), E4 lookalike flag rates.

**Rule for the end:** keep the last ~8 hours for writing, figures, slides and review — **no new experiments**.

---

# PART 10 — Index of report files

| Report | What it is about |
|---|---|
| 00 | First design (paid models; replaced) |
| 01 | Redesign for local models; benchmark; evidence fixes |
| 02 | P1 foundations (client, schema, labels, split, plan) |
| 03 | P3a RQ0.1 metrics (ML laptop) |
| 04 | P2 generator, brevity check, smoke game |
| 05 | P5 cleaner, views, monitor runner (machine B) |
| 06a | Pilot preparation (hint, placebo v3) |
| 07 | Monitor format candidates |
| 08 | Pilot 1 on B; CRLF fix; RQ0.1 fails on uptake |
| 09a | Amendment 1 (language line, uptake v2, two raters) |
| 09b | Pilot 2; RQ0.1 passes |
| 09c | Secrecy v4 re-pilot |
| 10 | Amendment 2; RQ0.1 status; dataset readiness |
| 11 | Analysis tools (flag-only cleaner, v3_pairs, stats, signals) |
| 12 | Dataset merge, quality, RQ0.2, views |
| 13 | P7 dev: monitor choice, RQ0.3, RQ0.4, freeze |
| 14 | P8 test: RQ1–RQ8 |
| 15 | Robustness, pooled, code signals, position bias, figures |
| 16 | Follow-up 1: pair order + session control |
| 17 | Study 2.2 synthesis + README |
| 13C | MacBook setup; judge + rules; dev fit; freeze |
| 17C | Study 2.3 test results |
| 15C | RQ9 granite second monitor |
| 18a | Replication pre-registration + plan |
| 18b | Replication labels file |
| 18c, 19C | In progress (replication code) |

**Key files to read next:**
- `writeup/results_22.md` — final Study 2.2 results with every number cited.
- `writeup/results_23.md` — Study 2.3 standard of evidence.
- `writeup/figures/` — Figures 1–8 with `captions.md`.
- `configs/prereg_*.md` — all pre-registrations and amendments.
- `README.md` — project overview.
