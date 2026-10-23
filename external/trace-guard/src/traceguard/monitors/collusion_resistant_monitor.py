"""Collusion-resistant variant of TraceGuard.

Uses the UNTRUSTED model (same as the agent) but with structured
dimension scoring. The hypothesis: explicit evaluation criteria constrain
what the monitor attends to, making it harder to silently pass attacks
through — even when the monitor is the same model as the agent.

Compare this against simple_untrusted_monitor to test the hypothesis.
"""

from traceguard.dimensions import DEFAULT_DIMENSIONS
from traceguard.monitors.traceguard_monitor import traceguard_monitor


def collusion_resistant_monitor():
    """TraceGuard using the untrusted model for collusion resistance testing.

    By forcing structured evaluation on the untrusted model, we test
    whether dimension-by-dimension scoring constrains the model enough
    to prevent collusion, even when it is the same model as the agent.
    """
    return traceguard_monitor(
        model_role="untrusted",
        dimensions=DEFAULT_DIMENSIONS,
    )
