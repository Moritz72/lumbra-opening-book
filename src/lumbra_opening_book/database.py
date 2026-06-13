from typing import TYPE_CHECKING

import duckdb

if TYPE_CHECKING:
    from pathlib import Path


def create_table(csv_directory: Path, connection: duckdb.DuckDBPyConnection) -> None:
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
    """

    connection.execute("SET memory_limit='8GB'")
    connection.execute("SET temp_directory='/tmp/duckdb_temp'")
    connection.execute(command)


def export_to_sqlite(
    database_file: Path, table_name: str, connection: duckdb.DuckDBPyConnection
) -> None:
    """Export to a sqlite database."""
    connection.execute("INSTALL sqlite; LOAD sqlite;")
    connection.execute(f"ATTACH '{database_file}' AS sqlite_db (TYPE SQLITE)")
    connection.execute(f"CREATE TABLE sqlite_db.{table_name} AS SELECT * FROM agg")
    connection.execute("DETACH sqlite_db")


def create_database(database_file: Path, table_name: str, csv_directory: Path) -> None:
    """Create a sqlite database."""
    connection = duckdb.connect()

    create_table(csv_directory, connection)
    export_to_sqlite(database_file, table_name, connection)

    connection.close()
