from pairo.infrastructure.llm.rate_limiter import RateLimiter


def test_no_wait_under_limit() -> None:
    limiter = RateLimiter(rpm=3)
    assert limiter.wait_seconds(now=100.0) == 0.0


def test_no_wait_when_calls_within_limit() -> None:
    limiter = RateLimiter(rpm=3)
    limiter.record(90.0)
    limiter.record(95.0)
    assert limiter.wait_seconds(now=100.0) == 0.0


def test_wait_when_limit_reached() -> None:
    limiter = RateLimiter(rpm=2)
    limiter.record(50.0)
    limiter.record(55.0)
    wait = limiter.wait_seconds(now=60.0)
    assert wait > 0
    assert wait <= 50.0  # must wait until 50+60=110, so ~50s


def test_old_calls_expire() -> None:
    limiter = RateLimiter(rpm=2)
    limiter.record(10.0)
    limiter.record(20.0)
    assert limiter.wait_seconds(now=71.0) == 0.0


def test_record_adds_timestamp() -> None:
    limiter = RateLimiter(rpm=5)
    limiter.record(1.0)
    limiter.record(2.0)
    assert len(limiter._calls) == 2
