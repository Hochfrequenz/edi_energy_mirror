import requests
from random import randint
from time import sleep
import re
import datetime
from bs4 import BeautifulSoup, Comment


def remove_comments(soup):
    for html_comment in soup.findAll(text=lambda text: isinstance(text, Comment)):
        html_comment.extract()


ROOT_URL = "https://www.edi-energy.de"
ROOT_DIR = "edi_energy_de/"
root_response = requests.get(ROOT_URL)
root_soup = BeautifulSoup(root_response.content, "html.parser")
remove_comments(root_soup)
with open(ROOT_DIR + "index.html", "w+", encoding="utf8") as outfile:
    outfile.write(root_soup.prettify())
docs_link = root_soup.find("a", {"title": "Dokumente"})
docs_url = ROOT_URL + docs_link.attrs["href"]
sleep(randint(1, 10))  # avoid DOS

docs_overview_response = requests.get(docs_url)
docs_overview_soup = BeautifulSoup(docs_overview_response.content, "html.parser")
doc_links = dict()
docs_texts = {
    "Aktuell gültige Dokumente": "current",
    "Zukünftig gültige Dokumente": "future",
    "Archivierte Dokumente": "past",
}
for doc_text in docs_texts:
    doc_links[docs_texts[doc_text]] = docs_overview_soup.find(
        "a", string=re.compile(r"\s*" + doc_text + r"\s*")
    ).attrs["href"]
for doc_link in doc_links:
    sleep(randint(1, 10))
    docs_response = requests.get(ROOT_URL + doc_links[doc_link])
    docs_soup = BeautifulSoup(docs_response.content, "html.parser")
    remove_comments(docs_soup)
    with open(ROOT_DIR + doc_link + ".html", "w+", encoding="utf8") as outfile:
        outfile.write(docs_soup.prettify())
    download_table = docs_soup.find(
        "table", {"class": "table table-responsive table-condensed"}
    )
    for table_line in download_table.find_all("tr"):
        table_cells = list(table_line.find_all("td"))
        if len(table_cells) < 4:
            continue
        doc_name = (
            re.sub(r"\s{2,}", "", table_cells[0].text)
            .replace(":", "")
            .replace(" ", "")
            .replace("/", "")
        )
        try:
            publ_date = datetime.datetime.strptime(
                table_cells[1].text.strip(), "%d.%m.%Y"
            )
        except ValueError:
            continue
        try:
            vali_date = datetime.datetime.strptime(
                table_cells[2].text.strip(), "%d.%m.%Y"
            )
        except ValueError as ve:
            if table_cells[2].text.strip() == "Offen":
                vali_date = datetime.date(9999, 12, 31)
            else:
                raise ve
        download_href = table_cells[3].find("a").attrs["href"]
        sleep(randint(1, 10))
        doc_response = requests.get(ROOT_URL + download_href)
        file_name = (
            doc_name
            + "_"
            + vali_date.strftime("%Y%d%m")
            + "_"
            + publ_date.strftime("%Y%d%m")
            + ".pdf"
        )
        with open(ROOT_DIR + "/" + doc_link + "/" + file_name, "wb") as outfile:
            outfile.write(doc_response.content)
