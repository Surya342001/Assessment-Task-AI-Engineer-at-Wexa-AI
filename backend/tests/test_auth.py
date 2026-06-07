from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_success(client: AsyncClient):
    response = await client.post(
        "/api/auth/signup",
        json={
            "email": "newuser@example.com",
            "password": "SecurePass123",
            "full_name": "New User",
            "organization_name": "New Org",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_signup_duplicate_email(client: AsyncClient):
    payload = {
        "email": "dup@example.com",
        "password": "SecurePass123",
        "full_name": "User",
        "organization_name": "Org",
    }
    await client.post("/api/auth/signup", json=payload)
    response = await client.post("/api/auth/signup", json=payload)
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_signin_success(client: AsyncClient):
    # First sign up
    await client.post(
        "/api/auth/signup",
        json={
            "email": "signin@example.com",
            "password": "SecurePass123",
            "full_name": "Sign In User",
            "organization_name": "Sign In Org",
        },
    )
    # Then sign in
    response = await client.post(
        "/api/auth/signin",
        json={"email": "signin@example.com", "password": "SecurePass123"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data


@pytest.mark.asyncio
async def test_signin_wrong_password(client: AsyncClient):
    response = await client.post(
        "/api/auth/signin",
        json={"email": "signin@example.com", "password": "WrongPassword"},
    )
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, auth_headers: dict):
    response = await client.get("/api/auth/me", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "email" in data
    assert "id" in data


@pytest.mark.asyncio
async def test_get_me_no_auth(client: AsyncClient):
    response = await client.get("/api/auth/me")
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_weak_password_rejected(client: AsyncClient):
    response = await client.post(
        "/api/auth/signup",
        json={
            "email": "weak@example.com",
            "password": "weak",
            "full_name": "User",
            "organization_name": "Org",
        },
    )
    assert response.status_code == 422
