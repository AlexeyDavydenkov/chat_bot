from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from Apisite.core import headers, params, site_api, url
from database.common.models import db, History
from database.core import crud
from settings import BotSettings

#Инициализация бота и настройка параметров
bot = BotSettings()
bot = Bot(token=bot.bot_key.get_secret_value())
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
dp.middleware.setup(LoggingMiddleware())

#Получение фактов о городах из API сайта
fact_by = site_api.get_fact()

#Минимальное и максимальное значение численности по умолчанию
min_population = 100000
max_population = 400000

#Объекты для работы с базой данных
db_write = crud.create()
db_read = crud.retrieve()

#Классы состояний для FSM
class UserData(StatesGroup):
    awaiting_city = State()

class ParamsData(StatesGroup):
    awaiting_min_value = State()
    awaiting_max_value = State()


def my_city(*args, **kwargs) -> dict:
    """Функция получения информации о городе из API"""
    fact_by = site_api.get_fact()
    responce = fact_by(*args, **kwargs)
    responce = responce.json()
    return responce

def write_history(data: list):
    """Функция записи запросов в базу данных"""
    db_write(db, History, data)
    History.clean_history()

#Обработчик команды /start
@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    buttons = [
        types.KeyboardButton(text='MIN'),
        types.KeyboardButton(text='MAX'),
        types.KeyboardButton(text='Город'),
        types.KeyboardButton(text='Параметры'),
        types.KeyboardButton(text='История запросов')
    ]
    keyboard.add(*buttons)

    await message.reply("Привет! Я бот городов России!\n"
        "Ознакомься с моей функциональностью по команде /info или начни работу.",
                        reply_markup=keyboard)

#Обработчик команды /info
@dp.message_handler(commands=['info'])
async def send_info(message: types.Message):
    await message.reply('Данный бот имеет следующую функциональность:'
                '\nнажимая кнопку "Параметры"'
                'Вы можете ввести минимальную и максимальную численность населения (по умолчанию минимальная '
                    'численность населения установлена - 100000 человек, максимальная - 400000 человек).\n'
                '\nПри нажатии кнопки "MIN" бот выдаст Вам город с наименьшей численностью населения исходя '
                    'из выбранных Вами параметров.\n'
                '\nПри нажатии кнопки "MAX" бот выдаст Вам город напротив, с '
                    'наибольшей численностью населения исходя из выбранных Вами параметров\n'
                '\nВыбирая кнопку "Город", Вам будет предложено ввести название интересующего Вас города '
                    'на что вы получите ответ в виде численности населения введенного Вами города '
                    '(для более точного результата, рекомендуем вводить название полностью, но бот будет '
                    'работать и по префиксу названия города).\n'
                '\nИ наконец нажимая кнопку "История запросов" Вы получите последние 10 результатов введенных запросов.\n'
                    '\nПриятного пользования!')

#Обработчик кнопки "Город"
@dp.message_handler(lambda message: message.text == 'Город')
async def process_city_start(message: types.Message):
    await message.answer('Введите название города')
    await UserData.awaiting_city.set()

#Обработчик ввода названия города
@dp.message_handler(state=UserData.awaiting_city)
async def process_city(message: types.Message, state: FSMContext):
    name_city = message.text
    params['namePrefix'] = name_city
    params["minPopulation"] = None
    params["maxPopulation"] = None
    params["sort"] = None
    try:
        my_responce = my_city('Get', url, headers, params, timeout=5)
        for elem in my_responce['data']:
            name = elem.get('name')
            population = elem.get('population')
            data = [{'message': elem.get('name'), 'number': elem.get('population')}]
            write_history(data)
        await message.answer('Город {}\nЧисленность населения: {} человек'.format(name, population))
    except NameError:
        await message.answer('Такого города нет в России, начните снова и введите корректное название города')
    await state.finish()

#Обработчик кнопки "Параметры"
@dp.message_handler(lambda message: message.text == 'Параметры')
async def process_params_start(message: types.Message):
    await message.answer('Введите минимальное значение населения')
    await ParamsData.awaiting_min_value.set()

#Обработчик ввода мимимального значения
@dp.message_handler(state=ParamsData.awaiting_min_value)
async def process_min_value(message: types.Message, state: FSMContext):
    global min_population
    min_population = message.text
    if not min_population.isnumeric():
        await message.answer('Вы ввели не число, начните заново и введите пожалуйста число')
    else:
        await message.answer('Введите максимальное значение населения')
    await ParamsData.awaiting_max_value.set()

#Обработчик ввода максимального значения
@dp.message_handler(state=ParamsData.awaiting_max_value)
async def process_max_value(message: types.Message, state: FSMContext):
    global max_population
    max_population = message.text
    if not max_population.isnumeric():
        await message.answer('Вы ввели не число, начните заново и введите пожалуйста число: ')
    else:
        await message.answer(f'Минимальное значение: {min_population}, максимальное значение: {max_population}')
    await state.finish()

#Обработчик кнопки "MIN"
@dp.message_handler(lambda message: message.text == 'MIN')
async def process_option(message: types.Message):
    params["sort"] = "population",
    params["minPopulation"] = str(min_population)
    params["maxPopulation"] = str(max_population)
    params['namePrefix'] = None
    my_responce = my_city('Get', url, headers, params, timeout=5)
    for elem in my_responce['data']:
        name = elem.get('name')
        population = elem.get('population')
        data = [{'message': elem.get('name'), 'number': elem.get('population')}]
        write_history(data)
    await message.answer(f'Город {name}\nЧисленность населения: {population} человек')

#Обработчик кнопки "MAX"
@dp.message_handler(lambda message: message.text == 'MAX')
async def process_option(message: types.Message):
    params["sort"] = "-population",
    params["minPopulation"] = str(min_population)
    params["maxPopulation"] = str(max_population)
    params['namePrefix'] = None
    my_responce = my_city('Get', url, headers, params, timeout=5)
    for elem in my_responce['data']:
        name = elem.get('name')
        population = elem.get('population')
        data = [{'message': elem.get('name'), 'number': elem.get('population')}]
        write_history(data)
    await message.answer(f'Город {name}\nЧисленность населения: {population} человек')

#Обработчик кнопки "История запросов"
@dp.message_handler(lambda message: message.text == 'История запросов')
async def process_history(message: types.Message):
    reteieved = db_read(db, History, History.message, History.number)
    if reteieved:
        for elem in reteieved:
            await message.answer(f'Город:{elem.message, }\nчисленность населения: {elem.number}')
    else:
        await message.answer('Список истории запросов пуст')

#Запуск бота
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

