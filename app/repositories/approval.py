from typing import Optional, List
import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.db.models import ApprovalRequest, ApprovalLog

class ApprovalRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_by_id(self, request_id: uuid.UUID, workspace_id: str) -> Optional[ApprovalRequest]:
        """
        Retrieve approval request by ID and workspace_id.
        Uses selectinload to eagerly load related logs to prevent N+1 queries.
        """
        stmt = (
            select(ApprovalRequest)
            .where(ApprovalRequest.id == request_id)
            .where(ApprovalRequest.workspace_id == workspace_id)
            .options(selectinload(ApprovalRequest.logs))
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_by_idempotency_key(self, workspace_id: str, idempotency_key: str) -> Optional[ApprovalRequest]:
        """
        Retrieve approval request by workspace_id and idempotency_key.
        """
        stmt = (
            select(ApprovalRequest)
            .where(ApprovalRequest.workspace_id == workspace_id)
            .where(ApprovalRequest.idempotency_key == idempotency_key)
        )
        result = await self.session.execute(stmt)
        return result.scalars().first()

    async def get_list(self, workspace_id: str) -> List[ApprovalRequest]:
        """
        List all approval requests for a given workspace_id.
        """
        stmt = (
            select(ApprovalRequest)
            .where(ApprovalRequest.workspace_id == workspace_id)
            .order_by(ApprovalRequest.created_at.desc())
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create(self, request: ApprovalRequest) -> ApprovalRequest:
        """
        Create a new approval request.
        """
        self.session.add(request)
        return request

    async def create_log(self, log: ApprovalLog) -> ApprovalLog:
        """
        Create a new audit log.
        """
        self.session.add(log)
        return log
