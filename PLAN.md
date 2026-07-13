# Voyagent — AI Multi-Agent Səyahət Planlaşdırıcı: İmplementasiya Planı

## Context

Div Academy AI Engineering capstone layihəsi. İstifadəçi büdcə, tarixlər, maraqlar və nəfər sayını daxil edir; 4 AI agent (Interest, Budget, Logistics, Planner) öz aralarında "danışaraq" optimal gündəlik marşrut qurur. Əsas fərqləndirici xüsusiyyət — agentlərin negotiation prosesi istifadəçiyə **canlı** göstərilir (SSE stream + xəritə vizualizasiyası). Repo hazırda boşdur (yalnız README), hər şey sıfırdan qurulur.

**İstifadəçinin seçdiyi texnologiyalar:**
- Frontend: **React + Vite + Tailwind CSS** (SPA)
- Xəritə: **Leaflet + CARTO Voyager tiles + Nominatim geocoding** (tam pulsuz, API açarsız)
- Streaming: **SSE** (Server-Sent Events)
- MVP həcmi: **1 şəhər, 1–5 günlük marşrut**
- Backend: FastAPI (Python), DB: PostgreSQL, tam Docker containerize
- LLM: OpenAI `gpt-4o-mini` əsas, OpenRouter pulsuz modellər avtomatik fallback

**İstifadəçinin sərt qaydaları:**
- Hər mərhələdən sonra avtomatik `git commit + push` (GitHub repo: origin/main)
- Commit mesajlarında **heç bir Claude/AI həmmüəllif qeydi OLMASIN** (Co-Authored-By yazma!)
- Token istifadəsi minimum: qısa promptlar, `max_tokens` limiti, lazımsız çağırış yox
- Hər mərhələdən sonra istifadəçiyə qısa xülasə

---

## Repo strukturu

```
Voyagent/
├── docker-compose.yml          # backend + db + frontend
├── .env.example                # API açarları, provider seçimi
├── PLAN.md                     # bu plan (repoya kopyalanır)
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── app/
│   │   ├── main.py             # FastAPI app, CORS, router qeydiyyatı
│   │   ├── config.py           # pydantic-settings (.env oxuyur)
│   │   ├── db.py               # SQLAlchemy async engine + session
│   │   ├── models.py           # ORM modelləri
│   │   ├── schemas.py          # Pydantic request/response sxemləri
│   │   ├── routers/
│   │   │   ├── trips.py        # POST /api/trips, GET /api/trips/{id}, GET stream
│   │   ├── llm/
│   │   │   ├── client.py       # call_llm() — OpenAI əsas + OpenRouter fallback
│   │   │   └── prompts.py      # bütün agent promptları bir yerdə (qısa!)
│   │   ├── agents/
│   │   │   ├── base.py         # ortaq agent run() helper (LLM çağırış + JSON parse)
│   │   │   ├── interest.py
│   │   │   ├── budget.py
│   │   │   ├── logistics.py
│   │   │   └── planner.py
│   │   ├── orchestrator.py     # negotiation dövrəsi, event emit, DB yazma
│   │   └── services/
│   │       └── geocode.py      # Nominatim client (cache ilə)
└── frontend/
    ├── Dockerfile              # nginx ilə build serve
    ├── package.json            # React + Vite + Tailwind + Leaflet (react-leaflet)
    └── src/
        ├── App.tsx
        ├── api.ts              # fetch + EventSource wrapper
        ├── components/
        │   ├── TripForm.tsx        # şəhər, tarixlər, büdcə, maraqlar, nəfər sayı
        │   ├── AgentChat.tsx       # yan panel — canlı negotiation axını
        │   ├── AgentMessage.tsx    # agent avatarı + rəng + mesaj balonu
        │   ├── MapView.tsx         # Leaflet xəritə, günlük marşrut xətləri
        │   └── ItineraryPanel.tsx  # son gündəlik plan (günə görə tab-lar)
        └── types.ts
```

