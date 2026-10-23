"""
Diner's Dilemma Game.

A social dilemma where diners agree to split the bill equally before ordering.
Each must choose between an expensive or cheap dish. The expensive dish provides
more joy but costs more, creating a tragedy of the commons scenario.
"""

from typing import Dict, Any
from src.games.base import GameDefinition


class DinersDilemmaGame(GameDefinition):
    """
    Diner's Dilemma Game.

    Several diners agree to split the bill equally. Each chooses EXPENSIVE or CHEAP dish.

    Payoffs:
    - expensive_joy (a): Joy from eating expensive dish (default: 10)
    - cheap_joy (b): Joy from eating cheap dish (default: 5)
    - expensive_cost (k): Cost of expensive dish (default: 8)
    - cheap_cost (l): Cost of cheap dish (default: 2)

    Your payoff = joy - (total_bill / n_diners)

    The dilemma: The expensive dish is better, but not enough to justify paying
    the full difference alone. However, when costs are split, each diner has an
    incentive to order expensive, leading to a worse outcome for everyone.
    """

    name = "diners"
    display_name = "Diner's Dilemma"
    output_directory = "diners"

    def initialize(self, **game_params):
        """Initialize game with optional parameters."""
        # Joy from dishes
        self.expensive_joy = game_params.get('expensive_joy', 10.0)
        self.cheap_joy = game_params.get('cheap_joy', 5.0)

        # Costs
        self.expensive_cost = game_params.get('expensive_cost', 8.0)
        self.cheap_cost = game_params.get('cheap_cost', 2.0)

    @property
    def action_question(self) -> str:
        """Question asking for agent's action."""
        return "Which dish will you order? Return ONLY 'EXPENSIVE' or 'CHEAP'."

    @property
    def game_rules(self) -> str:
        """Generate game rules dynamically based on parameters."""
        n_diners = len(self.agent_names)
        return f"""GAME RULES:
- There are {n_diners} diners who agreed to split the bill equally
- Each diner chooses between an EXPENSIVE or CHEAP dish
- EXPENSIVE dish: Joy = ${self.expensive_joy:.1f}, Cost = ${self.expensive_cost:.1f}
- CHEAP dish: Joy = ${self.cheap_joy:.1f}, Cost = ${self.cheap_cost:.1f}
- Your payoff = Joy from your dish - (Total bill / {n_diners} diners)
- Everyone chooses simultaneously with no knowledge of others' actual choices
- Your goal is to maximize your final payout."""

    decision_json_schema = {
        "name": "diner_decision",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "choice": {
                    "type": "string",
                    "enum": ["EXPENSIVE", "CHEAP"],
                    "description": "Whether to order the expensive dish (EXPENSIVE) or cheap dish (CHEAP)"
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
        """Get valid action range for diners game."""
        return "EXPENSIVE or CHEAP"

    def parse_action(self, agent_name: str, llm_response: Dict[str, Any]) -> str:
        """Parse decision from LLM response."""
        choice = llm_response.get('choice', 'CHEAP')

        # Normalize to uppercase and validate
        choice = str(choice).upper().strip()

        if choice not in ['EXPENSIVE', 'CHEAP']:
            # Default to CHEAP if invalid
            return 'CHEAP'

        return choice

    def evaluate(self, actions: Dict[str, str]) -> Dict[str, float]:
        """Calculate payouts based on dish choices."""
        if not actions:
            return {}

        n_diners = len(actions)

        # Calculate total bill
        total_bill = sum(
            self.expensive_cost if action == 'EXPENSIVE' else self.cheap_cost
            for action in actions.values()
        )

        # Each diner pays equal share
        cost_per_diner = total_bill / n_diners

        # Assign payouts
        payouts = {}
        for agent_name, action in actions.items():
            # Joy from dish minus share of bill
            joy = self.expensive_joy if action == 'EXPENSIVE' else self.cheap_joy
            payouts[agent_name] = joy - cost_per_diner

        return payouts

    def get_game_state(self, actions: Dict[str, str], payouts: Dict[str, float]) -> Dict[str, Any]:
        """Return interpretable game state."""
        # Count choices
        expensive_orders = [name for name, action in actions.items() if action == 'EXPENSIVE']
        cheap_orders = [name for name, action in actions.items() if action == 'CHEAP']

        num_expensive = len(expensive_orders)
        num_cheap = len(cheap_orders)
        n_diners = len(actions)

        # Calculate bill
        total_bill = num_expensive * self.expensive_cost + num_cheap * self.cheap_cost
        cost_per_diner = total_bill / n_diners

        # Determine outcome description
        if num_expensive == 0:
            outcome_description = "Everyone ordered cheap - minimal bill!"
        elif num_expensive == n_diners:
            outcome_description = "Everyone ordered expensive - maximum bill!"
        else:
            outcome_description = f"{num_expensive} expensive, {num_cheap} cheap - mixed orders"

        return {
            "choices": actions,
            "expensive_orders": expensive_orders,
            "cheap_orders": cheap_orders,
            "num_expensive": num_expensive,
            "num_cheap": num_cheap,
            "total_bill": round(total_bill, 2),
            "cost_per_diner": round(cost_per_diner, 2),
            "outcome": outcome_description,
            # Parameters for reference
            "expensive_joy": self.expensive_joy,
            "cheap_joy": self.cheap_joy,
            "expensive_cost": self.expensive_cost,
            "cheap_cost": self.cheap_cost
        }
