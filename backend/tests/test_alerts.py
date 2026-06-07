"""
ALERTS TEST CASES
==================
TC-ALT-01  Create alert → 201, all fields returned
TC-ALT-02  Create alert with invalid condition → 422
TC-ALT-03  List alerts → 200
TC-ALT-04  Get alert by ID → 200
TC-ALT-05  Get non-existent alert → 404
TC-ALT-06  Update alert name + threshold → 200
TC-ALT-07  Mute alert → 200, status becomes muted
TC-ALT-08  Delete alert → 204
TC-ALT-09  All endpoints require auth → 401
"""
import uuid

import pytest
from httpx import AsyncClient


def _alerts_url(org_id: str) -> str:
    return f"/api/orgs/{org_id}/alerts/"


def _alert_payload(**kwargs):
    return {
        "name": "High Error Rate",
        "description": "Alert when error rate > 5%",
        "metric_query": {"event_name": "error", "aggregation": "count"},
        "condition": "gt",
        "threshold": 100.0,
        "window_minutes": 5,
        "notification_channels": [],
        **kwargs,
    }


# ─── TC-ALT-01: Create alert ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_alert(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    resp = await client.post(
        _alerts_url(org_id),
        headers=auth_context["headers"],
        json=_alert_payload(),
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["name"] == "High Error Rate"
    assert data["condition"] == "gt"
    assert data["threshold"] == 100.0
    assert data["status"] == "active"
    assert "id" in data


# ─── TC-ALT-02: Invalid condition → 422 ──────────────────────────────────────

@pytest.mark.asyncio
async def test_create_alert_invalid_condition(client: AsyncClient, auth_context: dict):
    resp = await client.post(
        _alerts_url(auth_context["org_id"]),
        headers=auth_context["headers"],
        json=_alert_payload(condition="invalid_op"),
    )
    assert resp.status_code == 422


# ─── TC-ALT-03: List alerts ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_alerts(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    headers = auth_context["headers"]

    await client.post(_alerts_url(org_id), headers=headers, json=_alert_payload(name="Alert A"))
    await client.post(_alerts_url(org_id), headers=headers, json=_alert_payload(name="Alert B"))

    resp = await client.get(_alerts_url(org_id), headers=headers)
    assert resp.status_code == 200, resp.text
    alerts = resp.json()
    assert isinstance(alerts, list)
    assert len(alerts) >= 2


# ─── TC-ALT-04: Get alert by ID ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_alert_by_id(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    headers = auth_context["headers"]

    create_resp = await client.post(
        _alerts_url(org_id), headers=headers, json=_alert_payload(name="Lookup Alert")
    )
    alert_id = create_resp.json()["id"]

    resp = await client.get(f"/api/orgs/{org_id}/alerts/{alert_id}", headers=headers)
    assert resp.status_code == 200, resp.text
    assert resp.json()["id"] == alert_id


# ─── TC-ALT-05: Non-existent alert → 404 ─────────────────────────────────────

@pytest.mark.asyncio
async def test_get_nonexistent_alert(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    fake_id = str(uuid.uuid4())
    resp = await client.get(
        f"/api/orgs/{org_id}/alerts/{fake_id}", headers=auth_context["headers"]
    )
    assert resp.status_code == 404


# ─── TC-ALT-06: Update alert ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_alert(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    headers = auth_context["headers"]

    create_resp = await client.post(
        _alerts_url(org_id), headers=headers, json=_alert_payload(name="Update Me")
    )
    alert_id = create_resp.json()["id"]

    resp = await client.patch(
        f"/api/orgs/{org_id}/alerts/{alert_id}",
        headers=headers,
        json={"name": "Updated Alert", "threshold": 200.0},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["name"] == "Updated Alert"
    assert data["threshold"] == 200.0


# ─── TC-ALT-07: Mute alert ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_mute_alert(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    headers = auth_context["headers"]

    create_resp = await client.post(
        _alerts_url(org_id), headers=headers, json=_alert_payload(name="Mute Me")
    )
    alert_id = create_resp.json()["id"]

    resp = await client.post(
        f"/api/orgs/{org_id}/alerts/{alert_id}/mute",
        headers=headers,
        json={"duration_minutes": 60},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["status"] == "muted"
    assert data["muted_until"] is not None


# ─── TC-ALT-08: Delete alert ─────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_alert(client: AsyncClient, auth_context: dict):
    org_id = auth_context["org_id"]
    headers = auth_context["headers"]

    create_resp = await client.post(
        _alerts_url(org_id), headers=headers, json=_alert_payload(name="Delete Me")
    )
    alert_id = create_resp.json()["id"]

    del_resp = await client.delete(
        f"/api/orgs/{org_id}/alerts/{alert_id}", headers=headers
    )
    assert del_resp.status_code == 204

    get_resp = await client.get(
        f"/api/orgs/{org_id}/alerts/{alert_id}", headers=headers
    )
    assert get_resp.status_code == 404


# ─── TC-ALT-09: Requires auth ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_alerts_require_auth(client: AsyncClient, auth_context: dict):
    resp = await client.get(_alerts_url(auth_context["org_id"]))
    assert resp.status_code == 401
