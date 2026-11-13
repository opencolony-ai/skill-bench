# Library lending: terms

After a long argument:

- **Title**: a work in the catalogue (one ISBN). Avoid "book" for this.
- **Copy**: one physical item of a title that can be lent. Not "item", not "volume".
- **Loan**: a copy lent to a member until a due date. Avoid "checkout" and "borrowing".
- **Hold**: a member's claim on the next free copy of a title. Avoid "reservation" and "request".
- **Member**: someone with a library card. Not "patron", not "user".

Implementation aside: the loans list uses cursor pagination and the API has a rate limit of 60/min.
