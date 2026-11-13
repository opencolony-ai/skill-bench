# Commit message

Write the commit message for the change below.

Branch: `feature/API-310-rename-customer-id`

Save the message to `COMMIT_MSG` in this folder.

```diff
diff --git a/api/serializers.py b/api/serializers.py
--- a/api/serializers.py
+++ b/api/serializers.py
@@ -20,9 +20,8 @@ def order_to_json(order):
     return {
         "id": order.id,
-        "customerId": order.customer_id,
+        "customer_id": order.customer_id,
         "total": str(order.total),
-        "createdAt": order.created_at.isoformat(),
+        "created_at": order.created_at.isoformat(),
     }
diff --git a/docs/api.md b/docs/api.md
--- a/docs/api.md
+++ b/docs/api.md
@@ -40,2 +40,2 @@
-| customerId | string | |
+| customer_id | string | |
```
