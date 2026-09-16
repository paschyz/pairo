import re
from dataclasses import dataclass

HUNK_HEADER = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,\d+)? @@")


@dataclass(frozen=True)
class AddedLine:
    number: int
    content: str


def parse_patch(patch: str) -> list[AddedLine]:
    """Parse a unified diff patch into added lines with their new-file line numbers."""
    if not patch:
        return []

    result: list[AddedLine] = []
    current_line = 0

    for raw in patch.splitlines():
        m = HUNK_HEADER.match(raw)
        if m:
            current_line = int(m.group(1))
        elif raw.startswith("+"):
            result.append(AddedLine(number=current_line, content=raw[1:]))
            current_line += 1
        elif raw.startswith("-") or raw.startswith("\\"):
            pass
        else:
            current_line += 1

    return result
