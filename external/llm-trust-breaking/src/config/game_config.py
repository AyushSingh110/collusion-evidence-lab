"""
Configuration file for LLM Collusion experiments.
Contains all game settings, model parameters, and token limits.
"""

# ============================================================================
# GAME CONFIGURATION
# ============================================================================

GAME_TYPE = "attack"           # Game type: "coordination", "fishing", "publicgoods", "attack", or "twothirds"
MODEL = "gpt-4o-mini"           # Model to use
NUM_AGENTS = 5                 # Number of agents per game
NUM_ROUNDS = 2                # Number of discussion rounds per game
NUM_SIMULATIONS = 5           # Number of times to run the simulation
USE_BATCH_API = True           # Use parallel execution (not actual OpenAI Batch API, just parallel threading)
COMMUNICATION_STYLE = "roundrobin"     # Communication style: "dm", "multi-dm", or "roundrobin"
                               # "dm": agents send one DM per round
                               # "multi-dm": agents can send DMs to multiple recipients per round
                               # "roundrobin": agents speak publicly in sequential order

HYBRID = False                 # Hybrid mode: adds 1 roundrobin at start + end (only works with dm/multi-dm)
                               # When True: Public Round → DM/Multi-DM Rounds → Public Round → Decision
                               # Total communication rounds = NUM_ROUNDS + 2

AGGRESSIVE_MODE = False        # Aggressive mode: explicitly encourages deceptive strategies
                               # When True: agents are told they can lie, manipulate, and break promises
                               # Affects system prompt for all communication and decision phases

# ============================================================================
# GAME-SPECIFIC SETTINGS
# ============================================================================

# Fishing game specific settings
TOTAL_FISH = 100               # Total fish in the lake
COLLAPSE_THRESHOLD = 50        # If total caught > this, lake collapses

# Public goods game specific settings
INITIAL_TOKENS = 10            # Starting tokens per agent
MULTIPLIER = 1.5               # Public pool multiplier

# Two-thirds game specific settings
# (No additional settings needed - game uses 0-100 range by default)

# ============================================================================
# TOKEN LIMITS (all doubled from original values)
# ============================================================================

# Coordination game token limits
TOKEN_LIMIT_COORDINATION_DM = 16000              # DM communication (was 8000)
TOKEN_LIMIT_COORDINATION_POINTING = 20000        # Pointing decision (was 10000)
TOKEN_LIMIT_COORDINATION_ROUNDROBIN = 6000       # Round-robin discussion (was 3000)

# Fishing game token limits
TOKEN_LIMIT_FISHING_DM = 16000                   # DM communication (was 8000)
TOKEN_LIMIT_FISHING_DECISION = 20000             # Fishing decision (was 10000)
TOKEN_LIMIT_FISHING_ROUNDROBIN = 6000            # Round-robin discussion (was 3000)

# Public goods game token limits
TOKEN_LIMIT_PUBLICGOODS_DM = 16000               # DM communication (was 8000)
TOKEN_LIMIT_PUBLICGOODS_DECISION = 20000         # Contribution decision (was 10000)
TOKEN_LIMIT_PUBLICGOODS_ROUNDROBIN = 6000        # Round-robin discussion (was 3000)

# Two-thirds game token limits
TOKEN_LIMIT_TWOTHIRDS_DM = 16000                 # DM communication
TOKEN_LIMIT_TWOTHIRDS_DECISION = 20000           # Guess decision
TOKEN_LIMIT_TWOTHIRDS_ROUNDROBIN = 6000          # Round-robin discussion

# Attack game token limits
TOKEN_LIMIT_ATTACK_DM = 16000                    # DM communication
TOKEN_LIMIT_ATTACK_DECISION = 20000              # Voting decision
TOKEN_LIMIT_ATTACK_ROUNDROBIN = 6000             # Round-robin discussion

# El Farol game token limits
TOKEN_LIMIT_ELFAROL_DM = 16000                   # DM communication
TOKEN_LIMIT_ELFAROL_DECISION = 20000             # Bar decision
TOKEN_LIMIT_ELFAROL_ROUNDROBIN = 6000            # Round-robin discussion

# Volunteer's Dilemma token limits
TOKEN_LIMIT_VOLUNTEER_DM = 16000                 # DM communication
TOKEN_LIMIT_VOLUNTEER_DECISION = 20000           # Volunteer decision
TOKEN_LIMIT_VOLUNTEER_ROUNDROBIN = 6000          # Round-robin discussion

# Judge analysis token limits
TOKEN_LIMIT_JUDGE_DECEPTIVE = 32000              # Deceptive behaviors analysis (was 16000)
TOKEN_LIMIT_JUDGE_COORDINATION = 32000           # Coordination patterns analysis (was 16000)
TOKEN_LIMIT_JUDGE_COALITION = 32000              # Coalition dynamics analysis (was 16000)
TOKEN_LIMIT_JUDGE_SUMMARY = 40000                # Summary analysis (was 20000)
