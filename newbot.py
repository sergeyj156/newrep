import asyncio
import aiosqlite
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.callback_data import CallbackData
from aiogram.utils.exceptions import MessageToDeleteNotFound
from aiogram.dispatcher import FSMContext
from openpyxl import Workbook
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram import types
from aiogram.dispatcher.filters import Text

class PostState(StatesGroup):
    WAITING_FOR_POST = State()

from aiogram.dispatcher.filters.state import State, StatesGroup





ADMIN_ID = 679030634  # ID администратора

def is_admin(user_id):
    return user_id == ADMIN_ID

API_TOKEN = '7033678803:AAFgvv-6M1yRr_iJAgQDiN6C5lpYjMfNIoc'
async def set_webhook():
    await bot.set_webhook(url="")


bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
dp.middleware.setup(LoggingMiddleware())

callback_data = CallbackData('menu', 'item')
last_messages = []

async def create_db():
    async with aiosqlite.connect('users_activity.db') as db:
        await db.execute("PRAGMA foreign_keys = ON")
        await db.execute('''CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL UNIQUE, username TEXT, balance INTEGER DEFAULT 0)''')
        await db.execute('''CREATE TABLE IF NOT EXISTS activities (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, type TEXT NOT NULL, count INTEGER DEFAULT 0, FOREIGN KEY(user_id) REFERENCES users(user_id))''')
        await db.execute('''CREATE TABLE IF NOT EXISTS code_words (id INTEGER PRIMARY KEY AUTOINCREMENT, word TEXT NOT NULL UNIQUE, points INTEGER DEFAULT 0)''')
        await db.commit()

async def get_user_balance(user_id: int) -> int:
    async with aiosqlite.connect('users_activity.db') as db:
        async with db.execute('SELECT balance FROM users WHERE user_id = ?', (user_id,)) as cursor:
            row = await cursor.fetchone()
            return row[0] if row else 0

async def show_main_menu(chat_id):
    keyboard_markup = InlineKeyboardMarkup(row_width=1)
    btns_text = ['Правила', 'Каналы и чаты для участия', 'Мои баллы', 'Получить баллы', 'Рейтинг', 'Ачивки', 'Помощь']
    for text in btns_text:
        keyboard_markup.add(InlineKeyboardButton(text, callback_data=callback_data.new(item=text.replace(" ", "_").lower())))
    photo_path = '/Users/sergejavkin/PycharmProjects/Пробный бот/100Б/privet.jpg'
    with open(photo_path, 'rb') as photo:
        await bot.send_photo(chat_id, photo, caption="Привет! Ты попал в меню бота 100балльного репетитора 😎 \n\nСобрали здесь все кнопки для навигации, чтобы ты быстро подключился к гонке за баллами и смог отследить свой прогресс за месяц.", reply_markup=keyboard_markup)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username
    # Вызываем функцию для добавления или обновления пользователя в базе данных
    await add_or_update_user(user_id, username)
    # Показываем главное меню
    await show_main_menu(message.from_user.id)

# Функция для добавления или обновления пользователя в базе данных
async def add_or_update_user(user_id: int, username: str):
    async with aiosqlite.connect('users_activity.db') as db:
        await db.execute('''INSERT INTO users (user_id, username) VALUES (?, ?)
                            ON CONFLICT(user_id) DO UPDATE SET username=excluded.username''',
                         (user_id, username))
        await db.commit()


from io import BytesIO
from aiogram.types import InputMediaPhoto
last_messages = []  # Список для хранения message_id отправленных сообщений и фотографий

@dp.callback_query_handler(callback_data.filter(item='правила'))
async def show_rules(call: types.CallbackQuery):
    global last_messages
    last_messages.clear()
    photo_paths = [
        '/Users/sergejavkin/PycharmProjects/Пробный бот/100Б/pervay.jpg',
        '/Users/sergejavkin/PycharmProjects/Пробный бот/100Б/vtoroy.jpg',
        '/Users/sergejavkin/PycharmProjects/Пробный бот/100Б/treriy.jpg',
        '/Users/sergejavkin/PycharmProjects/Пробный бот/100Б/chet.jpg',
        '/Users/sergejavkin/PycharmProjects/Пробный бот/100Б/pyt.jpg',
        '/Users/sergejavkin/PycharmProjects/Пробный бот/100Б/six.jpg',
    ]

    media = [InputMediaPhoto(open(photo_path, 'rb')) for photo_path in photo_paths]
    media_messages = await bot.send_media_group(chat_id=call.message.chat.id, media=media)
    for msg in media_messages:
        last_messages.append(msg.message_id)

    rules_text = "Внимательно изучи карточки, что не пропустить ничего важного! Если возникнут вопросы, переходи в раздел «помощь». Менеджер подключится и поможет со всем разобраться ❤"
    rules_message = await call.message.answer(rules_text, reply_markup=InlineKeyboardMarkup().add(
        InlineKeyboardButton('Вернуться назад', callback_data='menu:back_to_menu')))
    last_messages.append(rules_message.message_id)

