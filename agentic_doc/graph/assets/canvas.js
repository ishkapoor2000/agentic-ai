// ================================================
// CANVAS SYSTEM - Infinite pan/zoom canvas
// ================================================

class InfiniteCanvas {
    constructor(canvasId) {
        this.canvas = document.getElementById(canvasId);
        this.ctx = this.canvas.getContext('2d');

        // Camera/viewport state
        this.camera = {
            x: 0,
            y: 0,
            zoom: 1
        };

        // Panning state
        this.isPanning = false;
        this.panStart = { x: 0, y: 0 };
        this.lastPanPosition = { x: 0, y: 0 };

        // Grid settings
        this.gridSize = 50;
        this.gridMajorEvery = 5;

        // Initialize
        this.setupCanvas();
        this.setupEventListeners();

        // Animation
        this.animationFrameId = null;
        this.isAnimating = false;
    }

    setupCanvas() {
        // Set canvas to window size with device pixel ratio
        const dpr = window.devicePixelRatio || 1;
        const rect = this.canvas.getBoundingClientRect();

        this.canvas.width = rect.width * dpr;
        this.canvas.height = rect.height * dpr;

        this.ctx.scale(dpr, dpr);

        this.width = rect.width;
        this.height = rect.height;
    }

    setupEventListeners() {
        // Resize handling
        window.addEventListener('resize', () => {
            this.setupCanvas();
            this.render();
        });

        // Pan with mouse
        this.canvas.addEventListener('mousedown', (e) => {
            if (e.button === 1 || e.button === 0 && e.shiftKey || e.button === 0 && window.currentTool === 'pan') {
                this.startPan(e.clientX, e.clientY);
                e.preventDefault();
            }
        });

        this.canvas.addEventListener('mousemove', (e) => {
            if (this.isPanning) {
                this.updatePan(e.clientX, e.clientY);
            }
        });

        this.canvas.addEventListener('mouseup', () => {
            this.endPan();
        });

        this.canvas.addEventListener('mouseleave', () => {
            this.endPan();
        });

        // Zoom with mouse wheel
        this.canvas.addEventListener('wheel', (e) => {
            e.preventDefault();

            const zoomFactor = e.deltaY > 0 ? 0.9 : 1.1;
            const mouseX = e.clientX;
            const mouseY = e.clientY;

            // Zoom towards mouse position
            const worldPosBefore = this.screenToWorld(mouseX, mouseY);
            this.camera.zoom *= zoomFactor;
            this.camera.zoom = Math.max(0.1, Math.min(5, this.camera.zoom));
            const worldPosAfter = this.screenToWorld(mouseX, mouseY);

            this.camera.x += (worldPosBefore.x - worldPosAfter.x);
            this.camera.y += (worldPosBefore.y - worldPosAfter.y);

            this.render();
        }, { passive: false });

        // Keyboard controls
        window.addEventListener('keydown', (e) => {
            if (e.code === 'Space' && !e.repeat) {
                window.currentTool = 'pan';
                this.canvas.style.cursor = 'grab';
                e.preventDefault();
            }
            if (e.code === 'Home') {
                this.resetView();
                e.preventDefault();
            }
        });

        window.addEventListener('keyup', (e) => {
            if (e.code === 'Space') {
                window.currentTool = window.previousTool || 'select';
                this.canvas.style.cursor = 'default';
            }
        });
    }

    startPan(x, y) {
        this.isPanning = true;
        this.panStart = { x, y };
        this.lastPanPosition = { x: this.camera.x, y: this.camera.y };
        this.canvas.parentElement.classList.add('panning');
    }

    updatePan(x, y) {
        if (!this.isPanning) return;

        const dx = (x - this.panStart.x) / this.camera.zoom;
        const dy = (y - this.panStart.y) / this.camera.zoom;

        this.camera.x = this.lastPanPosition.x - dx;
        this.camera.y = this.lastPanPosition.y - dy;

        this.render();
    }

    endPan() {
        this.isPanning = false;
        this.canvas.parentElement.classList.remove('panning');
    }

    resetView() {
        this.camera = { x: 0, y: 0, zoom: 1 };
        this.render();
    }

