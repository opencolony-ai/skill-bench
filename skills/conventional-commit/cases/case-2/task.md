# Commit message

Write the commit message for the change below.

Branch: `bugfix/AUTH-77-token-expiry`

Save the message to `COMMIT_MSG` in this folder.

```diff
diff --git a/web/auth/session.js b/web/auth/session.js
--- a/web/auth/session.js
+++ b/web/auth/session.js
@@ -12,7 +12,7 @@ export function isExpired(token) {
   const claims = decode(token);
-  return claims.exp < Date.now();
+  return claims.exp * 1000 < Date.now();
 }
diff --git a/tests/session.test.js b/tests/session.test.js
--- a/tests/session.test.js
+++ b/tests/session.test.js
@@ -3,0 +4,5 @@
+test("a token valid for another hour is not expired", () => {
+  const token = sign({ exp: Math.floor(Date.now() / 1000) + 3600 });
+  expect(isExpired(token)).toBe(false);
+});
```
