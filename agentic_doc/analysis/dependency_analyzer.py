"""
Dependency Analyzer for detecting and analyzing code dependencies.
Tracks function calls, imports, class inheritance, and dependency graphs.
"""
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict
from sqlmodel import select, Session
from agentic_doc.db.schema import File, Symbol, Reference


class DependencyAnalyzer:
    """Analyze dependencies between symbols and files."""
    
    def __init__(self, session: Session):
        self.session = session
        self._dependency_cache: Dict[int, Set[int]] = {}
        self._reverse_dependency_cache: Dict[int, Set[int]] = {}
    
    def get_symbol_dependencies(self, symbol_id: int) -> List[Dict]:
        """
        Get all symbols that a given symbol depends on.
        
        Args:
            symbol_id: ID of the symbol to analyze
            
        Returns:
            List of dependency information dicts with keys:
            - target_symbol_id
            - target_name
            - reference_type (CALLS, IMPORTS, INHERITS)
            - file_path
        """
        references = self.session.exec(
            select(Reference)
            .where(Reference.source_symbol_id == symbol_id)
        ).all()
        
        dependencies = []
        for ref in references:
            if ref.target_symbol_id:
                target_symbol = self.session.get(Symbol, ref.target_symbol_id)
                if target_symbol:
                    target_file = self.session.get(File, target_symbol.file_id)
                    dependencies.append({
                        'target_symbol_id': target_symbol.id,
                        'target_name': target_symbol.name,
                        'target_kind': target_symbol.kind,
                        'reference_type': ref.reference_type,
                        'file_path': target_file.rel_path if target_file else 'unknown',
                        'line_number': ref.line_number
                    })
        
        return dependencies
    
    def get_symbol_dependents(self, symbol_id: int) -> List[Dict]:
        """
        Get all symbols that depend on a given symbol (reverse dependencies).
        
        Args:
            symbol_id: ID of the symbol to analyze
            
        Returns:
            List of dependent information dicts
        """
        references = self.session.exec(
            select(Reference)
            .where(Reference.target_symbol_id == symbol_id)
        ).all()
        
        dependents = []
        for ref in references:
            if ref.source_symbol_id:
                source_symbol = self.session.get(Symbol, ref.source_symbol_id)
                if source_symbol:
                    source_file = self.session.get(File, source_symbol.file_id)
                    dependents.append({
                        'source_symbol_id': source_symbol.id,
                        'source_name': source_symbol.name,
                        'source_kind': source_symbol.kind,
                        'reference_type': ref.reference_type,
                        'file_path': source_file.rel_path if source_file else 'unknown',
                        'line_number': ref.line_number
                    })
        
        return dependents
    
    def calculate_importance_score(self, symbol_id: int) -> int:
        """
        Calculate an importance score for a symbol based on:
        - Number of dependents (how many things use it)
        - Number of dependencies (complexity)
        
        Args:
            symbol_id: ID of the symbol
            
        Returns:
            Importance score (higher = more important)
        """
        dependents = self.get_symbol_dependents(symbol_id)
        dependencies = self.get_symbol_dependencies(symbol_id)
        
        # Weight dependents more heavily than dependencies
        score = len(dependents) * 3 + len(dependencies)
        
        return score
    
    def get_file_dependencies(self, file_id: int) -> Dict[str, List[str]]:
        """
        Get all file-level dependencies (imports, etc.).
        
        Args:
            file_id: ID of the file
            
        Returns:
            Dict with 'imports' and 'imported_by' lists
        """
        # Get all symbols in this file
        symbols = self.session.exec(
            select(Symbol).where(Symbol.file_id == file_id)
        ).all()
        
        imported_files = set()
        imported_by_files = set()
        
        for symbol in symbols:
            # Find what this file imports
            deps = self.get_symbol_dependencies(symbol.id)
            for dep in deps:
                if dep['reference_type'] == 'IMPORTS':
                    imported_files.add(dep['file_path'])
            
            # Find what imports this file
            dependents = self.get_symbol_dependents(symbol.id)
            for dependent in dependents:
                if dependent['reference_type'] == 'IMPORTS':
                    imported_by_files.add(dependent['file_path'])
        
        return {
            'imports': sorted(list(imported_files)),
            'imported_by': sorted(list(imported_by_files))
        }
    
    def get_critical_dependencies(self, symbol_id: int, depth: int = 2) -> List[Dict]:
        """
        Get critical dependencies for a symbol up to a certain depth.
        Critical = dependencies that have high importance scores.
        
        Args:
            symbol_id: ID of the symbol
            depth: How many levels deep to search
            
        Returns:
            List of critical dependencies sorted by importance
        """
        visited = set()
        critical_deps = []
        
        def _traverse(sid: int, current_depth: int):
            if current_depth > depth or sid in visited:
                return
            
            visited.add(sid)
            deps = self.get_symbol_dependencies(sid)
            
            for dep in deps:
                target_id = dep['target_symbol_id']
                importance = self.calculate_importance_score(target_id)
                
                # Consider it critical if importance > 5
                if importance > 5:
                    critical_deps.append({
                        **dep,
                        'importance_score': importance,
                        'depth': current_depth
                    })
                
                if current_depth < depth:
                    _traverse(target_id, current_depth + 1)
        
        _traverse(symbol_id, 1)
        
        # Sort by importance score
        return sorted(critical_deps, key=lambda x: x['importance_score'], reverse=True)
    
    def get_dependency_graph(self, file_id: Optional[int] = None) -> Dict[str, List]:
        """
        Build a dependency graph for visualization.
        
        Args:
            file_id: Optional file ID to scope the graph. If None, returns full graph.
            
        Returns:
            Dict with 'nodes' and 'edges' for graph visualization
        """
        nodes = []
        edges = []
        
        # Determine which symbols to include
        if file_id:
            symbols = self.session.exec(
                select(Symbol).where(Symbol.file_id == file_id)
            ).all()
        else:
            symbols = self.session.exec(select(Symbol)).all()
        
        symbol_ids = {s.id for s in symbols}
        
        # Build nodes
        for symbol in symbols:
            importance = self.calculate_importance_score(symbol.id)
            file = self.session.get(File, symbol.file_id)
            
            nodes.append({
                'id': symbol.id,
                'name': symbol.name,
                'kind': symbol.kind,
                'file': file.rel_path if file else 'unknown',
                'importance': importance
            })
        
        # Build edges
        references = self.session.exec(
            select(Reference)
            .where(
                (Reference.source_symbol_id.in_(symbol_ids)) |
                (Reference.target_symbol_id.in_(symbol_ids))
            )
        ).all()
        
        for ref in references:
            if ref.source_symbol_id in symbol_ids and ref.target_symbol_id in symbol_ids:
                edges.append({
                    'source': ref.source_symbol_id,
                    'target': ref.target_symbol_id,
                    'type': ref.reference_type
                })
        
        return {
            'nodes': nodes,
            'edges': edges
        }
    
    def get_dependency_chain(self, from_symbol_id: int, to_symbol_id: int) -> Optional[List[int]]:
        """
        Find the dependency chain from one symbol to another using BFS.
        
        Args:
            from_symbol_id: Starting symbol ID
            to_symbol_id: Target symbol ID
            
        Returns:
            List of symbol IDs representing the path, or None if no path exists
        """
        from collections import deque
        
        queue = deque([(from_symbol_id, [from_symbol_id])])
        visited = {from_symbol_id}
        
        while queue:
            current_id, path = queue.popleft()
            
            if current_id == to_symbol_id:
                return path
            
            deps = self.get_symbol_dependencies(current_id)
            for dep in deps:
                target_id = dep['target_symbol_id']
                if target_id not in visited:
                    visited.add(target_id)
                    queue.append((target_id, path + [target_id]))
        
        return None
