from urllib.parse import urlparse
from requests import Response
from bs4 import BeautifulSoup


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    return f"{parsed.scheme}://{parsed.netloc}"


def get_accessibility_content(response: Response) -> dict:
    soup = BeautifulSoup(response.text, "html.parser")
    return {
        "status_code": response.status_code,
        "h1": soup.find("h1").text if soup.find("h1") else "",
        "title": soup.title.text if soup.title else "",
        "description": soup.find("meta", attrs={"name": "description"})["content"] if soup.find("meta", attrs={"name": "description"}) else "",
    }
