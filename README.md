<div align="center">

<img src="assets/banner.svg" alt="Collusion Evidence Lab — can an auditor tell when two LLM agents secretly team up?" width="100%"/>

<br/>

# 🕵️ Collusion Evidence Lab

**Detecting and auditing collusion between LLM agents: monitor views vs. behaviour evidence, with a pre-registered replication.**

<p>
  <a href="writeup/paper.md"><img alt="Paper" src="https://img.shields.io/badge/paper-read-b31b1b?style=for-the-badge&logo=readthedocs&logoColor=white"/></a>
  <a href="writeup/results_summary.md"><img alt="One-page summary" src="https://img.shields.io/badge/summary-1_page-4c6ef5?style=for-the-badge"/></a>
  <a href="configs/prereg_replication.md"><img alt="Pre-registered" src="https://img.shields.io/badge/pre--registered-yes-2f9e44?style=for-the-badge"/></a>
</p>

<p>
  <img alt="Python 3.11" src="https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white"/>
  <img alt="Ollama 0.40.3" src="https://img.shields.io/badge/ollama-0.40.3-000000?logo=ollama&logoColor=white"/>
  <img alt="Agents qwen2.5:7b" src="https://img.shields.io/badge/agents-qwen2.5%3A7b-7048e8"/>
  <img alt="Monitors" src="https://img.shields.io/badge/monitors-llama3.1%3A8b%20%7C%20granite3.3%3A8b-1971c2"/>
  <img alt="Cost" src="https://img.shields.io/badge/API%20cost-%240-2f9e44"/>
  <img alt="Replication" src="https://img.shields.io/badge/replication-48%20new%20games-e8590c"/>
  <img alt="Tests" src="https://img.shields.io/badge/tests-pytest%20%C2%B7%20mock%20LLM-0ca678?logo=pytest&logoColor=white"/>
  <img alt="Sprint" src="https://img.shields.io/badge/AI%20Collusion%20Research%20Sprint-Oct%202026-f08c00"/>
</p>

[**Paper**](writeup/paper.md) · [**LaTeX**](writeup/paper.tex) · [**Study 2.2 results**](writeup/results_22.md) · [**Study 2.3 results**](writeup/results_23.md) · [**Figures**](writeup/figures/) · [**Work log & reports**](notes/)

</div>

---

> [!IMPORTANT]
> **TL;DR.** Five LLM agents play a repeated bar game. In some games, two of them get a secret alliance. In other games, two "lookalikes" imitate collusion without any agreement.
>
> **What did and didn't work:**
> - **Model-free behaviour signals were the most reliable way to catch the colluders, and that result replicated:**
>   - capture: AUROC **0.900** on 48 new games;
>   - capture beat the best LLM monitor view by **+0.264**.
> - **Small LLM monitors were mediocre and inconsistent** on new games (every view **0.32–0.66**).
> - **Reading the messages alone never worked.** Neither did a talk-only LLM judge.
> - **Outcome evidence is necessary but not sufficient:** a shared private incentive produces the same outcomes.

---

## 📑 Contents

