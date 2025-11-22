import typer
from rich.console import Console
from pathlib import Path
from agentic_doc.config import load_config, save_config, Config
from agentic_doc.db.session import init_db
from agentic_doc.llm.api_tracker import get_tracker

app = typer.Typer(help="Agentic AI Documentation Generator - Professional CLI for codebase documentation.")
console = Console()

@app.command()
def init(
    root: str = typer.Option(".", help="Root directory of the project to index."),
    provider: str = typer.Option("gemini", help="Model provider: openai, gemini (free), or mock"),
    openai_model: str = typer.Option("gpt-4o-mini", help="OpenAI model name."),
    gemini_model: str = typer.Option("gemini-2.5-flash", help="Gemini model name.")
):
    """
    Initialize the project with a default configuration.
    """
    config_path = Path(".agentic-doc.yml")
    if config_path.exists():
        console.print(f"[yellow]Configuration file {config_path} already exists.[/yellow]")
        return

    config = Config(root_path=root, model_provider=provider)
    save_config(config)
    console.print(f"[green]Created {config_path} with default settings.[/green]")
    
    # Initialize DB
    init_db()
    console.print("[green]Initialized SQLite database.[/green]")

@app.command()
def scan(force: bool = typer.Option(False, help="Force re-scan of all files.")):
    """
    Scan the codebase and update the file index.
    """
    console.print("[bold blue]Scanning codebase...[/bold blue]")
    from agentic_doc.indexer.core import scan_codebase
    
    config = load_config()
    root_path = Path(config.root_path)
    
    scan_codebase(root_path, force=force)
    console.print("[green]Scan complete.[/green]")

@app.command()
def doc(
    target: str = typer.Argument("files", help="Target: files, dirs, or architecture"),
    limit: int = typer.Option(10, help="Max files to document (for 'files' target)"),
    enhanced: bool = typer.Option(False, "--enhanced", "-e", help="Enable enhanced documentation with dependencies and usage stats (costs more tokens).")
):
    """
    Generate documentation at various levels.
    """
    from agentic_doc.core.doc_builder import DocBuilder
    
    # Reset tracker for this session
    tracker = get_tracker()
    tracker.reset()
    
    builder = DocBuilder()
    
    if target == "files":
        if enhanced:
            console.print(f"[bold blue]Generating ENHANCED docs for files (limit={limit})...[/bold blue]")
        else:
            console.print(f"[bold blue]Generating standard docs for files (limit={limit})...[/bold blue]")
            
        builder.generate_file_docs(limit=limit, enhanced=enhanced)
    elif target == "dirs":
        console.print(f"[bold blue]Generating directory-level documentation...[/bold blue]")
        builder.generate_dir_docs()
    elif target == "architecture":
        console.print(f"[bold blue]Generating architecture overview...[/bold blue]")
        builder.generate_arch_doc()
    else:
        console.print(f"[red]Unknown target: {target}[/red]")
        return
    
    # Display API usage statistics
    console.print(tracker.get_summary())

@app.command()
def use_cases(
    min_usage: int = typer.Option(5, help="Minimum usage count to include"),
    limit: int = typer.Option(20, help="Maximum number of components to document")
):
    """
    Generate use case documentation for frequently used components.
    
    This analyzes actual usage patterns in your codebase and generates
    documentation explaining when and how to use key components.
    """
    from agentic_doc.core.doc_builder import DocBuilder
    builder = DocBuilder()
    builder.generate_use_case_docs(min_usage=min_usage, limit=limit)

@app.command()
def function_usage(
    symbol_name: str = typer.Argument(None, help="Specific function/class name to document (optional)")
):
    """
    Generate usage documentation showing where and how functions are used.
    
    If no symbol name is provided, documents the top 10 most used functions.
    """
    from agentic_doc.core.doc_builder import DocBuilder
    builder = DocBuilder()
    builder.generate_function_usage_docs(symbol_name=symbol_name)

@app.command()
def analyze_deps(
    file_path: str = typer.Argument(None, help="Specific file to analyze (optional)"),
    show_hot: bool = typer.Option(True, help="Show hot functions report")
):
    """
    Analyze and display dependency information.
    """
    from agentic_doc.db.session import get_session
    from agentic_doc.graph.dependency_visualizer import DependencyVisualizer
    from agentic_doc.db.schema import File
    from sqlmodel import select
    
    session = next(get_session())
    visualizer = DependencyVisualizer(session)
    
    if show_hot:
        console.print("[bold blue]Generating hot functions report...[/bold blue]")
        report = visualizer.generate_hot_functions_report(limit=20)
        
        # Save to docs
        from agentic_doc.config import load_config
        from pathlib import Path
        config = load_config()
        docs_dir = Path(config.root_path) / "docs" / "analysis"
        docs_dir.mkdir(parents=True, exist_ok=True)
        
        report_path = docs_dir / "hot-functions.md"
        report_path.write_text(report)
        console.print(f"[green]Report saved to {report_path}[/green]")
    
    if file_path:
        file_obj = session.exec(
            select(File).where(File.rel_path == file_path)
        ).first()
        
        if file_obj:
            console.print(f"[bold blue]Analyzing dependencies for {file_path}...[/bold blue]")
            from agentic_doc.analysis.dependency_analyzer import DependencyAnalyzer
            analyzer = DependencyAnalyzer(session)
            
            deps = analyzer.get_file_dependencies(file_obj.id)
            console.print(f"\n[bold]Imports:[/bold] {', '.join(deps['imports'][:10])}")
            console.print(f"[bold]Imported by:[/bold] {', '.join(deps['imported_by'][:10])}")
        else:
            console.print(f"[red]File not found: {file_path}[/red]")
    
    session.close()

