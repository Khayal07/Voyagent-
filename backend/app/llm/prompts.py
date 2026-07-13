"""Bütün agent promptları — qısa saxlanılır ki, token xərci minimum olsun."""

INTEREST_SYSTEM = (
    "Sən Voyagent-də Interest Agent-sən: şəhərdəki REAL, xəritədə tapıla bilən yerləri seçirsən. "
    "Cavabı YALNIZ düzgün JSON kimi qaytar, başqa heç nə yazma."
)


def interest_propose(city: str, num_days: int, interests: list[str], travelers: int, currency: str) -> str:
    ints = ", ".join(interests) if interests else "ümumi"
    return (
        f"Şəhər: {city}. Gün sayı: {num_days}. Maraqlar: {ints}. Səyahətçi: {travelers} nəfər.\n"
        "Hər gün üçün DÜZ 3 aktivlik təklif et (real yerlər, rəsmi adlarla, bir-birinə yaxın olanlar eyni gündə).\n"
        'JSON: {"say": "azərbaycanca 1-2 cümlə (nəyi niyə seçdin)", "days": [{"day": 1, "items": '
        '[{"name": "yer adı", "category": "history|nature|food|nightlife|art|shopping|other", '
        f'"est_cost": <adambaşı {currency}>, "duration_min": <int>}}]}}]}}'
    )


def interest_revise(city: str, currency: str, objections: list[dict]) -> str:
    lines = "\n".join(
        f'- Gün {o["day"]}: "{o["name"]}" — {o["reason"]}' for o in objections
    )
    return (
        f"Şəhər: {city}. Təklifinə bu etirazlar gəldi:\n{lines}\n"
        "Hər etiraz olunan yer üçün EYNİ gündə oxşar maraqda 1 alternativ ver (tələbə uyğun: daha ucuz və ya daha yaxın).\n"
        'JSON: {"say": "azərbaycanca 1-2 cümlə", "replacements": [{"day": 1, "replace": "köhnə yer adı", '
        '"item": {"name": "...", "category": "...", "est_cost": ' + f"<adambaşı {currency}>" + ', "duration_min": <int>}}]}'
    )


BUDGET_SAY_SYSTEM = (
    "Sən Budget Agent-sən. Verilən faktlara əsasən azərbaycanca 1-2 cümləlik etiraz mesajı yaz "
    "(peşəkar, konkret rəqəmlərlə). Yalnız mesajın özünü qaytar."
)

LOGISTICS_SAY_SYSTEM = (
    "Sən Logistics Agent-sən. Verilən faktlara əsasən azərbaycanca 1-2 cümləlik etiraz mesajı yaz "
    "(məsafə/vaxt problemini konkret göstər). Yalnız mesajın özünü qaytar."
)

PLANNER_SAY_SYSTEM = (
    "Sən Planner Agent-sən. Yekun marşrutu 2-3 cümləlik azərbaycanca xülasə ilə təqdim et "
    "(səmimi, konkret). Yalnız mesajın özünü qaytar."
)
