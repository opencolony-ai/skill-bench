## Summary

```diff
 users
   email
-  legacy_email   (copied into email, then dropped)
```

## Evidence

- **Before:** `test_login_uses_email` fails for 212 users
  **After:** 418 passed

## Merge Danger

**Door:** one-way

The downgrade cannot restore `legacy_email`.

**Blast Radius:** user accounts
