import ast

from .base import AnalysisResult, BaseAnalyzer, ExtractedReference, ExtractedSymbol


class PythonAnalyzer(BaseAnalyzer):
    def analyze(self, content: str, _file_path: str) -> AnalysisResult:
        try:
            tree = ast.parse(content)
        except SyntaxError:
            return AnalysisResult()

        visitor = SymbolVisitor()
        visitor.visit(tree)
        return AnalysisResult(
            symbols=visitor.symbols, 
            references=visitor.references,
            routes=visitor.routes
        )


class SymbolVisitor(ast.NodeVisitor):
    def __init__(self):
        self.symbols: list[ExtractedSymbol] = []
        self.references: list[ExtractedReference] = []
        self.routes: list[ExtractedRoute] = [] # New
        self.current_scope: list[str] = []  # Stack of class/function names

    def _get_docstring(self, node) -> str | None:
        return ast.get_docstring(node)

    def visit_ClassDef(self, node):
        name = node.name
        full_name = ".".join(self.current_scope + [name])

        self.symbols.append(
            ExtractedSymbol(
                name=full_name,
                kind="class",
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                docstring=self._get_docstring(node),
            )
        )

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

        # Check for API route decorators
        route_path = None
        route_method = None
        
        for decorator in node.decorator_list:
            # Check for @app.get("/path") or @router.post("/path")
            if isinstance(decorator, ast.Call):
                func = decorator.func
                if isinstance(func, ast.Attribute):
                    # Check method (get, post, put, delete, patch)
                    method = func.attr.upper()
                    if method in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                        route_method = method
                        # Extract path from args
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            route_path = decorator.args[0].value

        self.symbols.append(
            ExtractedSymbol(
                name=full_name,
                kind=kind,
                line_start=node.lineno,
                line_end=node.end_lineno or node.lineno,
                docstring=self._get_docstring(node),
                route_path=route_path,
                route_method=route_method,
            )
        )

        self.current_scope.append(name)
        self.generic_visit(node)
        self.current_scope.pop()

    def visit_Import(self, node):
        for alias in node.names:
            self.references.append(
                ExtractedReference(
                    source_symbol=self.current_scope[-1]
                    if self.current_scope
                    else None,
                    target_symbol=alias.name,
                    reference_type="IMPORT",
                    line_number=node.lineno,
                )
            )

    def visit_ImportFrom(self, node):
        module = node.module or ""
        for alias in node.names:
            target = f"{module}.{alias.name}" if module else alias.name
            self.references.append(
                ExtractedReference(
                    source_symbol=self.current_scope[-1]
                    if self.current_scope
                    else None,
                    target_symbol=target,
                    reference_type="IMPORT",
                    line_number=node.lineno,
                )
            )

    def visit_Call(self, node):
        # Very basic call extraction
        func_name = self._get_func_name(node.func)
        if func_name:
            # Check for app.add_url_rule
            if func_name.endswith(".add_url_rule"):
                self._extract_route(node)

            self.references.append(
                ExtractedReference(
                    source_symbol=self.current_scope[-1]
                    if self.current_scope
                    else None,
                    target_symbol=func_name,
                    reference_type="CALL",
                    line_number=node.lineno,
                )
            )
        self.generic_visit(node)

    def _extract_route(self, node):
        """Extract route info from app.add_url_rule(path, endpoint, view_func)."""
        try:
            # 1. Path (1st arg)
            path = None
            if node.args and isinstance(node.args[0], ast.Constant):
                path = node.args[0].value
            
            # 2. Method (methods=["GET"])
            method = "GET" # Default
            for keyword in node.keywords:
                if keyword.arg == "methods":
                    if isinstance(keyword.value, ast.List) and keyword.value.elts:
                        # Just take the first method for now
                        first_method = keyword.value.elts[0]
                        if isinstance(first_method, ast.Constant):
                            method = first_method.value
            
            # 3. View Func (view_func=func or 3rd arg)
            view_func = None
            # Check kwargs
            for keyword in node.keywords:
                if keyword.arg == "view_func":
                    if isinstance(keyword.value, ast.Name):
                        view_func = keyword.value.id
            
            # Check args (3rd arg is usually view_func if not kwarg)
            if not view_func and len(node.args) >= 3:
                if isinstance(node.args[2], ast.Name):
                    view_func = node.args[2].id
            
            if path and view_func:
                from .base import ExtractedRoute
                self.routes.append(
                    ExtractedRoute(
                        path=path,
                        method=method,
                        view_func=view_func,
                        line_number=node.lineno
                    )
                )

        except Exception:
            pass

    def _get_func_name(self, node) -> str | None:
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return (
                f"{self._get_func_name(node.value)}.{node.attr}"
                if self._get_func_name(node.value)
                else node.attr
            )
        return None
