"""Task 27: remove sprint/track mentions from writeup/paper.md (mirror of the paper.tex edits)."""
from pathlib import Path
p = Path(__file__).resolve().parents[1] / "writeup" / "paper.md"
t = p.read_text(encoding="utf-8")
subs = [
    ("# Behaviour Beats Judgement: Auditing Collusion Between LLM Agents with Monitor Views and Antitrust-Style Evidence¹",
     "# Behaviour Beats Judgement: Auditing Collusion Between LLM Agents with Monitor Views and Antitrust-Style Evidence"),
    ("**Author name 1** (Affiliation) · **Author name 2** (Affiliation) · **Author name 3** (Affiliation)\n**With** Apart Research\n\n"
     "¹ Research conducted at the [AI Collusion Research Sprint](https://apartresearch.com/sprints/ai-collusion-research-sprint-2026-10-23-to-2026-10-25), October 2026.\n",
     "**Author name 1** (Affiliation) · **Author name 2** (Affiliation) · **Author name 3** (Affiliation)\n"),
    ("The sprint's Track 2 (Detection and Audit of Collusion) poses two questions that we study on one shared dataset:",
     "We study two questions on one shared dataset:"),
    ("- **2.2 Say vs. do.**", "- **Study 1 — say vs. do.**"),
    ("- **2.3 Standard of evidence.**", "- **Study 2 — standard of evidence.**"),
    ("Competition law offers a useful frame for 2.3.", "Competition law offers a useful frame for Study 2."),
    (" *(Teams: edit this statement to describe your own final writing process.)*", ""),
]
for old, new in subs:
    assert t.count(old) == 1, old[:60]
    t = t.replace(old, new)
p.write_text(t, encoding="utf-8", newline="\n")
print("ok")
