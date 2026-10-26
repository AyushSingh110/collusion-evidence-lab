# Report 28 — Professional README

## 1. Goal
"Update the readme: remove the icons, keep sensible icons only, and keep it professional."

## 2. What was built
- `README.md`: rewritten without decorative emoji; text status labels; plain headings and anchors; Study 1 / Study 2 naming; trimmed badges (7); sprint only in Acknowledgements.
- `assets/banner.svg`: sprint/track label replaced by "AUDITING MULTI-AGENT LLM SYSTEMS".

## 3. How it was verified
- `cp README.md scratch/_readme_check.md && conda run -n collusion-lab python -B scratch/audit_paper_numbers.py scratch/_readme_check.md` (copy deleted afterwards).
- Python scan of README.md for characters above U+2600 (excluding arrows/dashes/×/·/…).

## 4. Results
- Number audit: 0 numbers not found verbatim in sources.
- Emoji scan: 0 characters found.

## 5. Acceptance criteria
- Decorative icons removed — PASSED (scan: none).
- Sensible visual elements kept (banner, badges, callout boxes, figures) — PASSED (by inspection).
- No numbers changed or invented — PASSED (audit 0 missing).
- Professional tone, consistent with the paper — PASSED (Study 1/2 naming, no sprint branding outside Acknowledgements).

## 6. Deviations
- Also edited the banner text and the BibTeX (removed sprint/track), to match the Task 27 decision.

## 7. Open problems
- GitHub rendering of the SVG banner and Mermaid diagram not checked (needs a push).

## 8. Next task
- Lead review of README rendering on GitHub; optionally add a LICENSE and fill BibTeX authors.

## 9. Suggested commit line
Commit: docs: make the README professional (remove decorative icons, plain headings and status labels)
