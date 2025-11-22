/**
 * Documentation Panel Module
 * Renders a collapsible tree view of the project's code structure.
 * Expects a JSON manifest at `/doc_manifest.json`.
 */
class DocPanel {
    constructor(containerId = 'doc-panel') {
        this.container = document.getElementById(containerId);
        if (!this.container) {
            this.container = document.createElement('div');
            this.container.id = containerId;
            this.container.className = 'doc-panel';
            document.body.appendChild(this.container);
        }
        this.loadManifest();
    }

    async loadManifest() {
        try {
            const res = await fetch('doc_manifest.json');
            if (!res.ok) throw new Error('Failed to load manifest');
            const data = await res.json();
            this.renderTree(data);
        } catch (e) {
            console.error('DocPanel error:', e);
            this.container.innerHTML = `<p class="error">❌ Unable to load documentation.</p>`;
        }
    }

    renderTree(node, parent = this.container) {
        const ul = document.createElement('ul');
        ul.className = 'doc-tree';
        parent.appendChild(ul);
        for (const key of Object.keys(node)) {
            const li = document.createElement('li');
            li.className = 'doc-node';
            const item = node[key];
            const hasChildren = typeof item === 'object' && item !== null && Object.keys(item).length > 0;
            const label = document.createElement('span');
            label.textContent = key;
            label.className = 'doc-label';
            li.appendChild(label);
            if (hasChildren) {
                label.classList.add('collapsible');
                label.addEventListener('click', () => {
                    li.classList.toggle('expanded');
                });
                this.renderTree(item, li);
            }
            ul.appendChild(li);
        }
    }
}

// Initialize when DOM is ready
window.addEventListener('DOMContentLoaded', () => {
    new DocPanel();
});
