from sqlmodel import create_engine, Session, SQLModel
from typing import Annotated
from fastapi import Depends
from .config import settings

# Create engine with connection pooling
engine = create_engine(
    url=settings.database_url,
    echo=settings.debug,  # SQL logging in development
    pool_pre_ping=True,  # Verify connection pool before use
    pool_recycle=300,  # Recycle connection pooling every 5 minutes
)


def create_db_and_tables():
    """Create database and tables"""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Database session dependency"""
    with Session(engine) as session:
        yield session


# Type alias for dependency injection
SessionDep = Annotated[Session, Depends(get_session)]
