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
        self._pending_references = []  # Store references to resolve later
        
        try:
            # Pass 1: Scan files and symbols
            for root, dirs, files in os.walk(self.root):
                # Filter directories in place
                dirs[:] = [d for d in dirs if not self.should_ignore(Path(root) / d)]
                
                for file in files:
                    file_path = Path(root) / file
                    if self.should_ignore(file_path):
                        continue
                        
                    self._process_file(session, file_path, force)
            
            session.commit()
            
            # Pass 2: Resolve references
            self._resolve_references(session)
            session.commit()
            
        finally:
            session.close()

    def _process_file(self, session: Session, path: Path, force: bool):
        # Normalize to POSIX style (forward slashes) for consistency across OS
        rel_path = str(path.relative_to(self.root)).replace(os.sep, "/")
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
            
            # Clear old symbols and references
            # Note: Cascading delete should handle references if configured, 
            # but let's be safe.
            # Actually, we need to delete references where this file is the SOURCE
            # We can find them via symbols
            symbols = session.exec(select(Symbol).where(Symbol.file_id == db_file.id)).all()
            for s in symbols:
                # Delete references FROM this symbol
                refs = session.exec(select(Reference).where(Reference.source_symbol_id == s.id)).all()
                for r in refs:
                    session.delete(r)
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
                
                # Map symbol names to IDs for this file
                local_symbol_map = {}
                
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
                    session.flush() # Get ID
                    local_symbol_map[sym.name] = db_sym.id
                
                # Store references for later resolution
                for ref in result.references:
                    source_id = None
                    if ref.source_symbol:
                        # Try to find source in this file
                        # It should be in local_symbol_map if it was defined here
                        # If it's a nested class/function, the name matches
                        source_id = local_symbol_map.get(ref.source_symbol)
                    
                    self._pending_references.append({
                        'source_symbol_id': source_id,
                        'target_symbol_name': ref.target_symbol,
                        'reference_type': ref.reference_type,
                        'line_number': ref.line_number,
                        'file_id': db_file.id
                    })
                
            except Exception as e:
                print(f"Error analyzing {rel_path}: {e}")

    def _resolve_references(self, session: Session):
        """Resolve pending references to actual symbol IDs."""
        if not self._pending_references:
            return
            
        # Build a global symbol map for fast lookup: name -> [id, ...]
        # We might have multiple symbols with same name (e.g. __init__), 
        # so we need to be smart or just pick one for now.
        # Ideally we use imports to resolve, but for MVP we'll match by name.
        
        all_symbols = session.exec(select(Symbol.id, Symbol.name)).all()
        symbol_map = {}
        for sym_id, name in all_symbols:
            if name not in symbol_map:
                symbol_map[name] = []
            symbol_map[name].append(sym_id)
            
        # Process references
        for ref in self._pending_references:
            target_name = ref['target_symbol_name']
            target_ids = symbol_map.get(target_name)
            
            if target_ids:
                # If multiple matches, heuristic: prefer same file, then just pick first
                # For now, just pick first
                target_id = target_ids[0]
                
                db_ref = Reference(
                    source_symbol_id=ref['source_symbol_id'],
                    target_symbol_id=target_id,
                    reference_type=ref['reference_type'],
                    line_number=ref['line_number']
                )
                session.add(db_ref)

def scan_codebase(root: Path, force: bool = False):
    indexer = Indexer(root)
    indexer.scan(force)
