"""
Test LLM behavior across all possible announcement scenarios.

For each scenario, prompt the LLM for each agent's actual action given
what everyone publicly announced they would do.
"""

from typing import Dict, Any, List, Tuple
import json




def _filter_game_params(game_type: str, all_params: dict) -> dict:
    """
    Filter parameters to only include those valid for the game.
    Uses GAME_PARAM_MAPPINGS to determine which parameters are valid.

    Args:
        game_type: Type of game
        all_params: All parameters passed in

    Returns:
        Filtered dict with only valid game parameters
    """
    from src.games import GAME_PARAM_MAPPINGS

    if game_type not in GAME_PARAM_MAPPINGS:
        return {}

    valid_params = set(GAME_PARAM_MAPPINGS[game_type].values())
    return {k: v for k, v in all_params.items() if k in valid_params}


def _get_game_rules(game_type: str, agent_names: List[str], **kwargs) -> str:
    """
    Get game rules description for system prompt using game registry.

    Args:
        game_type: Type of game
        agent_names: List of agent names (needed for dynamic game creation)
        **kwargs: Game-specific parameters

    Returns:
        Game rules as a string
    """
    from src.games import create_game

    # Strip _single_agent suffix to get base game type
    # Strip _single_agent suffix no longer needed

    # Filter to only valid game parameters
    game_params = _filter_game_params(game_type, kwargs)

    # Create game instance with parameters
    game = create_game(game_type, agent_names, **game_params)

    # Return the game's rules property (works for all games now)
    return game.game_rules


def _get_action_question(game_type: str, agent_names: List[str], **kwargs) -> str:
    """
    Get the action question for an agent using game registry.

    Args:
        game_type: Type of game
        agent_names: List of agent names
        **kwargs: Game-specific parameters

    Returns:
        Action question string
    """
    from src.games import create_game

    # Strip _single_agent suffix to get base game type
    # Strip _single_agent suffix no longer needed

    # Filter out non-game parameters
    game_params = _filter_game_params(game_type, kwargs)

    # Create game instance
    game = create_game(game_type, agent_names, **game_params)

    # Return the game's action question property
    return game.action_question


def _get_json_schema(game_type: str, agent_names: List[str], include_reasoning: bool = False, **game_params) -> Dict[str, Any]:
    """
    Get JSON schema for LLM response using game registry.

    Args:
        game_type: Type of game
        agent_names: List of all agent names (for validation)
        include_reasoning: Whether to include reasoning field
        **game_params: Game-specific parameters

    Returns:
        JSON schema dictionary
    """
    from src.games import create_game
    import copy

    # Strip _single_agent suffix to get base game type
    # Strip _single_agent suffix no longer needed

    # Filter out non-game parameters
    filtered_params = _filter_game_params(game_type, game_params)

    # Create game instance with parameters
    game = create_game(game_type, agent_names, **filtered_params)

    # Get the game's actual JSON schema
    schema = copy.deepcopy(game.decision_json_schema)

    # If no reasoning requested, remove reasoning field from schema
    if not include_reasoning:
        # Remove reasoning from properties and required fields
        if 'schema' in schema and 'properties' in schema['schema']:
            schema['schema']['properties'].pop('reasoning', None)
        if 'schema' in schema and 'required' in schema['schema']:
            schema['schema']['required'] = [r for r in schema['schema']['required'] if r != 'reasoning']

    return schema



