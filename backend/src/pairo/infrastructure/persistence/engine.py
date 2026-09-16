from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from pairo.config import settings

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None


def _init() -> None:
    global _engine, _SessionLocal  # noqa: PLW0603
    url = settings.database_url
    connect_args = (
        {"check_same_thread": False} if url.startswith("sqlite") else {}
    )
    _engine = create_engine(url, connect_args=connect_args)
    _SessionLocal = sessionmaker(bind=_engine)


def get_session() -> Session:
    if _SessionLocal is None:
        _init()
    assert _SessionLocal is not None
    return _SessionLocal()
