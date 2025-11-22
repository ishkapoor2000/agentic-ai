import re
from .base import BaseAnalyzer, AnalysisResult, ExtractedSymbol, ExtractedReference

class JavaScriptAnalyzer(BaseAnalyzer):
    def analyze(self, content: str, file_path: str) -> AnalysisResult:
        symbols = []
        references = []
        
        # Regex patterns for common JS/TS constructs
        # Note: This is a heuristic fallback since we don't have tree-sitter yet.
        
        # function foo() {}
        func_pattern = re.compile(r"function\s+([a-zA-Z0-9_$]+)\s*\(")
        # class Foo {}
        class_pattern = re.compile(r"class\s+([a-zA-Z0-9_$]+)")
        # const foo = () => {} or const foo = function() {}
        const_func_pattern = re.compile(r"(?:const|let|var)\s+([a-zA-Z0-9_$]+)\s*=\s*(?:async\s*)?(?:\([^)]*\)|[a-zA-Z0-9_$]+)\s*=>")
        
        # Imports
        import_pattern = re.compile(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]")
        
        lines = content.splitlines()
        for i, line in enumerate(lines):
            lineno = i + 1
            
            # Functions
            for match in func_pattern.finditer(line):
                symbols.append(ExtractedSymbol(
                    name=match.group(1),
                    kind="function",
                    line_start=lineno,
                    line_end=lineno, # Approximation
                ))
                
            # Classes
            for match in class_pattern.finditer(line):
                symbols.append(ExtractedSymbol(
                    name=match.group(1),
                    kind="class",
                    line_start=lineno,
                    line_end=lineno,
                ))
                
            # Const functions
            for match in const_func_pattern.finditer(line):
                symbols.append(ExtractedSymbol(
                    name=match.group(1),
                    kind="function",
                    line_start=lineno,
                    line_end=lineno,
                ))
                
            # Imports
            for match in import_pattern.finditer(line):
                references.append(ExtractedReference(
                    source_symbol=None,
                    target_symbol=match.group(1),
                    reference_type="IMPORT",
                    line_number=lineno
                ))
                
        return AnalysisResult(symbols=symbols, references=references)
