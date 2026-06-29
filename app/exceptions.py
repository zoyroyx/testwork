class DomainError(Exception):
    """Base domain exception for the business logic errors."""
    pass

class ApprovalNotFoundError(DomainError):
    """Raised when an approval request cannot be found."""
    pass

class InvalidStateTransitionError(DomainError):
    """Raised when a state machine transition is illegal."""
    pass

class IdempotencyKeyConflictError(DomainError):
    """Raised when an idempotency key is reused with mismatching parameters."""
    pass
