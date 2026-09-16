"""Parse @pairo commands from comment text. Pure domain."""

import re
from dataclasses import dataclass

_COMMAND_RE = re.compile(
    r"@pairo\s+(ignore|valid)(?:\s+(.+))?", re.IGNORECASE
)

_VALID_ACTIONS = {"ignore", "valid"}


@dataclass(frozen=True)
class PairoCommand:
    action: str  # "ignore" or "valid"
    reason: str | None


def parse_command(text: str) -> PairoCommand | None:
    """Extract first @pairo command from text. Returns None if no command found."""
    match = _COMMAND_RE.search(text)
    if not match:
        return None
    action = match.group(1).lower()
    reason = match.group(2).strip() if match.group(2) else None
    return PairoCommand(action=action, reason=reason)
