"""
Base class for all game definitions.

All games inherit from GameDefinition and implement the required methods.
"""

from typing import Dict, Any, List, Optional
from abc import ABC, abstractmethod


class GameDefinition(ABC):
    """
    Base class for unified game definitions.

    All games inherit from this and implement the required methods.
    """

    # Metadata (must be set by subclass)
    name: str = ""  # Internal identifier (e.g., "twothirds")
    display_name: str = ""  # Name shown to agents (e.g., "Number Guessing Game")
    output_directory: str = ""  # Where to save results (e.g., "twothirds")

    # Prompts (must be set by subclass)
    game_rules: str = ""  # Rules appended to default system prompt

    # JSON schema for decision (must be set by subclass)
    decision_json_schema: Dict[str, Any] = {}

    def __init__(self, agent_names: List[str], **game_params):
        """
        Initialize game with agent names and optional parameters.

        Args:
            agent_names: List of agent names
            **game_params: Game-specific parameters
        """
        self.agent_names = agent_names
        self.game_params = game_params
        self.actions = {}  # {agent_name: action_string}
        self.message_log = []  # For DM tracking

        # Allow games to add custom initialization
        self.initialize(**game_params)

    def initialize(self, **game_params):
        """Optional: Custom initialization logic for game-specific parameters."""
        pass

    @abstractmethod
    def parse_action(self, agent_name: str, llm_response: Dict[str, Any]) -> str:
        """
        Parse LLM response to extract action as string.

        Args:
            agent_name: Name of the agent
            llm_response: Raw JSON response from LLM

        Returns:
            Action as string (e.g., "42" for a guess)
        """
        raise NotImplementedError

    @abstractmethod
    def evaluate(self, actions: Dict[str, str]) -> Dict[str, float]:
        """
        Compute payouts from all agent actions.

        Args:
            actions: {agent_name: action_string}

        Returns:
            {agent_name: payout}
        """
        raise NotImplementedError

    @abstractmethod
    def get_game_state(self, actions: Dict[str, str], payouts: Dict[str, float]) -> Dict[str, Any]:
        """
        Return game state for output/display.

        Args:
            actions: {agent_name: action_string}
            payouts: {agent_name: payout}

        Returns:
            Dictionary with game-specific state (interpretable for analysis)
        """
        raise NotImplementedError

    # Helper methods (generic for all games)

    def submit_action(self, agent_name: str, action: str):
        """Record an agent's action."""
        self.actions[agent_name] = action

    def log_dm(self, round_num: int, from_agent: str, to_agent: str, message: str):
        """Log a DM for later analysis."""
        self.message_log.append((round_num, from_agent, to_agent, message))

    def get_action_range(self, agent_name: str) -> str:
        """
        Get the valid action range/options for an agent (for multi-turn prompts).

        Returns:
            String describing valid actions (e.g., "0-10", "YES or NO")
        """
        # Default implementation - subclasses should override if needed
        return "valid action"

    def calculate_results(self) -> Dict[str, Any]:
        """
        Calculate game results (for compatibility with existing infrastructure).

        This combines evaluate() and get_game_state() into a single result dictionary.

        Returns:
            Dictionary with payouts and game_state combined
        """
        payouts = self.evaluate(self.actions)
        game_state = self.get_game_state(self.actions, payouts)

        # Combine payouts and game_state into a single result
        result = dict(game_state)
        result['payouts'] = payouts

        return result

    def get_results_for_output(self) -> Dict[str, Any]:
        """Get complete results formatted for JSON output."""
        # Calculate results
        payouts = self.evaluate(self.actions)
        game_state = self.get_game_state(self.actions, payouts)

        # Build dm_histories from agents if available
        dm_histories = {}
        if hasattr(self, 'agents'):
            for agent_name, agent in self.agents.items():
                dm_histories[agent_name] = agent.dm_histories

        # Flatten game_state into top-level for compatibility
        result = {
            "agents": self.agent_names,
            "message_log": self.message_log,
            "dm_histories": dm_histories,
            "actions": self.actions,
            "payouts": payouts
        }

        # Add all game_state fields to top-level
        result.update(game_state)

        return result