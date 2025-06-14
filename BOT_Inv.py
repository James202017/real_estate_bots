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
from aiogram.types import ReplyKeyboardMarkup, ReplyKeyboardRemove, KeyboardButton, InputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties

# Загрузка переменных окружения из .env файла
load_dotenv()

# Получение значений из переменных окружения
API_TOKEN = os.getenv('API_TOKEN3')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID'))

# Проверка наличия необходимых переменных окружения
if not API_TOKEN:
    raise ValueError("API_TOKEN3 не найден в .env файле")
if not ADMIN_CHAT_ID:
    raise ValueError("ADMIN_CHAT_ID не найден в .env файле")

logging.basicConfig(level=logging.INFO)

if ssl is None:
    sys.exit("Ошибка: Модуль SSL недоступен. Установите OpenSSL или используйте среду с поддержкой SSL.")

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

class InvestForm(StatesGroup):
    direction = State()
    amount = State()
    term = State()
    comment = State()
    contact = State()

invest_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="Новостройки (доход до 3 млн руб и выше)")],
    [KeyboardButton(text="Зарубежная недвижимость")],
    [KeyboardButton(text="Выкуп лотов ниже рынка")],
    [KeyboardButton(text="Вклады под 29% годовых")],
    [KeyboardButton(text="🔙 Назад")]
])

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await message.answer(
        "<b>Добро пожаловать!</b>\n\n"
        "С помощью этого помощника вы можете оставить заявку на инвестиционные предложения. "
        "Выгодные инвестиции: зарубежная недвижимость, вклады под 29% годовых, пассивный доход.\n"
        "Пожалуйста, заполняйте все поля внимательно и максимально подробно, "
        "чтобы наши специалисты могли связаться с вами и помочь быстро и качественно."
    )
    await message.answer(
        "🔹 <b>Рекомендации:</b>\n"
        "— Указывайте максимум информации\n"
        "— Все поля обязательны\n"
        "— Мы подберем выгодное решение по вашему профилю"
    )
    await state.set_state(InvestForm.direction)
    await message.answer("Выберите направление инвестиций:", reply_markup=invest_kb)

@dp.message(F.text == "🔙 Назад")
async def go_back(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    state_list = list(InvestForm.__all_states__)
    if current_state == state_list[0]:
        await message.answer("Вы на начальном этапе. Выберите направление инвестиций:", reply_markup=invest_kb)
    else:
        prev_index = state_list.index(current_state) - 1
        await state.set_state(state_list[prev_index])
        await message.answer("⬅️ Вернулись на предыдущий шаг. Введите данные снова:")

@dp.message(InvestForm.direction)
async def process_direction(message: types.Message, state: FSMContext):
    valid_options = [
        "Новостройки (доход до 3 млн руб и выше)",
        "Зарубежная недвижимость",
        "Выкуп лотов ниже рынка",
        "Вклады под 29% годовых"
    ]
    if message.text not in valid_options:
        await message.answer("❗Пожалуйста, выберите вариант из списка.", reply_markup=invest_kb)
        return
    await state.update_data(direction=message.text)
    await state.set_state(InvestForm.amount)
    await message.answer("💰 Укажите желаемую сумму инвестиций:", reply_markup=ReplyKeyboardRemove())

@dp.message(InvestForm.amount)
async def process_amount(message: types.Message, state: FSMContext):
    if not message.text.strip():
        await message.answer("❗Это поле обязательно. Укажите сумму.")
        return
    await state.update_data(amount=message.text)
    await state.set_state(InvestForm.term)
    await message.answer("📅 На какой срок планируете инвестировать?\n(например: 6 месяцев, 1 год, долгосрочно)")

@dp.message(InvestForm.term)
async def process_term(message: types.Message, state: FSMContext):
    if not message.text.strip():
        await message.answer("❗Пожалуйста, укажите срок.")
        return
    await state.update_data(term=message.text)
    await state.set_state(InvestForm.comment)
    await message.answer("📝 Есть ли дополнительные пожелания или комментарии?")

@dp.message(InvestForm.comment)
async def process_comment(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await state.set_state(InvestForm.contact)
    await message.answer("📞 Укажите ваше имя и номер телефона для связи:")

@dp.message(InvestForm.contact)
async def process_contact(message: types.Message, state: FSMContext):
    if not message.text.strip():
        await message.answer("❗Контактные данные обязательны.")
        return
    await state.update_data(contact=message.text)
    data = await state.get_data()

    summary = (
        f"<b>📥 Новая заявка на инвестиции:</b>\n"
        f"🔸 Направление: {data.get('direction')}\n"
        f"🔸 Сумма: {data.get('amount')}\n"
        f"🔸 Срок: {data.get('term')}\n"
        f"🔸 Комментарий: {data.get('comment')}\n"
        f"🔸 Контакт: {data.get('contact')}"
    )

    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=summary)
    await message.answer("✅ Спасибо! Ваша заявка отправлена. Наш консультант скоро свяжется с вами.")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except RuntimeError as e:
        if 'asyncio.run() cannot be called from a running event loop' in str(e):
            import nest_asyncio
            nest_asyncio.apply()
            asyncio.get_event_loop().run_until_complete(main())
        else:
            raise
