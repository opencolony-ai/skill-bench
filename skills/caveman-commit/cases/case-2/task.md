# Commit message

Write a commit message for the change below. Callers that still pass `timeout=` will break: the old keyword is gone.

Save the message to `COMMIT_MSG` in this folder.

```diff
diff --git a/client/http.py b/client/http.py
--- a/client/http.py
+++ b/client/http.py
@@ -9,11 +9,11 @@ class Client:
-    def __init__(self, base_url, timeout=30):
+    def __init__(self, base_url, timeout_ms=30_000):
         self.base_url = base_url
-        self.timeout = timeout
+        self.timeout = timeout_ms / 1000
diff --git a/docs/client.md b/docs/client.md
--- a/docs/client.md
+++ b/docs/client.md
@@ -3,3 +3,3 @@
-`Client(base_url, timeout=30)` - timeout in seconds.
+`Client(base_url, timeout_ms=30000)` - timeout in milliseconds.
```
