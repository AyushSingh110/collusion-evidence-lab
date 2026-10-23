"""
Game definitions for LLM strategic deception experiments.

This module provides a unified interface for all game types.
Each game is implemented as a separate class in its own file.
"""

from typing import List
from src.games.base import GameDefinition
from src.games.diners import DinersDilemmaGame
from src.games.elfarol import ElFarolGame
from src.games.fishing import FishingGame
from src.games.publicgoods import PublicGoodsGame
from src.games.volunteer import VolunteerGame
from src.games.weakestlink import WeakestLinkGame


# Game registry mapping game type names to classes
GAMES = {
    "diners": DinersDilemmaGame,
    "elfarol": ElFarolGame,
    "fishing": FishingGame,
    "publicgoods": PublicGoodsGame,
    "volunteer": VolunteerGame,
    "weakestlink": WeakestLinkGame,
}

# Game-specific parameter mappings (config key -> game param key)
# These map configuration keys to game initialization parameters
GAME_PARAM_MAPPINGS = {
    "diners": {
        "expensive_joy": "expensive_joy",
        "cheap_joy": "cheap_joy",
        "expensive_cost": "expensive_cost",
        "cheap_cost": "cheap_cost",
    },
    "elfarol": {
        "threshold": "threshold",
        "bar_uncrowded_payout": "bar_uncrowded_payout",
        "bar_crowded_payout": "bar_crowded_payout",
        "home_payout": "home_payout",
    },
    "fishing": {
        "collapse_threshold": "collapse_threshold",
        "max_catch_per_agent": "max_catch_per_agent",
    },
    "publicgoods": {
        "initial_tokens": "initial_tokens",
        "multiplier": "multiplier",
    },
    "volunteer": {
        "cooperate_payout": "cooperate_payout",
        "defect_success_payout": "defect_success_payout",
        "defect_fail_payout": "defect_fail_payout",
    },
    "weakestlink": {
        "max_effort": "max_effort",
        "cost_per_effort": "cost_per_effort",
        "benefit_per_min_effort": "benefit_per_min_effort",
    },
}

# Default values for game-specific parameters
GAME_PARAM_DEFAULTS = {
    "diners": {
        "expensive_joy": 10.0,
        "cheap_joy": 5.0,
        "expensive_cost": 8.0,
        "cheap_cost": 2.0,
    },
    "elfarol": {
        "threshold": 0.5,
        "bar_uncrowded_payout": 10.0,
        "bar_crowded_payout": -5.0,
        "home_payout": 0.0,
    },
    "fishing": {
        "collapse_threshold": None,  # Will be calculated as n_agents * 3
        "max_catch_per_agent": 5,
    },
    "publicgoods": {
        "initial_tokens": 5,
        "multiplier": 1.5,
    },
    "volunteer": {
        "cooperate_payout": 0.0,
        "defect_success_payout": 1.0,
        "defect_fail_payout": -5.0,
    },
    "weakestlink": {
        "max_effort": 5,
        "cost_per_effort": 2.0,
        "benefit_per_min_effort": 3.0,
    },
}


def get_game_params_from_config(game_type: str, config: dict) -> dict:
    """
    Extract game-specific parameters from configuration.

    Args:
        game_type: Type of game
        config: Configuration dictionary

    Returns:
        Dictionary of game-specific parameters with defaults applied
    """
    if game_type not in GAME_PARAM_MAPPINGS:
        return {}

    game_params = {}
    defaults = GAME_PARAM_DEFAULTS.get(game_type, {})
    mappings = GAME_PARAM_MAPPINGS[game_type]

    for config_key, param_key in mappings.items():
        # Use value from config if available, otherwise use default
        game_params[param_key] = config.get(config_key, defaults.get(param_key))

    return game_params


def create_game(game_type: str, agent_names: List[str], **game_params) -> GameDefinition:
    """
    Factory function to create game instances.

    Args:
        game_type: Type of game (e.g., "fishing", "publicgoods", "volunteer")
        agent_names: List of agent names
        **game_params: Game-specific parameters (e.g., collapse_threshold=15, max_catch_per_agent=5)

    Returns:
        GameDefinition instance

    Raises:
        ValueError: If game_type is not recognized

    Examples:
        >>> game = create_game('fishing', ['A', 'B', 'C'], collapse_threshold=15, max_catch_per_agent=5)
        >>> game = create_game('publicgoods', ['A', 'B', 'C'], initial_tokens=5, multiplier=1.5)
        >>> game = create_game('volunteer', ['A', 'B', 'C'])
    """
    if game_type not in GAMES:
        raise ValueError(f"Unknown game type: {game_type}. Available: {list(GAMES.keys())}")

    game_class = GAMES[game_type]
    return game_class(agent_names, **game_params)


# Export public API
__all__ = [
    'GameDefinition',
    'DinersDilemmaGame',
    'ElFarolGame',
    'FishingGame',
    'PublicGoodsGame',
    'VolunteerGame',
    'WeakestLinkGame',
    'GAMES',
    'GAME_PARAM_MAPPINGS',
    'GAME_PARAM_DEFAULTS',
    'create_game',
    'get_game_params_from_config',
]
