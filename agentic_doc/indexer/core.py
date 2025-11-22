import os
import hashlib
from pathlib import Path
from typing import List, Set
from pathspec import PathSpec
from pathspec.patterns import GitWildMatchPattern
from sqlmodel import Session, select

from agentic_doc.db.session import get_session
from agentic_doc.db.schema import File, Symbol, Reference
from agentic_doc.analysis.python import PythonAnalyzer
from agentic_doc.analysis.javascript import JavaScriptAnalyzer
from agentic_doc.config import load_config

class Indexer:
    def __init__(self, root: Path):
        self.root = root.resolve()
        self.config = load_config()
        self.ignore_spec = self._load_ignore_spec()
        
        self.analyzers = {
            ".py": PythonAnalyzer(),
            ".js": JavaScriptAnalyzer(),
            ".jsx": JavaScriptAnalyzer(),
            ".ts": JavaScriptAnalyzer(),
            ".tsx": JavaScriptAnalyzer(),
        }

    def _load_ignore_spec(self) -> PathSpec:
        patterns = []
        
        # Default ignores
        patterns.extend(self.config.exclude_globs)
        
        # .gitignore
        gitignore = self.root / ".gitignore"
        if gitignore.exists():
            with open(gitignore, "r") as f:
                patterns.extend(f.read().splitlines())
                
        # .agentic-doc-ignore
        docignore = self.root / ".agentic-doc-ignore"
        if docignore.exists():
            with open(docignore, "r") as f:
                patterns.extend(f.read().splitlines())
                
        return PathSpec.from_lines(GitWildMatchPattern, patterns)

    def should_ignore(self, path: Path) -> bool:
        try:
            rel_path = path.relative_to(self.root)
            return self.ignore_spec.match_file(str(rel_path))
        except ValueError:
            return True

    def get_file_hash(self, path: Path) -> str:
        hasher = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        return hasher.hexdigest()

    def scan(self, force: bool = False):
        session_gen = get_session()
        session = next(session_gen)
        
        try:
            for root, dirs, files in os.walk(self.root):
                # Filter directories in place
                dirs[:] = [d for d in dirs if not self.should_ignore(Path(root) / d)]
                
                for file in files:
                    file_path = Path(root) / file
                    if self.should_ignore(file_path):
                        continue
                        
                    self._process_file(session, file_path, force)
            
            session.commit()
        finally:
            session.close()

    def _process_file(self, session: Session, path: Path, force: bool):
        rel_path = str(path.relative_to(self.root))
        current_hash = self.get_file_hash(path)
        stat = path.stat()
        
        # Check if file exists in DB
        db_file = session.exec(select(File).where(File.path == str(path))).first()
        
        if db_file:
            if not force and db_file.content_hash == current_hash:
                return # Skip if unchanged
            
            # Update existing
            db_file.content_hash = current_hash
            db_file.mtime = stat.st_mtime
            db_file.size = stat.st_size
            
            # Clear old symbols
            symbols = session.exec(select(Symbol).where(Symbol.file_id == db_file.id)).all()
            for s in symbols:
                session.delete(s)
            
            session.delete(db_file)
            session.commit()
            db_file = None

        if not db_file:
            db_file = File(
                path=str(path),
                rel_path=rel_path,
                extension=path.suffix,
                language=path.suffix.lstrip("."),
                size=stat.st_size,
                mtime=stat.st_mtime,
                content_hash=current_hash
            )
            session.add(db_file)
            session.commit()
            session.refresh(db_file)

        # Analyze content
        analyzer = self.analyzers.get(path.suffix)
        if analyzer:
            try:
                content = path.read_text(errors="ignore")
                result = analyzer.analyze(content, str(path))
                
                for sym in result.symbols:
                    db_sym = Symbol(
                        name=sym.name,
                        kind=sym.kind,
                        file_id=db_file.id,
                        line_start=sym.line_start,
                        line_end=sym.line_end,
                        docstring=sym.docstring
                    )
                    session.add(db_sym)
                
                # TODO: Store references. 
                # References need source_symbol_id which we might not have yet if we don't link them up.
                # For MVP, we can store them if we resolve the source symbol, or just store raw strings in a different table?
                # The schema has source_symbol_id as int.
                # We can skip references for this exact step or do a second pass.
                # Let's just store them if source is None (top level) or if we can map it.
                
            except Exception as e:
                print(f"Error analyzing {rel_path}: {e}")

def scan_codebase(root: Path, force: bool = False):
    indexer = Indexer(root)
    indexer.scan(force)
