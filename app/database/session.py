"""Database session factory and context-managed access."""

from __future__ import annotations

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session, sessionmaker

from app.core.logger import logger
from app.database.database import engine

__all__ = [
    "SessionLocal",
    "get_session",
]


SessionLocal: sessionmaker[Session] = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Yield a transactional SQLAlchemy session.

    The session is committed if the block exits successfully,
    rolled back if an exception occurs, and always closed.
    """
    session = SessionLocal()

    try:
        yield session
        session.commit()

    except Exception:
        session.rollback()
        logger.exception("Database session failed")
        raise

    finally:
        session.close()
