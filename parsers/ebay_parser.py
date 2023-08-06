import asyncio
import httpx
from math import ceil
from store import Store
from computer import Computer
from urllib.parse import urlencode
from bs4 import BeautifulSoup
from dataclasses import dataclass


@dataclass
class EbayComputer(Computer):

    # init with simple context(dict)
    def __init__(self, context):
        self.url = context["url"]
        self.title = context["title"]
        self.price = context["price"]
        self.shipping = context["shipping"]
        self.condition = context["condition"]

    # more beautiful repr
    def __str__(self):
        return f"Title: {self.title}\nPrice: {self.price + ' ' + self.shipping}\nCondition: {self.condition if self.condition else 'No info'}\nUrl: {self.url}"

    # get price including shipping
    def get_price(self):
        computer_price = float(self.price.replace("$", "").replace(",", "")) if "to" not in self.price else float(
            (float(self.price.split(" to ")[0].replace("$", "").replace(",", '')) + float(self.price.split(" to ")[1]
                                                                            .replace("$", "").replace(",", ''))) / 2
        )
        shipping_price = float(self.shipping.split(" ")[0].replace(",", "").replace("+$", "")) if self.shipping \
            and self.shipping not in ("Shipping not specified", "Free International Shipping") else 0.0
        return computer_price + shipping_price

    # dict convert
    def to_dict(self):
        dictionary = dict()

        dictionary["url"] = self.url
        dictionary["title"] = self.title
        dictionary["price"] = self.price
        dictionary["shipping"] = self.shipping
        dictionary["condition"] = self.condition

        return dictionary


class Ebay(Store):
    __filters: dict = dict()
    __sort: int = 15
    __query: str = "PC"
    __price_min: float = 0
    __price_max: float = 1000000000
    # sorting of the website encoding
    __sorting_map = {
        "best_match": 12,
        "lowest_price": 15,
        "highest_price": 16,
    }
    __items_per_page = 240
    __max_pages = 1

    def __init__(self, max_pages, items_per_page):
        # starting async client
        self.__session = httpx.AsyncClient(follow_redirects=True)

        self.__max_pages = max_pages
        self.__items_per_page = items_per_page


    @staticmethod
    def __parse_search(bs):
        # creating list of computers
        previews = []
        # getting li items from search
        listing_boxes = bs.find_all("li", class_="s-item")
        # removing first element (it has similar class but it's hidden and is from template with no info
        listing_boxes = listing_boxes[1:len(listing_boxes)]
        for box in listing_boxes:
            # iterating everything
            div_info = box.div.find("div", class_="s-item__info clearfix")
            shipping = div_info.find("div", class_="s-item__details clearfix").find("span", class_="s-item__shipping")
            condition = div_info.find("div", class_="s-item__subtitle").span
            data = {
                    "url": div_info.a['href'],
                    "title": div_info.a.div.span.text,
                    "price": div_info.find("div", class_="s-item__details clearfix")
                    .find("span", class_="s-item__price").text,
                    "shipping": shipping.text if shipping else "",
                    "condition": condition.text if condition else "",
                   }
            product = EbayComputer(data)
            previews.append(product)
        return previews

    # applying data from query class
    def set_query(self, query):
        self.__price_min = query.price_min
        self.__price_max = query.price_max
        self.__sort = self.__sorting_map[query.sort]
        self.__query = query.prompt
        if query.gpu:
            self.__filters["GPU"] = query.gpu.replace(" ", "%20")
        if query.cpu:
            self.__query += " " + query.cpu
        if query.ram > 0:
            self.__filters["RAM%20Size"] = f"{query.ram}%20GB"
        if query.ram <= 0 and not query.gpu:
            self.__filters = dict()

    def make_request(self, page):
        link_keywords = dict()

        # query
        link_keywords["_nkw"] = self.__query
        # sort method
        link_keywords["_sop"] = self.__sort
        link_keywords["_ipg"] = self.__items_per_page
        link_keywords["_pgn"] = page
        link_keywords["_udlo"] = self.__price_min
        link_keywords["_udhi"] = self.__price_max

        # adding filters
        if self.__filters:
            for parameter, val in self.__filters.items():
                link_keywords[parameter] = val

        # url encoding
        url = "https://www.ebay.com/sch/179/i.html?" + urlencode(link_keywords)

        print(url)
        return url

    async def get_computers(self):
        # getting first page to find out how many pages it has
        first_page = await self.__session.get(self.make_request(page=1))
        # parsing it
        bs = BeautifulSoup(first_page.content, "lxml")
        # getting computers
        results = self.__parse_search(bs)
        if self.__max_pages == 1:
            return results
        # find total amount of results for concurrent pagination
        total_results = bs.find("h1", class_="srp-controls__count-heading").span.text
        total_results = int(total_results.split(" ")[0].replace(",", ""))
        total_pages = ceil(total_results / self.__items_per_page)
        if total_pages > self.__max_pages:
            total_pages = self.__max_pages
        # getting all other pages to iterate them in for loop
        other_pages = [self.__session.get(self.make_request(page=i)) for i in range(2, total_pages + 1)]
        for response in asyncio.as_completed(other_pages):
            response = await response
            try:
                results.extend(self.__parse_search(BeautifulSoup(response, "lxml")))
            except Exception:
                print(f"failed to scrape search page {response.url}")
        return results

