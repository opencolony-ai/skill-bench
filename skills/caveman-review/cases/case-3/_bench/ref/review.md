L4: 🔴 bug: mutable default `overrides={}` is shared, and L11 writes into it. Default to `None`, copy inside.
L8: 🟡 risk: `except Exception` hides a broken settings file. Catch `FileNotFoundError` only.
