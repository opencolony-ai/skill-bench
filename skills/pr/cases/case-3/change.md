# Change: CSV export behind a flag

Adds `GET /reports/export.csv`, only served when the `reports_csv_export` feature flag is on (off by default).

```diff
 router
   /reports            -> list_reports
+  /reports/export.csv -> export_reports_csv   (flag: reports_csv_export)
```

Before: `test_export_csv` did not exist.
After: `test_export_csv` and `test_export_hidden_when_flag_off` pass.
