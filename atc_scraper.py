from pathlib import Path
from re import compile

from bs4 import BeautifulSoup
from requests import get
from tabulate import tabulate

from src.classes.atc_code import ATCCode
from src.helpers.file_helper import FileHelper

class ATCScraper:
    """
    Class to scraper atc codes from the website and parse them to ATCCode
    """
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.atc_index = f"{self.base_url}/atc_ddd_index/"
        self.headers = {
            "User-Agent":"Mozilla/5.0"
        }
        self.timeout = 10
        self.code_pattern = compile(r"code=([A-Z])")
        self.soup = None

    def parse_website_with_soup(self) -> BeautifulSoup:
        """
        Parse the website to bs4 object to parse it.
        """
        response = get(self.atc_index, headers=self.headers, timeout=10)
        self.soup = BeautifulSoup(response.content, "html.parser")

    def obtain_atc_categories(self) -> list[ATCCode]:
        # find the title and get the next paragraph containing the categories
        atc_h3 = self.soup.find("h3", string="ATC code")
        atc_paragraph = atc_h3.find_next("p")
        # parse the 
        atc_categories: list[ATCCode] = []
        for a in atc_paragraph.find_all("a"):
            href: str = a.get("href", "")
            code_match = self.code_pattern.search(href)
            if code_match:
                code = code_match.group(1)
                name = a.text.strip()
                atc_code = ATCCode(code, name, f"{self.atc_index}{href.lstrip('./')}")
                atc_categories.append(atc_code)
        return atc_categories



if __name__ == "__main__":
    atc_scraper = ATCScraper("https://atcddd.fhi.no/")
    atc_scraper.parse_website_with_soup()
    atc_categories = atc_scraper.obtain_atc_categories()
    filepath = Path("atc_categories.csv")
    FileHelper.save_to_csv(filepath, atc_categories)
    if filepath.exists():
        rows = FileHelper.read_from_csv(filepath)
        print(tabulate(rows[1:], headers=rows[0], tablefmt="grid"))

