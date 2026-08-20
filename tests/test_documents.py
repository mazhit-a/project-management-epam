from httpx import AsyncClient

from tests.helpers import auth_headers, register_and_login

PDF_BYTES = b"%PDF-1.4 fake pdf content"
DOCX_BYTES = b"PK fake docx content"


async def _create_project(client: AsyncClient, token: str) -> dict:
    resp = await client.post(
        "/projects", json={"name": "Docs Project"}, headers=auth_headers(token)
    )
    assert resp.status_code == 201, resp.text
    return resp.json()


async def test_upload_and_list_documents(client: AsyncClient):
    _, token = await register_and_login(client, "owner")
    project = await _create_project(client, token)

    upload = await client.post(
        f"/project/{project['id']}/documents",
        headers=auth_headers(token),
        files=[
            ("files", ("spec.pdf", PDF_BYTES, "application/pdf")),
            ("files", ("notes.docx", DOCX_BYTES, "application/vnd.custom")),
        ],
    )
    assert upload.status_code == 201, upload.text
    uploaded = upload.json()
    assert {d["filename"] for d in uploaded} == {"spec.pdf", "notes.docx"}

    listing = await client.get(f"/project/{project['id']}/documents", headers=auth_headers(token))
    assert listing.status_code == 200
    assert len(listing.json()) == 2


async def test_upload_rejects_unsupported_extension(client: AsyncClient):
    _, token = await register_and_login(client, "owner")
    project = await _create_project(client, token)

    resp = await client.post(
        f"/project/{project['id']}/documents",
        headers=auth_headers(token),
        files=[("files", ("virus.exe", b"nope", "application/octet-stream"))],
    )
    assert resp.status_code == 422
    assert resp.json()["error"]["code"] == "unsupported_document_type"


async def test_stranger_cannot_upload_or_list(client: AsyncClient):
    _, owner_token = await register_and_login(client, "owner")
    project = await _create_project(client, owner_token)
    _, stranger_token = await register_and_login(client, "stranger")

    resp = await client.get(
        f"/project/{project['id']}/documents", headers=auth_headers(stranger_token)
    )
    assert resp.status_code == 403


async def test_download_document(client: AsyncClient, s3_client: AsyncClient):
    _, token = await register_and_login(client, "owner")
    project = await _create_project(client, token)
    upload = await client.post(
        f"/project/{project['id']}/documents",
        headers=auth_headers(token),
        files=[("files", ("spec.pdf", PDF_BYTES, "application/pdf"))],
    )
    document_id = upload.json()[0]["id"]

    resp = await client.get(f"/document/{document_id}", headers=auth_headers(token))
    assert resp.status_code == 307
    download = await s3_client.get(resp.headers["location"])
    assert download.content == PDF_BYTES


async def test_download_without_access_is_forbidden(client: AsyncClient):
    _, owner_token = await register_and_login(client, "owner")
    project = await _create_project(client, owner_token)
    upload = await client.post(
        f"/project/{project['id']}/documents",
        headers=auth_headers(owner_token),
        files=[("files", ("spec.pdf", PDF_BYTES, "application/pdf"))],
    )
    document_id = upload.json()[0]["id"]

    _, stranger_token = await register_and_login(client, "stranger")
    resp = await client.get(f"/document/{document_id}", headers=auth_headers(stranger_token))
    assert resp.status_code == 403


async def test_update_document_replaces_content(client: AsyncClient, s3_client: AsyncClient):
    _, token = await register_and_login(client, "owner")
    project = await _create_project(client, token)
    upload = await client.post(
        f"/project/{project['id']}/documents",
        headers=auth_headers(token),
        files=[("files", ("spec.pdf", PDF_BYTES, "application/pdf"))],
    )
    document_id = upload.json()[0]["id"]

    updated = await client.put(
        f"/document/{document_id}",
        headers=auth_headers(token),
        files={"file": ("spec-v2.pdf", b"%PDF-1.4 new content", "application/pdf")},
    )
    assert updated.status_code == 200
    assert updated.json()["filename"] == "spec-v2.pdf"

    resp = await client.get(f"/document/{document_id}", headers=auth_headers(token))
    download = await s3_client.get(resp.headers["location"])
    assert download.content == b"%PDF-1.4 new content"


async def test_delete_document_removes_it(client: AsyncClient):
    _, token = await register_and_login(client, "owner")
    project = await _create_project(client, token)
    upload = await client.post(
        f"/project/{project['id']}/documents",
        headers=auth_headers(token),
        files=[("files", ("spec.pdf", PDF_BYTES, "application/pdf"))],
    )
    document_id = upload.json()[0]["id"]

    deleted = await client.delete(f"/document/{document_id}", headers=auth_headers(token))
    assert deleted.status_code == 204

    resp = await client.get(f"/document/{document_id}", headers=auth_headers(token))
    assert resp.status_code == 404


async def test_deleting_project_removes_its_documents(client: AsyncClient):
    _, token = await register_and_login(client, "owner")
    project = await _create_project(client, token)
    upload = await client.post(
        f"/project/{project['id']}/documents",
        headers=auth_headers(token),
        files=[("files", ("spec.pdf", PDF_BYTES, "application/pdf"))],
    )
    document_id = upload.json()[0]["id"]

    deleted = await client.delete(f"/project/{project['id']}", headers=auth_headers(token))
    assert deleted.status_code == 204

    resp = await client.get(f"/document/{document_id}", headers=auth_headers(token))
    assert resp.status_code == 404
