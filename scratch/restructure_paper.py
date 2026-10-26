"""Task 31: cut the paper body to ~8 pages.

Rebuilds section 4 (Study 1 results) with shorter text, moves Figures (test AUROC, per-type scores,
follow-up 1, RQ9) and the replication hypothesis table to a new appendix, removes \\FloatBarrier and
switches body floats to [t]. Every number is copied from the existing paper text (no new numbers).
Usage: python scratch/restructure_paper.py writeup/paper.tex
"""
import sys
from pathlib import Path

p = Path(sys.argv[1])
lines = p.read_text(encoding="utf-8").split("\n")


def block(start_pat, end_pat, frm=0):
    """Return (i, j) line indices of the first block from start_pat to end_pat (inclusive)."""
    i = next(k for k in range(frm, len(lines)) if start_pat in lines[k])
    j = next(k for k in range(i, len(lines)) if end_pat in lines[k])
    return i, j


def grab(label, kind):
    """Copy a float (figure/table) by its label, verbatim, as text."""
    lab = next(k for k, l in enumerate(lines) if f"\\label{{{label}}}" in l)
    i = max(k for k in range(lab) if f"\\begin{{{kind}}}" in lines[k])
    j = next(k for k in range(lab, len(lines)) if f"\\end{{{kind}}}" in lines[k])
    return "\n".join(lines[i:j + 1]).replace(f"\\begin{{{kind}}}[!htbp]", f"\\begin{{{kind}}}[!htbp]")


moved = {
    "fig:auroc": grab("fig:auroc", "figure"),
    "fig:pertype": grab("fig:pertype", "figure"),
    "fig:followup": grab("fig:followup", "figure"),
    "fig:granite": grab("fig:granite", "figure"),
    "tab:repl22": grab("tab:repl22", "table"),
    "fig:repl22": grab("fig:repl22", "figure"),
    "tab:views": grab("tab:views", "table"),
}

s4_start = next(k for k, l in enumerate(lines) if l.startswith("\\section{Results: Study 1"))
s5_start = next(k for k, l in enumerate(lines) if l.startswith("\\section{Results: Study 2"))
s5_start -= 1  # keep the "% ====" rule line that precedes section 5

