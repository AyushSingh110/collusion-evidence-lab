# 26 — Project README redesign (machine D; no model calls, no new numbers)

Date: 2026-10-26

1. **Goal.** Turn `README.md` into a "trending research project" style page: a banner, badges and full project details.

2. **What was built.**
   - `assets/banner.svg`: a custom banner (title, sprint line, three pills, and a 5-agent motif with a secret T–Z link). Pure SVG, no external service.
   - `README.md`, rewritten. In order:
     - centred banner, shields.io badges and a links row;
     - a TL;DR callout and a table of contents;
     - "Why this matters" (2.2 / 2.3 table);
     - the 8 key findings with status icons;
     - "How it works": game, episode types, a Mermaid pipeline, the views table and the evidence-families table;
     - results with figures 9 and 10, plus collapsible tables and a 2×2 grid of more figures;
     - the LLM-monitor failure modes table;
     - research integrity (pre-registration commits, pinned digests);
     - quickstart, with a collapsible pipeline section;
     - repository layout, limitations, BibTeX citation and acknowledgements.

3. **How it was verified.**
   - `scratch/audit_paper_numbers.py` on a copy of the README: **0 numbers not found** in the write-up sources.
   - All 6 figure paths and the banner exist.
   - `pytest -q` to check the tests badge: **671 passed, 3 skipped, 2 failed**. The 2 failures are in `tests/test_replication22.py`, with `FileNotFoundError: data/labels.csv`; the data is gitignored and not on this machine.

4. **Results.** No new numbers. Every finding is copied from `writeup/results_summary.md`, `results_22.md` and `results_23.md`.

5. **Acceptance.**

   | Item | Status |
   |---|---|
   | Banner and badges | **PASSED** |
   | Full project details | **PASSED** |
   | Numbers traceable | **PASSED** |

6. **Deviations.**
   - The tests badge says "pytest · mock LLM", not "passing", because 2 data-dependent tests fail on a clone without `data/`. The README has a note about it.
   - No licence badge: the repository has no LICENSE file.

7. **Open.**
   - Add a LICENSE if the team wants one.
   - Fill in the BibTeX author names.
   - The banner font depends on the viewer's system fonts (Segoe UI, Helvetica or Arial); check it on GitHub after pushing.

8. **Next.** Commit and push; check that the banner, badges and Mermaid diagram render on GitHub.

9. **Commit:** `docs: redesign README with banner, badges, findings, pipeline diagram and figures`
