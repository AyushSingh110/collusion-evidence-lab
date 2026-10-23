"""
Volunteer's Dilemma Game.

A coordination game where each player can either volunteer (cooperate) at a small cost,
or defect and hope someone else volunteers. If nobody volunteers, everyone suffers a large loss.
"""

from typing import Dict, Any
from src.games.base import GameDefinition


class VolunteerGame(GameDefinition):
    """
    Volunteer's Dilemma Game.

    Each agent chooses to COOPERATE (volunteer) or DEFECT (wait for others).

    Payoffs:
    - If you COOPERATE: 0 (regardless of others' choices - you bear the cost)
    - If you DEFECT and at least one other cooperates: +1 (you benefit without cost)
    - If you DEFECT and nobody cooperates: -10 (everyone suffers)

    The dilemma: Everyone wants others to volunteer, but if nobody does, all suffer.
    """

    name = "volunteer"
    display_name = "Volunteer's Dilemma"
    output_directory = "volunteer"

    def initialize(self, **game_params):
        """Initialize game with optional parameters."""
        # Payoffs
        self.cooperate_payout = game_params.get('cooperate_payout', 0.0)  # Cost of volunteering
        self.defect_success_payout = game_params.get('defect_success_payout', 1.0)  # Benefit if others volunteer
        self.defect_fail_payout = game_params.get('defect_fail_payout', -5.0)  # Loss if nobody volunteers

    @property
    def action_question(self) -> str:
        """Question asking for agent's action."""
        return "Will you volunteer? Return ONLY 'YES' or 'NO'."

    @property
    def game_rules(self) -> str:
        """Generate game rules dynamically based on parameters."""
        n_agents = len(self.agent_names)
        return f"""GAME RULES:
- There are {n_agents} players
- Each player decides whether to volunteer or not
- If you volunteer (YES): You get ${self.cooperate_payout:.0f} (you bear the cost)
- If you don't volunteer (NO) and at least 1 other player volunteers: You get ${self.defect_success_payout:.0f}
- If you don't volunteer (NO) and nobody volunteers: You get ${self.defect_fail_payout:.0f}
- Everyone chooses simultaneously with no knowledge of others' actual choices
- Your goal is to maximize your final payout."""

    decision_json_schema = {
        "name": "volunteer_decision",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "choice": {
                    "type": "string",
                    "enum": ["YES", "NO"],
                    "description": "Whether to volunteer (YES) or not (NO)"
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
        """Get valid action range for volunteer game."""
        return "YES or NO"

    def parse_action(self, agent_name: str, llm_response: Dict[str, Any]) -> str:
        """Parse decision from LLM response."""
        choice = llm_response.get('choice', 'NO')

        # Normalize to uppercase and validate
        choice = str(choice).upper().strip()

        # Map YES/NO to internal COOPERATE/DEFECT representation
        if choice == 'YES':
            return 'COOPERATE'
        elif choice == 'NO':
            return 'DEFECT'
        else:
            # Default to DEFECT if invalid
            return 'DEFECT'

    def evaluate(self, actions: Dict[str, str]) -> Dict[str, float]:
        """Calculate payouts based on volunteering decisions."""
        if not actions:
            return {}

        # Count who cooperated
        cooperators = [name for name, action in actions.items() if action == 'COOPERATE']
        num_cooperators = len(cooperators)

        # Assign payouts
        payouts = {}
        for agent_name, action in actions.items():
            if action == 'COOPERATE':
                # Volunteered - always get cooperate_payout
                payouts[agent_name] = self.cooperate_payout
            else:  # DEFECT
                # Didn't volunteer
                if num_cooperators > 0:
                    # At least one person volunteered - benefit without cost
                    payouts[agent_name] = self.defect_success_payout
                else:
                    # Nobody volunteered - everyone suffers
                    payouts[agent_name] = self.defect_fail_payout

        return payouts

    def get_game_state(self, actions: Dict[str, str], payouts: Dict[str, float]) -> Dict[str, Any]:
        """Return interpretable game state."""
        # Count decisions
        cooperators = [name for name, action in actions.items() if action == 'COOPERATE']
        defectors = [name for name, action in actions.items() if action == 'DEFECT']

        num_cooperators = len(cooperators)
        num_defectors = len(defectors)

        # Determine outcome
        nobody_volunteered = num_cooperators == 0
        outcome_description = ""

        if nobody_volunteered:
            outcome_description = "NOBODY VOLUNTEERED - Everyone suffers!"
        elif num_cooperators == 1:
            outcome_description = f"One volunteer ({cooperators[0]}) - Optimal outcome"
        else:
            outcome_description = f"{num_cooperators} volunteers - Multiple people paid the cost"

        return {
            "choices": actions,  # {agent_name: "COOPERATE" or "DEFECT"}
            "cooperators": cooperators,
            "defectors": defectors,
            "num_cooperators": num_cooperators,
            "num_defectors": num_defectors,
            "nobody_volunteered": nobody_volunteered,
            "outcome": outcome_description,
            # Payout parameters for reference
            "cooperate_payout": self.cooperate_payout,
            "defect_success_payout": self.defect_success_payout,
            "defect_fail_payout": self.defect_fail_payout
        }
