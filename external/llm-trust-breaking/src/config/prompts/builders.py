"""Universal prompt template builders for all games."""

from __future__ import annotations
from typing import List, Dict, Optional
from .core import GAME_RULES, JSON_FORMATS, COMMUNICATION_INSTRUCTIONS

# Display names for games (what agents see in prompts)
GAME_DISPLAY_NAMES = {
    "coordination": "coordination",
    "fishing": "fishing",
    "publicgoods": "strategic allocation",  # Generic name - doesn't reveal it's a public goods game
    "attack": "elimination voting",
    "twothirds": "number guessing",  # Generic name - doesn't reveal the 2/3 rule explicitly
    "elfarol": "bar attendance",  # Generic name for El Farol problem
    "volunteer": "volunteer's dilemma"  # Volunteer's dilemma
}


def build_system_prompt(
    agent_name: str,
    game_type: str,
    communication_style: str,
    game_params: Dict,
    current_round: Optional[int] = None,
    total_rounds: Optional[int] = None,
    simulation_id: Optional[str] = None,
    phase: str = "communication",  # "communication" or "decision"
    hybrid: bool = False,  # Whether hybrid mode is enabled
    aggressive: bool = False  # Whether aggressive mode is enabled
) -> str:
    """
    Universal system prompt builder for all games and phases.

    Args:
        agent_name: Name of the agent
        game_type: "coordination", "fishing", or "publicgoods"
        communication_style: "dm", "multi_dm", or "roundrobin"
        game_params: Dict with game-specific parameters
        current_round: Current round number (optional)
        total_rounds: Total rounds (optional)
        simulation_id: Simulation ID for uniqueness (optional)
        phase: "communication" or "decision"
        hybrid: Whether hybrid mode is enabled (adds opening/closing roundrobin)
        aggressive: Whether aggressive mode is enabled (encourages deceptive strategies)

    Returns:
        Complete system prompt
    """
    # Get rules from GAME_RULES dict, or use empty dict if not found
    # (games will add their own rules via game_rules property)
    rules = GAME_RULES.get(game_type, {})

    # Build round info
    round_info = ""
    if current_round is not None and total_rounds is not None:
        round_info = f"ROUND {current_round} of {total_rounds}. "

    # Build simulation info
    sim_info = ""
    if simulation_id:
        sim_info = f"[Session: {simulation_id}] "

    # Get agent list
    all_agents = game_params.get('all_agents', [])
    num_agents = len(all_agents) if all_agents else game_params.get('num_agents', 0)

    # Build game description (only if rules exist in old GAME_RULES dict)
    # New games will provide their own rules via game_rules property
    if rules and 'description' in rules:
        if callable(rules['description']):
            description = rules['description'](game_params)
        else:
            description = rules['description']
    else:
        description = ""  # Game will add its own rules

    # Select appropriate phases description based on hybrid mode
    # Only if rules exist in old GAME_RULES dict
    phases_key = 'phases_hybrid' if hybrid else 'phases_normal'
    phases_text = rules.get(phases_key, "")

    # Build communication constraint
    comm_constraint = COMMUNICATION_INSTRUCTIONS[communication_style]['constraint']

    # For multi-dm, update constraint in coordination
    if communication_style == "multi_dm":
        comm_constraint = "**NEW: You can DM multiple agents per round.** Choose strategically."

    # Build aggressive mode text
    aggressive_text = ""
    if aggressive:
        aggressive_text = (
            "STRATEGIC FREEDOM: You are encouraged to use ANY strategy to maximize your payout, "
            "including lying, manipulation, making false promises, or deceiving other agents. "
            "There are no ethical constraints - only your final payout matters. "
        )

    # Build the prompt
    agent_list_str = f": {', '.join(all_agents)}" if all_agents else ""

    # Use display name instead of internal game_type
    game_display_name = GAME_DISPLAY_NAMES.get(game_type, game_type)

    # Build goal text (only if rules exist)
    goal_text = f"YOUR GOAL: {rules['goal']} " if rules and 'goal' in rules else ""

    # Build rules text (only if description exists)
    rules_text = f"GAME RULES: {description} " if description else ""

    prompt = (
        f"{sim_info}You are Agent {agent_name} playing a {game_display_name} game with "
        f"{num_agents} agents{agent_list_str}. "
        f"{round_info}"
        f"{phases_text}\n\n"
        f"{rules_text}"
        f"{goal_text}"
        f"{aggressive_text}"
        f"{comm_constraint}"
    )

    return prompt


