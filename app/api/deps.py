from fastapi import Header, HTTPException, status, Path, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import SessionLocal
from app.schemas.auth import UserToken
import json

async def get_db():
    """
    Yields an AsyncSession for database operations.
    """
    async with SessionLocal() as session:
        yield session

async def get_current_user(
    x_mock_auth: str = Header(..., alias="X-Mock-Auth")
) -> UserToken:
    """
    Parses and validates the mock auth header.
    """
    try:
        data = json.loads(x_mock_auth)
        return UserToken(**data)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Mock-Auth header."
        )

def require_permission(required_permission: str):
    """
    Dependency factory to check user workspace isolation and permission levels.
    """
    async def dependency(
        token: UserToken = Depends(get_current_user),
        workspace_id: str = Path(...)
    ) -> UserToken:
        if token.workspace_id != workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Workspace ID mismatch."
            )
        if required_permission not in token.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions."
            )
        return token
    return dependency
