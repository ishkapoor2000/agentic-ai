"""
Dependency Graph Visualizer for creating visual representations of code dependencies.
Supports Mermaid, DOT, and interactive HTML visualizations.
"""

from pathlib import Path

from sqlmodel import Session

from agentic_doc.analysis.dependency_analyzer import DependencyAnalyzer
from agentic_doc.analysis.usage_tracker import UsageTracker
from agentic_doc.db.schema import File, Symbol


class DependencyVisualizer:
    """Create visual dependency graphs in various formats."""

    def __init__(self, session: Session):
        self.session = session
        self.dep_analyzer = DependencyAnalyzer(session)
        self.usage_tracker = UsageTracker(session)

    def generate_mermaid_dependency_graph(
        self, file_id: int | None = None, max_nodes: int = 50
    ) -> str:
        """
        Generate a Mermaid flowchart showing dependencies.

        Args:
            file_id: Optional file ID to scope the graph
            max_nodes: Maximum number of nodes to include

        Returns:
            Mermaid diagram as string
        """
        graph_data = self.dep_analyzer.get_dependency_graph(file_id)

        # Limit nodes if too many
        nodes = graph_data["nodes"][:max_nodes]
        node_ids = {n["id"] for n in nodes}

        # Filter edges to only include nodes we're showing
        edges = [
            e
            for e in graph_data["edges"]
            if e["source"] in node_ids and e["target"] in node_ids
        ]

        # Build Mermaid
        lines = ["graph TD"]

        # Add nodes with styling based on importance and kind
        for node in nodes:
            node_id = f"node_{node['id']}"
            label = f"{node['name']}"

            # Style based on kind
            if node["kind"] == "class":
                shape = f"[{label}]"
            elif node["kind"] == "function":
                shape = f"({label})"
            else:
                shape = f"{{{label}}}"

            # Add importance indicator
            if node["importance"] > 10:
                lines.append(f"    {node_id}{shape}:::important")
            elif node["importance"] > 5:
                lines.append(f"    {node_id}{shape}:::moderate")
            else:
                lines.append(f"    {node_id}{shape}")

        # Add edges
        for edge in edges:
            source = f"node_{edge['source']}"
            target = f"node_{edge['target']}"
            edge_label = edge["type"]

            if edge_label == "CALLS":
                lines.append(f"    {source} -->|calls| {target}")
            elif edge_label == "IMPORTS":
                lines.append(f"    {source} -.->|imports| {target}")
            elif edge_label == "INHERITS":
                lines.append(f"    {source} ==>|inherits| {target}")
            else:
                lines.append(f"    {source} --> {target}")

        # Add styling
        lines.append("")
        lines.append("    classDef important fill:#ff6b6b,stroke:#c92a2a,color:#fff")
        lines.append("    classDef moderate fill:#69db7c,stroke:#37b24d,color:#000")

        return "\n".join(lines)

    def generate_file_dependency_mermaid(
        self, scope_files: list[str] | None = None
    ) -> str:
        """
        Generate a Mermaid diagram showing file-level dependencies.

        Args:
            scope_files: Optional list of file paths to include

        Returns:
            Mermaid diagram as string
        """
        from sqlmodel import select

        # Get all files
        if scope_files:
            files = self.session.exec(
                select(File).where(File.rel_path.in_(scope_files))
            ).all()
        else:
            files = self.session.exec(select(File)).all()

        # Build file dependency map
        file_deps = {}
        for file in files:
            deps = self.dep_analyzer.get_file_dependencies(file.id)
            file_deps[file.rel_path] = deps

        # Build Mermaid
        lines = ["graph LR"]

        for file_path, deps in file_deps.items():
            # Sanitize file path for Mermaid ID
            file_id = file_path.replace("/", "_").replace(".", "_")
            file_name = file_path.split("/")[-1]

            lines.append(f"    {file_id}[{file_name}]")

            # Add import edges
            for import_path in deps["imports"]:
                if not scope_files or import_path in scope_files:
                    import_id = import_path.replace("/", "_").replace(".", "_")
                    lines.append(f"    {file_id} -->|imports| {import_id}")

        return "\n".join(lines)

    def calculate_criticality_score(self, symbol_id: int) -> dict:
        """
        Calculate how critical/risky a function is based on multiple factors.
        
        Args:
            symbol_id: ID of the symbol to analyze
            
        Returns:
            Dict with score, risk level, and component metrics
        """
        stats = self.usage_tracker.get_usage_statistics(symbol_id)
        deps = self.dep_analyzer.get_symbol_dependencies(symbol_id)
        dependents = self.dep_analyzer.get_symbol_dependents(symbol_id)
        
        # Get LOC from symbol
        symbol = self.session.get(Symbol, symbol_id)
        loc = (symbol.line_end - symbol.line_start) if symbol else 0
        
        # Calculate components
        usage_count = stats["total_usages"]
        fan_in = len(dependents)  # How many call this
        fan_out = len(deps)       # How many this calls
        complexity_factor = 1 if loc > 100 else 0
        
        # Weighted score
        score = (
            usage_count * 2.0 +
            fan_in * 1.5 +
            fan_out * 0.5 +
            complexity_factor * 10
        )
        
        # Normalize to 0-100
        normalized = min(100, int(score * 0.8))
        
        # Risk level
        if normalized >= 80:
            risk = "HIGH"
            emoji = "🔴"
        elif normalized >= 50:
            risk = "MEDIUM"
            emoji = "🟡"
        else:
            risk = "LOW"
            emoji = "🟢"
        
        return {
            "score": normalized,
            "risk_level": risk,
            "risk_emoji": emoji,
            "usage_count": usage_count,
            "fan_in": fan_in,
            "fan_out": fan_out,
            "loc": loc
        }

    def generate_hot_functions_report(self, limit: int = 20) -> str:
        """
        Generate a markdown report of the hottest (most used) functions.

        Args:
            limit: Number of functions to include

        Returns:
            Markdown report as string
        """
        hot_functions = self.usage_tracker.get_hot_functions(limit=limit)

        lines = [
            "# Hot Functions Report",
            "",
            "Functions ranked by usage frequency across the codebase.",
            "",
            "| Rank | Function | Kind | File | Usage Count |",
            "|------|----------|------|------|-------------|",
        ]

        for i, func in enumerate(hot_functions, 1):
            lines.append(
                f"| {i} | `{func['name']}` | {func['kind']} | "
                f"`{func['file']}` | {func['usage_count']} |"
            )

        lines.append("")
        lines.append("## Dependency Graphs")
        lines.append("")
        lines.append("### Top 5 Function Dependencies")
        lines.append("")

        # Add mini dependency graphs for top 5
        for func in hot_functions[:5]:
            symbol = self.session.get(Symbol, func["id"])
            if symbol:
                lines.append(f"#### {func['name']}")
                lines.append("")

                deps = self.dep_analyzer.get_symbol_dependencies(symbol.id)
                dependents = self.dep_analyzer.get_symbol_dependents(symbol.id)

                lines.append(f"**Dependencies ({len(deps)}):**")
                for dep in deps[:5]:
                    lines.append(f"- `{dep['target_name']}` ({dep['reference_type']})")

                lines.append("")
                lines.append(f"**Used by ({len(dependents)}):**")
                for dependent in dependents[:5]:
                    lines.append(
                        f"- `{dependent['source_name']}` ({dependent['reference_type']})"
                    )

                lines.append("")

        return "\n".join(lines)

    def generate_enhanced_hot_functions_report(self, limit: int = 20) -> str:
        """
        Generate ENHANCED critical code report with criticality scoring.
        
        Args:
            limit: Number of functions to analyze
            
        Returns:
            Markdown report with risk analysis
        """
        hot_functions = self.usage_tracker.get_hot_functions(limit=limit)
        
        # Calculate criticality for each
        enriched = []
        for func in hot_functions:
            criticality = self.calculate_criticality_score(func["id"])
            enriched.append({**func, **criticality})
        
        # Sort by criticality score
        enriched.sort(key=lambda x: x["score"], reverse=True)
        
        lines = [
            "# 🔥 Critical Code Report",
            "",
            "> **Deputy CTO Summary**: These are your **load-bearing** functions. Changes here affect the entire system.",
            "",
            "---",
            "",
            "## 📊 Top Critical Functions",
            "",
            "| 🏆 | Function | Criticality | Usage | Risk | File |",
            "|----|----------|-------------|-------|------|------|",
        ]
        
        for i, func in enumerate(enriched[:10], 1):
            lines.append(
                f"| {i} | `{func['name']}` | {func['risk_emoji']} **{func['score']}/100** | "
                f"{func['usage_count']} calls | {func['risk_emoji']} {func['risk_level']} | `{func['file']}` |"
            )
        
        lines.extend([
            "",
            "---",
            "",
            "## 🎯 Why This Matters",
            "",
            "### High-Risk Changes (🔴)",
            "These functions are **critical infrastructure**. Before modifying:",
            "- ✅ Write comprehensive tests",
            "- ✅ Review with 2+ engineers",
            "- ✅ Deploy with feature flag",
            "- ✅ Monitor error rates closely",
            "",
            "### Medium-Risk Changes (🟡)",
            "Widely used but manageable:",
            "- ✅ Unit test coverage",
            "- ✅ Code review required",
            "- ✅ Monitor after deployment",
            "",
            "---",
            "",
            "## 📈 Dependency Impact Analysis",
            "",
        ])
        
        # Deep dive on top 3 critical functions
        for func in enriched[:3]:
            symbol = self.session.get(Symbol, func["id"])
            if not symbol:
                continue
                
            deps = self.dep_analyzer.get_symbol_dependencies(symbol.id)
            dependents = self.dep_analyzer.get_symbol_dependents(symbol.id)
            
            lines.extend([
                f"### `{func['name']}` Deep Dive",
                f"**Criticality Score: {func['score']}/100** {func['risk_emoji']}",
                "",
                "**Why It's Critical**:",
                f"- Called by **{func['fan_in']} different functions**",
                f"- Uses **{func['fan_out']} dependencies**",
                f"- Total usage: **{func['usage_count']} times**",
            ])
            
            if func['loc'] > 100:
                lines.append(f"- Large function: **{func['loc']} lines** (complexity risk)")
            
            lines.append("")
            lines.append("**What Calls It** (Top 5):")
            for i, dep in enumerate(dependents[:5], 1):
                lines.append(f"{i}. `{dep['source_name']}` in `{dep['file_path']}`")
            
            lines.append("")
            
            if func['fan_out'] > 0:
                lines.append("**What It Calls** (Top 5):")
                for i, dep in enumerate(deps[:5], 1):
                    lines.append(f"{i}. `{dep['target_name']}` ({dep['reference_type']})")
                lines.append("")
            
            # Recommendation
            if func['score'] >= 80 and func['fan_in'] > 10:
                lines.extend([
                    "**Recommendation**: ",
                    "⚠️ Consider **wrapper functions** for different use cases to reduce coupling",
                    "",
                ])
            
            lines.extend(["", "---", ""])
        
        # Find unused functions
        from sqlmodel import select
        all_symbols = self.session.exec(
            select(Symbol).where(Symbol.kind.in_(["function", "method"]))
        ).all()
        
        unused = []
        for sym in all_symbols:
            stats = self.usage_tracker.get_usage_statistics(sym.id)
            if stats["total_usages"] <= 1:
                file_obj = self.session.get(File, sym.file_id)
                unused.append({
                    "name": sym.name,
                    "file": file_obj.rel_path if file_obj else "unknown",
                    "usage": stats["total_usages"]
                })
        
        if unused:
            lines.extend([
                "## 🔍 Unused/Rare Functions (Candidates for Removal)",
                "",
                "These functions are called < 2 times - safe to deprecate:",
                "",
            ])
            
            for func in unused[:10]:  # Top 10 unused
                lines.append(f"- `{func['name']}()` in `{func['file']}` - {func['usage']} usage")
            
            if len(unused) > 10:
                lines.append(f"\n*...and {len(unused) - 10} more unused functions*")
            
            lines.extend(["", "---", ""])
        
        lines.extend([
            "## 📅 Metadata",
            "",
            f"- **Total Functions Analyzed**: {len(hot_functions)}",
            f"- **High-Risk Functions**: {len([f for f in enriched if f['risk_level'] == 'HIGH'])}",
            f"- **Medium-Risk Functions**: {len([f for f in enriched if f['risk_level'] == 'MEDIUM'])}",
            f"- **Low-Risk Functions**: {len([f for f in enriched if f['risk_level'] == 'LOW'])}",
            f"- **Unused Functions Found**: {len(unused)}",
        ])
        
        return "\n".join(lines)

    def generate_usage_heatmap_data(self, file_id: int | None = None) -> dict:
        """
        Generate data for a usage heatmap visualization.

        Args:
            file_id: Optional file ID to scope the analysis

        Returns:
            Dict with heatmap data suitable for visualization
        """
        from sqlmodel import select

        if file_id:
            symbols = self.session.exec(
                select(Symbol).where(Symbol.file_id == file_id)
            ).all()
        else:
            # Get top 50 symbols by usage
            hot_symbols = self.usage_tracker.get_hot_functions(limit=50)
            symbols = [self.session.get(Symbol, s["id"]) for s in hot_symbols]

        heatmap_data = []

        for symbol in symbols:
            if symbol:
                stats = self.usage_tracker.get_usage_statistics(symbol.id)
                usages = self.usage_tracker.get_usage_locations(symbol.id)

                # Count usage by file
                file_usage = {}
                for usage in usages:
                    file_usage[usage["file"]] = file_usage.get(usage["file"], 0) + 1

                heatmap_data.append(
                    {
                        "symbol": symbol.name,
                        "kind": symbol.kind,
                        "total_usage": stats["total_usages"],
                        "file_count": stats["files_used_in"],
                        "usage_by_file": file_usage,
                    }
                )

        return {
            "data": heatmap_data,
            "metadata": {
                "total_symbols": len(heatmap_data),
                "total_files": len(
                    {
                        file
                        for item in heatmap_data
                        for file in item["usage_by_file"]
                    }
                ),
            },
        }

    def export_interactive_html(
        self, output_path: Path, file_id: int | None = None
    ) -> None:
        """
        Export an interactive HTML visualization of dependencies.

        Args:
            output_path: Path to save the HTML file
            file_id: Optional file ID to scope the visualization
        """
        graph_data = self.dep_analyzer.get_dependency_graph(file_id)

        # Build HTML with embedded D3.js visualization
        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Dependency Graph</title>
    <script src="https://d3js.org/d3.v7.min.js"></script>
    <style>
        body {{
            margin: 0;
            font-family: Arial, sans-serif;
        }}
        #graph {{
            width: 100vw;
            height: 100vh;
        }}
        .node {{
            cursor: pointer;
        }}
        .node circle {{
            stroke: #fff;
            stroke-width: 2px;
        }}
        .node.class circle {{
            fill: #69db7c;
        }}
        .node.function circle {{
            fill: #4dabf7;
        }}
        .node.method circle {{
            fill: #ffd43b;
        }}
        .link {{
            fill: none;
            stroke: #999;
            stroke-opacity: 0.6;
        }}
        .link.CALLS {{
            stroke: #4dabf7;
        }}
        .link.IMPORTS {{
            stroke: #fd7e14;
            stroke-dasharray: 5,5;
        }}
        .link.INHERITS {{
            stroke: #69db7c;
            stroke-width: 3px;
        }}
        .node text {{
            font-size: 12px;
            pointer-events: none;
        }}
        #info {{
            position: absolute;
            top: 10px;
            right: 10px;
            background: white;
            padding: 15px;
            border: 1px solid #ccc;
            border-radius: 5px;
            max-width: 300px;
        }}
    </style>
