import config
import sqlite3
import telebot
from telebot import types

# функция для создания для нового подключения к бд
def get_db_connection():
    connection = sqlite3.connect("telegram_notes.db")
    connection.row_factory = sqlite3.Row
    return connection

connection = get_db_connection()
cursor = connection.cursor()

# включение поддержки внешних ключей
cursor.execute("PRAGMA foreign_keys = ON")

# создаём таблицу с пользователями
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        name VARCHAR(255)
    )
''')

# создаём таблицу с записками
cursor.execute('''
    CREATE TABLE IF NOT EXISTS notes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        title VARCHAR(500),
        text TEXT,
        FOREIGN KEY (user_id) REFERENCES users(id)
    )
''')

# сохранение изменений
connection.commit()
connection.close()

# инициализация бота
bot = telebot.TeleBot(config.API_KEY)

# вспомогательные переменные
temp_titles = {} # временное хранилище заголовков, чтобы потом их перенести в notes таблицу

# обработчик команды /start
@bot.message_handler(commands=["start"])
def welcome(message):
    username = message.from_user.username
    connection = get_db_connection()
    cursor = connection.cursor()

    bot.send_message(message.chat.id, f"Здравствуйте <b>{username}</b>. Вас приветствует удобный бот 'telegram_notes' для управлениями заметками. Предлагаю создать свою первую заметку", parse_mode="HTML")

    # добавление нового пользователя в бд
    cursor.execute('''
        INSERT INTO users(id, name) VALUES (?, ?)
    ''', (message.from_user.id, username))

    connection.commit()
    cursor.close()

# обработчик создания записок
@bot.message_handler(commands=["new_note"])
def new_note_handler(message):
    msg = bot.reply_to(message, "Введите заголовок новой заметки:")
    bot.register_next_step_handler(msg, new_note_title)

# ввод заголовка
def new_note_title(message):
    user_id = message.from_user.id
    temp_titles[user_id] = message.text

    msg = bot.reply_to(message, "Введите текст новой заметки:")
    bot.register_next_step_handler(msg, new_note_text)

# ввод текста заголовка
def new_note_text(message):
    user_id = message.from_user.id
    title = temp_titles[user_id]

    connection = get_db_connection()
    cursor = connection.cursor()

    # добавление новой заметки
    cursor.execute('''
        INSERT INTO notes(user_id, title, text) VALUES (?, ?, ?)
    ''', (message.from_user.id, title, message.text))

    connection.commit()
    cursor.close()

    # удаление заголовка из временного "хранилища"
    del temp_titles[user_id]

    bot.send_message(message.chat.id, "Записка создана")

# обработчик просмотра всех записок пользователя
@bot.message_handler(commands=["view_notes"])
def view_notes(message):
    message_text = ""
    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute(f"SELECT * FROM `notes` WHERE user_id = (?)", (message.from_user.id,))
    rows = cursor.fetchall()

    cursor.close()

    # формирование текста с записками
    for row in rows:
        message_text += f"Заголовок: <b>{row["title"]}</b>\nТекст: {row["text"]}\n\n"

    bot.send_message(message.chat.id, message_text, parse_mode="HTML")

# запуск бота
if __name__ == "__main__":
    bot.polling(non_stop=True)
