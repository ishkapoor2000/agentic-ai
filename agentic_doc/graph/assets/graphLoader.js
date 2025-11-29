/**
 * GraphLoader Module
 * Parses graph data and instantiates interactive LinkageSystem entities.
 */
class GraphLoader {
    constructor(linkageSystem, canvas) {
        this.system = linkageSystem;
        this.canvas = canvas;
        this.nodeMap = new Map(); // Maps node ID to Joint
    }

    /**
     * Parses Mermaid string and loads the graph
     * @param {string} mermaidData - The Mermaid graph string
     */
    loadGraph(mermaidData) {
        if (!mermaidData) return;

        // Check if it's a string (Mermaid) or object (JSON)
        let graphData;
        if (typeof mermaidData === 'string') {
            graphData = this.parseMermaid(mermaidData);
        } else {
            graphData = mermaidData;
        }

        this.renderGraph(graphData);
    }

    /**
     * Simple Regex-based Mermaid Parser
     */
    parseMermaid(text) {
        const nodes = [];
        const edges = [];
        const nodeMap = new Map();

        const lines = text.split('\n');
        let currentSubgraph = null;

        lines.forEach(line => {
            line = line.trim();
            if (!line || line.startsWith('graph') || line === 'end') return;

            // Subgraph (Directory)
            if (line.startsWith('subgraph')) {
                const match = line.match(/subgraph\s+(\w+)\["(.+?)"\]/);
                if (match) {
                    const id = match[1];
                    const label = match[2];
                    if (!nodeMap.has(id)) {
                        const node = { id, label, kind: 'directory' };
                        nodes.push(node);
                        nodeMap.set(id, node);
                    }
                    currentSubgraph = id;
                }
                return;
            }

            // Edges: id1 --> id2
            if (line.includes('-->')) {
                const parts = line.split('-->');
                const sourceId = this.extractId(parts[0]);
                const targetId = this.extractId(parts[1]);

                if (sourceId && targetId) {
                    edges.push({ source: sourceId, target: targetId, relation: 'dependency' });
                }
                return;
            }

            // Nodes: id["label"] or id[label]
            // Matches: file_18["config.py"] or sym_30[class: Config]
            const nodeMatch = line.match(/(\w+)\["?(.*?)"?\]/);
            if (nodeMatch) {
                const id = nodeMatch[1];
                let label = nodeMatch[2];
                let kind = 'file';

                // Heuristic for kind based on label or ID
                if (label.startsWith('class:')) {
                    kind = 'class';
                    label = label.replace('class: ', '');
                } else if (label.startsWith('function:') || label.startsWith('method:')) {
                    kind = 'function';
                    label = label.replace('function: ', '').replace('method: ', '');
                } else if (id.startsWith('file')) {
                    kind = 'file';
                }

                if (!nodeMap.has(id)) {
                    const node = { id, label, kind };
                    nodes.push(node);
                    nodeMap.set(id, node);
                }

                // If inside a subgraph, add an edge from subgraph to node (hierarchy)
                if (currentSubgraph) {
                    edges.push({ source: currentSubgraph, target: id, relation: 'belongs_to' });
                }
            }
        });

        return { nodes, edges };
    }

    extractId(str) {
        const match = str.trim().match(/^(\w+)/);
        return match ? match[1] : null;
    }

    /**
     * Renders the parsed graph data
     */
    renderGraph(graphData) {
        // Clear existing simulation
        this.system.clear();
        this.nodeMap.clear();

        if (!graphData || !graphData.nodes) {
            console.error("Invalid graph data");
            return;
        }

        console.log("Loading graph...", graphData.nodes.length, "nodes");

        // 1. Create Joints for Nodes
        graphData.nodes.forEach((node, index) => {
            // Initial random layout centered around origin
            const spread = Math.max(800, graphData.nodes.length * 15);
            const x = (Math.random() - 0.5) * spread;
            const y = (Math.random() - 0.5) * spread;

            const joint = this.system.addJoint(x, y);

            // Custom properties for visualization
            joint.label = node.label || node.id;
            joint.nodeId = node.id;
            joint.type = node.type || node.kind || 'file'; // 'file', 'class', 'function', 'directory'

            // CRITICAL: Store full node data for Magic Panel & Heatmap
            joint.data = node;

            // Set visual properties based on type
            if (joint.type === 'directory') {
                joint.radius = 40;
                joint.mass = 10;
            } else if (joint.type === 'file') {
                joint.radius = 30;
                joint.mass = 5;
            } else if (joint.type === 'class') {
                joint.radius = 20;
                joint.mass = 3;
            } else {
                joint.radius = 10;
                joint.mass = 1;
            }

            this.nodeMap.set(node.id, joint);
        });

        // 2. Create Links for Edges
        if (graphData.edges) {
            graphData.edges.forEach(edge => {
                const source = this.nodeMap.get(edge.source);
                const target = this.nodeMap.get(edge.target);

                if (source && target) {
                    const link = this.system.addLink(source, target);
                    if (link) {
                        link.type = edge.relation || 'dependency';
                        // Adjust spring length based on relationship
                        if (link.type === 'belongs_to') {
                            link.length = 100; // Hierarchy
                            link.stiffness = 0.08;
                        } else {
                            link.length = 250; // Dependency
                            link.stiffness = 0.03;
                        }
                    }
                }
            });
        }

        console.log(`Loaded ${graphData.nodes.length} nodes and ${graphData.edges ? graphData.edges.length : 0} edges.`);

        // Start the simulation
        this.system.start();
    }
}