    // Coordinate transformations
    screenToWorld(screenX, screenY) {
        return {
            x: (screenX - this.width / 2) / this.camera.zoom + this.camera.x,
            y: (screenY - this.height / 2) / this.camera.zoom + this.camera.y
        };
    }

    worldToScreen(worldX, worldY) {
        return {
            x: (worldX - this.camera.x) * this.camera.zoom + this.width / 2,
            y: (worldY - this.camera.y) * this.camera.zoom + this.height / 2
        };
    }

    // Clear canvas
    clear() {
        this.ctx.clearRect(0, 0, this.width, this.height);
    }

    // Draw grid
    drawGrid() {
        const ctx = this.ctx;

        // Calculate visible world bounds
        const topLeft = this.screenToWorld(0, 0);
        const bottomRight = this.screenToWorld(this.width, this.height);

        // Calculate grid bounds
        const gridSize = this.gridSize;
        const startX = Math.floor(topLeft.x / gridSize) * gridSize;
        const startY = Math.floor(topLeft.y / gridSize) * gridSize;
        const endX = Math.ceil(bottomRight.x / gridSize) * gridSize;
        const endY = Math.ceil(bottomRight.y / gridSize) * gridSize;

        ctx.save();
        ctx.lineWidth = 1 / this.camera.zoom;

        // Draw vertical lines
        for (let x = startX; x <= endX; x += gridSize) {
            const screenPos = this.worldToScreen(x, 0);
            const isMajor = (x / gridSize) % this.gridMajorEvery === 0;

            ctx.strokeStyle = isMajor ?
                'rgba(255, 255, 255, 0.1)' :
                'rgba(255, 255, 255, 0.05)';

            ctx.beginPath();
            ctx.moveTo(screenPos.x, 0);
            ctx.lineTo(screenPos.x, this.height);
            ctx.stroke();
        }

        // Draw horizontal lines
        for (let y = startY; y <= endY; y += gridSize) {
            const screenPos = this.worldToScreen(0, y);
            const isMajor = (y / gridSize) % this.gridMajorEvery === 0;

            ctx.strokeStyle = isMajor ?
                'rgba(255, 255, 255, 0.1)' :
                'rgba(255, 255, 255, 0.05)';

            ctx.beginPath();
            ctx.moveTo(0, screenPos.y);
            ctx.lineTo(this.width, screenPos.y);
            ctx.stroke();
        }

        // Draw origin axes
        const origin = this.worldToScreen(0, 0);
        ctx.strokeStyle = 'rgba(168, 85, 247, 0.3)';
        ctx.lineWidth = 2 / this.camera.zoom;

        ctx.beginPath();
        ctx.moveTo(origin.x, 0);
        ctx.lineTo(origin.x, this.height);
        ctx.stroke();

        ctx.beginPath();
        ctx.moveTo(0, origin.y);
        ctx.lineTo(this.width, origin.y);
        ctx.stroke();

        ctx.restore();
    }

    // ==========================================
    // MINDMAP RENDERING
    // ==========================================

