---
name: ui-ux
description: >-
  Advanced UI/UX engineering, visual hierarchy, modern design tokens, glassmorphism,
  micro-animations, GSAP motion choreography, responsive layouts, and anti-slop guidelines
  for high-end student web experiences.
---

# UI/UX & Frontend Design System Guidelines

Use this skill when designing, refactoring, or polishing user interfaces, navigation shells, cards, interactive dashboards, forms, and visual components in CampusLife AI.

## 1. Visual Hierarchy & Anti-Slop Principles
- **No Data Clutter on Landing**: Keep the root dashboard (`/`) focused on elegant high-impact analytics, vitality pulse, and 3D scenes rather than dumping raw task rows or student ID cards.
- **Human-Centric Language**: Never use syllabus jargon like "Module 1", "Module 2", etc. Use clear human terms: "To-Do & Study Planner", "Health & Wellness", "Finances", "Travel", "AI Voice Co-Pilot".
- **Generous Spacing & Typography**:
  - Headings: `Outfit`, sans-serif (clean geometric weight 600-700).
  - Body & UI: `Plus Jakarta Sans` or `Inter`, sans-serif (balanced line-height 1.5-1.6).
  - Avoid tight, suffocating paddings; use standard token scales (8px, 12px, 16px, 24px, 32px).

## 2. Multi-Theme Token Architecture
- Support the 5 primary design themes via CSS custom properties (`[data-theme="..."]`):
  1. **Alabaster (Universal Default)**: Clean modern light mode (`#f8fafc` canvas, `#ffffff` surfaces, sapphire `#2563eb` and `#4f46e5` accents).
  2. **Midnight Obsidian**: Ultra-sleek cosmic dark mode (`#070a13` background, `#0f172a` glass cards).
  3. **Cyberpunk Neon**: High-contrast cyberpunk styling (`#050814` canvas, glowing magenta `#ec4899` and cyan `#06b6d4`).
  4. **Emerald Matrix**: Deep cybernetic terminal green (`#04120c` canvas, neon emerald `#10b981`).
  5. **Solar Sunset**: Warm twilight amber/rose palette (`#120c0e` canvas, gold `#f59e0b` and coral `#f43f5e`).

## 3. Motion & Micro-Interactions (GSAP)
- **Entrance Choreography**: Stagger card entries (`gsap.from('.card', { y: 20, opacity: 0, stagger: 0.08, duration: 0.6, ease: 'power2.out' })`).
- **Tactile Feedback**:
  - Subtle scale up (`transform: translateY(-2px) scale(1.005)`) on card hover with dynamic box-shadow glow.
  - Active button press states (`transform: scale(0.98)`).
- **Navigation Shell**: Left vertical collapsible sidebar with smooth transitions, persistent `localStorage` state, and `Ctrl+B` hotkey support.
