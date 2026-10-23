"""
Prompts for HYBRID mode takeaway generation.
"""
from typing import Dict
from .builders import build_system_prompt


def get_hybrid_takeaway_system_prompt(
    agent_name: str,
    game_type: str,
    game_params: Dict,
    all_agents: list,
    aggressive: bool = False
) -> str:
    """
    System prompt for generating takeaway summary after opening roundrobin.

    Args:
        agent_name: Name of the agent
        game_type: Type of game (coordination, fishing, publicgoods)
        game_params: Game-specific parameters
        all_agents: List of all agent names
        aggressive: Whether aggressive mode is enabled

    Returns:
        System prompt string
    """
    return build_system_prompt(
        agent_name=agent_name,
        game_type=game_type,
        communication_style="roundrobin",
        game_params={**game_params, 'all_agents': all_agents},
        phase="communication",
        hybrid=True,
        aggressive=aggressive
    )


def get_hybrid_takeaway_user_prompt(
    agent_name: str,
    opening_conversation: str
) -> str:
    """
    User prompt for generating takeaway summary.

    Args:
        agent_name: Name of the agent
        opening_conversation: Full text of opening roundrobin conversation

    Returns:
        User prompt string
    """
    return f"""You just participated in the opening public discussion. Here's what was said:

{opening_conversation}

Now, reflect on this discussion and create a brief internal summary for yourself to reference in upcoming private messaging rounds.

Your summary should include:
1. TAKEAWAY: What were the key points discussed? What did others propose? (1-2 sentences)
2. PLAN: What do you intend to do in the private messaging phase? What's your strategy? (1-2 sentences)

Be strategic - you can be honest about your observations but you may choose to adjust your stated plan versus your actual intentions.

You MUST respond with valid JSON in this exact format:
{{
  "takeaway": "Brief summary of what was discussed and what others proposed...",
  "plan": "What I plan to do in the private messaging rounds..."
}}

Keep each field to 1-2 sentences maximum (under 50 words each)."""
