1. Correct: attempts run back to back. Will add a backoff between attempts.
2. Keeping `==`: `v == null` is true for `undefined` too, and `check.test.js` asserts `isMissing(undefined)`. `v === null` would break that.
3. Nothing imports `fetchLegacyRates`; `src/rates/index.js` exports only `fetchRates`. Delete it (YAGNI) rather than cache it?
4. Which change in utils do you mean? Point me at the file or line.
