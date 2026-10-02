from pairo.infrastructure.llm.pricing import cost_usd


def test_known_model_is_priced_linearly() -> None:
    one = cost_usd("gpt-4o-mini", 1_000, 1_000)
    assert one is not None and one > 0
    assert cost_usd("gpt-4o-mini", 2_000, 2_000) == 2 * one


def test_unknown_or_missing_model_has_no_price() -> None:
    assert cost_usd("fake", 1_000, 1_000) is None
    assert cost_usd(None, 1_000, 1_000) is None