</head>
<body>
    <div id="graph"></div>
    <div id="info">
        <h3>Dependency Graph</h3>
        <p>Nodes: {len(graph_data["nodes"])}</p>
        <p>Edges: {len(graph_data["edges"])}</p>
        <p><strong>Click a node for details</strong></p>
    </div>
    <script>
        const graphData = {self._graph_to_json(graph_data)};

        const width = window.innerWidth;
        const height = window.innerHeight;

        const svg = d3.select("#graph")
            .append("svg")
            .attr("width", width)
            .attr("height", height);

        const simulation = d3.forceSimulation(graphData.nodes)
            .force("link", d3.forceLink(graphData.edges).id(d => d.id).distance(100))
            .force("charge", d3.forceManyBody().strength(-300))
            .force("center", d3.forceCenter(width / 2, height / 2));

        const link = svg.append("g")
            .selectAll("line")
            .data(graphData.edges)
            .enter().append("line")
            .attr("class", d => "link " + d.type)
            .attr("stroke-width", 2);

        const node = svg.append("g")
            .selectAll("g")
            .data(graphData.nodes)
            .enter().append("g")
            .attr("class", d => "node " + d.kind)
            .call(d3.drag()
                .on("start", dragstarted)
                .on("drag", dragged)
                .on("end", dragended));

        node.append("circle")
            .attr("r", d => Math.max(5, Math.min(20, d.importance * 2)));

        node.append("text")
            .attr("dx", 12)
            .attr("dy", ".35em")
            .text(d => d.name);

        node.on("click", function(event, d) {{
            d3.select("#info").html(`
                <h3>${{d.name}}</h3>
                <p><strong>Type:</strong> ${{d.kind}}</p>
                <p><strong>File:</strong> ${{d.file}}</p>
                <p><strong>Importance:</strong> ${{d.importance}}</p>
            `);
        }});

        simulation.on("tick", () => {{
            link
                .attr("x1", d => d.source.x)
                .attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x)
                .attr("y2", d => d.target.y);

            node.attr("transform", d => `translate(${{d.x}},${{d.y}})`);
        }});

        function dragstarted(event) {{
            if (!event.active) simulation.alphaTarget(0.3).restart();
            event.subject.fx = event.subject.x;
            event.subject.fy = event.subject.y;
        }}

        function dragged(event) {{
            event.subject.fx = event.x;
            event.subject.fy = event.y;
        }}

        function dragended(event) {{
            if (!event.active) simulation.alphaTarget(0);
            event.subject.fx = null;
            event.subject.fy = null;
        }}
    </script>
