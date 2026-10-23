"""Ensemble monitor baseline for comparison against TraceGuard.

Thin wrapper around ControlArena's ensemble_monitor_builder, providing
a simple multi-sample averaging baseline to compare against structured
dimension scoring.
"""

from control_arena.monitor import ensemble_monitor_builder


def ensemble_monitor(num_samples: int = 5, temperature: float = 1.0):
    """Ensemble baseline using ControlArena's ensemble_monitor_builder.

    Generates multiple suspicion scores at the given temperature and
    returns their average as the final suspicion score.

    Args:
        num_samples: Number of suspicion scores to generate and average.
        temperature: Sampling temperature for model responses.

    Returns:
        An ensemble monitor agent built via ensemble_monitor_builder.
    """
    return ensemble_monitor_builder(num_samples=num_samples, temperature=temperature)
