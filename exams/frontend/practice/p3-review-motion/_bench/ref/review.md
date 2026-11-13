app.css:5 — `transition: all` animates every property, including colours and layout — list only `background-color 150ms ease-out`
app.css:12 — ease-in on an opening menu feels sluggish at the start — use ease-out, e.g. cubic-bezier(0.23, 1, 0.32, 1)
app.css:17 — the toast enters from scale(0), which looks like it pops out of nothing — start from scale(0.95) with opacity 0
app.css:24 — 800ms hover lift is far too slow for UI feedback — keep it under 200ms
app.css:28 — the command palette is opened from the keyboard many times a day; animating it only adds delay — remove the animation
