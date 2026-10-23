"""
Game-Theoretic Analysis for LLM Strategic Deception

This module provides categorization of lies based on payoff and collective welfare changes.
"""

from .lying_categories import (
    compute_collective_state,
    categorize_lie,
    analyze_decision,
    check_missed_opportunity
)

__all__ = [
    'compute_collective_state',
    'categorize_lie',
    'analyze_decision',
    'check_missed_opportunity'
]