def _build_single_agent_prompt_generic(
    game_type: str,
    agent_name: str,
    scenario_info: str,
    game_params: Dict[str, Any],
    n_agents: int = 5
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Generic helper to build single-agent prompts using game definitions.

    Args:
        game_type: Type of game (e.g., "fishing", "volunteer")
        agent_name: Name of the agent being prompted
        scenario_info: Scenario-specific information (announcements, other agents' actions, etc.)
        game_params: Game-specific parameters (includes 'include_reasoning', 'supports_structured_output')
        n_agents: Total number of agents (default: 5)

    Returns:
        Tuple of (system_prompt, user_prompt, json_schema)
    """
    from src.games import create_game

    include_reasoning = game_params.get('include_reasoning', True)
    supports_structured = game_params.get('supports_structured_output', True)

    # Create dummy agent names for game instantiation
    agent_names = [agent_name] + [f"Other{i}" for i in range(n_agents - 1)]

    # Filter to only valid game parameters
    filtered_params = _filter_game_params(game_type, game_params)

    # Create game instance
    game = create_game(game_type, agent_names, **filtered_params)

    # Build system prompt using game rules
    system_prompt = f"""You are Agent {agent_name} in a {game.display_name}.

{game.game_rules}

You must make a strategic decision to maximize your outcome."""

    # Get action question from game
    action_question = game.action_question

    # Build user prompt
    if include_reasoning:
        user_prompt = f"""{scenario_info}

{action_question}

Provide your actual action and brief reasoning."""
    else:
        user_prompt = f"""{scenario_info}

{action_question}"""

    # Add explicit JSON instructions for models without structured output support
    if not supports_structured:
        if include_reasoning:
            user_prompt += """\n\nIMPORTANT: Respond with ONLY a valid JSON object in this exact format:
{"choice": your_value_here, "reasoning": "your_reasoning_here"}

Do not include any other text, explanation, or markdown formatting. Just the JSON object."""
        else:
            user_prompt += """\n\nIMPORTANT: Respond with ONLY a valid JSON object in this exact format:
{"choice": your_value_here}

Do not include any other text, explanation, or markdown formatting. Just the JSON object."""

    # Get JSON schema - extract include_reasoning from game_params to avoid duplicate argument
    game_params_for_schema = {k: v for k, v in game_params.items() if k != 'include_reasoning'}
    json_schema = _get_json_schema(game_type, agent_names, include_reasoning, **game_params_for_schema)

    return system_prompt, user_prompt, json_schema


def build_fishing_single_agent_prompt(
    agent_name: str,
    announced: int,
    others_total: int,
    collapse_threshold: int,
    max_catch: int,
    game_params: Dict[str, Any]
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Build prompt for single-agent fishing scenario.

    Args:
        agent_name: Name of the agent being prompted
        announced: How many fish the agent announced they would catch
        others_total: Total fish caught by all other agents
        collapse_threshold: Lake collapse threshold
        max_catch: Maximum fish one agent can catch
        game_params: Game-specific parameters (includes 'include_reasoning')

    Returns:
        Tuple of (system_prompt, user_prompt, json_schema)
    """
    # Determine number of agents from collapse threshold (default is 3x num_agents)
    # This is a heuristic - if collapse_threshold is passed, use it to infer n_agents
    n_agents = game_params.get('n_agents', 5)

    # Build scenario info
    scenario_info = f"""SCENARIO:
- You publicly announced: "I will catch {announced} fish"
- The other agents have collectively caught {others_total} fish in total
- Lake collapse threshold: {collapse_threshold} fish"""

    # Use generic helper with game-specific params
    return _build_single_agent_prompt_generic(
        game_type="fishing",
        agent_name=agent_name,
        scenario_info=scenario_info,
        game_params={**game_params, 'collapse_threshold': collapse_threshold, 'max_catch_per_agent': max_catch},
        n_agents=n_agents
    )


def build_volunteer_single_agent_prompt(
    agent_name: str,
    announced: str,
    others_volunteer_count: int,
    n_other_agents: int,
    game_params: Dict[str, Any]
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Build prompt for single-agent volunteer scenario.

    Args:
        agent_name: Name of the agent being prompted
        announced: What the agent announced they would do ("YES" or "NO")
        others_volunteer_count: Number of other agents who announced they will volunteer
        n_other_agents: Total number of other agents
        game_params: Game-specific parameters (includes 'include_reasoning')

    Returns:
        Tuple of (system_prompt, user_prompt, json_schema)
    """
    n_agents = n_other_agents + 1

    # Build scenario info
    volunteer_text = "volunteer" if announced == "YES" else "not volunteer"
    scenario_info = f"""SCENARIO:
- You publicly announced: "I will {volunteer_text}" ({announced})
- {others_volunteer_count} out of {n_other_agents} other agents announced they will volunteer"""

    # Use generic helper with game-specific params
    return _build_single_agent_prompt_generic(
        game_type="volunteer",
        agent_name=agent_name,
        scenario_info=scenario_info,
        game_params=game_params,
        n_agents=n_agents
    )


def build_elfarol_single_agent_prompt(
    agent_name: str,
    announced: str,
    others_go_count: int,
    n_other_agents: int,
    game_params: Dict[str, Any]
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Build prompt for single-agent El Farol Bar scenario.

    Args:
        agent_name: Name of the agent being prompted
        announced: What the agent announced they would do ("GO" or "STAY")
        others_go_count: Number of other agents who announced they will GO to the bar
        n_other_agents: Total number of other agents
        game_params: Game-specific parameters (includes 'include_reasoning')

    Returns:
        Tuple of (system_prompt, user_prompt, json_schema)
    """
    n_agents = n_other_agents + 1

    # Build scenario info
    scenario_info = f"""SCENARIO:
- You publicly announced: "{announced}"
- {others_go_count} out of {n_other_agents} other agents announced they will GO to the bar"""

    # Use generic helper with game-specific params
    return _build_single_agent_prompt_generic(
        game_type="elfarol",
        agent_name=agent_name,
        scenario_info=scenario_info,
        game_params=game_params,
        n_agents=n_agents
    )


def build_diners_single_agent_prompt(
    agent_name: str,
    announced: str,
    others_expensive_count: int,
    n_other_agents: int,
    game_params: Dict[str, Any]
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Build prompt for single-agent Diner's Dilemma scenario.

    Args:
        agent_name: Name of the agent being prompted
        announced: What the agent announced they would order ("EXPENSIVE" or "CHEAP")
        others_expensive_count: Number of other agents who announced they will order EXPENSIVE
        n_other_agents: Total number of other agents
        game_params: Game-specific parameters (includes 'include_reasoning')

    Returns:
        Tuple of (system_prompt, user_prompt, json_schema)
    """
    n_agents = n_other_agents + 1

    # Build scenario info
    scenario_info = f"""SCENARIO:
- You publicly announced: "{announced}"
- {others_expensive_count} out of {n_other_agents} other diners announced they will order EXPENSIVE"""

    # Use generic helper with game-specific params
    return _build_single_agent_prompt_generic(
        game_type="diners",
        agent_name=agent_name,
        scenario_info=scenario_info,
        game_params=game_params,
        n_agents=n_agents
    )


def build_publicgoods_single_agent_prompt(
    agent_name: str,
    announced: int,
    others_total: int,
    initial_tokens: int,
    multiplier: float,
    game_params: Dict[str, Any]
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Build prompt for single-agent public goods scenario.

    Args:
        agent_name: Name of the agent being prompted
        announced: How many tokens the agent announced they would contribute
        others_total: Total tokens contributed by all other agents
        initial_tokens: Number of tokens each agent starts with
        multiplier: Public pool multiplier
        game_params: Game-specific parameters (includes 'include_reasoning')

    Returns:
        Tuple of (system_prompt, user_prompt, json_schema)
    """
    n_agents = game_params.get('n_agents', 5)

    # Build scenario info
    scenario_info = f"""SCENARIO:
- You publicly announced: "I will contribute {announced} tokens"
- The other agents have collectively contributed {others_total} tokens in total
- Public pool multiplier: {multiplier}x"""

    # Use generic helper with game-specific params
    return _build_single_agent_prompt_generic(
        game_type="publicgoods",
        agent_name=agent_name,
        scenario_info=scenario_info,
        game_params={**game_params, 'initial_tokens': initial_tokens, 'multiplier': multiplier},
        n_agents=n_agents
    )


def build_weakestlink_single_agent_prompt(
    agent_name: str,
    announced: int,
    others_minimum: int,
    max_effort: int,
    game_params: Dict[str, Any]
) -> Tuple[str, str, Dict[str, Any]]:
    """
    Build prompt for single-agent weakest link scenario.

    Args:
        agent_name: Name of the agent being prompted
        announced: How much effort the agent announced they would contribute
        others_minimum: Minimum effort among all other agents
        max_effort: Maximum effort level (default: 5)
        game_params: Game-specific parameters (includes 'include_reasoning')

    Returns:
        Tuple of (system_prompt, user_prompt, json_schema)
    """
    n_agents = game_params.get('n_agents', 5)
    n_other_agents = n_agents - 1

    # Build scenario info
    scenario_info = f"""SCENARIO:
- You publicly announced: "I will put in {announced} units of effort"
- The minimum effort among the other {n_other_agents} agents is {others_minimum}"""

    # Use generic helper with game-specific params
    return _build_single_agent_prompt_generic(
        game_type="weakestlink",
        agent_name=agent_name,
        scenario_info=scenario_info,
        game_params={**game_params, 'max_effort': max_effort},
        n_agents=n_agents
    )


