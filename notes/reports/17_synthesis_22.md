# 17 — Final Study 2.2 synthesis, results table and README

Date: 2026-10-25 · Task 17 · Machine B · **No model calls.** No frozen file, prompt, monitor output, earlier report or earlier number was changed.

## 1. Goal (from the prompt)

- Write `writeup/results_22.md`, the final Study 2.2 results with every number copied and cited from reports 13–16: headline, RQ status table, robustness table, monitor reliability, limitations / next steps, pre-registration story with the full deviations table.
- Fix one reference typo in `writeup/excerpts_22.md`.
- Replace `README.md`.

## 2. What was built

| File | One line |
|---|---|
| `writeup/results_22.md` (new) | Sections a–f as specified. Every number carries a report + section citation (R10–R16; R05 / R00 / R01 only as cited by later reports). |
| `writeup/excerpts_22.md` | Only change: case (c) "Report 15 §6" → "Report 15 §4.6". |
| `README.md` (new; there was no README before) | Project, 5-bullet setup, headline findings (pilot, n = 24), reproducibility, layout, tests, data note. 93 lines. |

## 3. How it was verified

- Each number in `results_22.md` was copied from the cited report section. They were checked against reports 10, 12 and 13 (read in full in this task) and 14–16 (written in this session). Nothing was recomputed.
- The only arithmetic shown is what the reports themselves give (e.g. the R16 §5 point estimates).
- Commits and LF sha256 values of the pre-registration files come from read-only `git log` / `git show HEAD:<file> | sha256sum`.
- Self-review found and fixed four errors in my first draft before finishing:
  1. a check_env citation for RQ9 that report 16 does not contain;
  2. "R10 §A2" → §A5;
  3. "0 length cuts" in the follow-up → "0 truncation flags" (what R16 reports);
  4. "only V4 is clearly above chance" (wrong: V3 and V5 test CIs also exclude 0.5; fixed in both `results_22.md` and `README.md`).
- `conda run -n collusion-lab pytest -q`: see §4 (no code changed).

## 4. Results

- **RQ status:**
  - RQ0.1–RQ0.3 PASS;
  - RQ0.4 PASS except V2;
  - RQ1–RQ8 reported with their CIs;
  - RQ9 PENDING (machine C);
  - Follow-up 1: H1 V3 supported / V1 unclear, H2 unclear, H3 supported.
- **Robustness labels (11 claims):**
  - **ROBUST (6):** messages fail; actions fail; structure beats same length; private plans do not help (no detectable gain); same-incentive fools messages; position bias exists.
  - **ROBUST (exploratory) (1):** code action signals competitive.
  - **FRAGILE (3):** combining helps (RQ2); structure beats raw (V4 − V3); persona talk fools actions.
  - **NOT SUPPORTED (1):** position bias explains the raw-view failure.
- **Deviations table:** 22 rows (R10's 12, plus 10 later), each marked before / after the related data.
- **pytest:** 490 passed, 0 failed.

## 5. Acceptance criteria

| Item | Status | Evidence |
|---|---|---|
| a) Headline paragraph | **PASSED** | `results_22.md` §a |
| b) RQ status table incl. RQ0.1–0.4, RQ1–8, follow-up, RQ9 pending | **PASSED** | §b |
| c) Robustness table, 11 claims, 4 sources, labels | **PASSED** | §c. Cells marked "not reported" / "not measured" where a report has no number |
| d) Monitor reliability findings | **PASSED** | §d |
| e) Limitations + next steps | **PASSED** | §e |
| f) Pre-registration story + full deviations table | **PASSED** | §f |
| Excerpts typo only | **PASSED** | one-line change |
| README < ~150 lines, numbers only from results_22.md, no marketing language | **PASSED** | 93 lines |

## 6. Deviations

- **Labelling judgement calls in the robustness table:**
  - "Private plans do not help" is labelled ROBUST as "no detectable gain", with the absence-of-evidence caveat written in the cell.
  - "Code action signals competitive" is labelled ROBUST (exploratory), because the pooled set includes test.
  - The lead may prefer different labels.
- **Robustness cells where a source gives no paired CI** (dev V4 − C-length, dev V5 − V3, follow-up V4 vs V3) show the reported AUROCs, not a new difference.

## 7. Open problems

- RQ9 (second monitor, machine C) is pending.
- `writeup/results_22.md` will need an RQ9 row update when it is run.

## 8. Next task

- RQ9 on machine C.
- Study 2.3 decision rules (R1–R7) with thresholds chosen on dev.

## 9. Commit line

`Commit: docs: add final Study 2.2 results synthesis and project README`