    drawJoint(joint) {
        const ctx = this.ctx;
        const screenPos = this.worldToScreen(joint.x, joint.y);
        const radius = joint.radius * this.camera.zoom;
        const type = joint.type || 'default';

        ctx.save();

        // Glow effect for selected/hovered
        if (joint.isSelected || joint.isHovered) {
            ctx.shadowBlur = 20;
            ctx.shadowColor = '#60a5fa';
        }

        // Draw Node Shape based on type
        ctx.beginPath();

        if (type === 'file') {
            // File: Rectangular Card
            const w = radius * 2.5;
            const h = radius * 1.8;
            ctx.roundRect(screenPos.x - w / 2, screenPos.y - h / 2, w, h, 5 * this.camera.zoom);
            ctx.fillStyle = joint.isSelected ? '#3b82f6' : '#1e3a8a'; // Blue
            ctx.strokeStyle = '#60a5fa';
        } else if (type === 'class') {
            // Class: Circle
            ctx.arc(screenPos.x, screenPos.y, radius, 0, Math.PI * 2);
            ctx.fillStyle = joint.isSelected ? '#f59e0b' : '#78350f'; // Amber
            ctx.strokeStyle = '#fbbf24';
        } else {
            // Function: Small Pill/Dot
            ctx.arc(screenPos.x, screenPos.y, radius, 0, Math.PI * 2);
            ctx.fillStyle = joint.isSelected ? '#10b981' : '#064e3b'; // Emerald
            ctx.strokeStyle = '#34d399';
        }

        ctx.fill();
        ctx.lineWidth = 2 * this.camera.zoom;
        ctx.stroke();

        // Draw Label (LOD: only if zoomed in enough or important)
        if (this.camera.zoom > 0.4 || joint.isSelected || joint.isHovered) {
            ctx.fillStyle = '#e2e8f0';
            ctx.font = `${12 * this.camera.zoom}px Inter, sans-serif`;
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';

            // Background for text readability
            const text = joint.label || joint.id;
            const metrics = ctx.measureText(text);
            const padding = 4 * this.camera.zoom;

            // Draw text background
            ctx.fillStyle = 'rgba(0, 0, 0, 0.6)';
            const textY = screenPos.y + radius + 15 * this.camera.zoom;
            ctx.roundRect(
                screenPos.x - metrics.width / 2 - padding,
                textY - 10 * this.camera.zoom,
                metrics.width + padding * 2,
                20 * this.camera.zoom,
                4 * this.camera.zoom
            );
            ctx.fill();

            // Draw text
            ctx.fillStyle = '#fff';
            ctx.fillText(text, screenPos.x, textY);
        }

        ctx.restore();
    }

    drawLink(link) {
        const ctx = this.ctx;
        const pos1 = this.worldToScreen(link.joint1.x, link.joint1.y);
        const pos2 = this.worldToScreen(link.joint2.x, link.joint2.y);

        ctx.save();

        // Glow effect for selected/hovered
        if (link.isSelected || link.isHovered) {
            ctx.shadowBlur = 15;
            ctx.shadowColor = '#8b5cf6';
        }

        ctx.strokeStyle = link.isSelected ? '#fbbf24' : 'rgba(139, 92, 246, 0.4)';
        ctx.lineWidth = (link.type === 'belongs_to' ? 4 : 2) * this.camera.zoom;
        ctx.lineCap = 'round';

        ctx.beginPath();
        ctx.moveTo(pos1.x, pos1.y);
        ctx.lineTo(pos2.x, pos2.y);
        ctx.stroke();

        // Draw arrow for direction
        const angle = Math.atan2(pos2.y - pos1.y, pos2.x - pos1.x);
        const arrowSize = 8 * this.camera.zoom;
        // Offset arrow to not overlap with node
        const targetRadius = (link.joint2.radius || 20) * this.camera.zoom;
        const arrowX = pos2.x - Math.cos(angle) * targetRadius;
        const arrowY = pos2.y - Math.sin(angle) * targetRadius;

        ctx.beginPath();
        // Fix arrow drawing
        ctx.lineTo(
            arrowX - arrowSize * Math.cos(angle - Math.PI / 6),
            arrowY - arrowSize * Math.sin(angle - Math.PI / 6)
        );
        ctx.lineTo(
            arrowX - arrowSize * Math.cos(angle + Math.PI / 6),
            arrowY - arrowSize * Math.sin(angle + Math.PI / 6)
        );
        ctx.lineTo(arrowX, arrowY);
        ctx.fillStyle = ctx.strokeStyle;
        ctx.fill();

        ctx.restore();
    }

    // Rendering
    render() {
        this.clear();
        this.drawGrid();

        // Trigger custom render event for linkage system
        if (window.linkageSystem) {
            window.linkageSystem.render(this);
        }
    }

    startAnimation() {
        if (this.isAnimating) return;
        this.isAnimating = true;
        this.animate();
    }

    stopAnimation() {
        this.isAnimating = false;
        if (this.animationFrameId) {
            cancelAnimationFrame(this.animationFrameId);
            this.animationFrameId = null;
        }
    }

    animate() {
        if (!this.isAnimating) return;

        this.render();
        this.animationFrameId = requestAnimationFrame(() => this.animate());
    }
}
