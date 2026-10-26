# 24 — Final documentation fixes

Date: 2026-10-26 · Task 24 · Machine B · **No model calls, no new analysis.**

## 1. Goal (from the prompt)

- Apply two lead label decisions in the robustness table and wherever they are repeated.
- Add every RQ9 / replication-phase deviation to the deviations table of `writeup/results_22.md` §f.

## 2. What was changed

| File | Change |
|---|---|
| `writeup/results_22.md` §c | "Actions alone fail" → **REPLICATED (llama); borderline for granite (G1: 0.628 [0.488, 0.754], R22C §4.4)**. "View ranking depends on the monitor" → **NOT SHARED BETWEEN MONITORS (G3; rests mainly on llama: llama V4 − V2 +0.313 [0.127, 0.481], granite −0.046 [−0.251, 0.152], R22C §4.4)**. The label legend entry is renamed to match. |
| `writeup/results_22.md` §g | Plain-English bullet "Monitor-dependent" → "Not shared between monitors (G3; rests mainly on llama)". |
| `writeup/results_22.md` §f | Header note, plus rows **23–39**: every RQ9 / replication-phase deviation from reports 15C, 18a, 18b, 18c, 19C, 20C, 21, 22C, 23 and 24, with what / why / where recorded (+ date) / before or after the related data. |
| `writeup/results_summary.md` | Finding 7 status "Monitor-dependent" → "Not shared between monitors (G3; rests mainly on llama)". |
| `README.md` | Unchanged: it does not repeat these two labels. |

## 3. How it was verified

- **Sources:** the deviation sections of reports 18a, 18b, 18c, 19, 19C, 20B, 20C, 21, 22C and 23 were extracted by script, and 15C §4.1 / §6 and 19C §4.2 were read for the machine-id items.
- **Rows:** each row cites its report section.
- **Label wording:** `grep` for "MONITOR-DEPENDENT" / "Monitor-dependent" across `results_22.md`, `results_summary.md` and `README.md`: 0 left.
- **No number was changed:** the only numbers added are copies of R22C §4.4 values already in the write-up.

## 4. Results

2 labels changed (3 places in `results_22.md`, 1 in `results_summary.md`); 17 deviation rows added (23–39).

## 5. Acceptance criteria

| Item | Status |
|---|---|
| 1. The two labels changed, and repeated wording updated | **PASSED** |
| 2. Deviation rows for all six listed items plus the other replication-phase deviations in reports 15C–23 | **PASSED** (rows 23–39) |
| 3. Diffs shown, DEVLOG, commit line | **PASSED** |

## 6. Deviations

- **Dates:** the table has no "When" column, so each new row gives its date in "Recorded where" rather than changing the table's shape.
- **Not listed as deviations:** items in the reports that are only implementation conventions with no effect on any result, e.g. 22C's read-only comparison helper and 20B's audit method notes. Documentation repairs are grouped in row 39.

## 7. Open problems

None.

## 8. Next task

The lead's final review.

## 9. Files to commit

`writeup/results_22.md`, `writeup/results_summary.md`, `notes/DEVLOG.md`, `notes/reports/24_doc_fixes.md`

## 10. Commit line

`Commit: docs: final label wording and the replication-phase deviations table`
