# Voyagent — AI Multi-Agent Travel Planner

A multi-agent AI system that builds an optimal travel itinerary from your budget, dates, interests and group size. Four agents (Interest, Budget, Logistics, Planner) "talk" to each other to resolve conflicts and shape the final route — the whole negotiation is streamed **live** to the user (SSE), and the route is visualised on a map.

## How it works

1. **Interest Agent** proposes real places/activities matching your interests (LLM)
2. **Budget Agent** calculates the total cost; objects to items that break the budget
3. **Logistics Agent** checks that each day fits a realistic schedule, using OpenStreetMap coordinates
4. When there is an objection, the Interest Agent proposes alternatives (max 2 negotiation rounds)
5. **Planner Agent** turns the approved plan into a timed daily schedule

Cost and distance checks run in code — the LLM is only called for generating proposals and short "talk" messages (token cost is kept to a minimum).

## Stack

- **Backend:** FastAPI (Python 3.12), SQLAlchemy async, SSE streaming
- **DB:** PostgreSQL 16
- **LLM:** OpenAI `gpt-4o-mini` (primary) + OpenRouter free models (automatic fallback)
- **Frontend:** React 19 + Vite + Tailwind CSS 4, Leaflet (CARTO Voyager tiles), EN/AZ language switch
- **Geocoding:** Nominatim (OpenStreetMap) — free, no API key
- **Docker:** 3 services via docker-compose (db, backend, frontend)

## Setup

```bash
git clone https://github.com/Khayal07/Voyagent-.git
cd Voyagent-
cp .env.example .env
# fill in OPENAI_API_KEY and OPENROUTER_API_KEY in .env
docker compose up --build
```

Then open: **http://localhost:8000**

Backend API docs: http://localhost:8001/docs

### .env parameters

| Variable | Description |
|---|---|
| `OPENAI_API_KEY` | Primary provider key |
| `OPENROUTER_API_KEY` | Fallback provider key |
| `PRIMARY_PROVIDER` | `openai` (default) or `openrouter` |
| `OPENAI_MODEL` | Default: `gpt-4o-mini` |
| `OPENROUTER_MODEL` | Default: `openrouter/free` |
| `GEOAPIFY_API_KEY` | Optional. Real POI candidates from [Geoapify Places](https://www.geoapify.com/) (free tier: 3,000 credits/day). If empty, the system falls back to LLM knowledge + Nominatim geocoding. |
| `JWT_SECRET` | Secret for signing auth tokens. **Override the default with a long random string.** |

> **Note (schema changes):** the project uses `Base.metadata.create_all` (no migration tool). After pulling a version that changes the DB schema (e.g. the auth update), reset the volume once: `docker compose down -v && docker compose up --build`.

If the OpenAI call fails (rate limit, key error, timeout), the system automatically switches to OpenRouter — the switch is logged transparently both in the backend log and in the agent chat in the UI.

## Demo

1. Pick a city (e.g. "Rome"), a date range (max 5 days), budget, group size and interests
2. Press **"Plan my route"**
3. Watch the agents negotiate live in the right panel — proposals, objections (`OBJECTION`), approvals (`APPROVED`) and the final decision
4. Each day's route is drawn on the map in its own colour; click the day tabs to focus
5. Switch the interface language (EN/AZ) in the header — agents reply in the selected language

## API

- `POST /api/trips` — create a new trip request (planning starts in the background)
- `GET /api/trips/{id}/stream` — SSE: agent messages in real time
- `GET /api/trips/{id}` — trip + all messages + final itinerary
- `GET /health`, `GET /debug/llm` — service checks

## Project structure

```
backend/app/
├── agents/          # interest, budget, logistics, planner
├── llm/             # call_llm() + fallback, prompts and message templates
├── services/        # Nominatim geocoding (cache + rate limit)
├── routers/         # trip API + SSE
└── orchestrator.py  # negotiation loop
frontend/src/
├── components/      # TripForm, AgentChat, MapView, ItineraryPanel
├── i18n.ts          # EN/AZ translations
└── api.ts           # fetch + EventSource
```

## License

Educational project (Div Academy AI Engineering capstone).
