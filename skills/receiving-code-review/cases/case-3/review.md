1. `find_user` in `src/db/users.py` builds SQL with an f-string. Use a query parameter.
2. Python 3.8 is long dead. Drop the `sys.version_info < (3, 9)` branch in `src/compat.py`.
3. The `legacy_stats` handler in `src/handlers/stats.py` should get proper auth, rate limiting and caching.
4. Please tidy up the config stuff too.
