from csv import writer, reader
from pathlib import Path

from src.classes.atc_code import ATCCode


class FileHelper:
    """
    Class to write atc categories to csv files
    """
    @staticmethod
    def save_to_csv(filename: Path, atc_categories: list[ATCCode]) -> None:
        """
        Save atc_categories to filename provided
        :param filename: file to save to
        :param atc_categories: list of atc categories to save to csv
        """
        if filename.suffix == (".csv"):
            with open(filename, 'w', newline="", encoding="utf-8") as f:
                csv_writer = writer(f)
                csv_writer.writerow(["ATC Code", "ATC Name", "URL"])
                for category in atc_categories:
                    csv_writer.writerow([category.code, category.name, category.url])
            print(f"Saved {atc_categories} at {filename}")
        else:
            print(f"Filename: '{filename}' does not have a .csv extension. Please use that format to save.")

    @staticmethod
    def read_from_csv(path_to_file: Path) -> list[str]:
        """
        Read csv file and return list of rows
        :param path_to_file: filepath to read
        """
        if path_to_file.suffix == (".csv"):
            with open(path_to_file, "r", newline="", encoding="utf-8") as f:
                csv_reader = reader(f)
                rows = list(csv_reader)
                return rows
        else:
            print(f"Filename: '{path_to_file}' does not have a .csv extension. Please use that format to save.")