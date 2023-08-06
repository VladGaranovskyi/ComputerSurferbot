from abc import ABC, abstractmethod
from dataclasses import dataclass, field


# computer interface
@dataclass
class Computer(ABC):
    url: str
    title: str
    price: str
    shipping: str
    condition: str = field(default="New")

    @abstractmethod
    def __str__(self):
        ...

    @property
    @abstractmethod
    def get_price(self):
        ...

    @property
    @abstractmethod
    def to_dict(self):
        ...

    def __lt__(self, other):
        return self.get_price() < other.get_price()

    def __gt__(self, other):
        return self.get_price() > other.get_price()

    def __ge__(self, other):
        return self.get_price() >= other.get_price()

    def __le__(self, other):
        return self.get_price() <= other.get_price()


