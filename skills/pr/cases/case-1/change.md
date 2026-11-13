# Change: drop `users.legacy_email`

Migration `0042_drop_legacy_email.py` copies any `legacy_email` that is still set into `email`, then drops the `legacy_email` column. The code that read the column is removed.

```diff
+def upgrade():
+    op.execute("UPDATE users SET email = legacy_email WHERE email IS NULL AND legacy_email IS NOT NULL")
+    op.drop_column("users", "legacy_email")
+
+def downgrade():
+    raise NotImplementedError("legacy_email values are not kept")
```

Test run before: `test_login_uses_email` failed for 212 fixture users whose only address was in `legacy_email`.
Test run after: 418 passed.
