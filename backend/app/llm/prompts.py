"""All agent prompts and message templates — kept short to minimise token cost.

Prompts are written in English (better model performance); the user-visible "say"
messages are generated in the trip's language. Static template messages live in
MESSAGES with az/en variants.
"""

LANG_NAMES = {"az": "Azerbaijani", "en": "English"}


def _lang_name(lang: str) -> str:
    return LANG_NAMES.get(lang, "English")


INTEREST_SYSTEM = (
    "You are the Interest Agent in Voyagent: you pick REAL places in a city that can be found on a map. "
    "Reply ONLY with valid JSON, nothing else."
)


def poi_block(pois: dict[str, list[dict]]) -> str:
    """Geoapify namizədlərini kompakt prompt blokuna çevirir (boş dict → boş sətir)."""
    if not pois:
        return ""
    lines = "\n".join(f"{cat}: " + "; ".join(p["name"] for p in items) for cat, items in pois.items() if items)
    return f"Verified real places nearby (PREFER these, use EXACT names):\n{lines}\n" if lines else ""


def interest_propose(
    city: str, num_days: int, interests: list[str], travelers: int, currency: str, lang: str,
    pois_text: str = "", weather_text: str = "",
) -> str:
    ints = ", ".join(interests) if interests else "general"
    return (
        f"City: {city}. Days: {num_days}. Interests: {ints}. Travelers: {travelers}.\n"
        + pois_text + weather_text +
        "Suggest 3-4 activities per day (you decide per day; real places, cluster nearby ones on the same day).\n"
        '"name" must be ONLY the official original name of the place (local language/English, findable on '
        'OpenStreetMap) — no descriptions, translations or extra words. Good: "Fontana di Trevi". '
        'Bad: "Seeing the Trevi fountain".\n'
        f'"say" must be 1-2 sentences in {_lang_name(lang)} explaining what you picked and why.\n'
        'JSON: {"say": "...", "days": [{"day": 1, "items": '
        '[{"name": "...", "category": "history|nature|food|nightlife|art|shopping|other", '
        f'"est_cost": <per person, {currency}>, "duration_min": <int>, "lat": <approx>, "lon": <approx>}}]}}]}}'
    )


def interest_revise(city: str, currency: str, objections: list[dict], lang: str, pois_text: str = "") -> str:
    lines = "\n".join(f'- Day {o["day"]}: "{o["name"]}" — {o["reason"]}' for o in objections)
    return (
        f"City: {city}. Your proposal received these objections:\n{lines}\n"
        + pois_text +
        "For EACH objected place suggest 1 alternative on the SAME day with a similar interest "
        "(matching the request: cheaper or closer).\n"
        '"name" must be ONLY the official original name (local/English), no extra words.\n'
        f'"say" must be 1-2 sentences in {_lang_name(lang)}.\n'
        'JSON: {"say": "...", "replacements": [{"day": 1, "replace": "old place name", '
        '"item": {"name": "...", "category": "...", "est_cost": ' + f"<per person, {currency}>"
        + ', "duration_min": <int>, "lat": <approx>, "lon": <approx>}}]}'
    )


def budget_say_system(lang: str) -> str:
    return (
        f"You are the Budget Agent. Based on the given facts, write a 1-2 sentence objection message in "
        f"{_lang_name(lang)} (professional, with concrete numbers). Return only the message itself."
    )


def logistics_say_system(lang: str) -> str:
    return (
        f"You are the Logistics Agent. Based on the given facts, write a 1-2 sentence objection message in "
        f"{_lang_name(lang)} (point out the distance/time problem concretely). Return only the message itself."
    )


def planner_say_system(lang: str) -> str:
    return (
        f"You are the Planner Agent. Present the final route with a warm, concrete 2-3 sentence summary in "
        f"{_lang_name(lang)}. Return only the message itself."
    )


MESSAGES = {
    "en": {
        "start": "Preparing a {days}-day plan for {city} — 4 agents are starting.",
        "poi_found": "Found {n} verified real places near {city} (Geoapify) — agents will prefer them.",
        "weather": "Weather forecast for {city}: {parts} (Open-Meteo).",
        "day_label": "Day",
        "geocoding": "Locating places on the map (OpenStreetMap)...",
        "budget_ok": "Budget check: total cost ~{total} {cur}, budget {budget} {cur} — within budget, approved.",
        "budget_reason": "too expensive ({cost} {cur} per person) — need an alternative up to ~{target} {cur}",
        "budget_obj_template": "Total cost {total} {cur} exceeds the budget ({budget} {cur}). {items}",
        "logistics_ok": "Logistics check: every day fits a realistic schedule ({parts}). Approved.",
        "logistics_day_part": "day {day}: ~{hours}h",
        "logistics_reason": "day {day} does not fit the schedule (~{hours}h of activities and travel) — need an alternative closer to the other places",
        "max_rounds": "Maximum negotiation rounds reached — continuing with the best available plan.",
        "fallback": "{agent} Agent switched to the OpenRouter fallback model ({model}). Reason: {reason}",
        "stopped": "Planning stopped: {error}",
        "planner_template": "The final route is ready: {days} days, total cost ~{total} {cur}. All days approved for budget and logistics.",
        "say_propose_default": "My proposals are ready.",
        "say_revise_default": "Here are some alternatives.",
    },
    "az": {
        "start": "{city} üçün {days} günlük plan hazırlanır — 4 agent işə başlayır.",
        "poi_found": "{city} yaxınlığında {n} təsdiqlənmiş real yer tapıldı (Geoapify) — agentlər onlara üstünlük verəcək.",
        "weather": "{city} üçün hava proqnozu: {parts} (Open-Meteo).",
        "day_label": "Gün",
        "geocoding": "Yerlərin koordinatları tapılır (OpenStreetMap)...",
        "budget_ok": "Büdcə yoxlanışı: ümumi xərc ~{total} {cur}, büdcə {budget} {cur} — uyğundur, təsdiqləyirəm.",
        "budget_reason": "bahalıdır ({cost} {cur} adambaşı) — ~{target} {cur}-dək alternativ lazımdır",
        "budget_obj_template": "Ümumi xərc {total} {cur} büdcəni ({budget} {cur}) aşır. {items}",
        "logistics_ok": "Logistika yoxlanışı: bütün günlər real vaxta sığır ({parts}). Təsdiqləyirəm.",
        "logistics_day_part": "gün {day}: ~{hours} saat",
        "logistics_reason": "gün {day} cədvələ sığmır (~{hours} saat aktivlik+yol) — digər yerlərə daha yaxın alternativ lazımdır",
        "max_rounds": "Maksimum danışıq raundu keçildi — mövcud ən yaxşı variantla davam edilir.",
        "fallback": "{agent} Agent OpenRouter fallback modelinə keçdi ({model}). Səbəb: {reason}",
        "stopped": "Planlaşdırma dayandı: {error}",
        "planner_template": "Yekun marşrut hazırdır: {days} gün, ümumi xərc ~{total} {cur}. Bütün günlər büdcə və logistika baxımından təsdiqlənib.",
        "say_propose_default": "Təkliflərim hazırdır.",
        "say_revise_default": "Alternativlər təklif edirəm.",
    },
}


def msg(lang: str, key: str, **kwargs) -> str:
    table = MESSAGES.get(lang, MESSAGES["en"])
    return table[key].format(**kwargs)
