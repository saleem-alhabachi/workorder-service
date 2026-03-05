# tests/test_workorders.py
from __future__ import annotations

import pytest
import pytest_asyncio
from httpx import AsyncClient


@pytest_asyncio.fixture
async def workorder_id(client: AsyncClient, token_editor: str) -> str:
    """Create a work order and return its ID."""
    r = await client.post(
        "/api/v1/workorders",
        json={"title": "Test WO", "description": "Test description"},
        headers={"Authorization": f"Bearer {token_editor}"},
    )
    assert r.status_code == 201
    return r.json()["id"]


@pytest.mark.asyncio
async def test_create_workorder_as_editor(
    client: AsyncClient,
    token_editor: str,
) -> None:
    r = await client.post(
        "/api/v1/workorders",
        json={"title": "New order", "description": "New order description"},
        headers={"Authorization": f"Bearer {token_editor}"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["title"] == "New order"
    assert data["description"] == "New order description"
    assert data["status"] == "pending"
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data
    assert "created_by" in data


@pytest.mark.asyncio
async def test_create_workorder_as_viewer_forbidden(
    client: AsyncClient,
    token_viewer: str,
) -> None:
    r = await client.post(
        "/api/v1/workorders",
        json={"title": "New order", "description": "Desc"},
        headers={"Authorization": f"Bearer {token_viewer}"},
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_create_workorder_unauthenticated(client: AsyncClient) -> None:
    r = await client.post(
        "/api/v1/workorders",
        json={"title": "New order", "description": "Desc"},
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_list_workorders(
    client: AsyncClient,
    token_viewer: str,
) -> None:
    r = await client.get(
        "/api/v1/workorders",
        headers={"Authorization": f"Bearer {token_viewer}"},
    )
    assert r.status_code == 200
    assert isinstance(r.json(), list)


@pytest.mark.asyncio
async def test_get_workorder_by_id(
    client: AsyncClient,
    token_viewer: str,
    workorder_id: str,
) -> None:
    r = await client.get(
        f"/api/v1/workorders/{workorder_id}",
        headers={"Authorization": f"Bearer {token_viewer}"},
    )
    assert r.status_code == 200
    assert r.json()["id"] == workorder_id
    assert r.json()["title"] == "Test WO"


@pytest.mark.asyncio
async def test_get_workorder_not_found(
    client: AsyncClient,
    token_viewer: str,
) -> None:
    r = await client.get(
        "/api/v1/workorders/00000000-0000-0000-0000-000000000000",
        headers={"Authorization": f"Bearer {token_viewer}"},
    )
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_status(
    client: AsyncClient,
    token_editor: str,
    workorder_id: str,
) -> None:
    r = await client.patch(
        f"/api/v1/workorders/{workorder_id}/status",
        json={"status": "in_progress"},
        headers={"Authorization": f"Bearer {token_editor}"},
    )
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"


@pytest.mark.asyncio
async def test_update_status_invalid_transition(
    client: AsyncClient,
    token_editor: str,
    workorder_id: str,
) -> None:
    # First move to in_progress
    await client.patch(
        f"/api/v1/workorders/{workorder_id}/status",
        json={"status": "in_progress"},
        headers={"Authorization": f"Bearer {token_editor}"},
    )
    # Then complete
    await client.patch(
        f"/api/v1/workorders/{workorder_id}/status",
        json={"status": "completed"},
        headers={"Authorization": f"Bearer {token_editor}"},
    )
    # COMPLETED -> PENDING is invalid
    r = await client.patch(
        f"/api/v1/workorders/{workorder_id}/status",
        json={"status": "pending"},
        headers={"Authorization": f"Bearer {token_editor}"},
    )
    assert r.status_code == 422
