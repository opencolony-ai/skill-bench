1. `retry()` in `src/net/retry.js` retries immediately; there is no delay between attempts.
2. `isMissing` in `src/util/check.js` uses `==`. Always use `===`: change it to `v === null`.
3. `fetchLegacyRates` in `src/rates/legacy.js` needs a caching layer with TTL and LRU eviction.
4. And the thing in utils, same as last time.
