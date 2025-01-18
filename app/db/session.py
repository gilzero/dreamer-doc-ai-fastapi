# app/db/session.py

from sqlmodel import Session, create_engine
from typing import Generator
from functools import lru_cache
from app.core.config import get_settings

settings = get_settings()

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
    pool_recycle=300  # Recycle connections after 5 minutes
)


def get_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency for database sessions.
    Usage:
        @app.get("/items/")
        def read_items(session: Session = Depends(get_session)):
            items = session.query(Item).all()
            return items
    """
    with Session(engine) as session:
        try:
            yield session
        finally:
            session.close()


# Database initialization
def init_db() -> None:
    """Initialize database with required tables."""
    from app.db.models import SQLModel  # Import here to avoid circular imports

    SQLModel.metadata.create_all(engine)


# Optional: Add database health check
async def check_database_connection() -> bool:
    """
    Check if database is accessible.
    Returns: bool indicating if database is connected
    """
    try:
        with Session(engine) as session:
            # Try to make a simple query
            session.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"Database connection failed: {str(e)}")
        return False


# Migration support (optional)
def run_migrations() -> None:
    """
    Run database migrations using Alembic.
    This is optional but recommended for production use.
    """
    try:
        import alembic.config
        alembic_cfg = alembic.config.Config("alembic.ini")
        alembic.command.upgrade(alembic_cfg, "head")
    except ImportError:
        print("Alembic not installed. Skipping migrations.")
    except Exception as e:
        print(f"Migration failed: {str(e)}")


# Connection management utilities
def close_db_connections() -> None:
    """
    Close all database connections.
    Useful for cleanup during application shutdown.
    """
    engine.dispose()


# Session context manager for cases where dependency injection isn't available
from contextlib import contextmanager


@contextmanager
def manual_session():
    """
    Context manager for database sessions.
    Usage:
        with manual_session() as session:
            items = session.query(Item).all()
    """
    session = Session(engine)
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()