@dp.callback_query_handler(callback_data.filter(item='back_to_menu'))
async def back_to_menu(call: types.CallbackQuery):
    for msg_id in last_messages:
        try:
            await bot.delete_message(chat_id=call.message.chat.id, message_id=msg_id)
        except Exception as e:
            print(f"Не удалось удалить сообщение: {e}")  # Логируем ошибку, если сообщение не найдено или уже удалено
    last_messages.clear()  # Очищаем список, т.к. все сообщения удалены
    await show_main_menu(call.from_user.id)  # Вызываем функцию, которая показывает главное меню



@dp.callback_query_handler(callback_data.filter(item='мои_баллы'))
async def show_my_points(call: types.CallbackQuery):
    await call.message.delete()
    balance = await get_user_balance(call.from_user.id)
    message = f'Ух-ты! На твоём счету уже {balance} баллов 😉\n\nПродолжай в том же духе, чтобы в конце месяца получить топовый приз.' if balance > 0 else 'Ой, у тебя пока 0 баллов...\n\nВозвращайся в главное меню и кликай на кнопку «канал и чаты для участия».'
    await call.message.answer(message, reply_markup=InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton('Вернуться назад', callback_data=callback_data.new(item='back_to_menu'))))

@dp.callback_query_handler(callback_data.filter(item='получить_баллы'))
async def earn_points(call: types.CallbackQuery):
    await call.message.delete()
    points_markup = InlineKeyboardMarkup(row_width=1)
    buttons = [
        InlineKeyboardButton("Отправить кодовое", callback_data='send_code'),
        InlineKeyboardButton("Отправить пост", callback_data='send_post'),
        InlineKeyboardButton("Пригласить друга", callback_data='invite_friend'),
        InlineKeyboardButton("Вернуться назад", callback_data='menu:back_to_menu')
    ]
    points_markup.add(*buttons)
    await call.message.answer("Выбери, как ты хочешь заработать баллы:", reply_markup=points_markup)




@dp.callback_query_handler(callback_data.filter(item='back_to_menu'))
async def back_to_menu(call: types.CallbackQuery):
    global last_messages
    # Удаление всех сообщений, включая фото и текст с правилами
    for msg_id in last_messages:
        try:
            await bot.delete_message(chat_id=call.message.chat.id, message_id=msg_id)
        except MessageToDeleteNotFound:
            print(f"Сообщение для удаления не найдено: {msg_id}")
    last_messages.clear()

    # Удаление кнопки, с которой был произведен вызов
    try:
        await bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except MessageToDeleteNotFound:
        print(f"Сообщение для удаления не найдено: {call.message.message_id}")

    # Показ главного меню
    await show_main_menu(call.from_user.id)


@dp.message_handler(commands=['admin'])
async def admin_menu(message: types.Message):
    if is_admin(message.from_user.id):
        await show_admin_menu(message.chat.id)
    else:
        await message.reply("Доступ запрещен.")

async def show_admin_menu(chat_id):
    admin_markup = InlineKeyboardMarkup(row_width=2)
    buttons = [
        InlineKeyboardButton("Добавить кодовое слово", callback_data='admin:add_code'),
        InlineKeyboardButton("Удалить кодовое слово", callback_data='admin:delete_code'),
        InlineKeyboardButton("Показать все кодовые слова", callback_data='admin:show_codes'),
        InlineKeyboardButton("Выгрузить базу участников", callback_data='admin:export_users')
    ]
    admin_markup.add(*buttons)
    await bot.send_message(chat_id, "Административное меню:", reply_markup=admin_markup)

from aiogram.dispatcher.filters.state import State, StatesGroup

class AdminCodeState(StatesGroup):
    waiting_for_code_word = State()
    waiting_for_code_word_input = State() # Состояние для ожидания ввода кодового слова и количества баллов

@dp.callback_query_handler(lambda c: c.data == 'admin:add_code', state=None)
async def admin_add_code_start(call: types.CallbackQuery):
    if call.from_user.id == ADMIN_ID:  # Проверка, что пользователь является администратором
        await AdminCodeState.waiting_for_code_word.set()
        await call.message.answer("Введите кодовое слово и количество баллов через пробел.")
    else:
        await call.answer("Доступ запрещен.", show_alert=True)


