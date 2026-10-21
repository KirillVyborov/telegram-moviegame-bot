import random

from aiogram import BaseMiddleware
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from tmdb import TMDBClient

games: dict[int, dict] = {}
class StopGameMiddleware(BaseMiddleware):
    async def __call__(self, handler, event:Message, data):
        if event.text != "Начать игру":
            games.pop(event.chat.id, None)
        return await handler(event, data)


async def send_game(message:Message, tmdb:TMDBClient):
    frame = await tmdb.random_image()

    wrong = await tmdb.random_movie()
    while wrong["id"] == frame["movie_id"]:
        wrong = await tmdb.random_movie()

    options = [
        {"id": frame["movie_id"], "title": frame["title"]},
        {"id": wrong["id"], "title": wrong["title"]}
    ]
    random.shuffle(options)

    games[message.chat.id] = {"movie_id": frame["movie_id"], "title": frame["title"]}

    builder = InlineKeyboardBuilder()
    for option in options:
        builder.button(text=option["title"], callback_data=f"ans:{option["id"]}")
    builder.adjust(1)

    await message.answer_photo(photo=frame["url"], caption="Угадай фильм по кадру", reply_markup=builder.as_markup())
