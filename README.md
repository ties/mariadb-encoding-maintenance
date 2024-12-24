# Convert database to utf8mb4

You may have a database that uses legacy (e.g. `latin1`) collation. It may even
contain some UTF-8 data.

**This may fail on foreign keys.** In that case, drop the foreign keys before
changing the encodings. You can supply a SQL file to execute before/after the
conversion.

```
# will output the SQL to run/it would run
uv run python convert_database.py [hostname] 3306 [username] [database]
# Applies the changes immediately
uv run python convert_database.py [hostname] 3306 [username] [database] --apply
# If you need to execute SQL before/after the conversion:
DB_PASSWORD=[password] uv run python convert_database.py [host] [port] [username] [database] --apply --prelude-sql prelude.sql --fixup-sql fixup.sql
```

### Example of prelude + fixup:
```
--- prelude.sql
alter table rawdata_rawdataquerylog DROP CONSTRAINT IF EXISTS `rawdata_rawdataquery_uuid_027ef6fb_fk`;
--- fixup.sql
alter table rawdata_rawdataquerylog add CONSTRAINT `rawdata_rawdataquery_uuid_027ef6fb_fk` FOREIGN KEY (`uuid`) REFERENCES `user` (`uuid`);
```

### Dependencies

  * `uv` (https://docs.astral.sh/uv/) - to manage dependencies.
  * `mariadb` (e.g. `brew install mariadb`) - for the database client.

The python dependencies are managed through uv.

**Limitations**:
  * May fail to change the collation of some tables if they have foreign keys
    (e.g. `Cannot change column 'user_id': used in a foreign key constraint
    '...'`).
