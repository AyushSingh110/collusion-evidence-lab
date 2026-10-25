# 20B — Independent number audit of the write-up

Date: 2026-10-25 · Task 20B · Machine B · **No model calls.** Nothing under `data/raw/replication/` and no replication output was read.

## 0. Independence note

- The task asks me to treat the files as someone else's work.
- **In fact, I wrote most of the audited text in earlier tasks:** `results_22.md`, `README.md`, the Figure 1–7 captions and `excerpts_22.md`. Machine C wrote `results_23.md` and the Figure 8 caption.
- To compensate, every check was made against the **sources** (reports, git objects, file hashes, local run outputs) by script, and nothing was accepted from memory. Two of the issues below are errors I introduced myself.

## 1. Goal (from the prompt)

- Check every number, CI, count, fraction, commit hash and sha256 in five files: `writeup/results_22.md`, `writeup/results_23.md`, `writeup/excerpts_22.md`, `writeup/figures/captions.md` and `README.md`.
- Check each against its cited source (and against local outputs where they exist), plus labels and wording.
- Fix only clear copy errors, list everything else for the lead, and check that figures and cited reports exist.

## 2. What was built

| Item | One line |
|---|---|
| Audit scripts (scratchpad, not committed) | `audit20b.py` (token extraction + lookup), `audit20b_ci.py` (whole CI triplets + context), `audit20b_sec.py` (number inside the cited section), `audit20b_23.py` (results_23 vs report 17C), `audit20b_ex.py` (excerpts and Figure 2 claim vs `runs/test_p8` monitor output), `audit20b_table.py` (appendix table) |
| `writeup/results_22.md` | 2 citation fixes (§4) |
| `notes/reports/20B_audit.md` | This report, with the full per-line table (Appendix A) |

## 3. How it was verified

**1. Token pass.**
- Every decimal, integer ≥ 10, fraction, percentage and hex hash in the 5 files was extracted: **763 tokens** (731 numeric, 32 hashes).
- Each was looked up in the cited report, then in all 28 reports, the write-ups and the prereg files, then in local outputs (`runs/test_p8/*.csv`, `runs/p7_analysis_dev/*.csv`, `runs/p15/results.json`, `runs/p15/pair_bias.json`, `runs/followup1/analysis.json`, `runs/test_p8/extras.json`), rounded to 0–4 decimals.

**2. CI-triplet pass.**
- **106** "estimate [low, high]" triplets were matched **as a whole** (same three numbers, same rounding) in the sources. The matcher allows the formats "e [", "e | [", "e, 95% CI [" and "e (n) [".
- Each match was printed with its surrounding text in the write-up and in the source, and checked by hand for the right row, column, split and model.

**3. Section pass.**
- For each clause with one "R14 §4.6"-style citation, the script checked that its numbers occur **inside that section** of the report.

**4. Study 2.3 pass.**
- Every number in `results_23.md` was checked against report 17C (its source, which it rarely cites by name).

**5. Direct data checks.**
- All 20 per-view score / named-pair cells of the 4 excerpt tables were checked against `runs/test_p8/outputs/monitor.jsonl`.
- The Figure 2 claim "only V4 has every T1 above every T2" and the V1 Type 4b mean 88.5 were recomputed from the same file.
- The model pins were checked against `configs/pins.json`.

**6. Hashes.**
- `git cat-file -e` and `git log` were run for all 13 commit hashes (dates and contents checked).
- The LF sha256 of all 8 referenced config files was recomputed.

**7. Existence.**
- The 8 figure files named in `captions.md` and the 13 distinct reports cited exist.

## 4. Results

**Summary counts.**

| Level | OK | MISMATCH | UNSUPPORTED | WRONG LABEL |
|---|---|---|---|---|
| Tokens (763) | 739 | 12 (on 2 lines) | 9 (on 2 lines) | 3 (on 1 line) |
| **Findings** | — | **2** (citation sections, **fixed**) | **2** | **1** |

- **Token-level counts** mark every token on a flagged line. In every flagged case **the numbers themselves are correct**: the issue is a citation, a missing source or a wording claim.
- **No wrong number was found** in any of the five files.
- **Also verified:**
  - all **106 CI triplets** match a source exactly and in the right context;
  - all **20 excerpt cells** match the monitor output;
  - all **13 commits** and **8 sha256** values check out, except the draft hash in finding 4;
  - all **8 figures** and **13 cited reports** exist.

**Rounded copies accepted as OK** (the source is unambiguous):

| Write-up | Source |
|---|---|
| captions "0.90 [0.77, 0.98]" | R14 V4 0.896 [0.771, 0.979] |
| captions "Kendall tau-b 0.26", "+0.42 [0.14, 0.68]" | R15 §4.1: 0.255; +0.417 [0.142, 0.684] |
| results_23 "0.40", "0.44", "0.48–0.51" | R17C: 0.396; 0.438; 0.481–0.509 |
| results_23 "0.25–0.50" | R17C "0.25–0.5" |
| results_22 robustness "21/24 … 22/24" | R15 §4.6 table written as "22 / 21" (dev / test) |

### The 5 most important issues

