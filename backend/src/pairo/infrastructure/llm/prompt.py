from pairo.domain.finding import Finding
from pairo.domain.ports import FileDiff

_AXIS_DESCRIPTIONS = {
    "crafts": "nommage, fonctions longues, duplication, code mort, lisibilité",
    "eco": "requêtes N+1, absence de pagination, dépendances lourdes, calculs inutiles",
    "a11y": (
        "alt manquant, contraste faible, "
        "éléments non sémantiques, navigation clavier"
    ),
}


def build_prompt(
    files: list[FileDiff],
    existing_findings: list[Finding],
    axes: list[str],
    language: str,
) -> str:
    parts: list[str] = []

    parts.append(
        "Tu es un reviewer de code expert. "
        "Analyse les lignes ajoutées (+) et signale les problèmes."
    )

    parts.append("\nAxes à vérifier :")
    for axis in axes:
        desc = _AXIS_DESCRIPTIONS.get(axis, axis)
        parts.append(f"- {axis} : {desc}")

    if files:
        parts.append("\nFichiers :")
        for f in files:
            parts.append(f"\n--- {f.path} ---")
            for line in f.added_lines:
                parts.append(f"{line.number}: {line.content}")
    else:
        parts.append("\nAucun fichier à analyser.")

    if existing_findings:
        parts.append(
            "\nFindings déjà détectés (ne pas dupliquer) :"
        )
        for finding in existing_findings:
            parts.append(
                f"- [{finding.axis}] {finding.file}:{finding.line} : "
                f"{finding.issue}"
            )

    parts.append(
        "\nRéponds uniquement en JSON, tableau d'objets avec : "
        '"axis", "file", "line", "issue", "suggestion". '
        "Tableau vide [] si rien à signaler."
    )

    return "\n".join(parts)
