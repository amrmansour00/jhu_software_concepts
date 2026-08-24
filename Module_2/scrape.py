"""GradCafe scraper for Module 2.

This scraper retrieves graduate admissions records from GradCafe while
failing safely when the website presents an anti-bot or Cloudflare
challenge.

Important:
- robots.txt is checked before scraping.
- Cloudflare/challenge pages are detected before parsing.
- Existing applicant_data.json is NOT overwritten when no valid
  records are collected.
- Parsed records are validated before being saved.
"""

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
    """Scrape graduate admissions records from GradCafe."""

    def __init__(self, max_records=30000):
        """Initialize scraper configuration."""

        self.base_url = "https://www.thegradcafe.com"
        self.survey_url = f"{self.base_url}/survey"
        self.max_records = max_records
        self.output_path = Path(__file__).parent / "applicant_data.json"

    # =====================================================
    # MAIN SCRAPING WORKFLOW
    # =====================================================

    def scrape_data(self):
        """Scrape admissions records and save them when successful."""

        print("Starting GradCafe scraper...")

        if not self._check_robots(self.survey_url):
            print(
                "robots.txt does not allow automated access "
                "to the requested page."
            )
            print("Scraping stopped.")
            return []

        print("robots.txt check passed.")

        driver = self._create_driver()

        records = []
        page = 1
        challenge_detected = False

        try:
            while len(records) < self.max_records:
                url = self._build_url(page)

                print()
                print(f"Opening: {url}")

                driver.get(url)

                # Give the page time to render.
                time.sleep(
                    random.uniform(3, 6)
                )

                html = driver.page_source

                # -----------------------------------------
                # Cloudflare / anti-bot protection
                # -----------------------------------------

                if self._is_challenge_page(html):
                    challenge_detected = True

                    print()
                    print(
                        "Cloudflare or anti-bot challenge detected."
                    )
                    print(
                        "The page does not contain reliable "
                        "GradCafe admissions data."
                    )
                    print(
                        "Stopping safely without overwriting "
                        "the existing applicant_data.json."
                    )

                    break

                # -----------------------------------------
                # Parse page
                # -----------------------------------------

                page_records = self._parse_page(
                    html,
                    url,
                )

                if not page_records:
                    print(
                        "No valid applicant records were found "
                        "on this page."
                    )
                    print(
                        "Stopping without treating page content "
                        "as applicant data."
                    )
                    break

                valid_records = [
                    record
                    for record in page_records
                    if self._is_valid_record(record)
                ]

                if not valid_records:
                    print(
                        "Parsed content did not pass applicant "
                        "record validation."
                    )
                    print("Scraping stopped.")
                    break

                records.extend(
                    valid_records
                )

                print(
                    f"Valid records collected: "
                    f"{len(records):,}"
                )

                page += 1

        finally:
            driver.quit()

        # -------------------------------------------------
        # Do not destroy an existing dataset on failure
        # -------------------------------------------------

        if not records:
            print()
            print("No new valid records were collected.")

            if self.output_path.exists():
                print(
                    "Existing applicant_data.json "
                    "has been preserved."
                )

            if challenge_detected:
                print(
                    "Reason: live site returned an "
                    "anti-bot challenge."
                )

            return []

        # -------------------------------------------------
        # Limit and clean successfully collected records
        # -------------------------------------------------

        records = records[
            : self.max_records
        ]

        records = self.clean_data(
            records
        )

        # -------------------------------------------------
        # Save only successful results
        # -------------------------------------------------

        self.save_data(
            records,
            "applicant_data.json",
        )

        print()
        print(
            f"Saved {len(records):,} valid records "
            "to applicant_data.json"
        )

        return records

    # =====================================================
    # CHALLENGE DETECTION
    # =====================================================

    def _is_challenge_page(self, html):
        """Detect Cloudflare and common anti-bot challenge pages."""

        if not html:
            return True

        lowered = html.casefold()

        markers = [
            "cf_chl_opt",
            "cf-chl",
            "cloudflare",
            "performance and security by cloudflare",
            "verify you are human",
            "checking your browser",
            "attention required",
            "challenge-platform",
            "just a moment",
        ]

        return any(
            marker in lowered
            for marker in markers
        )

    # =====================================================
    # RECORD VALIDATION
    # =====================================================

    def _is_valid_record(self, record):
        """Check whether a parsed record resembles an applicant result."""

        if not isinstance(record, dict):
            return False

        status = record.get(
            "applicant_status"
        )

        if status not in {
            "Accepted",
            "Rejected",
            "Waitlisted",
        }:
            return False

        raw_listing = record.get(
            "raw_listing"
        )

        if not raw_listing:
            return False

        # Reject obvious challenge-page content.
        if self._is_challenge_page(
            raw_listing
        ):
            return False

        return True

    # =====================================================
    # DATA CLEANING
    # =====================================================

    def clean_data(self, records):
        """Normalize whitespace in text fields."""

        cleaned = []

        for source_record in records:
            record = dict(
                source_record
            )

            record["program_name"] = self._clean_text(
                record.get(
                    "program_name"
                )
            )

            record["university"] = self._clean_text(
                record.get(
                    "university"
                )
            )

            record["comments"] = self._clean_text(
                record.get(
                    "comments"
                )
            )

            record["raw_listing"] = self._clean_text(
                record.get(
                    "raw_listing"
                )
            )

            cleaned.append(
                record
            )

        return cleaned

    # =====================================================
    # FILE OPERATIONS
    # =====================================================

    def save_data(
        self,
        data,
        filename="applicant_data.json",
    ):
        """Save applicant records as JSON."""

        output_path = (
            Path(__file__).parent
            / filename
        )

        with output_path.open(
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(
                data,
                file,
                indent=4,
                ensure_ascii=False,
            )

    def load_data(
        self,
        filename="applicant_data.json",
    ):
        """Load applicant records from JSON."""

        input_path = (
            Path(__file__).parent
            / filename
        )

        with input_path.open(
            "r",
            encoding="utf-8",
        ) as file:
            return json.load(file)

    # =====================================================
    # SELENIUM
    # =====================================================

    def _create_driver(self):
        """Create a headless Chrome WebDriver."""

        options = Options()

        options.add_argument(
            "--headless=new"
        )

        options.add_argument(
            "--disable-gpu"
        )

        options.add_argument(
            "--window-size=1920,1080"
        )

        service = Service()

        driver = webdriver.Chrome(
            service=service,
            options=options,
        )

        driver.set_page_load_timeout(
            60
        )

        return driver

    # =====================================================
    # URL HANDLING
    # =====================================================

    def _build_url(self, page):
        """Construct a paginated GradCafe survey URL."""

        query = {
            "page": page,
            "sort": "newest",
        }

        return (
            self.survey_url
            + "?"
            + urllib.parse.urlencode(
                query
            )
        )

    def _check_robots(self, url):
        """Check whether robots.txt permits the requested URL."""

        parser = urllib.robotparser.RobotFileParser()

        parser.set_url(
            f"{self.base_url}/robots.txt"
        )

        try:
            parser.read()

            return parser.can_fetch(
                "*",
                url,
            )

        except Exception as exc:
            print(
                "Unable to verify robots.txt:"
            )
            print(exc)

            # Fail safely rather than assuming permission.
            return False

    # =====================================================
    # PAGE PARSING
    # =====================================================

    def _parse_page(
        self,
        html,
        page_url,
    ):
        """Parse applicant result rows from rendered HTML."""

        soup = BeautifulSoup(
            html,
            "html.parser",
        )

        rows = soup.select(
            "tr"
        )

        records = []

        for row in rows:
            text = self._clean_text(
                row.get_text(
                    " ",
                    strip=True,
                )
            )

            if not text:
                continue

            if not self._contains_status(
                text
            ):
                continue

            record = self._parse_entry(
                row,
                text,
                page_url,
            )

            if record:
                records.append(
                    record
                )

        return records

    def _contains_status(self, text):
        """Check whether text contains an admissions outcome."""

        status_terms = [
            "Accepted",
            "Rejected",
            "Wait listed",
            "Waitlisted",
        ]

        return any(
            term in text
            for term in status_terms
        )

    # =====================================================
    # ENTRY PARSING
    # =====================================================

    def _parse_entry(
        self,
        row,
        raw_text,
        page_url,
    ):
        """Convert one rendered result row into a record."""

        links = row.find_all(
            "a"
        )

        entry_url = page_url

        # Prefer an actual /result/ link where available.
        for link in links:
            href = link.get(
                "href"
            )

            if (
                href
                and "/result/" in href
            ):
                entry_url = urllib.parse.urljoin(
                    self.base_url,
                    href,
                )
                break

        status = self._normalize_status(
            raw_text
        )

        decision_date = self._extract_decision_date(
            raw_text
        )

        start_term = self._extract_start_term(
            raw_text
        )

        degree = self._extract_degree(
            raw_text
        )

        gpa = self._extract_metric(
            raw_text,
            r"\bGPA\s*([0-9.]+)",
        )

        gre = self._extract_metric(
            raw_text,
            r"\bGRE\s*([0-9]{2,3})\b",
        )

        gre_v = self._extract_metric(
            raw_text,
            r"\bGRE V\s*([0-9]{2,3})\b",
        )

        gre_aw = self._extract_metric(
            raw_text,
            r"\bGRE AW\s*([0-9.]+)",
        )

        student_type = self._extract_student_type(
            raw_text
        )

        cells = row.find_all(
            [
                "td",
                "div",
            ]
        )

        cell_texts = [
            self._clean_text(
                cell.get_text(
                    " ",
                    strip=True,
                )
            )
            for cell in cells
        ]

        cell_texts = [
            cell
            for cell in cell_texts
            if cell
        ]

        university = (
            cell_texts[0]
            if len(cell_texts) > 0
            else None
        )

        program_name = (
            cell_texts[1]
            if len(cell_texts) > 1
            else None
        )

        date_added = (
            cell_texts[2]
            if len(cell_texts) > 2
            else None
        )

        return {
            "program_name":
                program_name,

            "university":
                university,

            "comments":
                self._extract_comments(
                    raw_text
                ),

            "date_added":
                date_added,

            "entry_url":
                entry_url,

            "applicant_status":
                status,

            "acceptance_date":
                (
                    decision_date
                    if status == "Accepted"
                    else None
                ),

            "rejection_date":
                (
                    decision_date
                    if status == "Rejected"
                    else None
                ),

            "start_term":
                start_term,

            "student_type":
                student_type,

            "gre_score":
                gre,

            "gre_v_score":
                gre_v,

            "degree":
                degree,

            "gpa":
                gpa,

            "gre_aw":
                gre_aw,

            "raw_listing":
                raw_text,

            "source_page":
                page_url,
        }

    # =====================================================
    # FIELD EXTRACTION
    # =====================================================

    def _normalize_status(self, text):
        """Normalize admission outcome values."""

        if "Accepted" in text:
            return "Accepted"

        if "Rejected" in text:
            return "Rejected"

        if (
            "Wait listed" in text
            or "Waitlisted" in text
        ):
            return "Waitlisted"

        return None

    def _extract_decision_date(self, text):
        """Extract the reported decision date."""

        match = re.search(
            r"(?:Accepted|Rejected|Wait listed|Waitlisted)"
            r"\s+on\s+"
            r"([A-Za-z]{3,9}\s+\d{1,2})",
            text,
        )

        if match:
            return match.group(
                1
            )

        return None

    def _extract_start_term(self, text):
        """Extract the intended start term."""

        match = re.search(
            r"\b("
            r"Fall|Spring|Summer|Winter"
            r")\s+\d{4}\b",
            text,
        )

        if match:
            return match.group(
                0
            )

        return None

    def _extract_degree(self, text):
        """Extract common GradCafe degree categories."""

        patterns = [
            (
                r"\b(?:PhD|Ph\.D\.?)\b",
                "PhD",
            ),
            (
                r"\bPsyD\b",
                "PsyD",
            ),
            (
                r"\bMFA\b",
                "MFA",
            ),
            (
                r"\bJD\b",
                "JD",
            ),
            (
                r"\b(?:Masters?|Master's|MS|MA)\b",
                "Masters",
            ),
            (
                r"\bOther\b",
                "Other",
            ),
        ]

        for pattern, normalized in patterns:
            if re.search(
                pattern,
                text,
                re.IGNORECASE,
            ):
                return normalized

        return None

    def _extract_student_type(self, text):
        """Extract applicant student type."""

        if "International" in text:
            return "International"

        if "American" in text:
            return "American"

        return None

    def _extract_metric(
        self,
        text,
        pattern,
    ):
        """Extract a numeric metric using a regular expression."""

        match = re.search(
            pattern,
            text,
            re.IGNORECASE,
        )

        if match:
            return match.group(
                1
            )

        return None

    def _extract_comments(self, text):
        """Extract comments when identifiable in the listing."""

        if "Added on" in text:
            return text.split(
                "Added on",
                1,
            )[-1].strip()

        return None

    # =====================================================
    # TEXT CLEANING
    # =====================================================

    def _clean_text(self, text):
        """Collapse repeated whitespace."""

        if text is None:
            return None

        cleaned = re.sub(
            r"\s+",
            " ",
            str(text),
        ).strip()

        return cleaned or None


# =========================================================
# COMMAND-LINE ENTRY POINT
# =========================================================

if __name__ == "__main__":
    scraper = GradCafeScraper(
        max_records=30000
    )

    scraper.scrape_data()