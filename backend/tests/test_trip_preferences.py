"""Trip seçimləri: must_visit / avoid / pace — validasiya, saxlanma və prompt blokları."""

from app.llm import prompts

from .conftest import register_user
from .test_api_trips import VALID_PAYLOAD


# --- Prompt blokları (LLM çağırışsız, sırf mətn) ---

def test_propose_prompt_includes_must_visit_and_avoid():
    p = prompts.interest_propose(
        "Rome", 2, ["history"], 2, "USD", "en",
        must_visit=["Colosseo", "Fontana di Trevi"], avoid=["Pantheon"],
    )
    assert "MUST-VISIT" in p and "Colosseo; Fontana di Trevi" in p
    assert "NEVER suggest" in p and "Pantheon" in p


def test_propose_prompt_pace_lines():
    relaxed = prompts.interest_propose("Rome", 2, [], 1, "USD", "en", pace="relaxed")
    intense = prompts.interest_propose("Rome", 2, [], 1, "USD", "en", pace="intense")
    normal = prompts.interest_propose("Rome", 2, [], 1, "USD", "en")
    assert "exactly 2 activities" in relaxed
    assert "4 activities per day (packed" in intense
    assert "3-4 activities" in normal
    # Naməlum pace → normal fallback
    assert "3-4 activities" in prompts.interest_propose("Rome", 2, [], 1, "USD", "en", pace="turbo")


def test_propose_prompt_empty_lists_add_no_blocks():
    p = prompts.interest_propose("Rome", 2, [], 1, "USD", "en")
    assert "MUST-VISIT" not in p and "NEVER suggest" not in p


def test_revise_prompt_keep_and_avoid():
    p = prompts.interest_revise(
        "Rome", "USD", [{"day": 1, "name": "X", "reason": "expensive"}], "en",
        must_visit=["Colosseo"], avoid=["Pantheon"],
    )
    assert "must-visit" in p and "Colosseo" in p
    assert "NEVER suggest" in p and "Pantheon" in p


# --- API validasiya + saxlanma ---

async def test_create_trip_with_preferences(client):
    headers = await register_user(client)
    payload = {
        **VALID_PAYLOAD,
        "must_visit": ["  Colosseo  ", "", "Fontana di Trevi"],
        "avoid": ["Pantheon"],
        "pace": "relaxed",
    }
    resp = await client.post("/api/trips", json=payload, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    # Boşlar atılır, kənar boşluqlar silinir
    assert data["must_visit"] == ["Colosseo", "Fontana di Trevi"]
    assert data["avoid"] == ["Pantheon"]
    assert data["pace"] == "relaxed"

    detail = await client.get(f"/api/trips/{data['id']}", headers=headers)
    assert detail.status_code == 200
    assert detail.json()["must_visit"] == ["Colosseo", "Fontana di Trevi"]


async def test_create_trip_defaults_without_preferences(client):
    headers = await register_user(client)
    resp = await client.post("/api/trips", json=VALID_PAYLOAD, headers=headers)
    assert resp.status_code == 201
    data = resp.json()
    assert data["must_visit"] == [] and data["avoid"] == []
    assert data["pace"] == "normal"


async def test_create_trip_too_many_must_visit_422(client):
    headers = await register_user(client)
    payload = {**VALID_PAYLOAD, "must_visit": [f"Place {i}" for i in range(6)]}
    resp = await client.post("/api/trips", json=payload, headers=headers)
    assert resp.status_code == 422


async def test_create_trip_invalid_pace_422(client):
    headers = await register_user(client)
    payload = {**VALID_PAYLOAD, "pace": "turbo"}
    resp = await client.post("/api/trips", json=payload, headers=headers)
    assert resp.status_code == 422
