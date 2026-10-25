# 19 — Write-up update: RQ9 and Study 2.3 added (no model calls)

Date: 2026-10-25 · Task 19 · Machine B · **No model calls** (replication generation is running on this GPU). Only `writeup/results_22.md`, `README.md` and notes were edited. Numbers are copied from reports 15C, 15, 16, 13 and `writeup/results_23.md` (17C), with report and section cited; nothing was recomputed.

## 1. Goal (from the prompt)

- Add RQ9 (granite3.3:8b) and the Study 2.3 link to `results_22.md`:
  - an RQ9 row;
  - an "RQ9 granite" robustness column with "(llama only)" labels;
  - a monitor-dependent headline;
  - a link to Study 2.3;
  - a replication section with results marked TBD.
- Update the README headline accordingly.

## 2. What was changed

| File | Change |
|---|---|
| `writeup/results_22.md` §a | Headline replaced with the monitor-dependent version: llama V1 / V2 fail and V4 best vs granite V2 0.767 / V4 0.510, τ −0.667; V3 0.736 with both; capture 0.944 pooled; reliability problems (constant 80 on 96/96, llama last-position bias, V2 session effect +0.188); RQ2 fragile and not holding with granite. **"Link to Study 2.3" paragraph** (R2 0.872, R1 0.396, R6 − R2 −0.080 [−0.208, 0.045] "no clear difference"). |
| `results_22.md` §b | RQ9 row: granite AUROCs with CIs (R15C §4.2), τ-b −0.667 with the resolution note (4 views, 6 pairs), verdict "view ranking is monitor-dependent". |
| `results_22.md` §c | New "RQ9 granite (R15C)" column. Per-claim status from R15C §4.2–4.5. "(llama only)" added where granite does not reproduce the claim. Position bias relabelled "llama-specific (RQ9: granite shows no last-position preference beyond ties)". |
| `results_22.md` §e | Two stale "RQ9 pending" lines updated: the limitation now cites the RQ9 result and the hardware confound (R15C §8); next-step 1 is marked done. |
| `results_22.md` §g (new) | "Replication (in progress)": R1–R10 and E1–E4 + E3b from `configs/prereg_replication.md`, and G1–G4 from the draft amendment, all **TBD**. |
| `README.md` | Headline findings replaced with the new monitor-dependent version (numbers from results_22 / results_23), plus one line that a pre-registered replication on 48 new games is in progress. 97 lines. |

**RQ9 column, claim by claim:**

| Claim | Granite result | Label |
|---|---|---|
| Messages fail | does not hold (0.729) | ROBUST (llama only) |
| Actions fail | does not hold (0.767) | ROBUST (llama only) |
| Combining helps | does not hold (−0.031) | FRAGILE (llama only) |
| Structure beats raw | does not hold (−0.226) | FRAGILE (llama only) |
| Structure beats same length | C-length not scored; granite V4 at chance (0.510) | ROBUST (llama only) |
| Private plans | not measured (V5 not scored) | CONSISTENT NULL (unchanged) |
| Same-incentive fools messages | does not hold (0.812) | ROBUST (llama only) |
| Persona fools actions | does not hold (0.833) | FRAGILE (llama only) |
| Code signals | model-free, not applicable | unchanged |
| Position bias exists | llama-specific | llama-specific (RQ9: granite shows no last-position preference beyond ties) |
| Position bias explains failure | — | NOT SUPPORTED (unchanged) |

## 3. How it was verified

- Every new number was checked by `grep` against its source: R15C (11 values; one, 0.812 [0.604, 0.958], is bold in the source, hence a literal-match miss), `results_23.md` (3 values) and R15 §4.4 (capture 0.944 [0.884, 0.986]).
- README line count: 97.

## 4. Results

- No new numbers were computed.
- **Write-up changes:** in `results_22.md`, 1 headline rewritten, 1 table row replaced, 1 column added (11 rows), 2 stale lines updated and 1 section added; the README headline was rewritten.

## 5. Acceptance criteria

| Item | Status | Evidence |
|---|---|---|
| RQ9 row with granite AUROCs and CIs, τ-b with low-resolution note, verdict | **PASSED** | §b |
| Robustness "RQ9 granite" column; "(llama only)" suffixes; position-bias label as specified | **PASSED** | §c |
| Monitor-dependent headline with the specified numbers | **PASSED** | §a |
| Link to Study 2.3 with R2 / R1 / R6 − R2 | **PASSED** | §a |
| Replication section, R1–R10, E1–E4/E3b, G1–G4, all TBD | **PASSED** (G1–G4 by name only, see §6) | §g |
| README headline + replication line, numbers only from the write-up files | **PASSED** | README |
| No model calls; only allowed files | **PASSED** | `git status` |

## 6. Deviations

1. **G1–G4 are listed by name only.** `configs/prereg_replication_amendment1.md` is not on machine B: it is an uncommitted DRAFT on machine C (report 19C, LF sha256 `778cf66b…7cbf7`). Their wording was not copied, so as not to invent it; the section points to the draft and marks it non-binding until committed.
2. **Two stale RQ9 lines in §e were updated** (outside the four listed items, but they contradicted the new RQ9 row).
3. **"Structure beats same length"** got "(llama only)" even though granite did not score C-length: granite's V4 is at chance, so the claim's premise (a working structured report) fails with granite. This is written in the cell.

## 7. Open problems

- §d (monitor reliability) still describes the position bias without the RQ9 qualifier. The headline and §c carry it; a one-line note in §d is a possible follow-up.
- The README and §g need updating when the replication results arrive.

## 8. Next task

The replication pipeline, after generation finishes (report 18c §8).

## 9. Files to commit

- `writeup/results_22.md`, `README.md`
- `notes/DEVLOG.md`, `notes/reports/19_writeup_update.md`

## 10. Commit line

`Commit: docs: add RQ9 (granite) and Study 2.3 to the Study 2.2 write-up and README`
