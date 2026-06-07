"""
API KEYS TEST CASES
====================
TC-KEY-01  Create API key → 201, full key in response body (one-time only)
TC-KEY-02  Created key has prefix field (masked display)
TC-KEY-03  List API keys → 200, returns list
TC-KEY-04  Listed keys do NOT expose full key (only prefix)
TC-KEY-05  Revoke API key → 204
TC-KEY-06  Revoked key no longer active in list
TC-KEY-07  Create with empty name → 422
TC-KEY-08  All endpoints require auth → 401
"""
import pytest
from httpx import AsyncClient


def _keys_url(org_id: str) -> str:
    return f"/api/orgs/{org_id}/api-keys/"


# ─── TC-KEY-01 + TC-KEY-02: Create API key ───────────────────────────────────

@pytest.mark.asyncio
async def test_create_api_key(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    resp = await client.post(
        _keys_url(org_id),
        headers=auth_context["headers"],
        json={"name": "My Integration Key"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "key" in data, "Full key must be present on creation (one-time)"
    assert "key_prefix" in data
    assert "id" in data
    assert data["name"] == "My Integration Key"
    assert data["is_active"] is True
    # Full key should be longer than just the prefix
    assert len(data["key"]) > len(data["key_prefix"])


# ─── TC-KEY-03 + TC-KEY-04: List API keys ────────────────────────────────────

@pytest.mark.asyncio
async def test_list_api_keys(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    headers = auth_context["headers"]

    # Create a key first
    await client.post(_keys_url(org_id), headers=headers, json={"name": "Listed Key"})

    resp = await client.get(_keys_url(org_id), headers=headers)
    assert resp.status_code == 200, resp.text
    keys = resp.json()
    assert isinstance(keys, list)
    assert len(keys) >= 1

    # Listed keys must NOT expose the full key
    for k in keys:
        assert "key" not in k, "Full key must not be returned in list endpoint"
        assert "key_prefix" in k


# ─── TC-KEY-05 + TC-KEY-06: Revoke API key ───────────────────────────────────

@pytest.mark.asyncio
async def test_revoke_api_key(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    headers = auth_context["headers"]

    create_resp = await client.post(
        _keys_url(org_id), headers=headers, json={"name": "To Be Revoked"}
    )
    assert create_resp.status_code == 201
    key_id = create_resp.json()["id"]

    revoke_resp = await client.delete(
        f"/api/orgs/{org_id}/api-keys/{key_id}", headers=headers
    )
    assert revoke_resp.status_code == 204

    # Confirm it's no longer active
    list_resp = await client.get(_keys_url(org_id), headers=headers)
    active_ids = [k["id"] for k in list_resp.json() if k["is_active"]]
    assert key_id not in active_ids


# ─── TC-KEY-07: Empty name → 422 ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_api_key_empty_name(client: AsyncClient, auth_context: dict):
    resp = await client.post(
        _keys_url(auth_context["org_id"]),
        headers=auth_context["headers"],
        json={"name": ""},
    )
    assert resp.status_code == 422


# ─── TC-KEY-08: Requires auth ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_api_keys_require_auth(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    resp = await client.get(_keys_url(org_id))
    assert resp.status_code == 401
