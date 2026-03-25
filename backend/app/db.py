from __future__ import annotations

from collections.abc import Generator
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker


def _default_database_url() -> str:
    return os.getenv("PAPER_DATABASE_URL", "sqlite:///./paper.db").strip() or "sqlite:///./paper.db"


def _create_engine():
    database_url = _default_database_url()
    connect_args = {"check_same_thread": False} if database_url.startswith("sqlite") else {}
    return create_engine(database_url, future=True, connect_args=connect_args)


class Base(DeclarativeBase):
    pass


engine = _create_engine()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, expire_on_commit=False)


def init_schema() -> None:
    from app import models  # noqa: F401

    Base.metadata.create_all(bind=engine)


def get_db_session() -> Generator[Session, None, None]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
