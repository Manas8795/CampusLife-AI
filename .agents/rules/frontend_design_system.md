# Frontend Design System & Taste Guidelines

## 1. Core Animation & 3D Stack
- **GSAP (GreenSock Animation Platform)**: Standard animation engine for all pages. Use GSAP for:
  - Staggered entrance animations on page load (`gsap.from(...)`, `gsap.timeline(...)`)
  - Smooth micro-interactions on hover/active states
  - Fluid view transitions and modal reveals
- **Three.js**: Standard 3D engine for interactive visual elements:
  - Interactive WebGL backgrounds (particles, abstract geometries, subtle mouse-following lighting)
  - Zero lag, 60fps lightweight shaders and canvas renderers with graceful fallbacks.

## 2. Component Design References (VibeUI & 21st.dev)
- **Palette**: Curated deep dark aesthetic:
  - Deep space midnight backgrounds (`#050811`, `#070a13`)
  - Glassmorphic panels (`rgba(15, 23, 42, 0.7)` with `backdrop-filter: blur(...)`)
  - Glowing accents in Cyan (`#06b6d4`), Indigo/Violet (`#6366f1`, `#8b5cf6`), and Emerald (`#10b981`)
  - Subtle borders (`rgba(255, 255, 255, 0.08)`) with glowing hover states
- **Component Blueprint**:
  - Pill badges with glowing indicator dots
  - Dual-action button groups (Primary high-contrast gradient + Secondary glass)
  - High-precision typography using Google Fonts `Outfit` (Headings) and `Plus Jakarta Sans` (Body)
  - Minimalist, high-clarity layout grids with generous breathing room

## 3. Taste Skill Guidelines (Anti-Slop Principles)
- **No Data Clutter on Landing**: The root dashboard (`/`) is an elegant, high-impact introductory landing showcase, not an information-dump dashboard.
- **Left Vertical Navigation**: Navigation lives in a clean, vertical left sidebar, keeping top real estate uncluttered.
- **Zero Jargon**: Never use academic syllabus terminology like "Module 1", "Module 2", etc. on user-facing surfaces. Use clear, human terms: Academics, Wellness, Finances, Trips, Voice Co-Pilot, Phone Screen.
- **Responsive Layout**: Desktop left sidebar transforms into a sleek mobile bottom/collapsible navigation bar on small viewports.
