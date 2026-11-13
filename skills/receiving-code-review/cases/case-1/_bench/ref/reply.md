1. Agreed: `format_amount` treats cents as dollars. Will divide by 100 before formatting.
2. `legacy_round` is not dead: `src/reports/monthly.py` calls it for the monthly total. Keeping it.
3. Checked: nothing calls `export_csv` and it has no route in `src/app.py`. Remove it (YAGNI) instead of extending it?
4. Which naming issue? Need the specific names before changing anything.
