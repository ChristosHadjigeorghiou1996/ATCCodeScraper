from pathlib import Path
from re import compile, Pattern
from time import sleep

from bs4 import BeautifulSoup, Tag
from requests import get
from tabulate import tabulate

from src.classes.atc_code import ATCCode
from src.helpers.file_helper import FileHelper

class ATCScraper:
    """
    Class to scraper atc codes from the website and parse them to ATCCode
    """
    def __init__(self, base_url: str = "https://atcddd.fhi.no/"):
        self.base_url = base_url
        self.atc_index = f"{self.base_url}/atc_ddd_index/"
        self.headers = {
            "User-Agent":"Mozilla/5.0"
        }
        self.timeout = 10
        self.code_pattern = compile(r"code=([A-Z])")
        self.subcategory_pattern = compile(r"code=([A-Z0-9]+)")
        self.soup = None
        # remember visited code to avoid in recursion
        self.visited: set[str] = set()

    def parse_website_with_soup(self, website: str) -> BeautifulSoup:
        """
        Parse the website to bs4 object to parse it.
        """
        sleep(.5)
        response = get(website, headers=self.headers, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        return soup

    def _extract_atc_codes_from_text(self, content_to_parse: Tag, regex_pattern: Pattern) -> list[ATCCode]:
        """
        Parse the content of the ATC page and get the codes according to regex
        :param content_to_parse: tag element of paragraph to parse
        :param regex_pattern: pattern to apply to get code
        :return list of ATCCode
        """
        atc_categories: list[ATCCode] = []
        for a in content_to_parse.find_all("a"):
            href: str = a.get("href", "")
            code_match = regex_pattern.search(href)
            if code_match:
                code = code_match.group(1)
                name = a.text.strip()
                url = f"{self.atc_index}{href.lstrip('./')}"
                atc_code = ATCCode(code, name, url)
                atc_categories.append(atc_code)
        return atc_categories

    def obtain_atc_categories(self) -> list[ATCCode]:
        """
        Get the main categories of ATC
        :return the list of extracted ATCCode
        """
        website_soup = self.parse_website_with_soup(self.atc_index)
        sleep(.5)
        # find the title and get the next paragraph containing the categories
        atc_h3 = website_soup.find("h3", string="ATC code")
        atc_paragraph = atc_h3.find_next("p")
        return self._extract_atc_codes_from_text(atc_paragraph, self.code_pattern)

    def obtain_atc_subcategories(self, atc_category: ATCCode) -> list[ATCCode]:
        """
        Recursively obtain subcategories from ATCCode category
        :param atc_category: ATCCode to parse and use url
        :return the list of extracted ATCCode
        """
        if atc_category.url in self.visited:
            return []
        self.visited.add(atc_category.url)
        atc_subcategories: list[ATCCode] = []
        c_website_soup = self.parse_website_with_soup(atc_category.url)
        atc_c_code = c_website_soup.find(string=atc_category.name)
        if not atc_c_code:
            return []
        atc_subcategory_paragraph = atc_c_code.find_next("p")
        if not atc_subcategory_paragraph:
            return []
        atc_subcategories = self._extract_atc_codes_from_text(atc_subcategory_paragraph, self.subcategory_pattern)
        for subcategory in atc_subcategories:
            atc_subcategories.extend(self.obtain_atc_subcategories(subcategory))
        return atc_subcategories

    def map_code_to_category(self, code: str) -> str|ATCCode:
        """
        Map a string code to atc categories given first letter
        :param code: string of code to check if it matches in category
        :return mapped ATCCode or "Unknown" otherwise 
        """
        atc_categories = self.obtain_atc_categories()
        match = list(atc_category for atc_category in atc_categories if code[0] == atc_category.code)
        if match:
            print(f"Code {code} -> {match[0]}")
            return match[0]
        return "Unknown"


if __name__ == "__main__":
    atc_scraper = ATCScraper()
    extracted_atc_categories: list[ATCCode] = list()
    filepath = Path("atc_categories.csv")
    if not filepath.exists():
        atc_categories = atc_scraper.obtain_atc_categories()
        extracted_atc_categories.extend(atc_categories)
        for atc_category in atc_categories:
            print(atc_category)
            atc_subcategories = atc_scraper.obtain_atc_subcategories(atc_category)
            extracted_atc_categories.extend(atc_subcategories)
        FileHelper.save_to_csv(filepath, extracted_atc_categories)
    else:
        rows = FileHelper.read_from_csv(filepath)
        # print(tabulate(rows[1:], headers=rows[0], tablefmt="grid"))

    code_mapping = atc_scraper.map_code_to_category('AB0123')