@dp.message_handler(state=AdminCodeState.waiting_for_code_word)
async def admin_add_code_finish(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['code_word'] = message.text.split()[0]  # Получаем кодовое слово
        data['points'] = message.text.split()[1]  # Получаем количество баллов

    # Здесь логика для добавления кодового слова и количества баллов в базу данных
    async with aiosqlite.connect('users_activity.db') as db:
        await db.execute("INSERT INTO code_words (word, points) VALUES (?, ?)",
                         (data['code_word'], int(data['points'])))
        await db.commit()

    await message.answer(f"Кодовое слово '{data['code_word']}' с {data['points']} баллами успешно добавлено.")
    await state.finish()  # Выходим из состояния

@dp.callback_query_handler(lambda c: c.data == 'admin:show_codes', user_id=ADMIN_ID)
async def admin_show_codes(call: types.CallbackQuery):
    async with aiosqlite.connect('users_activity.db') as db:  # Исправленный синтаксис
        cursor = await db.execute("SELECT word, points FROM code_words")
        codes_data = await cursor.fetchall()
        if codes_data:
            codes_list = "\n".join([f"{word} - {points} балл(ов)" for word, points in codes_data])
            await call.message.answer(f"Кодовые слова и баллы:\n{codes_list}")
        else:
            await call.message.answer("Список кодовых слов пуст.")


class AdminCodeState(StatesGroup):
    waiting_for_code_word = State()  # Состояние для ожидания ввода кодового слова и количества баллов
    waiting_for_code_word_to_delete = State()  # Состояние для ожидания ввода кодового слова для удаления

@dp.message_handler(state=AdminCodeState.waiting_for_code_word_to_delete)
async def delete_code_word(message: types.Message, state: FSMContext):
    code_word_to_delete = message.text.strip()
    async with aiosqlite.connect('users_activity.db') as db:
        # Проверяем, существует ли кодовое слово в базе данных
        cursor = await db.execute("SELECT id FROM code_words WHERE word = ?", (code_word_to_delete,))
        if await cursor.fetchone() is not None:
            # Удаляем кодовое слово, если оно найдено
            await db.execute("DELETE FROM code_words WHERE word = ?", (code_word_to_delete,))
            await db.commit()
            await message.answer(f"Кодовое слово '{code_word_to_delete}' было успешно удалено.")
        else:
            await message.answer(f"Кодовое слово '{code_word_to_delete}' не найдено в базе данных.")
    await state.finish()

@dp.callback_query_handler(lambda c: c.data == 'admin:delete_code', user_id=ADMIN_ID)
async def prompt_code_word_deletion(call: types.CallbackQuery):
    await AdminCodeState.waiting_for_code_word_to_delete.set()
    await call.message.answer("Введите кодовое слово, которое нужно удалить:")

async def export_users_to_excel():
    async with aiosqlite.connect('users_activity.db') as db:
        cursor = await db.execute("SELECT user_id, username, balance FROM users")
        users_data = await cursor.fetchall()

    # Создаем новую книгу Excel
    wb = Workbook()
    ws = wb.active
    ws.title = "Users Data"

    # Добавляем заголовки столбцов
    ws.append(["User ID", "Username", "Balance"])

    # Добавляем данные участников
    for user in users_data:
        ws.append(user)

    # Сохраняем файл
    filename = "users_data.xlsx"
    wb.save(filename)

    return filename

@dp.callback_query_handler(lambda c: c.data == 'admin:export_users', user_id=ADMIN_ID)
async def admin_export_users(call: types.CallbackQuery):
    filename = await export_users_to_excel()
    with open(filename, "rb") as file:
        await bot.send_document(call.message.chat.id, document=file, caption="Данные участников")

class UserAction(StatesGroup):
    waiting_for_code_word_input = State()

# Устанавливаем состояние для ожидания кодового слова после нажатия кнопки
@dp.callback_query_handler(lambda c: c.data == 'send_code', state='*')
async def prompt_for_code_word(call: types.CallbackQuery):
    await (UserAction.waiting_for_code_word_input.set())
    await call.message.answer("Введите кодовое слово:")

# Обработчик для введенного кодового слова
@dp.message_handler(state=UserAction.waiting_for_code_word_input)
async def process_code_word_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    username = message.from_user.username
    code_word_input = message.text.strip().lower()



    async with aiosqlite.connect('users_activity.db') as db:
        cursor = await db.execute("SELECT points FROM code_words WHERE LOWER(word) = ?", (code_word_input,))
        result = await cursor.fetchone()
        if result:
            points = result[0]
            try:
                await db.execute("UPDATE users SET balance = balance + ? WHERE user_id = ?", (points, user_id))
                await db.commit()
                await message.answer(f"Вам начислено {points} балл(ов) за кодовое слово '{code_word_input}'.")
            except Exception as e:
                print(f"Ошибка при обновлении баланса пользователя {user_id}: {e}")
                await message.answer("Произошла ошибка при обработке вашего запроса. Попробуйте позже.")
        else:
            await message.answer("Кодовое слово не найдено. Попробуйте еще раз.")
    await state.finish()

@dp.message_handler(lambda message: '#помощь' in message.text)
async def hashtag_help_handler(message: types.Message):
    user_id = message.from_user.id
    # Предполагаем, что у вас уже есть функция для добавления баллов пользователю
    await add_or_update_user_balance(user_id, 10)  # Добавляем 10 баллов за сообщение с #помощь
    # Опционально, можно отправить подтверждение о начислении баллов
    await message.reply("Вам начислено 10 баллов за помощь!")

async def add_or_update_user_balance(user_id: int, points: int):
    async with aiosqlite.connect('users_activity.db') as db:
        # Увеличиваем баланс пользователя на указанное количество баллов
        await db.execute('''INSERT INTO users (user_id, balance) VALUES (?, ?)
                            ON CONFLICT(user_id) DO UPDATE SET balance = balance + excluded.balance''',
                         (user_id, points))
        await db.commit()

@dp.callback_query_handler(text='send_post')  # Предполагается, что у вас есть кнопка с callback_data='send_post'
async def handle_send_post(call: types.CallbackQuery):
    await PostState.WAITING_FOR_POST.set()
    await call.message.answer("Пожалуйста, отправьте ваш пост с хештегом #100балльныйрепетитор.")

@dp.message_handler(state=PostState.WAITING_FOR_POST)
async def process_post(message: types.Message, state: FSMContext):
    if '#100балльныйрепетитор' in message.text:
        user_id = message.from_user.id
        await add_or_update_user_balance(user_id, 150)  # Добавляем 150 баллов
        await message.answer("Вам начислено 150 баллов за пост с хештегом #100балльныйрепетитор!")
    else:
        await message.answer("В вашем посте не найден хештег #100балльныйрепетитор. Попробуйте ещё раз.")

    await state.finish()  # Выходим из состояния ожидания поста

@dp.message_handler(content_types=types.ContentTypes.TEXT)
async def count_messages(message: types.Message):
    user_id = message.from_user.id
    # Предполагается, что у вас уже есть функция для добавления или обновления баланса пользователя в БД
    await add_or_update_user_balance(user_id, 1)  # Добавляем 1 балл за каждое сообщение
    # Опционально: отправить подтверждение пользователю (может быть нежелательно в групповых чатах)
    # await message.reply("Вам начислен 1 балл за сообщение.")
async def add_or_update_user_balance(user_id: int, points: int):
    async with aiosqlite.connect('users_activity.db') as db:
        # Увеличиваем баланс пользователя на указанное количество баллов
        await db.execute('''INSERT INTO users (user_id, balance) VALUES (?, ?)
                            ON CONFLICT(user_id) DO UPDATE SET balance = balance + excluded.balance''',
                         (user_id, points))
        await db.commit()





@dp.callback_query_handler(callback_data.filter(item='ачивки'))
async def show_achievements(call: types.CallbackQuery):
    await call.message.delete()
    message="Привет! В этот раз ты не набрал баллы для получения приза 😢 Ждём тебя в следующем месяце в числе самых активных!"
    await call.message.answer(message, reply_markup=InlineKeyboardMarkup(row_width=1).add(InlineKeyboardButton('Вернуться назад', callback_data=callback_data.new(item='back_to_menu'))))

from aiogram.dispatcher.filters.state import StatesGroup, State

class HelpState(StatesGroup):
    WAITING_FOR_PROBLEM_DESCRIPTION = State()

@dp.callback_query_handler(callback_data.filter(item='помощь'))
async def request_help(call: types.CallbackQuery):
    await HelpState.WAITING_FOR_PROBLEM_DESCRIPTION.set()
    await call.message.answer("Пожалуйста, опиши свою проблему, чтобы менеджер быстрее нашёл решение.")


@dp.message_handler(state=HelpState.WAITING_FOR_PROBLEM_DESCRIPTION, content_types=types.ContentTypes.TEXT)
async def handle_problem_description(message: types.Message, state: FSMContext):
    # Отправляем сообщение администратору с описанием проблемы и данными пользователя
    await bot.send_message(ADMIN_ID, f"Пользователь @{message.from_user.username} ({message.from_user.id}) "
                                     f"запросил помощь:\n\n{message.text}")
    # Отправляем ответ пользователю
    back_button = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton('Вернуться назад', callback_data=callback_data.new(item='back_to_menu')))

    # Отправляем ответ пользователю с кнопкой "Вернуться назад"
    await message.answer("Спасибо! Менеджер скоро подключится и поможет разобраться 🤓", reply_markup=back_button)

    await state.finish()  # Завершаем состояние

