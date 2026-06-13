# Sentinel API

A lightweight honeypot canary token service built with **FastAPI**. Provision fake URLs or AWS-style credentials, deploy them as tripwires in your environments, and get alerted when an unauthorized party interacts with them.

---

## What it does

1. **Generate** decoy tokens (`http`, `https`, or `aws` format)
2. **Deploy** the returned payload in configs, repos, or secret stores
3. **Detect** when someone triggers the tripwire
4. **Alert** you via email (Resend) with attacker IP, user agent, and timestamp

Token state and rate limiting are backed by **Redis**.

---

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Create a `.env` file with at least:

```env
DOMAIN=http://127.0.0.1:8000
RESEND_API_KEY=your_resend_api_key
REDIS_HOST=localhost
REDIS_PORT=6379
```

Start Redis, then run the API:

```bash
uvicorn main:app --reload
```

Verify it is running:

```bash
curl http://127.0.0.1:8000/
```

For full setup steps, environment variables, and Redis verification, see the [Setup Guide](DOCS/setup-guide.md).

---

## Documentation

| Document | Description |
|----------|-------------|
| [Architecture](DOCS/architecture.md) | System design, project structure, FastAPI and Redis roles, request flow from token generation to trigger interception |
| [API Reference](DOCS/api-reference.md) | Endpoint specifications — methods, request/response examples, status codes, and lifecycle roles |
| [Setup Guide](DOCS/setup-guide.md) | Environment configuration, local execution, Redis connectivity checks, and troubleshooting |
| [Design Decisions](DOCS/design-decisions.md) | Engineering rationale — `BackgroundTasks`, token validation, honeypot deception strategy, and more |

---

## API overview

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `POST` | `/canary/generate-token` | Create a new canary token |
| `GET` | `/canary/fetch/id/{token_id}` | Retrieve token by UUID |
| `GET` | `/canary/fetch/name/{name}` | Retrieve token by name |
| `GET` | `/canary/trigger/{token_id}` | Honeypot tripwire (attacker-facing) |
| `DELETE` | `/canary/delete/id/{token_id}` | Delete token by UUID |
| `DELETE` | `/canary/delete/name/{token_name}` | Delete token by name |

Interactive OpenAPI docs: `http://127.0.0.1:8000/docs` (when the server is running).

See [API Reference](DOCS/api-reference.md) for full request bodies, response shapes, and error codes.

---

## Tech stack

- [FastAPI](https://fastapi.tiangolo.com/) — HTTP API framework
- [Redis](https://redis.io/) — Token storage, name indexing, rate limiting
- [Resend](https://resend.com/) — Breach notification emails
- [Pydantic](https://docs.pydantic.dev/) — Request and storage model validation
- [Uvicorn](https://www.uvicorn.org/) — ASGI server

---

## Project structure

```text
sentinel-api/
├── main.py                 # Application entry point
├── config.py               # Redis client and rate limiter
├── models/                 # Pydantic models
├── routes/                 # API route modules
├── logger_config/          # Logging setup
├── DOCS/                   # Project documentation
└── requirements.txt
```

---

## License

See repository settings for license information.
