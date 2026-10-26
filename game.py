import random

from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tmdb import TMDBClient

games: dict[int, dict] = {}
prefs: dict[int, dict] = {}
DIFFICULTY = {
    "easy": ((1, 5), 1),
    "medium": ((6, 20), 2),
    "hard": ((21, 50), 3)
}
DIFFICULTY_LABELS = {
    "easy": "Лёгкая",
    "medium": "Средняя",
    "hard": "Тяжелая"
}

class StopGameMiddleware(BaseMiddleware):
    async def __call__(self, handler, event:Message, data):
        if event.text != "Начать игру":
            games.pop(event.chat.id, None)
        return await handler(event, data)

def get_prefs(user_id: int) -> dict:
    return prefs.setdefault(user_id, {"animation": False, "difficulty": "easy"})


async def send_game(message:Message, tmdb:TMDBClient, user_id: int):
    p = get_prefs(user_id)
    pages, points = DIFFICULTY[p["difficulty"]]
    frame = await tmdb.random_image(animation=p["animation"], pages=pages)

    wrong = await tmdb.random_movie(animation=p["animation"], pages=pages)
    while wrong["id"] == frame["movie_id"]:
        wrong = await tmdb.random_movie(animation=p["animation"], pages=pages)

    options = [
        {"id": frame["movie_id"], "title": frame["title"]},
        {"id": wrong["id"], "title": wrong["title"]}
    ]
    random.shuffle(options)

    games[message.chat.id] = {"movie_id": frame["movie_id"], "title": frame["title"], "points": points}

    builder = InlineKeyboardBuilder()
    for option in options:
        builder.button(text=option["title"], callback_data=f"ans:{option["id"]}")
    builder.adjust(1)

    await message.answer_photo(
        photo=frame["url"], 
        caption=f"Угадай фильм по кадру. {DIFFICULTY_LABELS[p['difficulty']]} (+{points})", 
        reply_markup=builder.as_markup(),
        )

def settings_markup(user_id: int):
    p = get_prefs(user_id)
    btn = InlineKeyboardBuilder()
    btn.button(text=("Выбрано: " if not p["animation"] else "") + "Фильмы", callback_data="set:type:movie")
    btn.button(text=("Выбрано: " if p["animation"] else "") + "Мультфильмы", callback_data="set:type:anim")
    for key, label in DIFFICULTY_LABELS.items():
        mark = "Сложность " if p["difficulty"] == key else ""
        btn.button(text=mark + label, callback_data=f"set:diff:{key}")
    btn.adjust(2, 3)
    return btn.as_markup()
