"""Create the application database and ORM tables."""

from app.database.base import Base
from app.database.database import engine
from app.models.internship import Internship  # noqa: F401


def main() -> None:
    """Create all registered database tables."""
    try:
        Base.metadata.create_all(bind=engine)
        print("Database and tables created successfully.")
    except Exception as exc:
        print(f"Failed to create database and tables: {exc}")


if __name__ == "__main__":
    main()
