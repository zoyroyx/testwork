from typing import List
from pydantic import BaseModel, Field

class UserToken(BaseModel):
    user_id: str
    workspace_id: str
    permissions: List[str] = Field(default_factory=list)