@app.command()
def visualize_deps(
    output: str = typer.Option("dependency-graph.html", help="Output file path"),
    format: str = typer.Option("html", help="Format: html, mermaid"),
    file_path: str = typer.Argument(None, help="Optional file to scope visualization")
):
    """
    Generate visual dependency graphs.
    
    Supports interactive HTML visualizations and Mermaid diagrams.
    """
    from agentic_doc.db.session import get_session
    from agentic_doc.graph.dependency_visualizer import DependencyVisualizer
    from agentic_doc.db.schema import File
    from agentic_doc.config import load_config
    from pathlib import Path
    from sqlmodel import select
    
    console.print(f"[bold blue]Generating dependency visualization...[/bold blue]")
    
    session = next(get_session())
    visualizer = DependencyVisualizer(session)
    config = load_config()
    
    file_id = None
    if file_path:
        file_obj = session.exec(
            select(File).where(File.rel_path == file_path)
        ).first()
        if file_obj:
            file_id = file_obj.id
        else:
            console.print(f"[red]File not found: {file_path}[/red]")
            session.close()
            return
    
    output_path = Path(config.root_path) / "docs" / output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format == "html":
        visualizer.export_interactive_html(output_path, file_id=file_id)
        console.print(f"[green]Interactive visualization saved to {output_path}[/green]")
        console.print(f"[blue]Open {output_path} in a browser to view[/blue]")
    elif format == "mermaid":
        mermaid = visualizer.generate_mermaid_dependency_graph(file_id=file_id)
        output_path = output_path.with_suffix('.md')
        output_path.write_text(f"```mermaid\n{mermaid}\n```")
        console.print(f"[green]Mermaid diagram saved to {output_path}[/green]")
    else:
        console.print(f"[red]Unknown format: {format}[/red]")
    
    session.close()

@app.command()
def graph(
    format: str = typer.Option("json", help="Export format: json, dot, mermaid, or html"),
    output: str = typer.Option(None, help="Output file path (default: stdout for text, graph.html for html)")
):
    """
    Export the symbol graph in various formats.
    
    Formats:
    - json: Machine-readable graph with nodes and edges
    - dot: Graphviz format for visualization
    - mermaid: Mermaid diagram for documentation
    - html: Interactive standalone web visualization
    """
    from agentic_doc.graph.exporter import GraphExporter
    
    console.print(f"[bold blue]Exporting graph as {format}...[/bold blue]")
    
    exporter = GraphExporter()
    
    try:
        if format == "json":
            result = exporter.export_json()
        elif format == "dot":
            result = exporter.export_dot()
        elif format == "mermaid":
            result = exporter.export_mermaid()
        elif format == "html":
            result = exporter.export_html()
            if not output:
                output = "graph.html"
        else:
            console.print(f"[red]Unknown format: {format}[/red]")
            console.print("Supported formats: json, dot, mermaid, html")
            return
        
        if output:
            # Write to file
            with open(output, 'w') as f:
                f.write(result)
            console.print(f"[green]Graph exported to {output}[/green]")
        else:
            # Print to stdout
            print(result)
    
    finally:
        exporter.close()

@app.command()
def mindmap(
    output: str = typer.Option("graph.html", help="Output file path"),
    format: str = typer.Option("html", help="Format: html (interactive) or mermaid")
):
    """
    Generate interactive mindmap visualization of the codebase.
    
    Creates a beautiful, interactive graph showing files, symbols, and their relationships.
    """
    console.print(f"[bold blue]🧠 Generating codebase mindmap...[/bold blue]")
    
    from agentic_doc.graph.exporter import GraphExporter
    from agentic_doc.config import load_config
    from pathlib import Path
    
    config = load_config()
    exporter = GraphExporter()
    
    try:
        output_path = Path(config.root_path) / "docs" / output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == "html":
            result = exporter.export_html()
            output_path.write_text(result)
            console.print(f"[green]✓ Interactive mindmap saved to {output_path}[/green]")
            console.print(f"[cyan]Open {output_path} in your browser to explore[/cyan]")
        elif format == "mermaid":
            result = exporter.export_mermaid()
            output_path = output_path.with_suffix('.md')
            output_path.write_text(f"```mermaid\n{result}\n```")
            console.print(f"[green]✓ Mermaid diagram saved to {output_path}[/green]")
        else:
            console.print(f"[red]Unknown format: {format}[/red]")
    finally:
        exporter.close()

@app.command()
def configure():
    """
    Interactive configuration wizard for API keys and model providers.
    
    Set up your OpenAI or Gemini API keys and choose your preferred model.
    """
    from agentic_doc.config_manager import ConfigManager
    
    manager = ConfigManager()
    manager.interactive_setup()

@app.command(name="switch-provider")
def switch_provider(
    provider: str = typer.Argument(..., help="Provider to switch to: openai, gemini, or mock")
):
    """
    Switch between model providers (OpenAI, Gemini, Mock).
    """
    from agentic_doc.config_manager import ConfigManager
    
    manager = ConfigManager()
    manager.switch_provider(provider)

@app.command()
def status():
    """
    Show current configuration and API key status.
    """
    from agentic_doc.config_manager import ConfigManager
    
    manager = ConfigManager()
    manager.show_config()

@app.command()
def serve(port: int = typer.Option(3000, help="Port to serve on")):
    """
    Launch the web-based documentation viewer.
    """
    console.print("[yellow]Web viewer not implemented yet.[/yellow]")
    console.print("Coming in Phase 4!")

if __name__ == "__main__":
    app()
