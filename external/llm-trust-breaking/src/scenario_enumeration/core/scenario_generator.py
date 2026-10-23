"""
Generate all possible announcement scenarios for different game types.

For each game, this generates every possible combination of public announcements
that agents could make, which can then be tested against LLM behavior.
"""

from typing import List, Dict, Any, Iterator
import itertools


def generate_attack_scenarios(agent_names: List[str]) -> Iterator[Dict[str, str]]:
    """
    Generate all possible announcement scenarios for attack game.

    In attack game, each agent announces which player they intend to vote for.
    Agents cannot vote for themselves, so self-vote announcements are excluded.

    Args:
        agent_names: List of agent names (e.g., ['A', 'B', 'C', 'D', 'E'])

    Yields:
        Dictionary mapping agent name to their announced target (excluding self-votes)

    Example:
        {'A': 'B', 'B': 'A', 'C': 'A', 'D': 'B', 'E': 'C'}
    """
    n_agents = len(agent_names)

    # Each agent can announce any other agent as their target (excluding themselves)
    # Build list of valid targets for each agent
    valid_targets_per_agent = [
        [target for target in agent_names if target != agent]
        for agent in agent_names
    ]

    # Generate all combinations where no agent votes for themselves
    # Total scenarios: (n-1)^n (e.g., 4^5 = 1,024 for 5 agents)
    for announcement_combo in itertools.product(*valid_targets_per_agent):
        yield dict(zip(agent_names, announcement_combo))


def generate_fishing_scenarios(
    agent_names: List[str],
    max_catch: int = 5
) -> Iterator[Dict[str, int]]:
    """
    Generate all possible announcement scenarios for fishing game.

    In fishing game, each agent announces how many fish they intend to catch (0-5).

    Args:
        agent_names: List of agent names
        max_catch: Maximum fish one agent can catch (default: 5)

    Yields:
        Dictionary mapping agent name to their announced catch amount

    Example:
        {'A': 5, 'B': 3, 'C': 0, 'D': 2, 'E': 4}
    """
    n_agents = len(agent_names)

    # Each agent can announce 0 to max_catch fish
    # Total scenarios: (max_catch + 1)^n (e.g., 6^5 = 7,776 for 5 agents)
    for announcement_combo in itertools.product(range(max_catch + 1), repeat=n_agents):
        yield dict(zip(agent_names, announcement_combo))


def generate_fishing_scenarios_single_agent(
    agent_name: str,
    max_catch: int = 5,
    n_other_agents: int = 4
) -> Iterator[Dict[str, Any]]:
    """
    Generate fishing scenarios for single agent optimization.

    Instead of enumerating all agent profiles, test one agent across
    different (announced, others_total) combinations.

    Args:
        agent_name: Name of the agent being tested
        max_catch: Maximum fish one agent can catch (default: 5)
        n_other_agents: Number of other agents (default: 4)

    Yields:
        Dictionary with 'announced' and 'others_total' keys

    Example:
        {'agent_name': 'A', 'announced': 3, 'others_total': 10}

    Total scenarios: 6 announcements × 21 others_total = 126
    """
    # Enumerate all (announced, others_total) pairs
    for announced in range(max_catch + 1):
        # Others can catch from 0 (all catch 0) to n_other_agents * max_catch (all catch max)
        max_others_total = n_other_agents * max_catch
        for others_total in range(max_others_total + 1):
            yield {
                'agent_name': agent_name,
                'announced': announced,
                'others_total': others_total
            }


def generate_weakestlink_scenarios_single_agent(
    agent_name: str,
    max_effort: int = 5,
    n_other_agents: int = 4
) -> Iterator[Dict[str, Any]]:
    """
    Generate weakest link scenarios for single agent optimization.

    Instead of enumerating all agent profiles, test one agent across
    different (announced, others_minimum) combinations.

    Args:
        agent_name: Name of the agent being tested
        max_effort: Maximum effort level (default: 5, so 0-5 range)
        n_other_agents: Number of other agents (default: 4)

    Yields:
        Dictionary with 'announced' and 'others_minimum' keys

    Example:
        {'agent_name': 'A', 'announced': 3, 'others_minimum': 2}

    Total scenarios: (max_effort+1) announcements × (max_effort+1) others_minimum
    For max_effort=5: 6 × 6 = 36 scenarios
    """
    # Enumerate all (announced, others_minimum) pairs
    for announced in range(max_effort + 1):
        # Others' minimum can be from 0 to max_effort
        for others_minimum in range(max_effort + 1):
            yield {
                'agent_name': agent_name,
                'announced': announced,
                'others_minimum': others_minimum
            }


