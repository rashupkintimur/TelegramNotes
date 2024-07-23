# Telegram Notes Bot

Этот бот для Telegram позволяет пользователям создавать, просматривать, редактировать и удалять заметки. Бот хранит данные заметок в базе данных SQLite.

## Функционал

- **Создание новой заметки**: `/new_note`
- **Просмотр всех заметок**: `/view_notes`
- **Просмотр конкретной заметки по ID**: `/view_note`
- **Удаление заметки по ID**: `/delete_note`
- **Редактирование заметки по ID**: `/edit_note`

## Установка

1. **Клонируйте репозиторий:**

    ```bash
    git clone https://github.com/your-username/telegram-notes-bot.git
    cd telegram-notes-bot
    ```

2. **Создайте и активируйте виртуальное окружение:**

    ```bash
    python -m venv venv
    source venv/bin/activate  # На Windows используйте `venv\Scripts\activate`
    ```

3. **Установите зависимости:**

    ```bash
    pip install -r requirements.txt
    ```

4. **Создайте файл конфигурации `config.py` и добавьте ваш API ключ:**

    ```python
    API_KEY = 'YOUR_TELEGRAM_BOT_API_KEY'
    ```

5. **Запустите бота:**

    ```bash
    python bot.py
    ```

## Использование

1. **Запустите бота и отправьте команду `/start` для приветствия.**
2. **Используйте команду `/new_note` для создания новой заметки. Бот запросит заголовок и текст заметки.**
3. **Просматривайте все заметки с помощью команды `/view_notes`. Пагинация поддерживается.**
4. **Просматривайте конкретную заметку по ID с помощью команды `/view_note`.**
5. **Удаляйте заметки по ID с помощью команды `/delete_note`.**
6. **Редактируйте заметки по ID с помощью команды `/edit_note`. Бот запросит новый заголовок и текст.**

## Структура базы данных

- **users**: Таблица с пользователями.
  - `id` INTEGER PRIMARY KEY
  - `name` VARCHAR(255)

- **notes**: Таблица с заметками.
  - `id` INTEGER PRIMARY KEY AUTOINCREMENT
  - `user_id` INTEGER (FOREIGN KEY, ссылается на `users.id`)
  - `title` VARCHAR(500)
  - `text` TEXT
  - `date` DATETIME

## Пример конфигурации

```python
API_KEY = 'YOUR_TELEGRAM_BOT_API_KEY'