## Data modeli (PostgreSQL)

- **trips**: `id (uuid)`, `city`, `start_date`, `end_date`, `budget`, `currency`, `travelers`, `interests (jsonb)`, `status (pending|planning|done|failed)`, `created_at`
- **agent_messages**: `id`, `trip_id (fk)`, `agent (interest|budget|logistics|planner|system)`, `round (int)`, `role (proposal|objection|revision|approval|final)`, `content (text — istifadəçiyə göstərilən qısa mesaj)`, `payload (jsonb — struktur data)`, `created_at`
- **itineraries**: `id`, `trip_id (fk)`, `days (jsonb)` — hər gün: `[{day, date, items: [{name, lat, lon, category, est_cost, start_time, duration_min, note}]}]`, `total_cost`

Sadəlik üçün migration aləti yox — startup-da `Base.metadata.create_all` (MVP üçün kifayətdir).

## API endpoint-lər

- `POST /api/trips` — trip yaradır, arxa planda orchestrator başladır (`asyncio.create_task`), `{trip_id}` qaytarır
- `GET /api/trips/{id}/stream` — **SSE**: agent mesajları real vaxtda axır. Event tipləri: `agent_message`, `status`, `itinerary`, `done`, `error`. Orchestrator → `asyncio.Queue` → SSE generator
- `GET /api/trips/{id}` — trip + bütün mesajlar + itinerary (səhifə yenilənəndə bərpa üçün)

## Agent axını (orchestrator)

```
1. Interest Agent  → hər gün üçün 3-4 aktivlik namizədi (JSON: ad, kateqoriya, təxmini qiymət, təxmini müddət)
2. Budget Agent    → ümumi xərci hesablayır; büdcəni aşırsa konkret item-lara etiraz + ucuz alternativ istəyi
3. Logistics Agent → Nominatim ilə geocode edilmiş koordinatlara əsasən günlük məsafələri yoxlayır
                     (haversine + ~4km/saat gəzinti / 25km/saat nəqliyyat evristikası);
                     sığmayan günlərə etiraz
4. Etiraz varsa    → Interest Agent yalnız etiraz olunan item-ları yenidən təklif edir (revision)
                     → Budget/Logistics yenidən yoxlayır. MAX 2 RAUND — sonra Planner mövcud ən yaxşı
                     variantla davam edir (sonsuz dövrə qarşı qoruma)
5. Planner Agent   → təsdiqlənmiş item-lardan son gündəlik cədvəl (vaxtlar, ardıcıllıq) formalaşdırır
6. Hər addım: agent_messages-ə INSERT + SSE queue-ya push (istifadəçi canlı görür)
```

**Token qənaəti taktikaları:**
- Budget və Logistics yoxlamaları mümkün qədər **kodda** (hesablama), LLM yalnız qısa "danışıq" mesajı üçün (`max_tokens=150`)
- Interest/Planner: structured JSON output, `max_tokens=800–1200`, `temperature=0.7`
- Revision raundunda tam kontekst yox, yalnız etiraz olunan item-lar göndərilir
- Nominatim nəticələri in-memory dict-də cache (eyni yer 2 dəfə geocode olunmur); rate limit üçün sorğular arası 1s

## LLM layer — `call_llm()`

`backend/app/llm/client.py`:
- Vahid interfeys: `await call_llm(messages, max_tokens, json_mode=True) -> (content, provider_used)`
- Əvvəl **OpenAI** (`gpt-4o-mini`); istənilən xəta (429, 5xx, auth, timeout) → **OpenRouter** fallback (`.env`-də `OPENROUTER_MODEL`, default: `meta-llama/llama-3.3-70b-instruct:free`)
- Hər ikisi OpenAI-compatible API — tək `httpx` client, yalnız base_url + açar dəyişir
- Fallback baş verəndə: `logger.warning` + SSE-yə `system` mesajı ("Budget Agent → OpenRouter (səbəb: rate limit)") — şəffaflıq tələbi
- `.env`: `OPENAI_API_KEY`, `OPENROUTER_API_KEY`, `PRIMARY_PROVIDER=openai`, `OPENROUTER_MODEL`

