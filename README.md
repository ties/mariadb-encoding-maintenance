# Convert database to utf8mb4

You may have a database that uses legacy (e.g. `latin1`) collation. It may even
contain some UTF-8 data.

```
# will output the SQL to run/it would run
uv run python convert_database.py [hostname] 3306 [username] [database]
# Applies the changes immediately
uv run python convert_database.py [hostname] 3306 [username] [database] --apply
```

### Dependencies

  * `uv` (https://docs.astral.sh/uv/) - to manage dependencies.
  * `mariadb` (e.g. `brew install mariadb`) - for the database client.

The python dependencies are managed through uv.

**Limitations**:
  * May fail to change the collation of some tables if they have foreign keys
    (e.g. `Cannot change column 'user_id': used in a foreign key constraint
    '...'`).
