# Convert database to utf8mb4

You may have a database that uses legacy (e.g. `latin1`) collation. It may even
contain some UTF-8 data.

This script requires [uv](https://docs.astral.sh/uv/) to be installed to manage dependencies as well as `mariadb` (e.g. `brew install mariadb`).

```
uv run python convert_database.py [hostname] 3306 [username] [database]
```

**Limitations**:
  * May fail to change the collation of some tables if they have foreign keys
    (e.g. `Cannot change column 'user_id': used in a foreign key constraint
    '...'`).
