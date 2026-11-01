[Telegram](https://t.me/minecraft6767bot)

# Бот-игра. Нужно угадать фильм по кадру из него.

## API

Для получения токена бота:

- Перейти в @BotFather и создать бота командой /newbot

Используются API TMDB и YouTube Data API. 

- Для получения API TMDB нужно пройти по ссылке [TMDB](https://www.themoviedb.org/), зарегистрироваться и по [ссылке](https://www.themoviedb.org/settings/api) или в профиле получить ключ. 
- Для YouTube Data API v3 нужно перейти по [ссылке](https://developers.google.com/youtube/data/getting-started?hl=ru) и ознакомиться.

## База данных

- Используется SQLite, отдельный сервер БД не нужен, все хранится в файле bot.db в папке проекта.
- Таблица создается при запуске бота функцией init_db() в файле db.py, путь задается DB_PATH

## Запуск

- Создать папку, создать виртуальное окружение
- Установить git. Прописать git clone https://github.com/KirillVyborov/telegram-moviegame-bot.git
- Установить зависимости requirements.txt (pip install -r requirements.txt)
- Создать .env с ключами по примеру .env.example
- Запустить бота: python3 tg_bot.py

## Используемые технологии:

- API: Telergam, TMDB, YouTube Data
- Для бота: aiogram, для работы с api: aiohttp, для логов: logging, для БД: aiosqlite
