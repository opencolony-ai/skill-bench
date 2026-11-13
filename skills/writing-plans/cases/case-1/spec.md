# Spec: short links

We need a small URL shortener inside our Python service.

- `shorten(url: str) -> str` returns a code of exactly 7 characters from the alphabet
  `23456789abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ` (no 0, 1, O, I or l).
- `resolve(code: str) -> str | None` returns the original URL, or None for an unknown code.
- Codes and URLs are stored in the SQLite file `links.db`.
- On a collision, generate a new code; give up with `ShortenError` after 3 attempts.
- Shortening the same URL twice returns the same code.

Project-wide: Python 3.11 or newer, standard library only (no new dependencies).
