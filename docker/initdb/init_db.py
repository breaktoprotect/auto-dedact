from sqlmodel import SQLModel, Session, text

from app.db.sqlmodels.regex_rule import RegexRuleSQL
from app.db.session import engine


def init_db() -> None:
    with Session(engine) as session:
        session.exec(text("CREATE EXTENSION IF NOT EXISTS vector"))  # type: ignore
        session.commit()

    SQLModel.metadata.create_all(engine)


if __name__ == "__main__":
    init_db()
    print("[+] db initialization...OK")
