import selenium.webdriver as webdriver
from selenium.webdriver.edge.service import Service
# from selenium.webdriver.chrome.service import Service
import time
from bs4 import BeautifulSoup

def scrape_website(website):
    print("Launching your Browser...")

    msedge_drive_path = "drivers\msedgedriver.exe"
    options = webdriver.EdgeOptions()
    driver = webdriver.Edge(service=Service(msedge_drive_path), options=options)


    try:
        driver.get(website)
        print("Website page Loading:", driver.title)
        html = driver.page_source
        print("Website page loaded successfully.")
        # time.sleep(5)

        return html
    finally:
        driver.quit()
        print("Browser closed.")



def extract_body_content(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    body_content = soup.body
    if body_content:
        return str(body_content)
    return ""
    


def clean_body_content(body_content):
    soup = BeautifulSoup(body_content, 'html.parser')

    for script_or_style in soup(['script', 'style']):
        script_or_style.decompose()

    cleaned_content = soup.get_text(separator='\n', strip=True)
    cleaned_content = "\n".join(
        line.strip() for line in cleaned_content.splitlines() if line.strip()
    )

    return cleaned_content


def split_dom_content(dom_content, max_length=6000):
    return [
        dom_content[ i : i+max_length] for i in range(0, len(dom_content), max_length)
    ]