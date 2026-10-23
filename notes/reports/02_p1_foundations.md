# 02 — P1 Foundations

Date: 2026-10-24 · Task 02 (first implementation task) · Time used: about 1.5 h of the 3 h time box.

## 1. Goal (from the prompt, short)

Build the lean foundations needed before the generator (P2):

- configs: pins, run defaults, RQ0.1 pre-registration draft;
- `core/schema`, `core/llm` (pinned, cached Ollama client plus a mock), `core/labels`, `core/split`, `core/plan`;
- `scripts/check_env.py` and `scripts/selftest.py`;
- pytest tests for every acceptance criterion.

Out of scope: the game runner, prompts, metrics, cleaner, views, monitor.

## 2. What was built

| File | One line |
|---|---|
| `configs/pins.json` | Ollama 0.40.3; per model: tag, digest, role, `num_ctx` 8192, required flag. granite3.3:8b is optional |
| `configs/run_defaults.json` | 6 rounds, temperatures, `num_predict` per stage (provisional), master seeds, counts, variants, measured minutes per round, LLM timeout and retry settings |
| `configs/prereg_rq01.md` | **DRAFT** RQ0.1 pre-registration: report 01 §7 with 6 rounds, pilot 4/2/1/1, criteria (a) / falsification / hand agreement / b1 / b2, decision tree, parse-failure policy |
| `core/config.py` | Repo paths, JSON loaders, `canonical_json`, `sha256_of`, `atomic_write_text` (temp file plus rename) |
| `core/schema/__init__.py` | Dataclasses `PlanEntry`, `GameConfig`, `CallMeta`, `Failure`, `GameRecord`, `Label`, `Split`, `LLMResult`, plus `validate_game(record) -> list[str]` |
| `core/llm/transport.py` | `OllamaTransport` (native `/api/chat`, `/api/version`, `/api/tags`, urllib), `TransportError(retryable)`, `MockTransport`, `ok_reply` |
| `core/llm/client.py` | `CachedLLM`: start-up pin check, required options, sha256 cache key, per-machine cache shards with atomic writes, retry policy, truncation flag. Plus `check_pins`, `cache_key`, `default_machine_id`, `gpu_name` |
| `core/labels/__init__.py` | `label_from_config` (only `episode_type` decides it), `write_labels` (refuses a differing overwrite), `read_labels`, `labels_sha256` |
| `core/split/__init__.py` | `make_split` (stratified by type, seeded, saves the labels sha256, refuses to overwrite), `load_split` |
| `core/plan/__init__.py` | `build_entries` / `make_plan` (ids, focal pairs, SeedSequence seeds, LPT machine balancing with speed factors, `config_sha256`, refuses to overwrite), `load_plan`, `machine_minutes` |
| `scripts/check_env.py` | Python, conda env, harness present, GPU, free RAM, Ollama version, each pinned digest MATCH / MISMATCH / MISSING. Exit 1 on any problem |
| `scripts/selftest.py` | 6 Stage-3-sized calls to qwen2.5:7b through `CachedLLM` with fresh `sample_idx`; prints medians and a one-line JSON for the team chat |
| `tests/` (5 files + `conftest.py`), `pytest.ini` | 61 tests, all using `MockTransport`. None calls the network |
| `environment.yml` | added `pytest==8.4.2`, `pluggy==1.7.0`, `iniconfig==2.3.1` |
| `CLAUDE.md` | Rule E text now matches your `.gitignore` change (`CLAUDE.md` is committed) |

No real plan files were generated. `configs/plans/` does not exist yet, as instructed.

## 3. How it was verified

All commands were run from the repo root:

```
conda run -n collusion-lab python -m pip install --no-user pytest==8.4.2
conda run -n collusion-lab pytest -q
conda run -n collusion-lab pytest --collect-only -q
conda run -n collusion-lab python scripts/check_env.py
conda run --no-capture-output -n collusion-lab python -u scripts/selftest.py      (run twice)
find external -name __pycache__ | wc -l                                            -> 0 (external untouched)
git status --porcelain --untracked-files=all | grep -c pycache                    -> 0
```

## 4. Results

**pytest** (final run):

```
.............................................................            [100%]
61 passed in 0.78s
```

Per file: `test_llm.py` 23, `test_schema.py` 14, `test_labels_split.py` 12, `test_plan.py` 8, `test_check_env.py` 4.

**check_env on this laptop** (live):

