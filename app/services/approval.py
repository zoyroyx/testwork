import uuid
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.models import ApprovalRequest, ApprovalLog, RequestStatus, ActionType
from app.repositories.approval import ApprovalRepository
from app.schemas.approval import ApprovalRequestCreate
from app.exceptions import (
    ApprovalNotFoundError,
    InvalidStateTransitionError,
    IdempotencyKeyConflictError
)

class ApprovalService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.repo = ApprovalRepository(session)

    async def create_request(
        self,
        workspace_id: str,
        idempotency_key: str,
        payload: ApprovalRequestCreate
    ) -> tuple[ApprovalRequest, bool]:
        """
        Create a new approval request or return an existing one if the idempotency key matches.
        Returns tuple: (ApprovalRequest, is_created)
        Ensures a single atomic transaction is used.
        """
        async with self.session.begin():
            existing = await self.repo.get_by_idempotency_key(workspace_id, idempotency_key)
            if existing:
                # Check if the payload matches the existing request
                if (
                    existing.source_type != payload.source_type or
                    existing.source_id != payload.source_id or
                    existing.title != payload.title or
                    existing.reviewer_user_ids != payload.reviewer_user_ids
                ):
                    raise IdempotencyKeyConflictError(
                        "An approval request already exists with this idempotency key but different data."
                    )
                return existing, False

            new_request = ApprovalRequest(
                workspace_id=workspace_id,
                source_type=payload.source_type,
                source_id=payload.source_id,
                title=payload.title,
                description=payload.description,
                reviewer_user_ids=payload.reviewer_user_ids,
                status=RequestStatus.PENDING,
                idempotency_key=idempotency_key
            )
            created = await self.repo.create(new_request)

        return created, True

    async def get_request(self, request_id: uuid.UUID, workspace_id: str) -> ApprovalRequest:
        """
        Retrieve an approval request. Raises ApprovalNotFoundError if not found.
        """
        existing = await self.repo.get_by_id(request_id, workspace_id)
        if not existing:
            raise ApprovalNotFoundError("Approval request not found.")
        return existing

    async def list_requests(self, workspace_id: str) -> List[ApprovalRequest]:
        """
        List all approval requests in a workspace.
        """
        return await self.repo.get_list(workspace_id)

    async def decide_request(
        self,
        request_id: uuid.UUID,
        workspace_id: str,
        actor_user_id: str,
        action: ActionType,
        comment_or_reason: Optional[str]
    ) -> ApprovalRequest:
        """
        Transition the state of a request and log the action in a single atomic transaction.
        """
        async with self.session.begin():
            request = await self.repo.get_by_id(request_id, workspace_id)
            if not request:
                raise ApprovalNotFoundError("Approval request not found.")

            # Validate State Machine: can only transition from PENDING
            if request.status != RequestStatus.PENDING:
                raise InvalidStateTransitionError(
                    f"Cannot change status from {request.status} to {action}."
                )

            # Apply status transition
            if action == ActionType.APPROVE:
                request.status = RequestStatus.APPROVED
            elif action == ActionType.REJECT:
                request.status = RequestStatus.REJECTED
            elif action == ActionType.CANCEL:
                request.status = RequestStatus.CANCELED

            # Add to audit log
            log = ApprovalLog(
                request_id=request.id,
                actor_user_id=actor_user_id,
                action=action,
                comment_or_reason=comment_or_reason
            )
            await self.repo.create_log(log)

            # Publish event hook
            self.publish_event(request)

        return request

    def publish_event(self, request: ApprovalRequest) -> None:
        """
        Stub function for publishing state transition events to a message broker (e.g. Kafka/RabbitMQ).
        In production, utilize the Transactional Outbox pattern by writing events to an outbox table
        in the same transaction, then publishing them via a separate publisher process.
        """
        pass
