from typing import Optional
from sqlmodel import select
import hashlib
from sqlalchemy.exc import IntegrityError
from loguru import logger

from app.db.session import get_session
from app.db.sqlmodels.regex_rule import RegexRuleSQL
from app.embeddings.embedding_client import embed_text


def create_rule(
    *,
    name: str,
    domain: str,
    data_category: str,
    description: str,
    pattern: str,
    active: bool = True,
) -> RegexRuleSQL:
    # * Encode text to vector embeddings
    embedding_text = _get_embedding_text(
        name=name,
        description=description,
    )

    embedding = embed_text(embedding_text)
    pat_hash = _pattern_hash(pattern)

    with get_session() as session:
        rule = RegexRuleSQL(
            name=name,
            domain=domain,
            data_category=data_category,
            description=description,
            pattern=pattern,
            pattern_hash=pat_hash,
            active=active,
            embedding=embedding,
        )
        session.add(rule)

        # Handle the event of a pattern hash collision
        try:
            session.commit()
        except Exception:
            session.rollback()
            stmt = select(RegexRuleSQL).where(RegexRuleSQL.pattern_hash == pat_hash)
            existing = session.exec(stmt).first()
            if existing:
                logger.warning(
                    "Duplicate regex rule blocked (pattern_hash collision)",
                    extra={
                        "pattern_hash": pat_hash,
                        "existing_rule_id": existing.id,
                        "name": name,
                        "domain": domain,
                        "data_category": data_category,
                    },
                )
                return existing
            raise

        session.refresh(rule)
        return rule


def get_rule_by_id(rule_id: int) -> Optional[RegexRuleSQL]:
    with get_session() as session:
        return session.get(RegexRuleSQL, rule_id)


def get_rule_by_name(name: str) -> Optional[RegexRuleSQL]:
    with get_session() as session:
        stmt = select(RegexRuleSQL).where(RegexRuleSQL.name == name)
        return session.exec(stmt).first()


def list_rules(
    domain: Optional[str] = None,
    data_category: Optional[str] = None,
    active: Optional[bool] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[RegexRuleSQL]:
    with get_session() as session:
        stmt = select(RegexRuleSQL)

        if domain is not None:
            stmt = stmt.where(RegexRuleSQL.domain == domain)
        if data_category is not None:
            stmt = stmt.where(RegexRuleSQL.data_category == data_category)
        if active is not None:
            stmt = stmt.where(RegexRuleSQL.active == active)
        if limit:
            stmt = stmt.limit(limit)
        if offset:
            stmt = stmt.offset(offset)

        return list(session.exec(stmt).all())


def list_all_rules(*, active: bool = True) -> list[RegexRuleSQL]:
    stmt = select(RegexRuleSQL)
    with get_session() as session:
        return list(session.exec(stmt).all())


def update_rule(
    *,
    rule_id: int,
    name: Optional[str] = None,
    domain: Optional[str] = None,
    data_category: Optional[str] = None,
    description: Optional[str] = None,
    pattern: Optional[str] = None,
    active: Optional[bool] = None,
) -> RegexRuleSQL:
    with get_session() as session:
        rule = session.get(RegexRuleSQL, rule_id)
        if rule is None:
            raise ValueError(f"RegexRuleSQL not found: id={rule_id}")

        if name is not None:
            rule.name = name
        if domain is not None:
            rule.domain = domain
        if data_category is not None:
            rule.data_category = data_category
        if description is not None:
            rule.description = description
        if pattern is not None:
            rule.pattern = pattern
        if active is not None:
            rule.active = active

        session.add(rule)
        session.commit()
        session.refresh(rule)
        return rule


def delete_rule(rule_id: int) -> None:
    with get_session() as session:
        rule = session.get(RegexRuleSQL, rule_id)
        if rule is None:
            return
        session.delete(rule)
        session.commit()


def _get_embedding_text(
    *,
    name: str,
    description: str,
) -> str:
    return f"{name}. {description}"


def _normalize_pattern(p: str) -> str:
    return p.strip().replace("\r\n", "\n")


def _pattern_hash(p: str) -> str:
    return hashlib.sha256(_normalize_pattern(p).encode("utf-8")).hexdigest()


if __name__ == "__main__":
    from app.logging_config import setup_logging

    setup_logging()

    create_rule(
        name="Test Rule",
        domain="finance",
        data_category="credit_card",
        description="Detect credit card numbers in text",
        pattern=r"\b(?:\d[ -]*?){13,16}\b",
    )
    rules = list_rules()
    for r in rules:
        print(
            {
                "id": r.id,
                "name": r.name,
                "domain": r.domain,
                "data_category": r.data_category,
                "active": r.active,
            }
        )
