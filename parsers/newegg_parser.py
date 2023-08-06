import asyncio
import httpx
from math import ceil
from store import Store
from computer import Computer
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from dataclasses import dataclass


# the code in this file works like ebay_parser.py
@dataclass
class NeweggComputer(Computer):

    def __init__(self, context):
        self.url = context["url"]
        self.title = context["title"]
        self.price = context["price"]
        self.shipping = context["shipping"]

    def __str__(self):
        return f"Title: {self.title}\nPrice: {self.price + ' ' + self.shipping}\nCondition: New\nUrl: {self.url}"

    def get_price(self):
        computer_price = float(self.price.replace("$", "").replace(",", ""))
        first_substring = self.shipping.split(" ")[0]
        if first_substring in ("Free", "Special"):
            shipping_price = 0.0
        else:
            shipping_price = float(first_substring.replace("$", "").replace(",", ""))
        return computer_price + shipping_price

    def to_dict(self):
        dictionary = dict()

        dictionary["url"] = self.url
        dictionary["title"] = self.title
        dictionary["price"] = self.price
        dictionary["shipping"] = self.shipping
        dictionary["condition"] = self.condition

        return dictionary


class Newegg(Store):
    __sort: int = 1
    __query: str = "PC"
    __price_min: float = 0
    __price_max: float = 1000000000
    __sorting_map = {
        "best_match": 0,
        "lowest_price": 1,
        "highest_price": 2,
    }
    __items_per_page = 60
    __max_pages = 2

    def __init__(self, max_pages, items_per_page):
        self.__session = httpx.AsyncClient(follow_redirects=True)
        self.__max_pages = max_pages
        self.__items_per_page = items_per_page

    def make_request(self, page):
        link_keywords = dict()

        link_keywords["d"] = self.__query
        link_keywords["Order"] = self.__sort
        link_keywords["PageSize"] = self.__items_per_page
        link_keywords["page"] = page
        link_keywords["LeftPriceRange"] = str(self.__price_min) + " " + str(self.__price_max)

        url = "https://www.newegg.com/p/pl?" + urlencode(link_keywords)

        print(url)
        return url

    def set_query(self, query):
        self.__query = query.prompt
        self.__price_min = query.price_min
        self.__price_max = query.price_max
        self.__sort = self.__sorting_map[query.sort]
        self.__query += query.gpu.replace("NVIDIA", "").replace("AMD", "") + " "
        self.__query += query.cpu
        self.__query += f" {query.ram} GB"

    @staticmethod
    def __parse_search(bs):
        previews = []
        listing_boxes = bs.find_all("div", class_="item-cell")
        for box in listing_boxes:
            container = box.div
            url = container.a
            if url is None:
                continue
            price = container.find("li", class_="price-current").strong
            if price is None:
                continue
            data = {
                "url": url['href'],
                "title": container.find("a", class_="item-title").text,
                "price": container.find("li", class_="price-current").strong.text + "$",
                "shipping": container.find("li", class_="price-ship").text
            }
            newegg = NeweggComputer(data)
            previews.append(newegg)
        return previews

    async def get_computers(self):

        first_page = await self.__session.get(self.make_request(page=1))
        bs = BeautifulSoup(first_page.content, "lxml")
        results = self.__parse_search(bs)
        if self.__max_pages == 1:
            return results
        # find total amount of results for concurrent pagination
        total_results = bs.find("span", class_="list-tool-pagination-text")
        if not total_results:
            return results
        total_results = int(total_results.strong.text.split("/")[-1])
        total_pages = ceil(total_results / self.__items_per_page)
        if total_pages > self.__max_pages:
            total_pages = self.__max_pages
        other_pages = [self.__session.get(self.make_request(page=i)) for i in range(2, total_pages + 1)]
        for response in asyncio.as_completed(other_pages):
            response = await response
            try:
                results.extend(self.__parse_search(BeautifulSoup(response, "lxml")))
            except Exception:
                print(f"failed to scrape search page {response.url}")
        return results

