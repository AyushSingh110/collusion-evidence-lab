# 25D — Final paper (machine D; no model calls, no new numbers)

Date: 2026-10-26 · Task 25D

## 1. Goal (short)

Write the final paper from the write-up files, in the Apart Research submission template:

- `writeup/paper.md`;
- on the lead's request in chat, also LaTeX in the template's format, with the figures placed where they are discussed.

Rules for the content:

- use only numbers that appear in the write-up files, copied exactly, each with its report citation in a comment;
- no new claims;
- `[MISSING]` where no number exists.

## 2. What was built

| File | One line |
|---|---|
| `writeup/paper.tex` | The submission paper in the template's structure: title block with sprint footnote, authors, "With Apart Research", abstract, sections 1–8, Code and Data, Author Contributions, References (11), Appendix A (all 39 deviations, longtable), Appendix B (reproducibility), LLM Usage Statement. 6 result figures + 1 TikZ pipeline diagram, 3 tables. Every number has a `% src:` comment |
| `writeup/paper.md` | The same paper in Markdown (figures embedded from `figures/`; sources in `<!-- src: -->` comments) |
| `scratch/lint_tex.py` | Structural lint for the .tex (braces, environments, labels, citations, figure paths, non-ASCII) |
| `scratch/audit_paper_numbers.py` | Checks that every decimal and k/n count in the paper appears verbatim in the sources |

**Figure placement:**

| Paper figure | Source file | Section |
|---|---|---|
| 1 | TikZ pipeline diagram | §3.2 |
| 2 | fig1 (AUROC by view) | §4.2 |
| 3 | fig2 (per-type scores) | §4.2 |
| 4 | fig7 (pair-order follow-up) | §4.3 |
| 5 | fig8 (granite) | §4.4 |
| 6 | fig9 (replication 2.2) | §4.5 |
| 7 | fig10 (replication 2.3) | §5 |

Figures 3–6 and 8 of the write-up are not used. `paper_figures.md` was not needed.

## 3. How it was verified

```
conda run -n collusion-lab python -B scratch/lint_tex.py writeup/paper.tex
conda run -n collusion-lab python -B scratch/audit_paper_numbers.py writeup/paper.tex
conda run -n collusion-lab python -B scratch/audit_paper_numbers.py writeup/paper.md
```

- **No LaTeX compiler is installed on machine D**, so the `.tex` was **not compiled**. Structure was checked instead:
  - braces balanced (437/437); every environment closed;
  - every `\ref` has a `\label`, every `\cite` has a `\bibitem`;
  - all 6 figure files exist under `writeup/figures/`;
  - no non-ASCII characters.
- **Number audit:** 0 result numbers missing. The only hits were a column width (`0.27\textwidth`) and a section number (`3.6`).

## 4. Results

- **Paper length:** about 8,000 words in the Markdown version, including the two appendices and the 39-row deviation table. The main text is about 6–8 pages in the template.
- **`[MISSING]` markers:** none. Every requested section had numbers in the write-up files.

## 5. Acceptance

| Item | Status |
|---|---|
| Structure 1–10 of the task, in template order | **PASSED** |
| Only numbers from the write-up files, with citations in comments | **PASSED, one exception** (below) |
| Figures 1, 2, 7, 8, 9 (Study 2.2) and 10 (Study 2.3) used, with captions from `captions.md` | **PASSED** |
| LaTeX in the template format | **PARTIAL**: written and linted, not compiled (no TeX on machine D) |

## 6. Deviations

- **Two-rater pilot-1 numbers from report 10.** 91.7% (κ 0.80) between raters, and rule v2 vs. raters 79.2% / 85.4%, come from **report 10 §B3**. That report is cited by `results_22.md`, but these four numbers are not written in the write-up files themselves. They were included because the task asks for "the two-rater validation". The comment next to them says so. **Lead: keep or delete that sentence.**
- **One interpretive sentence** in the Discussion, as the task's "communication evidence is usually private" link asked: "Real cartels rarely announce their agreement in public, and an auditor, like a competition authority, will often lack the private channel." This is framing, not a finding of ours.
- **Extra file:** `writeup/paper.tex` was created in addition to `paper.md`, on the lead's chat request.
- **Placeholders:** authors and author contributions are placeholders. The LLM usage statement is a draft for the team to edit.

## 7. Open problems

- **Compile on Overleaf** and check the layout:
  - the wide tables (Table 2's G3 row, the 8-column Table 3) and the longtable appendix;
  - upload `paper.tex` together with the `figures/` folder.
- **Author names and affiliations** are to be filled in by the team.
- **The template asks for about 4 pages.** Our main text is longer, because the task asked for 6–8 pages. Shorten Sections 4–6 if the judges enforce the 4 pages.

## 8. Next task

The lead compiles the paper on Overleaf, fills in authors, edits the LLM statement, and decides on the report-10 sentence. Then submit.

## 9. Suggested commit line

`Commit: docs: add final paper (LaTeX template version + Markdown) with sourced numbers and figures`
