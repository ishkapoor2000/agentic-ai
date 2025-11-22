// ================================================
// MINDMAP SYSTEM - Force-Directed Graph Physics
// ================================================

class Joint {
    constructor(x, y, isFixed = false) {
        this.x = x;
        this.y = y;
        this.px = x; // Previous position for velocity
        this.py = y;
        this.isFixed = isFixed;
        this.radius = 20; // Dynamic based on type
        this.isSelected = false;
        this.isHovered = false;
        this.id = Math.random().toString(36).substr(2, 9);

        // Node properties
        this.label = '';
        this.type = 'default'; // 'file', 'class', 'function'
        this.mass = 1.0;
        this.velocity = { x: 0, y: 0 };
    }

    update(dt) {
        if (this.isFixed) return;

        // Verlet integration
        const damping = 0.90; // Higher damping for graph stability
        const vx = (this.x - this.px) * damping;
        const vy = (this.y - this.py) * damping;

        this.px = this.x;
        this.py = this.y;

        this.x += vx;
        this.y += vy;

        // Store velocity for other calculations if needed
        this.velocity = { x: vx, y: vy };
    }

    // Drawing is handled by canvas.js now to keep concerns separated
    // but we keep a basic debug draw here just in case
    draw(canvas) {
        // Delegated to canvas.js
    }

    containsPoint(worldX, worldY) {
        const dx = worldX - this.x;
        const dy = worldY - this.y;
        return Math.sqrt(dx * dx + dy * dy) <= this.radius;
    }
}

class Link {
    constructor(joint1, joint2) {
        this.joint1 = joint1;
        this.joint2 = joint2;
        this.length = 150; // Ideal spring length
        this.stiffness = 0.05; // Spring constant (k)
        this.isSelected = false;
        this.isHovered = false;
        this.id = Math.random().toString(36).substr(2, 9);
        this.type = 'dependency'; // 'dependency', 'hierarchy'
    }

    // Spring force application
    applyForce() {
        const dx = this.joint2.x - this.joint1.x;
        const dy = this.joint2.y - this.joint1.y;
        const distance = Math.sqrt(dx * dx + dy * dy);

        if (distance === 0) return;

        // Hooke's Law: F = k * (currentLength - targetLength)
        const force = (distance - this.length) * this.stiffness;

        const fx = (dx / distance) * force;
        const fy = (dy / distance) * force;

        if (!this.joint1.isFixed) {
            this.joint1.x += fx;
            this.joint1.y += fy;
        }

        if (!this.joint2.isFixed) {
            this.joint2.x -= fx;
            this.joint2.y -= fy;
        }
    }

    draw(canvas) {
        // Delegated to canvas.js
    }

    containsPoint(worldX, worldY, threshold = 5) {
        // Distance from point to line segment logic remains same
        const x1 = this.joint1.x, y1 = this.joint1.y;
        const x2 = this.joint2.x, y2 = this.joint2.y;

        const A = worldX - x1;
        const B = worldY - y1;
        const C = x2 - x1;
        const D = y2 - y1;

        const dot = A * C + B * D;
        const lenSq = C * C + D * D;
        let param = -1;

        if (lenSq !== 0) param = dot / lenSq;

        let xx, yy;

        if (param < 0) {
            xx = x1;
            yy = y1;
        } else if (param > 1) {
            xx = x2;
            yy = y2;
        } else {
            xx = x1 + param * C;
            yy = y1 + param * D;
        }

        const dx = worldX - xx;
        const dy = worldY - yy;
        return Math.sqrt(dx * dx + dy * dy) <= threshold;
    }
}

class LinkageSystem {
    constructor() {
        this.joints = [];
        this.links = [];
        this.isRunning = true; // Always running for graph layout
        this.simulationSpeed = 1.0;

        // Physics parameters
        this.repulsionStrength = 2000;
        this.repulsionRange = 300;

        this.selectedJoint = null;
        this.selectedLink = null;
        this.hoveredJoint = null;
        this.hoveredLink = null;
        this.draggedJoint = null;
    }

