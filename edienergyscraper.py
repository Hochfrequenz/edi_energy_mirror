"""
A module to scrape data from edi-energy.de.
"""
from pathlib import Path

import requests
from bs4 import BeautifulSoup, Comment


class EdiEnergyScraper:
    """
    A class that uses beautiful soup to extract and download data from edi-energy.de.
    """

    def __init__(self, root_url: str = "https://www.edi-energy.de", directory: Path = Path("edi_energy_de")):
        self._root_url = root_url.strip()
        if self._root_url.endswith("/"):
            # remove trailing slashes
            self._root_url = self._root_url[:-1]
        self._root_dir = directory

    def get_index(self) -> BeautifulSoup:
        """
        Downloads the root url and returns the soup.
        """
        # As the landing page is usually called "index.html/php/..." this method is named index.
        root_response = requests.get(self._root_url)
        root_soup = BeautifulSoup(root_response.content, "html.parser")
        EdiEnergyScraper.remove_comments(root_soup)
        return root_soup

    @staticmethod
    def remove_comments(soup):
        """
        Removes thes HTML comments from the given soup.
        """
        for html_comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
            html_comment.extract()

    def mirror(self):
        """
        Main method of the scraper. Downloads all the files and pages.
        """
        index_soup = self.get_index()
        index_path: Path = Path(self._root_dir, "index.html")
        with open(index_path, "w+", encoding="utf8") as outfile:
            outfile.write(index_soup.prettify())
