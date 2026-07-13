# Voyagent — AI Multi-Agent Səyahət Planlaşdırıcı

Büdcə, tarix, maraqlar və iştirakçı sayına əsasən optimal səyahət marşrutu yaradan multi-agent AI sistemi. Dörd agent (Interest, Budget, Logistics, Planner) bir-biri ilə "danışaraq" ziddiyyətləri həll edir və son marşrutu formalaşdırır — bu proses istifadəçiyə **canlı** (SSE) göstərilir, marşrut isə xəritə üzərində vizuallaşdırılır.

## Necə işləyir

1. **Interest Agent** maraqlara uyğun real yerlər/aktivliklər təklif edir (LLM)
2. **Budget Agent** ümumi xərci hesablayır; büdcəni aşan item-lara etiraz edir
3. **Logistics Agent** OpenStreetMap koordinatlarına əsasən günlük marşrutun vaxta sığmasını yoxlayır
4. Etiraz olduqda Interest Agent alternativ təklif edir (maksimum 2 danışıq raundu)
5. **Planner Agent** təsdiqlənmiş plandan vaxtlı gündəlik cədvəl qurur

Xərc/məsafə yoxlamaları kodda aparılır — LLM yalnız təklif generasiyası və qısa "danışıq" mesajları üçün çağırılır (token xərci minimum saxlanılır).

## Stack

- **Backend:** FastAPI (Python 3.12), SQLAlchemy async, SSE streaming
- **DB:** PostgreSQL 16
- **LLM:** OpenAI `gpt-4o-mini` (əsas) + OpenRouter pulsuz modellər (avtomatik fallback)
- **Frontend:** React 19 + Vite + Tailwind CSS 4, Leaflet (CARTO Voyager tiles)
- **Geocoding:** Nominatim (OpenStreetMap) — pulsuz, API açarsız
- **Docker:** docker-compose ilə 3 servis (db, backend, frontend)

## Quraşdırma

```bash
git clone https://github.com/Khayal07/Voyagent-.git
cd Voyagent-
cp .env.example .env
# .env faylında OPENAI_API_KEY və OPENROUTER_API_KEY dəyərlərini doldur
docker compose up --build
```

Sonra brauzerdə: **http://localhost:8000**

Backend API sənədləri: http://localhost:8001/docs

### .env parametrləri

| Dəyişən | Təsvir |
|---|---|
| `OPENAI_API_KEY` | Əsas provider açarı |
| `OPENROUTER_API_KEY` | Fallback provider açarı |
| `PRIMARY_PROVIDER` | `openai` (default) və ya `openrouter` |
| `OPENAI_MODEL` | Default: `gpt-4o-mini` |
| `OPENROUTER_MODEL` | Default: `meta-llama/llama-3.3-70b-instruct:free` |

OpenAI çağırışı uğursuz olarsa (rate limit, açar xətası, timeout) sistem avtomatik OpenRouter-ə keçir — bu keçid həm backend logunda, həm də UI-dakı agent danışığında şəffaf göstərilir.

## Demo

1. Şəhər (məs. "Roma"), tarix aralığı (maks. 5 gün), büdcə, nəfər sayı və maraqları seç
2. **"Marşrutu planla"** düyməsinə bas
3. Sağ paneldə agentlərin canlı danışığını izlə — təkliflər, etirazlar (`ETİRAZ`), təsdiqlər (`TƏSDİQ`) və yekun qərar
4. Xəritədə hər günün marşrutu ayrı rəngli xətlə çəkilir; gün tab-larına klik etməklə fokusla

## API

- `POST /api/trips` — yeni səyahət sorğusu (planlaşdırma arxa planda başlayır)
- `GET /api/trips/{id}/stream` — SSE: agent mesajları real vaxtda
- `GET /api/trips/{id}` — trip + bütün mesajlar + yekun marşrut
- `GET /health`, `GET /debug/llm` — servis yoxlamaları

## Layihə strukturu

```
backend/app/
├── agents/          # interest, budget, logistics, planner
├── llm/             # call_llm() + fallback, promptlar
├── services/        # Nominatim geocoding (cache + rate limit)
├── routers/         # trip API + SSE
└── orchestrator.py  # negotiation dövrəsi
frontend/src/
├── components/      # TripForm, AgentChat, MapView, ItineraryPanel
└── api.ts           # fetch + EventSource
```

## Lisenziya

Təhsil məqsədli layihə (Div Academy AI Engineering capstone).
