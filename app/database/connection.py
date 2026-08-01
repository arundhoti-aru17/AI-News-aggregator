import os

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from pathlib import Path

from dotenv import load_dotenv

load_dotenv()
from pathlib import Path
from dotenv import load_dotenv

ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
print("Loading:", ENV_PATH)
print("Exists:", ENV_PATH.exists())

load_dotenv(dotenv_path=ENV_PATH)

def get_database_url() -> str:
    user = os.getenv("POSTGRES_USER", "postgres")
    password = os.getenv("POSTGRES_PASSWORD", "postgres")
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    db = os.getenv("POSTGRES_DB", "ai_news_aggregator")
    sslmode = os.getenv("POSTGRES_SSLMODE", "prefer")

    return f"postgresql://{user}:{password}@{host}:{port}/{db}?sslmode={sslmode}"


engine = create_engine(get_database_url())

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


def get_session():
    return SessionLocal()