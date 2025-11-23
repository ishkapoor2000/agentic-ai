from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class ExtractedSymbol:
    name: str
    kind: str  # function, class, method, etc.
    line_start: int
    line_end: int
    docstring: str | None = None


@dataclass
class ExtractedReference:
    source_symbol: str | None  # Name of the symbol making the reference (if any)
    target_symbol: str  # Name of the symbol being referenced
    reference_type: str  # CALLS, IMPORTS, etc.
    line_number: int


@dataclass
class AnalysisResult:
    symbols: list[ExtractedSymbol] = field(default_factory=list)
    references: list[ExtractedReference] = field(default_factory=list)


class BaseAnalyzer(ABC):
    @abstractmethod
    def analyze(self, content: str, file_path: str) -> AnalysisResult:
        """
        Analyze the given file content and return symbols and references.
        """
        pass
