"""SQLAlchemy engine configuration loaded from application settings."""

from pathlib import Path

import yaml
from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

_SETTINGS_PATH = Path(__file__).resolve().parent.parent / "config" / "settings.yaml"
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent


def _load_database_path() -> Path:
    """Read the SQLite database file path from settings.yaml."""
    with _SETTINGS_PATH.open(encoding="utf-8") as settings_file:
        settings = yaml.safe_load(settings_file)

    database_path = (settings or {}).get("database", {}).get("path")
    if not database_path:
        raise ValueError(
            f"'database.path' is missing or empty in {_SETTINGS_PATH}"
        )

    return _PROJECT_ROOT / database_path


def _build_sqlite_url(db_path: Path) -> str:
    """Build a SQLAlchemy-compatible SQLite connection URL."""
    return f"sqlite:///{db_path.resolve().as_posix()}"


_db_path = _load_database_path()
_db_path.parent.mkdir(parents=True, exist_ok=True)

# SQLAlchemy 2.x uses future-style engine behavior by default; no future= flag exists.
engine: Engine = create_engine(
    _build_sqlite_url(_db_path),
    echo=False,
)
