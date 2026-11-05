import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL
from sqlalchemy.orm import sessionmaker

load_dotenv()

db_type = os.getenv("DB_TYPE", "mysql").lower()

if db_type == "sqlite" or os.getenv("TESTING") == "1":
    db_path = os.getenv("SQLITE_PATH", "mindthespec.db")
    database_url = f"sqlite:///{db_path}"
    engine = create_engine(
        database_url,
        connect_args={"check_same_thread": False},
    )
else:
    database_url = URL.create(
        drivername="mysql+pymysql",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST", "localhost"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME"),
    )
    engine = create_engine(
        database_url,
        pool_pre_ping=True,
        pool_recycle=3600,
    )

from app.models.base import Base

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def test_connection():
    with engine.connect() as connection:
        if "sqlite" in str(engine.url):
            result = connection.execute(text("SELECT 1"))
            return "sqlite"
        result = connection.execute(text("SELECT DATABASE()"))
        return result.scalar()
