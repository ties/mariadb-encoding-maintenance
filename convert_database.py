"""
Convert a mariadb database to utf8mb4 encodings.

Changes:
    * schema collation.
    * character set and collation for every table.
"""

import logging

import os
from typing import Optional

import click
import mariadb


@click.command()
@click.argument('hostname')
@click.argument('port', type=int)
@click.argument('username')
@click.argument('database', type=str)
@click.option('-v', '--verbose', count=True, help="Increase verbosity level.")
@click.password_option(confirmation_prompt=False, default=os.environ.get('DB_PASSWORD'))
def main(hostname: str, port: int, database: str, username: Optional[str] = None, password: Optional[str] = None, verbose: int = 0):
    if verbose == 1:
        logging.basicConfig(level=logging.INFO)
    elif verbose >= 2:
        logging.basicConfig(level=logging.DEBUG)

    conn = mariadb.connect(
        user=username,
        password=password,
        host=hostname,
        port=port,
        database=database
    )
    conn.autocommit = False

    cur = conn.cursor()
    # Using transactions does not avoid the issue with tables failing due to foreign key contraints
    click.echo(click.style(f"Changing {database} collation to utf8mb4_general_ci", bold=True))
    cur.execute("SHOW TABLES")

    tables = [row[0] for row in cur]
    failed_tables = []

    cur.execute(f"ALTER SCHEMA {database} DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;")
    # _should_ prevent inserts while this runs.
    cur.execute("LOCK TABLES {}".format(",".join(f"{table} WRITE" for table in tables)))
    # does not prevent errors due to foreign keys.
    cur.execute("SET SESSION FOREIGN_KEY_CHECKS = 0;")

    cur.execute("SELECT @@FOREIGN_KEY_CHECKS;")
    click.echo(click.style(f"@@FOREIGN_KEY_CHECKS: {cur.fetchone()[0]}", fg="yellow"))

    for table_name in tables:
        click.echo(click.style(f"Changing table {table_name} collation to utf8mb4_general_ci", fg="green"))
        try:
            cur.execute(f"ALTER TABLE {table_name} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")
        except mariadb.OperationalError as e:
            click.echo(click.style(e, fg="red"))
            failed_tables.append(table_name)

    click.echo(click.style("Failed tables:", bold=True))
    for table in failed_tables:
        click.echo(click.style(f"    - {table}", fg="red"))

    cur.execute("SET SESSION FOREIGN_KEY_CHECKS = 1")
    cur.execute("UNLOCK TABLES")

    conn.commit()


if __name__ == "__main__":
    main()
