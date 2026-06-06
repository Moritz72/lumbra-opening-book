import sqlite3
from typing import TYPE_CHECKING

import duckdb

if TYPE_CHECKING:
    from pathlib import Path


def create_duckdb_table(
    csv_directory: Path, connection: duckdb.DuckDBPyConnection
) -> None:
    """Create the temporary duckdb table."""
    path = csv_directory / "*.csv"
    command = f"""
        CREATE TABLE agg AS
        SELECT
            hash,
            move,
            SUM(white) AS white,
            SUM(draw)  AS draw,
            SUM(black) AS black
        FROM read_csv(
            '{path}',
            header=false,
            names=['hash', 'move', 'white', 'draw', 'black']
        )
        GROUP BY hash, move
    """  # noqa: S608
    connection.execute(command)


def create_table(name: str, connection: sqlite3.Connection) -> None:
    """Create the database table."""
    command = f"""
        CREATE TABLE {name} (
            hash  INTEGER NOT NULL,
            move  INTEGER NOT NULL,
            white INTEGER NOT NULL,
            draw  INTEGER NOT NULL,
            black INTEGER NOT NULL
        )
    """
    connection.execute("PRAGMA journal_mode=WAL")
    connection.execute("PRAGMA synchronous=OFF")
    connection.execute("PRAGMA cache_size=-524288")
    connection.execute(command)


def populate_table(
    name: str,
    batch_size: int,
    connection_sqlite: sqlite3.Connection,
    connection_duckdb: duckdb.DuckDBPyConnection,
) -> None:
    """Populate the database table from duckdb."""
    insert = f"INSERT INTO {name} VALUES (?,?,?,?,?)"  # noqa: S608
    select_template = (
        f"SELECT hash, move, white, draw, black "  # noqa: S608
        f"FROM agg LIMIT {batch_size} OFFSET {{offset}}"
    )
    offset = 0

    while True:
        command = select_template.format(offset=offset)
        rows = connection_duckdb.execute(command).fetchall()
        if not rows:
            break

        connection_sqlite.executemany(insert, rows)
        connection_sqlite.commit()
        offset += batch_size


def create_database(
    database_file: Path, table_name: str, csv_directory: Path, batch_size: int
) -> None:
    """Create a sqlite database."""
    connection_sqlite = sqlite3.connect(database_file)
    connection_duckdb = duckdb.connect()

    create_duckdb_table(csv_directory, connection_duckdb)
    create_table(table_name, connection_sqlite)
    populate_table(table_name, batch_size, connection_sqlite, connection_duckdb)

    create_index = f"CREATE INDEX idx_hash ON {table_name}(hash)"
    connection_sqlite.execute(create_index)

    connection_duckdb.close()
    connection_sqlite.close()
