## Summary

```diff
 router
   /reports            -> list_reports
+  /reports/export.csv -> export_reports_csv   (flag off by default)
```

## Evidence

- **Before:** no export endpoint
  **After:** `test_export_csv` and `test_export_hidden_when_flag_off` pass

## Merge Danger

**Door:** two-way

Turning the flag off removes it.

**Blast Radius:** reports
