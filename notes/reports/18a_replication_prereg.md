# 18a — Replication pre-registration (Study 2.2 and 2.3) and plan

Date: 2026-10-25 · Task 18a · Machine B · **No model calls.** No existing frozen file, prompt, plan, labels, split, output or earlier number was changed.

## 1. Goal (from the prompt)

- Apply two robustness-label changes in `writeup/results_22.md`.
- Pre-register a replication of Study 2.2 and 2.3 on 48 new games.
- Create its plan, check that its game ids don't overlap with any earlier plan, and print the generation commands with time estimates. Then STOP.

## 2. What was built

| File | One line |
|---|---|
| `configs/prereg_replication.md` (new) | Purpose; data (Amendment 2 §5 exactly, seed 20261027, separate labels file, no split, quality rule with/without); Study 2.2 R1–R10; Study 2.3 E1–E4; order of work; outcome-neutral statement; limitations. LF sha256 `5f08ab68d571efae1e77281fd5753528ddf43f066b5619713d15a30ad6e0c0a6`. |
| `configs/plans/replication.json` (new, via `make_plan`) | 48 games, A 16 / B 32. LF sha256 `d15ffe5ea15d2af851722ddbb0ee70fa10d98c3528caff953bde92f8436d451f`. |
| `writeup/results_22.md` | Only the two labels: "CONSISTENT NULL (no detectable gain at n = 24)" and "CONSISTENT (exploratory; pooled includes test)". README does not repeat them, so it is unchanged. |
| `notes/DEVLOG.md` | Merge-conflict markers from commit e65e46f removed (3 lines; both sides kept). The Task 17 entry was re-appended, plus a repair entry and the Task 18a entry. |

## 3. How it was verified

```
conda run -n collusion-lab python scripts/make_plan.py --name replication --seed 20261027 --counts 1=24 2=8 3=8 4=8 --machines A B --rounds 8 --speed A=1.0 B=2.0
#   -> wrote configs/plans/replication.json (48 games); estimated wall minutes per machine (plan units) A 297.84, B 297.84
# same command again -> "REFUSED: ... already exists; plans are created once" (exit 1)
conda run -n collusion-lab python -B <scratchpad>/p18_check.py   # ids unique; overlap 0 with dataset/pilot/pilot2/repilot_secrecy plans and data/labels.csv
conda run -n collusion-lab python -B <scratchpad>/p18_hash.py    # LF sha256 of every frozen/config file cited in the prereg
git diff -- notes/DEVLOG.md                                      # only the 3 marker lines (+ separator) changed before the appends
```

## 4. Results

**Plan checks:**
- Seed 20261027; 8 rounds; 48 unique ids.
- **0 overlaps** with `dataset.json` (48), `pilot.json` (8), `pilot2.json` (6), `repilot_secrecy.json` (2) and `data/labels.csv` (48).
- `data/raw/replication/` does not exist.
- **Variants:** collusion_v4_secrecy 24, placebo_v3 8, persona_v1 8, incentive_4b_v1 8.
- **Machine × type:** A: T1 8, T2 2, T3 3, T4b 3. B: T1 16, T2 6, T3 5, T4b 5. This is identical to the original dataset's assignment (report 12 §4.2).

**Generation commands (printed, NOT run):**

```
# machine A  (COLLUSION_LAB_MACHINE=A; Ollama 0.40.3, check_env READY first)
set PYTHONIOENCODING=utf-8
conda run --no-capture-output -n collusion-lab python -u scripts/run_plan.py --plan configs/plans/replication.json --machine A

# machine B  (COLLUSION_LAB_MACHINE=B)
set PYTHONIOENCODING=utf-8
conda run --no-capture-output -n collusion-lab python -u scripts/run_plan.py --plan configs/plans/replication.json --machine B
```

Records go to `data/raw/replication/` (the `run_plan` default for this plan name). Runs are resumable.

