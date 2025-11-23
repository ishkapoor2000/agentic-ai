import os
from pathlib import Path

from rich.console import Console
from rich.progress import track
from sqlmodel import select

from agentic_doc.analysis.dependency_analyzer import DependencyAnalyzer
from agentic_doc.analysis.usage_tracker import UsageTracker
from agentic_doc.config import load_config
from agentic_doc.core.prompts import (
    FILE_DOC_SYSTEM_PROMPT,
    FILE_DOC_USER_PROMPT,
    FUNCTION_USAGE_DOC_PROMPT,
    USE_CASE_DOC_SYSTEM_PROMPT,
    USE_CASE_DOC_USER_PROMPT,
)
from agentic_doc.db.schema import File, Symbol
from agentic_doc.db.session import get_session
from agentic_doc.llm.core import LLMClient

console = Console()


class DocBuilder:
    def __init__(self):
        self.config = load_config()
        self.root = Path(self.config.root_path)
        self.docs_dir = self.root / "docs"
        session = next(get_session())
        self.llm = LLMClient(self.config, session)

    def generate_file_docs(self, limit: int = 10, enhanced: bool = False):
        session = next(get_session())
        files = session.exec(select(File).limit(limit)).all()

        self.docs_dir.mkdir(exist_ok=True)
        (self.docs_dir / "files").mkdir(exist_ok=True, parents=True)

        for file in track(files, description="Generating file docs..."):
            try:
                self._process_file(session, file, enhanced=enhanced)
            except Exception as e:
                console.print(f"[red]Failed to doc {file.rel_path}: {e}[/red]")

    def _process_file(self, session, file: File, enhanced: bool = False):
        # Read content
        file_path = self.root / file.rel_path
        if not file_path.exists():
            return

        content = file_path.read_text(errors="ignore")

        # Get symbols
        symbols = session.exec(select(Symbol).where(Symbol.file_id == file.id)).all()
        symbol_str = "\n".join([f"- {s.kind}: {s.name}" for s in symbols])

        dependencies_str = ""
        usage_stats_str = ""

        if enhanced:
            # Initialize analyzers
            dep_analyzer = DependencyAnalyzer(session)
            usage_tracker = UsageTracker(session)

            # Get dependency info for this file
            file_deps = dep_analyzer.get_file_dependencies(file.id)
            dependencies_str = f"""Imports: {", ".join(file_deps["imports"][:5]) if file_deps["imports"] else "None"}
Imported by: {", ".join(file_deps["imported_by"][:5]) if file_deps["imported_by"] else "None"}"""

            # Get usage stats for key symbols
            for symbol in symbols[:3]:  # Top 3 symbols
                stats = usage_tracker.get_usage_statistics(symbol.id)
                if stats["total_usages"] > 0:
                    usage_stats_str += f"\n- {symbol.name}: used {stats['total_usages']} times in {stats['files_used_in']} files"

            if not usage_stats_str:
                usage_stats_str = "No significant usage tracked yet."

        # Generate
        if enhanced:
            prompt = FILE_DOC_USER_PROMPT.format(
                file_path=file.rel_path,
                language=file.language,
                content=content[:10000],  # Truncate for safety
                symbols=symbol_str,
                dependencies=dependencies_str,
                usage_stats=usage_stats_str,
            )
        else:
            # Use a simpler prompt for standard docs to save tokens
            prompt = f"""
File Path: {file.rel_path}
Language: {file.language}

Source Code:
```
{content[:10000]}
```

Symbols:
{symbol_str}

Please generate standard documentation for this file.
"""

        doc_content = self.llm.generate(prompt, FILE_DOC_SYSTEM_PROMPT)

        # Save
        doc_path = self.docs_dir / "files" / f"{file.rel_path}.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(doc_content)

    def generate_dir_docs(self):
        """Generate directory-level documentation by aggregating file docs."""
        console.print("[bold blue]Generating directory docs...[/bold blue]")

        docs_files_dir = self.docs_dir / "files"
        docs_dirs_dir = self.docs_dir / "dirs"
        docs_dirs_dir.mkdir(exist_ok=True, parents=True)

        # Walk through the docs/files structure
        directories = set()
        for root, _dirs, files in os.walk(docs_files_dir):
            if files:  # Only process dirs with files
                rel_path = Path(root).relative_to(docs_files_dir)
                if str(rel_path) != ".":
                    directories.add(rel_path)

        for dir_path in track(
            sorted(directories), description="Generating dir docs..."
        ):
            self._process_directory(docs_files_dir / dir_path, dir_path)

        console.print("[green]Directory docs complete.[/green]")

    def _process_directory(self, dir_path: Path, rel_path: Path):
        """Process a single directory with enhanced function/class indexing."""
        session = next(get_session())

        # Collect all file docs and their symbols
        file_summaries = []
        all_symbols = []

        for file in dir_path.glob("*.md"):
            # Get file documentation
            content = file.read_text()
            file_name = file.stem
            file_summaries.append(
                f"### [{file_name}](../files/{rel_path}/{file_name}.md)\n{content[:300]}..."
            )

            # Get symbols from this file
            db_file = session.exec(
                select(File).where(File.rel_path == str(Path(rel_path) / file_name))
            ).first()

            if db_file:
                symbols = session.exec(
                    select(Symbol).where(Symbol.file_id == db_file.id)
                ).all()

                for sym in symbols:
                    all_symbols.append(
                        {
                            "name": sym.name,
                            "kind": sym.kind,
                            "file": file_name,
                            "signature": "",
                        }
                    )

        if not file_summaries:
            session.close()
            return

        # Build symbol index
        symbol_index = "## Function & Class Index\n\n"

        # Group by type
        classes = [s for s in all_symbols if s["kind"] == "class"]
        functions = [s for s in all_symbols if s["kind"] in ["function", "method"]]

        if classes:
            symbol_index += "### Classes\n"
            for cls in classes:
                symbol_index += f"- **{cls['name']}** - [`{cls['file']}`](../files/{rel_path}/{cls['file']}.md)\n"
            symbol_index += "\n"

        if functions:
            symbol_index += "### Functions\n"
            for func in functions[:20]:  # Limit to first 20
                sig = (
                    func["signature"][:60] + "..."
                    if len(func["signature"]) > 60
                    else func["signature"]
                )
                symbol_index += f"- **{func['name']}**{sig} - [`{func['file']}`](../files/{rel_path}/{func['file']}.md)\n"
            if len(functions) > 20:
                symbol_index += f"\n*...and {len(functions) - 20} more functions*\n"
            symbol_index += "\n"

        # Generate directory summary
        prompt = f"""
Directory: {rel_path}

## Symbol Index
{symbol_index}

## File Summaries
{chr(10).join(file_summaries)}

Please write a comprehensive README.md for this directory/module with the following structure:

1. **Module Overview**: Brief description of what this module does
2. **Core Components**: Highlight the main classes and functions (reference the index above)
3. **Component Interactions**: How do these components work together?
4. **Usage Guide**: Common usage patterns or entry points
5. **Dependencies**: What this module depends on

Make sure to reference specific classes and functions from the index above. Use markdown links where appropriate.
"""

        system_prompt = """You are a technical writer creating directory-level documentation.
Focus on the big picture: what this module does and how its components work together.
Reference specific functions and classes from the provided index."""

        doc_content = self.llm.generate(prompt, system_prompt)

        # Prepend symbol index to generated content
        final_content = f"# {rel_path}\n\n{symbol_index}\n---\n\n{doc_content}"

        # Save
        doc_path = self.docs_dir / "dirs" / f"{rel_path}.md"
        doc_path.parent.mkdir(parents=True, exist_ok=True)
        doc_path.write_text(final_content)

        session.close()

    def generate_arch_doc(self):
        """Generate architecture overview by analyzing the symbol graph."""
        console.print("[bold blue]Generating architecture overview...[/bold blue]")

        session = next(get_session())

        # Get top-level statistics
        from sqlmodel import func

        file_count = session.exec(select(func.count(File.id))).one()
        symbol_count = session.exec(select(func.count(Symbol.id))).one()

        # Get most symbol-rich files (likely core modules)
        from sqlalchemy import func as sa_func

        top_files = session.exec(
            select(File.rel_path, sa_func.count(Symbol.id).label("symbol_count"))
            .join(Symbol)
            .group_by(File.id)
            .order_by(sa_func.count(Symbol.id).desc())
            .limit(10)
        ).all()

        top_files_str = "\n".join([f"- {f[0]} ({f[1]} symbols)" for f in top_files])

        # Get symbol type distribution
        symbol_types = session.exec(
            select(Symbol.kind, sa_func.count(Symbol.id)).group_by(Symbol.kind)
        ).all()

        symbol_types_str = "\n".join([f"- {s[0]}: {s[1]}" for s in symbol_types])

        prompt = f"""
# Codebase Statistics

Total Files: {file_count}
Total Symbols: {symbol_count}

## Top Files by Symbol Count
{top_files_str}

## Symbol Distribution
{symbol_types_str}

Based on this analysis, please generate a comprehensive System Architecture Overview including:

1. **High-Level Architecture**: What type of system is this? (web app, library, CLI tool, etc.)
2. **Core Modules**: Identify the main modules and their responsibilities
3. **Key Components**: Highlight the most important classes/functions
4. **Architecture Patterns**: Any notable design patterns or architectural decisions
5. **Module Dependencies**: How do the major components interact?

Include a Mermaid diagram showing the high-level module structure.
"""

        system_prompt = """You are a software architect analyzing a codebase.
Create a clear, insightful architecture overview that helps developers understand the system structure."""

        doc_content = self.llm.generate(prompt, system_prompt)

        # Save
        arch_dir = self.docs_dir / "architecture"
        arch_dir.mkdir(exist_ok=True, parents=True)
        (arch_dir / "overview.md").write_text(doc_content)

        console.print("[green]Architecture overview complete.[/green]")
        session.close()

    def generate_use_case_docs(self, min_usage: int = 5, limit: int = 20):
        """Generate use case documentation for frequently used components."""
        console.print("[bold blue]Generating use case documentation...[/bold blue]")

        session = next(get_session())
        usage_tracker = UsageTracker(session)

        # Get hot functions/classes
        hot_symbols = usage_tracker.get_hot_functions(limit=limit)

        # Filter by minimum usage
        hot_symbols = [s for s in hot_symbols if s["usage_count"] >= min_usage]

        if not hot_symbols:
            console.print("[yellow]No symbols with sufficient usage found.[/yellow]")
            session.close()
            return

        use_cases_dir = self.docs_dir / "use-cases"
        use_cases_dir.mkdir(exist_ok=True, parents=True)

        for symbol_info in track(hot_symbols, description="Generating use cases..."):
            try:
                self._generate_use_case(session, symbol_info, usage_tracker)
            except Exception as e:
                console.print(
                    f"[red]Failed to generate use case for {symbol_info['name']}: {e}[/red]"
                )

        console.print("[green]Use case documentation complete.[/green]")
        session.close()

    def _generate_use_case(
        self, session, symbol_info: dict, usage_tracker: UsageTracker
    ):
        """Generate use case doc for a single symbol."""
        symbol_id = symbol_info["id"]

        # Get detailed usage info
        stats = usage_tracker.get_usage_statistics(symbol_id)
        patterns = usage_tracker.get_usage_patterns(symbol_id)
        examples = usage_tracker.get_usage_examples(symbol_id, limit=3)

        # Format usage examples
        examples_str = ""
        for i, ex in enumerate(examples, 1):
            examples_str += f"\n**Example {i}** ({ex['file']}:{ex['line']}):\n```\n{ex['context']}\n```\n{ex['description']}\n"

        # Get symbol for description
        symbol = session.get(Symbol, symbol_id)
        description = symbol.docstring or "No description available."

        # Generate use case doc
        prompt = USE_CASE_DOC_USER_PROMPT.format(
            component_name=symbol_info["name"],
            component_kind=symbol_info["kind"],
            file_path=symbol_info["file"],
            description=description,
            usage_count=stats["total_usages"],
            usage_patterns="\n- ".join(patterns)
            if patterns
            else "No patterns detected",
            usage_examples=examples_str if examples_str else "No examples available",
        )

        doc_content = self.llm.generate(prompt, USE_CASE_DOC_SYSTEM_PROMPT)

        # Save
        safe_name = symbol_info["name"].replace("/", "_").replace(".", "_")
        doc_path = self.docs_dir / "use-cases" / f"{safe_name}.md"
        doc_path.write_text(doc_content)

    def generate_function_usage_docs(self, symbol_name: str = None):
        """Generate usage documentation for specific function(s)."""
        console.print(
            "[bold blue]Generating function usage documentation...[/bold blue]"
        )

        session = next(get_session())
        usage_tracker = UsageTracker(session)
        dep_analyzer = DependencyAnalyzer(session)

        # Get symbols to document
        if symbol_name:
            symbols = session.exec(
                select(Symbol).where(Symbol.name == symbol_name)
            ).all()
        else:
            # Get top 10 most used functions
            hot_symbols = usage_tracker.get_hot_functions(limit=10)
            symbols = [session.get(Symbol, s["id"]) for s in hot_symbols]

        if not symbols:
            console.print("[yellow]No symbols found.[/yellow]")
            session.close()
            return

        usage_docs_dir = self.docs_dir / "function-usage"
        usage_docs_dir.mkdir(exist_ok=True, parents=True)

        for symbol in track(symbols, description="Generating usage docs..."):
            try:
                self._generate_function_usage(
                    session, symbol, usage_tracker, dep_analyzer
                )
            except Exception as e:
                console.print(
                    f"[red]Failed to generate usage doc for {symbol.name}: {e}[/red]"
                )

        console.print("[green]Function usage documentation complete.[/green]")
        session.close()

    def _generate_function_usage(
        self,
        session,
        symbol: Symbol,
        usage_tracker: UsageTracker,
        dep_analyzer: DependencyAnalyzer,
    ):
        """Generate usage documentation for a single function."""
        file = session.get(File, symbol.file_id)

        # Get usage info
        usages = usage_tracker.get_usage_locations(symbol.id)
        stats = usage_tracker.get_usage_statistics(symbol.id)
        patterns = usage_tracker.get_usage_patterns(symbol.id)

        # Format usage locations
        usage_locations_str = ""
        for usage in usages[:10]:  # Top 10
            usage_locations_str += f"- {usage['file']}:{usage['line']} in {usage['used_by']} ({usage['reference_type']})\n"

        # Get dependencies
        deps = dep_analyzer.get_symbol_dependencies(symbol.id)
        dependents = dep_analyzer.get_symbol_dependents(symbol.id)

        prompt = FUNCTION_USAGE_DOC_PROMPT.format(
            function_name=symbol.name,
            file_path=file.rel_path if file else "unknown",
            usage_count=len(usages),
            usage_locations=usage_locations_str or "Not used yet",
            common_callers=", ".join(stats["most_common_callers"])
            if stats["most_common_callers"]
            else "None",
            patterns="\n- ".join(patterns) if patterns else "No patterns detected",
        )

        doc_content = self.llm.generate(
            prompt, "You are documenting function usage patterns."
        )

        # Add dependency info
        full_content = f"# {symbol.name} - Usage Documentation\n\n{doc_content}\n\n"

        if deps:
            full_content += "\n## Dependencies\n"
            for dep in deps[:10]:
                full_content += f"- {dep['target_name']} ({dep['reference_type']}) in {dep['file_path']}\n"

        if dependents:
            full_content += "\n## Used By\n"
            for dependent in dependents[:10]:
                full_content += f"- {dependent['source_name']} ({dependent['reference_type']}) in {dependent['file_path']}\n"

        # Save
        safe_name = symbol.name.replace(".", "_").replace("/", "_")
        doc_path = self.docs_dir / "function-usage" / f"{safe_name}.md"
        doc_path.write_text(full_content)

    def generate_manifest(self) -> dict:
        """Generate a JSON manifest of the documentation structure."""
        manifest = {}
        docs_files_dir = self.docs_dir / "files"

        if not docs_files_dir.exists():
            return {}

        for root, _dirs, files in os.walk(docs_files_dir):
            rel_path = Path(root).relative_to(docs_files_dir)

            # Navigate to current level in manifest
            current_level = manifest
            if str(rel_path) != ".":
                for part in rel_path.parts:
                    if part not in current_level:
                        current_level[part] = {}
                    current_level = current_level[part]

            # Add files
            for file in files:
                if file.endswith(".md"):
                    name = file[:-3]  # Remove .md
                    # Store relative path to doc file
                    doc_rel_path = str(Path(root).relative_to(self.docs_dir) / file)
                    current_level[name] = doc_rel_path

        return manifest
