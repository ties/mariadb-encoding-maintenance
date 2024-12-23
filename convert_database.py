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

    cur = conn.cursor()
    click.echo(click.style(f"Changing {database} collation to utf8mb4_general_ci", bold=True))
    cur.execute(f"ALTER SCHEMA {database} DEFAULT CHARACTER SET utf8mb4 DEFAULT COLLATE utf8mb4_general_ci;")
    cur.execute("SHOW TABLES")
    tables = [row[0] for row in cur]
    for table_name in tables:
        click.echo(click.style(f"Changing table {table_name} collation to utf8mb4_general_ci", fg="green"))
        cur.execute(f"ALTER TABLE {table_name} CONVERT TO CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;")



if __name__ == "__main__":
    main()
