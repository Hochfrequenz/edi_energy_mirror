import asyncio

from edi_energy_scraper import EdiEnergyScraper


async def mirror():
    scraper = EdiEnergyScraper(path_to_mirror_directory="edi_energy_de")
    await scraper.mirror()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(mirror())
