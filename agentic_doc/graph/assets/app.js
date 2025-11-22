// ================================================
// MAIN APPLICATION - Initialize and orchestrate
// ================================================

// Global state
window.currentTool = 'select';
window.previousTool = 'select';

// Application initialization
document.addEventListener('DOMContentLoaded', () => {
    // Initialize systems
    const canvas = new InfiniteCanvas('main-canvas');
    const linkageSystem = new LinkageSystem();
    const ui = new UIController(canvas, linkageSystem);

    // Make globally accessible
    window.canvas = canvas;
    window.linkageSystem = linkageSystem;
    window.ui = ui;

    // Initial render
    canvas.render();

    // Start animation loop for smooth rendering
    function animate() {
        if (linkageSystem.isRunning) {
            linkageSystem.update();
        }
        requestAnimationFrame(animate);
    }
    animate();

    console.log('🔗 Linkage Visualizer initialized!');
    console.log('Tools: Select (V), Fixed Point (F), Joint (J), Link (L), Motor (M), Delete');
    console.log('Controls: Space to pan, Scroll to zoom, Home to reset view');
});
