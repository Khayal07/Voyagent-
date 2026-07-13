"""Auth API: register/login/me axını."""

from .conftest import register_user


async def test_register_returns_token(client):
    resp = await client.post("/api/auth/register", json={"email": "new@example.com", "password": "password123"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["email"] == "new@example.com"
    assert data["token"]


async def test_register_duplicate_email_409(client):
    await register_user(client, email="dup@example.com")
    resp = await client.post("/api/auth/register", json={"email": "dup@example.com", "password": "password123"})
    assert resp.status_code == 409


async def test_register_short_password_422(client):
    resp = await client.post("/api/auth/register", json={"email": "x@example.com", "password": "short"})
    assert resp.status_code == 422


async def test_login_success(client):
    await register_user(client, email="log@example.com", password="password123")
    resp = await client.post("/api/auth/login", json={"email": "log@example.com", "password": "password123"})
    assert resp.status_code == 200
    assert resp.json()["token"]


async def test_login_email_case_insensitive(client):
    await register_user(client, email="case@example.com", password="password123")
    resp = await client.post("/api/auth/login", json={"email": "CASE@example.com", "password": "password123"})
    assert resp.status_code == 200


async def test_login_wrong_password_401(client):
    await register_user(client, email="wp@example.com", password="password123")
    resp = await client.post("/api/auth/login", json={"email": "wp@example.com", "password": "wrongpass1"})
    assert resp.status_code == 401


async def test_login_unknown_email_401(client):
    resp = await client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "password123"})
    assert resp.status_code == 401


async def test_me_returns_current_user(client):
    headers = await register_user(client, email="me@example.com")
    resp = await client.get("/api/auth/me", headers=headers)
    assert resp.status_code == 200
    assert resp.json()["email"] == "me@example.com"


async def test_me_invalid_token_401(client):
    resp = await client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-token"})
    assert resp.status_code == 401
