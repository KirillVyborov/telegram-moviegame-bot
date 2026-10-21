import asyncio
import logging
from html import escape
from typing import Any
import random

import aiohttp
from aiogram import Bot, Dispatcher, F, Router, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ChatType, ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.types import Message, CallbackQuery

from config import Settings
from tmdb1 import TMDBClient

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
games: dict[int, dict] = {}

def main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Случайный фильм")
    builder.button(text="Случайный кадр")
    builder.button(text="Начать игру")
    return builder.as_markup()

@router.message(CommandStart())
async def start_handler(message:Message):
    await message.answer(
        "Привет, я бот - Угадай фильм по кадру\n"
        "Нажми кнопку 'Получить фильм' чтобы начать",
        reply_markup=main_keyboard()
    )

async def random_film(message:Message, tmdb:TMDBClient):
    movie = await tmdb.random_movie()
    title = movie["title"]
    id = movie["id"]
    date = movie.get("release_date", " ")
    await message.answer(f"Название фильма: {title} ({date})\n id:{id}")

async def random_image(message:Message, tmdb:TMDBClient):
    frame = await tmdb.random_image()
    await message.answer_photo(photo=frame["url"])

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

@router.message(Command("random_film"))
async def send_random_film(message:Message, tmdb:TMDBClient):
    await random_film(message, tmdb)

@router.message(F.text == "Случайный фильм")
async def send_random_film_button(message:Message, tmdb:TMDBClient):
    await random_film(message, tmdb)

@router.message(F.text == "Случайный кадр")
async def send_random_image_button(message:Message, tmdb:TMDBClient):
    await random_image(message, tmdb)

@router.message(Command("random_image"))
async def send_random_image(message:Message, tmdb:TMDBClient):
    await random_image(message, tmdb)

@router.callback_query(F.data.startswith("ans:"))
async def answer_handler(callback:CallbackQuery):
    game = games.pop(callback.message.chat.id, None)

    if game is None:
        await callback.answer("Этот вопрос уже закрыт. Нажмите кнопку еще раз", show_alert=True)
        return
    
    chosen = int(callback.data.split(":")[1])
    if chosen == game["movie_id"]:
        result = "Верно!"
    else:
        result = "Неверно("

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"{result} Это <<{game["title"]}>>")

@router.message(F.text == "Начать игру")
async def game_start(message:Message, tmdb:TMDBClient):
    await send_game(message, tmdb)

async def main():
    settings = Settings()
    bot = Bot(token=settings.bot_token.get_secret_value())
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
        dispatcher["tmdb"] = TMDBClient(
            session=session,
            token=settings.tmdb_token.get_secret_value()
        )
        await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


