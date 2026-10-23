"""Formatting utilities for conversation histories and output display."""
from __future__ import annotations
from typing import List, Dict, Tuple

def format_dm_histories(
    agent_name: str,
    dm_histories: Dict[str, List[Tuple[int, str, str]]],
    all_agents: List[str]
) -> str:
    """
    Format all DM conversation histories for a given agent.

    Args:
        agent_name: The agent whose perspective to format
        dm_histories: Dictionary mapping agent names to conversation histories
        all_agents: List of all agent names in the game

    Returns:
        Formatted string showing all DM conversations
    """
    lines = []
    for other in sorted(all_agents):
        if other == agent_name:
            continue
        history = dm_histories.get(other, [])
        lines.append(f"\n--- DMs with {other} ---")
        if not history:
            lines.append("(no messages yet)")
        else:
            for i, (round_num, speaker, text) in enumerate(history, 1):
                lines.append(f"{i}) {speaker}: {text}")
    return "\n".join(lines)

def format_general_chat_history(
    chat_history: List[Tuple[str, str]]
) -> str:
    """
    Format general chat history (visible to all agents).

    Args:
        chat_history: List of (speaker, message) tuples

    Returns:
        Formatted chat history string
    """
    if not chat_history:
        return "(no messages yet)"

    lines = []
    for i, (speaker, message) in enumerate(chat_history, 1):
        lines.append(f"{i}) {speaker}: {message}")
    return "\n".join(lines)

def format_round_robin_history(
    speaking_history: List[Tuple[str, str]]
) -> str:
    """
    Format round-robin speaking history.

    Args:
        speaking_history: List of (speaker, message) tuples in order

    Returns:
        Formatted speaking history
    """
    if not speaking_history:
        return "(no one has spoken yet)"

    lines = []
    for i, (speaker, message) in enumerate(speaking_history, 1):
        lines.append(f"Round {i} - {speaker}: {message}")
    return "\n".join(lines)

def format_broadcast_messages(
    broadcasts: Dict[str, str]
) -> str:
    """
    Format initial broadcast messages from all agents.

    Args:
        broadcasts: Dictionary mapping agent names to their broadcast messages

    Returns:
        Formatted broadcast messages
    """
    if not broadcasts:
        return "(no broadcasts yet)"

    lines = []
    for agent in sorted(broadcasts.keys()):
        lines.append(f"{agent}: {broadcasts[agent]}")
    return "\n".join(lines)
