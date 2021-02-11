"""
A module to scrape data from edi-energy.de.
"""
import datetime
import re
from pathlib import Path
from random import randint
from time import sleep
from typing import Callable, Dict

import aenum
import requests
from bs4 import BeautifulSoup, Comment


class Epoch(aenum.Enum):  # pylint: disable=too-few-public-methods
    """
    An Epoch describes the time range in which documents are valid.
    """

    _init_ = "value string"
    PAST = 1, "past"  # documents that are not valid anymore an have been archived
    CURRENT = (
        2,
        "current",
    )  # documents that are currently valid valid_from <= now < valid_to
    FUTURE = (
        3,
        "future",
    )  # documents that will become valid in the future (most likely with the next format version)

    def __str__(self):
        return self.string


class EdiEnergyScraper:
    """
    A class that uses beautiful soup to extract and download data from edi-energy.de.
    Beautiful soup is a library that makes it easy to scrape information from web pages:
    https://pypi.org/project/beautifulsoup4/
    """

    def __init__(
        self,
        root_url: str = "https://www.edi-energy.de",
        directory: Path = Path("edi_energy_de"),
        dos_waiter: Callable = lambda: sleep(randint(1, 10)),
    ):
        """
        Initialize the Scaper by providing the URL, a path to save the files to and a function that prevents DOS.
        """
        self._root_url = root_url.strip()
        if self._root_url.endswith("/"):
            # remove trailing slash if any
            self._root_url = self._root_url[:-1]
        self._root_dir = directory
        self._dos_waiter = dos_waiter

    def _get_soup(self, url: str) -> BeautifulSoup:
        """
        Downloads the given absolute URL, parses it as html, removes the comments and returns the soup.
        """
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        EdiEnergyScraper.remove_comments(soup)
        self._dos_waiter()  # <-- DOS protection, usually a blocking method (e.g. time.sleep(...))
        return soup

    def _download_and_save_pdf(self, epoch: Epoch, file_name: str, link: str) -> bytes:
        """
        Downloads a PDF file from a given link and stores it under the file name in a folder that has the same name
        as the directory.
        Returns the PDF.
        """
        if not file_name.endswith(".pdf"):
            raise ValueError(
                f"This method is thought to save pdf files but the filename was {file_name}"
            )
        if "/" in file_name:
            raise ValueError(f"file names must not contain slashes: '{file_name}'")
        if not link.startswith("http"):
            link = f"{self._root_url}/{link.strip('/')}"  # remove trailing slashes from relative link
        response = requests.get(link)
        file_path = Path(self._root_dir).joinpath(
            f"{epoch}/{file_name}"  # e.g "{root_dir}/future/ahbmabis_99991231_20210401.pdf"
        )
        with open(file_path, "wb+") as outfile:  # pdfs are written as binaries
            outfile.write(response.content)
        return response.content

    def get_index(self) -> BeautifulSoup:
        """
        Downloads the root url and returns the soup.
        """
        # As the landing page is usually called "index.html/php/..." this method is named index.
        return self._get_soup(self._root_url)

    @staticmethod
    def remove_comments(soup):
        """
        Removes thes HTML comments from the given soup.
        """
        for html_comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
            html_comment.extract()

    def get_documents_page_link(self, index_soup) -> str:
        """
        Extracts the links for the "Dokumente" from a given index soup.
        """
        # HTML links look like this <a href="url">...</a>; That's why we search for "a"
        documents_link = index_soup.find("a", {"title": "Dokumente"})
        if not documents_link:
            raise ValueError('The soup did not contain a link called "Dokumente".')
        documents_url = documents_link.attrs["href"]
        if not documents_url.startswith("http"):
            documents_url = self._root_url + documents_link.attrs["href"]
        return documents_url

    # a dictionary that maps link titles to short names.
    _docs_texts: Dict[str, Epoch] = {
        "Aktuell gültige Dokumente": Epoch.CURRENT,
        "Zukünftig gültige Dokumente": Epoch.FUTURE,
        "Archivierte Dokumente": Epoch.PAST,
    }

    @staticmethod
    def get_epoch_links(document_soup) -> Dict[Epoch, str]:
        """
        Extract the links to
        * "Aktuell gültige Dokumente"
        * "Zukünftig gültige Dokumente"
        * "Archivierte Dokumente"
        from the "Dokumente" sub page soup.
        """
        result: Dict[Epoch, str] = dict()
        for doc_text in EdiEnergyScraper._docs_texts:
            result[EdiEnergyScraper._docs_texts[doc_text]] = document_soup.find(
                "a", string=re.compile(r"\s*" + doc_text + r"\s*")
            ).attrs["href"]
        # result now looks like this:
        # { "past": "link_to_vergangene_dokumente.html", "current": "link_to_active_docs.html", "future": ...}
        # see the unittest
        return result

    @staticmethod
    def get_epoch_file_map(epoch_soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extracts a dictionary from the epoch soup (e.g. soup of "future.html") that maps filenames as keys
        (e.g. "APERAKCONTRLAHB2.3h_99993112_20210104.pdf") to URLs of the documents as value.
        """
        download_table = epoch_soup.find(
            "table", {"class": "table table-responsive table-condensed"}
        )  # a table that contains all the documents
        result: Dict[str, str] = dict()
        for table_row in download_table.find_all("tr"):
            table_cells = list(table_row.find_all("td"))
            if len(table_cells) < 4:
                # Not all the rows in the table contain 4 columns. sad but true. Usually it's the header lines.
                # This might be subsections of the table.
                continue
            # The first cell in a row contains a lot of whitespaces and somewhere in between a name.
            # e.g. "   INVOIC / REMADV AHB 2.4 Konsolidierte Lesefassung mit Fehlerkorrekturen Stand: 01.07.2020    "
            # To normalize it, we remove all adjacent occurences of more than 1 whitespaces and replace characters that
            # might cause problems in filenames (e.g. slash)
            # Looking back, this might not be the most readable format to store the files but by keeping it, it's way
            # easier to keep track of a file based history in our git archive.
            doc_name = (
                re.sub(r"\s{2,}", "", table_cells[0].text)
                .replace(":", "")
                .replace(" ", "")
                .replace("/", "")
            )
            # the "Gültig ab" column / publication date is the second column. e.g. "    17.12.2019    "
            # Spoiler: It's not the real publication date. They modify the files once in a while without updating it.
            publication_date = datetime.datetime.strptime(
                table_cells[1].text.strip(), "%d.%m.%Y"
            )
            try:
                # the "Gültig bis" column / valid to date describes on which date the document becomes legally binding.
                # usually this is something like "   31.03.2020   " or "30.09.2019"
                valid_to_date = datetime.datetime.strptime(
                    table_cells[2].text.strip(), "%d.%m.%Y"
                )
            except ValueError as value_error:
                # there's a special case: "Offen" means the document is valid until further notice.
                if table_cells[2].text.strip() == "Offen":
                    valid_to_date = datetime.date(9999, 12, 31)
                else:
                    raise value_error
            # the 4th column contains a download link for the PDF.
            file_link = table_cells[3].find("a").attrs["href"]
            # there was a bug until 2021-02-10 where I used a weird %Y%d%m instead of %Y%m%d format.
            file_name = f"{doc_name}_{valid_to_date.strftime('%Y%m%d')}_{publication_date.strftime('%Y%m%d')}.pdf"
            result[file_name] = file_link
        return result

    def mirror(self):
        """
        Main method of the scraper. Downloads all the files and pages and stores them in the filesystem
        """
        index_soup = self.get_index()
        index_path: Path = Path(self._root_dir, "index.html")
        with open(index_path, "w+", encoding="utf8") as outfile:
            # save the index file as html
            outfile.write(index_soup.prettify())
        epoch_links = EdiEnergyScraper.get_epoch_links(
            self._get_soup(self.get_documents_page_link(index_soup))
        )
        for epoch, epoch_link in epoch_links.items():
            epoch_soup = self._get_soup(epoch_link)
            epoch_path: Path = Path(
                self._root_dir, f"{epoch}.html"
            )  # e.g. "future.html"
            with open(epoch_path, "w+", encoding="utf8") as outfile:
                outfile.write(epoch_soup.prettify())
            file_map = EdiEnergyScraper.get_epoch_file_map(epoch_soup)
            for file_name, link in file_map.items():
                self._download_and_save_pdf(file_name=file_name, link=link, epoch=epoch)
