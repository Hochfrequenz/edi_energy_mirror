import time

import pytest

from edienergyscraper import EdiEnergyScraper


def fast_waiter():
    """
    a helper method to prevent actual DOS waiting (up to 3 seconds per call.)
    """
    time.sleep(0)


class TestEdiEnergyScraper:
    """
    A class to test the EdiEnergyScraper.
    """

    def test_instantiation(self):
        """
        Tests, that the constructor works.
        """
        instance = EdiEnergyScraper(root_url="https://my_url.de/")
        assert not instance._root_url.endswith("/")

    @pytest.mark.datafiles(
        "testfiles/index_20210208.html",
    )
    def test_index_retrieval(self, requests_mock):
        """
        Tests that the landing page is downloaded correctly
        """
        with open("testfiles/index_20210208.html", "r", encoding="utf8") as infile:
            response_body = infile.read()
        assert "<!--" in response_body
        requests_mock.get("https://www.my_root_url.test", text=response_body)
        ees = EdiEnergyScraper("https://www.my_root_url.test", waiter=fast_waiter)
        actual_soup = ees.get_index()
        actual_html = actual_soup.prettify()
        assert "<!--" not in actual_html, "comments should be ignored/removed"
        assert "Startseite: BDEW Forum Datenformate" in actual_html, "content should be returned"

    @pytest.mark.datafiles(
        "testfiles/index_20210208.html",
    )
    def test_dokumente_link(self, requests_mock):
        """
        Tests that the "Dokumente" link is extracted from the downloaded landing page.
        """
        with open("testfiles/index_20210208.html", "r", encoding="utf8") as infile:
            response_body = infile.read()
        assert "<!--" in response_body
        requests_mock.get("https://www.edi-energy.de", text=response_body)
        ees = EdiEnergyScraper("https://www.edi-energy.de", waiter=fast_waiter)
        actual_link = ees.get_documents_page_link(ees.get_index())
        assert actual_link == "https://www.edi-energy.de/index.php?id=38"
