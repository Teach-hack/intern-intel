"""Database session factory and context-managed access."""

from collections.abc import Generator
from contextlib import contextmanager

from sqlalchemy.orm import Session, sessionmaker

from app.core.logger import logger
from app.database.database import engine

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=Session,
)


@contextmanager
def get_session() -> Generator[Session, None, None]:
    """Provide a transactional database session.

    Commits on successful exit, rolls back on exception, and always closes
    the session.
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        logger.exception("Database session failed")
        session.rollback()
        raise
    finally:
        session.close()