1. **WRONG LABEL. Figure 1 caption (`captions.md` line 11):** "Only the structured report (V4, 0.90 [0.77, 0.98]) has a CI clearly above chance."
   - This is false by report 14 §4.2: V3 0.736 [0.535, 0.920] and V5 0.705 [0.517, 0.882] also exclude 0.5.
   - I wrote this caption in task 15. The same error was corrected in results_22 and README in task 17, but not here.
   - It is a wording claim, so I did not change it (for the lead). Suggested text: "V4 has the highest AUROC (0.90 [0.77, 0.98]); the CIs of V3 and V5 also exclude chance."
2. **UNSUPPORTED (citation). `results_23.md` line 32, "Capture alone … 0.896 [0.781, 0.986]":**
   - The value is correct: report 15 §4.4, capture test AUROC; the counts 8/12, FPR 2/12 and T4b 2/4 match report 17C §4.5.
   - But the line cites no source, and the CI is not in 17C. Suggested: add "(report 15 §4.4)". Not changed (adding a source is not a copy-error fix).
3. **MISMATCH (citation sections) — FIXED.** In `results_22.md` §d, two clauses cited the wrong section of report 16:
   - line 113: exact values 0.417 [0.250, 0.625] and 0.217 are in §4.3; it cited §4.7 only;
   - line 117: AUROC 0.559 vs 0.372 are in §4.2; it cited §4.4 only.

   The values were already correct. I wrote both lines myself.
4. **UNSUPPORTED (not verifiable on B). `results_22.md` §g:**
   - The granite amendment hash `778cf66b…` and the G1–G4 rows rest on report 19C only.
   - `configs/prereg_replication_amendment1.md` is an uncommitted draft on machine C, so neither the hash nor the hypotheses can be checked here.
5. **For the lead (labels, not numbers):**
   - "Structure beats same length → ROBUST (llama only)": granite never scored C-length (R15C §2), so the "(llama only)" rests on granite's V4 being at chance, not on a direct test.
   - §d ("Position / recency bias") still states the bias without the RQ9 qualifier that the headline and §c carry.

### Fixes made (all in `writeup/results_22.md`)

| Line | Old | New | Source |
|---|---|---|---|
| 113 | "… beyond the T-Z habit (R16 §4.7)." | "… beyond the T-Z habit (R16 §4.3, §4.7)." | R16 §4.3 table (V1 random 10/24 = 0.417 [0.250, 0.625], no-bias 0.217) |
| 117 | "… with MAD 10.79 and Spearman 0.653 (R16 §4.4)." | "… (R16 §4.2, §4.4)." | R16 §4.2 (V2 fixed 0.559, frozen 0.372) |

**No number, verdict, robustness label or headline wording was changed.**

### For the lead to decide

- Issue 1: correct the Figure 1 caption claim.
- Issue 2: add the report 15 §4.4 citation in `results_23.md`.
- Issue 4: commit the granite amendment so §g can be verified.
- Issue 5: the "(llama only)" label for "structure beats same length", and an RQ9 qualifier in §d.

## 5. Acceptance criteria

| Item | Status | Evidence |
|---|---|---|
| 1. Every number / CI / count / fraction / hash checked against its source; local outputs where present; labels and wording | **PASSED** | §3 passes 1–6; 763 tokens, 106 triplets |
| 2. Table: file, location, value, source, status | **PASSED** | Appendix A (one row per line with numbers; source column; status) |
| 3. Only clear copy errors fixed and listed; interpretations left for the lead | **PASSED** | 2 citation fixes; 4 lead items |
| 4. Figures exist; cited reports exist; unsupported numbers flagged | **PASSED** | 8/8 figures, 13/13 reports; 2 UNSUPPORTED |
| 5. Summary counts + top 5 issues | **PASSED** | §4 |
| No model calls; no replication data read; only allowed files | **PASSED** | `git status`: results_22.md + notes |

## 6. Deviations

- **Single digits (0–9) were not looked up** on their own: too ambiguous. They are checked wherever they are part of a fraction, a CI or a count such as "8/12".
- **Appendix A has one row per line, not one row per token.** Each row lists every value on that line. The token-level table (763 rows) is in the scratchpad (`audit_tokens.tsv`) and can be added on request.
- **The "source value" column** is given as the source in which each value was found, plus the exact source value wherever it differs (rounded copies and the issues). For OK rows the source value equals the written value by construction of the check.

## 7. Open problems

