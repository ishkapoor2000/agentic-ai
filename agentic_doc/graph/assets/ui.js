// ================================================
// UI CONTROLLER - Mindmap Controls
// ================================================

class UIController {
    constructor(canvas, linkageSystem) {
        this.canvas = canvas;
        this.linkageSystem = linkageSystem;

        this.currentTool = 'select';
        this.isDragging = false;
        this.dragStartWorld = null;

        // Graph Loader instance
        this.graphLoader = new GraphLoader(linkageSystem, canvas);

        this.setupToolbar();
        this.setupLayerToggles(); // New
        this.setupSearch();       // New
        this.setupSimulationControls();
        this.setupCanvas();
        this.setupWelcome();
        this.updateStats();

        // Load graph initially if data is available
        if (window.MERMAID_GRAPH_DATA) {
            setTimeout(() => {
                this.graphLoader.loadGraph(window.MERMAID_GRAPH_DATA);
                this.updateStats();
            }, 500);
        }
    }

    setupToolbar() {
        // Tool buttons (Simplified for Mindmap)
        const toolButtons = document.querySelectorAll('.tool-btn');
        toolButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                // Only 'select' and 'pan' are relevant now
                const tool = btn.dataset.tool;
                if (tool === 'select' || tool === 'pan') {
                    this.selectTool(tool);
                    toolButtons.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                }
            });
        });

        // Reset view button
        document.getElementById('reset-view').addEventListener('click', () => {
            this.canvas.resetView();
        });

        // Load Graph Button (New)
        const loadBtn = document.getElementById('load-graph-btn'); // Will add to HTML
        if (loadBtn) {
            loadBtn.addEventListener('click', () => {
                if (window.MERMAID_GRAPH_DATA) {
                    this.graphLoader.loadGraph(window.MERMAID_GRAPH_DATA);
                    this.updateStats();
                } else {
                    alert('No graph data found!');
                }
            });
        }

        // Reset Layout Button (New)
        const layoutBtn = document.getElementById('reset-layout-btn'); // Will add to HTML
        if (layoutBtn) {
            layoutBtn.addEventListener('click', () => {
                this.linkageSystem.joints.forEach(j => {
                    if (!j.isFixed) {
                        j.x += (Math.random() - 0.5) * 100;
                        j.y += (Math.random() - 0.5) * 100;
                    }
                });
                this.linkageSystem.start(); // Ensure physics is running
            });
        }

        // Clear all button
        document.getElementById('clear-all').addEventListener('click', () => {
            if (confirm('Clear the entire mindmap?')) {
                this.linkageSystem.clear();
                this.canvas.render();
                this.updateStats();
            }
        });

        // Heatmap Toggle (New)
        const heatmapToggle = document.getElementById('heatmap-toggle'); // Will add to HTML
        if (heatmapToggle) {
            heatmapToggle.addEventListener('change', (e) => {
                this.toggleHeatmap(e.target.checked);
            });
        }

        // Keyboard shortcuts
        window.addEventListener('keydown', (e) => {
            if (e.target.tagName === 'INPUT') return;

            switch (e.key.toLowerCase()) {
                case 'v':
                    this.selectTool('select');
                    break;
                case 'space':
                    if (!e.repeat) {
                        this.selectTool('pan');
                        this.canvas.canvas.style.cursor = 'grab';
                    }
                    break;
                case 'home':
                    this.canvas.resetView();
                    break;
            }
        });

        window.addEventListener('keyup', (e) => {
            if (e.code === 'Space') {
                this.selectTool('select');
                this.canvas.canvas.style.cursor = 'default';
            }
        });
    }

    setupLayerToggles() {
        const toggles = document.querySelectorAll('.layer-toggle input');
        toggles.forEach(toggle => {
            toggle.addEventListener('change', () => {
                this.filterNodes();
            });
        });
    }

    setupSearch() {
        const searchInput = document.getElementById('node-search');
        if (!searchInput) return;

        searchInput.addEventListener('input', (e) => {
            const term = e.target.value.toLowerCase();
            this.filterNodes(term);
        });

        // Zoom to first match on Enter
        searchInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                const term = e.target.value.toLowerCase();
                const match = this.linkageSystem.joints.find(j =>
                    j.label.toLowerCase().includes(term) && !j.isHidden
                );
                if (match) {
                    // Zoom to node
                    // This requires canvas to have a method to zoom to point, 
                    // or we just center view on it.
                    // For now, let's just center.
                    this.canvas.offsetX = this.canvas.canvas.width / 2 - match.x * this.canvas.scale;
                    this.canvas.offsetY = this.canvas.canvas.height / 2 - match.y * this.canvas.scale;

                    // Highlight it
                    this.linkageSystem.selectedJoint = match;
                    match.isSelected = true;
                }
            }
        });
    }

    filterNodes(searchTerm = '') {
        const activeLayers = Array.from(document.querySelectorAll('.layer-toggle input:checked'))
            .map(input => input.dataset.layer);

        const searchInput = document.getElementById('node-search');
        const term = searchTerm || (searchInput ? searchInput.value.toLowerCase() : '');

        this.linkageSystem.joints.forEach(joint => {
            // Determine layer (default to 'other' if not found in data)
            // Note: We need to ensure 'layer' property is available on joints.
            // The GraphLoader needs to pass this through.
            const layer = joint.data && joint.data.layer ? joint.data.layer : 'other';

            const layerMatch = activeLayers.includes(layer) || layer === 'other'; // Always show 'other' or make it toggleable? 
            // Let's assume 'other' is always shown or mapped to a default layer.
            // Actually, let's map unknown layers to 'other' and add a toggle for it if needed.
            // For now, if layer is missing, we show it.

            const nameMatch = joint.label.toLowerCase().includes(term);

            const isVisible = layerMatch && nameMatch;

            joint.isHidden = !isVisible;
        });

        // Also hide links connected to hidden nodes
        this.linkageSystem.links.forEach(link => {
            link.isHidden = link.joint1.isHidden || link.joint2.isHidden;
        });
    }

    setupSimulationControls() {
        // We keep play/pause for physics
        const playPauseBtn = document.getElementById('play-pause');
        if (playPauseBtn) {
            const playIcon = playPauseBtn.querySelector('.play-icon');
            const pauseIcon = playPauseBtn.querySelector('.pause-icon');
            const btnText = playPauseBtn.querySelector('.btn-text');

            playPauseBtn.addEventListener('click', () => {
                if (this.linkageSystem.isRunning) {
                    this.linkageSystem.stop();
                    this.canvas.stopAnimation();
                    if (playIcon) playIcon.style.display = 'block';
                    if (pauseIcon) pauseIcon.style.display = 'none';
                    if (btnText) btnText.textContent = 'Play Physics';
                } else {
                    this.linkageSystem.start();
                    this.canvas.startAnimation();
                    if (playIcon) playIcon.style.display = 'none';
                    if (pauseIcon) pauseIcon.style.display = 'block';
                    if (btnText) btnText.textContent = 'Pause Physics';
                }
            });
        }

        // Hide motor controls as they are not relevant
        const motorControls = document.querySelector('.motor-controls');
        if (motorControls) motorControls.style.display = 'none';
    }

    setupCanvas() {
        const canvasElement = this.canvas.canvas;

        canvasElement.addEventListener('click', (e) => {
            if (this.canvas.isPanning) return;

            const rect = canvasElement.getBoundingClientRect();
            const worldPos = this.canvas.screenToWorld(
                e.clientX - rect.left,
                e.clientY - rect.top
            );

            this.handleCanvasClick(worldPos.x, worldPos.y);
        });

        canvasElement.addEventListener('mousedown', (e) => {
            if (e.button !== 0 || this.currentTool !== 'select') return;

            const rect = canvasElement.getBoundingClientRect();
            const worldPos = this.canvas.screenToWorld(
                e.clientX - rect.left,
                e.clientY - rect.top
            );

            const joint = this.linkageSystem.getJointAt(worldPos.x, worldPos.y);
            if (joint) {
                this.isDragging = true;
                this.linkageSystem.draggedJoint = joint;
                this.dragStartWorld = worldPos;

                // If physics is paused, we might want to wake it up briefly or just move manually
                // For mindmap, usually physics is always running or runs on drag
                if (!this.linkageSystem.isRunning) {
                    this.linkageSystem.start();
                    this.canvas.startAnimation();
                }
            }
        });

        canvasElement.addEventListener('mousemove', (e) => {
            const rect = canvasElement.getBoundingClientRect();
            const worldPos = this.canvas.screenToWorld(
                e.clientX - rect.left,
                e.clientY - rect.top
            );

            // Handle dragging
            if (this.isDragging && this.linkageSystem.draggedJoint) {
                const joint = this.linkageSystem.draggedJoint;
                if (!joint.isFixed) {
                    joint.x = worldPos.x;
                    joint.y = worldPos.y;
                    // Reset velocity on drag to prevent shooting off
                    joint.px = worldPos.x;
                    joint.py = worldPos.y;
                }
                // No need to call render here if animation loop is running
                return;
            }

            // Update hover state
            this.updateHoverState(worldPos.x, worldPos.y);
        });

        canvasElement.addEventListener('mouseup', () => {
            this.isDragging = false;
            this.linkageSystem.draggedJoint = null;
        });

        canvasElement.addEventListener('mouseleave', () => {
            this.isDragging = false;
            this.linkageSystem.draggedJoint = null;
            this.clearHoverState();
        });
    }

    setupWelcome() {
        const welcomeMessage = document.getElementById('welcome-message');
        const closeBtn = document.getElementById('close-welcome');

        if (closeBtn && welcomeMessage) {
            closeBtn.addEventListener('click', () => {
                welcomeMessage.classList.add('hidden');
            });
        }
    }

    selectTool(tool) {
        window.previousTool = this.currentTool;
        this.currentTool = tool;
        window.currentTool = tool;
    }

    handleCanvasClick(worldX, worldY) {
        if (this.currentTool === 'select') {
            this.handleSelect(worldX, worldY);
        }
    }

    handleSelect(worldX, worldY) {
        // Clear previous selection
        this.linkageSystem.joints.forEach(j => j.isSelected = false);
        this.linkageSystem.links.forEach(l => l.isSelected = false);

        // Select joint or link
        const joint = this.linkageSystem.getJointAt(worldX, worldY);
        if (joint) {
            joint.isSelected = true;
            this.linkageSystem.selectedJoint = joint;
            console.log("Selected Node:", joint.label, joint.type);

            // Show Magic Panel
            this.showMagicPanel(joint);
        } else {
            const link = this.linkageSystem.getLinkAt(worldX, worldY);
            if (link) {
                link.isSelected = true;
                this.linkageSystem.selectedLink = link;
            }
            this.hideMagicPanel();
        }

        this.canvas.render();
    }

    showMagicPanel(node) {
        const panel = document.getElementById('magic-panel');
        if (!panel) return;

        const title = panel.querySelector('.magic-title');
        const subtitle = panel.querySelector('.magic-subtitle');
        const desc = panel.querySelector('.magic-desc');
        const meta = panel.querySelector('.magic-meta');

        // Reset
        panel.classList.remove('hidden');
        panel.className = 'magic-panel glass-panel'; // Reset classes

        // Title & Icon
        let icon = '📦';
        if (node.type === 'file') icon = '📄';
        if (node.data.kind === 'class') icon = '🧩';
        if (node.data.kind === 'function') icon = 'ƒ';

        // API Route Magic
        if (node.data.route_path) {
            icon = '🚀';
            panel.classList.add('is-route');
            title.innerHTML = `${icon} ${node.data.route_method} ${node.data.route_path}`;
            subtitle.textContent = `API Route • ${node.label}`;
        } else {
            title.innerHTML = `${icon} ${node.label}`;
            subtitle.textContent = `${node.type} • ${node.data.kind || ''}`;
        }

        // Description (Docstring or Generated)
        if (node.data.docstring) {
            // Simple cleanup of docstring
            const cleanDoc = node.data.docstring.split('\n')[0].trim();
            desc.textContent = cleanDoc;
        } else {
            desc.textContent = "No documentation available.";
        }

        // Metadata (Criticality)
        const criticality = node.data.criticality || 0;
        let hotness = '❄️ Cold';
        if (criticality > 5) hotness = '🔥 Hot';
        if (criticality > 20) hotness = '🌋 Critical';

        meta.innerHTML = `
            <div class="meta-item">
                <span class="meta-label">Criticality</span>
                <span class="meta-value">${hotness} (${criticality} refs)</span>
            </div>
        `;
    }

    hideMagicPanel() {
        const panel = document.getElementById('magic-panel');
        if (panel) panel.classList.add('hidden');
    }

    toggleHeatmap(enabled) {
        this.linkageSystem.joints.forEach(j => {
            if (enabled) {
                const criticality = j.data.criticality || 0;
                // Scale radius based on criticality (base 5, max 20)
                j.r = 5 + Math.min(15, criticality / 2);
                // Opacity handled in renderer or by class
                j.isHeatmap = true;
            } else {
                j.r = 5; // Reset radius
                j.isHeatmap = false;
            }
        });
        this.canvas.render();
    }

    updateHoverState(worldX, worldY) {
        let changed = false;

        // Clear previous hover
        if (this.linkageSystem.hoveredJoint) {
            this.linkageSystem.hoveredJoint.isHovered = false;
            this.linkageSystem.hoveredJoint = null;
            changed = true;
        }
        if (this.linkageSystem.hoveredLink) {
            this.linkageSystem.hoveredLink.isHovered = false;
            this.linkageSystem.hoveredLink = null;
            changed = true;
        }

        // Set new hover
        const joint = this.linkageSystem.getJointAt(worldX, worldY);
        if (joint) {
            joint.isHovered = true;
            this.linkageSystem.hoveredJoint = joint;
            changed = true;
            this.canvas.canvas.style.cursor = 'pointer';
        } else {
            const link = this.linkageSystem.getLinkAt(worldX, worldY);
            if (link) {
                link.isHovered = true;
                this.linkageSystem.hoveredLink = link;
                changed = true;
                this.canvas.canvas.style.cursor = 'pointer';
            } else {
                this.canvas.canvas.style.cursor = this.currentTool === 'pan' ? 'grab' : 'default';
            }
        }
    }

    clearHoverState() {
        if (this.linkageSystem.hoveredJoint) {
            this.linkageSystem.hoveredJoint.isHovered = false;
            this.linkageSystem.hoveredJoint = null;
        }
        if (this.linkageSystem.hoveredLink) {
            this.linkageSystem.hoveredLink.isHovered = false;
            this.linkageSystem.hoveredLink = null;
        }
    }

    updateStats() {
        if (window.linkageSystem) {
            const nodeCount = window.linkageSystem.joints.length;
            const linkCount = window.linkageSystem.links.length;
            console.log('UI UpdateStats:', nodeCount, 'nodes', linkCount, 'links');

            const nodeCountEl = document.getElementById('joint-count');
            const linkCountEl = document.getElementById('link-count');

            if (nodeCountEl) nodeCountEl.textContent = nodeCount;
            if (linkCountEl) linkCountEl.textContent = linkCount;
        }
    }
}
