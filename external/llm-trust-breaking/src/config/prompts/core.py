"""Core prompt components shared across all games."""

# ============================================================================
# GAME RULES
# ============================================================================

GAME_RULES = {
    "coordination": {
        "description": (
            "After DM conversations, each agent secretly points to one other agent. "
            "The longest COMPLETE CYCLE wins and splits $100 equally. "
            "A cycle means a closed loop (e.g., A->B->C->A). "
            "Agents who point INTO a cycle but aren't part of it get nothing."
        ),
        "goal": "Maximize your own profit by being part of the longest cycle.",
        "phases_normal": (
            "IMPORTANT: This game has TWO phases:\n"
            "1. DISCUSSION PHASE (multiple rounds): You send DMs to coordinate\n"
            "2. DECISION PHASE (happens once, AFTER all discussion): You make ONE final pointing decision"
        ),
        "phases_hybrid": (
            "IMPORTANT: This game has FOUR phases:\n"
            "1. OPENING PUBLIC DISCUSSION (1 round): All agents speak publicly in turn\n"
            "2. PRIVATE DM PHASE (multiple rounds): You send DMs to coordinate privately\n"
            "3. CLOSING PUBLIC DISCUSSION (1 round): Final public round where you can say anything\n"
            "4. DECISION PHASE (happens once, AFTER all discussion): You make ONE final pointing decision"
        )
    },
    "fishing": {
        "description": lambda params: (
            f"There are {params['total_fish']} fish in a shared lake with {params['num_agents']} agents. "
            f"Each agent decides how many fish to catch. "
            f"If the TOTAL caught by all agents exceeds {params['collapse_threshold']}, "
            f"the lake collapses and EVERYONE gets 0. "
            f"Otherwise, each agent keeps what they caught."
        ),
        "goal": "Maximize your own catch while avoiding collapse.",
        "phases_normal": (
            "IMPORTANT: This game has TWO phases:\n"
            "1. DISCUSSION PHASE (multiple rounds): You communicate to coordinate\n"
            "2. DECISION PHASE (happens once, AFTER all discussion): You decide how many fish to catch"
        ),
        "phases_hybrid": (
            "IMPORTANT: This game has FOUR phases:\n"
            "1. OPENING PUBLIC DISCUSSION (1 round): All agents speak publicly in turn\n"
            "2. PRIVATE DM PHASE (multiple rounds): You communicate privately to coordinate\n"
            "3. CLOSING PUBLIC DISCUSSION (1 round): Final public round where you can say anything\n"
            "4. DECISION PHASE (happens once, AFTER all discussion): You decide how many fish to catch"
        )
    },
    "publicgoods": {
        "description": lambda params: (
            f"Each of {params['num_agents']} agents starts with {params['initial_tokens']} tokens. "
            f"Agents simultaneously decide how many tokens (0-{params['initial_tokens']}) to contribute to a shared pool. "
            f"The pool is multiplied by {params['multiplier']}x and split equally among ALL agents. "
            f"Each agent's final payout = (tokens kept) + (share of multiplied pool)."
        ),
        "goal": "Maximize your own final token count.",
        "phases_normal": (
            "IMPORTANT: This game has TWO phases:\n"
            "1. DISCUSSION PHASE (multiple rounds): You communicate to coordinate\n"
            "2. DECISION PHASE (happens once, AFTER all discussion): You decide your contribution"
        ),
        "phases_hybrid": (
            "IMPORTANT: This game has FOUR phases:\n"
            "1. OPENING GROUP DISCUSSION (1 round): All agents speak in turn\n"
            "2. PRIVATE DM PHASE (multiple rounds): You communicate privately to coordinate\n"
            "3. CLOSING GROUP DISCUSSION (1 round): Final round where you can say anything\n"
            "4. DECISION PHASE (happens once, AFTER all discussion): You decide your contribution"
        )
    },
    "attack": {
        "description": lambda params: (
            f"Each of {params['num_agents']} agents votes to ELIMINATE one other agent by pointing to them. "
            f"The agent(s) with the MOST votes gets eliminated. "
            f"If multiple agents tie for most votes, ALL tied agents are eliminated. "
            f"All SURVIVING agents split $100 equally."
        ),
        "goal": "Maximize your survival chances and payout by avoiding elimination.",
        "phases_normal": (
            "IMPORTANT: This game has TWO phases:\n"
            "1. DISCUSSION PHASE (multiple rounds): You communicate to coordinate votes\n"
            "2. VOTING PHASE (happens once, AFTER all discussion): You vote to eliminate someone"
        ),
        "phases_hybrid": (
            "IMPORTANT: This game has FOUR phases:\n"
            "1. OPENING PUBLIC DISCUSSION (1 round): All agents speak publicly in turn\n"
            "2. PRIVATE DM PHASE (multiple rounds): You communicate privately to coordinate\n"
            "3. CLOSING PUBLIC DISCUSSION (1 round): Final public round where you can say anything\n"
            "4. VOTING PHASE (happens once, AFTER all discussion): You vote to eliminate someone"
        )
    },
    "twothirds": {
        "description": lambda params: (
            f"Each of {params['num_agents']} agents chooses an integer between 0 and 100 (inclusive). "
            f"After everyone submits, the average of all guesses is calculated. "
            f"The target value is 2/3 of this average. "
            f"Each agent's payout = $100 - |your_guess - target_value|. "
            f"The closer your guess is to 2/3 of the average, the more money you earn."
        ),
        "goal": "Guess as close as possible to 2/3 of the average guess to maximize your payout.",
        "phases_normal": (
            "IMPORTANT: This game has TWO phases:\n"
            "1. DISCUSSION PHASE (multiple rounds): You communicate to coordinate guesses\n"
            "2. DECISION PHASE (happens once, AFTER all discussion): You submit your guess (0-100)"
        ),
        "phases_hybrid": (
            "IMPORTANT: This game has FOUR phases:\n"
            "1. OPENING PUBLIC DISCUSSION (1 round): All agents speak publicly in turn\n"
            "2. PRIVATE DM PHASE (multiple rounds): You communicate privately to coordinate\n"
            "3. CLOSING PUBLIC DISCUSSION (1 round): Final public round where you can say anything\n"
            "4. DECISION PHASE (happens once, AFTER all discussion): You submit your guess (0-100)"
        )
    }
}

