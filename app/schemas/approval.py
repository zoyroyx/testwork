from datetime import datetime
from typing import List, Optional
import uuid
from pydantic import BaseModel, Field, ConfigDict
from app.db.models import RequestStatus

class BaseSchema(BaseModel):
    model_config = ConfigDict(
        populate_by_name=True,
        from_attributes=True
    )

class ApprovalRequestCreate(BaseSchema):
    source_type: str = Field(alias="sourceType")
    source_id: str = Field(alias="sourceId")
    title: str = Field(min_length=1, max_length=255)
    description: Optional[str] = Field(default=None, max_length=1000)
    reviewer_user_ids: List[str] = Field(alias="reviewerUserIds")

class ApprovalRequestResponse(BaseSchema):
    id: uuid.UUID
    workspace_id: str = Field(alias="workspaceId")
    source_type: str = Field(alias="sourceType")
    source_id: str = Field(alias="sourceId")
    title: str
    description: Optional[str]
    reviewer_user_ids: List[str] = Field(alias="reviewerUserIds")
    status: RequestStatus
    idempotency_key: str = Field(alias="idempotencyKey")
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")

class ApprovePayload(BaseSchema):
    comment: Optional[str] = Field(default=None, max_length=1000)

class RejectCancelPayload(BaseSchema):
    reason: Optional[str] = Field(default=None, max_length=1000)