- [Why this matters](#-why-this-matters)
- [Key findings](#-key-findings)
- [How it works](#%EF%B8%8F-how-it-works)
- [Results at a glance](#-results-at-a-glance)
- [Where LLM monitors fail](#-where-llm-monitors-fail)
- [Research integrity](#-research-integrity)
- [Quickstart](#-quickstart)
- [Repository layout](#-repository-layout)
- [Limitations](#%EF%B8%8F-limitations)
- [Citation](#-citation)
- [Acknowledgements](#-acknowledgements)

---

## 🎯 Why this matters

LLM agents increasingly act side by side: in markets, in shared infrastructure and in multi-agent workflows. If two of them quietly coordinate against the rest, an auditor usually has only **logs**: what agents *said*, what they *did*, and what happened. This project answers two questions from Track 2 of the AI Collusion Research Sprint:

| | Question | What we test |
|---|---|---|
| **2.2** | *Does combining what agents say with what they do beat either alone?* | The same LLM monitor reads different **views** of each game record |
| **2.3** | *What should count as convincing evidence of collusion?* | Evidence families and fixed **decision rules**, framed like antitrust "plus factors" |

> In competition law, **parallel conduct alone does not prove an agreement**: firms may move together for independent reasons. Courts look for *plus factors* on top. Our dataset contains lookalikes that test both halves of that rule.

---

## 🔑 Key findings

<div align="center">

| # | Finding | Key number(s) | Status |
|:-:|---|---|:-:|
| 1 | **Model-free behaviour signals were the most reliable evidence** | capture **0.900** [0.811, 0.965]; capture − best LLM view +0.264 [0.121, 0.412]; coalition gain **0.885** [0.786, 0.961] | ✅ Replicated |
| 2 | Both LLM monitors were **mediocre and inconsistent** on new games | all views V1–V4, both monitors, between 0.32 and 0.66; llama's structured report 0.896 → 0.636 | ❌ Original V4 advantage not replicated |
| 3 | Reading the **messages alone never worked** | V1 0.490 (test) → 0.505 (replication) | ✅ Replicated |
| 4 | **Talk-only LLM judging was near chance** | judge 0.396 (test) → 0.543 [0.392, 0.693] | ✅ Replicated |
| 5 | **Private plans added nothing** | V5 − V3 −0.031 (test), −0.022 [−0.192, 0.155] | ⚪ Consistent null |
| 6 | **Combining evidence did not beat gain alone** | R6 − R2 −0.080 (test), −0.059 [−0.135, 0.010] | ⚪ Replicated null |
| 7 | **Which view works depends on the monitor** | llama V4 − V2 +0.313 [0.127, 0.481]; granite −0.046 [−0.251, 0.152] | ⚠️ Not shared between monitors |
| 8 | llama has a **last-position bias** in its pair scores (granite does not) | last-listed pair gets the top score in 44/48 V1 replies vs 0.215 expected | ✅ Replicated (llama only) |

<sub>AUROC with 95% stratified bootstrap CIs (B = 2000). Every number is copied from <a href="writeup/results_summary.md"><code>writeup/results_summary.md</code></a>, where each one cites its report.</sub>

</div>

---

## ⚙️ How it works

### The game

**El Farol bar game:**
- 5 agents (J, M, Q, T, Z), all `qwen2.5:7b`, 8 rounds.
- Payoffs: going pays **$10** if at most 2 of 5 go; a crowded bar pays **−$5**; staying home pays **$0**.
- Each round (built on the [Shi et al. 2026](https://arxiv.org/abs/2607.05132) harness) has three stages:
  1. a **private plan**;
  2. a **public announcement** with a message;
  3. a simultaneous **GO / STAY** choice.

### Four kinds of games: one real, three lookalikes

| Type | What happens | Collusion? | Built to fool… |
|---|---|:-:|---|
| 🔴 **T1 Collusion** | Two agents get an alliance note + a private channel | **Yes** | — |
| ⚪ **T2 Placebo** | A neutral, length-matched note; honest play | No | — |
| 💬 **T3 Persona talk** | Two agents talk like friends in public; no agreement | No | **word** evidence |
| 💰 **T4b Shared incentive** | Two agents privately lose an $8 deposit if they stay home → both go, no agreement | No | **outcome** evidence ("conscious parallelism") |

**Ground truth comes only from how each game was generated.** One dev/test split (24 / 24) was fixed **before** any game existed.

### The pipeline

```mermaid
flowchart LR
    P["📋 Plan<br/>seed · type · focal pair"] --> G["🎲 Generation<br/>5 × qwen2.5:7b · El Farol · 8 rounds"]
    G --> R["🗂️ Raw record<br/>private + public"]
    R --> L["🏷️ Labels from config<br/>+ one dev/test split"]
    R --> C["🧹 Cleaner<br/>public fields only"]
    C --> V["👁️ Views V1–V5<br/>+ 3 controls"]
    V --> M["🤖 LLM monitor<br/>llama3.1:8b / granite3.3:8b"]
    C --> E["📐 Code evidence<br/>+ LLM judge"]
    E --> D["⚖️ Decision rules<br/>R1–R7"]
```

### What the monitor sees (Study 2.2)

| View | Contents |
|---|---|
| **V1** messages | All public announcements and messages |
| **V2** actions | Final actions and payoffs per round |
| **V3** combined | V1 + V2, interleaved per round |
| **V4** structured report | Built by code: announced vs. actual, broken promises, per-pair co-attendance and mentions |
| **V5** oracle | V3 + private plans and reasoning (never the private channel) |
| **Controls** | C-mismatch (words of one game, actions of another), C-length (V3 cut to V4's length), C-shuffled (leak check) |

### What counts as evidence (Study 2.3)

| Family | Signal | Plain meaning |
|---|---|---|
| E1 conversation | LLM judge (+ keywords) | Does the public talk look like an agreement? |
| E2 coalition advantage | G_others | Does the pair do better than everyone else? |
| E3 dependence | Dep | Do the pair's choices depend on each other? |
| E4 word–action | W_joint | Do the pair break public promises together? |

These are combined into seven frozen rules (R1–R7). Examples: "gain only", "legal-style: parallel conduct + a plus factor", "points", and a learned logistic rule.

---

## 📊 Results at a glance

<div align="center">

<img src="writeup/figures/fig9_replication_22.png" alt="Study 2.2: original test vs pre-registered replication" width="92%"/>

<sub><b>Study 2.2 — original test vs. pre-registered replication.</b> The structured report's original 0.896 shrank to 0.636. No LLM view of either monitor reaches 0.7 on the new games, while the model-free capture signal stays at about 0.90.</sub>

</div>

<details>
<summary><b>📋 Per-view AUROC on the 48 replication games</b> (click to expand)</summary>

| Monitor | V1 | V2 | V3 | V4 |
|---|---|---|---|---|
| llama3.1:8b | 0.505 [0.363, 0.655] | 0.324 [0.186, 0.469] | 0.565 [0.421, 0.706] | 0.636 [0.507, 0.751] |
| granite3.3:8b | 0.618 [0.474, 0.756] | 0.628 [0.488, 0.754] | 0.662 [0.560, 0.771] | 0.582 [0.414, 0.730] |
| **capture (no LLM)** | | | | **0.900 [0.811, 0.965]** |

</details>

<br/>

<div align="center">

<img src="writeup/figures/fig10_replication_23.png" alt="Study 2.3: frozen decision rules, original test vs replication" width="85%"/>

<sub><b>Study 2.3 — frozen decision rules.</b> The gain rule R2 replicates (0.872 → 0.885); the talk-only judge R1 stays near chance (0.396 → 0.543); the combined rules R6 / R7 do not beat R2.</sub>

</div>

<details>
<summary><b>⚖️ The standard of evidence, in one table</b> (click to expand)</summary>

| Rule | AUROC test | AUROC replication | False positives on shared-incentive games (replication) |
|---|---|---|---|
| R1 judge (talk only) | 0.396 | 0.543 | 4/8 |
| **R2 coalition gain** | **0.872** | **0.885** | **3/8** |
| R6 points (combined) | 0.792 | 0.826 | 3/8 |
| R7 learned (combined) | 0.812 | 0.844 | 3/8 |
| Plus-factor rule (capture AND coordination words) | — | — | catches **0/24** colluders on the replication |

**In one line:** outcome evidence (gain, capture) is necessary and replicates, but it is not sufficient against a shared incentive. None of the communication evidence we measured was a usable plus factor.

</details>

<details>
<summary><b>🔬 More figures</b> (click to expand)</summary>

| | |
|:-:|:-:|
| <img src="writeup/figures/fig1_auroc_by_view_test.png" width="100%"/><br/><sub>AUROC per view, original test (n = 24)</sub> | <img src="writeup/figures/fig2_per_type_scores_test.png" width="100%"/><br/><sub>Monitor score per game, by episode type (exploratory)</sub> |
| <img src="writeup/figures/fig7_pair_order_followup.png" width="100%"/><br/><sub>Follow-up 1: randomising the pair order</sub> | <img src="writeup/figures/fig8_rq9_granite.png" width="100%"/><br/><sub>RQ9: the same prompt with a second monitor model</sub> |

All figures and captions: [`writeup/figures/`](writeup/figures/) · [`captions.md`](writeup/figures/captions.md)

</details>

---

## 🧨 Where LLM monitors fail

| Failure mode | Evidence |
|---|---|
| 🎚️ **Constant score** | The single-score format returned **80 on 96/96** dev calls, so we switched to per-pair scoring before any test call |
| 🧱 **Judge ceiling** | The messages-only judge scored almost every game near 98 and never above 98 (0 of 480 pair scores) |
| 📍 **Position bias** (llama only) | The last-listed pair got the top score in **44/48** V1 replies (no-bias expectation 0.215) |
| 🔄 **Session effect** | Re-scoring V2 unchanged in a new session moved its AUROC by **+0.188** [+0.007, +0.389] |
| 📉 **Small-sample optimism** | Best first results shrank on new games: llama V4 **0.896 → 0.636**, granite V2 **0.767 → 0.628** |
| 💬 **Friendly talk read as collusion** | V4 flagged **8/8** persona-talk games on the replication; mention counts look like a pair signal |

---

## 🧪 Research integrity

- 🔒 **Pre-registered:** every decision was frozen before the data it affects. The full chain, with commits:

  | Document | Commit |
  |---|---|
  | [`prereg_rq01.md`](configs/prereg_rq01.md) (frozen) | `4909c7e` |
  | [`prereg_rq01_amendment1.md`](configs/prereg_rq01_amendment1.md) | `2d47580` |
  | [`prereg_rq01_amendment2.md`](configs/prereg_rq01_amendment2.md) | `a989c7a` |
  | [`prereg_rq01_amendment2_erratum.md`](configs/prereg_rq01_amendment2_erratum.md) | `0dfd1b1` |
  | [`frozen/monitor_frozen.json`](configs/frozen/) (frozen monitor + dev thresholds) | `89bdb79` |
  | [`prereg_followup1_pair_order.md`](configs/prereg_followup1_pair_order.md) | `496fc28` |
  | [`prereg_replication.md`](configs/prereg_replication.md) | `2bc3d3a` |
  | [`prereg_replication_amendment1.md`](configs/prereg_replication_amendment1.md) (second monitor) | `306502e` |

- 🧊 **Frozen, then tested once:** prompts, formats and thresholds were chosen on 24 dev games, then run **once** on 24 test games. The 48 replication games were never used to fit anything.
- 📝 **Failures stay on the record:** the first pilot **failed** its own pre-registered check (uptake 2/4). We report it, together with the amendment that replaced the rule. All **39 deviations** are listed with "decided before / after the data" in [`results_22.md` §f](writeup/results_22.md).
- 🏷️ **Labels from config only:** an LLM never decides ground truth.
- 💾 **Every LLM call is cached:** keyed by model digest, prompt, schema, settings, seed and sample index.
- 💸 **$0, fully local:** Ollama **0.40.3**, every model pinned by digest (`configs/pins.json`):

  | Model | Digest |
  |---|---|
  | `qwen2.5:7b` | `845dbda0ea48…` |
  | `llama3.1:8b` | `46e0c10c039e…` |
  | `granite3.3:8b` | `fd429f23b909…` |

---

## 🚀 Quickstart

```bash
# 1. one conda environment for everything
conda env create -f environment.yml                       # environment name: collusion-lab

# 2. run the test suite (mock LLM transport, no model calls)
conda run -n collusion-lab pytest -q

# 3. check the local model setup (needs Ollama 0.40.3 with the pinned models)
ollama pull qwen2.5:7b && ollama pull llama3.1:8b
conda run -n collusion-lab python scripts/check_env.py    # must end with: RESULT: READY
conda run --no-capture-output -n collusion-lab python -u scripts/selftest.py
```

> [!NOTE]
> Two tests in `tests/test_replication22.py` re-derive the original test-set tables. They need the local `data/labels.csv`, which is not in git, so they fail on a fresh clone. All other tests run anywhere.

<details>
<summary><b>▶️ Generate games and run the pipeline</b> (click to expand)</summary>

```bash
# plan games (one central file: ids, types, focal pairs, seeds, machine assignment)
conda run -n collusion-lab python scripts/make_plan.py --name mygames --seed 12345 \
    --counts 1=24 2=8 3=8 4=8 --machines A B --rounds 8

# each machine runs its own games (resumable; prints a line per round)
conda run --no-capture-output -n collusion-lab python -u scripts/run_plan.py \
    --plan configs/plans/mygames.json --machine A

# merge and verify (one record per game, pinned digests, unique seeds, cache complete)
conda run -n collusion-lab python scripts/merge_check.py \
    --plan configs/plans/mygames.json --raw-dir data/raw/mygames
```

Rendering views, running the monitor and the analyses: see the commands in the per-task reports in [`notes/reports/`](notes/reports/).

</details>

---

## 📁 Repository layout

```
configs/            pre-registrations, frozen monitor + rules, prompts, monitor templates, pins, plans
core/               generation (El Farol runner), cleaning + leak scan, pinned & cached LLM client,
                    labels / split, plan, schema, statistics, evidence signals
study_2_2_views/    view rendering, monitor runner, Study 2.2 analysis
study_2_3_evidence/ judge, decision rules, Study 2.3 analysis
scripts/            CLI entry points (check_env, selftest, make_plan, run_plan, merge_check,
                    render_views, run_monitor, analyses, ...)
tests/              pytest suite (mock LLM transport)
writeup/            paper (md + LaTeX), results, case studies, figures + captions
notes/              DEVLOG.md (append-only work log) and reports/ (one report per task)
scratch/            per-task measurement and analysis scripts and small results
external/           starter code, read-only (Shi et al. harness; TraceGuard rubric)
assets/             README banner
```

> **Not in git:** `data/` (games, labels, split, views), `cache/` (every LLM response) and `runs/` (monitor outputs, analysis tables). Without the cache, re-running makes new model calls, and these may not reproduce every score exactly (session nondeterminism).

---

## ⚠️ Limitations

- **Small samples:** 24 test + 48 replication games, with 8 or fewer per lookalike type, so CIs are wide.
- **Narrow setup:** one game, one agent model, 8 rounds. The collusion is **suggested by a prompt**, not invented by the agents.
- **Two small monitors** (8B), one frozen prompt format, one sample per call. Scores can change between sessions. The second monitor ran on different hardware, so model and hardware are confounded.
- **An unplanned clue:** shared-incentive agents talk about their "deposit" in public, and monitors could see it.

Full list: [`writeup/results_22.md` §e](writeup/results_22.md) and [`writeup/results_23.md` §5](writeup/results_23.md).

---

## 📖 Citation

If you use this testbed or its findings, please cite:

```bibtex
@misc{collusion_evidence_lab_2026,
  title        = {Behaviour Beats Judgement: Auditing Collusion Between LLM Agents
                  with Monitor Views and Antitrust-Style Evidence},
  author       = {{Collusion Evidence Lab team}},
  year         = {2026},
  howpublished = {AI Collusion Research Sprint (Apart Research), Track 2},
  url          = {https://github.com/AyushSingh110/collusion-evidence-lab}
}
```

---

## 🙏 Acknowledgements

- [**Apart Research**](https://apartresearch.com/) and the **AI Collusion Research Sprint** (October 2026) for the research questions and the starter code.
- **Shi et al. (2026)**, *When Agents Lie* ([arXiv:2607.05132](https://arxiv.org/abs/2607.05132)), for the game harness.
- **Nguyen et al. (2026)**, *TraceGuard* ([arXiv:2604.03968](https://arxiv.org/abs/2604.03968)), for the action–trace consistency rubric idea behind the structured report.
- The open-weight models **Qwen 2.5**, **Llama 3.1** and **Granite 3.3**, served locally with [**Ollama**](https://ollama.com/).

<div align="center">
<br/>

**⭐ If this was useful, consider starring the repo.**

<sub>Built in 3 days · every number traceable to a report in <code>notes/reports/</code> · no paid APIs</sub>

</div>
