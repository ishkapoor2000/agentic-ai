import ast
from typing import List, Optional
from .base import BaseAnalyzer, AnalysisResult, ExtractedSymbol, ExtractedReference

class PythonAnalyzer(BaseAnalyzer):
    def analyze(self, content: str, file_path: str) -> AnalysisResult:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return AnalysisResult()

        visitor = SymbolVisitor()
        visitor.visit(tree)
        return AnalysisResult(symbols=visitor.symbols, references=visitor.references)

class SymbolVisitor(ast.NodeVisitor):
    def __init__(self):
        self.symbols: List[ExtractedSymbol] = []
        self.references: List[ExtractedReference] = []
        self.current_scope: List[str] = [] # Stack of class/function names

    def _get_docstring(self, node) -> Optional[str]:
        return ast.get_docstring(node)

    def visit_ClassDef(self, node):
        name = node.name
        full_name = ".".join(self.current_scope + [name])
        
        self.symbols.append(ExtractedSymbol(
            name=full_name,
            kind="class",
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=self._get_docstring(node)
        ))
        
        self.current_scope.append(name)
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_FunctionDef(self, node):
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node):
        self._visit_function(node)

    def _visit_function(self, node):
        name = node.name
        full_name = ".".join(self.current_scope + [name])
        kind = "method" if self.current_scope else "function"
        
        self.symbols.append(ExtractedSymbol(
            name=full_name,
            kind=kind,
            line_start=node.lineno,
            line_end=node.end_lineno or node.lineno,
            docstring=self._get_docstring(node)
        ))
        
        self.current_scope.append(name)
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_Import(self, node):
        for alias in node.names:
            self.references.append(ExtractedReference(
                source_symbol=self.current_scope[-1] if self.current_scope else None,
                target_symbol=alias.name,
                reference_type="IMPORT",
                line_number=node.lineno
            ))

    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            target = f"{module}.{alias.name}" if module else alias.name
            self.references.append(ExtractedReference(
                source_symbol=self.current_scope[-1] if self.current_scope else None,
                target_symbol=target,
                reference_type="IMPORT",
                line_number=node.lineno
            ))

    def visit_Call(self, node):
        # Very basic call extraction
        func_name = self._get_func_name(node.func)
        if func_name:
             self.references.append(ExtractedReference(
                source_symbol=self.current_scope[-1] if self.current_scope else None,
                target_symbol=func_name,
                reference_type="CALL",
                line_number=node.lineno
            ))
        self.generic_visit(node)

    def _get_func_name(self, node) -> Optional[str]:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return f"{self._get_func_name(node.value)}.{node.attr}" if self._get_func_name(node.value) else node.attr
        return None