```
collusion-evidence-lab environment check
  Python                           3.11.17                                  MATCH
  Conda env                        collusion-lab                            MATCH
  Harness (external/)              present                                  OK
  GPU                              NVIDIA GeForce RTX 3050 4GB Laptop GPU
  RAM                              2.3 GB free of 16.8 GB
  Ollama version                   0.40.3                                   MATCH
  qwen2.5:7b [agent]               845dbda0ea48ed74...                      MATCH
  llama3.1:8b [monitor_judge]      46e0c10c039e0191...                      MATCH
  granite3.3:8b [second_monitor]   fd429f23b90980ed...                      MATCH
RESULT: READY
exit=0
```

granite3.3:8b is installed on this laptop, so it shows MATCH, not MISSING.

**selftest** (live, qwen2.5:7b, 6 calls, 753 prompt tokens each, `num_ctx` 8192, `num_predict` 350, temp 1.0):

| Run | Valid | Errors | Median s/call | Median gen tok/s | Median prompt tok/s | Median gen tokens | Note |
|---|---|---|---|---|---|---|---|
| 1 | 6/6 | 0 | 19.41 | 8.6 | **4,586.6 (not valid)** | 157 | the 6 prompts were identical, so Ollama reused the cached prompt prefix and prompt speed is inflated |
| 2 (final script) | 6/6 | 0 | **29.38** | **4.8** | **315.1** | 133 | a unique first line per call, so prompts are really processed |

Final team-chat line (run 2):

```
TEAM CHAT: {"machine_id": "m_49b19883", "gpu": "NVIDIA GeForce RTX 3050 4GB Laptop GPU", "ollama": "0.40.3", "model": "qwen2.5:7b", "calls": 6, "errors": 0, "valid": 6, "cache_hits": 0, "median_s_per_call": 29.38, "median_gen_tok_s": 4.8, "median_prompt_tok_s": 315.1, "median_prompt_tokens": 753.0, "median_gen_tokens": 133.0, "cold_load_s": 0.0}
```

Total live LLM calls in this task: 12. Cost: $0.

## 5. Acceptance criteria

| Criterion | Status | Evidence |
|---|---|---|
| `pytest -q` ≥ 20 passed, 0 failed | **PASSED** | 61 passed |
| Repeated identical call = cache hit with 0 mock transport calls | **PASSED** | `test_repeated_call_is_cache_hit_with_no_transport_call` (and the cross-machine shard reuse test) |
| A change in digest / num_ctx / num_predict / temperature / seed / sample_idx / format schema gives a miss (one test each) | **PASSED** | `test_changing_one_option_is_a_cache_miss` ×6 (parametrised) and `test_changing_digest_is_a_cache_miss` |
| Start-up refuses a wrong digest and a wrong version | **PASSED** | `test_startup_refuses_wrong_digest`, `test_startup_refuses_wrong_version` (also refuses a missing model) |
| `truncation_suspect` when prompt_eval_count ≥ num_ctx/2, and when done_reason == "length" | **PASSED** | `test_truncation_suspect_when_prompt_fills_half_the_context` (4096 of 8192), `test_truncation_suspect_when_output_hits_length_limit`; the negative case at 4095 is not flagged |
| Transport error retried at most 2× with every attempt logged; parse failure not retried | **PASSED** | `test_transport_error_retried_at_most_twice_and_logged` (3 attempts, sleeps 5 s and 20 s, not cached), `test_transient_transport_error_then_success`, `test_non_retryable_transport_error_is_not_retried`, `test_parse_failure_is_not_retried` (1 call) |
| `label_from_config`: no other field changes the label | **PASSED** | `test_other_fields_never_change_the_label` (10 mutations × 4 types), `test_label_depends_on_episode_type` |
| `make_split`: deterministic, stratified, disjoint, covering, refuses overwrite | **PASSED** | `test_split_deterministic_stratified_disjoint_covering`, `test_split_refuses_to_overwrite_and_loads` |
| `make_plan`: deterministic; unique ids; pilot and dataset ids disjoint; refuses overwrite; machines balanced within one game | **PASSED** | `test_plan_is_deterministic`, `test_game_ids_unique_and_well_formed`, `test_pilot_and_dataset_ids_are_disjoint` (seeds too), `test_plan_refuses_to_overwrite`, `test_machine_minutes_balanced_within_one_game` (dataset and pilot), `test_speed_factor_shifts_work_to_faster_machine` |
| `validate_game` returns [] for a valid fixture and catches ≥ 3 planted errors | **PASSED** | `test_valid_fixture_has_no_errors`; 11 planted errors caught in `test_planted_errors_are_caught` |
| Live: `check_env` prints 0.40.3 and MATCH for qwen2.5:7b and llama3.1:8b | **PASSED** | output in §4 (granite also MATCH); exit 0. Exit 1 on mismatch is tested in `test_check_env.py` |
| Live: selftest runs and its numbers are recorded | **PASSED** | §4 (2 runs) |
| `environment.yml` lists every new dependency, pinned | **PASSED** | pytest 8.4.2, pluggy 1.7.0, iniconfig 2.3.1 |
| `core/llm` does not import the harness | **PASSED** | `test_core_llm_does_not_import_the_harness` (scans the imports) |

