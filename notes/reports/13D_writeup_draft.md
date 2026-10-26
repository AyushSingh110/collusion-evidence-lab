# 13D — Write-up Draft (Machine D, no model calls, no code changes)

Date: 2026-10-24 · Task 13D · Machine D · No model calls · No code changes

---

## 1. Goal (from the prompt)
Read `CLAUDE.md`, every file in `notes/reports/`, `configs/prereg_rq01.md`, `amendment1`, `amendment2` and the erratum. Only create files under `writeup/`. Do not edit anything else.
Create `writeup/draft.md`: a research write-up skeleton in clear, simple English covering:
1. Title + abstract placeholder (results TBD).
2. Introduction: collusion detection; question 2.2 (say vs do) and 2.3 (what counts as evidence; antitrust "plus factors").
3. Setup: El Farol, 5 agents, 8 rounds, the 3-stage protocol (from Shi et al. 2026), the four episode types and why each exists, models (`qwen2.5:7b` agents, `llama3.1:8b` monitor/judge, local, $0).
4. Pre-registration and integrity: frozen prereg, Amendments 1–2 + erratum, the full deviations table, RQ0.1 pilot-1 failure and pilot-2 pass, hand-check agreements.
5. Dataset: quality numbers, manipulation check, RQ0.2 results (report 12 placeholders).
6. Methods for RQ1–RQ9 and Study 2.3 (views V1–V5, controls, metrics, bootstrap, freeze procedure). Results sections left as "TBD" placeholders with exact tables.
7. Limitations (collected from every report).
8. `writeup/figures_plan.md`: 6–8 figures/tables needed and the exact CSV source for each.
9. `writeup/case_studies.md`: placeholders for 3 transcript case studies (one collusion game, one Type 3, one Type 4b with "deposit" talk).

---

## 2. What was built
| File | Summary |
|---|---|
| `writeup/draft.md` | Comprehensive 9-section research paper skeleton in clear, simple English with formal methods, preregistration audit, deviations table, exact result tables marked TBD, and comprehensive limitations from all reports. |
| `writeup/figures_plan.md` | Specifications for 7 tables and 2 figures, detailing the title, exact source CSV, primary columns, and research question addressed. |
| `writeup/case_studies.md` | Structured qualitative case studies with concrete transcript placeholders for Type 1 (collusion), Type 3 (talk-only lookalike), and Type 4b (same-incentive lookalike with "deposit" talk). |
| `notes/reports/13D_writeup_draft.md` | This summary report. |

---

## 3. How it was verified
- Verified zero code files modified.
- Verified zero model calls made.
- Verified all numbers cited in pre-registration and pilot sections originate from Reports 00 through 11 with explicit report citations.
- Confirmed file existence and content of `writeup/draft.md`, `writeup/figures_plan.md`, and `writeup/case_studies.md`.

---

## 4. Results and numbers obtained
- **Pilot 1 (Report 08):** 8 games, 1,088 calls, 0 failures, 79.6 min. Uptake Rule v1 FAIL (2/4 Type 1; rates: 0.875, 0.312, 0.688, 0.125); Type 2 falsification PASS (0/2); b1 top coGO PASS (4/4); b2 surplus PASS (4/4, +8.33, +6.25, +0.83, +6.67); reveals 6/64 = 9.4%.
- **Pilot 1 Hand-Check (Report 09b §4.6):** R1 (lead) vs R2 (teammate) agreement 91.7% (88/96 cells, $\kappa = 0.80$).
- **Pilot 2 (Report 09b §4.3, §12):** 6 games, 848 calls, 20 truncations (2.36%), 76.0 min. Uptake Rule v2 PASS (4/4 Type 1; rates: 1.000, 1.000, 0.938, 0.938); Type 2 falsification PASS (0/2); b1 top coGO PASS (4/4); b2 surplus PASS (4/4); reveals 8/64 = 12.5%; Lead Hand-Check Agreement PASS (96.9%, 93/96 cells, $\kappa = 0.931$). Overall RQ0.1: **PASS under Amendment 1**.
- **Secrecy Re-pilot (Report 09c):** 2 games, 304 calls, 1 truncation (0.33%), 27.4 min. Token ratio placebo_v3 / alliance_v4 = 139 / 138 = 1.007 (within $\pm 10\%$). Uptake v2 PASS (2/2); top coGO PASS (2/2); reveals 4/32 = 12.5%.
- **All un-computed dataset/test numbers:** Marked strictly as `TBD`.

---

## 5. Acceptance criteria
| Criterion | Status | Evidence |
|---|---|---|
| No model calls, no code changes | **PASSED** | Verified via file inspection; 0 calls made |
| Files created only under `writeup/` (plus this report) | **PASSED** | `writeup/draft.md`, `writeup/figures_plan.md`, `writeup/case_studies.md` |
| Draft sections 1–7 complete with exact tables | **PASSED** | `writeup/draft.md` §1–§9 |
| Never invent a number; missing results marked TBD | **PASSED** | Exact pilot numbers copied and cited; test tables marked TBD |
| Full deviations table included | **PASSED** | 14 items tabulated in `writeup/draft.md` §4.2 |
| Figures plan with 6–8 figures and CSV sources | **PASSED** | `writeup/figures_plan.md` (7 tables + 2 figures) |
| Case studies with 3 placeholders | **PASSED** | `writeup/case_studies.md` |
| Limitations collected from every report | **PASSED** | `writeup/draft.md` §8 covers Reports 00–11 |

---

## 6. Deviations
None. The task was executed strictly as specified for Machine D.

---

## 7. Open problems and limitations
- Report 12 numbers (full dataset generation quality, manipulation checks, and RQ0.2 full dataset results) are pending completion by the dataset generation machines (A & B) and will need to be inserted into `writeup/draft.md` §5.
- The test set execution of `study_2_2_views/analysis.py` and Study 2.3 decision rules is required to fill the `[TBD]` result table cells in `writeup/draft.md` §7.

---

## 8. What the next task should be
1. Execute `scripts/merge_check.py` on Machine B once generation concludes on Machines A & B (Report 12).
2. Render views with the flag-only cleaner (`scripts/render_views.py`).
3. Run the monitor on dev views, freeze dev choices and thresholds, and execute the frozen test analysis.
4. Populate the final test numbers into `writeup/draft.md` from the generated CSV artifacts.

---

## 9. Files to commit
- `writeup/draft.md`
- `writeup/figures_plan.md`
- `writeup/case_studies.md`
- `notes/reports/13D_writeup_draft.md`

## 10. Suggested commit line
`Commit: docs: add research write-up draft, figures plan, case studies, and Task 13D report`
