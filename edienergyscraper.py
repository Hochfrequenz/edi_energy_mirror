"""
A module to scrape data from edi-energy.de.
"""
import cgi
import datetime
import io
import os
import re
from enum import Enum
from pathlib import Path
from random import randint
from time import sleep
from typing import Callable, Dict, Set

import requests
from bs4 import BeautifulSoup, Comment  # type:ignore[import]
from PyPDF2 import PdfFileReader  # type:ignore[import]
from requests.models import CaseInsensitiveDict


class Epoch(str, Enum):  # pylint: disable=too-few-public-methods
    """
    An Epoch describes the time range in which documents are valid.
    """

    PAST = "past"  #: documents that are not valid anymore and have been archived
    CURRENT = "current"  #: documents that are currently valid valid_from <= now < valid_to
    FUTURE = "future"  #: documents that will become valid in the future (most likely with the next format version)


class EdiEnergyScraper:
    """
    A class that uses beautiful soup to extract and download data from edi-energy.de.
    Beautiful soup is a library that makes it easy to scrape information from web pages:
    https://pypi.org/project/beautifulsoup4/
    """

    def __init__(
        self,
        root_url: str = "https://www.edi-energy.de",
        path_to_mirror_directory: Path = Path("edi_energy_de"),
        # HTML and PDF files will be stored relative to this
        dos_waiter: Callable = lambda: sleep(randint(1, 10)),
    ):
        """
        Initialize the Scaper by providing the URL, a path to save the files to and a function that prevents DOS.
        """
        self._root_url = root_url.strip()
        if self._root_url.endswith("/"):
            # remove trailing slash if any
            self._root_url = self._root_url[:-1]
        self._root_dir = path_to_mirror_directory
        self._dos_waiter = dos_waiter

    def _get_soup(self, url: str) -> BeautifulSoup:
        """
        Downloads the given absolute URL, parses it as html, removes the comments and returns the soup.
        """
        if not url.startswith("http"):
            url = f"{self._root_url}/{url.strip('/')}"  # remove trailing slashes from relative link
        response = requests.get(url, timeout=5)
        soup = BeautifulSoup(response.content, "html.parser")
        EdiEnergyScraper.remove_comments(soup)
        self._dos_waiter()  # <-- DOS protection, usually a blocking method (e.g. time.sleep(...))
        return soup

    def _download_and_save_pdf(self, epoch: Epoch, file_basename: str, link: str) -> Path:
        """
        Downloads a PDF file from a given link and stores it under the file name in a folder that has the same name
        as the directory, if the pdf does not exist yet or if the metadata has changed since the last download.
        Returns the path to the downloaded pdf.
        """

        if not link.startswith("http"):
            link = f"{self._root_url}/{link.strip('/')}"  # remove trailing slashes from relative link

        response = requests.get(link, timeout=5)

        file_name = EdiEnergyScraper._add_file_extension_to_file_basename(
            headers=response.headers, file_basename=file_basename
        )

        file_path = self._get_file_path(file_name=file_name, epoch=epoch)

        # Save file if it does not exist yet
        if not os.path.isfile(file_path):
            with open(file_path, "wb+") as outfile:  # pdfs are written as binaries
                outfile.write(response.content)
            return file_path

        # First fix, different file types do just the same as before, only with correct file extension
        if not file_name.endswith(".pdf"):
            with open(file_path, "wb+") as outfile:
                outfile.write(response.content)
            return file_path

        # Check if metadata has changed
        metadata_has_changed = self._have_different_metadata(response.content, file_path)
        if metadata_has_changed:  # delete old file and replace with new one
            os.remove(file_path)
            with open(file_path, "wb+") as outfile:  # pdfs are written as binaries
                outfile.write(response.content)

        return file_path

    def _get_file_path(self, epoch: Epoch, file_name: str) -> Path:
        if "/" in file_name:
            raise ValueError(f"file names must not contain slashes: '{file_name}'")
        file_path = Path(self._root_dir).joinpath(
            f"{epoch}/{file_name}"  # e.g "{root_dir}/future/ahbmabis_99991231_20210401.pdf"
        )

        return file_path

    @staticmethod
    def _add_file_extension_to_file_basename(headers: CaseInsensitiveDict, file_basename: str) -> str:
        """Extracts the extension of a file from a response header and add it to the file basename."""
        content_disposition = headers["Content-Disposition"]
        _, params = cgi.parse_header(content_disposition)
        file_extension = Path(params["filename"]).suffix
        file_name = file_basename + file_extension
        return file_name

    @staticmethod
    def _have_different_metadata(data_new_file: bytes, path_to_old_file: Path) -> bool:
        """
        Compares the metadata of two pdf files.
        :param data_new_file: bytes from response.content
        :param path_to_old_file: str

        :return: bool, if metadata of the two pdf files are different or if at least one of the files is encrypted.

        """
        pdf_new = PdfFileReader(io.BytesIO(data_new_file))
        if pdf_new.isEncrypted:
            return True
        pdf_new_metadata = pdf_new.getDocumentInfo()

        with open(path_to_old_file, "rb") as file_old:
            pdf_old = PdfFileReader(file_old)
            if pdf_old.isEncrypted:
                return True
            pdf_old_metadata = pdf_old.getDocumentInfo()

        metadata_has_changed: bool = pdf_new_metadata == pdf_old_metadata

        return metadata_has_changed

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
        result: Dict[Epoch, str] = {}
        for (doc_text, doc_epoch) in EdiEnergyScraper._docs_texts.items():
            result[doc_epoch] = document_soup.find("a", string=re.compile(r"\s*" + doc_text + r"\s*")).attrs["href"]
        # result now looks like this:
        # { "past": "link_to_vergangene_dokumente.html", "current": "link_to_active_docs.html", "future": ...}
        # see the unittest
        return result

    @staticmethod
    def get_epoch_file_map(epoch_soup: BeautifulSoup) -> Dict[str, str]:
        """
        Extracts a dictionary from the epoch soup (e.g. soup of "future.html") that maps file basenames as keys
        (e.g. "APERAKCONTRLAHB2.3h_99993112_20210104") to URLs of the documents as value.
        """
        download_table = epoch_soup.find(
            "table", {"class": "table table-responsive table-condensed"}
        )  # a table that contains all the documents
        result: Dict[str, str] = {}
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
            doc_name = re.sub(r"\s{2,}", "", table_cells[0].text).replace(":", "").replace(" ", "").replace("/", "")
            # the "Gültig ab" column / publication date is the second column. e.g. "    17.12.2019    "
            # Spoiler: It's not the real publication date. They modify the files once in a while without updating it.
            publication_date = datetime.datetime.strptime(table_cells[1].text.strip(), "%d.%m.%Y")
            try:
                # the "Gültig bis" column / valid to date describes on which date the document becomes legally binding.
                # usually this is something like "   31.03.2020   " or "30.09.2019"
                valid_to_date = datetime.datetime.strptime(table_cells[2].text.strip(), "%d.%m.%Y")
            except ValueError as value_error:
                # there's a special case: "Offen" means the document is valid until further notice.
                if table_cells[2].text.strip() == "Offen":
                    valid_to_date = datetime.datetime(9999, 12, 31)
                else:
                    raise value_error
            # the 4th column contains a download link for the PDF.
            file_link = table_cells[3].find("a").attrs["href"]
            # there was a bug until 2021-02-10 where I used a weird %Y%d%m instead of %Y%m%d format.
            file_basename = f"{doc_name}_{valid_to_date.strftime('%Y%m%d')}_{publication_date.strftime('%Y%m%d')}"
            result[file_basename] = file_link
        return result

    def remove_no_longer_online_files(self, online_files: Set[Path]) -> Set[Path]:
        """
        Removes files that are no longer online. This could be due to being moved to another folder,
        e.g. from future to current.
        :param online_files: set, all the paths to the pdfs that were being downloaded and compared.
        :return: Set[Path], Set of Paths that were removed
        """

        all_files_in_mirror_dir: Set = set((self._root_dir).glob("**/*.*[!html]"))
        no_longer_online_files = all_files_in_mirror_dir.symmetric_difference(online_files)
        for path in no_longer_online_files:
            os.remove(path)

        return no_longer_online_files

    def mirror(self):
        """
        Main method of the scraper. Downloads all the files and pages and stores them in the filesystem
        """
        index_soup = self.get_index()
        index_path: Path = Path(self._root_dir, "index.html")
        with open(index_path, "w+", encoding="utf8") as outfile:
            # save the index file as html
            outfile.write(index_soup.prettify())
        epoch_links = EdiEnergyScraper.get_epoch_links(self._get_soup(self.get_documents_page_link(index_soup)))
        new_file_paths: Set = set()
        for epoch, epoch_link in epoch_links.items():
            epoch_soup = self._get_soup(epoch_link)
            epoch_path: Path = Path(self._root_dir, f"{epoch}.html")  # e.g. "future.html"
            with open(epoch_path, "w+", encoding="utf8") as outfile:
                outfile.write(epoch_soup.prettify())
            file_map = EdiEnergyScraper.get_epoch_file_map(epoch_soup)
            for file_basename, link in file_map.items():
                file_path = self._download_and_save_pdf(epoch=epoch, file_basename=file_basename, link=link)
                new_file_paths.add(file_path)
        self.remove_no_longer_online_files(new_file_paths)