## 6. Deviations from the approved plan

- **`core/config.py`** (new small module): shared hashing, atomic writes and config loading. Without it, the three packages that need them would each duplicate the code.
- **Transport failures are returned but not cached.** Successful responses, including those that fail to parse, are cached. Reason: a failure caused by a dead Ollama server is not model output, and caching it would block a later run forever. The game runner (P2) must log it as a `failures[]` entry.
- **The cache lookup also searches other machines' shards** (`cache/llm/*/<aa>/<key>.json`), so a merged cache is reused on the lead's machine. Writes always go to the own shard.
- **`machine_id`** = the env variable `COLLUSION_LAB_MACHINE` (for example `A`) if set, otherwise `m_` plus 8 hex digits of a hostname hash. The GPU name is stored per cache entry.
- **`check_env` also checks** the Python version, the conda env name and that the harness is present, and fails if any is wrong. Teammates need all three for P2. Its `main()` accepts a transport for testing.
- **`write_labels` refuses** to overwrite `labels.csv` with different content, because the split's sha256 depends on it.
- **selftest** writes to `cache/selftest/` (not `cache/llm/`) and adds a unique first line to every prompt (see §7).

## 7. Problems and limitations still open

- **Prompt-prefix caching in Ollama.** Identical prompt prefixes are reused across consecutive calls, so prompt-processing time drops and prompt tok/s is inflated (run 1: 4,587 tok/s). It does not change outputs in principle [A], but **any speed measurement must use unique prompts**. In real games each agent's prompt starts differently ("You are Agent X…"), so reuse is limited. Monitor calls share a long system prompt and will benefit (faster) [A].
- **Speed on this laptop is unstable**: 19.4 s/call in run 1 and 29.4 s/call in run 2. Generation speed was 8.6 vs 4.8 tok/s, with 2.3 GB of RAM free. Report 01's per-round minutes (4.6 / 5.2) fall within this range. The P4 machine allocation should use each laptop's own self-test speed factor, measured just before the run.
- `validate_game` checks structure and internal consistency. It does not yet check payoff arithmetic against the rules (that belongs with the P2 outcome function) or that call metadata exists in the cache (that is `merge_check`, P2).
- Not built, by design: game runner, prompts, history block, channel, `merge_check`, `run_plan` (all P2); metrics (P3a, on another laptop).
- `configs/prereg_rq01.md` is **DRAFT**. P2 must fill in the final `num_predict` and brevity-cap values before you freeze it.

## 8. What the next task should be

**P2 Generator** (report 01 §9):

- the El Farol runner on top of the harness builders, using `CachedLLM`;
- addenda v2, history block, private channel, private payoffs, failure logging with the `imputed` flag;
- `run_plan --machine X` and `merge_check`;
- the brevity check (20 calls);
- one live 2-round Type 1 smoke game.

Then generate the pilot plan with `make_plan("pilot", 20261024, {1: 4, 2: 2, 3: 1, 4: 1}, ["A", "B", "C"], 6, speed=…)` using the teammates' self-test speeds.

### How teammates run check_env and selftest (copy-paste)

```bash
# 1. once: create the environment (from the repo root)
conda env create -f environment.yml

# 2. make sure Ollama 0.40.3 is running and the models are pulled
ollama --version                      # must say 0.40.3
ollama pull qwen2.5:7b
ollama pull llama3.1:8b
# (granite3.3:8b only on the machine that runs the second monitor)

# 3. give this laptop its machine letter (A = lead, B, C) - Windows PowerShell:
#      setx COLLUSION_LAB_MACHINE B      (then open a new terminal)
#    macOS / Linux:  export COLLUSION_LAB_MACHINE=B

# 4. environment check - must end with "RESULT: READY" (exit code 0)
conda run -n collusion-lab python scripts/check_env.py

# 5. speed self-test (~3 min; close other heavy apps, laptop plugged in)
conda run --no-capture-output -n collusion-lab python -u scripts/selftest.py
#    -> paste the line starting with "TEAM CHAT:" into the team chat

# 6. optional: run the unit tests (no Ollama needed)
conda run -n collusion-lab pytest -q
```

If `check_env` prints `MISMATCH` for a model digest, do not run anything. Follow the setup sheet in report 01 §4.3, step 4 (copy the lead's model files).

## 9. Suggested commit line

`Commit: feat: add P1 foundations (pinned cached Ollama client, schema, labels, split, plan, env checks, tests)`
