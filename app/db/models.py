import uuid
from datetime import datetime, timezone
from enum import Enum as PyEnum
from typing import List, Optional
from sqlalchemy import String, Enum, ForeignKey, JSON, DateTime, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base

def utc_now() -> datetime:
    return datetime.now(timezone.utc).replace(tzinfo=None)

class RequestStatus(str, PyEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELED = "CANCELED"

class ActionType(str, PyEnum):
    APPROVE = "Approve"
    REJECT = "Reject"
    CANCEL = "Cancel"

class ApprovalRequest(Base):
    __tablename__ = "approval_requests"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    workspace_id: Mapped[str] = mapped_column(String(255), index=True)
    source_type: Mapped[str] = mapped_column(String(100))
    source_id: Mapped[str] = mapped_column(String(255))
    title: Mapped[str] = mapped_column(String(255))
    description: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    reviewer_user_ids: Mapped[List[str]] = mapped_column(JSON)
    status: Mapped[RequestStatus] = mapped_column(
        Enum(RequestStatus, name="requeststatus", native_enum=False),
        default=RequestStatus.PENDING
    )
    idempotency_key: Mapped[str] = mapped_column(String(255), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now, onupdate=utc_now)

    logs: Mapped[List["ApprovalLog"]] = relationship(
        back_populates="request",
        cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("workspace_id", "idempotency_key", name="uq_workspace_idempotency_key"),
    )

class ApprovalLog(Base):
    __tablename__ = "approval_logs"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    request_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("approval_requests.id", ondelete="CASCADE"),
        index=True
    )
    actor_user_id: Mapped[str] = mapped_column(String(255))
    action: Mapped[ActionType] = mapped_column(Enum(ActionType, name="actiontype", native_enum=False))
    comment_or_reason: Mapped[Optional[str]] = mapped_column(String(1000), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utc_now)

    request: Mapped[ApprovalRequest] = relationship(back_populates="logs")
