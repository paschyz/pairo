from pairo.domain.finding import Finding
from pairo.domain.ports import FileDiff

# Increment when prompts change to invalidate cache
PROMPT_VERSION = "4"

_AXIS_DESCRIPTIONS: dict[str, str] = {
    "crafts": "naming, long functions, duplication, dead code, readability",
    "eco": (
        "N+1 queries, missing pagination, heavy dependencies, unnecessary computation"
    ),
    "a11y": ("missing alt, low contrast, non-semantic elements, keyboard navigation"),
}

_SYSTEM = "You are an expert code reviewer. Analyze added lines (+) and report issues."
_OUTPUT = (
    "\nRespond only in JSON, array of objects with: "
    '"axis", "file", "line", "issue", "suggestion". '
    "Empty array [] if nothing to report."
    '\nOptionally add "code_suggestion": {"replacement": "<new code for '
    'the line(s)>", "end_line": <last line, only if multi-line>} ONLY when '
    "the fix is local, precise, limited to added lines (+) listed above "
    '(consecutive lines for a range, starting at "line"), needs no other '
    "file change and you are confident. Omit it for architectural issues "
    "or large refactors."
)


def build_prompt(
    files: list[FileDiff],
    existing_findings: list[Finding],
    axes: list[str],
    language: str,
) -> str:
    parts: list[str] = [_SYSTEM, "\nAxes to check:"]

    for axis in axes:
        parts.append(f"- {axis}: {_AXIS_DESCRIPTIONS.get(axis, axis)}")

    if files:
        parts.append("\nFiles:")
        for f in files:
            parts.append(f"\n--- {f.path} ---")
            for line in f.added_lines:
                parts.append(f"{line.number}: {line.content}")
    else:
        parts.append("\nNo files to analyze.")

    if existing_findings:
        parts.append("\nAlready detected findings (do not duplicate):")
        for finding in existing_findings:
            parts.append(
                f"- [{finding.axis}] {finding.file}:{finding.line}: {finding.issue}"
            )

    parts.append(_OUTPUT)
    if language != "en":
        parts.append(
            f'Write the "issue" and "suggestion" text in the language '
            f'with code "{language}".'
        )
    return "\n".join(parts)
