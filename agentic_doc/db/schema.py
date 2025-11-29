from datetime import datetime

from sqlmodel import Field, Relationship, SQLModel


class File(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True, unique=True)
    rel_path: str
    extension: str
    language: str
    size: int
    mtime: float
    content_hash: str
    last_scanned_at: datetime | None = None

    # Relationships
    symbols: list["Symbol"] = Relationship(back_populates="file")


class Directory(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    path: str = Field(index=True, unique=True)
    rel_path: str
    summary: str | None = None


class Symbol(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    kind: str  # function, class, method, variable, etc.
    file_id: int = Field(foreign_key="file.id")
    line_start: int
    line_end: int
    docstring: str | None = None
    route_path: str | None = None  # API Route path (e.g. /users)
    route_method: str | None = None  # API Method (e.g. GET, POST)

    file: File = Relationship(back_populates="symbols")


class Reference(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    source_symbol_id: int | None = Field(default=None, foreign_key="symbol.id")
    target_symbol_id: int | None = Field(default=None, foreign_key="symbol.id")
    reference_type: str  # CALLS, IMPORTS, INHERITS, etc.
    line_number: int


class LLMCache(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    prompt_hash: str = Field(index=True, unique=True)
    model: str
    response: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class Route(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    path: str
    method: str
    symbol_id: int = Field(foreign_key="symbol.id")

