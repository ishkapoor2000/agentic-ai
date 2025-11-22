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
        if (welcomeMessage) {
            welcomeMessage.innerHTML = `
                <h2>Codebase Mindmap</h2>
                <p>Explore your project structure interactively.</p>
                <ul>
                    <li>🖱️ <strong>Drag</strong> nodes to rearrange</li>
                    <li>📜 <strong>Scroll</strong> to zoom</li>
                    <li>␣ <strong>Space</strong> to pan</li>
                </ul>
                <button id="close-welcome" class="primary-btn">Start Exploring</button>
            `;

            const closeBtn = document.getElementById('close-welcome');
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    welcomeMessage.classList.add('hidden');
                });
            }
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
            // TODO: Show details in side panel
        } else {
            const link = this.linkageSystem.getLinkAt(worldX, worldY);
            if (link) {
                link.isSelected = true;
                this.linkageSystem.selectedLink = link;
            }
        }

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
