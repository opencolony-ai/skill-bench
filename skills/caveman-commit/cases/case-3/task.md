# Commit message

Write a commit message for the change below. Measured on the 1M-line fixture: parsing went from 4.1 s to 2.6 s.

Save the message to `COMMIT_MSG` in this folder.

```diff
diff --git a/logs/parse.py b/logs/parse.py
--- a/logs/parse.py
+++ b/logs/parse.py
@@ -1,9 +1,11 @@
 import re
 
+LINE = re.compile(r"^(\S+) (\S+) \[(.*?)\] \"(.*?)\" (\d{3})")
+
 
 def parse_line(line):
-    m = re.compile(r"^(\S+) (\S+) \[(.*?)\] \"(.*?)\" (\d{3})").match(line)
+    m = LINE.match(line)
     if not m:
         return None
     return m.groups()
```
