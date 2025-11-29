"""
Graph export functionality for symbol graphs.
Supports JSON, DOT (Graphviz), and Mermaid formats.
"""

import json

from sqlalchemy import func as sa_func
from sqlmodel import select

from agentic_doc.db.schema import File, Symbol
from agentic_doc.db.session import get_session


class GraphExporter:
    """Export symbol graph in various formats."""

    def __init__(self):
        self.session = next(get_session())

    def export_json(self) -> str:
        """
        Export graph as JSON.

        Returns:
            JSON string with nodes and edges
        """
        files = self.session.exec(select(File)).all()
        symbols = self.session.exec(select(Symbol)).all()

        # Build nodes and edges
        nodes = []
        edges = []

        # File nodes
        for file in files:
            nodes.append(
                {
                    "id": f"file_{file.id}",
                    "type": "file",
                    "label": file.rel_path,
                    "language": file.language,
                    "size": file.size,
                    "layer": self._get_layer(file.rel_path),
                }
            )

        # Calculate criticality (usage count)
        from collections import Counter
        from agentic_doc.db.schema import Reference, Route
        
        ref_counts = self.session.exec(
            select(Reference.target_symbol_id, sa_func.count(Reference.id))
            .group_by(Reference.target_symbol_id)
        ).all()
        criticality_map = {sym_id: count for sym_id, count in ref_counts}

        # Fetch Routes
        routes = self.session.exec(select(Route)).all()
        route_map = {r.symbol_id: r for r in routes}

        # Symbol nodes
        for symbol in symbols:
            # Get route info from Symbol (decorators) OR Route table (add_url_rule)
            r_path = symbol.route_path
            r_method = symbol.route_method
            
            if not r_path and symbol.id in route_map:
                r_path = route_map[symbol.id].path
                r_method = route_map[symbol.id].method

            nodes.append(
                {
                    "id": f"symbol_{symbol.id}",
                    "type": "symbol",
                    "label": symbol.name,
                    "kind": symbol.kind,
                    "file_id": f"file_{symbol.file_id}",
                    "route_path": r_path,
                    "route_method": r_method,
                    "criticality": criticality_map.get(symbol.id, 0),
                    "docstring": symbol.docstring, # Include docstring for Magic Panel
                }
            )

            # Edge from symbol to file
            edges.append(
                {
                    "source": f"symbol_{symbol.id}",
                    "target": f"file_{symbol.file_id}",
                    "type": "belongs_to",
                }
            )

        graph = {
            "nodes": nodes,
            "edges": edges,
            "metadata": {"total_files": len(files), "total_symbols": len(symbols)},
        }

        return json.dumps(graph, indent=2)

    def export_dot(self) -> str:
        """
        Export graph as DOT (Graphviz) format.

        Returns:
            DOT format string
        """
        files = self.session.exec(select(File)).all()
        symbols = self.session.exec(select(Symbol)).all()

        # Build DOT graph
        dot_lines = ["digraph SymbolGraph {"]
        dot_lines.append("  rankdir=LR;")
        dot_lines.append("  node [shape=box];")
        dot_lines.append("")

        # File nodes
        dot_lines.append("  // Files")
        for file in files:
            label = file.rel_path.replace('"', '\\"')
            dot_lines.append(
                f'  file_{file.id} [label="{label}", style=filled, fillcolor=lightblue];'
            )

        dot_lines.append("")
        dot_lines.append("  // Symbols")

        # Symbol nodes by type
        for symbol in symbols:
            label = f"{symbol.kind}: {symbol.name}".replace('"', '\\"')
            color = self._get_symbol_color(symbol.kind)
            dot_lines.append(
                f'  symbol_{symbol.id} [label="{label}", style=filled, fillcolor={color}];'
            )

        dot_lines.append("")
        dot_lines.append("  // Relationships")

        # Edges
        for symbol in symbols:
            dot_lines.append(f"  symbol_{symbol.id} -> file_{symbol.file_id};")

        dot_lines.append("}")

        return "\n".join(dot_lines)

    def export_mermaid(self) -> str:
        """
        Export graph as Mermaid diagram.

        Returns:
            Mermaid format string
        """
        files = self.session.exec(select(File)).all()

        # Group files by directory
        dir_files: dict[str, list[File]] = {}
        for file in files:
            parts = file.rel_path.split("/")
            dir_name = "/".join(parts[:-1]) if len(parts) > 1 else "root"

            if dir_name not in dir_files:
                dir_files[dir_name] = []
            dir_files[dir_name].append(file)

        # Build Mermaid graph
        mermaid_lines = ["graph TD"]

        # Create subgraphs for directories
        for dir_name, dir_file_list in sorted(dir_files.items()):
            safe_dir_id = dir_name.replace("/", "_").replace(".", "_")
            mermaid_lines.append(f'  subgraph {safe_dir_id}["{dir_name}"]')

            for file in dir_file_list:
                file_name = file.rel_path.split("/")[-1]
                mermaid_lines.append(f'    file_{file.id}["{file_name}"]')

                # Get top symbols for this file
                symbols = self.session.exec(
                    select(Symbol).where(Symbol.file_id == file.id).limit(5)
                ).all()

                for symbol in symbols:
                    symbol_id = f"sym_{symbol.id}"
                    mermaid_lines.append(
                        f"    {symbol_id}[{symbol.kind}: {symbol.name}]"
                    )
                    mermaid_lines.append(f"    file_{file.id} --> {symbol_id}")

            mermaid_lines.append("  end")

        return "\n".join(mermaid_lines)

    def export_html(self) -> str:
        """
        Export graph as a standalone interactive HTML file.

        Embeds all JS/CSS assets and graph data into a single file.

        Returns:
            HTML content string
        """
        from pathlib import Path

        # Get assets directory
        assets_dir = Path(__file__).parent / "assets"

        if not assets_dir.exists():
            return "<!-- Error: Visualization assets not found. Please reinstall agentic_doc. -->"

        # Read template
        try:
            template = (assets_dir / "index.html").read_text(encoding="utf-8")
        except Exception as e:
            return f"<!-- Error reading template: {e} -->"

        # Generate graph data
        graph_json = self.export_json()
        graph_mermaid = self.export_mermaid()

        # Assets to embed
        css_files = ["styles.css", "mermaidViewer.css", "docPanel.css"]
        js_files = [
            "canvas.js",
            "linkage.js",
            "graphLoader.js",
            "ui.js",
            "docPanel.js",
            "mermaidViewer.js",
            "app.js",
        ]

        # Embed CSS
        css_content = ""
        for css_file in css_files:
            try:
                content = (assets_dir / css_file).read_text(encoding="utf-8")
                css_content += f"\n<style>\n/* {css_file} */\n{content}\n</style>"
            except Exception:
                pass

        # Embed JS
        js_content = ""
        for js_file in js_files:
            try:
                content = (assets_dir / js_file).read_text(encoding="utf-8")
                js_content += f"\n<script>\n/* {js_file} */\n{content}\n</script>"
            except Exception:
                pass

        # Embed Mermaid (CDN fallback or local if available)
        mermaid_script = '<script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>'

        # Inject Graph Data
        data_script = f"""
        <script>
            /* Embedded Graph Data */
            const GRAPH_DATA = {graph_json};
            const MERMAID_GRAPH_DATA = `{graph_mermaid}`;

            // Make globally accessible
            window.GRAPH_DATA = GRAPH_DATA;
            window.MERMAID_GRAPH_DATA = MERMAID_GRAPH_DATA;
            window.embeddedGraphData = GRAPH_DATA;
        </script>
        """

        # Replace links/scripts in template with embedded content
        # 1. Remove existing link tags
        import re

        html = re.sub(r'<link rel="stylesheet" href="[^"]+">', "", template)

        # 2. Remove existing script tags (except mermaid if we keep it external)
        html = re.sub(r'<script src="[^"]+"></script>', "", html)

        # 3. Inject CSS before </head>
        html = html.replace("</head>", f"{css_content}\n</head>")

        # 4. Inject JS and Data before </body>
        html = html.replace(
            "</body>", f"{mermaid_script}\n{data_script}\n{js_content}\n</body>"
        )

        return html

    def _get_symbol_color(self, kind: str) -> str:
        """Get color for symbol type."""
        colors = {
            "class": "lightgreen",
            "function": "lightyellow",
            "method": "lightcoral",
            "import": "lightgray",
        }
        return colors.get(kind, "white")

    def _get_layer(self, file_path: str) -> str:
        """Determine the architectural layer of a file."""
        path = file_path.lower()
        if any(x in path for x in ["dockerfile", ".yml", ".yaml", "requirements.txt", "package.json", "pyproject.toml", ".env"]):
            return "infra"
        if path.endswith(".py"):
            return "backend"
        if any(path.endswith(x) for x in [".js", ".jsx", ".ts", ".tsx", ".css", ".html"]):
            return "frontend"
        if any(path.endswith(x) for x in [".sql", ".db"]):
            return "data"
        if path.endswith(".md"):
            return "docs"
        return "other"

    def close(self):
        """Close database session."""
        self.session.close()