    addJoint(x, y, isFixed = false) {
        const joint = new Joint(x, y, isFixed);
        this.joints.push(joint);
        return joint;
    }

    addLink(joint1, joint2) {
        const exists = this.links.some(link =>
            (link.joint1 === joint1 && link.joint2 === joint2) ||
            (link.joint1 === joint2 && link.joint2 === joint1)
        );
        if (exists || joint1 === joint2) return null;

        const link = new Link(joint1, joint2);
        this.links.push(link);
        return link;
    }

    clear() {
        this.joints = [];
        this.links = [];
        this.selectedJoint = null;
        this.selectedLink = null;
    }

    update() {
        if (!this.isRunning) return;

        const dt = 0.016 * this.simulationSpeed; // Fixed time step approx 60fps

        // 1. Apply Repulsion (Coulomb-like force)
        for (let i = 0; i < this.joints.length; i++) {
            const nodeA = this.joints[i];
            for (let j = i + 1; j < this.joints.length; j++) {
                const nodeB = this.joints[j];

                const dx = nodeB.x - nodeA.x;
                const dy = nodeB.y - nodeA.y;
                const distSq = dx * dx + dy * dy;

                if (distSq > 0 && distSq < this.repulsionRange * this.repulsionRange) {
                    const dist = Math.sqrt(distSq);
                    const force = this.repulsionStrength / (distSq + 0.1); // Avoid division by zero

                    const fx = (dx / dist) * force;
                    const fy = (dy / dist) * force;

                    if (!nodeA.isFixed) {
                        nodeA.x -= fx;
                        nodeA.y -= fy;
                    }
                    if (!nodeB.isFixed) {
                        nodeB.x += fx;
                        nodeB.y += fy;
                    }
                }
            }
        }

        // 2. Apply Attraction (Springs)
        this.links.forEach(link => link.applyForce());

        // 3. Integrate positions
        this.joints.forEach(joint => joint.update(dt));

        // 4. Center drift correction (optional, keeps graph near origin)
        // This prevents the whole graph from floating away
        if (this.joints.length > 0) {
            let cx = 0, cy = 0;
            let count = 0;
            this.joints.forEach(j => {
                if (!j.isFixed) {
                    cx += j.x;
                    cy += j.y;
                    count++;
                }
            });
            if (count > 0) {
                cx /= count;
                cy /= count;
                const driftFactor = 0.01;
                this.joints.forEach(j => {
                    if (!j.isFixed) {
                        j.x -= cx * driftFactor;
                        j.y -= cy * driftFactor;
                    }
                });
            }
        }
    }

    render(canvas) {
        // Draw links
        this.links.forEach(link => {
            // We need to call canvas.drawLink(link) if we move drawing logic there
            // For now, we assume canvas.js will iterate and draw, or we call a method on canvas
            // But the previous architecture called joint.draw(canvas)
            // Let's keep the pattern but delegate the actual drawing implementation to canvas.js
            // Wait, canvas.js is the *Canvas* class, it doesn't have drawLink/drawJoint methods usually
            // The previous code had draw() methods on the classes themselves.
            // I will update canvas.js to handle the drawing logic to separate concerns as planned.
            // So here we do nothing or we can call a static renderer.
            // Actually, the app.js calls system.render(canvas).
            // So I should iterate here and call canvas.drawLink(link) etc.

            if (canvas.drawLink) canvas.drawLink(link);
        });

        // Draw joints
        this.joints.forEach(joint => {
            if (canvas.drawJoint) canvas.drawJoint(joint);
        });
    }

    // Hit testing methods remain same
    getJointAt(worldX, worldY) {
        for (let i = this.joints.length - 1; i >= 0; i--) {
            if (this.joints[i].containsPoint(worldX, worldY)) return this.joints[i];
        }
        return null;
    }

    getLinkAt(worldX, worldY) {
        for (let i = this.links.length - 1; i >= 0; i--) {
            if (this.links[i].containsPoint(worldX, worldY)) return this.links[i];
        }
        return null;
    }
}
