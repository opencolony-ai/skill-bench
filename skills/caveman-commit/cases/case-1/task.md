# Commit message

Write a commit message for the change below. It fixes issue #214 (checkout crashed when a cart had no coupon).

Save the message to `COMMIT_MSG` in this folder.

```diff
diff --git a/shop/cart.py b/shop/cart.py
--- a/shop/cart.py
+++ b/shop/cart.py
@@ -18,7 +18,7 @@ def cart_total(cart):
     subtotal = sum(line.price * line.qty for line in cart.lines)
-    discount = subtotal * cart.coupon.percent / 100
+    discount = subtotal * cart.coupon.percent / 100 if cart.coupon else 0
     return round(subtotal - discount, 2)
diff --git a/tests/test_cart.py b/tests/test_cart.py
--- a/tests/test_cart.py
+++ b/tests/test_cart.py
@@ -40,3 +40,7 @@ def test_total_with_coupon():
+
+def test_total_without_coupon():
+    cart = make_cart(lines=[("pen", 2.5, 4)], coupon=None)
+    assert cart_total(cart) == 10.0
```
