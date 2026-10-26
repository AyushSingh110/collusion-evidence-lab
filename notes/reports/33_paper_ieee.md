# Report 33 — Paper in IEEE conference format

1. **Goal:** IEEE format; keep all text (no cuts); place figures where they belong; clean alignment with no overlap or cut-off content.
2. **What was built:** `writeup/paper.tex` in IEEEtran conference format (see DEVLOG Task 33).
3. **How verified:** `scratch/lint_tex.py`; label/ref and cite/bibitem checks; `scratch/audit_paper_numbers.py` on a copy. Not compiled.
4. **Results:** braces 418/418; 6/6 images resolve; 10 full-width floats; 0 missing refs or citations; no new numbers.
5. **Acceptance:** IEEE format — PASSED (source); nothing cut — PASSED; figure placement and no overlap — PARTIAL (needs compile).
6. **Deviations:** fixed garbled/wrong sentences (listed in DEVLOG) and filled Author Contributions.
7. **Open:** compile check; "Study 2.2/2.3" inside figure images; author roles to confirm.
8. **Next task:** compile on Overleaf and review.
9. **Commit:** Commit: docs: convert the paper to IEEE conference format with full-width figures