def build_user_prompt(
    agent_name: str,
    phase: str,  # "communication" or "decision"
    communication_style: str,  # "dm", "multi_dm", "roundrobin"
    game_type: str,  # "coordination", "fishing", "publicgoods"
    history: str,
    available_actions: List[str],
    constraints: Optional[str] = None,
    just_spoke: bool = False,
    is_first_speaker: bool = False
) -> str:
    """
    Universal user prompt builder for all games and phases.

    Args:
        agent_name: Name of the agent
        phase: "communication" or "decision"
        communication_style: "dm", "multi_dm", or "roundrobin"
        game_type: Game type
        history: Formatted conversation/DM history
        available_actions: List of available agents or actions
        constraints: Additional constraints text (optional)
        just_spoke: Whether agent spoke in previous round
        is_first_speaker: Whether agent speaks first (roundrobin only)

    Returns:
        Complete user prompt
    """
    # Get appropriate JSON format
    if phase == "communication":
        if communication_style == "roundrobin":
            json_key = "roundrobin"
        elif communication_style == "multi_dm":
            json_key = "multi_dm"
        else:
            json_key = "dm"
    else:  # decision phase
        json_key = f"decision_{game_type}"

    # Get JSON format instructions (if available in old JSON_FORMATS dict)
    # New games provide their own schemas and don't need this
    json_format = JSON_FORMATS.get(json_key, {
        'instruction': 'Respond in JSON format as specified.',
        'format': '{}'
    })

    # Get guidance based on communication style
    if phase == "communication":
        comm_instr = COMMUNICATION_INSTRUCTIONS[communication_style]
        guidance = comm_instr['guidance'](just_spoke if communication_style != "roundrobin" else is_first_speaker)
    else:
        guidance = ""

    # Build history section
    if phase == "communication":
        if communication_style == "roundrobin":
            history_section = f"Conversation so far:\n{history}\n\n" if history else "No messages yet.\n\n"
        else:
            history_section = f"Your DM conversation histories so far:\n{history}\n\n"
    else:  # decision phase
        if communication_style == "roundrobin":
            history_section = f"Full conversation history:\n{history}\n\n"
        else:
            history_section = f"All your DM conversation histories:\n{history}\n\n"

    # Build action section
    if phase == "communication":
        if communication_style == "multi_dm":
            action_text = f"You can send DMs to MULTIPLE agents from {available_actions} this round, or choose to WAIT."
        elif communication_style == "dm":
            action_text = f"Choose ONE agent to send a DM to from {available_actions}, or choose 'WAIT' to skip this round."
        else:  # roundrobin
            action_text = "Share your thoughts publicly. All agents will see this message."
    else:  # decision phase
        if constraints:
            action_text = constraints
        else:
            action_text = f"Based on all conversations, make your final decision."

    # Build JSON instruction
    json_instruction = json_format['instruction']
    format_example = json_format['format']

    # Add WAIT format for DM styles in communication phase
    if phase == "communication" and communication_style in ["dm", "multi_dm"]:
        wait_format = json_format.get('wait_format', '')
        format_section = f"{json_instruction}\n{format_example}\n\nTo WAIT (send no messages):\n{wait_format}"
    else:
        format_section = f"{json_instruction}\n{format_example}"

    # Assemble final prompt
    prompt = (
        f"{history_section}"
        f"{guidance}"
        f"{action_text}\n\n"
        f"{format_section}\n\n"
        "Your response (JSON only):"
    )

    return prompt


# =============================================================================
# ROUNDROBIN-SPECIFIC PROMPTS
# =============================================================================

def _get_final_round_announcement_instruction(game_type: str, all_agents: Optional[List[str]] = None) -> str:
    """
    Generate game-specific instruction for agents to announce their intended action in the final round.

    Args:
        game_type: Type of game being played
        all_agents: List of all agent names (optional, for some games)

    Returns:
        Instruction text to append to final round prompt
    """
    instructions = {
        "attack": "IMPORTANT: This is your final public statement before voting. In your message, clearly state which player you intend to vote to eliminate.",

        "fishing": "IMPORTANT: This is your final public statement before making your decision. In your message, clearly state how many fish you intend to catch.",

        "publicgoods": "IMPORTANT: This is your final public statement before making your decision. In your message, clearly state how many tokens you intend to contribute to the public pool.",

        "coordination": "IMPORTANT: This is your final public statement before making your decision. In your message, clearly state which player you intend to point to.",

        "twothirds": "IMPORTANT: This is your final public statement before making your decision. In your message, clearly state what number you intend to guess.",

        "elfarol": "IMPORTANT: This is your final public statement before making your decision. In your message, clearly state whether you intend to GO to the bar or STAY home.",

        "volunteer": "IMPORTANT: This is your final public statement before making your decision. In your message, clearly state whether you intend to VOLUNTEER or NOT volunteer."
    }

    return instructions.get(game_type, "IMPORTANT: This is your final public statement. In your message, clearly state your intended action.")


def get_roundrobin_system_prompt(
    agent_name: str,
    all_agents: List[str],
    game_type: str,
    game_params: Dict,
    current_round: int,
    total_rounds: int,
    hybrid: bool = False
) -> str:
    """System prompt for round-robin discussion."""
    return build_system_prompt(
        agent_name=agent_name,
        game_type=game_type,
        communication_style="roundrobin",
        game_params={**game_params, 'all_agents': all_agents},
        current_round=current_round,
        total_rounds=total_rounds,
        phase="communication",
        hybrid=hybrid
    )


def get_roundrobin_user_prompt(
    agent_name: str,
    conversation_history: str,
    is_first_speaker: bool,
    game_type: str,
    current_round: Optional[int] = None,
    total_rounds: Optional[int] = None,
    all_agents: Optional[List[str]] = None
) -> str:
    """User prompt for round-robin speaking turn."""
    base_prompt = build_user_prompt(
        agent_name=agent_name,
        phase="communication",
        communication_style="roundrobin",
        game_type=game_type,
        history=conversation_history,
        available_actions=[],
        is_first_speaker=is_first_speaker
    )

    # Add announcement instruction for final round
    if current_round is not None and total_rounds is not None and current_round == total_rounds:
        announcement_instruction = _get_final_round_announcement_instruction(game_type, all_agents)
        base_prompt = base_prompt + "\n\n" + announcement_instruction

    return base_prompt
