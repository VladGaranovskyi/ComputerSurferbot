from abc import ABC, abstractmethod


# store interface
class Store(ABC):

    @abstractmethod
    async def get_computers(self):
        ...

    @abstractmethod
    def make_request(self, page):
        ...

    @abstractmethod
    def set_query(self, query):
        ...
