# DEVLOG — collusion-evidence-lab

Append-only. Newest entry at the bottom. Never edit old entries; corrections are new entries
that refer to the old one.

---

## 2026-10-23 — Task 00 (design), Step 1 setup + Step 3 blocked

### What was implemented or executed
- Created `CLAUDE.md` with project rules A–I (no git writes, one conda env, DEVLOG, one report
  per task, ignored docs/data, read-only starter code, research integrity, cost control,
  scope discipline).
- Created `.gitignore` (Rule E): `notes/`, `CLAUDE.md`, `data/`, `runs/`, `cache/`,
  `external/`, `.env*` (except `.env.example`), Python/Jupyter/OS/editor junk.
- Created `notes/`, `notes/reports/`, and this DEVLOG.
- Created `environment.yml` and the conda env:
  - `conda env create -f environment.yml` → success.
  - `conda run -n collusion-lab python -c "import sys; print(sys.version)"` →
    `3.11.17 | packaged by conda-forge`, executable
    `C:\Users\ASUS\anaconda3\envs\collusion-lab\python.exe`.
  - `pip 26.2.2`. Pinned `python=3.11.17`, `pip=26.2.2` in `environment.yml`.
- Inspected the starter code location:
  - `ls -la external/llm-trust-breaking external/trace-guard` → both directories exist but
    are EMPTY (no files, no `.git`, no `.gitmodules` in the repo root).
- Git state (read-only): branch `main`, no commits yet, only `.env` untracked before this
  task. `.env` exists but is 0 bytes (no API keys yet).

### Errors and problems faced
- Starter code missing: `external/llm-trust-breaking/` and `external/trace-guard/` are empty.
  Root cause unknown (likely the clone/copy step was not done, or was done into another path).

### How each problem was solved
- Unsolved. Per the task prompt ("If it is missing, stop and tell me"), Step 3 (code
  investigation) and Step 4 (design report) were NOT started. Waiting for the team to
  populate `external/`.

### Decisions taken
- No dependencies beyond Python + pip were installed: the harness's requirements cannot be
  known until its code is present. Alternative considered: guess common packages (openai,
  anthropic, etc.) — rejected, it would pollute the env with unpinned guesses.
- Did not search for / clone the repos myself: Rule F says starter code is provided by the
  organisers and must be read-only; picking a repo/version on my own could pick the wrong one.
- `notes/reports/00_design_report.md` not written yet: the report depends on Step 3 evidence.
  It will be created when the task resumes.
- Channel: `conda-forge` only, for reproducible pinned builds.

### Open questions for the team
1. Where is the starter code? Please copy/clone `llm-trust-breaking` (Shi et al.) and
   `trace-guard` into `external/` (or give the URLs + commit hashes so they can be cloned).
2. Models and provider are still unfilled: agent model(s), monitor model, judge model,
   API provider. Design will stay provider-agnostic until decided.
3. `.env` is empty — API keys will be needed before any smoke run that calls an LLM.

---

## 2026-10-23 — Task 00 (design), resumed: starter code fetched, Steps 3–5

Refers to the previous entry ("Starter code missing"). That problem is now solved: the user gave
the URLs `github.com/poseidon-research/collusion_hackathon/tree/main/{llm-trust-breaking,trace-guard}`.

### What was implemented or executed
- `git ls-remote https://github.com/poseidon-research/collusion_hackathon refs/heads/main` →
  `d585a7b3be50366cc2bdf5789bf8add5890b2abd` (read-only; does not touch our repo).
- Downloaded `codeload.github.com/.../tar.gz/refs/heads/main` (≈225 MB, all 16 folders) into the
  scratchpad, extracted there, then copied ONLY into `external/`:
  `llm-trust-breaking/`, `trace-guard/`, `util/` (the `poseidon_compute` package the harness imports),
  and the root docs into `external/_hackathon_root/` (README.md, COMPUTE.md, compute.env.example,
  setup.sh). Source recorded in `external/SOURCE.txt`.