from aiogram import types
from aiogram.dispatcher.filters import Text

@dp.callback_query_handler(callback_data.filter(item='рейтинг'))
async def show_rating(callback_query: types.CallbackQuery):
    await callback_query.answer()  # Ответ на callback_query, чтобы убрать "часики" в интерфейсе Telegram
    await send_rating(callback_query.message.chat.id)


from datetime import datetime


async def send_rating(chat_id):
    try:
        async with aiosqlite.connect('users_activity.db') as db:  # Укажите путь к вашей базе данных
            query = 'SELECT username, balance FROM users ORDER BY balance DESC LIMIT 10'
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()

                if not rows:
                    await bot.send_message(chat_id, "Рейтинг пока пуст.")
                    return

                rating_message = "Рейтинг игроков на " + datetime.now().strftime("%Y-%m-%d") + ":\n\n"
                for index, (username, balance) in enumerate(rows, start=1):
                    rating_message += f"{index}. {username if username else 'Аноним'}: {balance} баллов\n"

                await bot.send_message(chat_id, rating_message)
    except Exception as e:
        logging.error(f"Ошибка при отправке рейтинга: {e}")
        await bot.send_message(chat_id, "Произошла ошибка при попытке отправить рейтинг.")

@dp.callback_query_handler(Text(equals="invite_friend"))
async def invite_friend(call: types.CallbackQuery):
    # Генерация и отправка пользователю реферальной ссылки
    invite_link = f'https://t.me/tutor_100ballniy_bot?start={call.from_user.id}'
    await call.message.answer(f'Отправь эту ссылку друзьям: {invite_link}\nЕсли друг подписывается и остается с нами 3 дня, вы оба получите по 100 баллов!')

