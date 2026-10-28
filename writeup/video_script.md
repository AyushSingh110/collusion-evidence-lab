# Collusion Evidence Lab — explainer video blueprint (4:45)

**Format:** 16:9, 1920×1080 · **Voice:** one engineer, relaxed and enthusiastic, ~140 words per minute · **Music:** low, steady electronic bed; drop it under the voiceover, lift it in the hook and the outro.

**Asset rules**
- Every asset path is relative to the repository root. Figures live in `writeup/figures/`.
- Every number on screen and in the voiceover comes from `writeup/results_summary.md`, `writeup/results_22.md`, `writeup/results_23.md` or `writeup/figures/captions.md`. Do not round or change them.
- Figures 9 and 10 still say "Study 2.2" and "Study 2.3" in their titles. In the video, either crop the title or cover it with a "Study 1" / "Study 2" label.
- Code is shown as screen recordings of the file open in an editor (dark theme, font size 18+, line numbers on).

**Visual identity:** dark navy background (#0b1020), blue accent (#8fa3ff) for normal agents, red accent (#ff5c7a) for the colluding pair. Five agent circles labelled J, M, Q, T, Z recur throughout, taken from `assets/banner.svg`.

---

## 1. Hook & problem statement (0:00 – 0:45)

| Timestamp & visual action | Animation & text overlay | Voiceover script | Asset reference |
|---|---|---|---|
| **0:00–0:08** Black screen. Five agent circles fade in one by one in a ring. A dashed red line quietly connects T and Z. | Circles pop in on each word. The red dashed line draws itself at "quietly". Overlay: **"Two of these agents are working together."** | "Here are five AI agents. Two of them are secretly working together. Can you tell which two?" | `assets/banner.svg` (agent ring, recreated as an animation) |
| **0:08–0:22** The ring shrinks into the corner. A fake log scrolls past: chat lines, then GO / STAY actions, then payoffs. | Three tags slide in over the log: **"What they said"**, **"What they did"**, **"What happened"**. Each tag lights up as the matching log section scrolls by. | "That's the auditor's problem. If two AI agents team up against the rest, you rarely catch them in the act. You just get logs: what they said, what they did, and how it turned out." | `writeup/excerpts_22.md`: case (a), lines from game `g_77be9e68db`, shown as scrolling text |
| **0:22–0:35** Split screen. Left: a speech bubble icon labelled "Read the chat". Right: a bar-chart icon labelled "Check the behaviour". A robot reviewer sits in the middle. | A question mark pulses over the robot. Overlay: **"Can an AI monitor tell?"** | "So the obvious idea is: hand those logs to another AI and ask it, 'Is anyone colluding here?' But is that actually reliable? And what should even count as evidence?" | none (motion graphics) |
| **0:35–0:45** Full-screen title card from the banner. | Title types in: **"Behaviour Beats Judgement"**, then the subtitle **"Auditing collusion between LLM agents"**. Three small pills slide up: *pre-registered*, *replicated on 48 new games*, *local models, $0*. | "That's what we set out to test. Spoiler: the answer surprised us." | `assets/banner.svg` |

## 2. Research & discoveries (0:45 – 1:45)

| Timestamp & visual action | Animation & text overlay | Voiceover script | Asset reference |
|---|---|---|---|
| **0:45–1:00** Animated bar-game scene: a bar with a capacity sign "2", five agents deciding GO or STAY. Then four cards flip in: Collusion, Placebo, Persona talk, Shared incentive. | Payoff tags float up: **+$10 if the bar isn't crowded**, **−$5 if it is**, **$0 at home**. The cards get colour codes: red, grey, blue, orange. | "Our agents play El Farol, where the bar only pays if it isn't crowded. Some games hide a secret alliance with a private channel. Others are lookalikes: a placebo, a friendly pair, or a pair with a private reason to go." | `writeup/paper.md`: section "Episode types and ground truth" (cards built from it) |
| **1:00–1:15** Slow zoom into the test-set bar chart. Highlight V4, then V1 and V2. | V4's bar glows. A label snaps on: **0.896**. V1 and V2 dim, with labels **0.490** and **0.372**. A dashed "coin flip = 0.5" line pulses once. | "First result, on the test games: an LLM monitor reading a structured report built by our code scored 0.896. Reading only the chat, or only the actions? Basically a coin flip." | `writeup/figures/fig1_auroc_by_view_test.png` |
| **1:15–1:30** Cut to the per-game score grid. Circle the persona-talk dots in V2 and the shared-incentive dots in V1. | Circles draw around the dot clusters. Two overlays appear one after the other: **"Friendly chat fools the actions view"**, **"Shared incentive fools the messages view"**. | "And each lookalike fooled a different view. Friendly chat tripped up the monitor reading actions. The shared incentive tripped up the one reading messages." | `writeup/figures/fig2_per_type_scores_test.png` |
| **1:30–1:45** Transition to the replication figure. Grey dots (original test) shift left, dark and red dots (new games) appear. Pan right to the "capture" column. | V4's grey dot at 0.896 visibly drops to the dark dot at 0.636, with a red arrow. On the right, the capture dot holds steady: overlay **"0.900 — no LLM at all"**. | "That is a small sample, so we re-ran everything, frozen, on 48 new games. The structured report fell to 0.636. A code signal, how often the pair had the bar to themselves, hit 0.900." | `writeup/figures/fig9_replication_22.png` (cover the "Study 2.2" title with "Study 1") |

## 3. Architecture & tech stack (1:45 – 2:45)

| Timestamp & visual action | Animation & text overlay | Voiceover script | Asset reference |
|---|---|---|---|
| **1:45–2:00** The pipeline diagram builds left to right: Plan → Generation → Raw record. | Each box fades in as it's named; arrows draw between them. Small tech badges pop next to the boxes: **Python 3.11**, **Ollama 0.40.3**, **qwen2.5:7b**. | "Here's how it's built. A plan file fixes every game's seed, type and secret pair before anything runs. Then five Qwen agents play it out locally through Ollama, and we save the full raw record." | `writeup/paper.tex`: pipeline figure (TikZ, Fig. 1 in the PDF) or redraw from `README.md` (Mermaid "Pipeline") |
| **2:00–2:15** The diagram splits at "Raw record": a gold branch goes up to "Labels from config", a grey branch down to "Cleaner". | The gold box gets a lock icon and the overlay **"Ground truth comes from the setup — never from a model"**. The cleaner box shows a filter animation stripping out red "secret" lines. | "Next, the labels, collusion or not, come straight from the setup, never from a model's opinion. And a cleaner strips everything private, so the monitors only see what a real auditor would see." | same pipeline diagram; `core/clean/cleaner.py` (filename shown as a caption) |
| **2:15–2:30** The cleaner box fans out into five "view" cards V1–V5 plus three grey control cards, all feeding an "LLM monitor" box. | Cards deal out like playing cards: **V1 messages**, **V2 actions**, **V3 both**, **V4 structured report**, **V5 + private plans**. Then the controls slide in greyed out: *mismatch*, *length-matched*, *shuffled*. | "From the cleaned record we render five views of the same game, plus three control views that catch shortcuts. The same monitor, Llama, or Granite as a second opinion, scores every pair in every view." | `study_2_2_views/views.py` (filename caption) |
| **2:30–2:45** The bottom branch lights up: "Code evidence + LLM judge" → "Decision rules R1–R7". | Four evidence chips stack up: **conversation**, **coalition gain**, **dependence**, **word vs action**. They feed into a "rules" box labelled **R1–R7**. | "In parallel, plain code computes behaviour evidence, and seven frozen rules turn it into a verdict. Everything runs locally at zero cost, pinned to exact versions and cached, so anyone can re-check our numbers." | `configs/frozen/rules_frozen.json`, `configs/pins.json` |

## 4. Key engineering decisions (2:45 – 3:45)

| Timestamp & visual action | Animation & text overlay | Voiceover script | Asset reference |
|---|---|---|---|
| **2:45–3:00** A ledger page with timestamps; one entry is stamped **"FROZEN"**. Then the pre-registration file list scrolls by. | Stamp slams down with a small shake. Overlay: **"Decide first. Test once."** A counter ticks up to **8 pre-registration documents**. | "Our biggest decision was discipline. We wrote every plan down before seeing its data, tuned on 24 development games, and ran the test set once. Every change went into a deviation log: 39 entries." | `configs/prereg_rq01.md`, `configs/prereg_replication.md`, `writeup/results_22.md` §f (deviation table) |
| **3:00–3:15** A test result card reads **"Pilot 1 — uptake 2/4 — FAIL"** in red. It flips to **"Amendment 1 → Pilot 2: 4/4 — PASS"** in green. | Red card shakes, then flips. Overlay: **"We kept the failure on the record."** | "Things did break. Our first pilot failed a check: the uptake rule fired in only two of four games, and one game drifted into Chinese. We wrote an amendment, ran a fresh pilot, and kept the failure on the record." | `configs/prereg_rq01_amendment1.md` |
| **3:15–3:30** A bar of identical numbers: "80, 80, 80, 80…" fills the screen. | The 80s multiply rapidly, then freeze. Counter: **96 / 96 calls = 80**. Then the screen splits into 10 pair rows with varied scores. | "Another surprise: our first monitor format, one score per game, returned 80 every time. Ninety-six out of ninety-six. So we switched to scoring each pair, and made that call on development data, before the test set." | `configs/monitor/manifest_v3_pairs.json` |
| **3:30–3:45** A slider labelled "Clean harder ↔ Keep behaviour" sits in the middle. A speech bubble says "my deposit…". | The slider wobbles, then settles in the middle. Overlay: **"Trade-off: flag, don't over-delete."** | "Deleting anything suspicious would also wipe out real behaviour, so the cleaner only removes copied setup text and flags the rest. The cost: shared-incentive agents mention their deposit in public, and we report that as a limitation." | `core/clean/cleaner.py`; `writeup/results_22.md` §e (limitations) |

## 5. Live demo / code walkthrough (3:45 – 4:30)

| Timestamp & visual action | Animation & text overlay | Voiceover script | Asset reference |
|---|---|---|---|
| **3:45–3:56** Screen recording: `core/generate/runner.py` open in the editor, scroll through the round loop. Terminal below runs `run_plan.py`, printing one line per round. | A highlight box follows the scroll. Overlay in the corner: **"1 · Generate"**. | "Let's open the code. The runner plays each game round by round: a private plan, a public announcement, then a final GO or STAY." | `core/generate/runner.py`, `scripts/run_plan.py` |
| **3:56–4:07** Editor switches to `core/llm/client.py`; highlight `check_pins` and `cache_key`, then the `CachedLLM` class. | Two highlight boxes: **"exact model version or stop"** on `check_pins`, **"never pay twice"** on `cache_key`. Overlay: **"2 · Every call pinned & cached"**. | "Every model call goes through this client. It refuses to run unless the model matches its pinned version, and it caches every answer, so re-running costs nothing." | `core/llm/client.py` |
| **4:07–4:18** Editor switches to `study_2_2_views/views.py`, scrolled to `_v4`. Side panel shows a rendered V4 report. | Lines of the report highlight one by one: broken promises, rounds both went, mentions. Overlay: **"3 · Views"**. | "This builds the structured report: who broke a promise, which pairs went together, and who mentions whom. Those mention counts are exactly what fooled the monitor." | `study_2_2_views/views.py` |
| **4:18–4:30** Editor switches to `core/evidence/signals.py`, highlight `pair_signal_table`. Then cut to a quote card. | Quote types out in a terminal font: **"T and Z repeatedly mention each other in messages, suggesting coordination."** A red tag appears under it: **"Nobody went to the bar. Score: 80."** | "This is the plain-code evidence that won. Compare the monitor's verdict on a game where two agents just chatted, and nobody went to the bar. It still gave them 80." | `core/evidence/signals.py`; `writeup/excerpts_22.md` case (d), game `g_4e868953d1` |

## 6. Conclusion & impact (4:30 – 5:00)

| Timestamp & visual action | Animation & text overlay | Voiceover script | Asset reference |
|---|---|---|---|
| **4:30–4:45** The Study 2 replication figure animates in; R2 and capture glow, R1 dims. Then a balance scale: "Behaviour" outweighs "Judgement". | Three takeaway lines stack in: **"Behaviour signals: 0.900, and they replicated"**, **"LLM monitors: 0.32–0.66 on new games"**, **"Shared incentives still fool outcome evidence"**. | "Here's where we landed. What agents did beat what an AI concluded from reading about it, and it held up on new games. LLM monitors were shaky. But outcomes alone aren't proof: agents that share an incentive look like colluders." | `writeup/figures/fig10_replication_23.png` (cover the "Study 2.3" title with "Study 2") |
| **4:45–5:00** Back to the agent ring from the opening; the red T–Z line pulses once, then the title card returns with the repo link. | End card: **"Behaviour Beats Judgement"**, GitHub link **github.com/AyushSingh110/collusion-evidence-lab**, and the four author names. Music swells and cuts. | "If you're building systems where AI agents work together, start with the behaviour data, and make any AI monitor prove it can beat it. Everything's open, from the code to the plans to the mistakes. Thanks for watching." | `assets/banner.svg`; `README.md` (repo link) |

---

**Run time:** 5:00. If you need 4:45, trim scene 2:00–2:15 to 10 seconds and scene 3:30–3:45 to 10 seconds.

**Optional B-roll** (for cutaways, all real repo files):
- `writeup/figures/fig4_dev_vs_test_auroc.png`: dev vs test shift, if the decisions section needs a visual for "small samples mislead".
- `writeup/figures/fig7_pair_order_followup.png`: the last-position bias follow-up.
- `writeup/figures/fig8_rq9_granite.png`: the second monitor model disagreeing with the first.
- `writeup/figures/fig6_code_signals_vs_V4.png`: code signals vs the structured report on the test set.