- Installed harness runtime deps into `collusion-lab`, pinned to the harness `uv.lock` versions for
  Python 3.11: openai 3.37.0, python-dotenv 1.2.4, requests 2.34.2, aiohttp 3.14.5, tqdm 4.70.1,
  numpy 2.4.6, matplotlib 3.11.2 (+ their transitive deps). Also poseidon-compute 0.1.0, installed
  from a scratchpad COPY of `external/util` so nothing was written into `external/`.
  Why: needed to import and smoke-test the harness (Step 1.4 / Step 3). `environment.yml` updated.
- Offline smoke test (scratchpad script `smoke/offline_smoke.py`, run with `python -B`): imported
  the 6 games, the prompt builders and the trial runner. Computed El Farol / Diners / Public-goods
  payoffs, built Stage 1–3 prompts and measured their size. Checked afterwards that there is no
  `__pycache__` in `external/`.
- Fetched OpenRouter's public model list (`GET https://openrouter.ai/api/v1/models`, no key, nothing
  sent) for current prices and structured-output / seed support of candidate models.
- Read the harness code (runner, trial_runner, prompt_builders, games, settings, client_factory,
  capabilities, queued client) and the TraceGuard rubric (dimensions.py, traceguard_monitor.py).
- Wrote `notes/reports/00_design_report.md` (17 sections, every statement tagged [V]/[A]/[P]).

### Errors and problems faced
1. First `curl … | python -c` to the GitHub API failed:
   `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`. Root cause: the
   unauthenticated GitHub API returned a non-JSON body (likely a rate limit). It did not stop the tarball download.
2. The tarball download took more than 2 minutes (225 MB), so the command was moved to the background.
3. `conda run -n collusion-lab python -c "<multi-line>"` failed with
   `AssertionError: Support for scripts where arguments contain newlines not implemented.` Root
   cause: `conda run` cannot pass multi-line `-c` arguments on Windows.
4. Importing `src/config/settings.py` raises
   `ValueError: OPENROUTER_API_KEY is not set, or is still the placeholder from .env.example.`
   Root cause: `.env` is empty and there is no `compute.env`. So no live LLM smoke test was possible.
5. Harness findings that matter for integrity (not errors in our code):
   - every request uses `seed: 42`;
   - the judge is hard-coded to `openai/gpt-5-mini`;
   - raw responses and token usage are not saved;
   - an invalid or missing action silently becomes STAY (El Farol) / CHEAP (Diners) when payoffs are
     computed — checked offline for El Farol.

### How each problem was solved
1. Used `git ls-remote` (read-only) to get the commit hash instead.
2. Waited for the background job to finish. Verified the archive extracted fully.
3. Wrote such scripts to files in the scratchpad and ran them with `conda run … python -B file.py`.
   Rule for the future: never pass multi-line `-c` through `conda run`.
4. Unsolved: needs an API key. Workaround: offline smoke test only. A live smoke game is planned in
   Phase 2 and will run only after the user's OK.
5. Design work-around (proposed): our own runner calls the harness prompt builders. It sets a
   different seed for each call, skips the judge and reflection, caches and logs every call, and
   keeps `None` actions as recorded failures.

### Decisions taken
- Downloaded a tarball instead of using `git clone`. Reason: Rule A (no git writes) and it keeps
  `.git` metadata out of `external/`. Alternative considered: `git clone` into the scratchpad and
  copy — equivalent, but slower for a 225 MB repo.
- Copied only `llm-trust-breaking/`, `trace-guard/` and `util/` into `external/`. Reason: scope.
  Alternative: copy all 16 folders — rejected. `colosseum/` and `steganographic-collusion/` stay in
  the scratchpad tarball; their use is listed as open question 14.
- Did NOT install TraceGuard. Reason: it needs Python ≥ 3.12, `control-arena`, `inspect-ai` and
  Docker, and we only reuse its rubric text (MIT licence). Alternative: a second environment —
  rejected, because Rule B says one environment.
- Recommended El Farol over Diners, Public goods, Volunteer, Weakest link and Fishing (reasons in
  report §2). Main reason: Diners and Public goods have a dominant action, so collusion would be
  invisible in the actions.
- All other design decisions are [P] in the report and wait for approval.

