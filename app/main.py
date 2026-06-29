from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
import logging

from app.api.v1.endpoints import router as v1_router
from app.exceptions import (
    ApprovalNotFoundError,
    InvalidStateTransitionError,
    IdempotencyKeyConflictError
)

# Configure logger securely (no passwords, tokens, or emails logged)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("approval-service")

app = FastAPI(title="Approval Service", version="1.0.0")

@app.exception_handler(ApprovalNotFoundError)
async def approval_not_found_handler(request: Request, exc: ApprovalNotFoundError):
    logger.error(f"Approval not found: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={"detail": str(exc)}
    )

@app.exception_handler(InvalidStateTransitionError)
async def invalid_state_transition_handler(request: Request, exc: InvalidStateTransitionError):
    logger.error(f"Invalid state transition: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)}
    )

@app.exception_handler(IdempotencyKeyConflictError)
async def idempotency_key_conflict_handler(request: Request, exc: IdempotencyKeyConflictError):
    logger.error(f"Idempotency conflict: {str(exc)}")
    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={"detail": str(exc)}
    )

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.get("/ready")
async def ready_check():
    return {"status": "ready"}

app.include_router(v1_router, prefix="/api/v1")
