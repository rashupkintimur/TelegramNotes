import config
import sqlite3
import telebot
from telebot import types
import datetime
import math

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
        date DATETIME,
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

    bot.send_message(message.chat.id, f"Здравствуйте <b>{username}</b>. Вас приветствует бот 'telegram_notes' для управления заметками. Создайте свою первую заметку.", parse_mode="HTML")

    # Добавление нового пользователя в БД
    cursor.execute('''
        INSERT OR IGNORE INTO users(id, name) VALUES (?, ?)
    ''', (message.from_user.id, username))

    connection.commit()
    cursor.close()

# Обработчик создания записок
@bot.message_handler(commands=["new_note"])
def new_note_handler(message):
    msg = bot.reply_to(message, "Введите заголовок новой заметки:")
    bot.register_next_step_handler(msg, new_note_title)

# Ввод заголовка
def new_note_title(message):
    user_id = message.from_user.id
    temp_titles[user_id] = message.text

    msg = bot.reply_to(message, "Введите текст новой заметки:")
    bot.register_next_step_handler(msg, new_note_text)

# Ввод текста заметки
def new_note_text(message):
    user_id = message.from_user.id
    title = temp_titles[user_id]

    connection = get_db_connection()
    cursor = connection.cursor()

    # Добавление новой заметки
    cursor.execute('''
        INSERT INTO notes(user_id, title, text, date) VALUES (?, ?, ?, CURRENT_TIMESTAMP)
    ''', (user_id, title, message.text))

    connection.commit()
    cursor.close()

    # Удаление заголовка из временного хранилища
    del temp_titles[user_id]

    bot.send_message(message.chat.id, "Записка создана")

# Обработчик просмотра всех записок пользователя
@bot.message_handler(commands=["view_notes"])
def view_notes(message):
    user_id = message.from_user.id
    # Начальная страница - 1
    show_notes(message, user_id, 1)

def show_notes(message, user_id, page):
    per_page = 5
    offset = (page - 1) * per_page

    connection = get_db_connection()
    cursor = connection.cursor()

    # Общее количество записок
    cursor.execute("SELECT COUNT(*) FROM notes WHERE user_id = ?", (user_id,))
    total_notes = cursor.fetchone()[0]
    total_pages = (total_notes + per_page - 1) // per_page

    # Запрашиваем записки для текущей страницы
    cursor.execute("SELECT * FROM notes WHERE user_id = ? ORDER BY id DESC LIMIT ? OFFSET ?", (user_id, per_page, offset))
    rows = cursor.fetchall()
    cursor.close()

    # Формирование текста для сообщения
    message_text = ""
    if rows:
        for row in rows:
            message_text += f"<b>ID Записки</b>: {row['id']}\n"
            message_text += f"<b>Заголовок</b>: {row['title']}\n"
            message_text += f"<b>Текст</b>: {row['text']}\n"
            message_text += f"<b>Дата создания</b>: {row['date']}\n\n"
    else:
        message_text = "У вас нет записок на этой странице."

    # Создание inline-кнопок для навигации по страницам
    markup = types.InlineKeyboardMarkup()
    if page > 1:
        markup.add(types.InlineKeyboardButton("⏪ Назад", callback_data=f"page_{page-1}"))
    if page < total_pages:
        markup.add(types.InlineKeyboardButton("Вперед ⏩", callback_data=f"page_{page+1}"))

    bot.send_message(message.chat.id, message_text, parse_mode="HTML", reply_markup=markup)

# Обработчик просмотра конкретной записки по ID
@bot.message_handler(commands=["view_note"])
def view_note_handler(message):
    msg = bot.reply_to(message, "Введите ID заметки, которую хотите просмотреть:")
    bot.register_next_step_handler(msg, view_note_by_id)

def view_note_by_id(message):
    note_id = message.text
    user_id = message.from_user.id

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
    row = cursor.fetchone()
    cursor.close()

    if row:
        message_text = f"<b>ID Записки</b>: {row['id']}\n"
        message_text += f"<b>Заголовок</b>: {row['title']}\n"
        message_text += f"<b>Текст</b>: {row['text']}\n"
        message_text += f"<b>Дата создания</b>: {row['date']}\n"
        bot.send_message(message.chat.id, message_text, parse_mode="HTML")
    else:
        bot.send_message(message.chat.id, "Записка с таким ID не найдена.")

# Обработчик удаления конкретной записки по ID
@bot.message_handler(commands=["delete_note"])
def delete_note_handler(message):
    msg = bot.reply_to(message, "Введите ID заметки, которую хотите удалить:")
    bot.register_next_step_handler(msg, delete_note_by_id)

def delete_note_by_id(message):
    note_id = message.text
    user_id = message.from_user.id

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
    connection.commit()
    cursor.close()

    if cursor.rowcount > 0:
        bot.send_message(message.chat.id, "Записка успешно удалена.")
    else:
        bot.send_message(message.chat.id, "Записка с таким ID не найдена.")

# Обработчик редактирования конкретной записки по ID
@bot.message_handler(commands=["edit_note"])
def edit_note_handler(message):
    msg = bot.reply_to(message, "Введите ID заметки, которую хотите отредактировать:")
    bot.register_next_step_handler(msg, edit_note_by_id)

def edit_note_by_id(message):
    note_id = message.text
    user_id = message.from_user.id

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT * FROM notes WHERE id = ? AND user_id = ?", (note_id, user_id))
    row = cursor.fetchone()

    if row:
        bot.send_message(message.chat.id, "Введите новый заголовок:")
        bot.register_next_step_handler(message, lambda m: edit_note_title(m, note_id))
    else:
        bot.send_message(message.chat.id, "Записка с таким ID не найдена.")
    cursor.close()

def edit_note_title(message, note_id):
    new_title = message.text

    msg = bot.reply_to(message, "Введите новый текст заметки:")
    bot.register_next_step_handler(msg, lambda m: update_note_text(m, note_id, new_title))

def update_note_text(message, note_id, new_title):
    new_text = message.text
    user_id = message.from_user.id

    connection = get_db_connection()
    cursor = connection.cursor()

    cursor.execute('''
        UPDATE notes
        SET title = ?, text = ?
        WHERE id = ? AND user_id = ?
    ''', (new_title, new_text, note_id, user_id))

    connection.commit()
    cursor.close()

    bot.send_message(message.chat.id, "Записка успешно обновлена.")

# Обработчик нажатий на inline-кнопки для пагинации
@bot.callback_query_handler(func=lambda call: call.data.startswith("page_"))
def page_callback(call):
    try:
        page = int(call.data.split("_")[1])
        if page < 1:
            page = 1
        show_notes(call.message, call.message.chat.id, page)
        bot.delete_message(call.message.chat.id, call.message.message_id)
    except Exception as e:
        bot.send_message(call.message.chat.id, "Произошла ошибка при попытке загрузить страницу.")

# запуск бота
if __name__ == "__main__":
    bot.polling(non_stop=True)
