// mermaidViewer.js - loads and renders Mermaid diagram
document.addEventListener('DOMContentLoaded', () => {
    const container = document.createElement('div');
    container.id = 'mermaid-panel';
    container.className = 'mermaid-panel glass-panel';
    document.body.appendChild(container);

    // Initialize mermaid
    if (window.mermaid) {
        mermaid.initialize({ startOnLoad: false, theme: 'dark' });
    }

    // Try to load from global variable first (avoids CORS on file://)
    if (typeof MERMAID_GRAPH_DATA !== 'undefined') {
        renderMermaid(MERMAID_GRAPH_DATA);
    } else {
        // Fallback to fetch
        fetch('graph.mmd')
            .then(res => res.text())
            .then(data => renderMermaid(data))
            .catch(err => {
                container.innerHTML = '<p class="error">Failed to load Mermaid diagram. (CORS or file not found)</p>';
                console.error(err);
            });
    }

    function renderMermaid(data) {
        container.innerHTML = `<div class="mermaid">${data}</div>`;
        mermaid.contentLoaded();
    }
});
