import logging
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.utils import executor
from datetime import datetime

API_TOKEN = "7978486552:AAGGWOueJcz4Nv5paNZpXpMzfXhXtFkwa2I"
CHANNEL_ID = "@birgetest"
ADMIN_PASSWORD = "birgebest"
LANGUAGES = ["🇷🇺 Русский", "🇰🇬 Кыргызча"]

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

# FSM
class Form(StatesGroup):
    Language = State()
    WaitingPassword = State()
    Title = State()
    Date = State()
    Location = State()
    Description = State()
    Photo = State()
    Confirm = State()

user_data = {}
admins = set()

# Старт
@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    for lang in LANGUAGES:
        markup.add(KeyboardButton(lang))
    await message.answer("🌐 Пожалуйста, выберите язык / Тилди тандаңыз:", reply_markup=markup)
    await Form.Language.set()

@dp.message_handler(state=Form.Language)
async def language_handler(message: types.Message, state: FSMContext):
    lang = message.text
    if lang not in LANGUAGES:
        return await message.reply("⛔ Пожалуйста, выберите один из предложенных языков.")
    await state.update_data(language=lang)
    await message.answer("🔐 Введите пароль для доступа к админке или нажмите «Пропустить»", reply_markup=cancel_skip())
    await Form.WaitingPassword.set()

@dp.message_handler(state=Form.WaitingPassword)
async def password_handler(message: types.Message, state: FSMContext):
    if message.text.lower() == "пропустить":
        await start_title(message, state)
    elif message.text == ADMIN_PASSWORD:
        admins.add(message.from_user.id)
        await message.reply("✅ Пароль принят! Вы вошли как админ.")
        await start_title(message, state)
    else:
        await message.reply("❌ Неверный пароль.")

async def start_title(message, state):
    await message.answer("✏️ Введите название мероприятия", reply_markup=cancel_skip())
    await Form.Title.set()

@dp.message_handler(state=Form.Title)
async def title_handler(message: types.Message, state: FSMContext):
    if message.text.lower() == "пропустить":
        await state.update_data(title=None)
    else:
        await state.update_data(title=message.text)
    await message.answer("📅 Когда состоится мероприятие?", reply_markup=cancel_skip())
    await Form.Date.set()

@dp.message_handler(state=Form.Date)
async def date_handler(message: types.Message, state: FSMContext):
    if message.text.lower() == "пропустить":
        await state.update_data(date=None)
    else:
        await state.update_data(date=message.text)
    await message.answer("📍 Где пройдёт мероприятие?", reply_markup=cancel_skip())
    await Form.Location.set()

@dp.message_handler(state=Form.Location)
async def location_handler(message: types.Message, state: FSMContext):
    if message.text.lower() == "пропустить":
        await state.update_data(location=None)
    else:
        await state.update_data(location=message.text)
    await message.answer("📝 Добавьте описание:", reply_markup=cancel_skip())
    await Form.Description.set()

@dp.message_handler(state=Form.Description)
async def desc_handler(message: types.Message, state: FSMContext):
    if message.text.lower() == "пропустить":
        await state.update_data(description=None)
    else:
        await state.update_data(description=message.text)
    await message.answer("📸 Добавьте фото (или нажмите «Пропустить»):", reply_markup=cancel_skip())
    await Form.Photo.set()

@dp.message_handler(content_types=['photo'], state=Form.Photo)
async def photo_handler(message: types.Message, state: FSMContext):
    photo_id = message.photo[-1].file_id
    await state.update_data(photo=photo_id)
    await confirm_post(message, state)

@dp.message_handler(state=Form.Photo)
async def skip_photo_handler(message: types.Message, state: FSMContext):
    if message.text.lower() == "пропустить":
        await state.update_data(photo=None)
        await confirm_post(message, state)
    else:
        await message.answer("📸 Пожалуйста, отправьте фото или нажмите «Пропустить».")

async def confirm_post(message: types.Message, state: FSMContext):
    data = await state.get_data()
    text = "✨ Новое мероприятие:\n"
    if data.get("title"): text += f"📌 Название: {data['title']}\n"
    if data.get("date"): text += f"🗓 Дата: {data['date']}\n"
    if data.get("location"): text += f"📍 Локация: {data['location']}\n"
    if data.get("description"): text += f"📝 Описание: {data['description']}\n"
    text += "\n**БИРГЕ — ПЛАТФОРМА ВОЗМОЖНОСТЕЙ**\n@nicevolunteer"

    if data.get("photo"):
        await bot.send_photo(message.chat.id, data["photo"], caption=text)
    else:
        await message.answer(text)

    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("✅ Опубликовать", callback_data="publish"))
    markup.add(InlineKeyboardButton("❌ Отменить", callback_data="cancel"))
    await message.answer("Вы хотите опубликовать?", reply_markup=markup)
    await Form.Confirm.set()

@dp.callback_query_handler(state=Form.Confirm)
async def confirm_callback(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if call.data == "publish":
        text = "✨ Новое мероприятие:\n"
        if data.get("title"): text += f"📌 Название: {data['title']}\n"
        if data.get("date"): text += f"🗓 Дата: {data['date']}\n"
        if data.get("location"): text += f"📍 Локация: {data['location']}\n"
        if data.get("description"): text += f"📝 Описание: {data['description']}\n"
        text += "\n**БИРГЕ — ПЛАТФОРМА ВОЗМОЖНОСТЕЙ**\n@nicevolunteer"

        if data.get("photo"):
            await bot.send_photo(CHANNEL_ID, data["photo"], caption=text)
        else:
            await bot.send_message(CHANNEL_ID, text)
        await call.message.answer("✅ Опубликовано!")
    else:
        await call.message.answer("❌ Отменено.")

    await state.finish()

# Команда для админки
@dp.message_handler(commands=['birge'])
async def birge_admin(message: types.Message):
    if message.from_user.id in admins:
        await message.answer("🔧 Добро пожаловать в админ-панель!")
    else:
        await message.answer("🚫 У вас нет доступа.")

# Cancel / Skip кнопки
def cancel_skip():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("Пропустить"))
    markup.add(KeyboardButton("Отмена"))
    return markup

# Отмена
@dp.message_handler(lambda message: message.text.lower() == 'отмена', state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    await state.finish()
    await message.answer("❌ Отменено. Чтобы начать заново: /start")

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)