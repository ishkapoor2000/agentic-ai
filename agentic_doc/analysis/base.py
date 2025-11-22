from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List, Optional

@dataclass
class ExtractedSymbol:
    name: str
    kind: str  # function, class, method, etc.
    line_start: int
    line_end: int
    docstring: Optional[str] = None

@dataclass
class ExtractedReference:
    source_symbol: Optional[str]  # Name of the symbol making the reference (if any)
    target_symbol: str  # Name of the symbol being referenced
    reference_type: str # CALLS, IMPORTS, etc.
    line_number: int

@dataclass
class AnalysisResult:
    symbols: List[ExtractedSymbol] = field(default_factory=list)
    references: List[ExtractedReference] = field(default_factory=list)

class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze(self, content: str, file_path: str) -> AnalysisResult:
        """
        Analyze the given file content and return symbols and references.
        """
        pass
