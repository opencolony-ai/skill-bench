# Change: one button component

The three button styles (`.btn-primary`, `.btn-cta`, `.button-main`) are replaced by one `<Button variant>` component. No visual change intended.

```diff
-<a class="btn-cta" href="/signup">Sign up</a>
+<Button variant="primary" href="/signup">Sign up</Button>
```

Before: visual regression suite, 0 diffs on 64 screenshots (baseline).
After: visual regression suite, 0 diffs on 64 screenshots.
