from edienergyscraper import EdiEnergyScraper


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

    def test_index_retrieval(self):
        """
        Tests that the landing page is downloaded correctly
        """
        pass
