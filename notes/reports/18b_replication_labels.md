# 18b — Replication labels file (before generation)

Date: 2026-10-25 · Task 18b · Machine B · **No model calls.** No replication game exists yet.

## 1. Goal (from the prompt)

- Add a labels-only writer: plan → labels CSV, never a split, refusing the protected paths and any overwrite.
- Test it, run it once for the replication plan, and verify the original labels/split are unchanged.
- Print the two generation commands (not run).

## 2. What was built

| File | One line |
|---|---|
| `scripts/labels_from_plan.py` (new) | Every plan entry → `core.labels.label_from_config` → `core.labels.write_labels` at `--out`. `--out` is required. Refuses `data/labels.csv` / `data/split.json` (resolved, case-insensitive on Windows) and any existing file. Never writes a split. |
| `tests/test_labels_from_plan.py` (new) | 9 tests on mock plans (`make_plan` in a temp folder); listed in §3. |
| `data/replication/labels.csv` (output, not committed) | 48 labels. |
| `notes/DEVLOG.md` | Part 0 entry: the prereg commit verified, and the three missing machine-B entries (Task 17, pull repair, Task 18a) re-appended verbatim from the backup. Plus this task's entry. |

## 3. How it was verified

```
conda run -n collusion-lab pytest -q tests/test_labels_from_plan.py    # 9 passed
conda run -n collusion-lab pytest -q                                   # 549 passed, 0 failed
sha256sum data/labels.csv data/split.json                              # before
conda run -n collusion-lab python scripts/labels_from_plan.py --plan configs/plans/replication.json --out data/replication/labels.csv
sha256sum data/labels.csv data/split.json                              # after (identical)
# again, same --out -> "REFUSED: ... already exists; refusing to overwrite"
# --out data/labels.csv -> "REFUSED: data\labels.csv is a protected path ..."
```

**The 9 tests:**
1. Labels equal `label_from_config` (also when read back).
2. collusion = (type == 1).
3. Counts per type are right.
4. The output is byte-identical to `core.labels.labels_csv_text`, with LF endings.
5. Refuses `data/labels.csv` and `data/split.json`, via the function and the CLI, and leaves them untouched.
6. Refuses a protected path given relatively, and in another case (Windows).
7. Refuses overwrite, even with identical content.
8. Refuses to run without `--out`.
9. Never writes a split.

## 4. Results

- **Prereg precondition:** `configs/prereg_replication.md` was committed alone in `2bc3d3a`; working copy = blob; LF sha256 `d9d25b583b1d6052778f8668d8a55d7680069ba1ce6e9f8b61a72c49e1f7a1f9`. Recorded in the DEVLOG before the run.
- **`data/replication/labels.csv`:**
  - 48 labels: **Type 1: 24, Type 2: 8, Type 3: 8, Type 4b: 8**.
  - sha256 **`27a0d4bfcfd5831b0e100482276d5ab36f663bd010ef0a84ada5194771742114`** (same as the `labels_sha256` of the label list).
- **Protected files unchanged** (sha256 before = after):
  - `data/labels.csv` `208491526cabc8a8e8078794cb14548e5b17cf15d1c37f0b4acadf2c64f1146e`
  - `data/split.json` `22503c45c653b85471a2513a1bdc943dd6e8db0895840aa895daccce684b60fa`

**Generation commands** (exactly as in report 18a; printed, NOT run):

```
# machine A  (COLLUSION_LAB_MACHINE=A; Ollama 0.40.3, check_env READY first)
set PYTHONIOENCODING=utf-8
conda run --no-capture-output -n collusion-lab python -u scripts/run_plan.py --plan configs/plans/replication.json --machine A

# machine B  (COLLUSION_LAB_MACHINE=B)
set PYTHONIOENCODING=utf-8
conda run --no-capture-output -n collusion-lab python -u scripts/run_plan.py --plan configs/plans/replication.json --machine B
```

Estimated wall time (report 18a §4): **A ≈ 412 min, B ≈ 388 min**. Both are over 15 min, so they need the lead's OK (Rule H).

## 5. Acceptance criteria

| Item | Status | Evidence |
|---|---|---|
| Prereg committed and unchanged; commit + sha256 in the DEVLOG first | **PASSED** | §4; DEVLOG "Task 18b (part 0)" |
| Script: label_from_config, same format, `--out` required, refuses protected paths / overwrite, no split | **PASSED** | §2, §3 |
| Tests (mock plans) | **PASSED** | 9 passed; suite 549 passed |
| Ran once; counts 24/8/8/8; file sha256 | **PASSED** | §4 |
| data/labels.csv and data/split.json unchanged | **PASSED** | sha256 before = after |
| Generation commands printed, not run | **PASSED** | §4 |

## 6. Deviations

- **Stricter overwrite rule:** the script refuses any existing output file, even with identical content. `core.labels.write_labels` alone would accept identical content. This matches "refuse to overwrite an existing file".
- **DEVLOG:** the three machine-B entries missing after the lead's marker fix (68b9211) were re-appended verbatim. A correction note in part 0 says the Task 18a entry's prereg hash (`5f08ab68…`) was superseded by the pre-commit E3 edit (`d9d25b58…`).

## 7. Open problems

- Before any replication view is rendered or analysed, more additive code is still needed (report 18a §7): one-group control pairing for render_views, split-free analysis entry points (Study 2.2 and 2.3), and rules application to new ids.
- `notes/DEVLOG.md` is still CRLF while `.gitattributes` says LF (one-time renormalisation: the lead's decision).

## 8. Next task

Generation on A and B with the commands above (after the lead's OK), then merge and `merge_check` on B.

## 9. Files to commit

- `scripts/labels_from_plan.py`, `tests/test_labels_from_plan.py`
- `notes/DEVLOG.md`, `notes/reports/18b_replication_labels.md`

**Not committed** (Rule E): `data/replication/labels.csv`.

## 10. Commit line

`Commit: feat: add labels-only writer for plans and write the replication labels file`
