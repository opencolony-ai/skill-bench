# Rate limiting plan

## Steps
- Add a middleware that counts requests per key (100/60s)
- Return 429 with Retry-After
- Write tests
