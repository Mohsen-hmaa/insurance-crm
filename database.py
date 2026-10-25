import os
import sys
from pathlib import Path
from contextlib import contextmanager
from sqlalchemy import create_engine, event
from sqlalchemy.engine import URL
from sqlalchemy.orm import declarative_base, sessionmaker
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    if getattr(sys, "frozen", False):
        # نسخه اجرایی: دیتابیس کنار فایل EXE
        database_path = (
            Path(sys.executable).resolve().parent / "insurance.db"
        )
    else:
        # اجرای معمولی پایتون: دیتابیس کنار database.py
        database_path = (
            Path(__file__).resolve().parent / "insurance.db"
        )
    DATABASE_URL = URL.create(
        "sqlite",
        database=str(database_path),
    )
engine = create_engine(
    DATABASE_URL,
    echo=False,
    connect_args={"check_same_thread": False},
)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """فعال‌سازی WAL برای بهبود کار با SQLite."""
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()
@contextmanager
def get_db():
    """مدیریت خودکار commit، rollback و بستن نشست دیتابیس."""
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()