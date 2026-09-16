"""SQLAlchemy implementation of FindingCache."""

import asyncio
import json
from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import select
from sqlalchemy.orm import Session

from pairo.infrastructure.persistence.models import LlmCacheRow


class SqlFindingCache:
    def __init__(self, session: Session, ttl_days: int = 30) -> None:
        self._session = session
        self._ttl = timedelta(days=ttl_days)

    async def get(self, key: str) -> dict[str, Any] | None:
        def _query() -> dict[str, Any] | None:
            stmt = select(LlmCacheRow).where(
                LlmCacheRow.cache_key == key
            )
            row = self._session.scalars(stmt).first()
            if row is None:
                return None
            # TTL check
            if datetime.now(tz=UTC) - row.created_at.replace(
                tzinfo=UTC
            ) > self._ttl:
                self._session.delete(row)
                self._session.commit()
                return None
            return {
                "findings": json.loads(row.findings_json),
                "input_tokens": row.input_tokens,
                "output_tokens": row.output_tokens,
            }

        return await asyncio.to_thread(_query)

    async def put(
        self,
        key: str,
        findings: list[dict[str, Any]],
        *,
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> None:
        def _save() -> None:
            stmt = select(LlmCacheRow).where(
                LlmCacheRow.cache_key == key
            )
            existing = self._session.scalars(stmt).first()
            if existing:
                existing.findings_json = json.dumps(findings)
                existing.input_tokens = input_tokens
                existing.output_tokens = output_tokens
                existing.created_at = datetime.now(tz=UTC)
            else:
                row = LlmCacheRow(
                    cache_key=key,
                    findings_json=json.dumps(findings),
                    input_tokens=input_tokens,
                    output_tokens=output_tokens,
                )
                self._session.add(row)
            self._session.commit()

        await asyncio.to_thread(_save)
