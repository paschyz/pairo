from pairo.domain.finding import Axis, Finding, Source


def test_finding_creation() -> None:
    f = Finding(
        axis=Axis.A11Y,
        file="src/App.vue",
        line=42,
        issue="<img> without alt attribute",
        suggestion='Add alt="description"',
        source=Source.RULE,
    )
    assert f.axis == Axis.A11Y
    assert f.file == "src/App.vue"
    assert f.line == 42
    assert f.source == Source.RULE


def test_finding_global_has_no_line() -> None:
    f = Finding(
        axis=Axis.ECO,
        file="assets/hero.png",
        line=None,
        issue="Image exceeds 200 KB",
        suggestion="Compress the image",
        source=Source.RULE,
    )
    assert f.line is None


def test_finding_is_frozen() -> None:
    f = Finding(
        axis=Axis.CRAFTS,
        file="main.py",
        line=10,
        issue="Fonction trop longue",
        suggestion="Extraire en sous-fonctions",
        source=Source.LLM,
    )
    try:
        f.line = 20  # type: ignore[misc]
        raise AssertionError("Should be frozen")
    except AttributeError:
        pass
