L2: 🔴 bug: `fetch` not awaited, so `res.ok` is always undefined and every call throws. `await fetch(...)`.
L15-16: 🟡 risk: `el` is null when #greeting is missing. Guard before `.textContent`.
