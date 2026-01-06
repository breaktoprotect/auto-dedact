from datetime import datetime, timezone
from typing import Any, Optional
from sqlmodel import SQLModel, Field
from pgvector.sqlalchemy import VECTOR


class RegexRuleSQL(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(index=True)
    domain: str = Field(index=True)
    data_category: str = Field(index=True)

    description: str
    pattern: str

    pattern_hash: str = Field(
        index=True,
        unique=True,
        nullable=False,
    )

    active: bool = Field(default=True)

    # todo: pgvector column (choose your embedding dim)
    embedding: Optional[Any] = Field(default=None, sa_type=VECTOR(768))  # type: ignore

    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