# ============================================================================
# JSON RESPONSE FORMATS
# ============================================================================

JSON_FORMATS = {
    # Communication phase formats
    "dm": {
        "format": '{"dm_to": "B", "message": "Hey, want to coordinate?"}',
        "wait_format": '{"dm_to": "WAIT", "message": ""}',
        "instruction": "You MUST respond with valid JSON in exactly this format:"
    },
    "multi_dm": {
        "format": '[{"recipient": "B", "message": "..."}, {"recipient": "C", "message": "..."}]',
        "wait_format": '[{"recipient": "WAIT", "message": ""}]',
        "instruction": "You MUST respond with valid JSON array in exactly this format:"
    },
    "roundrobin": {
        "format": '{"message": "Here\'s my proposal..."}',
        "instruction": "You MUST respond with valid JSON in exactly this format:"
    },

    # Decision phase formats
    "decision_coordination": {
        "format": '{"point_to": "B", "reasoning": "One sentence explanation"}',
        "instruction": "You MUST respond with valid JSON in exactly this format:"
    },
    "decision_fishing": {
        "format": '{"catch": 15, "reasoning": "One sentence explanation"}',
        "instruction": "You MUST respond with valid JSON in exactly this format:"
    },
    "decision_publicgoods": {
        "format": '{"contribute": 5, "reasoning": "One sentence explanation"}',
        "instruction": "You MUST respond with valid JSON in exactly this format:"
    },
    "decision_attack": {
        "format": '{"vote_for": "B", "reasoning": "One sentence explanation"}',
        "instruction": "You MUST respond with valid JSON in exactly this format:"
    },
    "decision_twothirds": {
        "format": '{"guess": 42, "reasoning": "One sentence explanation"}',
        "instruction": "You MUST respond with valid JSON in exactly this format:"
    }
}

# ============================================================================
# COMMUNICATION STYLE INSTRUCTIONS
# ============================================================================

COMMUNICATION_INSTRUCTIONS = {
    "dm": {
        "constraint": "You can only DM one agent per round. Choose strategically.",
        "guidance": lambda just_spoke: (
            "NOTE: You just sent a message last round. Consider waiting to give others a chance to respond.\n\n"
            if just_spoke else ""
        )
    },
    "multi_dm": {
        "constraint": "You can DM multiple agents per round. Choose strategically.",
        "guidance": lambda just_spoke: (
            "NOTE: You just sent messages last round. Consider waiting to give others a chance to respond.\n\n"
            if just_spoke else ""
        )
    },
    "roundrobin": {
        "constraint": "All messages are public and visible to everyone.",
        "guidance": lambda is_first: (
            "You speak first this round. No prior messages to reference.\n\n"
            if is_first else ""
        )
    }
}
