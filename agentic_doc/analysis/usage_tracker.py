"""
Usage Tracker for analyzing how functions and classes are used across the codebase.
Provides usage patterns, statistics, and context extraction.
"""

from collections import Counter
from pathlib import Path

from sqlmodel import Session, select

from agentic_doc.config import load_config
from agentic_doc.db.schema import File, Reference, Symbol


class UsageTracker:
    """Track and analyze symbol usage patterns."""

    def __init__(self, session: Session):
        self.session = session
        self.config = load_config()
        self.root = Path(self.config.root_path)

    def get_usage_locations(self, symbol_id: int) -> list[dict]:
        """
        Get all locations where a symbol is used.

        Args:
            symbol_id: ID of the symbol to track

        Returns:
            List of usage location dicts with file, line, and context
        """
        # Get all references to this symbol
        references = self.session.exec(
            select(Reference).where(Reference.target_symbol_id == symbol_id)
        ).all()

        usages = []
        for ref in references:
            if ref.source_symbol_id:
                source_symbol = self.session.get(Symbol, ref.source_symbol_id)
                if source_symbol:
                    source_file = self.session.get(File, source_symbol.file_id)

                    # Extract code context if possible
                    context = (
                        self._extract_context(source_file.rel_path, ref.line_number)
                        if source_file
                        else ""
                    )

                    usages.append(
                        {
                            "file": source_file.rel_path if source_file else "unknown",
                            "line": ref.line_number,
                            "used_by": source_symbol.name,
                            "used_by_kind": source_symbol.kind,
                            "reference_type": ref.reference_type,
                            "context": context,
                        }
                    )

        return usages

    def _extract_context(
        self, file_path: str, line_number: int, context_lines: int = 3
    ) -> str:
        """
        Extract code context around a line number.

        Args:
            file_path: Relative path to the file
            line_number: Line number to extract context from
            context_lines: Number of lines before and after to include

        Returns:
            String containing the code context
        """
        try:
            full_path = self.root / file_path
            if not full_path.exists():
                return ""

            lines = full_path.read_text(errors="ignore").splitlines()
            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)

            context_snippet = "\n".join(lines[start:end])
            return context_snippet.strip()
        except Exception:
            return ""

    def get_usage_statistics(self, symbol_id: int) -> dict:
        """
        Get usage statistics for a symbol.

        Args:
            symbol_id: ID of the symbol

        Returns:
            Dict containing usage statistics
        """
        usages = self.get_usage_locations(symbol_id)

        # Count by file
        files_counter = Counter(u["file"] for u in usages)

        # Count by reference type
        ref_type_counter = Counter(u["reference_type"] for u in usages)

        # Count by caller kind
        caller_kind_counter = Counter(u["used_by_kind"] for u in usages)

        return {
            "total_usages": len(usages),
            "files_used_in": len(files_counter),
            "usage_by_file": dict(files_counter.most_common(10)),
            "usage_by_type": dict(ref_type_counter),
            "usage_by_caller_kind": dict(caller_kind_counter),
            "most_common_callers": self._get_common_callers(usages),
        }

    def _get_common_callers(self, usages: list[dict], limit: int = 5) -> list[str]:
        """Get the most common callers of a symbol."""
        callers = [u["used_by"] for u in usages]
        counter = Counter(callers)
        return [caller for caller, _ in counter.most_common(limit)]

    def get_usage_patterns(self, symbol_id: int) -> list[str]:
        """
        Detect common usage patterns for a symbol.

        Args:
            symbol_id: ID of the symbol

        Returns:
            List of detected usage patterns
        """
        usages = self.get_usage_locations(symbol_id)
        patterns = []

        # Pattern: Mostly used in one file (file-local utility)
        if usages:
            file_counter = Counter(u["file"] for u in usages)
            most_common_file, count = file_counter.most_common(1)[0]
            if count / len(usages) > 0.7:
                patterns.append(
                    f"File-local utility (70%+ usage in {most_common_file})"
                )

        # Pattern: Called from many different files (shared utility)
        unique_files = len({u["file"] for u in usages})
        if unique_files > 5:
            patterns.append(f"Shared utility (used in {unique_files} files)")

        # Pattern: Mostly called by one function (helper function)
        caller_counter = Counter(u["used_by"] for u in usages)
        if caller_counter:
            most_common_caller, count = caller_counter.most_common(1)[0]
            if count / len(usages) > 0.6:
                patterns.append(
                    f"Helper function (60%+ calls from {most_common_caller})"
                )

        # Pattern: Import-only (module/class)
        import_ratio = sum(1 for u in usages if u["reference_type"] == "IMPORTS") / max(
            len(usages), 1
        )
        if import_ratio > 0.8:
            patterns.append("Primarily imported (module/library component)")


        return patterns

    def get_usage_examples(self, symbol_id: int, limit: int = 5) -> list[dict]:
        """
        Get actual usage examples from the codebase.

        Args:
            symbol_id: ID of the symbol
            limit: Maximum number of examples to return

        Returns:
            List of example dicts with file, context, and description
        """
        usages = self.get_usage_locations(symbol_id)

        # Try to get diverse examples from different files
        examples = []
        seen_files = set()

        for usage in usages:
            if (usage["file"] not in seen_files or len(examples) < limit) and usage["context"]:
                    examples.append(
                        {
                            "file": usage["file"],
                            "line": usage["line"],
                            "context": usage["context"],
                            "description": f"Used in {usage['used_by']} ({usage['used_by_kind']})",
                        }
                    )
                    seen_files.add(usage["file"])

            if len(examples) >= limit:
                break

        return examples

    def find_unused_symbols(self, file_id: int | None = None) -> list[dict]:
        """
        Find symbols that are defined but never used.

        Args:
            file_id: Optional file ID to scope the search

        Returns:
            List of unused symbol information
        """
        # Get symbols
        if file_id:
            symbols = self.session.exec(
                select(Symbol).where(Symbol.file_id == file_id)
            ).all()
        else:
            symbols = self.session.exec(select(Symbol)).all()

        unused = []
        for symbol in symbols:
            # Check if this symbol is referenced anywhere
            ref_count = self.session.exec(
                select(Reference).where(Reference.target_symbol_id == symbol.id)
            ).all()

            if len(ref_count) == 0:
                file = self.session.get(File, symbol.file_id)
                unused.append(
                    {
                        "id": symbol.id,
                        "name": symbol.name,
                        "kind": symbol.kind,
                        "file": file.rel_path if file else "unknown",
                    }
                )

        return unused

    def get_hot_functions(self, limit: int = 10) -> list[dict]:
        """
        Get the most frequently used functions in the codebase.

        Args:
            limit: Maximum number of hot functions to return

        Returns:
            List of hot function info sorted by usage count
        """
        # Count references for each symbol
        from sqlalchemy import func as sa_func

        hot_symbols = self.session.exec(
            select(
                Symbol.id,
                Symbol.name,
                Symbol.kind,
                Symbol.file_id,
                sa_func.count(Reference.id).label("usage_count"),
            )
            .outerjoin(Reference, Reference.target_symbol_id == Symbol.id)
            .where(Symbol.kind.in_(["function", "method", "class"]))
            .group_by(Symbol.id)
            .order_by(sa_func.count(Reference.id).desc())
            .limit(limit)
        ).all()

        results = []
        for symbol_id, name, kind, file_id, usage_count in hot_symbols:
            file = self.session.get(File, file_id)
            results.append(
                {
                    "id": symbol_id,
                    "name": name,
                    "kind": kind,
                    "file": file.rel_path if file else "unknown",
                    "usage_count": usage_count,
                }
            )

        return results