async def check_referrals():
    # Функция для проверки и начисления баллов за рефералов (запускать периодически, например, раз в день)
    async with aiosqlite.connect('users_activity.db') as db:
        # Проверяем пользователей, кто был приглашен более 3 дней назад и еще не получил баллы
        cursor = await db.execute('''SELECT user_id, referred_by FROM users 
                                     WHERE referral_time <= datetime('now', '-3 day') AND balance_earned = 0''')
        referrals = await cursor.fetchall()
        for user_id, referrer_id in referrals:
            # Начисляем баллы и обновляем статус
            await db.execute('UPDATE users SET balance = balance + 100 WHERE user_id IN (?, ?)', (user_id, referrer_id))
            await db.execute('UPDATE users SET balance_earned = 1 WHERE user_id = ?', (user_id,))
            await db.commit()
            # Оповещаем об успехе
            await bot.send_message(referrer_id, f'Твой друг остался с нами более 3 дней! Вам обоим начислено по 100 баллов.')

InlineKeyboardButton("Каналы и чаты для участия", callback_data=callback_data.new(item='каналы_и_чаты_для_участия'))

@dp.callback_query_handler(callback_data.filter(item='каналы_и_чаты_для_участия'))
async def join_channels_and_chats(call: types.CallbackQuery):
    message_text = "В этом канале и чате мы будет отслеживать твою активность 👇\n\nСкорее присоединяйся!"
    join_button_url = "https://t.me/addlist/MEcHZ58uECw0MWQy"
    keyboard_markup = InlineKeyboardMarkup(row_width=1).add(
        InlineKeyboardButton(text="Присоединиться", url=join_button_url),
        InlineKeyboardButton(text="Вернуться назад", callback_data=callback_data.new(item='back_to_menu'))
    )
    await call.message.answer(message_text, reply_markup=keyboard_markup)

async def main():
    await create_db()
    await dp.start_polling()
    loop = asyncio.get_running_loop()
    loop.create_task(check_referrals())
    await dp.start_polling()


if __name__ == '__main__':
    asyncio.run(main())

if __name__ == '__main__':
    asyncio.run(main())