## Frontend dizayn

- **Layout**: sol tərəf — xəritə (Leaflet, CARTO Voyager tiles) + altda itinerary panel; sağ tərəf — agent chat paneli (sticky, scroll)
- **AgentChat**: hər agentin öz rəngi/ikonu (Interest 🎯 bənövşəyi, Budget 💰 yaşıl, Logistics 🚗 narıncı, Planner 📋 mavi); mesajlar EventSource ilə real vaxtda əlavə olunur, typing-indicator effekti; etiraz mesajları vizual fərqlənir (qırmızı haşiyə)
- **MapView**: hər günün marşrutu ayrı rəngli polyline + nömrələnmiş markerlər; gün tabı seçiləndə xəritə həmin günə fokuslanır
- **TripForm**: şəhər (text), tarix aralığı (date input, max 5 gün), büdcə + valyuta, maraqlar (çip-lərlə multi-select: tarix, təbiət, yemək, gecə həyatı, incəsənət, alış-veriş), nəfər sayı
- Vizual keyfiyyət üçün `frontend-design:frontend-design` skill-i UI mərhələsində istifadə olunacaq

## Docker

`docker-compose.yml` — 3 servis:
- `db`: `postgres:16-alpine`, volume, healthcheck
- `backend`: build `./backend`, `depends_on: db (healthy)`, port 8000, `.env` mount
- `frontend`: build `./frontend` (multi-stage: node build → nginx), port 3000, nginx `/api` → backend proxy (SSE üçün `proxy_buffering off`)

## Mərhələlər (hər biri ayrıca commit + push, AI qeydi OLMADAN)

1. **Skeleton + Docker** — repo strukturu, docker-compose, FastAPI healthcheck, DB qoşulması, `.env.example`, PLAN.md repoya. Commit: `Add project skeleton with Docker, FastAPI and PostgreSQL setup`
2. **LLM layer** — `call_llm()` OpenAI + OpenRouter fallback, loglama, sadə test endpoint. Commit: `Add LLM client with OpenAI primary and OpenRouter fallback`
3. **Data modeli + API** — modellər, sxemlər, `POST /api/trips`, `GET /api/trips/{id}`, SSE endpoint (hələlik dummy event). Commit: `Add trip API endpoints with SSE streaming`
4. **Agentlər + orchestrator** — 4 agent, negotiation dövrəsi, geocode servisi, real SSE axını. Commit: `Add multi-agent negotiation orchestrator`
5. **Frontend əsas** — Vite + React + Tailwind quraşdırma, TripForm, AgentChat (SSE), nginx Docker. Commit: `Add React frontend with live agent chat`
6. **Xəritə + itinerary UI** — MapView, ItineraryPanel, günlük marşrut vizualizasiyası, son cilalama. Commit: `Add map visualization and itinerary panel`
7. **Sənədləşdirmə** — README quraşdırma bölməsi, demo təlimatı. Commit: `Update README with setup instructions`

Hər mərhələnin sonunda istifadəçiyə 2-3 cümləlik xülasə verilir.

## Verification

- Hər mərhələ: `docker compose up --build` işləyir, backend `GET /health` 200 qaytarır
- Mərhələ 4: `curl -N .../api/trips/{id}/stream` ilə real agent mesajlarının axdığını yoxla; OpenAI açarını qəsdən pozaraq OpenRouter fallback-in işlədiyini və loglandığını təsdiqlə
- Mərhələ 5-6: Playwright browser tools ilə UI-ni aç — form doldur, agent chat-in canlı axdığını, xəritədə marşrutun çəkildiyini vizual yoxla (screenshot)
- Son: tam end-to-end axın — form → negotiation (ən azı 1 etiraz raundu görünür) → xəritədə 1-5 günlük marşrut
