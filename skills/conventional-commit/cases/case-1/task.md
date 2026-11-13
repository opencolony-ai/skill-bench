# Commit message

Write the commit message for the change below.

Branch: `feature/PAY-142-refund-endpoint`

Save the message to `COMMIT_MSG` in this folder.

```diff
diff --git a/api/refunds.py b/api/refunds.py
new file mode 100644
--- /dev/null
+++ b/api/refunds.py
@@ -0,0 +1,24 @@
+from flask import Blueprint, request, jsonify
+from .payments import find_payment, issue_refund
+
+bp = Blueprint("refunds", __name__)
+
+
+@bp.post("/refunds")
+def create_refund():
+    body = request.get_json()
+    payment = find_payment(body["payment_id"])
+    if payment is None:
+        return jsonify(error="unknown payment"), 404
+    if body["amount"] > payment.captured:
+        return jsonify(error="amount exceeds captured total"), 422
+    refund = issue_refund(payment, body["amount"], reason=body.get("reason"))
+    return jsonify(id=refund.id, status=refund.status), 201
diff --git a/tests/test_refunds.py b/tests/test_refunds.py
new file mode 100644
--- /dev/null
+++ b/tests/test_refunds.py
@@ -0,0 +1,9 @@
+def test_refund_over_captured_is_refused(client, captured_payment):
+    r = client.post("/refunds", json={"payment_id": captured_payment.id, "amount": 10_000})
+    assert r.status_code == 422
```