def generate_publicgoods_scenarios(
    agent_names: List[str],
    initial_tokens: int = 5
) -> Iterator[Dict[str, int]]:
    """
    Generate all possible announcement scenarios for public goods game.

    In public goods game, each agent announces how many tokens they intend to contribute (0-5).

    Args:
        agent_names: List of agent names
        initial_tokens: Number of tokens each agent starts with (default: 5)

    Yields:
        Dictionary mapping agent name to their announced contribution

    Example:
        {'A': 0, 'B': 5, 'C': 3, 'D': 2, 'E': 4}
    """
    n_agents = len(agent_names)

    # Each agent can announce 0 to initial_tokens contribution
    # Total scenarios: (initial_tokens + 1)^n (e.g., 6^5 = 7,776 for 5 agents)
    for announcement_combo in itertools.product(range(initial_tokens + 1), repeat=n_agents):
        yield dict(zip(agent_names, announcement_combo))


def generate_publicgoods_scenarios_single_agent(
    agent_name: str,
    initial_tokens: int = 5,
    n_other_agents: int = 4
) -> Iterator[Dict[str, Any]]:
    """
    Generate public goods scenarios for single agent optimization.

    Instead of enumerating all agent profiles, test one agent across
    different (announced, others_total_contribution) combinations.

    Args:
        agent_name: Name of the agent being tested
        initial_tokens: Number of tokens each agent starts with (default: 5)
        n_other_agents: Number of other agents (default: 4)

    Yields:
        Dictionary with 'announced' and 'others_total' keys

    Example:
        {'agent_name': 'A', 'announced': 3, 'others_total': 15}

    Total scenarios: (initial_tokens+1) announcements × (n_other_agents * initial_tokens + 1) others_total
    For 5 agents with 5 tokens: 6 × 21 = 126 scenarios (same as fishing!)
    """
    # Enumerate all (announced, others_total) pairs
    for announced in range(initial_tokens + 1):
        # Others can contribute from 0 (all contribute 0) to n_other_agents * initial_tokens (all contribute max)
        max_others_total = n_other_agents * initial_tokens
        for others_total in range(max_others_total + 1):
            yield {
                'agent_name': agent_name,
                'announced': announced,
                'others_total': others_total
            }


def generate_auction_scenarios(
    agent_names: List[str],
    max_bid: int = 5
) -> Iterator[Dict[str, int]]:
    """
    Generate all possible announcement scenarios for auction game.

    In auction game, each agent announces their bid amount (0 to max_bid).

    Args:
        agent_names: List of agent names
        max_bid: Maximum bid allowed (default: 5)

    Yields:
        Dictionary mapping agent name to their announced bid

    Example:
        {'A': 0, 'B': 2, 'C': 5, 'D': 1, 'E': 3}
    """
    n_agents = len(agent_names)

    # Each agent can announce bid from 0 to max_bid
    # Total scenarios: (max_bid + 1)^n (e.g., 6^5 = 7,776 for 5 agents with max_bid=5)
    for announcement_combo in itertools.product(range(max_bid + 1), repeat=n_agents):
        yield dict(zip(agent_names, announcement_combo))


def generate_coordination_scenarios(agent_names: List[str]) -> Iterator[Dict[str, str]]:
    """
    Generate all possible announcement scenarios for coordination game.

    In coordination game, each agent announces which player they intend to point to.

    Args:
        agent_names: List of agent names

    Yields:
        Dictionary mapping agent name to their announced pointer target

    Example:
        {'A': 'B', 'B': 'C', 'C': 'A', 'D': 'E', 'E': 'D'}
    """
    n_agents = len(agent_names)

    # Each agent can announce pointing to any of the n_agents (including themselves)
    # Total scenarios: n^n (e.g., 5^5 = 3,125 for 5 agents)
    for announcement_combo in itertools.product(agent_names, repeat=n_agents):
        yield dict(zip(agent_names, announcement_combo))


