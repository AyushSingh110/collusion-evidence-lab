"""Task 35: restore the team's humanized wording in the paragraphs rewritten in Task 33, and keep the
appendix in two columns (no page break after the references).
Only two content corrections stay: the Follow-up 1 V1 count (source: results_22.md §d.2, 21/24 -> 10/24)
and "fool the LLM Judge" -> "fool them" (the shared incentive fools the outcome signals, not the judge).
Usage: python scratch/restore_wording.py writeup/paper.tex"""
import sys
from pathlib import Path

p = Path(sys.argv[1])
t = p.read_text(encoding="utf-8")


def sub(old, new):
    global t
    assert t.count(old) == 1, old[:80]
    t = t.replace(old, new)


# --- Introduction, paragraph 1 (only "An the auditor" -> "The auditor")
sub(r"""workflows involving multiple agents. When two of them act in coordination with one another, the damage can be serious
(in the form of higher prices, a resource that has been captured or a competitor that has been displaced), and the agents
may never openly acknowledge the coordination. An auditor normally keeps records of what the agents said in public,
what actions they took and the results that followed. The practical question is what action to take regarding those logs.""",
r"""workflows involving multiple agents; when two of them act in coordination with one another, the damage can be serious (in the form of higher prices,
a resource that has been captured and a competitor that has been displaced) may never officially acknowledge the coordination.
The auditor normally keeps records of what the agents said in public, what actions they took and the results that displayed.
The practical question is what action to take regarding those logs.""")

# --- contribution 2 (team wording)
sub(r"""\item \textbf{A view comparison for LLM monitors with controls, a second monitor model and a pre-registered
replication on 48 new games.} The view which appeared best in the original test, a structured report built with
code, failed to replicate, while a model-free behaviour signal did and clearly outperformed all the LLM views.""",
r"""\item \textbf{A view comparison for LLM monitors with controls, a second monitor model and a pre-registered}
{The view which appeared best in the original test was one that was built with code on 48 new games.}
The report failed to do so, while a model-free behaviour signal did and clearly outperformed all the LLM views.""")

# --- game payoffs (team wording; "i.e" -> "i.e.")
sub(r"""(if fewer than half go, i.e.\ at most 2 of 5)""", r"""(if fewer than half, i.e.\ go at most 2 of 5)""")

# --- RQ2 / RQ5 (team wording)
sub(r"""\textbf{Primary comparisons.} \emph{RQ2} (V3 minus the dev-chosen best single view, V2) was +0.365 [0.094, 0.611].
By the pre-registered wording, `combining helps', but the result is fragile: V2 failed RQ0.4, the pooled value was only
+0.040 [$-$0.155, 0.238], and V2 alone moved by +0.188 between sessions. \emph{RQ5} found no clear advantage of the
structured view over the raw combined view (V4 $-$ V3 +0.160 [$-$0.021, 0.351]), but an advantage over a raw view of
the same length (V4 $-$ C-length +0.285 [0.017, 0.556]).""",
r"""\textbf{Primary comparisons.} \emph{RQ2} (V3, with the dev-chosen best single view excluded, V2) was +0.365 [0.094, 0.611]:
The fact that `combining helps' is indicated by the pre-registered term yet it is fragile since V2 failed RQ0.4 means that the pooled value was
It increased by +0.040 [$-$0.155, 0.238] and V2 alone rose by +0.188 between sessions. RQ5 found no clear advantage with respect to
a preference for the structured view (V4 $-$ V3 +0.160 [$-$0.021, 0.351]) as compared with a raw view of the
same length (V4 $-$ C-length +0.285 [0.017, 0.556]).""")

# --- Follow-up 1 (team wording; V1 count corrected to the source)
sub(r"""Llama gave the top score to the last-listed pair (T-Z) in 21/24 V1 and 17/24 V3 test replies, although T-Z was the
true pair in only 1 of 12 test collusion games. A pre-registered follow-up re-scored the test games with the pair
order randomised (Fig.~\ref{fig:followup}). Randomisation cut the last-position effect to 10/24 replies in V1 and 9/24
in V3, but there was no clear change in the AUROC of any view (V1 +0.017 [$-$0.229, +0.281], V3 +0.042 [$-$0.198,
+0.285], V4 $-$0.076 [$-$0.240, +0.111]). Although the bias is real, it does not account for the raw-view failure;
when the order was chosen at random, V4 identified the correct pair in 8 out of 12 games.""",
r"""Llama gave the top score to the last-listed pair (T-Z) in 21/24 V1 and 17/24 V3 test replies, although T-Z was the
true pair in only one out of the twelve test collusion games; a pre-registered follow-up re-scored the test games involving the pair.
The order was randomised (see Fig.~\ref{fig:followup}). Randomisation eliminated the last-position effect in V1 (21 out of 24, now 10 out of 24)
and for V3 it was 19 out of 24 (now 9 out of 24), but there was no clear change in the AUROC for either one (V1 +0.017 [$-$0.229, +0.281], V3
+0.042 ($-$0.198 to +0.285), V4 $-$0.076 ($-$0.240 to +0.111)). Although the bias is real, it does not account for the raw-view.
There was a failure; when the order was chosen at random, V4 identified the correct pair in 8 out of 12 games.""")

# --- RQ9 (team wording)
sub(r"""$-$0.667, a coarse measure with 4 views). Granite had no preference for the last position other than in the case of
ties. Since different hardware""",
r"""$-$0.667 (a coarse measure with 4 views)); granite had no preference for the last position other than in the case of ties. Granite continued to run.
Since different hardware""")