- Issues 1, 2, 4 and 5 remain open (the lead's decisions).
- The audit trusts the reports as the reference. It does not re-derive report numbers from raw data, except for the excerpts, the Figure 2 claim and the hash and pin checks.

## 8. Next task

The lead decides the four open items. Then the replication pipeline, after generation (report 18c §8).

## 9. Files to commit

- `writeup/results_22.md`
- `notes/DEVLOG.md`, `notes/reports/20B_audit.md`

## 10. Commit line

`Commit: docs: independent number audit of the write-up (2 citation fixes, issues listed for the lead)`

## Appendix A — per-line audit table

The "Source checked" column lists where the line's values were found: R = report, plus write-ups, prereg files and local outputs.

| File | Line | Values as written | Source checked | Status |
|---|---|---|---|---|
| results_22.md | 1 | 2.2 | R0, R1, R12, R13, R13C, R9C, local outputs | OK |
| results_22.md | 3 | 2.2 | R0, R1, R12, R13, R13C, R9C, local outputs | OK |
| results_22.md | 7 | 48 24 24 12 | R0, R1, R2, R3, R4, R5, R6A, R7, R9B, local outputs | OK |
| results_22.md | 11 | 24 | R0, R1, R2, R3, R4, R5, local outputs | OK |
| results_22.md | 12 | 95% 2000 20261023 | R0, R1, R11, R13, R14, R15, R15C, R16, R4, R6A, R9B, R9C, local output | OK |
| results_22.md | 13 | 4.3 | 14 | OK |
| results_22.md | 24 | 0.490 0.299 0.691 0.372 0.170 0.601 | R14, R15, R15C, R16, R18C, README.md, local outputs | OK |
| results_22.md | 25 | 0.896 0.771 0.979 | 14, local outputs | OK |
| results_22.md | 28 | 0.767 0.604 0.917 | R13C, R14, R15, R15C, R16, R17C, R19, README.md, local outputs | OK |
| results_22.md | 29 | 0.510 0.292 0.729 | R13, R14, R15, R15C, R16, R17C, R19, README.md, local outputs, results | OK |
| results_22.md | 30 | -0.667 | 15C, local outputs | OK |
| results_22.md | 32 | 0.736 | 14, 15C, local outputs | OK |
| results_22.md | 34 | 0.944 0.884 0.986 48 | 15, local outputs | OK |
| results_22.md | 37 | 80 96/96 | 13, local outputs | OK |
| results_22.md | 39 | +0.188 +0.007 +0.389 | 16, local outputs | OK |
| results_22.md | 41 | +0.365 0.094 0.611 -0.031 -0.250 0.191 | 14, 15C, local outputs | OK |
| results_22.md | 43 | 2.3 24 | local outputs, results_23 | OK |
| results_22.md | 44 | 0.872 0.736 0.986 | R14, R15, R15C, R16, R17C, R19, README.md, local outputs, results_23.m | OK |
| results_22.md | 45 | 0.396 0.205 0.597 | R15, R17C, R19, README.md, local outputs, results_23.md | OK |
| results_22.md | 46 | -0.080 -0.208 0.045 | R16, R17C, R19, README.md, local outputs, results_23.md | OK |
| results_22.md | 54 | 95% | R0, R13, R14, R15, R15C, R16 | OK |
| results_22.md | 56 | 4/4 0/2 4/4 4/4 4/4 96.9% 0.931 2/4 24/24 23/24 | 10, 12, R13, R16, R17C | OK |
| results_22.md | 57 | 7/8 6/8 | 12 | OK |
| results_22.md | 58 | 0/0 384 0.465 0.250 0.667 0.632 0.431 0.833 0.5 | 12, 13, 14, local outputs; rounded copy of the cited value or tokenisation artefact; checked by hand | OK (rounded / format) |
| results_22.md | 59 | 0.44 0.971 5.00 0.676 1.000 1.000 5.44 0.851 | 13, local outputs | OK |
| results_22.md | 60 | 0.490 0.299 0.691 0.372 0.170 0.601 0.736 0.535 0.920 0.896 0.771 0.979 0.705 0.517 0.8… | 14, local outputs | OK |
| results_22.md | 61 | +0.365 0.094 0.611 +0.040 -0.155 0.238 +0.188 +0.007 +0.389 | 14, 15, 16, local outputs | OK |
| results_22.md | 62 | 0/4 2/4 1/4 2/4 3/4 2/4 0/4 4/4 0.344 0.12 0.65 0.219 0.00 0.62 | 14, local outputs | OK |
| results_22.md | 63 | +0.188 -0.028 0.386 | 14, local outputs | OK |
| results_22.md | 64 | +0.160 -0.021 0.351 +0.285 0.017 0.556 | 14, local outputs | OK |
| results_22.md | 65 | -0.031 -0.267 0.236 | 14, local outputs | OK |
| results_22.md | 66 | -0.173 -0.382 -0.009 21 | 14, 15, local outputs | OK |
| results_22.md | 67 | 12 0.1 1/12 6/12 2/12 7/12 5/12 5/12 4/12 5/12 8/12 | 14, 16, R0, R1, R2, R3, R4, R5, local outputs | OK |
| results_22.md | 68 | 0.729 0.549 0.896 0.767 0.604 0.917 0.736 0.573 0.917 0.510 0.292 0.729 -0.667 | 15C, local outputs | OK |
| results_22.md | 69 | +0.458 0.292 0.667 +0.417 0.167 0.667 +0.017 -0.229 +0.281 +0.042 -0.198 +0.285 -0.076 … | 16, local outputs | OK |
| results_22.md | 78 | 48 | 15, local outputs | OK |
| results_22.md | 79 | 24 | 16, local outputs | OK |
| results_22.md | 80 | 24 | 15C, local outputs | OK |
| results_22.md | 90 | 0.490 0.299 0.691 0.431 0.219 0.646 0.459 0.323 0.597 0.490 0.299 0.691 0.507 0.306 0.7… | R13, R13C, R14, R15, R15C, R16, R17C, R18C, R19, README.md, local outp | OK |
| results_22.md | 91 | 0.372 0.170 0.601 0.493 0.260 0.726 0.447 0.302 0.595 0.559 0.319 0.788 0.514 0.295 0.7… | R13, R13C, R14, R15, R15C, R16, R17C, R19, README.md, local outputs | OK |
| results_22.md | 92 | +0.365 0.094 0.611 -0.174 -0.406 0.056 +0.040 -0.155 0.238 +0.19 +0.28 -0.031 -0.250 0.191 | R13, R14, R15, R15C, R16, R17C, R18C, R19, README.md, local outputs, r | OK |
| results_22.md | 93 | +0.160 -0.021 0.351 +0.444 0.146 0.729 +0.350 0.166 0.534 0.826 0.750 0.750 0.792 -0.22… | R12, R13, R13C, R14, R15, R15C, R16, R17C, R18C, R19, R8, R9B, R9C, RE | OK |
| results_22.md | 94 | +0.285 0.017 0.556 0.764 0.583 +0.237 0.030 0.443 0.510 0.292 0.729 | R10, R13, R13C, R14, R15, R15C, R16, R17C, R19, README.md, local outpu | OK |
| results_22.md | 95 | -0.031 -0.267 0.236 0.583 0.319 +0.149 -0.062 0.347 24 | R0, R1, R13, R13C, R14, R15, R15C, R16, R17C, R19, R2, R3, R4, R5, loc | OK |
| results_22.md | 96 | 0.344 0.12 0.65 0.359 0.190 0.562 0.344 0.125 0.646 0.365 0.115 0.625 0.812 0.604 0.958 | R1, R10, R12, R13, R13C, R14, R15, R15C, R16, R17C, R18A, R18C, R19, R | OK |
| results_22.md | 97 | 0.219 0.00 0.62 0.266 0.049 0.526 0.458 0.083 0.854 0.500 0.156 0.844 0.833 0.708 0.958 | R1, R10, R12, R13, R13C, R14, R15, R15C, R16, R17C, R18A, R19, R3, R4, | OK |
| results_22.md | 98 | 0.896 0.896 0.872 0.896 0.885 0.944 0.906 0.837 0.767 0.604 0.917 | 15, R13C, R15C, R16, R19, README.md, local outputs | OK |
| results_22.md | 99 | 21/24 17/24 7/24 22/24 22/24 7/24 21/24 19/24 +0.458 0.292 0.667 +0.417 0.167 0.667 0.7… | 15, D:\collusion-evidence-lab\configs\prereg_followup1_pair_order.md,  | OK |
| results_22.md | 100 | +0.017 -0.229 +0.281 +0.042 -0.198 +0.285 | R10, R14, R15, R15C, R16, R17C, local outputs, results_23.md | OK |
| results_22.md | 107 | 100 80 96/96 15/16 80 | 13, 5, local outputs | OK |
| results_22.md | 109 | 10 | 13, local outputs | OK |
| results_22.md | 111 | 21/24 17/24 24/24 7/24 12 | 15, D:\collusion-evidence-lab\configs\prereg_followup1_pair_order.md,  | OK |
| results_22.md | 112 | 10/24 9/24 | 16 | OK |
| results_22.md | 113 | 0.417 0.250 0.625 0.217 | 16, local outputs; values in R16 §4.3 (0.417 [0.250, 0.625], 0.217); cited §4.7 only | MISMATCH (citation) -> FIXED |
| results_22.md | 117 | 0.676 0.559 0.372 +0.188 +0.007 +0.389 10.79 0.653 | 13, 16, local outputs; AUROC 0.559 / 0.372 are in R16 §4.2; cited §4.4 only | MISMATCH (citation) -> FIXED |
| results_22.md | 118 | 23/24 22/24 7.92 0.775 | 16, local outputs | OK |
| results_22.md | 121 | 25% | 13 | OK |
| results_22.md | 122 | 8/12 | 13 | OK |
| results_22.md | 128 | 16 | 10, local outputs | OK |
| results_22.md | 131 | 24 25 | 10, 14, local outputs | OK |
| results_22.md | 134 | 6.5% 12 24 | 12, local outputs | OK |
| results_22.md | 137 | 1.75% 36 12 | 12, local outputs | OK |
| results_22.md | 145 | 0.319 0.736 +0.417 0.142 0.684 0.255 | 15, local outputs | OK |
| results_22.md | 147 | 21 | 14, local outputs | OK |
| results_22.md | 152 | 24 | 14, 16, local outputs | OK |
| results_22.md | 160 | 2.3 | R0, R1, R11, R2, R4, R9B, local outputs | OK |
| results_22.md | 167 | 16 | R0, R1, R2, R4, R5, R7, local outputs | OK |
| results_22.md | 169 | 4909c7e 84fca68 c5976220465c10f5 2026 08 31 | 10, D:\collusion-evidence-lab\configs\prereg_rq01_amendment1.md, D:\co | OK |
| results_22.md | 170 | 2d47580 c214284753ff2cf1 2026 10 42 | 10, D:\collusion-evidence-lab\configs\prereg_rq01_amendment2.md, D:\co | OK |
| results_22.md | 171 | a989c7a ccb24bbe99095b88 2026 13 37 | 10, D:\collusion-evidence-lab\configs\prereg_replication.md, D:\collus | OK |
| results_22.md | 172 | ef31afca9c45d630 0dfd1b1 2026 2026 02 28 | 12, D:\collusion-evidence-lab\configs\prereg_replication.md, R12, READ | OK |
| results_22.md | 173 | 89bdb79 ccc4bf07838be73e 2026 02 28 | 14, D:\collusion-evidence-lab\configs\prereg_followup1_pair_order.md,  | OK |
| results_22.md | 174 | 496fc28 0d6aaa412b394419 2026 04 39 | 16, R14, R15C, R16, R4, R9B, README.md, figures/captions.md | OK |
| results_22.md | 178 | 12 13 | 10, local outputs | OK |
| results_22.md | 183 | 4909c7e 84fca68 | git objects / LF sha256 of files | OK |
| results_22.md | 184 | 09 | 8 | OK |
| results_22.md | 187 | 10 12 | R0, R1, R2, R3, R4, R5, R6A, local outputs | OK |
| results_22.md | 191 | 10 12.5% | D:\collusion-evidence-lab\configs\prereg_rq01_amendment2.md, R0, R1, R | OK |
| results_22.md | 192 | 11 12.5% | D:\collusion-evidence-lab\configs\prereg_rq01_amendment2.md, R0, R1, R | OK |
| results_22.md | 193 | 12 | R0, R1, R2, R4, R5, R6A, local outputs | OK |
| results_22.md | 194 | 13 | 12, local outputs | OK |
| results_22.md | 195 | 14 | 12, local outputs | OK |
| results_22.md | 196 | 15 16384 8192 | 12, 13, local outputs | OK |
| results_22.md | 197 | 16 80 96/96 | 13, local outputs | OK |
| results_22.md | 198 | 17 | 13, local outputs | OK |
| results_22.md | 199 | 18 | R0, R1, R11, R4, R5, R8, local outputs | OK |
| results_22.md | 200 | 19 | 15, local outputs | OK |
| results_22.md | 201 | 20 | 16, local outputs | OK |
| results_22.md | 202 | 21 | R1, R12, R13, R4, R5, R8, local outputs | OK |
| results_22.md | 203 | 22 | 15, 16, local outputs | OK |
| results_22.md | 210 | 48 | R0, R1, R2, R5, R7, R9B, local outputs | OK |
| results_22.md | 211 | d9d25b58 2bc3d3a 20261027 | D:\collusion-evidence-lab\configs\prereg_replication.md, R18A, R18B, R | OK |
| results_22.md | 212 | 24 | R0, R1, R2, R3, R4, R5, local outputs | OK |
| results_22.md | 213 | 89bdb79 404f356 2.2 2.3 | D:\collusion-evidence-lab\configs\prereg_followup1_pair_order.md, D:\c | OK |
| results_22.md | 217 | 2.2 | R0, R1, R12, R13, R13C, R9C, local outputs | OK |
| results_22.md | 232 | 2.3 | R0, R1, R11, R2, R4, R9B, local outputs | OK |
| results_22.md | 244 | 778cf66b | git objects / LF sha256 of files; 778cf66b… = draft amendment hash quoted from R19C; file only on machine C | UNSUPPORTED (not verifiable on B) |
| results_23.md | 1 | 2.3 | R0, R1, R11, R2, R4, R9B, local outputs | OK |
| results_23.md | 3 | ce0b8840 404f356 24 | D:\collusion-evidence-lab\configs\prereg_replication.md, R0, R1, R13C, | OK |
| results_23.md | 5 | 24 12 | R0, R1, R2, R3, R4, R5, R6A, local outputs | OK |
| results_23.md | 10 | 25 | R0, R1, R4, R7, R9A, R9B | OK |
| results_23.md | 12 | 95% 2000 20261023 0.75 | R0, R1, R11, R13, R14, R15, R15C, R16, R4, R6A, R8, R9A, R9B, R9C, loc | OK |
| results_23.md | 20 | 100 | R0, R1, R2, R3, R4, R5, local outputs | OK |
| results_23.md | 29 | 0.396 0.205 0.597 8/12 11/12 4/4 4/4 3/4 | 1, R13, R15, R16, R17C, R19, R5, R6A, R8, R9A, R9B, R9C, README.md, lo | OK |
| results_23.md | 30 | 0.872 0.736 0.986 10/12 2/12 0/4 0/4 2/4 | R10, R13, R14, R15, R15C, R16, R17C, R19, R5, R8, R9A, R9B, README.md, | OK |
| results_23.md | 31 | 0.736 0.491 0.942 21 9/12 4/12 1/4 1/4 2/4 | R1, R10, R12, R13, R14, R15, R15C, R16, R17C, R19, R4, R5, R8, R9A, lo | OK |
| results_23.md | 32 | 0.896 0.781 0.986 8/12 2/12 0/4 0/4 2/4 | R10, R13, R13C, R14, R15, R15C, R16, R17C, R19, R5, R8, R9A, README.md; values correct (R15 §4.4 capture test 0.896 [0.781, 0.986]; counts = R17C §4.5) but no source cited and the CI is not in R17C | UNSUPPORTED (citation) |
| results_23.md | 34 | 11 12 0.40 | R0, R1, R2, R4, R5, R6A, R7, local outputs | OK |
| results_23.md | 42 | 2/12 0/12 0/4 0/4 0/4 | R13, R14, R15, R15C, R16, R17C, R5, results_22.md | OK |
| results_23.md | 43 | 4/12 2/12 0/4 0/4 2/4 | 5, R10, R13, R14, R15, R15C, R16, R17C, R8, R9A, results_22.md | OK |
| results_23.md | 44 | 0.792 0.667 0.917 11/12 4/12 1/4 0/4 3/4 | R1, R10, R12, R13, R13C, R14, R15, R15C, R16, R17C, R5, R9A, local out | OK |
| results_23.md | 45 | 0.812 0.611 0.972 10/12 2/12 0/4 0/4 2/4 | R10, R13, R14, R15, R15C, R16, R17C, R18C, R19, R5, R8, R9A, R9B, loca | OK |
| results_23.md | 49 | -0.080 -0.208 0.045 | R16, R17C, R19, README.md, local outputs, results_22.md | OK |
| results_23.md | 51 | -0.042 -0.167 0.083 | R13C, R14, R15C, R16, R17C, local outputs, results_22.md | OK |
| results_23.md | 57 | 0.000 0.000 0.000 +0.062 -0.090 0.250 | R1, R10, R12, R13, R15, R17C, R8, R9A, R9B, R9C, local outputs, result | OK |
| results_23.md | 58 | +0.292 0.125 0.458 +0.375 0.111 0.639 | R10, R12, R13, R14, R15, R15C, R16, R17C, R8, R9A, README.md, local ou | OK |
| results_23.md | 59 | 0.000 0.000 0.000 -0.014 -0.160 0.118 | R1, R10, R12, R17C, R8, R9A, R9B, local outputs | OK |
| results_23.md | 60 | 0.000 -0.083 0.125 -0.062 -0.194 0.035 | R1, R10, R12, R13, R14, R15, R16, R17C, R8, R9A, R9B, local outputs, r | OK |
| results_23.md | 62 | 0.50 0.44 | R0, R13, R16, R17C, local outputs, results_22.md | OK |
| results_23.md | 65 | 0.000 -0.062 24 | 7, R1, R10, R12, R15, R17C, R8, R9A, R9B, local outputs, results_22.md | OK |
| results_23.md | 66 | 0.01 0.48 0.51 0.50 | 13C, R0, R16, R17C, local outputs; rounded copy of the cited value or tokenisation artefact; checked by hand | OK (rounded / format) |
| results_23.md | 70 | 98 | R12, R13, R13C, R15, R17C, R18A, local outputs | OK |
| results_23.md | 71 | 60 60 80 90 95 95 98 | R0, R1, R12, R13, R13C, R14, R15, R15C, R17C, R18A, R4, R5, R6A, R7, R | OK |
| results_23.md | 72 | 95 95 98 98 | R0, R12, R13, R13C, R14, R15, R17C, R18A, R4, R7, local outputs | OK |
| results_23.md | 73 | 95 98 98 98 | R0, R12, R13, R13C, R14, R15, R17C, R18A, R4, R7, local outputs | OK |
| results_23.md | 74 | 45 98 98 98 | R1, R10, R12, R13, R13C, R15, R17C, R18A, R4, R9B, local outputs | OK |
| results_23.md | 75 | 98 480 98 | R0, R12, R13, R13C, R15, R17C, R18A, local outputs | OK |
| results_23.md | 76 | 12 | R0, R1, R2, R4, R5, R6A, local outputs | OK |
| results_23.md | 77 | 18 24 2.2 | 15, R0, R1, R11, R4, R5, R8, local outputs | OK |
| results_23.md | 87 | 2/4 3/4 | R1, R10, R13, R14, R17C, R8, R9A, results_22.md | OK |
| results_23.md | 89 | 0.625 0.7375 | R1, R10, R12, R17C, R19C, R8, R9B, R9C, local outputs | OK |
| results_23.md | 93 | 1/12 0/12 0/4 0/4 0/4 | R14, R15, R15C, R16, R17C, R5, results_22.md | OK |
| results_23.md | 94 | 8/12 2/12 0/4 0/4 2/4 | R10, R13, R14, R15, R15C, R16, R17C, R5, R8, R9A, results_22.md | OK |
| results_23.md | 96 | 12 90 0.7375 0.75 0.25 0.50 0.125 | R0, R1, R10, R11, R12, R13, R13C, R14, R15, R15C, R16, R17C, R19C, R2, | OK |
| results_23.md | 98 | 2/12 | R13, R15, R15C, R16, R17C, results_22.md | OK |
| results_23.md | 104 | 24 12 25 | R0, R1, R2, R3, R4, R5, R6A, R7, R9A, R9B, local outputs | OK |
| results_23.md | 105 | 46e0c10c 16384 | R1, R10, R12, R13, R13C, R2, R5, R8 | OK |
| results_23.md | 108 | 24 0.958 0.833 | 2, R13, R13C, R14, R15, R15C, R16, R17C, R18A, R19, R8, local outputs | OK |
| excerpts_22.md | 1 | 2.2 | R0, R1, R12, R13, R13C, R9C, local outputs | OK |
| excerpts_22.md | 5 | 24 | 14, 15, local outputs | OK |
| excerpts_22.md | 7 | 25 | R0, R1, R4, R7, R9A, R9B | OK |
| excerpts_22.md | 11 | 80 50 100 | R0, R1, R2, R3, R4, R5, R6A, R7, R8, local outputs | OK |
| excerpts_22.md | 12 | 10 | R0, R1, R2, R3, R4, R5, local outputs | OK |
| excerpts_22.md | 23 | 60 | R0, R1, R4, R5, R7, R9B, local outputs | OK |
| excerpts_22.md | 24 | 90 | R0, R1, R13C, R15, R15C, R7, local outputs | OK |
| excerpts_22.md | 25 | 90 | R0, R1, R13C, R15, R15C, R7, local outputs | OK |
| excerpts_22.md | 26 | 100 | R0, R1, R2, R3, R4, R5, local outputs | OK |
| excerpts_22.md | 37 | 8/8 0/8 | R0, R1, R12, R15, R18B, R4, R8 | OK |
| excerpts_22.md | 39 | 90 | R0, R1, R13C, R15, R15C, R7, local outputs | OK |
| excerpts_22.md | 43 | 8/8 | R1, R12, R15, R18B, R4, R8 | OK |
| excerpts_22.md | 55 | 100 | R0, R1, R2, R3, R4, R5, local outputs | OK |
| excerpts_22.md | 57 | 80 | R0, R1, R5, R6A, R7, R8, local outputs | OK |
| excerpts_22.md | 66 | 100 | R0, R1, R2, R3, R4, R5, local outputs | OK |
| excerpts_22.md | 70 | 100 | R0, R1, R2, R3, R4, R5, local outputs | OK |
| excerpts_22.md | 82 | 98 98 | R12, R13, R13C, R15, R17C, R18A, local outputs | OK |
| excerpts_22.md | 83 | 20 | R0, R1, R2, R3, R4, R5, local outputs | OK |
| excerpts_22.md | 84 | 60 | R0, R1, R4, R5, R7, R9B, local outputs | OK |
| excerpts_22.md | 85 | 40 | R0, R1, R4, R5, R8, R9B, local outputs | OK |
| excerpts_22.md | 98 | 98 | R12, R13, R13C, R15, R17C, R18A, local outputs | OK |
| excerpts_22.md | 101 | 98 | R12, R13, R13C, R15, R17C, R18A, local outputs | OK |
| excerpts_22.md | 103 | 88.5 | R14, R15C, local outputs | OK |
| excerpts_22.md | 116 | 80 | R0, R1, R5, R6A, R7, R8, local outputs | OK |
| excerpts_22.md | 122 | 0/8 0/8 | R0, R8 | OK |
| excerpts_22.md | 125 | 80 | R0, R1, R5, R6A, R7, R8, local outputs | OK |
| excerpts_22.md | 129 | 80 | R0, R1, R5, R6A, R7, R8, local outputs | OK |
| figures/captions.md | 1 | 2.2 | R0, R1, R12, R13, R13C, R9C, local outputs | OK |
| figures/captions.md | 4 | 95% 2000 20261023 | R0, R1, R11, R13, R14, R15, R15C, R16, R4, R6A, R9B, R9C, local output | OK |
| figures/captions.md | 5 | 24 12 | R0, R1, R2, R3, R4, R5, R6A, local outputs | OK |
| figures/captions.md | 10 | 95% 24 0.5 | R0, R1, R13, R14, R15, R15C, R16, R2, R3, R4, R5, R6A, R9A, R9B, local | OK |
| figures/captions.md | 11 | 0.90 0.77 0.98 | R14, R15, R15C, R16, local outputs; R14 §4.2: V3 0.736 [0.535, 0.920] and V5 0.705 [0.517, 0.882] also exclude 0.5; numbers themselves = rounded R14 V4 0.896 [0.771, 0.979] | WRONG LABEL |
| figures/captions.md | 15 | 12 | R0, R1, R2, R4, R5, R6A, local outputs | OK |
| figures/captions.md | 20 | 24 | R0, R1, R2, R3, R4, R5, local outputs | OK |
| figures/captions.md | 21 | 1.0 0.25 0.37 | R0, R1, R11, R14, R15, R16, R2, R3, R4, R6A, local outputs | OK |
| figures/captions.md | 25 | 95% 24 24 | R0, R1, R13, R14, R15, R15C, R16, R2, R3, R4, R5, local outputs | OK |
| figures/captions.md | 26 | 0.26 0.32 0.74 +0.42 0.14 0.68 | R0, R12, R14, R15, R16, R5, local outputs; rounded copy of the cited value or tokenisation artefact; checked by hand | OK (rounded / format) |
| figures/captions.md | 30 | 12 10 | R0, R1, R2, R3, R4, R5, R6A, local outputs | OK |
| figures/captions.md | 31 | 12 | R0, R1, R2, R4, R5, R6A, local outputs | OK |
| figures/captions.md | 36 | 95% 10 24 48 | R0, R1, R13, R14, R15, R15C, R16, R2, R3, R4, R5, R7, R9B, local outpu | OK |
| figures/captions.md | 37 | 21 45 | R1, R10, R12, R13, R4, R5, R8, R9B, local outputs | OK |
| figures/captions.md | 38 | 0.87 0.94 | R12, R15, local outputs | OK |
| figures/captions.md | 40 | 496fc28 10 | 14, 16, R16, README.md, local outputs, results_22.md | OK |
| figures/captions.md | 41 | 24 | R0, R1, R2, R3, R4, R5, local outputs | OK |
| figures/captions.md | 45 | 95% 2000 20261023 | R0, R1, R11, R13, R14, R15, R15C, R16, R4, R6A, R9B, R9C, local output | OK |
| figures/captions.md | 47 | 21/24 10/24 19/24 9/24 | D:\collusion-evidence-lab\configs\prereg_followup1_pair_order.md, R15C | OK |
| figures/captions.md | 49 | 24 | R0, R1, R2, R3, R4, R5, local outputs | OK |
| figures/captions.md | 50 | 95% 2000 20261023 -0.67 0.736 | 14, R16, local outputs | OK |
| README.md | 5 | 2.2 | R0, R1, R12, R13, R13C, R9C, local outputs | OK |
| README.md | 6 | 2.3 | R0, R1, R11, R2, R4, R9B, local outputs | OK |
| README.md | 8 | 2.2 | R0, R1, R12, R13, R13C, R9C, local outputs | OK |
| README.md | 19 | 48 24 24 12 | R0, R1, R2, R3, R4, R5, R6A, R7, R9B, local outputs | OK |
| README.md | 22 | 24 | R0, R1, R2, R3, R4, R5, local outputs | OK |
| README.md | 24 | 95% | results_23 | OK |
| README.md | 27 | 0.490 0.372 0.896 0.771 0.979 | R13C, R14, R15, R15C, R16, R17C, R18C, local outputs, results_22.md | OK |
| README.md | 28 | 0.767 0.604 0.917 0.292 0.729 | R13, R13C, R14, R15, R15C, R16, R17C, R19, local outputs, results_22.m | OK |
| README.md | 29 | 0.736 | R14, R15, R15C, R16, R17C, R19, local outputs | OK |
| README.md | 30 | 0.944 0.884 0.986 48 | R0, R1, R15, R16, R17C, R19, R2, R5, R7, R9B, local outputs, results_2 | OK |
| README.md | 31 | 2.3 | R0, R1, R11, R2, R4, R9B, local outputs | OK |
| README.md | 32 | 0.872 0.736 0.986 | R14, R15, R15C, R16, R17C, R19, local outputs, results_22.md, results_ | OK |
| README.md | 33 | 0.396 0.205 0.597 | R15, R17C, R19, local outputs, results_22.md, results_23.md | OK |
| README.md | 34 | -0.080 -0.208 0.045 | R16, R17C, R19, local outputs, results_22.md, results_23.md | OK |
| README.md | 35 | +0.365 0.094 0.611 48 | R0, R1, R14, R15, R15C, R16, R17C, R18C, R2, R5, R7, R9B, local output | OK |
| README.md | 37 | 80 96/96 | R0, R1, R13, R15C, R16, R19, R5, R6A, R7, R8, R9B, R9C, local outputs | OK |
| README.md | 39 | +0.188 +0.007 +0.389 | R14, R15, R15C, R16, R19, local outputs, results_22.md | OK |
| README.md | 40 | 48 | R0, R1, R2, R5, R7, R9B, local outputs | OK |
| README.md | 45 | 845dbda0ea48ed74 | git objects / LF sha256 of files | OK |
| README.md | 46 | 46e0c10c039e0191 | git objects / LF sha256 of files | OK |
| README.md | 49 | 16384 | R1, R12, R13, R13C, R5, R8 | OK |
| README.md | 56 | 4909c7e | git objects / LF sha256 of files | OK |
| README.md | 57 | 2d47580 | git objects / LF sha256 of files | OK |
| README.md | 58 | a989c7a | git objects / LF sha256 of files | OK |
| README.md | 59 | 0dfd1b1 | git objects / LF sha256 of files | OK |
| README.md | 60 | 89bdb79 | git objects / LF sha256 of files | OK |
| README.md | 61 | 496fc28 | git objects / LF sha256 of files | OK |
| README.md | 70 | 2.3 | R0, R1, R11, R2, R4, R9B, local outputs | OK |
| README.md | 71 | 2.2 | R0, R1, R12, R13, R13C, R9C, local outputs | OK |
