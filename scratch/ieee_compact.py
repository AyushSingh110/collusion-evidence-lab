"""Task 34: compact IEEE floats (no text change), page numbers, swap two author roles.
Usage: python scratch/ieee_compact.py writeup/paper.tex"""
import sys
from pathlib import Path

p = Path(sys.argv[1])
t = p.read_text(encoding="utf-8")


def sub(old, new):
    global t
    assert t.count(old) == 1, old
    t = t.replace(old, new)


# page numbers on every page (IEEEtran conference turns them off by default)
sub(r"\maketitle" + "\n", r"\maketitle" + "\n" + r"\thispagestyle{plain}" + "\n" + r"\pagestyle{plain}" + "\n")

# smaller full-width figures
sub(r"\resizebox{0.95\textwidth}{!}{%", r"\resizebox{0.85\textwidth}{!}{%")
sub(r"\includegraphics[width=\textwidth]{fig2_per_type_scores_test.png}",
    r"\includegraphics[width=0.85\textwidth]{fig2_per_type_scores_test.png}")
sub(r"\includegraphics[width=0.9\textwidth]{fig7_pair_order_followup.png}",
    r"\includegraphics[width=0.75\textwidth]{fig7_pair_order_followup.png}")
sub(r"\includegraphics[width=0.85\textwidth]{fig8_rq9_granite.png}",
    r"\includegraphics[width=0.7\textwidth]{fig8_rq9_granite.png}")
sub(r"\includegraphics[width=0.9\textwidth]{fig9_replication_22.png}",
    r"\includegraphics[width=0.75\textwidth]{fig9_replication_22.png}")

# two single-panel figures become one-column figures (half the page area)
sub("\\begin{figure*}[t]\n    \\centering\n    \\includegraphics[width=0.78\\textwidth]{fig1_auroc_by_view_test.png}",
    "\\begin{figure}[t]\n    \\centering\n    \\includegraphics[width=\\columnwidth]{fig1_auroc_by_view_test.png}")
sub("    \\label{fig:auroc}\n\\end{figure*}", "    \\label{fig:auroc}\n\\end{figure}")
sub("\\begin{figure*}[t]\n\\centering\n\\includegraphics[width=0.8\\textwidth]{fig10_replication_23.png}",
    "\\begin{figure}[t]\n\\centering\n\\includegraphics[width=\\columnwidth]{fig10_replication_23.png}")
sub("\\label{fig:repl23}\n\\end{figure*}", "\\label{fig:repl23}\n\\end{figure}")

# replication table in footnotesize
sub("\\begin{table*}[t]\n\\centering\\small\n\\caption{\\textbf{Study 1 replication}",
    "\\begin{table*}[t]\n\\centering\\footnotesize\n\\caption{\\textbf{Study 1 replication}")

# Ayush Singh and Param Bapu roles swapped (user correction)
sub("\\textbf{Ayush Singh} built the harness integration, the data pipeline, the generation runs and the LLM caching.\n"
    "\\textbf{Param Bapu} led the project, the research design and the pre-registrations.",
    "\\textbf{Ayush Singh} led the project, the research design and the pre-registrations. \\textbf{Param Bapu} built the\n"
    "harness integration, the data pipeline, the generation runs and the LLM caching.")

p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
