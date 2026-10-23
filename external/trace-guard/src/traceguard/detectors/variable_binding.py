"""Variable Binding Table for tracking shell variable assignments across trajectory steps.

Pure-function module — no LLM calls. All functions return new objects (immutable).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# Matches: VAR='value', VAR="value", VAR=value (unquoted, no spaces)
# Also handles: export VAR=value, declare VAR=value
_ASSIGNMENT_RE = re.compile(
    r"(?:^|(?<=\s)|(?<=;))"          # start of string, after whitespace, or after ;
    r"(?:export\s+|declare\s+)?"     # optional export/declare prefix
    r"([A-Za-z_][A-Za-z0-9_]*)"      # variable name (group 1)
    r"="                              # equals sign
    r"(?:"
    r"'([^']*)'"                      # single-quoted value (group 2)
    r"|\"([^\"]*)\""                  # double-quoted value (group 3)
    r"|([^\s;'\"]*)"                  # unquoted value (group 4)
    r")"
)

# Matches: ${VAR} or $VAR (not inside single quotes)
_VAR_REF_BRACED_RE = re.compile(r"\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_VAR_REF_PLAIN_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


@dataclass(frozen=True)
class VariableBindingTable:
    """Tracks shell variable assignments across trajectory steps."""

    bindings: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, str]:
        """Serialize to a JSON-compatible dict for AgentState.store."""
        return dict(self.bindings)

    @classmethod
    def from_dict(cls, data: dict[str, str]) -> VariableBindingTable:
        """Deserialize from a dict stored in AgentState.store."""
        return cls(bindings=dict(data))


def parse_variable_assignments(command: str) -> dict[str, str]:
    """Extract variable assignments from a bash command string.

    Detects patterns: VAR='value', VAR="value", VAR=value,
    export VAR=value, declare VAR=value.
    Returns dict of variable_name -> assigned_value.
    Later assignments in the same command overwrite earlier ones.
    """
    assignments: dict[str, str] = {}
    for match in _ASSIGNMENT_RE.finditer(command):
        name = match.group(1)
        # Pick whichever capture group matched
        value = match.group(2) if match.group(2) is not None else (
            match.group(3) if match.group(3) is not None else (
                match.group(4) or ""
            )
        )
        assignments[name] = value
    return assignments


def resolve_command(command: str, bindings: dict[str, str]) -> str:
    """Substitute all tracked variable references in a command.

    Handles ${VAR}, $VAR, and "${VAR}" patterns.
    Only substitutes variables present in *bindings*; unknown references
    are left as-is.
    Returns the fully resolved command string.
    """
    if not bindings:
        return command

    # Replace ${VAR} first (more specific), then $VAR
    result = _VAR_REF_BRACED_RE.sub(
        lambda m: bindings.get(m.group(1), m.group(0)),
        command,
    )
    result = _VAR_REF_PLAIN_RE.sub(
        lambda m: bindings.get(m.group(1), m.group(0)),
        result,
    )
    return result


def update_binding_table(
    table: VariableBindingTable, command: str
) -> VariableBindingTable:
    """Parse assignments from command and return an updated table.

    Later assignments overwrite earlier ones for the same variable.
    Returns a new VariableBindingTable (does not mutate input).
    """
    new_assignments = parse_variable_assignments(command)
    if not new_assignments:
        return table

    merged = {**table.bindings, **new_assignments}
    return VariableBindingTable(bindings=merged)