**Estimated wall time per machine:**
- **Plan units** (`make_plan`, speed A = 1.0, B = 2.0): A 298 min, B 298 min.
- **Measured basis** (the per-machine type mix is identical to the dataset run, report 12 §4.2): **A ≈ 412 min (6.9 h)**, **B ≈ 388 min (6.5 h)**. This is the better estimate. A ran at ≈ 0.49 × B's speed in the dataset run.
- **Later steps (estimates, for planning):**
  - Study 2.2 monitor on B: 384 calls ≈ 336 × 20.7 s + 48 × 31.3 s ≈ 141 min (report 13 §7 per-call times).
  - Study 2.3 judge on C: 48 calls ≈ 22 min at the 27.5 s median latency (report 13C §4.3).
- Every part is over 15 min, so each needs the lead's OK (Rule H) unless it is pre-approved.

## 5. Acceptance criteria

| Item | Status | Evidence |
|---|---|---|
| 0. Two label changes (README only if repeated) | **PASSED** | results_22 robustness rows; README has no such labels |
| 1. Prereg written before any replication game, all required sections and R1–R10 / E1–E4 decision rules | **PASSED** | `configs/prereg_replication.md` |
| 2. Plan created; refuses to overwrite; no id overlap | **PASSED** | §3, §4 |
| 3. run_plan commands and estimated times printed, not run | **PASSED** | §4 |
| No model calls; no existing frozen file / prompt / plan / labels / split / output changed | **PASSED** | `git status`: only the new prereg and plan, results_22 (labels) and DEVLOG |

## 6. Deviations and decisions (please confirm)

1. **E3 choices:** the task points to "dev choices recorded for task 17C", but no 17C record exists. The prereg fixes a **fallback now**, from the frozen dev report:
   - best single family = R2 (dev BA 0.958);
   - best combined rule = R6 (0.833, tie with R7's LOO 0.833 broken by the lower rule number).
   - It applies unless a 17C record is committed before the first replication game is generated.
   - Note that R1–R6 dev BAs are in-sample and R7's is leave-one-out, so the tie compares unlike numbers.
2. **Replication labels go to a separate file** `data/replication/labels.csv`. `labels_split_from_plan.py` must **not** be run on this plan, since it writes `data/labels.csv` / `data/split.json`.
3. **C-mismatch partners** are drawn within type across the 48 replication games, because there is no split.
4. **Outcome mapping:** each decision rule has a complete outcome map (e.g. R1 "confirmed (below chance)", R7 "not confirmed (reversed)", R10b "capture better / V4 better").
5. **Primary analysis = all 48 games;** a sensitivity analysis excludes quality-fail games.
6. **DEVLOG repair:** outside this task's strict scope but within `notes/`, and needed before appending. Commit e65e46f contained unresolved merge-conflict markers; only the 3 marker lines were removed.

## 7. Open problems

- **Additive code is needed before the replication can be processed:** a labels-only writer for `data/replication/labels.csv`, a one-group option for render_views' control pairing, analysis entry points for a set without a split (Study 2.2 and 2.3), and possibly a way for `rules.apply_frozen` to accept non-test game ids and a new judge file. Each will be a separate, tested task before any replication output is read.
- `notes/DEVLOG.md` needs the one-time LF renormalisation commit (lead).

## 8. Next task

- **Lead:** commit the prereg (alone), then the plan.
- **Then:** the labels-only writer task, then generation on A and B with the printed commands.

## 9. Files to commit (in this order)

1. **Alone:** `configs/prereg_replication.md`
2. **Then:** `configs/plans/replication.json`
3. **Then:** `writeup/results_22.md`, `notes/DEVLOG.md`, `notes/reports/18a_replication_prereg.md`

## 10. Commit lines

1. `Commit: docs: pre-register the Study 2.2 and 2.3 replication on 48 new games (seed 20261027)`
2. `Commit: exp: add the replication plan (48 games, machines A and B, seed 20261027)`
3. `Commit: docs: relabel two robustness rows, repair DEVLOG merge markers, add report 18a`
