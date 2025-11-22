/**
 * Simple code‑structure extractor for the visualizer project.
 * Scans the `linkage-visualizer` folder and builds a nested JSON object:
 *   {
 *     "index.html": {},
 *     "styles.css": {},
 *     "canvas.js": { "Canvas": {} },
 *     "linkage.js": { "Joint": {}, "Link": {}, "LinkageSystem": {} },
 *     "ui.js": { "UIController": {} },
 *     "docPanel.js": { "DocPanel": {} }
 *   }
 *
 * This is a lightweight alternative to full‑blown parsers – it uses
 * regular expressions to find class and function declarations.
 */
const fs = require('fs');
const path = require('path');

const ROOT = path.resolve(__dirname);

function parseFile(filePath) {
    const content = fs.readFileSync(filePath, 'utf8');
    const result = {};
    const classRegex = /class\s+([A-Za-z0-9_]+)\s*/g;
    const funcRegex = /function\s+([A-Za-z0-9_]+)\s*\(/g;
    let match;
    while ((match = classRegex.exec(content)) !== null) {
        result[match[1]] = {};
    }
    while ((match = funcRegex.exec(content)) !== null) {
        result[match[1]] = {};
    }
    return result;
}

function buildManifest(dir) {
    const manifest = {};
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        if (entry.isDirectory()) continue; // flat structure for now
        if (!entry.name.endsWith('.js') && !entry.name.endsWith('.html') && !entry.name.endsWith('.css')) continue;
        const base = entry.name;
        manifest[base] = parseFile(fullPath);
    }
    return manifest;
}

const manifest = buildManifest(ROOT);
fs.writeFileSync(path.join(ROOT, 'doc_manifest.json'), JSON.stringify(manifest, null, 2), 'utf8');
console.log('Documentation manifest generated at doc_manifest.json');
