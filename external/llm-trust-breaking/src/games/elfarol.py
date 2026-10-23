"""
El Farol Bar Problem.

A classic game theory problem about coordination without communication.
Agents simultaneously decide whether to go to a bar, where overcrowding reduces utility.
"""

from typing import Dict, Any
from src.games.base import GameDefinition


class ElFarolGame(GameDefinition):
    """
    El Farol Bar Problem.

    Every Thursday night, agents decide whether to go to El Farol Bar.
    - If < 60% of population goes: Everyone at bar has more fun (gets positive payout)
    - If >= 60% of population goes: Everyone at bar has less fun (gets negative payout)
    - Those who stay home get baseline payout (0)

    Goal: Go to the bar only when it won't be too crowded.
    """

    name = "elfarol"
    display_name = "Bar Attendance Game"
    output_directory = "elfarol"

    def initialize(self, **game_params):
        """Initialize game with optional parameters."""
        # Threshold as percentage (default 50% - at least half)
        self.threshold = game_params.get('threshold', 0.5)

        # Payouts
        self.bar_uncrowded_payout = game_params.get('bar_uncrowded_payout', 10.0)  # If < 50% go
        self.bar_crowded_payout = game_params.get('bar_crowded_payout', -5.0)     # If >= 50% go
        self.home_payout = game_params.get('home_payout', 0.0)                     # Stay home

    @property
    def game_rules(self) -> str:
        """Generate game rules dynamically based on parameters."""
        n_agents = len(self.agent_names)
        threshold_pct = int(self.threshold * 100)
        return f"""GAME RULES:
- There are {n_agents} agents deciding whether to GO to El Farol Bar or STAY HOME this Thursday night
- The bar is fun when not too crowded, but miserable when overcrowded
- If fewer than {threshold_pct}% of agents go to the bar: Everyone at the bar has a great time (payout: ${self.bar_uncrowded_payout:.0f})
- If {threshold_pct}% or more of agents go to the bar: The bar is overcrowded and miserable (payout: ${self.bar_crowded_payout:.0f})
- If you STAY HOME: You have a quiet evening at home (payout: ${self.home_payout:.0f})
- Everyone chooses simultaneously with no knowledge of others' actual choices
- Your goal is to maximize your final payout."""

    @property
    def action_question(self) -> str:
        """Question asking for agent's action."""
        return "Do you GO or STAY? Return ONLY 'GO' or 'STAY'."

    decision_json_schema = {
        "name": "bar_decision",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "choice": {
                    "type": "string",
                    "enum": ["GO", "STAY"],
                    "description": "Whether to go to the bar (GO) or stay home (STAY)"
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
        """Get valid action range for elfarol game."""
        return "GO or STAY"

    def parse_action(self, agent_name: str, llm_response: Dict[str, Any]) -> str:
        """Parse decision from LLM response."""
        choice = llm_response.get('choice', 'STAY')

        # Normalize to uppercase and validate
        choice = str(choice).upper().strip()

        if choice not in ['GO', 'STAY']:
            # Default to STAY if invalid
            return 'STAY'

        return choice

    def evaluate(self, actions: Dict[str, str]) -> Dict[str, float]:
        """Calculate payouts based on bar attendance."""
        if not actions:
            return {}

        # Count how many agents chose to GO
        num_go = sum(1 for action in actions.values() if action == 'GO')
        total_agents = len(actions)

        # Calculate attendance rate
        attendance_rate = num_go / total_agents if total_agents > 0 else 0

        # Determine if bar is crowded
        is_crowded = attendance_rate >= self.threshold

        # Assign payouts
        payouts = {}
        for agent_name, action in actions.items():
            if action == 'GO':
                # Went to bar
                if is_crowded:
                    payouts[agent_name] = self.bar_crowded_payout  # Overcrowded, negative
                else:
                    payouts[agent_name] = self.bar_uncrowded_payout  # Just right, positive
            else:  # STAY
                # Stayed home
                payouts[agent_name] = self.home_payout  # Baseline

        return payouts

    def get_game_state(self, actions: Dict[str, str], payouts: Dict[str, float]) -> Dict[str, Any]:
        """Return interpretable game state."""
        # Count decisions
        num_go = sum(1 for action in actions.values() if action == 'GO')
        num_stay = sum(1 for action in actions.values() if action == 'STAY')
        total_agents = len(actions)

        # Calculate attendance rate
        attendance_rate = num_go / total_agents if total_agents > 0 else 0

        # Determine outcome
        is_crowded = attendance_rate >= self.threshold

        # Get who went where
        went_to_bar = [name for name, action in actions.items() if action == 'GO']
        stayed_home = [name for name, action in actions.items() if action == 'STAY']

        return {
            "choices": actions,  # {agent_name: "GO" or "STAY"}
            "went_to_bar": went_to_bar,
            "stayed_home": stayed_home,
            "num_at_bar": num_go,
            "num_at_home": num_stay,
            "attendance_rate": round(attendance_rate, 3),
            "threshold": self.threshold,
            "is_crowded": is_crowded,
            "bar_status": "CROWDED" if is_crowded else "UNCROWDED",
            # Payout parameters for reference
            "bar_uncrowded_payout": self.bar_uncrowded_payout,
            "bar_crowded_payout": self.bar_crowded_payout,
            "home_payout": self.home_payout
        }