def generate_twothirds_scenarios(
    agent_names: List[str],
    max_guess: int = 5
) -> Iterator[Dict[str, int]]:
    """
    Generate all possible announcement scenarios for two-thirds game.

    In two-thirds game, each agent announces what number they intend to guess (0-5).

    Args:
        agent_names: List of agent names
        max_guess: Maximum guess value (default: 5)

    Yields:
        Dictionary mapping agent name to their announced guess

    Example:
        {'A': 5, 'B': 3, 'C': 2, 'D': 4, 'E': 1}
    """
    n_agents = len(agent_names)

    # Each agent can announce 0 to max_guess
    # Total scenarios: (max_guess + 1)^n (e.g., 6^5 = 7,776 for 5 agents)
    for announcement_combo in itertools.product(range(max_guess + 1), repeat=n_agents):
        yield dict(zip(agent_names, announcement_combo))


def generate_elfarol_scenarios(agent_names: List[str]) -> Iterator[Dict[str, str]]:
    """
    Generate all possible announcement scenarios for El Farol bar game.

    In El Farol, each agent announces whether they intend to GO to the bar or STAY home.

    Args:
        agent_names: List of agent names

    Yields:
        Dictionary mapping agent name to their announced choice ("GO" or "STAY")

    Example:
        {'A': 'GO', 'B': 'STAY', 'C': 'GO', 'D': 'GO', 'E': 'STAY'}
    """
    n_agents = len(agent_names)

    # Each agent can announce GO or STAY
    # Total scenarios: 2^n (e.g., 2^5 = 32 for 5 agents)
    for announcement_combo in itertools.product(['GO', 'STAY'], repeat=n_agents):
        yield dict(zip(agent_names, announcement_combo))


def generate_congestion_scenarios(agent_names: List[str]) -> Iterator[Dict[str, str]]:
    """
    Generate all possible announcement scenarios for Congestion Game.

    In Congestion Game, each agent announces whether they will use the shortcut (YES) or main route (NO).

    Args:
        agent_names: List of agent names

    Yields:
        Dictionary mapping agent name to their announced choice ("YES" or "NO")
    """
    n_agents = len(agent_names)

    # Each agent can announce YES or NO
    # Total scenarios: 2^n (e.g., 2^5 = 32 for 5 agents)
    for announcement_combo in itertools.product(['YES', 'NO'], repeat=n_agents):
        yield dict(zip(agent_names, announcement_combo))


def generate_volunteer_scenarios(agent_names: List[str]) -> Iterator[Dict[str, str]]:
    """
    Generate all possible announcement scenarios for Volunteer's Dilemma.

    In Volunteer's Dilemma, each agent announces whether they intend to volunteer (YES or NO).

    Args:
        agent_names: List of agent names

    Yields:
        Dictionary mapping agent name to their announced choice ("YES" or "NO")

    Example:
        {'A': 'YES', 'B': 'NO', 'C': 'NO', 'D': 'YES', 'E': 'NO'}
    """
    n_agents = len(agent_names)

    # Each agent can announce YES or NO
    # Total scenarios: 2^n (e.g., 2^5 = 32 for 5 agents)
    for announcement_combo in itertools.product(['YES', 'NO'], repeat=n_agents):
        yield dict(zip(agent_names, announcement_combo))


def generate_volunteer_scenarios_single_agent(
    agent_name: str,
    n_other_agents: int = 4
) -> Iterator[Dict[str, Any]]:
    """
    Generate volunteer scenarios for single agent optimization.

    Instead of enumerating all agent profiles, test one agent across
    different (announced, others_volunteer_count) combinations.

    Args:
        agent_name: Name of the agent being tested
        n_other_agents: Number of other agents (default: 4)

    Yields:
        Dictionary with 'announced' and 'others_volunteer_count' keys

    Example:
        {'agent_name': 'A', 'announced': 'YES', 'others_volunteer_count': 2}

    Total scenarios: 2 announcements × (n_other_agents + 1) volunteer counts
    For 5 agents: 2 × 5 = 10 scenarios
    """
    # Enumerate all (announced, others_volunteer_count) pairs
    for announced in ['YES', 'NO']:
        # Others can have 0 to n_other_agents volunteers
        for others_volunteer_count in range(n_other_agents + 1):
            yield {
                'agent_name': agent_name,
                'announced': announced,
                'others_volunteer_count': others_volunteer_count
            }


