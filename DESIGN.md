# Design

Visual system for Voyagent's frontend (Vite 6 + React 19 + Tailwind v4, tokens live in `frontend/src/index.css` `@theme`; there is no tailwind.config). Animation via the `motion` package (`motion/react`) and CSS keyframes.

## Direction — "Midnight & Sand"

A premium travel bureau after dark: matte midnight-blue paper, warm ivory type, a champagne-gold accent used sparingly, precise mono timetables. Dark theme — matte and editorial, explicitly **not** the neon mission-control look (no glow, no glassmorphism, no radar sweeps). Color strategy: **Restrained** — near-monochrome midnight surfaces carry the frame; champagne gold marks primary actions, selection and key graphics; a lightened ink-blue is the secondary role (route lines, links, stream thread).

## Palette (OKLCH only)

| Token | Value | Role |
|---|---|---|
| `--color-bg` | `oklch(0.18 0.025 262)` | body background — matte midnight, never pitch black |
| `--color-surface` | `oklch(0.225 0.028 262)` | panels, cards, sidebars |
| `--color-surface-2` | `oklch(0.27 0.03 262)` | nested/hover surfaces |
| `--color-line` | `oklch(0.33 0.025 262)` | 1px borders — deliberately low-contrast |
| `--color-ink` | `oklch(0.955 0.008 85)` | primary text — warm ivory, not #fff (≥7:1 on bg) |
| `--color-muted` | `oklch(0.72 0.015 262)` | secondary text (≥4.5:1 on bg) |
| `--color-primary` | `oklch(0.85 0.08 85)` | champagne gold — primary buttons and selection, **midnight text on top** (`text-bg`) |
| `--color-primary-bright` | `oklch(0.87 0.09 87)` | gold for graphics: markers, gauge (3:1 floor) |
| `--color-primary-deep` | `oklch(0.78 0.09 82)` | gold pressed/hover |
| `--color-accent` | `oklch(0.72 0.07 255)` | lightened ink-blue — route lines, links, stream thread |
| `--color-ok` | `oklch(0.75 0.12 155)` | success / approved |
| `--color-alert` | `oklch(0.72 0.16 25)` | error / budget conflict / objection |

Day route colors (`DAY_COLORS` in `MapView.tsx`, shared by HUD chips): `#d9a441`, `#7fa3d8`, `#b58fd9`, `#6fbf94`, `#e08099` — light enough to read on the dark map, dark `DAY_INK` (`#141a28`) text on top.

Agent identity colors (light enough for text on midnight, distinct hues):
interest `oklch(0.75 0.11 300)` violet · budget `oklch(0.76 0.11 155)` green · logistics `oklch(0.78 0.09 70)` amber · planner `oklch(0.74 0.07 250)` blue · system `oklch(0.72 0.015 262)` (= muted).

Text on light fills (gold buttons, day chips, active `bg-ink` chips) is midnight via `text-bg`; white text is never used on this theme.

## Typography

- Display: **Bodoni Moda** (opsz, 500–600) — H1 logo, city names, brand moments only; vintage travel-poster didone, large sizes only (≥20px). Never in labels, buttons or data.
- UI/body: **Archivo** 400/500/600 — everything else.
- Data: **IBM Plex Mono** 400/500 — dates, prices, coordinates, timetable rows, log timestamps.
- Fixed rem scale, ratio ~1.2: 12 / 13 / 14 (base) / 17 / 20 / 24 / 34px equivalents. No fluid clamp headings in app UI.

## Surfaces & depth

Solid panels: `bg-surface` + 1px `line` border + soft diffused black shadow (`0 1px 2px oklch(0 0 0 / 0.35), 0 4px 16px / 0.28`). No glassmorphism, no glow shadows, no gradient backgrounds. Map HUD panels use near-opaque midnight (`oklch(0.18 0.025 262 / 0.92)`) so the map reads through the gaps, not through the panel.

## Motion

150–250 ms, `ease-out` (quart-like curves). Motion states: agent thinking (soft dot pulse), objection (border emphasis, no flashing loop), marker landing (geo-drop, ~300 ms), route drawing (dash draw-on while streaming only), typewriter caret on live stream. No radar sweeps, no sonar rings, no orchestrated page-load choreography. Every animation has a `prefers-reduced-motion: reduce` fallback (instant/crossfade); `useReducedMotion` guards JS-driven motion.

## Map

CARTO `dark_all` tiles (dark, cartographic). Markers are `L.divIcon` HTML (react-leaflet v5 renders children only in popups): light day-color pin with midnight numeral and `DAY_INK` border, selected-day pins full-strength, other days faded (`#4a5266` fill, light numeral). Route polyline in the day's color. Leaflet chrome (popups, zoom bar, attribution) overridden to the dark palette in `index.css`.

## Components

Single control vocabulary everywhere: 8px-radius inputs and buttons, visible focus ring (`2px` gold outline, offset 2), complete hover/focus/active/disabled states. Primary action = gold filled with midnight text (`bg-primary text-bg`); secondary = `bg` with `line` border; destructive/objection = alert. Active chips/tabs = `bg-ink text-bg` (ivory fill, midnight text). Status pills: agent color dot + mono label. Empty states explain the interface; loading uses skeletons or the stream itself, not spinners over content.

## Print

`@media print` keeps the screen tree hidden (`.app-screen`) and shows `PrintableItinerary` (`.print-only`) in plain black-on-white with attribution footer. Unchanged by theme work.
