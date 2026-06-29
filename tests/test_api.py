import json
import pytest
from fastapi import status
from httpx import AsyncClient

# Helper to generate mock auth headers
def get_auth_header(user_id: str, workspace_id: str, permissions: list[str]) -> dict:
    auth_data = {
        "user_id": user_id,
        "workspace_id": workspace_id,
        "permissions": permissions
    }
    return {"X-Mock-Auth": json.dumps(auth_data)}

@pytest.mark.asyncio
async def test_health_and_ready(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ok"}

    response = await client.get("/ready")
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {"status": "ready"}

@pytest.mark.asyncio
async def test_create_and_idempotency(client: AsyncClient):
    workspace_id = "ws_1"
    headers = get_auth_header("usr_1", workspace_id, ["approval:create", "approval:read"])
    headers["Idempotency-Key"] = "idem_key_1"

    payload = {
        "sourceType": "ARTICLE",
        "sourceId": "art_123",
        "title": "Test Title",
        "description": "Test Description",
        "reviewerUserIds": ["usr_2", "usr_3"]
    }

    # 1. First request creates the resource (201 Created)
    response = await client.post(
        f"/api/v1/workspaces/{workspace_id}/approval-requests",
        json=payload,
        headers=headers
    )
    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data["id"] is not None
    assert data["status"] == "PENDING"
    assert data["title"] == "Test Title"
    assert data["workspaceId"] == workspace_id
    assert data["idempotencyKey"] == "idem_key_1"
    request_id = data["id"]

    # 2. Second request with same idempotency key and same payload returns existing resource (200 OK)
    response_replay = await client.post(
        f"/api/v1/workspaces/{workspace_id}/approval-requests",
        json=payload,
        headers=headers
    )
    assert response_replay.status_code == status.HTTP_200_OK
    data_replay = response_replay.json()
    assert data_replay["id"] == request_id

    # 3. Third request with same key but different payload returns 409 Conflict
    payload_mismatch = payload.copy()
    payload_mismatch["title"] = "Different Title"
    response_conflict = await client.post(
        f"/api/v1/workspaces/{workspace_id}/approval-requests",
        json=payload_mismatch,
        headers=headers
    )
    assert response_conflict.status_code == status.HTTP_409_CONFLICT
    assert "already exists with this idempotency key but different data" in response_conflict.json()["detail"]

@pytest.mark.asyncio
async def test_state_machine_transitions(client: AsyncClient):
    workspace_id = "ws_1"
    headers_create = get_auth_header("usr_1", workspace_id, ["approval:create"])
    headers_decide = get_auth_header("usr_2", workspace_id, ["approval:decide"])
    
    headers_create["Idempotency-Key"] = "idem_key_state_machine"

    payload = {
        "sourceType": "ARTICLE",
        "sourceId": "art_456",
        "title": "State machine test",
        "reviewerUserIds": ["usr_2"]
    }

    # Create approval request
    res = await client.post(
        f"/api/v1/workspaces/{workspace_id}/approval-requests",
        json=payload,
        headers=headers_create
    )
    assert res.status_code == status.HTTP_201_CREATED
    request_id = res.json()["id"]

    # Reject request (PENDING -> REJECTED)
    res_reject = await client.post(
        f"/api/v1/workspaces/{workspace_id}/approval-requests/{request_id}/reject",
        json={"reason": "Incorrect spelling"},
        headers=headers_decide
    )
    assert res_reject.status_code == status.HTTP_200_OK
    assert res_reject.json()["status"] == "REJECTED"

    # Try to approve rejected request (REJECTED -> APPROVED) -> 409 Conflict
    res_approve = await client.post(
        f"/api/v1/workspaces/{workspace_id}/approval-requests/{request_id}/approve",
        json={"comment": "Looks good now!"},
        headers=headers_decide
    )
    assert res_approve.status_code == status.HTTP_409_CONFLICT
    assert "Cannot change status from RequestStatus.REJECTED to ActionType.APPROVE" in res_approve.json()["detail"]

@pytest.mark.asyncio
async def test_tenant_isolation(client: AsyncClient):
    # Workspace 1 setup
    ws_1 = "ws_1"
    headers_ws1 = get_auth_header("usr_1", ws_1, ["approval:create", "approval:read"])
    headers_ws1["Idempotency-Key"] = "idem_key_isolation"

    payload = {
        "sourceType": "ARTICLE",
        "sourceId": "art_789",
        "title": "Isolation Test",
        "reviewerUserIds": ["usr_2"]
    }

    res_create = await client.post(
        f"/api/v1/workspaces/{ws_1}/approval-requests",
        json=payload,
        headers=headers_ws1
    )
    assert res_create.status_code == status.HTTP_201_CREATED
    request_id = res_create.json()["id"]

    # Case A: User from ws_2 attempts to access ws_1 path -> 403 Forbidden (Auth layer checks workspace mismatch)
    headers_ws2_mismatch = get_auth_header("usr_ws2", "ws_2", ["approval:read"])
    res_forbidden = await client.get(
        f"/api/v1/workspaces/{ws_1}/approval-requests/{request_id}",
        headers=headers_ws2_mismatch
    )
    assert res_forbidden.status_code == status.HTTP_403_FORBIDDEN
    assert "Workspace ID mismatch" in res_forbidden.json()["detail"]

    # Case B: User from ws_2 attempts to access using ws_2 path but request_id from ws_1 -> 404 Not Found (Data isolation check)
    headers_ws2_valid_path = get_auth_header("usr_ws2", "ws_2", ["approval:read"])
    res_not_found = await client.get(
        f"/api/v1/workspaces/ws_2/approval-requests/{request_id}",
        headers=headers_ws2_valid_path
    )
    assert res_not_found.status_code == status.HTTP_404_NOT_FOUND
    assert "Approval request not found" in res_not_found.json()["detail"]
