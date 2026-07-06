import asyncio
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)  # global log config: write everything to stdout
from edi_energy_scraper import (  # pylint: disable=wrong-import-position
    AKTIVITAETSDIAGRAMME_SEED_URLS,
    BdewAnwendungshilfenScraper,
    EdiEnergyScraper,
)


async def mirror():
    scraper = EdiEnergyScraper(path_to_mirror_directory="edi_energy_de")
    await scraper.mirror()
    # The BDEW Anwendungshilfen (Aktivitätsdiagramme) are not part of the bdew-mako.de document
    # API; they are plain PDF/DOCX links on bdew.de service pages. Mirror them into a dedicated
    # directory using the scraper's curated list of current public seed pages.
    anwendungshilfen_scraper = BdewAnwendungshilfenScraper()
    try:
        await anwendungshilfen_scraper.download_from_seeds(
            list(AKTIVITAETSDIAGRAMME_SEED_URLS),
            target_directory="aktivitaetsdiagramme",
        )
    finally:
        await anwendungshilfen_scraper.close()


if __name__ == "__main__":
    asyncio.run(mirror())

