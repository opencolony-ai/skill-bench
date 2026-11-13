1. Agreed: the f-string allows SQL injection. Will pass `email` as a parameter.
2. `pyproject.toml` still declares `requires-python = ">=3.8"`, so the 3.8 branch is needed. Drop 3.8 support first, or keep it?
3. `legacy_stats` has no route in `src/router.py`; nothing reaches it. Remove it (YAGNI)?
4. Which config? Need the file and what you want changed.
