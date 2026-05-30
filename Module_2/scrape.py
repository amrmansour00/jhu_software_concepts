import json
import time
import random
import urllib.robotparser


class GradCafeScraper:
    def __init__(self):
        self.base_url = "https://www.thegradcafe.com"

    def scrape_data(self):
        print("Scraping started...")

        target_url = self.base_url

        if not self._check_robots(target_url):
            print("robots.txt does not allow scraping this URL.")
            return []

        print("robots.txt check passed.")
        return []

    def save_data(self, data, filename="applicant_data.json"):
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4, ensure_ascii=False)

    def load_data(self, filename="applicant_data.json"):
        with open(filename, "r", encoding="utf-8") as file:
            return json.load(file)

    def _check_robots(self, url):
        robots_url = f"{self.base_url}/robots.txt"

        parser = urllib.robotparser.RobotFileParser()
        parser.set_url(robots_url)
        parser.read()

        return parser.can_fetch("*", url)

    def _delay(self):
        time.sleep(random.uniform(2, 5))


if __name__ == "__main__":
    scraper = GradCafeScraper()
    data = scraper.scrape_data()
    scraper.save_data(data)
    print(f"Records collected: {len(data)}")