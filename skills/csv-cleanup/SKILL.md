---
name: csv-cleanup
description: Clean customer CSV exports by this team's data rules. Use whenever you clean, normalise or deduplicate a customer CSV.
---
# Customer CSV rules

- Trim spaces around every field; collapse runs of spaces inside names to one space.
- Emails: lowercase. Drop rows with an empty email.
- Dates in exports are day-first: `DD/MM/YYYY` or `DD-MM-YYYY` (some are already `YYYY-MM-DD`).
  Write every date as `YYYY-MM-DD`.
- Phones to E.164: keep digits only; a number that started with `+` keeps the `+`; a number
  starting with `0` becomes `+886` followed by the digits without that `0`; any other number
  gets `+886` in front.
- Duplicates are rows with the same email (after lowercasing and trimming). Keep the one with
  the latest `updated_at`; on a tie keep the first.
- Output columns: `id,name,email,phone,signup_date,updated_at`, sorted by `id` as a number.
- Also write `cleanup_log.json`:
  `{"input_rows": n, "dropped_no_email": n, "duplicates_removed": n, "output_rows": n}`
