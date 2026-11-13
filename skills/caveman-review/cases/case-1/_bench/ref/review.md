L3: 🔴 bug: pages start at 1, so page 1 skips the first 20 items. Use `(page - 1) * per_page`.
L10: 🔴 bug: floor division drops a partial last page. Use `-(-n_items // per_page)`.
