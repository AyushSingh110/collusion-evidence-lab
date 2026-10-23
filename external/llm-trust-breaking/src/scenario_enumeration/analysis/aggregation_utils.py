"""
Utility functions for aggregating LLM responses across shuffled scenarios.
"""

from typing import List, Any, Dict
from collections import Counter


def majority_vote(actions: List[Any]) -> Any:
    """
    Take majority vote over a list of actions.

    Args:
        actions: List of actions (can be strings, numbers, etc.)

    Returns:
        The most common action (ties broken by first occurrence)
    """
    if not actions:
        return None

    # Handle None values
    actions_filtered = [a for a in actions if a is not None]
    if not actions_filtered:
        return None

    # For numeric actions, handle floating point comparison
    if all(isinstance(a, (int, float)) for a in actions_filtered):
        # Round to avoid floating point issues
        actions_rounded = [round(float(a), 2) for a in actions_filtered]
        counter = Counter(actions_rounded)
        # Deterministic tie-breaking: sort by count (desc), then by value (asc)
        most_common = sorted(counter.items(), key=lambda x: (-x[1], x[0]))[0][0]
        return most_common

    # For string actions, normalize case
    if all(isinstance(a, str) for a in actions_filtered):
        actions_normalized = [str(a).strip().upper() for a in actions_filtered]
        counter = Counter(actions_normalized)
        # Deterministic tie-breaking: sort by count (desc), then alphabetically (asc)
        most_common = sorted(counter.items(), key=lambda x: (-x[1], x[0]))[0][0]

        # Return original casing from first occurrence
        for orig in actions_filtered:
            if str(orig).strip().upper() == most_common:
                return orig

    # Fallback: simple majority vote with deterministic tie-breaking
    counter = Counter(actions_filtered)
    # Convert to strings for sorting to ensure deterministic ordering
    most_common = sorted(counter.items(), key=lambda x: (-x[1], str(x[0])))[0][0]
    return most_common


def compute_consensus_stats(actions: List[Any]) -> Dict[str, Any]:
    """
    Compute statistics about consensus across shuffled responses.

    Args:
        actions: List of actions from different shuffle orders

    Returns:
        Dictionary with consensus statistics
    """
    actions_filtered = [a for a in actions if a is not None]

    if not actions_filtered:
        return {
            'majority_action': None,
            'num_responses': 0,
            'consensus_rate': 0.0,
            'action_distribution': {}
        }

    counter = Counter(actions_filtered)
    most_common_action, most_common_count = counter.most_common(1)[0]

    return {
        'majority_action': most_common_action,
        'num_responses': len(actions_filtered),
        'consensus_rate': most_common_count / len(actions_filtered),
        'action_distribution': dict(counter),
        'is_unanimous': len(counter) == 1
    }
