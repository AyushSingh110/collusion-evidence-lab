# Report 35 — Team wording restored; appendix layout

1. **Goal:** Keep the team's humanized wording; remove the empty space after the references; the appendix must not start on a fresh page.
2. **What was built:** `writeup/paper.tex` via `scratch/restore_wording.py` (see DEVLOG Task 35).
3. **How verified:** word diff against the team's pre-Task-33 file (no removed content); `scratch/lint_tex.py`; label check. Not compiled.
4. **Results:** 9 paragraphs restored; 2 content corrections + 2 typo fixes kept; appendix in two columns with `supertabular`.
5. **Acceptance:** wording restored — PASSED; no forced page break — PASSED (source); final look — PARTIAL (needs compile).
6. **Deviations:** the two content corrections (wrong count, wrong claim) were kept despite "keep the wording", for correctness.
7. **Open:** broken sentences in the restored text (listed in DEVLOG).
8. **Next task:** compile and review.
9. **Commit:** Commit: docs: restore the team's paper wording and keep the appendix in two columns
