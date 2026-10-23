"""
Weakest Link Game.

A coordination game where each player contributes effort to a project,
but everyone is rewarded based on the minimum effort contributed.
This creates pressure to coordinate but incentivizes free-riding.
"""

from typing import Dict, Any
from src.games.base import GameDefinition


class WeakestLinkGame(GameDefinition):
    """
    Weakest Link Game.

    Each player chooses effort level (0-5). Everyone is rewarded based on the minimum effort,
    but each player pays the cost of their own effort.

    Payoffs:
    - cost_per_effort (c): Cost per unit of effort (default: 2)
    - benefit_per_min_effort (b): Benefit per unit of minimum effort (default: 3)

    Your payoff = b * min_effort_across_all_players - c * your_effort

    The dilemma: You want others to work hard, but you personally want to minimize
    effort while still getting the group reward. However, if everyone thinks this way,
    the minimum drops and everyone suffers.
    """

    name = "weakestlink"
    display_name = "Weakest Link"
    output_directory = "weakestlink"

    def initialize(self, **game_params):
        """Initialize game with optional parameters."""
        # Cost and benefit parameters
        self.cost_per_effort = game_params.get('cost_per_effort', 2.0)
        self.benefit_per_min_effort = game_params.get('benefit_per_min_effort', 3.0)

        # Max effort level
        self.max_effort = game_params.get('max_effort', 5)

    @property
    def action_question(self) -> str:
        """Question asking for agent's action."""
        return f"How much effort will you contribute (0-{self.max_effort})? Return ONLY the number."

    @property
    def game_rules(self) -> str:
        """Generate game rules dynamically based on parameters."""
        n_players = len(self.agent_names)
        return f"""GAME RULES:
- There are {n_players} players working on a project
- Each player chooses effort level: 0 to {self.max_effort}
- Everyone is rewarded based on the MINIMUM effort across all players
- Your payoff = ${self.benefit_per_min_effort:.1f} × (minimum effort) - ${self.cost_per_effort:.1f} × (your effort)
- Everyone chooses simultaneously with no knowledge of others' actual choices
- Your goal is to maximize your final payout."""

    decision_json_schema = {
        "name": "effort_decision",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "choice": {
                    "type": "integer",
                    "description": "Effort level to contribute (0-5)"
                },
                "reasoning": {
                    "type": "string",
                    "description": "Brief explanation of your decision"
                }
            },
            "required": ["choice", "reasoning"],
            "additionalProperties": False
        }
    }

    def get_action_range(self, agent_name: str) -> str:
        """Get valid action range for weakest link game."""
        return f"0 to {self.max_effort}"

    def parse_action(self, agent_name: str, llm_response: Dict[str, Any]) -> int:
        """Parse decision from LLM response."""
        choice = llm_response.get('choice', 0)

        # Convert to integer
        try:
            effort = int(choice)
        except (ValueError, TypeError):
            # Default to 0 if invalid
            return 0

        # Clamp to valid range
        effort = max(0, min(self.max_effort, effort))

        return effort

    def evaluate(self, actions: Dict[str, int]) -> Dict[str, float]:
        """Calculate payouts based on effort choices."""
        if not actions:
            return {}

        # Convert all actions to integers (defensive - they should already be ints)
        int_actions = {name: int(effort) for name, effort in actions.items()}

        # Find minimum effort across all players
        min_effort = min(int_actions.values())

        # Assign payouts
        payouts = {}
        for agent_name, my_effort in int_actions.items():
            # Payoff = benefit × min_effort - cost × my_effort
            payouts[agent_name] = self.benefit_per_min_effort * min_effort - self.cost_per_effort * my_effort

        return payouts

    def get_game_state(self, actions: Dict[str, int], payouts: Dict[str, float]) -> Dict[str, Any]:
        """Return interpretable game state."""
        if not actions:
            return {}

        # Convert all actions to integers (defensive - they should already be ints)
        int_actions = {name: int(effort) for name, effort in actions.items()}

        # Find minimum effort
        min_effort = min(int_actions.values())
        max_effort = max(int_actions.values())
        avg_effort = sum(int_actions.values()) / len(int_actions)

        # Identify who is the weakest link
        weakest_links = [name for name, effort in int_actions.items() if effort == min_effort]

        # Determine outcome description
        if min_effort == max_effort:
            outcome_description = f"Perfect coordination - everyone contributed {min_effort}"
        elif len(weakest_links) == 1:
            outcome_description = f"{weakest_links[0]} is the weakest link with effort {min_effort}"
        else:
            outcome_description = f"{len(weakest_links)} players tied as weakest link with effort {min_effort}"

        return {
            "choices": int_actions,
            "min_effort": min_effort,
            "max_effort": max_effort,
            "avg_effort": round(avg_effort, 2),
            "weakest_links": weakest_links,
            "outcome": outcome_description,
            # Wasted effort
            "total_wasted_effort": sum(max(0, effort - min_effort) for effort in int_actions.values()),
            # Parameters for reference
            "cost_per_effort": self.cost_per_effort,
            "benefit_per_min_effort": self.benefit_per_min_effort
        }
