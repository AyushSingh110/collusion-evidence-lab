# Report 34 — Author roles, page numbers, ≤ 8 pages target

1. **Goal:** Swap Ayush Singh's and Param Bapu's contributions; keep everything up to the Conclusion within 8 pages; add page numbers.
2. **What was built:** `writeup/paper.tex` edits via `scratch/ieee_compact.py` (see DEVLOG Task 34).
3. **How verified:** script asserts each replacement matched exactly once; `scratch/lint_tex.py`. Not compiled.
4. **Results:** 2 figures moved to one-column; 5 figures narrowed; page numbers on; roles swapped; no text cut.
5. **Acceptance:** roles swapped — PASSED; page numbers — PASSED (source); ≤ 8 pages — PARTIAL (needs compile).
6. **Deviations:** none.
7. **Open:** page count after compile.
8. **Next task:** compile and check page 8.
9. **Commit:** Commit: docs: swap two author roles, add page numbers and compact paper figures
