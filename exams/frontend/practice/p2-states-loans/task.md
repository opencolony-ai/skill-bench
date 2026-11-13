# My loans

Build `index.html` in this folder: the "My loans" page of the Fernhill Reading Room's members' site, where a
member sees the books they have borrowed. Most members are retired and use a phone.

- Read the loans from `data.js` (it sets `window.LOANS`; include it with `<script src="data.js"></script>`), and
  show every loan: title, author and due date. Treat 2026-11-20 as today.
- Mark a loan whose due date is before today with the word "Overdue". List the loans by due date, soonest first.
- Above the list, say how many there are: "1 book on loan", "5 books on loan".
- When there are none, show exactly "You have no books on loan."
- If `window.LOANS_ERROR` is set, show "We couldn't load your loans. Please try again later." instead of the list.
- Some records have no author; some titles are very long. The page must still work on a 320 px wide phone.
- One self-contained page (CSS and JavaScript inside it, no network). Write only `index.html`; leave `data.js` as it is.
