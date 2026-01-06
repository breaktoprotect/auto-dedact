from contextlib import contextmanager
from typing import Iterator

from sqlmodel import Session, create_engine
from dotenv import load_dotenv

from app.utils.env_validation import require_env

load_dotenv(".env.local")

ENV = require_env(
    [
        "DATABASE_HOST",
        "DATABASE_PORT",
        "DATABASE_USERNAME",
        "DATABASE_PASSWORD",
        "DATABASE_NAME",
    ]
)

DATABASE_URL = ENV.get("DATABASE_URL") or (
    f"postgresql+psycopg://{ENV['DATABASE_USERNAME']}:{ENV['DATABASE_PASSWORD']}"
    f"@{ENV['DATABASE_HOST']}:{ENV['DATABASE_PORT']}/{ENV['DATABASE_NAME']}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)


@contextmanager
def get_session() -> Iterator[Session]:
    with Session(engine) as session:
        yield session
