import bs4 as bs
from parser.core.sync_parser import SyncParser

from config.settings import settings


class StupinoFlatLinks:
    def __init__(self):
        self.parser = SyncParser()

    def get_links(self, url):
        content = self.parser.parse(url)
        if content:
            soup = bs.BeautifulSoup(content, "html.parser")
            pagination_links = soup.find_all(
                "a", href=True, attrs={"data-value": True}
            )
            links = soup.find_all(
                "a", href=True, attrs={"data-marker": "item-title"}
            )
            return list(set(links)), pagination_links


if __name__ == "__main__":
    p = StupinoFlatLinks()
    links, pages = p.get_links(settings.target_url)
    if links:
        with open("links.txt", "w") as f:
            for link in links:
                f.write(link["href"] + "\n")
    if pages:
        with open("pages.txt", "w") as f:
            for page in pages:
                f.write(page["href"] + "\n")
    else:
        print("No links found")
