import asyncio
from collections import Counter
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from statistics import median
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from pairo.domain.finding import Axis, Finding, Source
from pairo.domain.review import Review
from pairo.infrastructure.persistence.models import FindingRow, ReviewRow

# (model, input_tokens, output_tokens) -> USD, or None when the model has no price
Price = Callable[[str | None, int, int], float | None]


class SqlReviewRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    async def save(self, review: Review) -> None:
        def _save() -> None:
            row = ReviewRow(
                delivery_id=review.delivery_id,
                owner=review.owner,
                repo=review.repo,
                pr_number=review.pr_number,
                head_sha=review.head_sha,
                model=review.model,
                input_tokens=review.input_tokens,
                output_tokens=review.output_tokens,
                co2_g=review.co2_g,
                pr_created_at=review.pr_created_at,
            )
            for f in review.findings:
                row.findings.append(
                    FindingRow(
                        axis=f.axis.value,
                        file=f.file,
                        line=f.line,
                        issue=f.issue,
                        suggestion=f.suggestion,
                        source=f.source.value,
                    )
                )
            self._session.add(row)
            self._session.commit()
            self._session.refresh(row)
            review.id = row.id
            review.created_at = row.created_at

        await asyncio.to_thread(_save)

    async def exists(self, delivery_id: str) -> bool:
        def _exists() -> bool:
            stmt = select(ReviewRow.id).where(ReviewRow.delivery_id == delivery_id)
            return self._session.execute(stmt).scalar() is not None

        return await asyncio.to_thread(_exists)

    async def get(self, review_id: int) -> Review | None:
        def _get() -> Review | None:
            row = self._session.get(ReviewRow, review_id)
            if row is None:
                return None
            return _to_domain(row)

        return await asyncio.to_thread(_get)

    async def list_reviews(self, offset: int = 0, limit: int = 20) -> list[Review]:
        def _list() -> list[Review]:
            # one row per PR: its latest review
            latest = select(func.max(ReviewRow.id)).group_by(
                ReviewRow.owner, ReviewRow.repo, ReviewRow.pr_number
            )
            stmt = (
                select(ReviewRow)
                .where(ReviewRow.id.in_(latest))
                .order_by(ReviewRow.created_at.desc(), ReviewRow.id.desc())
                .offset(offset)
                .limit(limit)
            )
            rows = self._session.scalars(stmt).all()
            return [_to_domain(r) for r in rows]

        return await asyncio.to_thread(_list)

    async def list_for_pr(self, owner: str, repo: str, pr_number: int) -> list[Review]:
        def _list() -> list[Review]:
            stmt = (
                select(ReviewRow)
                .where(
                    ReviewRow.owner == owner,
                    ReviewRow.repo == repo,
                    ReviewRow.pr_number == pr_number,
                )
                .order_by(ReviewRow.created_at.desc(), ReviewRow.id.desc())
            )
            return [_to_domain(r) for r in self._session.scalars(stmt).all()]

        return await asyncio.to_thread(_list)

    async def today_review_count(self) -> int:
        def _count() -> int:
            today = datetime.now(tz=UTC).date()
            stmt = select(func.count(ReviewRow.id)).where(
                func.date(ReviewRow.created_at) == today
            )
            return self._session.execute(stmt).scalar() or 0

        return await asyncio.to_thread(_count)

    async def stats(self) -> dict[str, int]:
        def _stats() -> dict[str, int]:
            review_count = (
                self._session.execute(select(func.count(ReviewRow.id))).scalar() or 0
            )
            finding_count = (
                self._session.execute(select(func.count(FindingRow.id))).scalar() or 0
            )
            input_tok = (
                self._session.execute(
                    select(func.coalesce(func.sum(ReviewRow.input_tokens), 0))
                ).scalar()
                or 0
            )
            output_tok = (
                self._session.execute(
                    select(func.coalesce(func.sum(ReviewRow.output_tokens), 0))
                ).scalar()
                or 0
            )
            return {
                "total_reviews": int(review_count),
                "total_findings": int(finding_count),
                "total_input_tokens": int(input_tok),
                "total_output_tokens": int(output_tok),
            }

        return await asyncio.to_thread(_stats)

    async def kpis(self, price: Price) -> dict[str, Any]:
        """Usage, cost and finding breakdowns for the dashboard."""

        def _kpis() -> dict[str, Any]:
            # ponytail: every aggregate scans all reviews; window by date or
            # add a rollup table when the reviews table gets large.
            day = func.date(ReviewRow.created_at)
            usage = self._session.execute(
                select(
                    day,
                    ReviewRow.owner,
                    ReviewRow.repo,
                    ReviewRow.model,
                    func.count(ReviewRow.id),
                    func.sum(ReviewRow.input_tokens),
                    func.sum(ReviewRow.output_tokens),
                ).group_by(day, ReviewRow.owner, ReviewRow.repo, ReviewRow.model)
            ).all()

            repos: dict[str, dict[str, Any]] = {}
            models: dict[str, dict[str, Any]] = {}
            days: dict[str, dict[str, Any]] = {}
            unpriced = 0
            for date, owner, repo, model, n, input_sum, output_sum in usage:
                input_tok, output_tok = int(input_sum or 0), int(output_sum or 0)
                # Judge and rule-classifier calls don't record tokens, so this
                # is the cost of review calls only.
                cost = price(model, input_tok, output_tok)
                if cost is None:
                    unpriced += n
                for bucket, name, key in (
                    (repos, "repo", f"{owner}/{repo}"),
                    (models, "model", model or "unknown"),
                    (days, "date", str(date)),
                ):
                    agg = bucket.setdefault(key, _empty_usage(name, key))
                    agg["reviews"] += n
                    agg["input_tokens"] += input_tok
                    agg["output_tokens"] += output_tok
                    if cost is not None:
                        agg["cost_usd"] = (agg["cost_usd"] or 0.0) + cost

            by_axis: Counter[str] = Counter()
            by_source: Counter[str] = Counter()
            repo_findings: Counter[str] = Counter()
            for owner, repo, axis, source, n in self._session.execute(
                select(
                    ReviewRow.owner,
                    ReviewRow.repo,
                    FindingRow.axis,
                    FindingRow.source,
                    func.count(FindingRow.id),
                )
                .join(FindingRow.review)
                .group_by(
                    ReviewRow.owner, ReviewRow.repo, FindingRow.axis, FindingRow.source
                )
            ):
                by_axis[axis] += n
                by_source[source] += n
                repo_findings[f"{owner}/{repo}"] += n

            repo_prs: Counter[str] = Counter()
            delays: list[float] = []
            for owner, repo, first_review, opened in self._session.execute(
                select(
                    ReviewRow.owner,
                    ReviewRow.repo,
                    func.min(ReviewRow.created_at),
                    func.min(ReviewRow.pr_created_at),
                ).group_by(ReviewRow.owner, ReviewRow.repo, ReviewRow.pr_number)
            ):
                repo_prs[f"{owner}/{repo}"] += 1
                if opened is not None:
                    delays.append((first_review - opened).total_seconds() / 60)

            clean_reviews = (
                self._session.execute(
                    select(func.count(ReviewRow.id)).where(~ReviewRow.findings.any())
                ).scalar()
                or 0
            )

            for name, agg in repos.items():
                agg["prs"] = repo_prs[name]
                agg["findings"] = repo_findings[name]

            costs = [r["cost_usd"] for r in repos.values() if r["cost_usd"] is not None]
            today = datetime.now(tz=UTC).date()
            last_days = (str(today - timedelta(days=i)) for i in range(13, -1, -1))
            return {
                "total_cost_usd": sum(costs) if costs else None,
                "unpriced_reviews": unpriced,
                "total_prs": sum(repo_prs.values()),
                "clean_reviews": int(clean_reviews),
                "median_minutes_to_first_review": (
                    round(median(delays), 1) if delays else None
                ),
                "by_repo": _by_cost(repos, "repo"),
                "by_model": _by_cost(models, "model"),
                "by_axis": dict(by_axis),
                "by_source": dict(by_source),
                "daily": [days.get(d, _empty_usage("date", d)) for d in last_days],
            }

        return await asyncio.to_thread(_kpis)


def _empty_usage(name: str, key: str) -> dict[str, Any]:
    return {
        name: key,
        "reviews": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cost_usd": None,
    }


def _by_cost(bucket: dict[str, dict[str, Any]], name: str) -> list[dict[str, Any]]:
    """Most expensive first; unpriced entries last, then by name."""
    return sorted(bucket.values(), key=lambda a: (-(a["cost_usd"] or 0.0), a[name]))


def _to_domain(row: ReviewRow) -> Review:
    return Review(
        id=row.id,
        delivery_id=row.delivery_id,
        owner=row.owner,
        repo=row.repo,
        pr_number=row.pr_number,
        head_sha=row.head_sha,
        model=row.model,
        input_tokens=row.input_tokens,
        output_tokens=row.output_tokens,
        co2_g=row.co2_g,
        created_at=row.created_at,
        pr_created_at=row.pr_created_at,
        findings=[
            Finding(
                axis=Axis(f.axis),
                file=f.file,
                line=f.line,
                issue=f.issue,
                suggestion=f.suggestion,
                source=Source(f.source),
            )
            for f in row.findings
        ],
    )
