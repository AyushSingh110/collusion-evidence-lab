"""
Public Goods Game Definition.

Agents decide how much to contribute to a public pool.
Contributions are multiplied and split equally among all.
"""

from src.games.base import GameDefinition
from typing import Dict, Any, List


class PublicGoodsGame(GameDefinition):
    """
    Public Goods Game.

    Agents decide how much to contribute to a public pool.
    Contributions are multiplied and split equally among all.
    """

    name = "publicgoods"
    display_name = "Resource Contribution Game"
    output_directory = "publicgoods"

    # Game parameters (can be overridden in __init__)
    initial_tokens = 5  # Default: 5 tokens (0-5 range, same as fishing)
    multiplier = 1.5

    @property
    def action_question(self) -> str:
        """Question asking for agent's action."""
        return f"How many tokens do you contribute? Return ONLY an integer between 0-{self.initial_tokens}."

    @property
    def game_rules(self) -> str:
        """Game rules for LLM prompt."""
        n_agents = len(self.agent_names)
        return f"""GAME RULES:
- There are {n_agents} players, each starting with {self.initial_tokens} tokens
- Each player decides how many tokens to contribute to a public pool (0-{self.initial_tokens})
- The public pool is multiplied by {self.multiplier}x and split equally among all players
- You keep any tokens you didn't contribute
- Your final payout = (tokens kept) + (your share of public pool)
- Your goal is to maximize your final payout."""

    decision_json_schema = {
        "name": "contribution_decision",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "choice": {
                    "type": "integer",
                    "description": "Number of tokens to contribute (0-5)"
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

    def __init__(self, agent_names: List[str], initial_tokens: int = 5, multiplier: float = 1.5):
        """Initialize with custom parameters."""
        super().__init__(agent_names)
        self.initial_tokens = initial_tokens
        self.multiplier = multiplier

    def parse_action(self, agent_name: str, llm_response: Dict[str, Any]) -> str:
        """Parse LLM response to extract contribution decision."""
        # Try multiple key variants
        tokens = llm_response.get('choice', llm_response.get('tokens_to_contribute', llm_response.get('contribution', llm_response.get('contribute', 0))))
        tokens = max(0, min(self.initial_tokens, int(tokens)))
        return str(tokens)

    def evaluate(self, actions: Dict[str, str]) -> Dict[str, float]:
        """Calculate final tokens for each agent."""
        contributions = {name: int(action) for name, action in actions.items()}

        total_contributed = sum(contributions.values())
        public_pool_value = total_contributed * self.multiplier
        num_agents = len(self.agent_names)
        share_per_agent = public_pool_value / num_agents if num_agents > 0 else 0

        # Calculate final tokens for each agent
        payouts = {}
        for agent in self.agent_names:
            contribution = contributions.get(agent, 0)
            kept = self.initial_tokens - contribution
            payouts[agent] = kept + share_per_agent

        return payouts

    def get_game_state(self, actions: Dict[str, str], payouts: Dict[str, float]) -> Dict[str, Any]:
        """Return interpretable game state."""
        contributions = {name: int(action) for name, action in actions.items()}

        total_contributed = sum(contributions.values())
        public_pool_value = total_contributed * self.multiplier
        num_agents = len(self.agent_names)
        share_per_agent = public_pool_value / num_agents if num_agents > 0 else 0

        return {
            "individual_contributions": contributions,
            "total_contributed": total_contributed,
            "public_pool_value": round(public_pool_value, 2),
            "share_per_agent": round(share_per_agent, 2),
            "initial_tokens": self.initial_tokens,
            "multiplier": self.multiplier,
            # Backwards compatibility
            "final_tokens": payouts  # Alias for payouts
        }
