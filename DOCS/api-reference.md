# Sentinel API — API Reference

Base URL (local default): `http://127.0.0.1:8000`

Most canary routes share the prefix `/canary`. All endpoints listed below (except root) are rate-limited via the shared `ratelimiter` dependency.

---

## Summary Table

| Method | Path | Status (success) | Lifecycle role |
|--------|------|------------------|----------------|
| `GET` | `/` | 200 | API health / welcome |
| `GET` | `/canary/docs` | 200 | Project documentation pointer |
| `GET` | `/canary/` | 200 | Canary module health check |
| `POST` | `/canary/generate-token` | 201 | **Provision** a new honeypot token |
| `GET` | `/canary/fetch/id/{token_id}` | 200 | **Inspect** token by UUID |
| `GET` | `/canary/fetch/name/{name}` | 200 | **Inspect** token by human-readable name |
| `GET` | `/canary/trigger/{token_id}` | 200* | **Intercept** unauthorized access (honeypot) |
| `DELETE` | `/canary/delete/id/{token_id}` | 200 | **Retire** token by UUID |
| `DELETE` | `/canary/delete/name/{token_name}` | 200 | **Retire** token by name |

\* Trigger returns HTTP `200` with a deceptive error-shaped JSON body when processing completes successfully and `alert_email` is set. See [Trigger Canary](#get-canarytriggertoken_id).

---

## Root Endpoints

### `GET /`

**Lifecycle role:** Confirms the API process is running.

**Request body:** None

**Success response (200):**

```json
{
  "message": "welcome to canary token generator API"
}
```

---

### `GET /canary/docs`

**Lifecycle role:** Returns a static pointer to the project repository (not OpenAPI docs).

**Request body:** None

**Success response (200):**

```json
{
  "message": "Docs endpoint reached",
  "GitRepo": "https://github.com/AWERDdev/sentinel-api"
}
```

> FastAPI's built-in interactive OpenAPI UI is available at `/docs` (framework default), separate from this custom route.

---

## Canary Module Health

### `GET /canary/`

**Lifecycle role:** Health check for the `/canary` router group. Multiple route modules register this path; behavior is identical across them.

**Request body:** None

**Success response (200):**

```json
{
  "message": "Welcome to canary route this is where you create fetch your canary tokens"
}
```

---

## Token Generation

### `POST /canary/generate-token`

**Lifecycle role:** Creates a new canary token, persists it in Redis, and returns the decoy payload (`auth_string`) for the operator to deploy in their environment.

#### Request

**Headers:**

```http
Content-Type: application/json
```

**Body schema (`CanaryTokenCreate`):**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `token_type` | string | Yes | One of: `http`, `https`, `aws` (case-insensitive; trimmed) |
| `name` | string | Yes | Human-readable identifier; used for secondary Redis index |
| `alert_email` | string | Yes | Email address for breach notifications |

**Example — HTTP tripwire:**

```json
{
  "token_type": "http",
  "name": "Production Passwords File",
  "alert_email": "security@company.local"
}
```

**Example — AWS credential honeypot:**

```json
{
  "token_type": "aws",
  "name": "Production Database Honey Key",
  "alert_email": "security@company.local"
}
```

#### Success response (201 Created)

```json
{
  "message": "your token has been generated successfully",
  "Canary_Token": "http://127.0.0.1:8000/canary/trigger/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "Token_ID": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "Token_Name": "Production Passwords File"
}
```

For `token_type: "aws"`, `Canary_Token` is a multi-line fake credential block:

```json
{
  "message": "your token has been generated successfully",
  "Canary_Token": "aws_access_key_id=AKIA_A1B2C3D4E5F6789\naws_secret_access_key=fake_secret_a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "Token_ID": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "Token_Name": "Production Database Honey Key"
}
```

#### Error responses

| Status | Condition | Body |
|--------|-----------|------|
| `400` | Invalid `token_type` | `{"detail": "Invalid token type. Choose from: http, https, aws"}` |
| `422` | Missing/invalid JSON fields | Pydantic validation error detail |
| `429` | Rate limit exceeded | `{"detail": "Too many requests. Please try again later."}` |

#### Redis side effects

- `SET canary:token:{token_id}` → full `CanaryToken` JSON
- `SET canary:name:{normalized_name}` → `token_id`

---

## Token Retrieval

### `GET /canary/fetch/id/{token_id}`

**Lifecycle role:** Allows operators to audit a token's current state, including breach history after a trigger.

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `token_id` | UUID assigned at generation time |

**Request body:** None

**Success response (200):**

```json
{
  "token_ID": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "token_type": "http",
  "name": "Production Passwords File",
  "alert_email": "security@company.local",
  "created_at": "2026-06-13T18:34:37.123456",
  "is_active": true,
  "auth_string": "http://127.0.0.1:8000/canary/trigger/a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "ACTIVE",
  "breach_count": 0,
  "logs": []
}
```

After a trigger, `status` becomes `COMPROMISED`, `breach_count` increments, and `logs` contains attacker metadata.

**Error responses:**

| Status | Condition | Body |
|--------|-----------|------|
| `404` | Token not found | `{"detail": "canary token not found"}` |
| `429` | Rate limit exceeded | `{"detail": "Too many requests. Please try again later."}` |

---

### `GET /canary/fetch/name/{name}`

**Lifecycle role:** Resolves a token by its `name` field using the Redis name index, then returns the full token document.

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `name` | Token name as provided at creation (spaces allowed in URL path) |

**Request body:** None

**Example:** `GET /canary/fetch/name/Production%20Database%20Honey%20Key`

**Success response (200):** Same structure as fetch-by-ID.

**Error responses:**

| Status | Condition | Body |
|--------|-----------|------|
| `404` | Name index missing | `{"detail": "canary token name not found"}` |
| `404` | Index exists but token payload missing | `{"detail": "canary token payload data missing"}` |
| `429` | Rate limit exceeded | `{"detail": "Too many requests. Please try again later."}` |

---

## Trigger Interception (Honeypot)

### `GET /canary/trigger/{token_id}`

**Lifecycle role:** The tripwire endpoint. Invoked when someone accesses an embedded URL or otherwise hits the tracking link. Records attacker fingerprints, marks the token compromised, queues an email alert, and returns a **deceptive** success response so the intruder does not know they were detected.

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `token_id` | UUID from the generated tripwire URL or credential mapping |

**Request body:** None

**Headers read (for attribution):**

- `X-Forwarded-For` — first IP in the chain used if present
- `User-Agent` — stored in breach log; defaults to attribution logic if absent

#### Success response — deceptive (200 OK)

When the token exists and `alert_email` is set, the handler returns HTTP `200` with a body that **looks like an internal server error**:

```json
{
  "status": "error",
  "code": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected error occurred while processing your request."
}
```

This is intentional honeypot behavior: attackers and scanners see a plausible failure rather than a "token triggered" confirmation.

#### Error responses

| Status | Condition | Body |
|--------|-----------|------|
| `404` | Token not in Redis | `{"detail": "Failed to find redis token"}` |
| `500` | Unhandled exception during processing | `{"detail": "failed to trigger canary token"}` |
| `429` | Rate limit exceeded | `{"detail": "Too many requests. Please try again later."}` |

#### Side effects (on successful processing)

1. `status` → `"COMPROMISED"`
2. `breach_count` incremented by 1
3. New log entry: `{ "ip", "user_agent", "timestamp" }`
4. Updated document written to `canary:token:{token_id}`
5. `send_security_alert` queued via `BackgroundTasks` (if `alert_email` is present)

#### Email alert (background)

Subject: `🚨 BREACH DETECTED: {token_name}`

Contains: token name, attacker IP, user agent, UTC timestamp.

---

## Token Deletion

### `DELETE /canary/delete/id/{token_id}`

**Lifecycle role:** Permanently removes a canary token and its name index from Redis.

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `token_id` | UUID of the token to delete |

**Request body:** None

**Success response (200):**

```json
{
  "message": "Token with ID a1b2c3d4-e5f6-7890-abcd-ef1234567890 deleted successfully."
}
```

**Error responses:**

| Status | Condition | Body |
|--------|-----------|------|
| `404` | Token not found | `{"detail": "Canary token wasn't found"}` |
| `500` | Unexpected error | `{"detail": "Internal server error occurred during deletion"}` |
| `429` | Rate limit exceeded | `{"detail": "Too many requests. Please try again later."}` |

**Redis side effects:** Deletes `canary:token:{token_id}` and `canary:name:{normalized_name}`.

---

### `DELETE /canary/delete/name/{token_name}`

**Lifecycle role:** Deletes a token by resolving the name index first, then removing both Redis keys.

**Path parameters:**

| Parameter | Description |
|-----------|-------------|
| `token_name` | Human-readable name assigned at creation |

**Request body:** None

**Success response (200):**

```json
{
  "message": "Token 'Production Database Honey Key' deleted successfully."
}
```

**Error responses:**

| Status | Condition | Body |
|--------|-----------|------|
| `404` | Name index not found | `{"detail": "Canary token name index wasn't found"}` |
| `500` | Unexpected error | `{"detail": "Internal server error occurred during deletion"}` |
| `429` | Rate limit exceeded | `{"detail": "Too many requests. Please try again later."}` |

---

## Stored Token Schema (`CanaryToken`)

Documents persisted in Redis follow this shape:

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `token_ID` | string | — | UUID primary identifier |
| `token_type` | string | — | `http`, `https`, or `aws` |
| `name` | string | — | Operator-defined label |
| `alert_email` | string | — | Breach notification recipient |
| `created_at` | datetime (ISO) | UTC now | Creation timestamp |
| `is_active` | boolean | `true` | Active flag |
| `auth_string` | string \| null | `null` | Deployable decoy payload |
| `status` | string | `"ACTIVE"` | Becomes `"COMPROMISED"` after trigger |
| `breach_count` | integer | `0` | Number of trigger events |
| `logs` | array | `[]` | Breach log entries |

---

## Rate Limiting (All Endpoints)

When exceeded:

**Status:** `429 Too Many Requests`

```json
{
  "detail": "Too many requests. Please try again later."
}
```

Defaults: 5 requests per 60 seconds per client IP (configurable via `REDIS_MAX_REQUESTS` and `REDIS_WINDOW_SECONDS`).

---

## Typical Operator Workflow

```text
1. POST /canary/generate-token     → obtain Canary_Token + Token_ID
2. Deploy auth_string in environment
3. (Attacker) GET /canary/trigger/{id}  → breach logged, email sent
4. GET /canary/fetch/id/{id}       → review logs and status
5. DELETE /canary/delete/id/{id}   → cleanup when no longer needed
```
