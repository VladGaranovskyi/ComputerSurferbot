from parsers.ebay_parser import Ebay
from parsers.newegg_parser import Newegg
from query import Query, FSMQuery
from aiogram import Bot, Dispatcher, executor, types
from aiogram.dispatcher import FSMContext
from aiogram.contrib.fsm_storage.memory import MemoryStorage
import pandas as pd
from os import remove as remove_file

# creating instances
ebay = Ebay(5, 60)

newegg = Newegg(2, 36)

# old test cases
#
# async def get_data(store):
#     store.set_query(
#         Query(
#             prompt="PC",
#             price_min=100,
#             price_max=2000,
#             sort="lowest_price",
#             gpu="NVIDIA GeForce GTX 1650",
#             cpu="",
#             ram=16
#         )
#     )
#     products = await store.get_computers()
#     for product in products:
#         print(product)
#         print(product.get_price())
#     return products
#
# if __name__ == "__main__":
#     asyncio.get_event_loop().run_until_complete(get_data(ebay))


# class EbayTest(IsolatedAsyncioTestCase):
#     async def len_test(self):
#         r = await get_data(ebay)
#         self.assertEquals(len(r), 300)
#
#
# class NeweggTest(IsolatedAsyncioTestCase):
#     async def existence_test(self):
#         r = await get_data(newegg)
#         self.assertGreater(len(r), 0)

API_TOKEN = '6462782345:AAF9DDvM-pgtzXLZTx_cNycFLlNAGd09RHo'

# setting up bot
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# gpu keyboard to let user write down data correctly
gpu_kb = types.ReplyKeyboardMarkup(row_width=2)
gpus_list = ["NVIDIA GeForce GTX 1650", "NVIDIA GeForce GTX 1660", "NVIDIA GeForce GTX 1060", "NVIDIA GeForce GTX 1070",
             "NVIDIA GeForce GTX 1080", "NVIDIA GeForce RTX 2060", "NVIDIA GeForce RTX 2070", "NVIDIA GeForce RTX 2080",
             "NVIDIA GeForce RTX 2050", "NVIDIA GeForce RTX 3060", "NVIDIA GeForce RTX 3070", "NVIDIA GeForce RTX 3080",
             "NVIDIA GeForce RTX 3090", "NVIDIA GeForce RTX 3050", "AMD Radeon RX 560", "AMD Radeon RX 570",
             "AMD Radeon RX 580", "AMD Radeon RX 480", "Skip"]
for gpu in gpus_list:
    gpu_kb.insert(types.KeyboardButton(text=gpu))

# cpu keyboard to let user write down data correctly
cpu_kb = types.ReplyKeyboardMarkup()
cpus_list = ["Intel Core i3", "Intel Core i5", "Intel Core i7", "Intel Core i9", "AMD Ryzen 3", "AMD Ryzen 5",
             "AMD Ryzen 7", "AMD Ryzen 9", "Skip"]
for cpu in cpus_list:
    cpu_kb.insert(types.KeyboardButton(text=cpu))

# ram keyboard to let user write down data correctly
ram_kb = types.ReplyKeyboardMarkup()
ram_sizes = ["16", "8", "4", "32", "64", "Skip"]
for ram in ram_sizes:
    ram_kb.insert(types.KeyboardButton(text=ram))

# sort keyboard to let user write down data correctly
sort_kb = types.ReplyKeyboardMarkup()
sort_types = ["Lowest Price", "Highest Price", "Best Match"]
for sort in sort_types:
    sort_kb.insert(types.KeyboardButton(text=sort))


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    await message.answer("Hi!\nI'm ComputerSurfer!\nI will help find you a computer on Ebay and Newegg"
                         "type /search to search some computers")


# starting point of search command
@dp.message_handler(commands=['search'], state=None)
async def start_search(message: types.Message):
    await FSMQuery.gpu.set()
    await message.answer("GPU:", reply_markup=gpu_kb)


# gpu state
@dp.message_handler(state=FSMQuery.gpu)
async def set_gpu(message: types.Message, state: FSMContext):
    # opening state proxy in order to save data there
    async with state.proxy() as data:
        # checking for existing of the answer in keyboard
        if message.text in gpus_list:
            # cancel if user doesn't want to specify it
            if message.text != "Skip":
                data["gpu"] = message.text
        else:
            await message.answer("Please, choose gpu from these buttons", reply_markup=gpu_kb)
            return
    # going to the next state
    await FSMQuery.next()
    await message.answer("CPU:", reply_markup=cpu_kb)


@dp.message_handler(state=FSMQuery.cpu)
async def set_cpu(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text in cpus_list:
            if message.text != "Skip":
                data["cpu"] = message.text
        else:
            await message.answer("Please, choose cpu from these buttons", reply_markup=cpu_kb)
            return
    await FSMQuery.next()
    await message.answer("RAM Size:", reply_markup=ram_kb)


@dp.message_handler(state=FSMQuery.ram)
async def set_ram(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text in ram_sizes:
            if message.text != "Skip":
                data["ram"] = int(message.text)
        else:
            await message.answer("Please, choose ram size from these buttons", reply_markup=ram_kb)
            return
    await FSMQuery.next()
    await message.answer("Enter the Minimal price in $:")


@dp.message_handler(state=FSMQuery.price_min)
async def set_price_min(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data["price_min"] = int(message.text)
        except Exception:
            await message.answer("Please enter a number")
            return None
    await FSMQuery.next()
    await message.answer("Enter the Maximal price in $:")


@dp.message_handler(state=FSMQuery.price_max)
async def set_price_max(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        try:
            data["price_max"] = int(message.text)
        except Exception:
            await message.answer("Please enter a number")
            return None
    await FSMQuery.next()
    await message.answer("Sorting order:", reply_markup=sort_kb)


@dp.message_handler(state=FSMQuery.sort)
async def set_sort(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        if message.text in sort_types:
            if message.text != "Skip":
                data["sort"] = message.text.lower().replace(" ", "_")
        else:
            await message.answer("Please, choose sort type from these buttons", reply_markup=sort_kb)
            return

    async with state.proxy() as data:
        # creating query instance
        query = Query(sort=data["sort"], price_max=data["price_max"], price_min=data["price_min"])
        if "gpu" in data.keys():
            query.gpu = data["gpu"]
        if "cpu" in data.keys():
            query.cpu = data["cpu"]
        if "ram" in data.keys():
            query.ram = data["ram"]
        # setting query
        ebay.set_query(query)
        newegg.set_query(query)
        # getting computers, sorting them by price and then converting them to data frame
        computers_ebay = await ebay.get_computers()
        computers_newegg = await newegg.get_computers()
        computers = computers_ebay + computers_newegg
        if query.sort != "best_match":
            computers = sorted(computers, reverse=(query.sort == "highest_price"))
        computers_dicts = [c.to_dict() for c in computers]
        computers_df = pd.DataFrame(computers_dicts)
        # giving the csv file to user, then deleting it from the local storage
        computers_df.to_csv(f"table{message.chat.id}.csv")
        await message.answer_document(open(f"table{message.chat.id}.csv", "rb"))
        remove_file(f"table{message.chat.id}.csv")

    await state.finish()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
