from httpx import AsyncClient

from tests.helpers import auth_headers, login, register, register_and_login


async def test_register_and_login_flow(client: AsyncClient):
    user = await register(client, "jdoe")
    assert user["login"] == "jdoe"
    assert "password" not in user
    assert "password_hash" not in user

    token = await login(client, "jdoe")
    assert token

    me_check = await client.post("/projects", json={"name": "P"}, headers=auth_headers(token))
    assert me_check.status_code == 201


async def test_register_duplicate_login_returns_409(client: AsyncClient):
    await register(client, "jdoe")
    resp = await client.post(
        "/auth",
        json={"login": "jdoe", "password": "Passw0rd!", "password_repeat": "Passw0rd!"},
    )
    assert resp.status_code == 409
    assert resp.json()["error"]["code"] == "duplicate_user"


async def test_register_password_mismatch_returns_422(client: AsyncClient):
    resp = await client.post(
        "/auth",
        json={"login": "jdoe", "password": "Passw0rd!", "password_repeat": "Different1!"},
    )
    assert resp.status_code == 422


async def test_login_wrong_password_returns_401(client: AsyncClient):
    await register(client, "jdoe")
    resp = await client.post("/login", json={"login": "jdoe", "password": "wrong-password"})
    assert resp.status_code == 401
    assert resp.json()["error"]["code"] == "invalid_credentials"


async def test_login_unknown_user_returns_401(client: AsyncClient):
    resp = await client.post("/login", json={"login": "nobody", "password": "Passw0rd!"})
    assert resp.status_code == 401


async def test_protected_endpoint_without_token_is_rejected(client: AsyncClient):
    resp = await client.get("/projects")
    assert resp.status_code in (401, 403)


async def test_protected_endpoint_with_garbage_token_returns_401(client: AsyncClient):
    resp = await client.get("/projects", headers=auth_headers("not-a-real-token"))
    assert resp.status_code == 401


async def test_full_auth_round_trip(client: AsyncClient):
    _, token = await register_and_login(client, "roundtrip")
    resp = await client.get("/projects", headers=auth_headers(token))
    assert resp.status_code == 200
    assert resp.json() == []
