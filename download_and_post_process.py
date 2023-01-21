from edi_energy_scraper import EdiEnergyScraper

ees = EdiEnergyScraper(dos_waiter=lambda: sleep(0))
ees.mirror()
