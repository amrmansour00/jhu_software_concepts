import json
import random
import re
import time
import urllib.parse
import urllib.robotparser
from pathlib import Path

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


class GradCafeScraper:
    def __init__(self, max_records=30000):
        self.base_url = "https://www.thegradcafe.com"
        self.survey_url = f"{self.base_url}/survey"
        self.max_records = max_records

    def scrape_data(self):
        print("Starting GradCafe scraper...")

        if not self._check_robots(self.survey_url):
            print("robots.txt does not allow scraping this page.")
            return []

        print("robots.txt check passed.")

        driver = self._create_driver()
        records = []
        page = 1

        try:
            while len(records) < self.max_records:
                url = self._build_url(page)
                print(f"Scraping page {page}: {url}")

                driver.get(url)
                time.sleep(random.uniform(3, 6))

                html = driver.page_source
                page_records = self._parse_page(html, url)

                if not page_records:
                    print("No records found. Stopping.")
                    break

                records.extend(page_records)
                print(f"Total records: {len(records)}")

                page += 1

        finally:
            driver.quit()

        records = records[: self.max_records]
        self.save_data(records, "applicant_data.json")

        print(f"Saved {len(records)} records to applicant_data.json")
        return records

    def clean_data(self, records):
        cleaned = []

        for record in records:
            record["program_name"] = self._clean_text(record.get("program_name"))
            record["university"] = self._clean_text(record.get("university"))
            record["comments"] = self._clean_text(record.get("comments"))
            record["raw_listing"] = self._clean_text(record.get("raw_listing"))
            cleaned.append(record)

        return cleaned

    def save_data(self, data, filename="applicant_data.json"):
        output_path = Path(__file__).parent / filename

        with open(output_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def load_data(self, filename="applicant_data.json"):
        input_path = Path(__file__).parent / filename

        with open(input_path, "r", encoding="utf-8") as file:
            return json.load(file)

    def _create_driver(self):
        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        service = Service()

        driver = webdriver.Chrome(service=service, options=options)
        driver.set_page_load_timeout(60)

        return driver

    def _build_url(self, page):
        query = {
            "page": page,
            "sort": "newest",
        }

        return self.survey_url + "?" + urllib.parse.urlencode(query)

    def _check_robots(self, url):
        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(f"{self.base_url}/robots.txt")
        parser.read()

        return parser.can_fetch("*", url)

    def _parse_page(self, html, page_url):
        soup = BeautifulSoup(html, "html.parser")

        rows = soup.select("tr")
        records = []

        for row in rows:
            text = self._clean_text(row.get_text(" ", strip=True))

            if not text:
                continue

            if "Accepted" not in text and "Rejected" not in text and "Wait listed" not in text and "Waitlisted" not in text:
                continue

            record = self._parse_entry(row, text, page_url)

            if record:
                records.append(record)

        return records

    def _parse_entry(self, row, raw_text, page_url):
        links = row.find_all("a")
        entry_url = page_url

        if links:
            href = links[-1].get("href")

            if href:
                entry_url = urllib.parse.urljoin(self.base_url, href)

        status = self._normalize_status(raw_text)
        decision_date = self._extract_decision_date(raw_text)
        start_term = self._extract_start_term(raw_text)
        degree = self._extract_degree(raw_text)

        gpa = self._extract_metric(raw_text, r"GPA\s*([0-9.]+)")
        gre = self._extract_metric(raw_text, r"GRE\s*([0-9]{2,3})")
        gre_v = self._extract_metric(raw_text, r"GRE V\s*([0-9]{2,3})")
        gre_aw = self._extract_metric(raw_text, r"GRE AW\s*([0-9.]+)")

        student_type = None
        if "International" in raw_text:
            student_type = "International"
        elif "American" in raw_text:
            student_type = "American"

        cells = row.find_all(["td", "div"])
        cell_texts = [self._clean_text(cell.get_text(" ", strip=True)) for cell in cells]
        cell_texts = [cell for cell in cell_texts if cell]

        university = cell_texts[0] if len(cell_texts) > 0 else None
        program_name = cell_texts[1] if len(cell_texts) > 1 else None
        date_added = cell_texts[2] if len(cell_texts) > 2 else None

        return {
            "program_name": program_name,
            "university": university,
            "comments": self._extract_comments(raw_text),
            "date_added": date_added,
            "entry_url": entry_url,
            "applicant_status": status,
            "acceptance_date": decision_date if status == "Accepted" else None,
            "rejection_date": decision_date if status == "Rejected" else None,
            "start_term": start_term,
            "student_type": student_type,
            "gre_score": gre,
            "gre_v_score": gre_v,
            "degree": degree,
            "gpa": gpa,
            "gre_aw": gre_aw,
            "raw_listing": raw_text,
            "source_page": page_url,
        }

    def _normalize_status(self, text):
        if "Accepted" in text:
            return "Accepted"

        if "Rejected" in text:
            return "Rejected"

        if "Wait listed" in text or "Waitlisted" in text:
            return "Waitlisted"

        return None

    def _extract_decision_date(self, text):
        match = re.search(
            r"(Accepted|Rejected|Wait listed|Waitlisted)\s+on\s+([A-Za-z]{3,9}\s+\d{1,2})",
            text,
        )

        if match:
            return match.group(2)

        return None

    def _extract_start_term(self, text):
        match = re.search(r"(Fall|Spring|Summer|Winter)\s+\d{4}", text)

        if match:
            return match.group(0)

        return None

    def _extract_degree(self, text):
        if "PhD" in text or "Ph.D" in text:
            return "PhD"

        if "Masters" in text or "Master" in text or "MS" in text or "MA" in text:
            return "Masters"

        return None

    def _extract_metric(self, text, pattern):
        match = re.search(pattern, text)

        if match:
            return match.group(1)

        return None

    def _extract_comments(self, text):
        if "Added on" in text:
            return text.split("Added on")[-1].strip()

        return None

    def _clean_text(self, text):
        if text is None:
            return None

        text = re.sub(r"\s+", " ", text)
        return text.strip()


if __name__ == "__main__":
    scraper = GradCafeScraper(max_records=50)
    scraper.scrape_data()