from fastapi import APIRouter, Depends, Header, Response, status
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.api.deps import get_db, require_permission
from app.schemas.auth import UserToken
from app.schemas.approval import (
    ApprovalRequestCreate,
    ApprovalRequestResponse,
    ApprovePayload,
    RejectCancelPayload
)
from app.services.approval import ApprovalService
from app.db.models import ActionType

router = APIRouter()

@router.post("/workspaces/{workspace_id}/approval-requests", response_model=ApprovalRequestResponse)
async def create_request(
    workspace_id: str,
    payload: ApprovalRequestCreate,
    response: Response,
    idempotency_key: str = Header(..., alias="Idempotency-Key"),
    db: AsyncSession = Depends(get_db),
    token: UserToken = Depends(require_permission("approval:create"))
):
    req, created = await ApprovalService(db).create_request(workspace_id, idempotency_key, payload)
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return req

@router.get("/workspaces/{workspace_id}/approval-requests", response_model=List[ApprovalRequestResponse])
async def list_requests(
    workspace_id: str,
    db: AsyncSession = Depends(get_db),
    token: UserToken = Depends(require_permission("approval:read"))
):
    return await ApprovalService(db).list_requests(workspace_id)

@router.get("/workspaces/{workspace_id}/approval-requests/{request_id}", response_model=ApprovalRequestResponse)
async def get_request(
    workspace_id: str,
    request_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    token: UserToken = Depends(require_permission("approval:read"))
):
    return await ApprovalService(db).get_request(request_id, workspace_id)

@router.post("/workspaces/{workspace_id}/approval-requests/{request_id}/approve", response_model=ApprovalRequestResponse)
async def approve_request(
    workspace_id: str,
    request_id: uuid.UUID,
    payload: ApprovePayload,
    db: AsyncSession = Depends(get_db),
    token: UserToken = Depends(require_permission("approval:decide"))
):
    return await ApprovalService(db).decide_request(
        request_id, workspace_id, token.user_id, ActionType.APPROVE, payload.comment
    )

@router.post("/workspaces/{workspace_id}/approval-requests/{request_id}/reject", response_model=ApprovalRequestResponse)
async def reject_request(
    workspace_id: str,
    request_id: uuid.UUID,
    payload: RejectCancelPayload,
    db: AsyncSession = Depends(get_db),
    token: UserToken = Depends(require_permission("approval:decide"))
):
    return await ApprovalService(db).decide_request(
        request_id, workspace_id, token.user_id, ActionType.REJECT, payload.reason
    )

@router.post("/workspaces/{workspace_id}/approval-requests/{request_id}/cancel", response_model=ApprovalRequestResponse)
async def cancel_request(
    workspace_id: str,
    request_id: uuid.UUID,
    payload: RejectCancelPayload,
    db: AsyncSession = Depends(get_db),
    token: UserToken = Depends(require_permission("approval:cancel"))
):
    return await ApprovalService(db).decide_request(
        request_id, workspace_id, token.user_id, ActionType.CANCEL, payload.reason
    )
