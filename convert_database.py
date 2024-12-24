"""
Convert a mariadb database to utf8mb4 encodings.

Changes:
    * schema collation.
    * character set and collation for every table.
"""

import logging
import os
from pathlib import Path
from typing import Optional

import click
import mariadb


@click.command()
@click.argument("hostname")
@click.argument("port", type=int)
@click.argument("username")
@click.argument("database", type=str)
@click.option("-v", "--verbose", count=True, help="Increase verbosity level.")
@click.option(
    "--apply",
    is_flag=True,
    show_default=True,
    default=False,
    help="Apply changes to database immediately",
)
@click.option(
    "--prelude-sql",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to optional SQL prelude file.",
)
@click.option(
    "--fixup-sql",
    type=click.Path(exists=True, path_type=Path),
    default=None,
    help="Path to optional SQL to execute after main changes (e.g. re-add foreign keys).",
)
@click.password_option(confirmation_prompt=False, default=os.environ.get("DB_PASSWORD"))
def main(
    hostname: str,
    port: int,
    database: str,
    username: Optional[str] = None,
    password: Optional[str] = None,
    verbose: int = 0,
    apply: bool = False,
    prelude_sql: Optional[Path] = None,
    fixup_sql: Optional[Path] = None,
):
    if verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)

    conn = mariadb.connect(
        user=username, password=password, host=hostname, port=port, database=database
    )
    # Disable autocommit. This is likely a NOOP, the DDL statements (ALTER) will implicitly commit.
    conn.autocommit = False
    cur = conn.cursor()

    prepared_sql = []

    def exec_if_not_prepare(sql):
        if apply:
            click.echo(f"SQL: {sql}")
            cur.execute(sql)
        else:
            prepared_sql.append(sql)

    # Using transactions does not avoid the issue with tables failing due to foreign key contraints
    click.echo(
        click.style(f"Changing {database} collation to utf8mb4_general_ci", bold=True)
    )
    cur.execute("SHOW TABLES")

    tables = [row[0] for row in cur]
    failed_tables = []

    if prelude_sql:
        with prelude_sql.open("r", encoding="utf-8") as f:
            for line in f.readlines():
                if line.strip() and not line.startswith("--"):
                    exec_if_not_prepare(line)

    exec_if_not_prepare(
        f"ALTER SCHEMA {database} DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;"
    )
    # _should_ prevent inserts while this runs.
    exec_if_not_prepare(
        "LOCK TABLES {}".format(",".join(f"{table} WRITE" for table in tables))
    )
    # does not prevent errors due to foreign keys.
    exec_if_not_prepare("SET SESSION FOREIGN_KEY_CHECKS = 0;")

    if apply:
        exec_if_not_prepare("SELECT @@FOREIGN_KEY_CHECKS;")
        click.echo(
            click.style(f"@@FOREIGN_KEY_CHECKS: {cur.fetchone()[0]}", fg="yellow")
        )

    for table_name in tables:
        click.echo(
            click.style(
                f"Setting table {table_name} collation to utf8mb4_general_ci",
                fg="green",
            )
        )
        try:
            exec_if_not_prepare(
                f"ALTER TABLE {table_name} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;"
            )
        except mariadb.OperationalError as e:
            click.echo(click.style(f"ERROR: {e}", fg="red"))
            failed_tables.append(table_name)

    click.echo(click.style("Failed tables:", bold=True))
    for table in failed_tables:
        click.echo(click.style(f"    - {table}", fg="red"))

    if fixup_sql:
        with fixup_sql.open("r", encoding="utf-8") as f:
            for line in f.readlines():
                if line.strip() and not line.startswith("--"):
                    exec_if_not_prepare(line)

    exec_if_not_prepare("SET SESSION FOREIGN_KEY_CHECKS = 1")
    exec_if_not_prepare("UNLOCK TABLES")
    # UNLOCK TABLES implicitly would commit

    if not apply:
        click.echo("=" * 72)
        click.echo("\n".join(prepared_sql))


if __name__ == "__main__":
    main()
