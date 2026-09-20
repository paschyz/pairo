from pairo.domain.finding import Finding
from pairo.domain.ports import FileDiff

# Increment when prompts change to invalidate cache
PROMPT_VERSION = "2"

_AXIS_DESCRIPTIONS: dict[str, dict[str, str]] = {
    "crafts": {
        "en": "naming, long functions, duplication, dead code, readability",
        "fr": "nommage, fonctions longues, duplication, code mort, lisibilité",
    },
    "eco": {
        "en": "N+1 queries, missing pagination, heavy dependencies, unnecessary computation",
        "fr": "requêtes N+1, absence de pagination, dépendances lourdes, calculs inutiles",
    },
    "a11y": {
        "en": "missing alt, low contrast, non-semantic elements, keyboard navigation",
        "fr": "alt manquant, contraste faible, éléments non sémantiques, navigation clavier",
    },
}

_TEMPLATES = {
    "en": {
        "system": "You are an expert code reviewer. Analyze added lines (+) and report issues.",
        "axes": "\nAxes to check:",
        "files": "\nFiles:",
        "no_files": "\nNo files to analyze.",
        "existing": "\nAlready detected findings (do not duplicate):",
        "output": (
            "\nRespond only in JSON, array of objects with: "
            '"axis", "file", "line", "issue", "suggestion". '
            "Empty array [] if nothing to report."
        ),
    },
    "fr": {
        "system": "Tu es un reviewer de code expert. Analyse les lignes ajoutées (+) et signale les problèmes.",
        "axes": "\nAxes à vérifier :",
        "files": "\nFichiers :",
        "no_files": "\nAucun fichier à analyser.",
        "existing": "\nFindings déjà détectés (ne pas dupliquer) :",
        "output": (
            "\nRéponds uniquement en JSON, tableau d'objets avec : "
            '"axis", "file", "line", "issue", "suggestion". '
            "Tableau vide [] si rien à signaler."
        ),
    },
}


def build_prompt(
    files: list[FileDiff],
    existing_findings: list[Finding],
    axes: list[str],
    language: str,
) -> str:
    t = _TEMPLATES.get(language, _TEMPLATES["en"])
    parts: list[str] = [t["system"], t["axes"]]

    for axis in axes:
        descs = _AXIS_DESCRIPTIONS.get(axis)
        desc = descs.get(language, descs.get("en", axis)) if descs else axis
        parts.append(f"- {axis}: {desc}")

    if files:
        parts.append(t["files"])
        for f in files:
            parts.append(f"\n--- {f.path} ---")
            for line in f.added_lines:
                parts.append(f"{line.number}: {line.content}")
    else:
        parts.append(t["no_files"])

    if existing_findings:
        parts.append(t["existing"])
        for finding in existing_findings:
            parts.append(
                f"- [{finding.axis}] {finding.file}:{finding.line}: "
                f"{finding.issue}"
            )

    parts.append(t["output"])
    return "\n".join(parts)
