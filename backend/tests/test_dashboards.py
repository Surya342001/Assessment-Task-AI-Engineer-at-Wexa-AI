from __future__ import annotations

import pytest
from httpx import AsyncClient


async def create_org_and_get_id(client: AsyncClient, auth_headers: dict) -> str:
    response = await client.post(
        "/api/orgs/",
        headers=auth_headers,
        json={"name": "Dashboard Test Org"},
    )
    return response.json()["id"]


@pytest.mark.asyncio
async def test_create_dashboard(client: AsyncClient, auth_headers: dict):
    org_id = await create_org_and_get_id(client, auth_headers)
    response = await client.post(
        f"/api/orgs/{org_id}/dashboards/",
        headers=auth_headers,
        json={
            "name": "My Dashboard",
            "description": "Test dashboard",
            "refresh_interval": 60,
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "My Dashboard"
    assert data["organization_id"] == org_id


@pytest.mark.asyncio
async def test_list_dashboards(client: AsyncClient, auth_headers: dict):
    org_id = await create_org_and_get_id(client, auth_headers)
    # Create two dashboards
    for i in range(2):
        await client.post(
            f"/api/orgs/{org_id}/dashboards/",
            headers=auth_headers,
            json={"name": f"Dashboard {i}"},
        )
    response = await client.get(
        f"/api/orgs/{org_id}/dashboards/",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert len(response.json()) >= 2


@pytest.mark.asyncio
async def test_add_widget_to_dashboard(client: AsyncClient, auth_headers: dict):
    org_id = await create_org_and_get_id(client, auth_headers)
    create_resp = await client.post(
        f"/api/orgs/{org_id}/dashboards/",
        headers=auth_headers,
        json={"name": "Widget Dashboard"},
    )
    dashboard_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/orgs/{org_id}/dashboards/{dashboard_id}/widgets",
        headers=auth_headers,
        json={
            "widget_type": "line_chart",
            "title": "Page Views",
            "query_config": {
                "event_name": "page_view",
                "aggregation": "count",
                "time_range": "24h",
                "interval": "1h",
            },
            "position": {"x": 0, "y": 0, "w": 6, "h": 4},
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["widget_type"] == "line_chart"
    assert data["title"] == "Page Views"


@pytest.mark.asyncio
async def test_share_dashboard(client: AsyncClient, auth_headers: dict):
    org_id = await create_org_and_get_id(client, auth_headers)
    create_resp = await client.post(
        f"/api/orgs/{org_id}/dashboards/",
        headers=auth_headers,
        json={"name": "Shareable Dashboard"},
    )
    dashboard_id = create_resp.json()["id"]

    response = await client.post(
        f"/api/orgs/{org_id}/dashboards/{dashboard_id}/share",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert "public_slug" in data
    assert "public_url" in data


@pytest.mark.asyncio
async def test_delete_dashboard(client: AsyncClient, auth_headers: dict):
    org_id = await create_org_and_get_id(client, auth_headers)
    create_resp = await client.post(
        f"/api/orgs/{org_id}/dashboards/",
        headers=auth_headers,
        json={"name": "To Delete"},
    )
    dashboard_id = create_resp.json()["id"]

    response = await client.delete(
        f"/api/orgs/{org_id}/dashboards/{dashboard_id}",
        headers=auth_headers,
    )
    assert response.status_code == 204
