# System Design - `approval-service`

## 1. Database Schema

The database uses PostgreSQL (Asyncpg) as the production driver. The schema contains two tables related with a foreign key and configured for cascade deletes:

### `approval_requests`
* `id` (UUID): Primary key, automatically generated using `uuid.uuid4`.
* `workspace_id` (String): Workspace identifier used for tenant isolation.
* `source_type` (String): Type of content (e.g. `ARTICLE`, `POST`).
* `source_id` (String): Target content identifier.
* `title` (String): Human-readable request title.
* `description` (String, nullable): Optional request details.
* `reviewer_user_ids` (JSON): List of user IDs assigned as reviewers.
* `status` (Enum/String): Current status (`PENDING`, `APPROVED`, `REJECTED`, `CANCELED`).
* `idempotency_key` (String): Client-provided token used to prevent duplicates.
* `created_at` (DateTime): Creation timestamp (UTC).
* `updated_at` (DateTime): Modification timestamp (UTC).

*Constraints:*
* Unique constraint on `(workspace_id, idempotency_key)` to ensure unique submissions per tenant.

### `approval_logs`
* `id` (UUID): Primary key.
* `request_id` (UUID): Foreign key referencing `approval_requests.id`.
* `actor_user_id` (String): User who performed the status transition.
* `action` (Enum/String): Transition type (`Approve`, `Reject`, `Cancel`).
* `comment_or_reason` (String, nullable): Optional remark.
* `created_at` (DateTime): Creation timestamp (UTC).

---

## 2. Idempotency Logic

To prevent duplicate creation from network retries or double-clicks:
1. Every creation request takes an `Idempotency-Key` header.
2. The database lookup retrieves any record matching `(workspace_id, idempotency_key)`.
3. If an existing record is found:
   - If the payload matches the database record exactly, the service returns the existing record with a **`200 OK`** response.
   - If the payload differs, the service raises an `IdempotencyKeyConflictError` which translates to a **`409 Conflict`** response.
4. If no record is found, the new request is successfully created and returns **`201 Created`**.

---

## 3. State Machine

The workflow uses a strict one-way state machine transitioning from the initial state:

```
          +------------+
          |  PENDING   |
          +------------+
           /    |     \
          /     |      \
         v      v       v
+----------+ +----------+ +----------+
| APPROVED | | REJECTED | | CANCELED |
+----------+ +----------+ +----------+
```

* **Valid Transitions:**
  * `PENDING` -> `APPROVED`
  * `PENDING` -> `REJECTED`
  * `PENDING` -> `CANCELED`
* **Invalid Transitions:**
  * Any transition out of `APPROVED`, `REJECTED`, or `CANCELED` is illegal and raises `InvalidStateTransitionError` (**`409 Conflict`**).

---

## 4. Event-Driven Architecture Readiness

To support asynchronous integrations (e.g. messaging with Kafka, RabbitMQ), a stub `publish_event` method is placed inside the service layer.

For full microservice resilience and delivery guarantees, it is recommended to implement the **Transactional Outbox Pattern**:
1. When a state change occurs, write an event payload to an `outbox_events` table in the database within the *same transaction*.
2. A separate background worker polls the `outbox_events` table, publishes them to the message broker, and deletes or marks them as processed upon acknowledgment.
3. This guarantees at-least-once delivery without affecting API latency or coupling transactions to external message broker health.