def generate_elfarol_scenarios_single_agent(
    agent_name: str,
    n_other_agents: int = 4
) -> Iterator[Dict[str, Any]]:
    """
    Generate El Farol Bar scenarios for single agent optimization.

    Instead of enumerating all agent profiles, test one agent across
    different (announced, others_go_count) combinations.

    Args:
        agent_name: Name of the agent being tested
        n_other_agents: Number of other agents (default: 4)

    Yields:
        Dictionary with 'announced' and 'others_go_count' keys

    Example:
        {'agent_name': 'A', 'announced': 'GO', 'others_go_count': 2}

    Total scenarios: 2 announcements × (n_other_agents + 1) go counts
    For 5 agents: 2 × 5 = 10 scenarios
    """
    # Enumerate all (announced, others_go_count) pairs
    for announced in ['GO', 'STAY']:
        # Others can have 0 to n_other_agents going to bar
        for others_go_count in range(n_other_agents + 1):
            yield {
                'agent_name': agent_name,
                'announced': announced,
                'others_go_count': others_go_count
            }


def generate_diners_scenarios_single_agent(
    agent_name: str,
    n_other_agents: int = 4
) -> Iterator[Dict[str, Any]]:
    """
    Generate Diner's Dilemma scenarios for single agent optimization.

    Instead of enumerating all agent profiles, test one agent across
    different (announced, others_expensive_count) combinations.

    Args:
        agent_name: Name of the agent being tested
        n_other_agents: Number of other agents (default: 4)

    Yields:
        Dictionary with 'announced' and 'others_expensive_count' keys

    Example:
        {'agent_name': 'A', 'announced': 'EXPENSIVE', 'others_expensive_count': 2}

    Total scenarios: 2 announcements × (n_other_agents + 1) expensive counts
    For 5 agents: 2 × 5 = 10 scenarios
    """
    # Enumerate all (announced, others_expensive_count) pairs
    for announced in ['EXPENSIVE', 'CHEAP']:
        # Others can have 0 to n_other_agents ordering expensive
        for others_expensive_count in range(n_other_agents + 1):
            yield {
                'agent_name': agent_name,
                'announced': announced,
                'others_expensive_count': others_expensive_count
            }


# Registry mapping game types to their generator functions and parameters
_SCENARIO_GENERATORS = {
    "fishing": (generate_fishing_scenarios_single_agent, {"max_catch": 5, "n_other_agents": 4}),
    "publicgoods": (generate_publicgoods_scenarios_single_agent, {"initial_tokens": 5, "n_other_agents": 4}),
    "weakestlink": (generate_weakestlink_scenarios_single_agent, {"max_effort": 5, "n_other_agents": 4}),
    "elfarol": (generate_elfarol_scenarios_single_agent, {"n_other_agents": 4}),
    "volunteer": (generate_volunteer_scenarios_single_agent, {"n_other_agents": 4}),
    "diners": (generate_diners_scenarios_single_agent, {"n_other_agents": 4}),
}

# Registry for scenario count formulas
# Tuple of (formula_type, parameter_name, default_value)
_SCENARIO_COUNT_FORMULAS = {
    "fishing": ("single_agent_fishing", "max_catch", 5),
    "publicgoods": ("single_agent_continuous", "initial_tokens", 5),
    "weakestlink": ("single_agent_weakestlink", "max_effort", 5),
    "elfarol": ("single_agent_binary", None, None),
    "volunteer": ("single_agent_binary", None, None),
    "diners": ("single_agent_binary", None, None),
}


