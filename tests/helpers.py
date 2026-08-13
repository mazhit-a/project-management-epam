from httpx import AsyncClient

DEFAULT_PASSWORD = "Passw0rd!"


async def register(client: AsyncClient, login: str, password: str = DEFAULT_PASSWORD) -> dict:
    resp = await client.post(
        "/auth",
        json={"login": login, "password": password, "password_repeat": password},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def login(client: AsyncClient, login_: str, password: str = DEFAULT_PASSWORD) -> str:
    resp = await client.post("/login", json={"login": login_, "password": password})
    assert resp.status_code == 200, resp.text
    return resp.json()["access_token"]


async def register_and_login(
    client: AsyncClient, login_: str, password: str = DEFAULT_PASSWORD
) -> tuple[dict, str]:
    user = await register(client, login_, password)
    token = await login(client, login_, password)
    return user, token


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}
