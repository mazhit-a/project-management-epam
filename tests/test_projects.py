from httpx import AsyncClient

from tests.helpers import auth_headers, register_and_login

PAYLOAD = {"name": "Website Redesign", "description": "Q3 marketing site refresh"}


async def _create_project(client: AsyncClient, token: str, **overrides) -> dict:
    resp = await client.post(
        "/projects", json={**PAYLOAD, **overrides}, headers=auth_headers(token)
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_create_project_makes_creator_the_owner(client: AsyncClient):
    _, token = await register_and_login(client, "owner")
    project = await _create_project(client, token)
    assert project["name"] == PAYLOAD["name"]
    assert project["description"] == PAYLOAD["description"]

    info = await client.get(f"/project/{project['id']}/info", headers=auth_headers(token))
    assert info.status_code == 200
    assert info.json()["owner_id"] == project["owner_id"]


async def test_list_projects_returns_full_info_with_documents(client: AsyncClient):
    _, token = await register_and_login(client, "owner")
    project = await _create_project(client, token)

    resp = await client.get("/projects", headers=auth_headers(token))
    assert resp.status_code == 200
    body = resp.json()
    assert len(body) == 1
    assert body[0]["id"] == project["id"]
    assert body[0]["documents"] == []


async def test_stranger_cannot_see_project_info(client: AsyncClient):
    _, owner_token = await register_and_login(client, "owner")
    project = await _create_project(client, owner_token)

    _, stranger_token = await register_and_login(client, "stranger")
    resp = await client.get(f"/project/{project['id']}/info", headers=auth_headers(stranger_token))
    assert resp.status_code == 403
    assert resp.json()["error"]["code"] == "project_access_denied"


async def test_get_info_for_missing_project_returns_404(client: AsyncClient):
    _, token = await register_and_login(client, "owner")
    resp = await client.get(
        "/project/0f2b1a2e-0000-4000-8000-000000000000/info", headers=auth_headers(token)
    )
    assert resp.status_code == 404


async def test_update_info_updates_name_and_description(client: AsyncClient):
    _, token = await register_and_login(client, "owner")
    project = await _create_project(client, token)

    resp = await client.put(
        f"/project/{project['id']}/info",
        json={"name": "New Name"},
        headers=auth_headers(token),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["name"] == "New Name"
    assert body["description"] == PAYLOAD["description"]


async def test_delete_project_requires_owner(client: AsyncClient):
    _, owner_token = await register_and_login(client, "owner")
    project = await _create_project(client, owner_token)

    _, other_token = await register_and_login(client, "invitee")
    await client.post(
        f"/project/{project['id']}/invite",
        params={"user": "invitee"},
        headers=auth_headers(owner_token),
    )

    denied = await client.delete(f"/project/{project['id']}", headers=auth_headers(other_token))
    assert denied.status_code == 403
    assert denied.json()["error"]["code"] == "project_owner_required"

    allowed = await client.delete(f"/project/{project['id']}", headers=auth_headers(owner_token))
    assert allowed.status_code == 204

    gone = await client.get(f"/project/{project['id']}/info", headers=auth_headers(owner_token))
    assert gone.status_code == 404


async def test_invite_grants_access_to_invited_user(client: AsyncClient):
    _, owner_token = await register_and_login(client, "owner")
    project = await _create_project(client, owner_token)
    _, invitee_token = await register_and_login(client, "invitee")

    before = await client.get(f"/project/{project['id']}/info", headers=auth_headers(invitee_token))
    assert before.status_code == 403

    invite = await client.post(
        f"/project/{project['id']}/invite",
        params={"user": "invitee"},
        headers=auth_headers(owner_token),
    )
    assert invite.status_code == 204

    after = await client.get(f"/project/{project['id']}/info", headers=auth_headers(invitee_token))
    assert after.status_code == 200


async def test_invite_by_non_owner_is_forbidden(client: AsyncClient):
    _, owner_token = await register_and_login(client, "owner")
    project = await _create_project(client, owner_token)
    _, other_token = await register_and_login(client, "other")

    resp = await client.post(
        f"/project/{project['id']}/invite",
        params={"user": "owner"},
        headers=auth_headers(other_token),
    )
    assert resp.status_code == 403


async def test_invite_unknown_user_returns_404(client: AsyncClient):
    _, owner_token = await register_and_login(client, "owner")
    project = await _create_project(client, owner_token)

    resp = await client.post(
        f"/project/{project['id']}/invite",
        params={"user": "ghost"},
        headers=auth_headers(owner_token),
    )
    assert resp.status_code == 404


async def test_invite_already_member_returns_422(client: AsyncClient):
    _, owner_token = await register_and_login(client, "owner")
    project = await _create_project(client, owner_token)
    await register_and_login(client, "invitee")

    first = await client.post(
        f"/project/{project['id']}/invite",
        params={"user": "invitee"},
        headers=auth_headers(owner_token),
    )
    assert first.status_code == 204

    second = await client.post(
        f"/project/{project['id']}/invite",
        params={"user": "invitee"},
        headers=auth_headers(owner_token),
    )
    assert second.status_code == 422
    assert second.json()["error"]["code"] == "already_member"
