from pathlib import Path
from re import compile, Pattern
from time import sleep
from csv import writer

from bs4 import BeautifulSoup, Tag
import requests
from tabulate import tabulate

from src.classes.atc_code import ATCCode
from src.helpers.file_helper import FileHelper

class ATCScraper:
    """
    Class to scraper atc codes from the website and parse them to ATCCode
    """
    def __init__(self, base_url: str = "https://atcddd.fhi.no/", request_delay: float = 0.5):
        self.base_url = base_url.rstrip("/")
        self.atc_index = f"{self.base_url}/atc_ddd_index/"
        self.headers = {
            "User-Agent": "Mozilla/5.0",
        }
        self.timeout = 10
        self.request_delay = request_delay
        self.code_pattern = compile(r"code=([A-Z])")
        self.subcategory_pattern = compile(r"code=([A-Z0-9]+)")
        # remember visited code to avoid in recursion
        self.visited: set[str] = set()
        # cache top-level categories to avoid repeated scraping / parsing
        self._atc_categories_cache: list[ATCCode] | None = None

        # reuse HTTP connection across requests
        self.session = requests.Session()
        self.session.headers.update(self.headers)

    def parse_website_with_soup(self, website: str) -> BeautifulSoup:
        """
        Parse the website to bs4 object to parse it.
        """
        sleep(self.request_delay)
        response = self.session.get(website, timeout=self.timeout)
        response.raise_for_status()
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
        if self._atc_categories_cache is not None:
            return self._atc_categories_cache

        website_soup = self.parse_website_with_soup(self.atc_index)
        # find the title and get the next paragraph containing the categories
        atc_h3 = website_soup.find("h3", string="ATC code")
        atc_paragraph = atc_h3.find_next("p")
        self._atc_categories_cache = self._extract_atc_codes_from_text(atc_paragraph, self.code_pattern)
        return self._atc_categories_cache

    def obtain_atc_subcategories(self, atc_category: ATCCode) -> list[ATCCode]:
        """
        Recursively obtain subcategories from ATCCode category
        :param atc_category: ATCCode to parse and use url
        :return the list of extracted ATCCode
        """
        if atc_category.url in self.visited:
            return []
        self.visited.add(atc_category.url)
        c_website_soup = self.parse_website_with_soup(atc_category.url)
        atc_c_code = c_website_soup.find(string=atc_category.name)
        if not atc_c_code:
            return []
        atc_subcategory_paragraph = atc_c_code.find_next("p")
        if not atc_subcategory_paragraph:
            return []
        direct_subcategories = self._extract_atc_codes_from_text(atc_subcategory_paragraph, self.subcategory_pattern)
        all_subcategories: list[ATCCode] = []
        for subcategory in direct_subcategories:
            all_subcategories.append(subcategory)
            all_subcategories.extend(self.obtain_atc_subcategories(subcategory))
        return all_subcategories

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

    def save_mappings_to_csv(self, codes: list[str], filename: Path) -> None:
        """Save mappings from input codes to main ATC category into a CSV file.

        The CSV will contain columns: Input Code, ATC Code, ATC Name, URL.
        Unknown codes will have "Unknown" for the ATC Code and empty name/url.
        """
        if filename.suffix != ".csv":
            raise ValueError("Output filename must have .csv extension")

        with open(filename, "w", newline="", encoding="utf-8") as f:
            csv_writer = writer(f)
            csv_writer.writerow(["Input Code", "ATC Code", "ATC Name", "URL"])
            for code in codes:
                mapping = self.map_code_to_category(code)
                if isinstance(mapping, ATCCode):
                    csv_writer.writerow([code, mapping.code, mapping.name, mapping.url])
                else:
                    csv_writer.writerow([code, "Unknown", "", ""])

        print(f"Saved code-to-category mappings for {len(codes)} code(s) to {filename}")

    def save_all_mappings_to_csv(self, atc_codes: list[ATCCode], filename: Path) -> None:
        """Save mappings for all scraped ATC codes to their main ATC category.

        The CSV will contain columns:
        ATC Code, ATC Name, URL, Main ATC Code, Main ATC Name, Main ATC URL.
        """
        if filename.suffix != ".csv":
            raise ValueError("Output filename must have .csv extension")

        # Get top-level categories (single-letter codes) from the site/cache
        top_level_categories = [
            cat for cat in self.obtain_atc_categories() if len(cat.code) == 1
        ]
        top_level_by_code = {cat.code: cat for cat in top_level_categories}

        with open(filename, "w", newline="", encoding="utf-8") as f:
            csv_writer = writer(f)
            csv_writer.writerow([
                "ATC Code",
                "ATC Name",
                "URL",
                "Main ATC Code",
                "Main ATC Name",
                "Main ATC URL",
            ])

            for atc in atc_codes:
                if not atc.code:
                    continue
                main_code = atc.code[0]
                main_cat = top_level_by_code.get(main_code)
                if main_cat is not None:
                    csv_writer.writerow([
                        atc.code,
                        atc.name,
                        atc.url,
                        main_cat.code,
                        main_cat.name,
                        main_cat.url,
                    ])
                else:
                    csv_writer.writerow([
                        atc.code,
                        atc.name,
                        atc.url,
                        "Unknown",
                        "",
                        "",
                    ])

        print(f"Saved mappings for {len(atc_codes)} ATC code(s) to {filename}")


if __name__ == "__main__":
    atc_scraper = ATCScraper()
    extracted_atc_categories: list[ATCCode] = list()
    filepath = Path("atc_categories.csv")
    all_atc_codes: list[ATCCode] = []
    if not filepath.exists():
        atc_categories = atc_scraper.obtain_atc_categories()
        extracted_atc_categories.extend(atc_categories)
        for atc_category in atc_categories:
            print(atc_category)
            atc_subcategories = atc_scraper.obtain_atc_subcategories(atc_category)
            extracted_atc_categories.extend(atc_subcategories)
        FileHelper.save_to_csv(filepath, extracted_atc_categories)
        all_atc_codes = extracted_atc_categories
    else:
        rows = FileHelper.read_from_csv(filepath)
        # first row is headers
        all_atc_codes = [
            ATCCode(code=row[0], name=row[1], url=row[2]) for row in rows[1:] if len(row) >= 3
        ]
        # print(tabulate(rows[1:], headers=rows[0], tablefmt="grid"))

    # Save mappings for all ATC codes scraped from the website/CSV
    mapping_filepath = Path("all_atc_mappings.csv")
    atc_scraper.save_all_mappings_to_csv(all_atc_codes, mapping_filepath)
