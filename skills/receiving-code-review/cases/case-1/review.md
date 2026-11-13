1. `src/billing/invoice.py`: `format_amount` formats cents as if they were dollars (`1999` prints as `1999.00`).
2. `legacy_round` in `src/billing/invoice.py` is dead code. Please delete it.
3. `export_csv` in `src/admin/export.py` should be implemented properly: pagination, date filters and gzip output.
4. Also fix the naming issue we talked about.
