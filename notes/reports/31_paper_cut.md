# Report 31 — Paper body cut toward 8 pages

1. **Goal:** Cut text and tighten spacing so everything up to the Conclusion fits in ~8 pages, keeping it readable; appendix may extend to 11–12 pages.
2. **What was built:** `writeup/paper.tex` restructured (see DEVLOG Task 31); `scratch/restructure_paper.py` (the section-4 rebuild and float moves).
3. **How verified:** `scratch/lint_tex.py` (braces 464/464, figures resolve, no non-ASCII); label check for every `\ref`; `scratch/audit_paper_numbers.py` on a copy (2 unmatched, both explained). Not compiled.
4. **Results:** 791 → 758 source lines; body floats 10 → 5; 4 figures + 1 table moved to Appendix A.
5. **Acceptance:** text cut and moved — PASSED; no new numbers — PASSED; ≤ 8 pages to Conclusion — PARTIAL (needs compile).
6. **Deviations:** also corrected garbled / wrong sentences in the paragraphs that were rewritten anyway, and the "fool the LLM Judge" misstatement.
7. **Open:** page count; abstract trim if needed; Author Contributions placeholders; `paper.md` out of sync; "Study 2.2 / 2.3" in figure titles.
8. **Next task:** compile, check page 8, then fix remaining items.
9. **Commit:** Commit: docs: cut the paper body to fit the page limit and move supporting results to the appendix
