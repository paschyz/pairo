from pairo.domain.finding import Axis, Finding, Source

_IMAGE_EXTENSIONS = (".png", ".jpg", ".jpeg", ".gif", ".svg", ".webp", ".avif")


def check_image_size(
    path: str, *, size_kb: int, max_kb: int
) -> list[Finding]:
    if not path.lower().endswith(_IMAGE_EXTENSIONS):
        return []
    if size_kb <= max_kb:
        return []
    return [
        Finding(
            axis=Axis.ECO,
            file=path,
            line=None,
            issue=f"Image de {size_kb} Ko dépasse la limite de {max_kb} Ko",
            suggestion="Compresser ou convertir en format plus léger (WebP, AVIF)",
            source=Source.RULE,
        )
    ]
