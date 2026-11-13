# New file: `greet.js`

```
 1  async function loadUser(id) {
 2    const res = fetch(`/api/users/${id}`);
 3    if (!res.ok) {
 4      throw new Error("load failed");
 5    }
 6    return res.json();
 7  }
 8
 9  function displayName(user) {
10    return user.firstName + " " + user.lastName;
11  }
12
13  async function greet(id) {
14    const user = await loadUser(id);
15    const el = document.getElementById("greeting");
16    el.textContent = "Hello, " + displayName(user);
17  }
```
