"""
Fishing Game Definition.

Tragedy of the Commons - Fishing Game.
Agents decide how many fish to catch from a shared lake.
Overfishing causes collapse and everyone gets 0.
"""

from src.games.base import GameDefinition
from typing import Dict, Any, List


class FishingGame(GameDefinition):
    """
    Tragedy of the Commons - Fishing Game.

    Agents decide how many fish to catch from a shared lake.
    Overfishing causes collapse and everyone gets 0.
    """

    name = "fishing"
    display_name = "Fishing Game"
    output_directory = "fishing"

    # Game parameters (can be overridden in __init__)
    collapse_threshold = 15
    max_catch_per_agent = 5

    @property
    def action_question(self) -> str:
        """Question asking for agent's action."""
        return f"How many fish do you catch? Return ONLY an integer between 0-{self.max_catch_per_agent}."

    @property
    def game_rules(self) -> str:
        """Game rules for LLM prompt."""
        n_agents = len(self.agent_names)
        return f"""GAME RULES:
- There are {n_agents} fishermen sharing a lake
- Each fisherman decides how many fish to catch (0-{self.max_catch_per_agent})
- If total catch exceeds {self.collapse_threshold} fish, the lake collapses and everyone gets 0
- If total catch ≤ {self.collapse_threshold}, each fisherman keeps what they caught
- Your goal is to maximize your final payout."""

    decision_json_schema = {
        "name": "fishing_decision",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "choice": {
                    "type": "integer",
                    "description": "Number of fish to catch (0-5)"
                },
                "reasoning": {
                    "type": "string",
                    "description": "One sentence explanation of your decision"
                }
            },
            "required": ["choice", "reasoning"],
            "additionalProperties": False
        }
    }

    def __init__(self, agent_names: List[str], collapse_threshold: int = None, max_catch_per_agent: int = 5):
        """
        Initialize with custom parameters.

        Args:
            agent_names: List of agent names
            collapse_threshold: Maximum sustainable catch. If None, defaults to num_agents * 3 - 1
            max_catch_per_agent: Maximum fish each agent can catch (default: 5)
        """
        super().__init__(agent_names)

        # Calculate default threshold based on number of agents (3n-1).
        # Catching exactly 3 per agent is already too much; the safe total is 3n-1.
        if collapse_threshold is None:
            collapse_threshold = len(agent_names) * 3 - 1

        self.collapse_threshold = collapse_threshold
        self.max_catch_per_agent = max_catch_per_agent

    def parse_action(self, agent_name: str, llm_response: Dict[str, Any]) -> str:
        """Parse LLM response to extract fish catch decision."""
        # Try multiple key variants
        fish_count = llm_response.get('choice', llm_response.get('fish_to_catch', llm_response.get('catch', llm_response.get('fish', 0))))
        fish_count = max(0, min(self.max_catch_per_agent, int(fish_count)))
        return str(fish_count)

    def evaluate(self, actions: Dict[str, str]) -> Dict[str, float]:
        """Calculate payouts based on total catch and collapse threshold."""
        catches = {name: int(action) for name, action in actions.items()}
        total_caught = sum(catches.values())
        collapsed = total_caught > self.collapse_threshold

        if collapsed:
            # Collapse: everyone gets 0
            payouts = {agent: 0.0 for agent in self.agent_names}
        else:
            # Success: everyone keeps their catch
            payouts = {agent: float(catches.get(agent, 0)) for agent in self.agent_names}

        return payouts

    def get_game_state(self, actions: Dict[str, str], payouts: Dict[str, float]) -> Dict[str, Any]:
        """Return interpretable game state."""
        catches = {name: int(action) for name, action in actions.items()}
        total_caught = sum(catches.values())
        collapsed = total_caught > self.collapse_threshold

        return {
            "individual_catches": catches,
            "total_caught": total_caught,
            "collapsed": collapsed,
            "sustainable": not collapsed,
            "threshold": self.collapse_threshold,
            # Backwards compatibility
            "collapse_threshold": self.collapse_threshold
        }
