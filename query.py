from dataclasses import dataclass, field
from aiogram.dispatcher.filters.state import State, StatesGroup


@dataclass
class Query:
    price_min: int = field(default=0)
    price_max: int = field(default=7000)
    sort: str = field(default="best_match")
    gpu: str = field(default="")
    cpu: str = field(default="")
    ram: int = field(default=16)
    prompt: str = field(default="PC")


class FSMQuery(StatesGroup):
    gpu = State()
    cpu = State()
    ram = State()
    price_min = State()
    price_max = State()
    sort = State()