def count_scenarios(game_type: str, n_agents: int, **kwargs) -> int:
    """
    Calculate total number of scenarios for a game type without generating them.

    Args:
        game_type: Type of game ('attack', 'fishing', 'publicgoods', etc.)
        n_agents: Number of agents
        **kwargs: Game-specific parameters (max_catch, initial_tokens, etc.)

    Returns:
        Total number of possible scenarios
    """
    if game_type not in _SCENARIO_COUNT_FORMULAS:
        raise ValueError(f"Unknown game type: {game_type}")

    formula_type, param_name, default_value = _SCENARIO_COUNT_FORMULAS[game_type]

    if formula_type == "power":
        return n_agents ** n_agents
    elif formula_type == "param_power":
        param_value = kwargs.get(param_name, default_value)
        return (param_value + 1) ** n_agents
    elif formula_type == "binary":
        return 2 ** n_agents
    elif formula_type == "no_self_vote":
        # For games where agents can't target themselves (e.g., attack game)
        return (n_agents - 1) ** n_agents
    elif formula_type == "single_agent_fishing":
        # For single-agent fishing: (max_catch+1) * (n_other_agents * max_catch + 1)
        max_catch = kwargs.get(param_name, default_value)
        n_other_agents = kwargs.get('n_other_agents', n_agents - 1)
        return (max_catch + 1) * (n_other_agents * max_catch + 1)
    elif formula_type == "single_agent_binary":
        # For single-agent binary games (volunteer, etc): 2 * (n_other_agents + 1)
        # 2 announcements × (0 to n_other_agents) other choices
        n_other_agents = kwargs.get('n_other_agents', n_agents - 1)
        return 2 * (n_other_agents + 1)
    elif formula_type == "single_agent_continuous":
        # For single-agent continuous games (publicgoods, etc): (param+1) * (n_other_agents * param + 1)
        # Similar to fishing but more general
        param_value = kwargs.get(param_name, default_value)
        n_other_agents = kwargs.get('n_other_agents', n_agents - 1)
        return (param_value + 1) * (n_other_agents * param_value + 1)
    elif formula_type == "single_agent_weakestlink":
        # For single-agent weakest link: (max_effort+1) * (max_effort+1)
        # announced values × others_minimum values
        max_effort = kwargs.get(param_name, default_value)
        return (max_effort + 1) * (max_effort + 1)
    else:
        raise ValueError(f"Unknown formula type: {formula_type}")


def generate_scenarios(
    game_type: str,
    agent_names: List[str],
    **kwargs
) -> Iterator[Dict[str, Any]]:
    """
    Generate all scenarios for any game type using registry.

    Args:
        game_type: Type of game ('attack', 'fishing', 'publicgoods', etc.)
        agent_names: List of agent names
        **kwargs: Game-specific parameters

    Yields:
        Dictionary mapping agent name to their announced action
    """
    if game_type not in _SCENARIO_GENERATORS:
        raise ValueError(f"Unknown game type: {game_type}")

    generator_func, default_params = _SCENARIO_GENERATORS[game_type]

    # Merge default parameters with provided kwargs
    params = {**default_params, **kwargs}

    # Special handling for single-agent scenarios
    if game_type == "fishing":
        # Use first agent from list, calculate n_other_agents
        agent_name = agent_names[0]
        max_catch = params.get('max_catch', 5)
        n_other_agents = len(agent_names) - 1
        yield from generator_func(agent_name, max_catch=max_catch, n_other_agents=n_other_agents)
        return

    if game_type == "volunteer":
        # Use first agent from list, calculate n_other_agents
        agent_name = agent_names[0]
        n_other_agents = len(agent_names) - 1
        yield from generator_func(agent_name, n_other_agents=n_other_agents)
        return

    if game_type == "elfarol":
        # Use first agent from list, calculate n_other_agents
        agent_name = agent_names[0]
        n_other_agents = len(agent_names) - 1
        yield from generator_func(agent_name, n_other_agents=n_other_agents)
        return

    if game_type == "diners":
        # Use first agent from list, calculate n_other_agents
        agent_name = agent_names[0]
        n_other_agents = len(agent_names) - 1
        yield from generator_func(agent_name, n_other_agents=n_other_agents)
        return

    if game_type == "publicgoods":
        # Use first agent from list, calculate n_other_agents
        agent_name = agent_names[0]
        initial_tokens = params.get('initial_tokens', 10)
        n_other_agents = len(agent_names) - 1
        yield from generator_func(agent_name, initial_tokens=initial_tokens, n_other_agents=n_other_agents)
        return

    if game_type == "weakestlink":
        # Use first agent from list, calculate n_other_agents
        agent_name = agent_names[0]
        max_effort = params.get('max_effort', 5)
        n_other_agents = len(agent_names) - 1
        yield from generator_func(agent_name, max_effort=max_effort, n_other_agents=n_other_agents)
        return

    # Call the generator function with appropriate parameters
    # Check the function signature to pass only what it needs
    import inspect
    sig = inspect.signature(generator_func)
    param_names = list(sig.parameters.keys())

    if len(param_names) == 1:
        # Only takes agent_names
        yield from generator_func(agent_names)
    else:
        # Takes additional parameters
        # Extract the specific parameter needed (second parameter)
        param_name = param_names[1]
        param_value = params.get(param_name, default_params.get(param_name))
        yield from generator_func(agent_names, param_value)
