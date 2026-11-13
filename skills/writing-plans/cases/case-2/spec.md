# Spec: API rate limiting

Add rate limiting to our Express API.

- Each API key may make at most 100 requests per rolling 60 seconds.
- Over the limit, respond with HTTP 429 and a `Retry-After` header in whole seconds.
- Requests without an API key are limited per client IP at 20 requests per 60 seconds.
- Limits live in memory (one process); no Redis.
- Health checks (`GET /healthz`) are never limited.

Project-wide: TypeScript, Node 20, tests with vitest.
