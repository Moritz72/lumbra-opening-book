import asyncio
import tempfile
from contextlib import contextmanager
from pathlib import Path
from typing import TYPE_CHECKING

import py7zr
import requests
from mega.client import MegaNzClient

if TYPE_CHECKING:
    from collections.abc import Generator

SITE_LINKS = {
    "OTB noDate": "https://lumbrasgigabase.com/download/otb-nodate/?wpdmdl=9164&refresh=6a2143260c52f1780564774",
    "OTB 0001-1899": "https://lumbrasgigabase.com/download/otb-0001-1899/?wpdmdl=9149&refresh=6a2143260930e1780564774",
    "OTB 1900-1949": "https://lumbrasgigabase.com/download/otb-1900-1949/?wpdmdl=9150&refresh=6a21432605c981780564774",
    "OTB 1950-1969": "https://lumbrasgigabase.com/download/otb-1950-1969/?wpdmdl=9152&refresh=6a21432601f581780564774",
    "OTB 1970-1989": "https://lumbrasgigabase.com/download/otb-1970-1989/?wpdmdl=9153&refresh=6a218e031e7271780583939",
    "OTB 1990-1999": "https://lumbrasgigabase.com/download/otb-1990-1999/?wpdmdl=9154&refresh=6a218e031b81b1780583939",
    "OTB 2000-2004": "https://lumbrasgigabase.com/download/otb-2000-2004/?wpdmdl=9155&refresh=6a218e03192231780583939",
    "OTB 2005-2009": "https://lumbrasgigabase.com/download/otb-2005-2009/?wpdmdl=9156&refresh=6a218e0316e2b1780583939",
    "OTB 2010-2014": "https://lumbrasgigabase.com/download/otb-2010-2014/?wpdmdl=9157&refresh=6a218e03148741780583939",
    "OTB 2015-2019": "https://lumbrasgigabase.com/download/otb-2015-2019/?wpdmdl=9158&refresh=6a218e03122521780583939",
    "OTB 2020-2024": "https://lumbrasgigabase.com/download/otb-2020-2024/?wpdmdl=9159&refresh=6a214325e138b1780564773",
    "OTB 2025": "https://lumbrasgigabase.com/download/otb-2025/?wpdmdl=9173&refresh=6a214325de0e81780564773",
}


def get_download_link(site_link: str) -> str:
    """Return the download link for the given site link."""
    response = requests.get(site_link, allow_redirects=True, timeout=30)
    response.raise_for_status()
    return response.url


async def mega_download(download_link: str, output_dir: str) -> Path:
    """Download from mega using the given link."""
    async with MegaNzClient() as client:
        results = await client.download_url(download_link, output_dir=output_dir)

        if results.fails:
            error_message = f"Failed to download of {download_link}"
            raise ValueError(error_message)

        return next(iter(results.success.values()))


@contextmanager
def open_mega_pgn(download_link: str) -> Generator[Path]:
    """Return a file handle for the pgn file retrieved from the given link."""
    with tempfile.TemporaryDirectory() as tmpdir:
        path = asyncio.run(mega_download(download_link, tmpdir))

        with py7zr.SevenZipFile(path, mode="r") as archive:
            names = archive.getnames()

            if len(names) != 1:
                error_message = f"Expected exactly 1 file for {download_link}"
                raise ValueError(error_message)

            archive.extractall(path=tmpdir)

        yield Path(tmpdir) / names[0]
