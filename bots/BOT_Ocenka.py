import logging
import asyncio
import os
from aiogram import Bot, Dispatcher, F, types
from aiogram.client.default import DefaultBotProperties
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN5')
ADMIN_CHAT_ID = int(os.getenv('ADMIN_CHAT_ID'))

logging.basicConfig(level=logging.INFO)

bot = Bot(token=API_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

class AppraisalForm(StatesGroup):
    object_type = State()
    purpose = State()
    region = State()
    area = State()
    comment = State()
    contact = State()

object_kb = ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [KeyboardButton(text="1. Квартира"), KeyboardButton(text="2. Дом")],
    [KeyboardButton(text="3. Земельный участок"), KeyboardButton(text="4. Коммерция")],
    [KeyboardButton(text="🔙 Назад")]
])

@dp.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    await message.answer("<b>Добро пожаловать!</b>\n\n"
                                       "Нужна официальная оценка недвижимости? 🏢 Мы подготовим отчет за 1 день!* ✅ Для банков, судов, сделок ✅ Гарантия принятия документа\n"
                                       "Пожалуйста, заполняйте все поля внимательно и максимально подробно, "
                                       "чтобы наши специалисты могли связаться с вами и помочь быстро и качественно.")
    await message.answer("Для продолжения нажмите нужный вам вариант. Что хотели бы оценить?", reply_markup=object_kb)
    await state.set_state(AppraisalForm.object_type)

@dp.message(F.text == "🔙 Назад")
async def go_back(message: types.Message, state: FSMContext):
    current = await state.get_state()
    steps = list(AppraisalForm.__all_states__)
    if current == steps[0]:
        await message.answer("Вы на начальном шаге. Укажите тип объекта:")
    else:
        idx = steps.index(current) - 1
        await state.set_state(steps[idx])
        await message.answer("⬅️ Вернулись на предыдущий шаг. Введите данные снова:")

@dp.message(AppraisalForm.object_type)
async def handle_object(message: types.Message, state: FSMContext):
    await state.update_data(object_type=message.text)
    await state.set_state(AppraisalForm.purpose)
    await message.answer("🎯 Укажите цель оценки (например: для продажи, для суда, для ипотеки):")

@dp.message(AppraisalForm.purpose)
async def handle_purpose(message: types.Message, state: FSMContext):
    await state.update_data(purpose=message.text)
    await state.set_state(AppraisalForm.region)
    await message.answer("🌍 Укажите регион или адрес объекта:")

@dp.message(AppraisalForm.region)
async def handle_region(message: types.Message, state: FSMContext):
    await state.update_data(region=message.text)
    await state.set_state(AppraisalForm.area)
    await message.answer("📐 Укажите площадь объекта в м²:")

@dp.message(AppraisalForm.area)
async def handle_area(message: types.Message, state: FSMContext):
    await state.update_data(area=message.text)
    await state.set_state(AppraisalForm.comment)
    await message.answer("📝 Есть ли дополнительные данные или комментарии?")

@dp.message(AppraisalForm.comment)
async def handle_comment(message: types.Message, state: FSMContext):
    await state.update_data(comment=message.text)
    await state.set_state(AppraisalForm.contact)
    await message.answer("📞 Укажите ваше имя и телефон для связи:")

@dp.message(AppraisalForm.contact)
async def handle_contact(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.text)
    data = await state.get_data()

    result = (
        f"<b>📩 Новая заявка на оценку:</b>\n"
        f"🏠 Объект: {data.get('object_type')}\n"
        f"🎯 Цель: {data.get('purpose')}\n"
        f"🌍 Регион: {data.get('region')}\n"
        f"📐 Площадь: {data.get('area')}\n"
        f"📝 Комментарий: {data.get('comment')}\n"
        f"📞 Контакт: {data.get('contact')}"
    )

    await bot.send_message(chat_id=ADMIN_CHAT_ID, text=result)
    await message.answer("✅ Спасибо! Ваша заявка отправлена. Мы скоро свяжемся с вами.")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
