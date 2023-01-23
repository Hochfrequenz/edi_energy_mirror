from time import sleep
from edi_energy_scraper import EdiEnergyScraper

ees = EdiEnergyScraper(path_to_mirror_directory="edi_energy_de", dos_waiter=lambda: sleep(0))
ees.mirror()
