# Plan: move from MySQL to Postgres

- Weekend cutover: stop writes Saturday 02:00, dump, restore into Postgres, point the app at it.
- The ORM hides most differences; we fix whatever breaks in the first week.
- Reporting jobs keep reading from the old MySQL replica for a month.
- Rollback: point the app back at MySQL.
