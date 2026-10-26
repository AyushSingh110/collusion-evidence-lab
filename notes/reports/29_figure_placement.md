# Report 29 — Figure placement in the paper

1. **Goal:** Stop the test-set AUROC figure from appearing inside the §4.1 text; place it after §4.1.
2. **What was built:** `writeup/paper.tex`: `\usepackage{flafter}` (floats never precede their source position).
3. **How verified:** Not compiled (no TeX on machine D). The change is a standard LaTeX package; the user verifies on recompile.
4. **Results:** No numbers changed.
5. **Acceptance:** Figure appears after §4.1 — PARTIAL (needs the user's recompile).
6. **Deviations:** None.
7. **Open:** If any figure drifts too far, use `[!htb]` for that figure.
8. **Next task:** Recompile and review the figure positions.
9. **Commit:** Commit: fix: keep paper figures from floating above the text that introduces them
