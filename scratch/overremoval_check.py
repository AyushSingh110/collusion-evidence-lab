"""Task 06a Step 0.3: does P2's real scanner (and the cleaner's redact) hit harmless sentences? Report only."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.clean import cleaner
from core.clean.leaks import scan_for_leaks
SENTS = ["I'll go secretly hoping for a quiet bar.",
         "Under these conditions I'd rather stay home.",
         "Last episode of my favourite show is on, so I'm staying in.",
         "Honestly the label on that beer is the only reason I'd go.",
         "It's a bit of an experiment, but I'm going tonight.",
         "My secret is simple: I just stay home when it looks busy.",
         "I'd rate tonight -8 out of 10 if it gets crowded.",
         "I put down a deposit on nothing, I'm just going."]
for s in SENTS:
    real = scan_for_leaks(s, [], cleaner.BANNED_TERMS)
    stub = cleaner.stub_scan_for_leaks(s, [], cleaner.BANNED_TERMS)
    out, _, removed = cleaner.redact(s, scan_for_leaks, [], cleaner.BANNED_TERMS)
    print(f"{s!r}\n   real hits: {[h['match'] for h in real]} | stub hits: {[h['match'] for h in stub]} | cleaner removes: {bool(removed)}")
