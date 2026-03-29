"""
SQLAlchemy database engine, session factory, and base model.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from config.settings import settings


engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, pool_size=10)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    """Base class for all ORM models."""
    pass


def init_db():
    """Create all tables if they do not exist."""
    from models.user import User  # noqa: F401
    from models.quote import Quote  # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_session():
    """Context-manager-friendly session getter."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
