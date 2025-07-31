# ATC Code Scraper

This project extracts the **ATC codes (Anatomical Therapeutic Chemical)** classification codes from the Norwegian Medicines Agency's ATC/DDD page

## Features
- It parses the website of [ATC/DDD Index](https://atcddd.fhi.no/atc_ddd_index/)
- Extracts ATC Code, Name and link to corresponding category
- Save data to CSV file
- Print the csv file in a pretty table to view

## Requirements

To install the required dependencies:

1. Optionally create and activate a virtual environment
```bash
python -m venv venv
```
and activate it depending on OS using the following on Ubuntu:
```bash
source ./venv/bin/activate
``` 
or on Windows:
```bash
venv\Scripts\activate
```
2. Install the dependencies from requirements.txt

```bash
pip install -r requirements.txt
```

3. Run the software to store the atc_categories as csv in the same root folder with the name "atc_categories.csv"
```bash
python atc_scraper.py
```

4. CSV output will be the following:


| ATC Code | Description                     | URL                                                                                                                                 |
| -------- | ------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| A        | ALIMENTARY TRACT AND METABOLISM | [https://atcddd.fhi.no/atc\_ddd\_index/?code=A\&showdescription=no](https://atcddd.fhi.no/atc_ddd_index/?code=A&showdescription=no) |
| B        | BLOOD AND BLOOD FORMING ORGANS  | [https://atcddd.fhi.no/atc\_ddd\_index/?code=B\&showdescription=no](https://atcddd.fhi.no/atc_ddd_index/?code=B&showdescription=no) |
| ...      | ...                             | ...                                                                                                                                 |
