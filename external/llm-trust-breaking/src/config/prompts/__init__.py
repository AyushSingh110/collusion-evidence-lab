"""
Prompts module - maintains backward compatibility.
All prompts are now organized by game in game/ folders.
Uses lazy loading to avoid circular imports.
"""

# Core components
from .core import GAME_RULES, JSON_FORMATS, COMMUNICATION_INSTRUCTIONS

# Builders
from .builders import build_system_prompt, build_user_prompt

# Judge prompts (stay in config) - one function per metric
from .judge import (
    # Deceptive behaviors (4)
    get_judge_lying_prompt,
    get_judge_manipulation_prompt,
    get_judge_breaking_promises_prompt,
    get_judge_strategic_exclusion_prompt,
    # Coalition dynamics (5)
    get_judge_attempted_grand_coalition_prompt,
    get_judge_successful_small_coalition_prompt,
    get_judge_fragmentation_prompt,
    get_judge_fallback_strategies_prompt,
    get_judge_opportunistic_pivoting_prompt,
    # Communication tactics (5)
    get_judge_conditional_commitments_prompt,
    get_judge_plan_instability_prompt,
    get_judge_verification_seeking_prompt,
    get_judge_leverage_tactics_prompt,
    get_judge_public_private_divergence_prompt,
    # Summary
    get_judge_summary_prompt,
)

# Hybrid mode prompts
from .hybrid import (
    get_hybrid_takeaway_system_prompt,
    get_hybrid_takeaway_user_prompt,
)

# Utils
from .utils import format_conversation_history

# Lazy imports for game-specific prompts to avoid circular imports
_game_prompts = {}

def __getattr__(name):
    """Lazy load game prompts on first access."""
    if name in _game_prompts:
        return _game_prompts[name]
    
    # Coordination prompts
    if name == 'get_coordination_system_prompt':
        from game.coordination.prompts import get_coordination_system_prompt
        _game_prompts[name] = get_coordination_system_prompt
        return get_coordination_system_prompt
    elif name == 'get_coordination_dm_user_prompt':
        from game.coordination.prompts import get_coordination_dm_user_prompt
        _game_prompts[name] = get_coordination_dm_user_prompt
        return get_coordination_dm_user_prompt
    elif name == 'get_coordination_pointing_system_prompt':
        from game.coordination.prompts import get_coordination_pointing_system_prompt
        _game_prompts[name] = get_coordination_pointing_system_prompt
        return get_coordination_pointing_system_prompt
    elif name == 'get_coordination_pointing_user_prompt':
        from game.coordination.prompts import get_coordination_pointing_user_prompt
        _game_prompts[name] = get_coordination_pointing_user_prompt
        return get_coordination_pointing_user_prompt
    elif name == 'get_coordination_multidm_system_prompt':
        from game.coordination.prompts import get_coordination_multidm_system_prompt
        _game_prompts[name] = get_coordination_multidm_system_prompt
        return get_coordination_multidm_system_prompt
    elif name == 'get_coordination_multidm_user_prompt':
        from game.coordination.prompts import get_coordination_multidm_user_prompt
        _game_prompts[name] = get_coordination_multidm_user_prompt
        return get_coordination_multidm_user_prompt
    
    # Fishing prompts
    elif name == 'get_fishing_dm_system_prompt':
        from game.fishing.prompts import get_fishing_dm_system_prompt
        _game_prompts[name] = get_fishing_dm_system_prompt
        return get_fishing_dm_system_prompt
    elif name == 'get_fishing_dm_user_prompt':
        from game.fishing.prompts import get_fishing_dm_user_prompt
        _game_prompts[name] = get_fishing_dm_user_prompt
        return get_fishing_dm_user_prompt
    elif name == 'get_fishing_decision_system_prompt':
        from game.fishing.prompts import get_fishing_decision_system_prompt
        _game_prompts[name] = get_fishing_decision_system_prompt
        return get_fishing_decision_system_prompt
    elif name == 'get_fishing_decision_user_prompt':
        from game.fishing.prompts import get_fishing_decision_user_prompt
        _game_prompts[name] = get_fishing_decision_user_prompt
        return get_fishing_decision_user_prompt
    elif name == 'get_fishing_roundrobin_system_prompt':
        from game.fishing.prompts import get_fishing_roundrobin_system_prompt
        _game_prompts[name] = get_fishing_roundrobin_system_prompt
        return get_fishing_roundrobin_system_prompt
    elif name == 'get_fishing_roundrobin_user_prompt':
        from game.fishing.prompts import get_fishing_roundrobin_user_prompt
        _game_prompts[name] = get_fishing_roundrobin_user_prompt
        return get_fishing_roundrobin_user_prompt
    elif name == 'get_fishing_roundrobin_decision_system_prompt':
        from game.fishing.prompts import get_fishing_roundrobin_decision_system_prompt
        _game_prompts[name] = get_fishing_roundrobin_decision_system_prompt
        return get_fishing_roundrobin_decision_system_prompt
    elif name == 'get_fishing_roundrobin_decision_user_prompt':
        from game.fishing.prompts import get_fishing_roundrobin_decision_user_prompt
        _game_prompts[name] = get_fishing_roundrobin_decision_user_prompt
        return get_fishing_roundrobin_decision_user_prompt
    
    # Public goods prompts
    elif name == 'get_publicgoods_dm_system_prompt':
        from game.publicgoods.prompts import get_publicgoods_dm_system_prompt
        _game_prompts[name] = get_publicgoods_dm_system_prompt
        return get_publicgoods_dm_system_prompt
    elif name == 'get_publicgoods_dm_user_prompt':
        from game.publicgoods.prompts import get_publicgoods_dm_user_prompt
        _game_prompts[name] = get_publicgoods_dm_user_prompt
        return get_publicgoods_dm_user_prompt
    elif name == 'get_publicgoods_decision_system_prompt':
        from game.publicgoods.prompts import get_publicgoods_decision_system_prompt
        _game_prompts[name] = get_publicgoods_decision_system_prompt
        return get_publicgoods_decision_system_prompt
    elif name == 'get_publicgoods_decision_user_prompt':
        from game.publicgoods.prompts import get_publicgoods_decision_user_prompt
        _game_prompts[name] = get_publicgoods_decision_user_prompt
        return get_publicgoods_decision_user_prompt
    elif name == 'get_publicgoods_roundrobin_system_prompt':
        from game.publicgoods.prompts import get_publicgoods_roundrobin_system_prompt
        _game_prompts[name] = get_publicgoods_roundrobin_system_prompt
        return get_publicgoods_roundrobin_system_prompt
    elif name == 'get_publicgoods_roundrobin_user_prompt':
        from game.publicgoods.prompts import get_publicgoods_roundrobin_user_prompt
        _game_prompts[name] = get_publicgoods_roundrobin_user_prompt
        return get_publicgoods_roundrobin_user_prompt
    elif name == 'get_publicgoods_roundrobin_decision_system_prompt':
        from game.publicgoods.prompts import get_publicgoods_roundrobin_decision_system_prompt
        _game_prompts[name] = get_publicgoods_roundrobin_decision_system_prompt
        return get_publicgoods_roundrobin_decision_system_prompt
    elif name == 'get_publicgoods_roundrobin_decision_user_prompt':
        from game.publicgoods.prompts import get_publicgoods_roundrobin_decision_user_prompt
        _game_prompts[name] = get_publicgoods_roundrobin_decision_user_prompt
        return get_publicgoods_roundrobin_decision_user_prompt
    
    # Round-robin prompts (from builders)
    elif name == 'get_roundrobin_system_prompt':
        from .builders import get_roundrobin_system_prompt
        _game_prompts[name] = get_roundrobin_system_prompt
        return get_roundrobin_system_prompt
    elif name == 'get_roundrobin_user_prompt':
        from .builders import get_roundrobin_user_prompt
        _game_prompts[name] = get_roundrobin_user_prompt
        return get_roundrobin_user_prompt
    
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

