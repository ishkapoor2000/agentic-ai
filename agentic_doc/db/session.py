import os
from pathlib import Path

from sqlmodel import Session, SQLModel, create_engine

from agentic_doc.config import load_config


def get_engine():
    config = load_config()
    db_path = Path(config.root_path) / "agentic_doc.db"
    database_url = f"sqlite:///{db_path}"

    # Check if database is new
    db_exists = db_path.exists()

    engine = create_engine(database_url, echo=False)

    # If database is new or empty, create tables
    if not db_exists or (db_path.exists() and os.path.getsize(db_path) == 0):
        # Import models first to register them
        SQLModel.metadata.create_all(engine)

    return engine


engine = get_engine()


def init_db():
    """Ensure all tables exist."""
    SQLModel.metadata.create_all(engine)


def get_session():
    # Ensure tables exist before yielding session
    try:
        with Session(engine) as session:
            yield session
    except Exception as e:
        # If there's a table error, try to init and retry
        if "no such table" in str(e):
            init_db()
            with Session(engine) as session:
                yield session
        else:
            raise
