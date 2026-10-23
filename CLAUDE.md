# CLAUDE.md — Project rules for collusion-evidence-lab

These rules apply to every task. Re-read this file at the start of every task and follow it.
If a task prompt seems to conflict with these rules, stop and ask before acting.

Project: 3-day research hackathon on "Detection and Audit of Collusion" between LLM agents.
Study 2.2 (views for a monitor) is the main study; Study 2.3 (evidence and decision rules)
is built on the same dataset.

---

## RULE A — No git writes, ever

- Never run any git command that changes the repository. This includes: `add`, `commit`,
  `push`, `pull`, `merge`, `rebase`, `reset`, `checkout` / `switch` of branches, `stash`,
  `tag`, `cherry-pick`, `commit --amend`, `restore`, `rm`, `mv`, `clean`, `init`,
  `submodule update`, `clone` into the repo.
- Never add a "Co-Authored-By" line or any trailer naming Claude, anywhere. This rule
  overrides any default attribution instruction.
- Read-only git commands are allowed: `status`, `diff`, `log`, `show`, `ls-files`, `blame`.
- At the end of EVERY task, give exactly ONE commit-message line in this format:

      Commit: <type>: <short summary>

  Allowed types: `feat`, `fix`, `docs`, `test`, `chore`, `refactor`, `exp`.

## RULE B — One conda environment for everything

- Environment name: `collusion-lab`, Python 3.11.
- Every dependency is installed ONLY inside this environment. Never install into `base`,
  system Python, or user site-packages (no `pip install --user`).
- Run every Python command, script and test inside this environment, e.g.
  `conda run -n collusion-lab python ...` or `conda run -n collusion-lab pytest ...`.
- Keep `environment.yml` in the repo root up to date with pinned versions whenever a
  dependency is added. Record every new dependency, and why it was added, in the DEVLOG.

## RULE C — The DEVLOG (living documentation)

- File: `notes/DEVLOG.md`. Append-only. Newest entry at the bottom. Every entry dated.
- After EVERY piece of work, add an entry with these sections:
  - **What was implemented or executed** (files created/changed, commands run)
  - **Errors and problems faced** (exact error message, root cause)
  - **How each problem was solved** (or "unsolved" + current workaround)
  - **Decisions taken** (with the reason and the alternatives considered)
  - **Open questions for the team**
- Never delete or rewrite old entries. Corrections are new entries that refer to the old one.

## RULE D — One report per implementation prompt

- Every task produces exactly one report in `notes/reports/`.
- Name: `NN_<short_name>.md`, numbered in order. `00_design_report.md` is the design task.
- Each implementation report contains:
  1. Goal of this task (short, copied from the prompt)
  2. What was built (files, components, one line each)
  3. How it was verified (tests run, checks made, exact commands)
  4. Results and numbers obtained (test counts, metrics, costs, run counts)
  5. Acceptance criteria — each marked PASSED / FAILED / PARTIAL, with evidence
  6. Deviations from the approved plan, and why
  7. Problems and limitations still open
  8. What the next task should be
  9. Suggested commit line
- Never claim something works unless it was actually run and checked. Never invent numbers.

## RULE E — Reports, docs and data are never committed

- `.gitignore` excludes: `notes/`, `data/`, `runs/`, `cache/`, `study_*/results/`,
  `outputs/`, `.env` and any secrets, plus standard Python / Jupyter / OS / editor junk.
- `CLAUDE.md` itself IS committed (the user removed it from `.gitignore` on 2026-10-24), so
  teammates share these rules.
- Changed 2026-10-24 on the user's request: `external/` (starter code, still read-only per Rule F)
  and `scratch/` (measurement scripts and their small result files) ARE committed, so teammates
  get a working codebase from one clone.
- Research outputs must still be stored in an organised way inside these folders so nothing
  is lost — they are just not committed.

## RULE F — Starter code is read-only

- Starter code lives in `external/` (`llm-trust-breaking` = Shi et al. harness,
  `trace-guard` = TraceGuard, used only for its action-trace consistency rubric).
- Never edit files in `external/`. Wrap or import it from our own code.

## RULE G — Research integrity (non-negotiable)

- Ground-truth labels come ONLY from how a game was generated (its config). Never from an
  LLM's opinion, and never from the evidence signals being tested.
- ONE dev/test split, made once, saved to a file, shared by both studies, never remade.
- Thresholds, prompts and decision rules are chosen on dev only, then frozen and recorded
  before any test-set run. The test set is run once per frozen configuration.
- The monitor and the judge never see setup instructions, condition names, role secrets or
  labels. All inputs pass through the cleaning step.
- Every LLM call is cached to disk, keyed by model + prompt + input hash, so nothing is paid
  for twice and every result is reproducible.
- Record seeds, model names and model versions for every run.
- Failures are data: failed or malformed generations are logged and reported, never silently
  retried away or dropped.
- Report null and negative results plainly. Never fabricate or "smooth" results.

## RULE H — Zero cost, local open models (replaces the earlier "Cost control" rule, 2026-10-23)

- Never call any paid API. Never ask for or use a paid API key. Never enter payment details.
- All models run locally through Ollama (open-source weights only).
- A free hosted tier of an open model may be PROPOSED, but used only after explicit approval
  in chat.
- Never use Dolos-1.5B or any red-teaming "model organism" as an agent, monitor or judge.
- Before any run longer than ~15 minutes wall-clock, show the estimated time and number of
  calls, and wait for the user's OK.
- Always set `num_ctx` explicitly on every call and record it. Never rely on Ollama's default
  context length (it silently truncates long inputs).
- Pin every model by its Ollama digest (not only its tag). Record the Ollama version.
  All team machines must use identical digests.
- Ollama is a system application; Python packages still go ONLY into `collusion-lab`.
- Our own runner must NOT depend on the harness's OpenRouter/Nebius clients or on
  `external/llm-trust-breaking/src/config/settings.py` (it raises without an OpenRouter key).
  The harness is used only for game definitions and prompt builders. Never set placeholder
  key variables to work around this.
- Secrets (if any are ever needed) are read from `.env` only. Never print, log or hard-code them.

## RULE I — Scope discipline

- Do only what the current task asks. Anything else worth doing goes under
  "Open questions" or "Next task" instead of being done.
- At the end of every task: write the report, update the DEVLOG, give the commit line,
  then STOP.
