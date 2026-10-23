"""TraceGuard detector modules for pre-processing enrichment in the monitor pipeline.

Exports all public classes, functions, and constants from the 7 detector modules:
- variable_binding: Variable indirection detection
- dual_purpose: Dual-purpose script detection
- data_flow: Timing-separated data flow tracking
- string_assembly: String assembly detection
- encoding: Encoding/obfuscation detection
- config_diff: Incremental config manipulation detection
- intent_analyzer: Contextual threat interpretation via Claude Opus (optional, INTENT_MODEL)
"""

from traceguard.detectors.variable_binding import (
    VariableBindingTable,
    parse_variable_assignments,
    resolve_command,
    update_binding_table,
)
from traceguard.detectors.dual_purpose import (
    DualPurposeResult,
    ATTACK_INDICATOR_PATTERNS,
    extract_file_writes,
    analyze_file_content,
)
from traceguard.detectors.data_flow import (
    DataFlowEvent,
    DataFlowState,
    detect_sensitive_read,
    detect_network_egress,
    update_data_flow,
    check_exfiltration,
)
from traceguard.detectors.string_assembly import (
    StringFragment,
    StringAssemblyState,
    DANGEROUS_STRINGS,
    record_fragments,
    check_dangerous_assembly,
)
from traceguard.detectors.encoding import (
    EncodingEvent,
    EncodingState,
    ENCODING_PATTERNS,
    detect_encoding,
    update_encoding_state,
    check_encoded_exfiltration,
)
from traceguard.detectors.config_diff import (
    ConfigModification,
    ConfigDiffState,
    SECURITY_CONFIG_FILES,
    DEGRADATION_PATTERNS,
    detect_config_modification,
    update_config_diffs,
    check_security_degradation,
)
from traceguard.detectors.intent_analyzer import (
    IntentAnalysis,
    THREAT_BOOST,
    analyze_intent,
    parse_intent_response,
    format_detector_findings,
)

__all__ = [
    # variable_binding
    "VariableBindingTable",
    "parse_variable_assignments",
    "resolve_command",
    "update_binding_table",
    # dual_purpose
    "DualPurposeResult",
    "ATTACK_INDICATOR_PATTERNS",
    "extract_file_writes",
    "analyze_file_content",
    # data_flow
    "DataFlowEvent",
    "DataFlowState",
    "detect_sensitive_read",
    "detect_network_egress",
    "update_data_flow",
    "check_exfiltration",
    # string_assembly
    "StringFragment",
    "StringAssemblyState",
    "DANGEROUS_STRINGS",
    "record_fragments",
    "check_dangerous_assembly",
    # encoding
    "EncodingEvent",
    "EncodingState",
    "ENCODING_PATTERNS",
    "detect_encoding",
    "update_encoding_state",
    "check_encoded_exfiltration",
    # config_diff
    "ConfigModification",
    "ConfigDiffState",
    "SECURITY_CONFIG_FILES",
    "DEGRADATION_PATTERNS",
    "detect_config_modification",
    "update_config_diffs",
    "check_security_degradation",
    # intent_analyzer
    "IntentAnalysis",
    "THREAT_BOOST",
    "analyze_intent",
    "parse_intent_response",
    "format_detector_findings",
]
