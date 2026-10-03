from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

DB_PATH = Path(__file__).resolve().parent.parent.parent / "condominio.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass

@contextmanager
def get_db_session(db: Session | None = None) -> Generator[Session]:
    if db is not None:
        yield db
        return

    session = SessionLocal()
    try:
        yield session
    except Exception:
        session.rollback()
    finally:
        session.close()
