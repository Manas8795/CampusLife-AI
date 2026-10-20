---
name: threejs
description: >-
  Expert guidelines and implementation patterns for Three.js 3D interactive graphics,
  scene graphs, responsive WebGL rendering, lighting, materials, physics-inspired micro-animations,
  and high-performance canvas integrations.
---

# Three.js 3D WebGL Implementation Guidelines

Use this skill when building or upgrading 3D visual components, hero scenes, canvas visualizers, or background animations using Three.js in CampusLife AI.

## Core Architecture Principles
1. **Responsive Viewport Management**:
   - Always listen for window `resize` and parent container bounding box changes.
   - Update `camera.aspect = width / height` and call `camera.updateProjectionMatrix()`.
   - Call `renderer.setSize(width, height)` and clamp `renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))` to prevent mobile/4K GPU throttling.

2. **Clean Scene Lifecycle**:
   - Store references to `scene`, `camera`, `renderer`, and `animationFrameId`.
   - Implement clean disposal methods: traverse scene objects, dispose geometries, materials, textures, and cancel `requestAnimationFrame` on page unload.

3. **Lighting & Material Best Practices**:
   - Use a balanced setup: ambient lighting for base visibility (`AmbientLight(0xffffff, 0.6)`) plus dual directional/point lights for depth and specular highlights.
   - For light themes (like Alabaster), use soft specular highlights and clean pastel emissive tints.
   - For dark themes (like Midnight Obsidian), leverage glowing neon accents (`MeshStandardMaterial` with emissive colors and subtle bloom-compatible shaders).

4. **Performance & Anti-Lag**:
   - Target 60fps locked animations.
   - Use shared geometry and material buffers where possible.
   - Utilize lightweight particle systems (`THREE.Points` with `BufferGeometry`) instead of thousands of individual meshes.
   - Enable pointer/mouse raycasting throttle for interactive hover effects.