</body>
</html>"""

        output_path.write_text(html)

    def _graph_to_json(self, graph_data: dict) -> str:
        """Convert graph data to JSON for embedding in HTML."""
        import json

        # Transform nodes for D3
        nodes = [
            {
                "id": n["id"],
                "name": n["name"],
                "kind": n["kind"],
                "file": n["file"],
                "importance": n["importance"],
            }
            for n in graph_data["nodes"]
        ]

        # Transform edges for D3
        edges = [
            {"source": e["source"], "target": e["target"], "type": e["type"]}
            for e in graph_data["edges"]
        ]

        return json.dumps({"nodes": nodes, "edges": edges})

    def export_mermaid_html(
        self, output_path: Path, file_id: int | None = None
    ) -> None:
        """
        Export an interactive HTML viewer for Mermaid dependency graph.
        
        Args:
            output_path: Path to save the HTML file
            file_id: Optional file ID to scope the visualization
        """
        from agentic_doc.config import load_config
        config = load_config()
        root_path = Path(config.root_path).resolve()

        # Generate Mermaid graph definition
        mermaid_graph = self.generate_mermaid_dependency_graph(file_id)
        
        # Ensure graph is TD (Vertical)
        if "graph LR" in mermaid_graph:
            mermaid_graph = mermaid_graph.replace("graph LR", "graph TD")
        elif "graph TD" not in mermaid_graph:
             # If no direction specified, prepend it
             mermaid_graph = "graph TD\n" + mermaid_graph
        
        # Add click events for nodes
        graph_data = self.dep_analyzer.get_dependency_graph(file_id)
        nodes = graph_data["nodes"][:50] # Match default limit of generate_mermaid_dependency_graph
        
        # We don't need to inject click events into mermaid syntax anymore
        # We will handle clicks via the rendered SVG elements in JS
        
        # Escape backticks in mermaid graph to avoid JS errors
        mermaid_graph_safe = mermaid_graph.replace("`", "\\`")

        html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Interactive Dependency Graph</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/svg-pan-zoom@3.6.1/dist/svg-pan-zoom.min.js"></script>
    <style>
        body {{
            margin: 0;
            padding: 0;
            overflow: hidden;
            background-color: #1e1e1e; /* Dark background */
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            color: #e0e0e0;
        }}
        #container {{
            width: 100vw;
            height: 100vh;
            display: flex;
            justify_content: center;
            align-items: center;
            background-image: 
                linear-gradient(#333 1px, transparent 1px),
                linear-gradient(90deg, #333 1px, transparent 1px);
            background-size: 20px 20px;
        }}
        #graph-div {{
            width: 100%;
            height: 100%;
            opacity: 0; /* Hidden until rendered */
            transition: opacity 0.5s ease-in;
        }}
        .controls {{
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #2d2d2d;
            padding: 10px;
            border-radius: 8px;
            box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            z-index: 100;
            display: flex;
            gap: 8px;
        }}
        .controls button {{
            padding: 8px 12px;
            cursor: pointer;
            background: #007bff;
            color: white;
            border: none;
            border-radius: 4px;
            font-weight: bold;
            transition: background 0.2s;
        }}
        .controls button:hover {{
            background: #0056b3;
        }}
        /* Tooltip styling */
        .mermaidTooltip {{
            background-color: #333 !important;
            color: #fff !important;
            border: 1px solid #555 !important;
        }}
        
        /* Node styling overrides */
        .node rect, .node circle, .node polygon {{
            fill: #2d2d2d !important;
            stroke: #555 !important;
        }}
        .node .label {{
            color: #e0e0e0 !important;
        }}
        
        /* Loading indicator */
        #loading {{
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            font-size: 24px;
            color: #007bff;
        }}
    </style>
</head>
<body>
    <div id="loading">Rendering Graph...</div>
    <div id="container">
        <div id="graph-div"></div>
    </div>
    
    <div class="controls">
        <button onclick="zoomIn()">+</button>
        <button onclick="zoomOut()">-</button>
        <button onclick="resetZoom()">Reset</button>
        <button onclick="fitGraph()">Fit</button>
    </div>

    <script>
        // Graph Data
        const graphDefinition = `{mermaid_graph_safe}`;
        const nodePaths = {self._get_node_paths_json(nodes, root_path)};

        mermaid.initialize({{
            startOnLoad: false,
            securityLevel: 'loose',
            theme: 'dark',
            flowchart: {{
                useMaxWidth: false,
                htmlLabels: true,
                curve: 'basis'
            }}
        }});

        var panZoom = null;

        async function renderGraph() {{
            try {{
                const element = document.querySelector('#graph-div');
                const {{ svg }} = await mermaid.render('mermaid-svg', graphDefinition);
                element.innerHTML = svg;
                
                // Setup interactions
                setupInteractions();
                
                // Initialize PanZoom
                initPanZoom();
                
                // Show graph, hide loading
                element.style.opacity = 1;
                document.getElementById('loading').style.display = 'none';
                
            }} catch (error) {{
                console.error('Mermaid rendering failed:', error);
                document.getElementById('loading').innerText = 'Rendering Failed: ' + error.message;
            }}
        }}

        function setupInteractions() {{
            // Add click handlers to nodes
            const nodes = document.querySelectorAll('.node');
            nodes.forEach(node => {{
                // Extract ID from mermaid node id (e.g., "flowchart-node_123-...")
                const idMatch = node.id.match(/node_(\\d+)/);
                if (idMatch) {{
                    const nodeId = parseInt(idMatch[1]);
                    const path = nodePaths[nodeId];
                    
                    if (path) {{
                        node.style.cursor = 'pointer';
                        node.onclick = () => {{
                            console.log("Opening:", path);
                            window.location.href = "vscode://file/" + path;
                        }};
                        
                        // Add hover effect
                        node.onmouseover = () => {{
                            node.querySelector('rect, circle, polygon').style.stroke = '#007bff';
                            node.querySelector('rect, circle, polygon').style.strokeWidth = '3px';
                        }};
                        node.onmouseout = () => {{
                            node.querySelector('rect, circle, polygon').style.stroke = '#555';
                            node.querySelector('rect, circle, polygon').style.strokeWidth = '1px';
                        }};
                    }}
                }}
            }});
        }}

        function initPanZoom() {{
            const svg = document.querySelector('#graph-div svg');
            if (!svg) return;

            // Make SVG responsive
            svg.style.width = '100%';
            svg.style.height = '100%';
            svg.style.maxWidth = 'none';

            panZoom = svgPanZoom(svg, {{
                zoomEnabled: true,
                controlIconsEnabled: false,
                fit: true,
                center: true,
                minZoom: 0.1,
                maxZoom: 20,
                dblClickZoomEnabled: true,
                mouseWheelZoomEnabled: true
            }});
        }}

        // Control functions
        function zoomIn() {{ if(panZoom) panZoom.zoomIn(); }}
        function zoomOut() {{ if(panZoom) panZoom.zoomOut(); }}
        function resetZoom() {{ if(panZoom) panZoom.resetZoom(); }}
        function fitGraph() {{ 
            if(panZoom) {{
                panZoom.fit();
                panZoom.center();
            }}
        }}

        // Start rendering
        renderGraph();
    </script>
</body>
</html>"""
        
        output_path.write_text(html)

    def _get_node_paths_json(self, nodes: list[dict], root_path: Path) -> str:
        """Helper to generate JSON mapping of node IDs to file paths."""
        import json
        mapping = {}
        for node in nodes:
            # Create absolute path
            abs_path = str(root_path / node['file'])
            mapping[node['id']] = abs_path
        return json.dumps(mapping)
