import asyncio
import time


class RateLimiter:
    def __init__(self, rpm: int) -> None:
        self._rpm = rpm
        self._calls: list[float] = []

    def wait_seconds(self, now: float | None = None) -> float:
        now = now or time.monotonic()
        self._calls = [t for t in self._calls if now - t < 60]
        if len(self._calls) < self._rpm:
            return 0.0
        return 60.0 - (now - self._calls[0])

    def record(self, now: float | None = None) -> None:
        self._calls.append(now or time.monotonic())

    async def acquire(self) -> None:
        wait = self.wait_seconds()
        if wait > 0:
            await asyncio.sleep(wait)
        self.record()