### Open questions for the team
See report §17 (14 questions, each with a recommendation). The most urgent ones:
1. Models and provider: recommended OpenRouter, gpt-4o-mini agents, gpt-4.1-mini monitor and judge,
   gemini-2.5-flash-lite as the second monitor. Needs an `OPENROUTER_API_KEY` in `.env`.
2. Dataset size: 48 or 60 games (60 recommended).
3. Approval of the protocol changes: no reflection step, rotating speaking order, private channel,
   Type 4b private incentive.

---

## 2026-10-23/24 — Task 01: design revision + RQ0.1 readiness (local Ollama, $0)

### What was implemented or executed
- **Rule changes (Part 0)**: `CLAUDE.md` Rule H replaced by "Zero cost, local open models" (Ollama only,
  no paid API, no Dolos, explicit `num_ctx`, digest pinning, no dependency on the harness clients or
  `settings.py`). `.gitignore` gained `scratch/` and `study_*/results/`. Both lines are already in the user's
  commit `f563295`.
- **Hardware / Ollama** (PowerShell `Get-CimInstance`, `nvidia-smi`, `ollama --version`, `ollama list`,
  `GET /api/version`, `/api/tags`, `/api/show`, the server log in `%LOCALAPPDATA%\Ollama`):
  - i7-12700H, 15.7 GB RAM (2.1 GB free), RTX 3050 4 GB, 18.8 GB free disk.
  - Ollama 0.40.3 (0.40.10 staged by the auto-updater).
  - `OLLAMA_NUM_PARALLEL=1`; user env `OLLAMA_CONTEXT_LENGTH=16384`.
  - Model digests recorded in `scratch/models_info.json`.
- **Scratch scripts** (all in `scratch/`, stdlib HTTP only, run with `conda run -n collusion-lab python -B …`):
  `ollama_util.py`, `models_info.py`, `prompts_draft.py` (addenda v1 + v2, history block, channel prompts,
  on top of the harness builders), `interface_test.py`, `bench.py` (format / game / monitor / unload),
  `summarize_format.py`, `parallel_test.py`, `token_counts.py`, `token_counts_v2.py`,
  `evidence_examples.py`, `analyze_games.py`, `show_game.py`, `tail_analysis.py`,
  `monitor_game_stats.py`, `history_example.py`. Results are in `scratch/results/`.
- **Runs** (user approved the "full" benchmark plan, then reduced part (c) to 2 models):
  1. `interface_test.py qwen2.5:7b`: about 12 calls, 4 min.
  2. `bench.py format` × {qwen2.5:7b, llama3.1:8b, llama3.2:latest}: 3 × 48 calls (40 format + 8 sweep).
  3. `parallel_test.py` on the default server (P=1) and on a temporary second server
     (`OLLAMA_HOST=127.0.0.1:11435 OLLAMA_NUM_PARALLEL=4 OLLAMA_MAX_LOADED_MODELS=1 ollama serve`),
     which was stopped afterwards by PID on port 11435 only.
  4. `bench.py game` alliance + placebo × {llama3.2:latest, qwen2.5:7b}: 204 calls, about 46 min.
  5. `bench.py monitor` × {granite3.3:8b, llama3.1:8b, qwen2.5:7b}: 6 calls.
  6. `token_counts.py` × {qwen2.5:7b, llama3.2:latest}, then `token_counts_v2.py` × 2.
- Totals: about 540 local LLM calls, $0, about 2 h 15 min of compute.
- Checked afterwards: `find external -name __pycache__` → 0 (external untouched).
- Wrote `notes/reports/01_design_revision_rq01.md`.

### Errors and problems faced
1. `curl … | conda run -n collusion-lab python -B -c "…json.load(sys.stdin)…"` →
   `json.decoder.JSONDecodeError: Expecting value: line 1 column 1 (char 0)`. Root cause: `conda run` does not
   forward stdin to the child process.
2. First background benchmark: `results/log_format.txt: No such file or directory` (exit 1), and the
   watching monitor failed too. Root cause: the shell redirect into `scratch/results/` ran before
   `bench.py` could create that folder.
