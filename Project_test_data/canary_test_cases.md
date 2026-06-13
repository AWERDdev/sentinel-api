# Sentinel Canary API Documentation

Complete API router reference documentation configured for development environments.

* **Base URL:** `http://localhost:8000`
* **Prefix path:** `/canary`

---

## 1. System Health Check

### Welcome Endpoint
Verifies that the API instance and global rate-limiter configurations are fully functional.

* **URL:** `http://localhost:8000/canary/`
* **Method:** `GET`
* **Headers:** None

#### Example Response (`200 OK`)
```json
{
  "message": "Welcome to canary route this is where you create fetch your canary tokens"
}
2. Token Creation
Generate Canary Token
Validates incoming configurations, creates tracking fields, and generates defensive credentials before updating Redis storage.

URL: http://localhost:8000/canary/generate-token

Method: POST

Headers:

Content-Type: application/json

Example Request Body
JSON
{
  "token_type": "aws",
  "name": "Production Database Honey Key",
  "alert_email": "security@company.local"
}
Example Response (201 Created)
JSON
{
  "message": "your token has been generated successfully",
  "Canary_Token": "aws_access_key_id=AKIA_ABCD1234EFGH5678\naws_secret_access_key=fake_secret_abcd1234-efgh-5678-ijkl-90abcdef1234",
  "Token_ID": "{token_id}",
  "Token_Name": "Production Database Honey Key"
}
3. Data Retrieval & Token Inspection
Fetch Token By ID
Retrieves full object schemas directly from Redis storage using the primary tracking identifier.

URL: http://localhost:8000/canary/fetch/id/{token_id}

Method: GET

Headers: None

Example Response (200 OK)
JSON
{
  "token_ID": "{token_id}",
  "token_type": "aws",
  "name": "Production Database Honey Key",
  "alert_email": "security@company.local",
  "created_at": "2026-06-13T18:34:37.000Z",
  "is_active": true,
  "auth_string": "aws_access_key_id=AKIA_ABCD1234EFGH5678\naws_secret_access_key=fake_secret_...",
  "status": "ACTIVE",
  "breach_count": 0,
  "logs": []
}
Fetch Token By Name
Resolves descriptive names using a secondary lookup index pointer to fetch the full schema block.

URL: http://localhost:8000/canary/fetch/name/{name}

Method: GET

Headers: None

Example Path: http://localhost:8000/canary/fetch/name/Production Database Honey Key

Example Response (200 OK)
JSON
{
  "token_ID": "{token_id}",
  "token_type": "aws",
  "name": "Production Database Honey Key",
  "alert_email": "security@company.local",
  "created_at": "2026-06-13T18:34:37.000Z",
  "is_active": true,
  "auth_string": "aws_access_key_id=AKIA_ABCD1234EFGH5678\naws_secret_access_key=fake_secret_...",
  "status": "ACTIVE",
  "breach_count": 0,
  "logs": []
}
4. Incident Interception
Trigger Canary Tripwire
Intercepts interaction requests, extracts network client fingerprints, appends telemetry items to logs, and triggers asynchronous warning notifications via Resend.

🚨 Honeypot Logic: To maintain high deception metrics, this route returns a fake error block inside a valid 200 OK header response to deceive standard scanners.

URL: http://localhost:8000/canary/trigger/{token_id}

Method: GET

Headers: None

Deceptive Response (200 OK)
JSON
{
  "status": "error",
  "code": "INTERNAL_SERVER_ERROR",
  "message": "An unexpected error occurred while processing your request."
}
Example Error Response (404 Not Found)
JSON
{
  "detail": "Failed to find redis token"
}