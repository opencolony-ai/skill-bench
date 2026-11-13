# New file: `settings.py`

```
 1  import json
 2
 3
 4  def load_settings(path, overrides={}):
 5      try:
 6          with open(path) as f:
 7              data = json.load(f)
 8      except Exception:
 9          data = {}
10      data.update(overrides)
11      overrides["loaded"] = True
12      return data
```
