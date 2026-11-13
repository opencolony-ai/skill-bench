# New file: `pager.py`

```
 1  def paginate(items, page, per_page=20):
 2      """Return the items on page `page` (pages start at 1)."""
 3      start = page * per_page
 4      end = start + per_page
 5      return items[start:end]
 6
 7
 8  def total_pages(n_items, per_page=20):
 9      """How many pages `n_items` items fill."""
10      return n_items // per_page
```
