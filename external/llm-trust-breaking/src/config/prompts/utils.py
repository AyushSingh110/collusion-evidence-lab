"""Utility functions for prompts."""

from typing import List
from .core import GAME_RULES


def format_conversation_history(conversation_history):
    """Format conversation history for display."""
    if not conversation_history:
        return "No previous conversation."

    lines = []
    for round_num, speaker, message in conversation_history:
        lines.append(f"Round {round_num} - {speaker}: \"{message}\"")

    return "\n".join(lines)


def get_game_rules(topic: str) -> str:
    """Get game rules description for a specific topic."""
    if topic not in GAME_RULES:
        return ""

    rules = GAME_RULES[topic]
    if callable(rules['description']):
        return rules['goal']  # Return just goal if description needs params
    return rules['description']


# ============================================================================
# Legacy functions for backward compatibility
# ============================================================================

def get_broadcast_system_prompt(agent_name: str, all_agents: List[str], game_rules: str) -> str:
    """System prompt for broadcast phase (legacy)."""
    return f"You are Agent {agent_name} with {len(all_agents)} agents: {', '.join(all_agents)}. {game_rules}"


def get_broadcast_user_prompt() -> str:
    """User prompt for broadcast phase (legacy)."""
    return "Send a public message to all agents. Return JSON: {\"message\": \"your message here\"}"


def get_round_robin_system_prompt(agent_name: str, all_agents: List[str], game_rules: str) -> str:
    """System prompt for round-robin (legacy)."""
    return f"You are Agent {agent_name} with {len(all_agents)} agents. {game_rules}"


def get_round_robin_speak_prompt(conversation_history: str) -> str:
    """User prompt for round-robin speaking (legacy)."""
    return f"Conversation so far:\n{conversation_history}\n\nYour turn. Return JSON: {{\"message\": \"your message\"}}"


def get_general_chat_system_prompt(agent_name: str, all_agents: List[str], game_rules: str) -> str:
    """System prompt for general chat (legacy)."""
    return f"You are Agent {agent_name}. {game_rules}"


def get_general_chat_user_prompt(chat_history: str, dm_history: str) -> str:
    """User prompt for general chat vs DM choice (legacy)."""
    return f"Chat: {chat_history}\nDMs: {dm_history}\nChoose action. Return JSON."
