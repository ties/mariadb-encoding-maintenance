# Convert database to utf8mb4

You may have a database that uses legacy (e.g. `latin1`) collation. It may even
contain some UTF-8 data.

```
uv run python convert_database.py [hostname] 3306 [username] [database]
```