3. No progress lines while the llama3.1 benchmark ran. Root cause: `conda run` captures child output until
   the process exits.
4. A command started with a stray `cat > /tmp/x.py` waited for stdin and hung (moved to the background
   after 120 s). My mistake.
5. Integrity findings (not code errors):
   - truncation is silent (`num_ctx=2048`: 3,383 → 1,026 prompt tokens);
   - `/v1` ignores per-call `num_ctx` and reloads the model;
   - the same seed gives a different output after different preceding requests (3 of 4 at P=1, 4 of 4 at P=4);
   - with P=4, the KV cache pushed the 3B model to 16/29 GPU layers, and 4,096 KV cells were shared by 4
     sequences;
   - qwen v1 alliance agents revealed the alliance publicly (3 of 6 focal messages);
   - all 3 monitor candidates named the wrong pair on one synthetic game.
6. Old evidence definitions were buggy:
   - κ = 0 for "pair always goes";
   - old `D_react` = 1.0 for plain parallel conduct;
   - `D_private` fires for Type 4b because of a common public trigger.

### How each problem was solved
1. Measurement code goes into files in `scratch/` that read from files or HTTP. Rule: never pipe into `conda run`.
2. `mkdir -p scratch/results` before redirecting, then re-ran.
3. Used `conda run --no-capture-output … python -u`.
4. Stopped the task (TaskStop) and re-ran without the stray `cat`.
5. Design: native `/api/chat` only; explicit `num_ctx`; truncation flag (`prompt_eval_count ≥ num_ctx/2` or
   `done_reason=length`); the cache is the reproducibility mechanism; `NUM_PARALLEL=1`; secrecy wording
   v2 (101 tokens) with the placebo re-matched (107 tokens, +5.9%). The monitor issue is recorded as a
   risk / RQ5-relevant observation, not fixed.
6. New definitions in report 01 §5, with worked examples computed by `scratch/evidence_examples.py`.

