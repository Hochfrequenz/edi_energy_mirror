import time
from pathlib import Path

import pytest
from bs4 import BeautifulSoup
from edienergyscraper import EdiEnergyScraper, Epoch


def fast_waiter():
    """
    A helper method to prevent actual DOS waiting (up to 3 seconds per call.)
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
        "./unittests/testfiles/index_20210208.html",
    )
    def test_index_retrieval(self, requests_mock, datafiles):
        """
        Tests that the landing page is downloaded correctly
        """
        with open(datafiles / "index_20210208.html", "r", encoding="utf8") as infile:
            response_body = infile.read()
        assert (
            "<!--" in response_body
        )  # original response contains comments, will be removed
        requests_mock.get("https://www.my_root_url.test", text=response_body)
        ees = EdiEnergyScraper("https://www.my_root_url.test", dos_waiter=fast_waiter)
        actual_soup = ees.get_index()
        actual_html = actual_soup.prettify()
        assert "<!--" not in actual_html, "comments should be ignored/removed"
        assert (
            "Startseite: BDEW Forum Datenformate" in actual_html
        ), "content should be returned"

    @pytest.mark.datafiles(
        "./unittests/testfiles/index_20210208.html",
    )
    def test_dokumente_link(self, requests_mock, datafiles):
        """
        Tests that the "Dokumente" link is extracted from the downloaded landing page.
        """
        with open(datafiles / "index_20210208.html", "r", encoding="utf8") as infile:
            response_body = infile.read()
        requests_mock.get("https://www.edi-energy.de", text=response_body)
        ees = EdiEnergyScraper("https://www.edi-energy.de", dos_waiter=fast_waiter)
        actual_link = ees.get_documents_page_link(ees.get_index())
        assert actual_link == "https://www.edi-energy.de/index.php?id=38"

    @pytest.mark.datafiles(
        "./unittests/testfiles/dokumente_20210208.html",
    )
    def test_epoch_links_extraction(self, datafiles):
        """
        Tests that the links to past/current/future documents overview pages are extracted.
        """
        with open(
            datafiles / "dokumente_20210208.html", "r", encoding="utf8"
        ) as infile:
            response_body = infile.read()
        soup = BeautifulSoup(response_body, "html.parser")
        actual = EdiEnergyScraper.get_epoch_links(soup)
        assert len(actual.keys()) == 3
        assert (
            actual[Epoch.CURRENT]
            == "https://www.edi-energy.de/index.php?id=38&tx_bdew_bdew%5Bview%5D=now&tx_bdew_bdew%5Baction%5D=list&tx_bdew_bdew%5Bcontroller%5D=Dokument&cHash=5d1142e54d8f3a1913af8e4cc56c71b2"
        )
        assert (
            actual[Epoch.PAST]
            == "https://www.edi-energy.de/index.php?id=38&tx_bdew_bdew%5Bview%5D=archive&tx_bdew_bdew%5Baction%5D=list&tx_bdew_bdew%5Bcontroller%5D=Dokument&cHash=6dd9d237ef46f6eebe2f4ef385528382"
        )
        assert (
            actual[Epoch.FUTURE]
            == "https://www.edi-energy.de/index.php?id=38&tx_bdew_bdew%5Bview%5D=future&tx_bdew_bdew%5Baction%5D=list&tx_bdew_bdew%5Bcontroller%5D=Dokument&cHash=325de212fe24061e83e018a2223e6185"
        )

    @pytest.mark.datafiles(
        "./unittests/testfiles/future_20210210.html",
    )
    def test_epoch_file_map_future_20210210(self, datafiles):
        with open(datafiles / "future_20210210.html", "r", encoding="utf8") as infile:
            response_body = infile.read()
        soup = BeautifulSoup(response_body, "html.parser")
        actual = EdiEnergyScraper.get_epoch_file_map(soup)
        assert len(actual.keys()) == 76
        for file_name in actual.keys():
            # all the future names should contain 99991231 as "valid to" date
            assert "_99991231_" in file_name
        assert (
            actual[
                "UTILMDAHBWiM3.1bKonsolidierteLesefassungmitFehlerkorrekturenStand18.12.2020_99991231_20210401.pdf"
            ]
            == "https://www.edi-energy.de/index.php?id=38&tx_bdew_bdew%5Buid%5D=1000&tx_bdew_bdew%5Baction%5D=download&tx_bdew_bdew%5Bcontroller%5D=Dokument&cHash=dbf7d932028aa2059c96b25a684d02ed"
        )

    @pytest.mark.datafiles(
        "./unittests/testfiles/current_20210210.html",
    )
    def test_epoch_file_map_current_20210210(self, datafiles):
        with open(datafiles / "current_20210210.html", "r", encoding="utf8") as infile:
            response_body = infile.read()
        soup = BeautifulSoup(response_body, "html.parser")
        actual = EdiEnergyScraper.get_epoch_file_map(soup)
        assert len(actual.keys()) == 81
        for file_name in actual.keys():
            # all the current documents are either "open" or valid until April 2021
            assert "_99991231_" in file_name or "_20210331_" in file_name
        assert (
            actual[
                "QUOTESMIG1.1aKonsolidierteLesefassungmitFehlerkorrekturenStand15.07.2019_20210331_20191201.pdf"
            ]
            == "https://www.edi-energy.de/index.php?id=38&tx_bdew_bdew%5Buid%5D=738&tx_bdew_bdew%5Baction%5D=download&tx_bdew_bdew%5Bcontroller%5D=Dokument&cHash=f01ed973e9947ccf6b91181c93cd2a28"
        )

    @pytest.mark.datafiles(
        "./unittests/testfiles/past_20210210.html",
    )
    def test_epoch_file_map_past_20210210(self, datafiles):
        with open(datafiles / "past_20210210.html", "r", encoding="utf8") as infile:
            response_body = infile.read()
        soup = BeautifulSoup(response_body, "html.parser")
        actual = EdiEnergyScraper.get_epoch_file_map(soup)
        assert len(actual.keys()) == 705

    @pytest.mark.datafiles(
        "./unittests/testfiles/example_ahb.pdf",
    )
    def test_pdf_download(self, requests_mock, tmpdir_factory, datafiles):
        """
        Tests that a PDF can be downloaded and is stored.
        """
        ees_dir = tmpdir_factory.mktemp("test_dir")
        ees_dir.mkdir("future")
        with open(datafiles / "example_ahb.pdf", "rb") as pdf_file:
            # Note that we do _not_ use pdf_file.read() here but provide the requests_mocker with a file handle.
            # Otherwise you'd run into a "ValueError: Unable to determine whether fp is closed."
            # docs: https://requests-mock.readthedocs.io/en/latest/response.html?highlight=file#registering-responses
            requests_mock.get("https://my_file_link.inv/foo_bar.pdf", body=pdf_file)
            ees = EdiEnergyScraper(
                "https://my_file_link.inv/", dos_waiter=fast_waiter, directory=ees_dir
            )
            ees._download_and_save_pdf(
                epoch=Epoch.FUTURE, file_name="my_favourite_ahb.pdf", link="foo_bar.pdf"
            )
        assert ees_dir.join(Path("future/my_favourite_ahb.pdf")).exists()

    @staticmethod
    def _get_soup_mocker(*args, **kwargs):
        if args[0] == "current.html":
            with open(
                "./unittests/testfiles/current_20210210.html", "r", encoding="utf8"
            ) as infile_current:
                response_body = infile_current.read()
        elif args[0] == "past.html":
            with open(
                "./unittests/testfiles/past_20210210.html", "r", encoding="utf8"
            ) as infile_past:
                response_body = infile_past.read()
        elif args[0] == "future.html":
            with open(
                "./unittests/testfiles/future_20210210.html", "r", encoding="utf8"
            ) as infile_future:
                response_body = infile_future.read()
        elif args[0] == "https://www.edi-energy.de":
            with open(
                "./unittests/testfiles/index_20210208.html", "r", encoding="utf8"
            ) as infile_index:
                response_body = infile_index.read()
        elif args[0] == "https://www.edi-energy.de/index.php?id=38":
            with open(
                "./unittests/testfiles/dokumente_20210208.html", "r", encoding="utf8"
            ) as infile_docs:
                response_body = infile_docs.read()
        else:
            raise NotImplementedError(
                f"The soup for {args[0]} is not implemented in this test."
            )
        soup = BeautifulSoup(response_body, "html.parser")
        return soup

    @staticmethod
    def _get_efm_mocker(*args, **kwargs):
        heading = args[0].find("h2").text
        if heading == "Aktuell gültige Dokumente":
            return {"xyz.pdf": "/a_current_ahb.pdf"}
        if heading == "Zukünftige Dokumente":
            return {"def.pdf": "/a_future_ahb.pdf"}
        if heading == "Archivierte Dokumente":
            return {"abc.pdf": "/a_past_ahb.pdf"}
        raise NotImplementedError(
            f"The case '{heading}' is not implemented in this test."
        )

    @pytest.mark.datafiles(
        "./unittests/testfiles/example_ahb.pdf",
        "./unittests/testfiles/dokumente_20210208.html",
        "./unittests/testfiles/index_20210208.html",
        "./unittests/testfiles/current_20210210.html",
        "./unittests/testfiles/past_20210210.html",
        "./unittests/testfiles/future_20210210.html",
    )
    def test_mirroring(self, mocker, requests_mock, tmpdir_factory, datafiles):
        """
        Tests the overall process and mocks most of the already tested methods.
        """
        ees_dir = tmpdir_factory.mktemp("test_dir_mirror")
        ees_dir.mkdir("future")
        ees_dir.mkdir("current")
        ees_dir.mkdir("past")
        with open(datafiles / "example_ahb.pdf", "rb") as pdf_file_current, open(
            datafiles / "example_ahb.pdf", "rb"
        ) as pdf_file_future, open(
            datafiles / "example_ahb.pdf", "rb"
        ) as pdf_file_past:
            requests_mock.get(
                "https://www.edi-energy.de/a_future_ahb.pdf", body=pdf_file_future
            )
            requests_mock.get(
                "https://www.edi-energy.de/a_current_ahb.pdf", body=pdf_file_current
            )
            requests_mock.get(
                "https://www.edi-energy.de/a_past_ahb.pdf", body=pdf_file_past
            )
            mocker.patch(
                "edienergyscraper.EdiEnergyScraper.get_epoch_links",
                return_value={
                    "current": "current.html",
                    "future": "future.html",
                    "past": "past.html",
                },
            )
            mocker.patch(
                "edienergyscraper.EdiEnergyScraper._get_soup",
                side_effect=TestEdiEnergyScraper._get_soup_mocker,
            )
            mocker.patch(
                "edienergyscraper.EdiEnergyScraper.get_epoch_file_map",
                side_effect=TestEdiEnergyScraper._get_efm_mocker,
            )
            ees = EdiEnergyScraper(dos_waiter=fast_waiter, directory=ees_dir)
            ees.mirror()
        assert ees_dir.join(Path("index.html")).exists()
        assert ees_dir.join(Path("future.html")).exists()
        assert ees_dir.join(Path("current.html")).exists()
        assert ees_dir.join(Path("past.html")).exists()
        assert ees_dir.join(Path("future")).join(Path("def.pdf")).exists()
        assert ees_dir.join(Path("past")).join(Path("abc.pdf")).exists()
        assert ees_dir.join(Path("current")).join(Path("xyz.pdf")).exists()
