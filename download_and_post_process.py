import asyncio
import logging
import sys

logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)  # global log config: write everything to stdout
from edi_energy_scraper import EdiEnergyScraper


async def mirror():
    scraper = EdiEnergyScraper(path_to_mirror_directory="edi_energy_de")
    await scraper.mirror()


if __name__ == "__main__":
    asyncio.run(mirror())