# --- replication paragraph (team wording; only the doubled "the The" removed)
sub(r"""Table~\ref{tab:repl22} and Fig.~\ref{fig:repl22} give the replication with frozen prompts, one sample and one run
per monitor; since there were no quality-fail games, the sensitivity analysis is the same as the primary one.
\textbf{Replicated:} messages alone fail (R1), private plans add nothing (R8), the shuffled control is at chance (R9),
and the model-free capture signal works (R10a) and is now clearly doing better than the best LLM view (R10b, with an
improvement of +0.264 [0.121, 0.412]). \textbf{Not replicated:} the structured report's advantages over the raw view
(R4) and over a same-length raw view (R5), and `persona talk fools actions' (R7). With llama, `combining beats
actions' was reproduced (R3), but only because llama's action view was below chance (0.324); with granite, the action
view was not reliably above chance (G1), and only llama prefers the structured report (G3). Neither of the monitors
reaches 0.7 on any view of the new games.""",
r"""Table~\ref{tab:repl22} and Fig.~\ref{fig:repl22} give the replication with frozen prompts, one sample and one run
per monitor; since there were no quality fail games the sensitivity analysis is the same as the primary one. Replicated:
messages alone fail (R1), private plans add nothing (R8), the shuffled control is at chance (R9), and the
model-free capture signal works (R10a) and is now clearly doing better than the best LLM view (R10b, with an improvement of +0.264 [0.121, 0.412]).
\textbf{Not replicated}: the structured report's advantages over the raw view (R4) and over a same-length raw view
Regarding `persona talk fools actions' (R7), with Llama `combining beats actions' was reproduced (R3) but only\ldots
The action view for Llama was below chance (0.324); with Granite, it was not consistently above chance.
The llama is the only one that prefers the structured report. Neither of the monitors reaches 0.7 in any of the new games.""")

# --- Study 2 opening (team wording; only "the LLM Judge" -> "them")
sub(r"""\textbf{Single families (test, $n=24$; Table~\ref{tab:rules}).} Talk alone (the agents' public messages) is not
evidence: the judge flagged 11 of 12 innocent games and ranked below chance (0.396). On the other hand, outcomes rank
the games really well, but the shared-incentive lookalike is still able to fool them:""",
r"""\textbf{Single families (test, $n=24$; Table~\ref{tab:rules}).} Agents' public channel messages, that is, Talk alone is not
evidence: the judge flagged 11 of 12 innocent games and ranked below chance (0.396). On the other hand, Outcomes rank
the games really well, but the shared-incentive lookalike is still able to fool them:""")

# --- Discussion (team wording)
sub(r"""\emph{what the agents did} carried the
signal""", r"""\emph{what the agents did} was that they carried the
signal""")
sub(r"""best LLM view on the first test did not survive.""", r"""best LLM view which was on the first test did not survive.""")

# --- appendix stays in two columns: no \onecolumn page break; deviation table as supertabular
sub("\\usepackage{booktabs,tabularx,longtable,multirow,array}",
    "\\usepackage{booktabs,tabularx,longtable,multirow,array}\n\\usepackage{supertabular}        % long table that breaks across columns")
sub("% Appendices: one column, so the long deviation table can break across pages.\n\\onecolumn\n\\appendices",
    "% Appendices in two columns, directly after the references (no forced page break).\n\\appendices")

# longtable -> supertabular at column width
lt_start = t.index("\\begin{longtable}")
lt_end = t.index("\\end{longtable}") + len("\\end{longtable}")
body = t[lt_start:lt_end]
rows = body.split("\\endfoot\n", 1)[1].rsplit("\\end{longtable}", 1)[0]
head = "\\# & What & Why & When\\\\"
st = ("\\tablefirsthead{\\toprule " + head + " \\midrule}\n"
      "\\tablehead{\\toprule " + head + " \\midrule}\n"
      "\\tabletail{\\midrule}\n"
      "\\tablelasttail{\\bottomrule}\n"
      "\\begin{supertabular}{@{}p{0.05\\columnwidth}p{0.36\\columnwidth}p{0.25\\columnwidth}p{0.26\\columnwidth}@{}}\n"
      + rows + "\\end{supertabular}")
t = t[:lt_start] + st + t[lt_end:]
sub("{\\footnotesize\nItems 1--12", "{\\scriptsize\nItems 1--12")
sub("\\setlength{\\tabcolsep}{3pt}\n\\setlength{\\emergencystretch}{1em}\n\\tablefirsthead",
    "\\setlength{\\tabcolsep}{2pt}\n\\setlength{\\emergencystretch}{1em}\n\\par\\medskip\\noindent\n\\tablefirsthead")

# reproducibility table: full width at the top of a page (too wide for one column)
sub("{\\small\n\\noindent\\begin{tabularx}{\\textwidth}{@{}lllY@{}}",
    "{\\small\n\\begin{table*}[t]\n\\centering\\small\n\\caption{Pre-registration chain: commits and file hashes.}\n\\label{tab:prereg}\n\\begin{tabularx}{\\textwidth}{@{}lllY@{}}")
sub("Replication amendment 1 (granite) & 306502e & 778cf66b03bdea1f & before any replication view was rendered\\\\\n\\bottomrule\n\\end{tabularx}",
    "Replication amendment 1 (granite) & 306502e & 778cf66b03bdea1f & before any replication view was rendered\\\\\n\\bottomrule\n\\end{tabularx}\n\\end{table*}")
sub("\\noindent\\textbf{Frozen inputs for the replication:}", "\\noindent The commits and hashes of every pre-registration are listed in Table~\\ref{tab:prereg}.\n\\textbf{Frozen inputs for the replication:}")
sub("\\begin{Verbatim}[fontsize=\\small,breaklines=true,breakanywhere=true]", "\\begin{Verbatim}[fontsize=\\scriptsize,breaklines=true,breakanywhere=true]")

p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
