from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship

class File(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    path: str = Field(index=True, unique=True)
    rel_path: str
    extension: str
    language: str
    size: int
    mtime: float
    content_hash: str
    last_scanned_at: Optional[datetime] = None
    
    # Relationships
    symbols: List["Symbol"] = Relationship(back_populates="file")

class Directory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    path: str = Field(index=True, unique=True)
    rel_path: str
    summary: Optional[str] = None

class Symbol(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    kind: str  # function, class, method, variable, etc.
    file_id: int = Field(foreign_key="file.id")
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    
    file: File = Relationship(back_populates="symbols")

class Reference(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    source_symbol_id: Optional[int] = Field(default=None, foreign_key="symbol.id")
    target_symbol_id: Optional[int] = Field(default=None, foreign_key="symbol.id")
    reference_type: str # CALLS, IMPORTS, INHERITS, etc.
    line_number: int

class LLMCache(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    prompt_hash: str = Field(index=True, unique=True)
    model: str
    response: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
