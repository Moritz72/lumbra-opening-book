import argparse
import tempfile
from pathlib import Path

from tqdm import tqdm

from lumbra_opening_book.database import create_database
from lumbra_opening_book.fetch import SITE_LINKS, get_download_link, open_mega_pgn
from lumbra_opening_book.shakmaty_python import parse_pgn


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Build a Lumbra opening book database from PGN files."
    )
    parser.add_argument(
        "--database-path",
        type=Path,
        default=Path("lumbra_opening_book.db"),
        help="Path to the output SQLite database (default: lumbra_opening_book.db)",
    )
    parser.add_argument(
        "--table-name",
        type=str,
        default="positionmove",
        help="Name of the table to populate (default: positionmove)",
    )
    parser.add_argument(
        "--csv-directory",
        type=Path,
        default=None,
        help="Directory to store intermediate CSV files. Uses a temp dir if not set.",
    )
    parser.add_argument(
        "--max-plies",
        type=int,
        default=50,
        help="Maximum number of plies to parse per game (default: 50)",
    )
    return parser.parse_args()


def main(
    *,
    database_path: Path,
    table_name: str,
    csv_directory: Path | None,
    max_plies: int | None,
) -> None:
    """Create the opening book."""
    download_links = {key: get_download_link(link) for key, link in SITE_LINKS.items()}

    if csv_directory is None:
        temporary_directory = tempfile.TemporaryDirectory()
        csv_directory = Path(temporary_directory.name)
    else:
        temporary_directory = None

    with tqdm(
        download_links.items(), desc="Parsing PGNs", total=len(download_links)
    ) as progress_bar:
        for key, download_link in progress_bar:
            with open_mega_pgn(download_link) as pgn_path:
                csv_path = csv_directory / f"{key}.csv"
                parse_pgn(str(pgn_path), str(csv_path), max_plies)

    with tqdm(desc="Creating Database", total=1) as progress_bar:
        create_database(database_path, table_name, csv_directory)
        progress_bar.update(1)

    if temporary_directory is not None:
        temporary_directory.cleanup()


if __name__ == "__main__":
    args = parse_args()
    main(
        database_path=args.database_path,
        table_name=args.table_name,
        csv_directory=args.csv_directory,
        max_plies=args.max_plies,
    )
