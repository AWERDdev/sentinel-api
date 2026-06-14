# Test Fixtures

Sample payloads, request collections, and manual test scenarios for the Sentinel API. Use this folder during **local development** and **API testing** — not as production data.

---

## What's in this folder

| File | Format | Purpose |
|------|--------|---------|
| [`canary_generation_tests.json`](./canary_generation_tests.json) | Postman Collection v2.1 | Import into Postman (or compatible tools) to run health checks, successful token generation, and validation error cases against a running local server |
| [`canary_test_cases.md`](./canary_test_cases.md) | Markdown | Step-by-step manual test scenarios with example URLs, request bodies, and expected responses for the full canary lifecycle |
| [`canaryTokens.json`](./canaryTokens.json) | JSON array | Sample token generation responses (`Token_ID`, `Canary_Token`, etc.) for reference when building or debugging routes without calling the API repeatedly |

---

## Development testing

Use these fixtures while implementing or changing API behavior:

- **Request shapes** — Copy JSON bodies from `canary_generation_tests.json` or `canary_test_cases.md` into Swagger UI (`/docs`), `curl`, or your HTTP client to verify handlers and Redis writes.
- **Expected responses** — Compare live API output against examples in `canary_test_cases.md` and stored samples in `canaryTokens.json`.
- **Regression checks** — After code changes, re-run the Postman collection or manual cases to confirm generation, fetch, trigger, and delete flows still behave as documented.

Assumes the API is running locally at `http://127.0.0.1:8000` with Redis available. See the [Setup Guide](../DOCS/setup-guide.md) for environment configuration.

---

## API testing

### Postman collection

1. Start the API: `uvicorn main:app --reload`
2. In Postman: **Import** → select `canary_generation_tests.json`
3. Run the collection against `http://127.0.0.1:8000`

The collection includes:

- **Health Checks** — `GET /canary/`
- **Successful Token Generation** — `http`, `https`, and `aws` token types
- **Input Validation & Error Handling** — invalid `token_type`, malformed payloads, missing required fields

### Manual test cases

Open [`canary_test_cases.md`](./canary_test_cases.md) for documented flows:

- System health check
- Token creation (with real-world-style names and emails)
- Fetch by ID and by name
- Trigger tripwire (including the deceptive honeypot response)
- Error responses (`404`, validation failures)

Use these for exploratory testing, QA checklists, or onboarding new contributors.

### Sample token data

[`canaryTokens.json`](./canaryTokens.json) holds example **201 Created** responses from past runs. Useful when:

- Testing fetch/delete routes with known `Token_ID` values (after loading matching data into Redis, or after generating tokens with the same names)
- Documenting response field names and formats
- Debugging URL or AWS credential string formatting

> Token IDs in this file refer to historical dev runs. Generate fresh tokens for new test sessions unless you have intentionally seeded Redis with matching records.

---

## Suggested workflow

```text
1. Start Redis + API (see DOCS/setup-guide.md)
2. Import canary_generation_tests.json into Postman → run health + generation tests
3. Use canary_test_cases.md for fetch / trigger / delete manual passes
4. Compare responses with canaryTokens.json when validating response shape
```

For full endpoint specifications, see the [API Reference](../DOCS/api-reference.md).
