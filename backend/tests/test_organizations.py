"""
ORGANIZATION TEST CASES
========================
TC-ORG-01  Create organization → 201, id + name returned
TC-ORG-02  Create org requires auth → 401
TC-ORG-03  Get organization by ID → 200
TC-ORG-04  Update organization name → 200
TC-ORG-05  List members of organization → 200, creator listed as OWNER
TC-ORG-06  Invite member to org → 201, invitation returned
TC-ORG-07  Invite to non-existent org → 404
"""
import uuid

import pytest
from httpx import AsyncClient


_BASE = "/api/orgs"


# ─── TC-ORG-01: Create org ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_organization(client: AsyncClient, auth_headers: dict):
    resp = await client.post(_BASE + "/", headers=auth_headers, json={"name": "My Org"})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "id" in data
    assert data["name"] == "My Org"


# ─── TC-ORG-02: Requires auth ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_org_requires_auth(client: AsyncClient):
    resp = await client.post(_BASE + "/", json={"name": "No Auth Org"})
    assert resp.status_code == 401


# ─── TC-ORG-03: Get org by ID ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_organization(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    resp = await client.get(f"{_BASE}/{org_id}", headers=auth_context["headers"])
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == org_id


# ─── TC-ORG-04: Update org name ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_organization(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    resp = await client.patch(
        f"{_BASE}/{org_id}",
        headers=auth_context["headers"],
        json={"name": "Renamed Org"},
    )
    assert resp.status_code == 200, resp.text
    assert resp.json()["name"] == "Renamed Org"


# ─── TC-ORG-05: List members ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_members(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    resp = await client.get(f"{_BASE}/{org_id}/members", headers=auth_context["headers"])
    assert resp.status_code == 200, resp.text
    members = resp.json()
    assert isinstance(members, list)
    assert len(members) >= 1
    roles = [m["role"] for m in members]
    assert "owner" in roles


# ─── TC-ORG-06: Invite member ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invite_member(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    invite_email = f"invite_{uuid.uuid4().hex[:8]}@example.com"
    resp = await client.post(
        f"{_BASE}/{org_id}/members/invite",
        headers=auth_context["headers"],
        json={"email": invite_email, "role": "viewer"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "token" in data or "id" in data


# ─── TC-ORG-07: Invite to non-existent org ───────────────────────────────────

@pytest.mark.asyncio
async def test_invite_nonexistent_org(client: AsyncClient, auth_headers: dict):
    fake_id = str(uuid.uuid4())
    resp = await client.post(
        f"{_BASE}/{fake_id}/members/invite",
        headers=auth_headers,
        json={"email": "x@example.com", "role": "member"},
    )
    assert resp.status_code in (403, 404, 422)
