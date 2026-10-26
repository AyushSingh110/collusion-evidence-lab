# Report 37 — Leak audit of the GitHub repository

1. **Goal:** remove anything from the repo that could leak; keep only necessary files.
2. **What was built:** `.gitignore` additions (`*.log`, `external/_hackathon_root/`, `external/util/`); untrack commands for the user.
3. **How verified:** `git ls-files`, `git grep` for key/email/IP/path patterns, `git log --all --name-only` for secret and data paths.
4. **Results:** 0 keys, 0 secret files ever committed, 0 data/cache files ever committed; 1 server log + 6 doc lines with local Windows paths; 13 unused hackathon tooling files.
5. **Acceptance:** audit — PASSED; removal from GitHub — PARTIAL (user must run the git commands; Rule A).
6. **Deviations:** none.
7. **Open:** licence of external/llm-trust-breaking; CLAUDE.md Rule E wording.
8. **Next task:** user runs the untrack commands and pushes.
9. **Commit:** Commit: chore: stop tracking the server log and unused hackathon tooling
