# Design

Visual system for Voyagent's frontend (Vite 6 + React 19 + Tailwind v4, tokens live in `frontend/src/index.css` `@theme`; there is no tailwind.config). Animation via the `motion` package (`motion/react`) and CSS keyframes.

## Direction — "Atlas Bureau"

Mid-century airline route map: white paper, ochre sun, ink-blue routes, precise mono timetables. Light theme — chosen for projector demos and itinerary legibility. Color strategy: **Committed** — ochre carries identity (markers, gauge, selection, primary actions); ink-blue is the secondary role (route lines, links, stream thread).

## Palette (OKLCH only)

| Token | Value | Role |
|---|---|---|
| `--color-bg` | `oklch(1 0 0)` | body background — pure white, never tinted |
| `--color-surface` | `oklch(0.965 0.006 260)` | panels, cards, sidebars |
| `--color-surface-2` | `oklch(0.93 0.01 260)` | nested/hover surfaces |
| `--color-line` | `oklch(0.88 0.012 260)` | 1px borders |
| `--color-ink` | `oklch(0.22 0.03 260)` | primary text (≥7:1 on bg) |
| `--color-muted` | `oklch(0.47 0.025 260)` | secondary text (≥4.5:1 on bg) |
| `--color-primary` | `oklch(0.62 0.12 77)` | ochre — primary buttons (white text), markers, gauge, selection |
| `--color-primary-deep` | `oklch(0.5 0.11 72)` | ochre pressed/hover, small ochre text on white |
| `--color-accent` | `oklch(0.38 0.08 260)` | ink-blue — route lines, links, stream thread |
| `--color-ok` | `oklch(0.55 0.13 155)` | success / approved |
| `--color-alert` | `oklch(0.55 0.2 25)` | error / budget conflict / objection |

Agent identity colors (dark enough for text on white, distinct hues):
interest `oklch(0.5 0.14 300)` violet · budget `oklch(0.5 0.13 155)` green · logistics `oklch(0.52 0.12 60)` amber-brown · planner `oklch(0.45 0.09 250)` blue · system `oklch(0.47 0.025 260)` (= muted).

Text on saturated mid-luminance fills (primary buttons, agent pills) is white per Helmholtz-Kohlrausch; dark text only on pale (`L > 0.85`) or neutral fills.

## Typography

- Display: **Bodoni Moda** (opsz, 500–600) — H1 logo, city names, brand moments only; vintage travel-poster didone, large sizes only (≥20px). Never in labels, buttons or data.
- UI/body: **Archivo** 400/500/600 — everything else.
- Data: **IBM Plex Mono** 400/500 — dates, prices, coordinates, timetable rows, log timestamps.
- Fixed rem scale, ratio ~1.2: 12 / 13 / 14 (base) / 17 / 20 / 24 / 34px equivalents. No fluid clamp headings in app UI.

## Surfaces & depth

Solid panels: `bg-surface` + 1px `line` border + small shadow (`0 1px 2px oklch(0.22 0.03 260 / 0.06), 0 4px 12px / 0.04`). No glassmorphism, no glow shadows, no gradient backgrounds. Map HUD panels use near-opaque white (`oklch(1 0 0 / 0.94)`) so the map reads through the gaps, not through the panel.

## Motion

150–250 ms, `ease-out` (quart-like curves). Motion states: agent thinking (soft dot pulse), objection (border emphasis, no flashing loop), marker landing (geo-drop, ~300 ms), route drawing (dash draw-on while streaming only), typewriter caret on live stream. No radar sweeps, no sonar rings, no orchestrated page-load choreography. Every animation has a `prefers-reduced-motion: reduce` fallback (instant/crossfade); `useReducedMotion` guards JS-driven motion.

## Map

CARTO `voyager` tiles (light, cartographic). Markers are `L.divIcon` HTML (react-leaflet v5 renders children only in popups): ochre pin with white numeral, selected-day pins full-strength, other days faded. Route polyline in accent ink-blue. Leaflet chrome (popups, zoom bar, attribution) overridden to the light palette in `index.css`.

## Components

Single control vocabulary everywhere: 8px-radius inputs and buttons, visible focus ring (`2px` accent outline, offset 2), complete hover/focus/active/disabled states. Primary action = ochre filled with white text; secondary = white with `line` border; destructive/objection = alert. Status pills: agent color dot + mono label. Empty states explain the interface; loading uses skeletons or the stream itself, not spinners over content.

## Print

`@media print` keeps the screen tree hidden (`.app-screen`) and shows `PrintableItinerary` (`.print-only`) in plain black-on-white with attribution footer. Unchanged by theme work.
