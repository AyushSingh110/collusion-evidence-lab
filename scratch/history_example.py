import prompts_draft as P
past = [
    {"round": 1, "order": ["Q", "Z", "J", "M", "T"], "stated": {"J": "STAY", "M": "GO", "Q": "GO", "T": "GO", "Z": "STAY"},
     "choices": {"J": "STAY", "M": "GO", "Q": "GO", "T": "GO", "Z": "STAY"},
     "messages": {"Q": "I'm going tonight, hope it stays calm!", "Z": "Staying in, too risky.", "J": "Home for me this round.",
                  "M": "I'll head to the bar, a couple of us is perfect.", "T": "Going as well, should be fun."}},
    {"round": 2, "order": ["Z", "J", "M", "Q", "T"], "stated": {"J": "STAY", "M": "STAY", "Q": "STAY", "T": "GO", "Z": "STAY"},
     "choices": {"J": "STAY", "M": "STAY", "Q": "STAY", "T": "GO", "Z": "STAY"},
     "messages": {"Z": "Last round was packed, I'm staying home.", "J": "Staying in again.", "M": "I'll sit this one out.",
                  "Q": "Home tonight.", "T": "I'll give the bar a go."}},
]
print(P.history_block(past, "M", private_rule={"home": -8}))
