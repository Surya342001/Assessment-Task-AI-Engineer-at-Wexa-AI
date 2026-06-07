from __future__ import annotations

import uuid

import pytest
from httpx import AsyncClient


async def get_org_id(client: AsyncClient, auth_headers: dict) -> str:
    response = await client.get("/api/auth/me", headers=auth_headers)
    # Get the first org from the member list
    me = response.json()
    user_id = me["id"]
    # We'll create a new org for events tests
    org_response = await client.post(
        "/api/orgs/",
        headers=auth_headers,
        json={"name": "Events Test Org"},
    )
    return org_response.json()["id"]


@pytest.mark.asyncio
async def test_ingest_single_event(client: AsyncClient, auth_headers: dict):
    org_id = await get_org_id(client, auth_headers)
    response = await client.post(
        f"/api/orgs/{org_id}/events/ingest",
        headers=auth_headers,
        json={
            "name": "page_view",
            "properties": {"url": "/home", "browser": "Chrome"},
        },
    )
    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 1
    assert len(data["event_ids"]) == 1


@pytest.mark.asyncio
async def test_ingest_batch_events(client: AsyncClient, auth_headers: dict):
    org_id = await get_org_id(client, auth_headers)
    events = [
        {"name": "click", "properties": {"button": "cta"}} for _ in range(5)
    ]
    response = await client.post(
        f"/api/orgs/{org_id}/events/ingest/batch",
        headers=auth_headers,
        json={"events": events},
    )
    assert response.status_code == 202
    data = response.json()
    assert data["accepted"] == 5


@pytest.mark.asyncio
async def test_list_events(client: AsyncClient, auth_headers: dict):
    org_id = await get_org_id(client, auth_headers)
    # Ingest some events first
    await client.post(
        f"/api/orgs/{org_id}/events/ingest",
        headers=auth_headers,
        json={"name": "test_event", "properties": {}},
    )
    response = await client.get(
        f"/api/orgs/{org_id}/events/",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_event_requires_auth(client: AsyncClient):
    org_id = str(uuid.uuid4())
    response = await client.post(
        f"/api/orgs/{org_id}/events/ingest",
        json={"name": "test", "properties": {}},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_batch_too_large(client: AsyncClient, auth_headers: dict):
    org_id = await get_org_id(client, auth_headers)
    events = [{"name": "e", "properties": {}} for _ in range(1001)]
    response = await client.post(
        f"/api/orgs/{org_id}/events/ingest/batch",
        headers=auth_headers,
        json={"events": events},
    )
    assert response.status_code == 422
