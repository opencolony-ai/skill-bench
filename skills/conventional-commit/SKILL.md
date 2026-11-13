---
name: conventional-commit
description: Write git commit messages in this team's convention. Use whenever you write or propose a commit message.
---
# Commit messages

1. Header: `<type>(<scope>): <subject>`. Types: feat, fix, docs, refactor, test, chore.
   The scope is the top-level directory of the changed source files (e.g. `api`, `web`);
   ignore `tests/`. If several, use the one with the most changed lines.
2. A breaking change (a public endpoint, field or function removed or renamed) adds `!`
   before the colon - `feat(api)!: ...` - and a footer line
   `BREAKING CHANGE: <what callers must change>`.
3. Subject: imperative mood, starts with a lowercase letter, no trailing period, at most 50 characters.
4. Then one blank line, then a body that says why, wrapped at 72 columns.
5. The last line is `Refs: <TICKET>`, the Jira key from the branch name
   (`feature/PAY-142-refunds` -> `PAY-142`).
6. Write only the message - no code fences, no commentary.
