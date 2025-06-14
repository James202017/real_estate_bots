import logging
import asyncio
import sys
import os
from dotenv import load_dotenv

try:
    import ssl
except ModuleNotFoundError:
    ssl = None
    logging.error("Модуль SSL не найден. Проверьте наличие OpenSSL в вашей системе.")

from aiogram import Bot, Dispatcher, F, types
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение значений из переменных окружения
API_TOKEN = os.getenv('API_TOKEN1')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID'))

# Проверка наличия необходимых переменных окружения
if not API_TOKEN:
    raise ValueError("API_TOKEN1 не найден в .env файле")
if not ADMIN_CHAT_ID:
    raise ValueError("ADMIN_CHAT_ID не найден в .env файле")

logging.basicConfig(level=logging.INFO)

# Проверка SSL перед запуском бота
if ssl is None:
    sys.exit("Ошибка: Модуль SSL недоступен. Установите OpenSSL или используйте среду с поддержкой SSL.")

# Инициализация бота
bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# Состояния опросника
class SaleForm(StatesGroup):
    property_type = State()
    location = State()
    details = State()
    price = State()
    contact = State()

# Клавиатура выбора типа недвижимости
property_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="Квартира"), KeyboardButton(text="Дом")],
    [KeyboardButton(text="Дача"), KeyboardButton(text="Участок")],
    [KeyboardButton(text="Коммерческая недвижимость")],
    [KeyboardButton(text="🔙 Назад")]
])

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await message.answer("<b>Добро пожаловать!</b>\n\n"
                        "Этот помощник поможет вам оставить заявку на покупку недвижимости.\n"
                        "Пожалуйста, заполняйте все поля внимательно и максимально подробно, "
                        "чтобы наши специалисты могли связаться с вами и помочь быстро и качественно.")
    await message.answer("Для продолжения нажмите нужный вам вариант. Что хотели бы купить?", reply_markup=property_kb)
    await state.set_state(SaleForm.property_type)

@dp.message(F.text == "🔙 Назад")
async def go_back(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    state_list = list(SaleForm.__all_states__)
    if current_state == state_list[0]:
        await message.answer("Вы на начальном этапе. Выберите тип недвижимости.", reply_markup=property_kb)
    else:
        prev_index = state_list.index(current_state) - 1
        await state.set_state(state_list[prev_index])
        await message.answer("Вернулись на предыдущий шаг. Введите данные снова:")

@dp.message(SaleForm.property_type)
async def process_type(message: types.Message, state: FSMContext):
    await state.update_data(property_type=message.text)
    await state.set_state(SaleForm.location)
    await message.answer("Укажите населенный пункт, район, какие есть пожелания:", reply_markup=ReplyKeyboardRemove())

@dp.message(SaleForm.location)
async def process_location(message: types.Message, state: FSMContext):
    await state.update_data(location=message.text)
    await state.set_state(SaleForm.details)
    await message.answer("Укажите метраж, количество комнат и прочие детали:")

@dp.message(SaleForm.details)
async def process_details(message: types.Message, state: FSMContext):
    await state.update_data(details=message.text)
    await state.set_state(SaleForm.price)
    await message.answer("Укажите желаемую цену:")

@dp.message(SaleForm.price)
async def process_price(message: types.Message, state: FSMContext):
    await state.update_data(price=message.text)
    await state.set_state(SaleForm.contact)
    await message.answer("Оставьте ваш телефон и имя:")

@dp.message(SaleForm.contact)
async def process_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()

    summary = (
        f"<b>Новая заявка на покупку:</b>\n"
        f"Тип: {data['property_type']}\n"
        f"Адрес: {data['location']}\n"
        f"Детали: {data['details']}\n"
        f"Цена: {data['price']}\n"
        f"Контакт: {data['contact']}"
    )
    await bot.send_message(ADMIN_CHAT_ID, summary)
    await message.answer("Спасибо! Ваша заявка отправлена. Наш специалист свяжется с вами.")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
