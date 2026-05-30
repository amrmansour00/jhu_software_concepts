from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service


def scrape_data():

    print("TEST START")

    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--disable-gpu")
    options.add_argument("--window-size=1920,1080")

    service = Service()

    driver = webdriver.Chrome(
        service=service,
        options=options
    )

    driver.set_page_load_timeout(30)

    driver.get("https://www.google.com")

    print(driver.title)

    driver.quit()


if __name__ == "__main__":
    scrape_data()