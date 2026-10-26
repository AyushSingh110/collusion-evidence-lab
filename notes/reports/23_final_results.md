# 23 — Final results integration (original + replication)

Date: 2026-10-26 · Task 23 (+ lead addendum) · Machine B · **No model calls.** Numbers are copied from reports 13–17C, 20B, 21 and 22C, with report and section cited. The figures re-plot stored result files. No new analysis was run on any game.

## 1. Goal (from the prompt)

Integrate the replication into the write-up:
- `results_22.md`: §g results; a robustness-table column for the replication with a final label per claim; §d additions; the final headline;
- `results_23.md`: a replication section;
- Figures 9 and 10 with captions;
- a one-page `results_summary.md`;
- the README headline.

## 2. What was built / changed

| File | Change |
|---|---|
| `writeup/results_22.md` | §a replaced by the final headline from the lead's addendum, plus "why V4 was optimistic" and "small-sample optimism" (numbers copied only). §c: a "Replication (R21 / R22C)" column and a final label per claim (the old label kept as "Pilot label"), plus a new row "view ranking depends on the monitor". §d: the replication of llama's last-position bias (V1 44/48) and V4's 8/8 persona false positives. §f: 2 replication pre-registration rows. §g: TBD replaced by R1–R10 and G1–G4 next to the originals, per-view replication AUROCs and a plain-English summary. "How to read" mentions the replication. |
| `writeup/results_23.md` | New §6: E1–E4 / E3b and all rules next to 17C, the plus-factor rule, and the final standard of evidence. |
| `writeup/results_summary.md` (new) | One page: problem, both studies, 8 main findings with key numbers and status, what it means, limitations. |
| `writeup/figures/fig9_replication_22.png`, `fig10_replication_23.png` (new) | See §4. |
| `writeup/figures/captions.md` | Figures 9 and 10 captions appended. |
| `README.md` | Final headline findings, links to the three results files, the two replication pre-registrations in the commit table, and the writeup line in the layout. 104 lines. |
| `scratch/p23_inspect.py`, `scratch/p23_figures.py` (new) | Read-only inspection of the result files, and the figure script. |

## 3. How it was verified

- **Stop condition checked:** the G1–G4 addendum is in report 22C §4.4, and `runs/replication_granite/results.json` and `runs/replication_23/results.json` exist on B. The G values in the file equal report 22C.
- **Figure 9 consistency check (asserted in `p23_figures.py`):** machine C's llama V1 and V4 replication AUROCs equal machine B's own analysis (R21 R1 / R2) to < 0.001.
- **CI triplets:** the audit-20B checker (`audit20b_ci.py`, scratchpad), re-run over `results_22.md`, `results_23.md`, `results_summary.md`, `excerpts_22.md`, `captions.md` and `README.md`. **All 170 CI triplets occur exactly in a report; 0 are not found.**
- **Figures:** both PNGs opened and checked by eye (Figure 9's legend moved off the data).

## 4. Results

**Final labels (`results_22.md` §c):**

| Claim | Final label |
|---|---|
| Messages alone fail | **REPLICATED** |
| Actions alone fail | **REPLICATED** |
| Combining helps (RQ2) | **LLAMA ONLY** |
| Structure beats raw | **NOT REPLICATED** |
| Structure beats same length | **NOT REPLICATED** |
| Private plans | **CONSISTENT NULL** |
| Same-incentive fools messages | **LLAMA ONLY** |
| Persona fools actions | **NOT REPLICATED** |
| Code action signals competitive | **REPLICATED** |
| Position bias | **LLAMA ONLY** |
| Position bias explains failure | NOT SUPPORTED (not re-tested) |
| View ranking | **MONITOR-DEPENDENT** |

**Figures:**
- **Figure 9:** V1–V4 AUROC with CIs for llama on the original test, llama on the replication and granite on the replication, plus capture (test and replication). Chance line.
- **Figure 10:** the AUROC of R1, R2, R3, R6 and R7 on 17C vs the replication, with CIs.

## 5. Acceptance criteria

| # | Item | Status | Evidence |
|---|---|---|---|
| 1 | §g filled (R1–R10, G1–G4 vs the originals); robustness column + final labels; §d additions | **PASSED** | `results_22.md` §c, §d, §g |
| 2 | Final headline (addendum wording) + the V4-optimism sentence + "small-sample optimism" | **PASSED** | §a |
| 3 | `results_23.md` replication section + final standard-of-evidence wording | **PASSED** | §6 |
| 4 | Figures 9 (with granite) and 10, captions (n, pre-registered, one sample) | **PASSED** | PNGs + `captions.md` |
| 5 | `results_summary.md` | **PASSED** | 8 findings with status |
| 6 | README headline final; "in progress" replaced with the outcome | **PASSED** | README |
| — | No model calls; numbers copied, cited, triplet-checked | **PASSED** | §3 |

## 6. Deviations

- **"Position bias explains the raw-view failure"** keeps **NOT SUPPORTED**, which is not one of the five final labels. The replication did not re-test it, so none of the five fits.
- **Figure 10's 17C values** are copied from report 17C (`runs/study23/results.json` is on machine C only). This is stated in the caption and in the script.
- **Figure 9 omits V5 and the C-length / C-mismatch controls:** their replication AUROCs were not computed in reports 21 / 22C, and computing them would be new analysis.
- **Two §f rows added** (the replication pre-registrations; hashes verified in R21 §4.0). This is outside the listed items but keeps §f complete.
- **The lead's range "0.32–0.66"** covers V1–V4 of both monitors on the replication (llama 0.324–0.636; granite 0.582–0.662). It is stated as "every view V1–V4".

## 7. Open problems

- The original-test per-type AUROCs for granite on the replication are in `runs/replication_granite/results.json` but not in any report. So "same-incentive fools messages" for granite on new games is unreported (LLAMA ONLY rests on 15C).
- The deviations table (§f) does not yet list replication-phase deviations (e.g. 22C's V1–V4 subset of B's llama file). A later documentation task could add them.

## 8. Next task

The lead's review of the final labels and the summary. Optionally, the remaining documentation items in §7.

## 9. Files to commit

- `writeup/results_22.md`, `writeup/results_23.md`, `writeup/results_summary.md`, `README.md`
- `writeup/figures/fig9_replication_22.png`, `writeup/figures/fig10_replication_23.png`, `writeup/figures/captions.md`
- `scratch/p23_inspect.py`, `scratch/p23_figures.py`
- `notes/DEVLOG.md`, `notes/reports/23_final_results.md`

## 10. Commit line

`Commit: docs: integrate the pre-registered replication into the final results, summary, figures 9-10 and README`