__all__ = [
    # Core
    'GAME_RULES',
    'JSON_FORMATS',
    'COMMUNICATION_INSTRUCTIONS',
    # Builders
    'build_system_prompt',
    'build_user_prompt',
    # Judge (14 metrics + 1 summary)
    'get_judge_lying_prompt',
    'get_judge_manipulation_prompt',
    'get_judge_breaking_promises_prompt',
    'get_judge_strategic_exclusion_prompt',
    'get_judge_attempted_grand_coalition_prompt',
    'get_judge_successful_small_coalition_prompt',
    'get_judge_fragmentation_prompt',
    'get_judge_fallback_strategies_prompt',
    'get_judge_opportunistic_pivoting_prompt',
    'get_judge_conditional_commitments_prompt',
    'get_judge_plan_instability_prompt',
    'get_judge_verification_seeking_prompt',
    'get_judge_leverage_tactics_prompt',
    'get_judge_public_private_divergence_prompt',
    'get_judge_summary_prompt',
    # Hybrid
    'get_hybrid_takeaway_system_prompt',
    'get_hybrid_takeaway_user_prompt',
    # Utils
    'format_conversation_history',
    # Coordination
    'get_coordination_system_prompt',
    'get_coordination_dm_user_prompt',
    'get_coordination_pointing_system_prompt',
    'get_coordination_pointing_user_prompt',
    'get_coordination_multidm_system_prompt',
    'get_coordination_multidm_user_prompt',
    # Fishing
    'get_fishing_dm_system_prompt',
    'get_fishing_dm_user_prompt',
    'get_fishing_decision_system_prompt',
    'get_fishing_decision_user_prompt',
    'get_fishing_roundrobin_system_prompt',
    'get_fishing_roundrobin_user_prompt',
    'get_fishing_roundrobin_decision_system_prompt',
    'get_fishing_roundrobin_decision_user_prompt',
    # Public goods
    'get_publicgoods_dm_system_prompt',
    'get_publicgoods_dm_user_prompt',
    'get_publicgoods_decision_system_prompt',
    'get_publicgoods_decision_user_prompt',
    'get_publicgoods_roundrobin_system_prompt',
    'get_publicgoods_roundrobin_user_prompt',
    'get_publicgoods_roundrobin_decision_system_prompt',
    'get_publicgoods_roundrobin_decision_user_prompt',
    # Round-robin
    'get_roundrobin_system_prompt',
    'get_roundrobin_user_prompt',
]