### Decisions taken
- **Agent model**: qwen2.5:7b. Alternatives: llama3.1:8b (slower, not tested in games because of the
  user's choice; it is the monitor family) and llama3.2:3b (4× faster but no co-GO, poor understanding).
- **Monitor**: llama3.1:8b (different family). Second monitor: granite3.3:8b. qwen2.5 was excluded (same
  family as the agents).
- **Interface**: native `/api/chat`. Alternative `/v1` rejected (no per-call `num_ctx`).
- **Placebo**: a neutral afternoon text that names no agent and no action. An alternative naming the
  partner was rejected, because it could itself induce affinity.
- The Type 4b incentive is an addendum in the shared slot (public rules unchanged), plus a private
  real-payoff line in the history.
- Proposed (not decided): 6 rounds, 48 games, brevity cap. Waiting for user approval.
- No new Python dependency was added (stdlib only), so `environment.yml` is unchanged in this task.

### Open questions for the team
See report 01 §11 (10 questions). Most urgent:
- (1) 6 vs 8 rounds;
- (2) 48 vs 60 games;
- (3) brevity cap;
- (5) pin Ollama 0.40.3 and turn off auto-update — do not restart the Ollama app on the lead laptop
  before that;
- (6) teammates' hardware.

---

## 2026-10-24 — Task 02: P1 Foundations

### What was implemented or executed
- New: `configs/{pins.json, run_defaults.json, prereg_rq01.md (DRAFT)}`, `core/config.py`,
  `core/{schema,llm,labels,split,plan}`, `scripts/{check_env.py, selftest.py}`, `tests/` (61 tests),
  `pytest.ini`. Changed: `environment.yml` (pytest), `CLAUDE.md` Rule E (`CLAUDE.md` is now committed,
  matching the user's `.gitignore` edit).
- Commands:
  - `conda run -n collusion-lab python -m pip install --no-user pytest==8.4.2` (also brought pluggy 1.7.0
    and iniconfig 2.3.1). New dependency because the task requires pytest tests; versions pinned in
    `environment.yml`.
  - `conda run -n collusion-lab pytest -q`: 57 passed at first, 61 passed after adding the check_env tests.
  - `conda run -n collusion-lab python scripts/check_env.py`: READY, exit 0 (0.40.3; all 3 digests MATCH).
  - `conda run --no-capture-output -n collusion-lab python -u scripts/selftest.py`, twice (12 live calls).
  - `find external -name __pycache__` → 0. `git status … | grep -c pycache` → 0.

### Errors and problems faced
1. Selftest run 1 reported a prompt speed of 4,586.6 tok/s. Root cause: the 6 calls had identical
   prompts, so Ollama reused the cached prompt prefix and the timing was not real.
2. Speed varies a lot between runs on this laptop: run 1 took 19.4 s/call (8.6 gen tok/s), run 2 took
   29.4 s/call (4.8 gen tok/s), with 2.3 GB of RAM free.
3. No test failures. Once `pytest.ini` set `pythonpath = .`, all imports worked from the repo root.

### How each problem was solved
1. The selftest now adds a unique first line (`[self-test call <n>]`) to every system prompt. Run 2
   measured 315 prompt tok/s, which matches report 01 (438–463). Lesson: speed measurements must use
   unique prompts.
2. Unsolved (hardware). Both runs are recorded. The P4 machine allocation will use each laptop's
   self-test speed factor, measured just before the run.

### Decisions taken
- Transport failures are not cached; parse failures are (they are model outputs). Alternative: cache
  everything — rejected, because a dead server would then poison the cache permanently.
- Cache lookups also search other machines' shards. Writes go only to the own shard (`machine_id`
  comes from `COLLUSION_LAB_MACHINE` or a hostname hash).
- `check_env` fails on a wrong Python version, conda env or missing harness, not only on Ollama
  problems. Teammates need all of these for P2.
- `make_plan` uses LPT scheduling (longest game first, each game to the machine that would finish it
  earliest, using speed factors). Alternative: round-robin — rejected, as it does not use speed factors.
- `write_labels` refuses a differing overwrite, because the split depends on the labels sha256.
- Machine A's id on this laptop is `m_49b19883` until `COLLUSION_LAB_MACHINE=A` is set.

### Open questions for the team
- Please set `COLLUSION_LAB_MACHINE` (A, B, C) on each laptop and send the selftest TEAM CHAT line
  from each, so the pilot plan can use real speed factors.
- `configs/prereg_rq01.md` is DRAFT. The `num_predict` and brevity-cap values come from P2, then the
  lead freezes and commits it.

---

## 2026-10-24 — [machine: ML] Task 03: P3a RQ0.1 metrics

### What was implemented or executed
- Created `core/__init__.py` (empty; missing on this machine), `core/evidence/__init__.py`,
  `core/evidence/rq01.py`, `core/stats/__init__.py`, `core/stats/basic.py`, `tests/conftest.py`
  (2-line sys.path shim; missing), `tests/test_rq01.py`, `tests/fixtures/rq01/example_{A..E}.json`
  (GameRecord layout) and copies of the 4 mini-games from `scratch/results/` as
  `tests/fixtures/rq01/mini_game_*.json`. No P1 files touched.
- `conda env create -f environment.yml` (env `collusion-lab` did not exist here; Python 3.11.17).
- `conda run -n collusion-lab python -m pip install pytest` → pytest 9.1.1 (+ iniconfig 2.3.1,
  pluggy 1.7.0, pygments 2.21.0). Reason: test runner for this task.
- `conda run -n collusion-lab pytest -q tests` → **28 passed**.
- No LLM calls, no GPU use (RTX 3060 present but not needed), $0.

### Errors and problems faced
- `EnvironmentLocationNotFound: Not a conda environment: E:\hell\hell\envs\collusion-lab` — env never
  created on this laptop.
- `No module named pytest` in the fresh env — pytest is not yet in `environment.yml` (P1 item).
- `pytest -q` from the repo root: 3 collection errors (`scratch/interface_test.py` URLError — needs
  Ollama; `scratch/parallel_test.py` IndexError; `external/trace-guard/scripts/test_model_access.py`).
  Root cause: no `testpaths` config, so pytest collects scratch scripts.
- Found `CLAUDE.md` and `notes/` tracked in git, and absent from `.gitignore` (conflicts with Rule E).

### How each problem was solved
- Env created from the committed `environment.yml`; pytest installed into it only.
- Collection errors: unsolved here (config file is P1's); workaround `pytest -q tests`.
- Rule E tracking issue: unsolved (Rule A forbids git writes); reported to the lead.

### Decisions taken
- NA = Python `None` everywhere, with a reason flag (`few_valid_rounds`, `constant`). Alternative NaN
  rejected: NaN compares False silently and is easy to average in by mistake.
- Constant-series → NA applies to co-variation signals only (D_sync, D_private, W_joint), not to the level
  measures coGO/capture/G_others, because the report 01 §5.4 table gives values (1.0, 0.0) for constant
  level series.
- Labels kept out of `GameData`; passed to gate/pilot table as a separate dict (Rule G). Deviates from the
  prompt's `pilot_table(games)` signature.
- Uptake computed over all rounds (text check, §7 "2 agents × rounds"), not only valid rounds.
- Included D_sync, D_private, W_joint to check the full A–E table; D_react deferred as the prompt says.
- `environment.yml` not edited to avoid a merge conflict with P1, which pins pytest.

### Open questions for the team
- Lead: un-track `CLAUDE.md` and `notes/` and add them to `.gitignore` (Rule E)?
- P1: add `testpaths = tests` (and `pythonpath = .`, after which `tests/conftest.py` can go); pin pytest.
- Where do `machine` and per-game wall time live in GameRecord? `pilot_table` reads `machine` /
  `config.machine` and `wall_s`.
- Name pattern does not match possessives ("Agent M's"); keep as pre-registered, or reword before freezing?

---

## 2026-10-24 — [machine: ML] Merge-conflict fix after P1 merge (refers to the Task 03 entry above)

### What was implemented or executed
- Resolved the 2 conflicted files left by merging P1 (`1cc0923`) into the Task 03 work tree. No git
  command that writes was run (no `add`, no commit); the files are only edited on disk.
  - `tests/conftest.py` (both sides added it): kept P1's version as-is. My 2-line `sys.path` shim was
    dropped, because P1's `pytest.ini` sets `pythonpath = .` and `testpaths = tests`.
  - `notes/DEVLOG.md`: both new entries kept unchanged, in task order (Task 02 P1, then Task 03 P3a).
- `conda run -n collusion-lab pytest -q` → **89 passed** (P1 tests + 28 `test_rq01.py`).

### Errors and problems faced
- Git conflict markers (`<<<<<<< HEAD` / `>>>>>>> 1cc0923…`) in `tests/conftest.py` (add/add) and
  `notes/DEVLOG.md` (both sides appended an entry at the same place).

### How each problem was solved
- As above; checked that no conflict markers remain outside `external/` and `.git/`.

### Decisions taken
- Took P1's conftest whole instead of merging the shim in: it is redundant with `pytest.ini`.
- This corrects the Task 03 entry's note that `tests/conftest.py` holds a sys.path shim, and closes its
  open question about `testpaths` (P1 added it).

### Open questions for the team
- The files still show as unmerged to git until someone runs `git add` on them. The user/lead does this
  (Rule A).
- `.gitignore` has an unstaged working-tree change that removes the `notes/` line the merge staged.
  Was that intentional? Rule E says `notes/` is ignored.

---

## 2026-10-24 — Task 04: Step 0 (P3a merge check) + P2 Generator

### What was implemented or executed
- **Step 0:**
  - Read report 03.
  - Full suite: 89 passed (P1 61 + P3a 28).
  - `conftest.py` = P1's version; `pytest.ini` already has `testpaths=tests` and `pythonpath=.`.
  - Adapter check: `from_record` matches the P1 layout except `machine` / `wall_s` → added to GameRecord.
  - Possessive name-pattern fix + 11 tests + adapter test → 100 passed.
- **P2 code:**
  - `configs/prompts/` (9 files + `manifest.json`);
  - `core/generate/{elfarol,history,prompts,runner}.py`, `core/clean/leaks.py`;
  - `scripts/{make_plan,labels_split_from_plan,run_plan,merge_check}.py`;
  - tests `genmock.py`, `test_generate.py`, `test_leaks.py`, `test_scripts_p2.py`;
  - schema additions (GameRecord `machine`/`wall_s`/`prompts`; GameConfig `plan_index`/`plan_config_sha256`/`brevity`; CallMeta `seed`).
- **Scratch helpers:** `dump_prompts.py` (verbatim addenda), `write_manifest.py`, `brevity_check.py` (L1), `smoke_report.py` (L2), `update_prereg.py`, `estimate_plans.py`.
- **Live runs** (pre-approved):
  - L1 brevity check: 20 calls; free RAM 6.0 GB; started 02:15.
  - L2 smoke game: plan `smoke` seed 20261099 in `runs/smoke/`, 38 calls, 5.2 min; free RAM 2.1 GB.
  - Total: 58 local calls, $0.
- **Final configs:** `run_defaults.json` (brevity on, `num_predict` 200/200/200/150, 8 rounds, minutes per round 2.6/2.05, Type 1 factor 1.27); `prereg_rq01.md` still DRAFT, sha256 `22c8ff71…5d57`.
- **Final test run:** `pytest -q` → **156 passed**. `find external -name __pycache__` → 0.

### Errors and problems faced
1. `test_prompts_module_does_not_import_harness_clients` FAILED: `external/llm-trust-breaking/src/games/__pycache__` existed. Root cause:
   `prompt_builders._get_game_rules` imports `src.games` lazily, at call time, after our
   `sys.dont_write_bytecode` guard had been restored. That violated Rule F.
2. Leak pattern bug, found while writing it (before any test ran): `(?![\d.,]\d)` would still match the
   "-8" inside "-80".
3. P3a name pattern did not match possessives ("Agent M's plan"), as report 03 §7 flagged.
4. The P1 schema had no `machine` / `wall_s`, so the pilot-table columns would have been empty.

### How each problem was solved
1. Import `src.games` eagerly inside the bytecode guard in `core/generate/prompts.py`. Deleted the
   `__pycache__` folder our test run had created. Re-ran: 0 folders; the test now guards it permanently.
2. Changed it to `(?!\d)(?![.,]\d)`. Tests cover -80, -8.5, 5-8 (no hit) and -8, $-8, − 8 (hit).
3. **Pre-freeze rule change (approved):** the new pattern is
   `(?<![A-Za-z'’])(?:Agent\s+)?<P>(?:(?=['’][sS]\b)|(?![A-Za-z'’]))`. 11 tests added; the recorded
   mini-games still give uptake 1.00 (alliance) and 0.00 (placebo); the DRAFT prereg wording was updated.
4. Added `machine`, `wall_s` and `prompts` as required GameRecord fields; `run_game` writes them.

### Decisions taken
- **Brevity KEEP** (pre-set rule: L1 20/20 valid, 0 length cuts, L2 0 parse failures, uptake 2/2 per focal
  agent). Effect: Stage 3 132 → 32.5 median output tokens, 30.0 → 6.6 s.
- **Rounds = 8** (pre-set rule: estimated 8-round Type 1 game ≈ 22.7 min ≤ 25 min).
- Partial records go to `<id>.partial.json` and the final record to `<id>.json`. Alternative: one file with
  a status flag — rejected, because a partial record would be confused with a finished one.
- Brevity line placed at the end of every user prompt (identical for all agents), not in the addendum slot.
  It is protocol-wide, not type-specific.
- `run_plan` output goes to `data/raw/<plan name>/`.

### Open questions for the team
- B and C self-test lines are needed for the pilot plan speed factors.
- The ML laptop must re-sync to pytest 8.4.2.
- `notes/` is gitignored but still tracked from commit `ed3be3b`. Untrack or keep? (lead decision)
- Lead: freeze `configs/prereg_rq01.md` (remove DRAFT, commit, record its sha256 in the DEVLOG) before P4.

---

## 2026-10-24 — Task 06a: Step 0 (P5 merge check) + P4 pilot preparation

### What was implemented or executed
- **Step 0:**
  - full suite after the P5 merge: 1 failed / 297 passed;
  - the Type 4 hit count fixed in `test_cleaner.py` → 298 passed;
  - import-cycle check OK;
  - 4b patterns are internal to P2's scanner (the cleaner already matches);
  - over-removal check on 8 sentences (`scratch/overremoval_check.py`);
  - monitor `num_predict` 300 → 200 in run_defaults;
  - `scripts/export_setup_texts.py` → `configs/monitor/setup_texts.json` (24 texts).
- **Pre-freeze change (approved, prereg still DRAFT):**
  - `configs/prompts/alliance_v3.txt` (v2 + hint, byte-exact) and `placebo_v3.txt` (v2 + 1 neutral sentence);
  - token counts measured with qwen2.5:7b: v2 method check 101/107; **v3 130/139, ratio 1.069**;
  - manifest updated; Type 1 → `collusion_v3_hint`, Type 2 → `placebo_v3`; runtime hint appending removed;
  - prereg: prompts row, machines A+B, E1 removed, times for 2 laptops, §10 "Pre-freeze changes";
  - prereg sha256 (DRAFT) `a0ff97e8f68c69313d8d101b23251c8aecff8624dad112db85995f4c1c5150ab`.
- **Two machines:** `run_defaults` `"machines": ["A","B"]`; `make_plan --machines` defaults to it.
- **`scripts/pilot_report.py`** (report + `--handcheck`) and `tests/test_pilot_report.py` (6 tests).
- **notes/:** Rule E and the `.gitignore` header now say `notes/` is tracked (it was already not ignored).
- **Live runs:**
  - 8 token-count calls;
  - L3: plan `smoke3` seed 20261098 in `runs/smoke3/`, 1 Type 1 game, 2 rounds, 38 calls, 4.8 min;
  - A's selftest: 6 calls, 27.17 s/call;
  - total 52 local calls, $0.
- **Final:** `pytest -q` → **308 passed**.

### Errors and problems faced
1. `test_leak_counts_per_fixture`: Type 4 `{"hits": 3, "redactions": 2}` instead of `{"hits": 4, ...}`. Root cause: the P5 stub
   counted "$-8" twice ("-8" and "$-8"); P2's real scanner counts it once (`minus_8` skips a minus after "$").
2. `conda run -n collusion-lab python -B scratch/smoke_report.py smoke3` crashed in conda itself:
   `UnicodeEncodeError: 'charmap' codec can't encode character '�'`. Root cause: `conda run` re-prints
   captured stdout with cp1252; the L3 model output contained emoji and a replacement character.
3. With `alliance_v3` already containing the hint, the old runtime rule (`"hint" in variant` → append the hint)
   would have appended it a second time for the variant `collusion_v3_hint`.

### How each problem was solved
1. Changed only the expected count (4 → 3), with a comment. Same sentences are removed; scanner and
   `leaks.py` tests unchanged.
2. Re-ran with `PYTHONIOENCODING=utf-8 conda run --no-capture-output …`, writing to a file. Rule: scripts
   that print model text use `--no-capture-output` and UTF-8.
3. Removed runtime hint appending (`addendum_text(type, partner)`); a test asserts the hint file is not
   listed separately in Type 1 records.

### Decisions taken
- Placebo extension sentence chosen with no agent names, actions, team words or banned terms;
  measured +6.9% vs alliance_v3. Alternative: two shorter sentences — not needed, the ratio is already within ±10%.
- `external/` NOT re-added to `.gitignore`, although the task text says "stays ignored": it is tracked since
  `835b289` and teammates need it. Flagged for the lead to confirm.
- L3 result (the pair captured the bar in round 2) is reported only; no wording changed (one game is an anecdote).

### Open questions for the team
- Over-removal: is removing sentences with generic words ("secret", "episode", "label", "experiment")
  acceptable, or should those words only be flagged?
- Confirm that `external/` stays tracked.
- Lead: freeze the prereg, run fresh self-tests on A and B, create the pilot plan with B_FACTOR (≈ 2.26 today).