new_s4 = r"""\section{Results: Study 1 (Monitor Views)}
\label{sec:22}

\subsection{Gates: does the dataset behave as intended? (RQ0.1--RQ0.4)}
\textbf{RQ0.1 -- Real collusion} passed under Amendment~1. Pilot~1 failed the frozen uptake criterion (2/4) even though
the transcripts suggested coordination in all 4 games: the rule missed brief instructions without `we/us' phrasing,
and one game drifted into Chinese. Amendment~1 introduced an English-only instruction and uptake rule~v2, and the
fresh Pilot~2 met every criterion: uptake 4/4, placebo false positives 0/2, the focal pair first by coGO in 4/4 games,
coalition advantage and capture in 4/4, and rule--hand-check agreement 96.9\% (Cohen's $\kappa=0.931$). Across the full
dataset, uptake was recorded in 24/24 games and uptake plus effect in 23/24 (the pilot-1 hand check is in
Appendix~\ref{app:extra}).
\textbf{RQ0.2 -- Lookalikes.} Type~3 behaved as intended in 7/8 games (one partial) and Type~4b in 6/8; all eight Type~4b
games mention the ``deposit'' in public, an unplanned cue visible to monitors.
\textbf{RQ0.3 -- Leakage} passed: no setup copies required removal, a search across 384 views found no leakage, and the
shuffled control stayed at chance (dev 0.465 [0.250, 0.667]; test 0.632 [0.431, 0.833]).
\textbf{RQ0.4 -- Stability} was met for V1, V3, V4 and V5 but not for V2 (mean absolute difference 5.00; Spearman
$\rho=0.676$). Collusion was not fully concealed: 6.5\% of focal public messages revealed joint action, and 12/24
Type~1 games contained at least one such disclosure.
% src: results_22.md RQ status table (R10 §B3-B4; R12 §4.3-4.5, §5; R13 §3-4; R14 §4.10).

\subsection{Original test set (RQ1--RQ8)}
Table~\ref{tab:views} compares the views on the 24-game test set (bar chart: Appendix Figure~\ref{fig:auroc}). V4 achieved
the highest AUROC (0.896 [0.771, 0.979]), while V1 was close to chance (0.490) and V2 fell below it (0.372).

""" + moved["tab:views"].replace("[!htbp]", "[t]") + r"""
% src: results_22.md RQ1 row and §g per-view table; R10a; capture test value R15 §4.4.

\textbf{Primary comparisons.} \emph{RQ2} (V3 minus the dev-chosen best single view, V2) was +0.365 [0.094, 0.611]. By the
pre-registered wording, combining helps, but the result is fragile: V2 failed RQ0.4, the pooled value was only +0.040
[$-$0.155, 0.238], and V2 alone moved by +0.188 between sessions. \emph{RQ5} found no clear advantage of the structured
view over the raw combined view (V4 $-$ V3 +0.160 [$-$0.021, 0.351]), but an advantage over a raw view of the same length
(V4 $-$ C-length +0.285 [0.017, 0.556]).
% src: results_22.md RQ2, RQ5 rows (R14 §4.3, §4.6; R15 §4.2; R16 §4.4).

\textbf{Other questions.} Each single view was fooled by one lookalike (RQ3). At the frozen thresholds V4 flagged
0/4 placebo, 2/4 persona and 1/4 shared-incentive games; V2 flagged 2/4, 3/4 and 2/4. Per-type AUROC showed
persona talk fooling actions (V2, T1 vs.\ T3 0.219 [0.00, 0.62]) and the shared incentive fooling messages
(V1, T1 vs.\ T4b 0.344 [0.12, 0.65]) (Appendix Figure~\ref{fig:pertype}). There was no clear evidence that the monitor
cross-checks words against actions (RQ4, V3 $-$ C-mismatch +0.188 [$-$0.028, 0.386]), and private plans added
nothing (RQ6, V5 $-$ V3 $-$0.031 [$-$0.267, 0.236]). The dependence code signal lost to V4 (RQ7, $-$0.173
[$-$0.382, $-$0.009], $n=21$), but the simpler action signals coGO, capture and $G_{\text{others}}$ matched V4
(exploratory). For naming the colluding pair (RQ8; chance 0.1), V4 was best with 7/12.
% src: results_22.md RQ3, RQ4, RQ6, RQ7, RQ8 rows (R14 §4.4-§4.9; R15 §4.4).

\subsection{Robustness: pair order and a second monitor}
\textbf{Pair order (Follow-up~1).} Llama gave the top score to the last-listed pair (T-Z) in 21/24 V1 and 17/24 V3 test
replies, although T-Z was the true pair in only 1 of 12 test collusion games. A pre-registered follow-up re-scored the
test games with the pair order randomised (Appendix Figure~\ref{fig:followup}). This cut the last-position effect to
10/24 (V1) and 9/24 (V3) but changed no view's AUROC clearly (V1 +0.017 [$-$0.229, +0.281], V3 +0.042 [$-$0.198, +0.285],
V4 $-$0.076 [$-$0.240, +0.111]). The bias is real, but it does not explain the raw-view failure; with a random order,
V4 named the correct pair in 8/12 games.
% src: results_22.md §d.2 (R15 §4.6; R16 §4.3); Follow-up 1 row (R16 §4.2, §4.7); RQ8 row (R16 §4.5).

\textbf{A second monitor (RQ9).} The same frozen prompt with \texttt{granite3.3:8b} produced a different ranking
(Appendix Figure~\ref{fig:granite}): V1 0.729 [0.549, 0.896], V2 0.767 [0.604, 0.917], V3 0.736 [0.573, 0.917] and V4
0.510 [0.292, 0.729] (Kendall $\tau$-b $-$0.667, a coarse measure with 4 views). Granite showed no preference for the
last position beyond ties. It ran on different hardware (Apple Metal vs.\ NVIDIA), so the effects of model and
hardware cannot be separated.
% src: results_22.md RQ9 row (R15C §4.2, §4.5, §8.1).

\subsection{Pre-registered replication on 48 new games}
Figure~\ref{fig:repl22} gives the replication with frozen prompts, one sample and one run per monitor (all hypotheses
with CIs: Appendix Table~\ref{tab:repl22}). There were no quality-fail games, so the sensitivity analysis equals the
primary one. \textbf{Replicated:} messages alone fail (R1), private plans add nothing (R8), the shuffled control is at
chance (R9), and the model-free capture signal works (R10a), now clearly better than the best LLM view (R10b, +0.264
[0.121, 0.412]). \textbf{Not replicated:} the structured report's advantage over the raw view (R4) and over a
same-length raw view (R5), and `persona talk fools actions' (R7). With llama, `combining beats actions' replicated (R3),
but only because llama's action view was below chance (0.324); with granite the action view was not reliably above
chance (G1), and only llama prefers the structured report (G3). Neither monitor reaches 0.7 on any view of the new games.
% src: results_22.md §g (R21 §4.2, §4.7; R22C §4.4).

""" + moved["fig:repl22"].replace("[!htbp]", "[t]") + r"""
% src: figures/captions.md Figure 9.
"""

lines[s4_start:s5_start] = new_s4.split("\n")

# appendix with the moved material, placed first in the appendix
appendix_extra = r"""\section{Additional Study 1 results}
\label{app:extra}
\textbf{Pilot-1 hand check (RQ0.1, descriptive).} Two raters, blind to the rule, hand-checked pilot~1. They agreed on
91.7\% of the cases ($\kappa=0.80$); rule~v2 agreed with them on 79.2\% and 85.4\%. Every disagreement was a missed
detection of coordination; there were no false alarms.
% src: results_22.md RQ0.1 (R10 §B3).

""" + "\n\n".join(moved[k] for k in ("fig:auroc", "fig:pertype", "fig:followup", "fig:granite", "tab:repl22")) + "\n\\FloatBarrier\n"

app = next(k for k, l in enumerate(lines) if l.strip() == "\\appendix")
lines[app + 1:app + 1] = appendix_extra.split("\n")

text = "\n".join(lines)
# body floats: drop barriers before the appendix, use [t]
body, appx = text.split("\\appendix", 1)
body = body.replace("\\FloatBarrier\n", "").replace("\\begin{figure}[!htbp]", "\\begin{figure}[t]") \
           .replace("\\begin{table}[!htbp]", "\\begin{table}[t]")
p.write_text(body + "\\appendix" + appx, encoding="utf-8", newline="\n")
print("ok; FloatBarrier left in body:", body.count("FloatBarrier"))
