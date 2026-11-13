❓ **Q1** - **Writes after cutover**: Once Postgres takes writes, MySQL falls behind. Do we accept that rollback after Saturday loses Postgres-only writes?

➡️ Yes: rollback only within the cutover window, before writes resume.

---

❓ **Q2** - **Reporting on stale data**: Reports read the old MySQL replica for a month, which stops changing at cutover. Is a frozen month of reports acceptable?

➡️ No: move reporting in the same weekend, read-only on Postgres.

---

❓ **Q3** - **Rehearsal**: Do we rehearse the dump and restore on a production-size copy before the real weekend?

➡️ Yes: one full rehearsal, timed, the week before.
