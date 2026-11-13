# Spec: contact import

A command-line tool, `import-contacts <file.csv>`, loads contacts into our address book.

- Columns: `name,email,phone`. `email` is required; rows without one are rejected and listed in the report.
- Duplicates are detected by lowercased email; the first row wins.
- At most 10,000 rows per file; larger files are refused before anything is imported.
- At the end, print `imported N, duplicates D, rejected R`.

Project-wide: Go 1.22, no third-party modules.
