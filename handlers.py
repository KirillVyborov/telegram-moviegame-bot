from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart
from aiogram.types import Message, CallbackQuery

from db import init_db, add_point, get_score
from game import games, send_game, StopGameMiddleware, settings_markup, get_prefs
from keyboards import main_keyboard
from tmdb import TMDBClient

router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.message.outer_middleware(StopGameMiddleware())

async def random_film(message:Message, tmdb:TMDBClient, user_id: int):
    p = get_prefs(user_id)
    movie = await tmdb.random_movie(animation=p["animation"])
    title = movie["title"]
    id = movie["id"]
    date = movie.get("release_date", " ")
    await message.answer(f"Название фильма: {title} ({date})\n id:{id}")

async def random_image(message:Message, tmdb:TMDBClient, user_id: int):
    p = get_prefs(user_id)
    frame = await tmdb.random_image(animation=p["animation"])
    await message.answer_photo(photo=frame["url"])

@router.message(CommandStart())
async def start_handler(message:Message):
    await message.answer(
        "Привет, я бот - Угадай фильм по кадру",
        reply_markup=main_keyboard()
    )

@router.message(Command("random_film"))
async def send_random_film(message:Message, tmdb:TMDBClient):
    await random_film(message, tmdb, message.from_user.id)

@router.message(F.text == "Случайный фильм")
async def send_random_film_button(message:Message, tmdb:TMDBClient):
    await random_film(message, tmdb, message.from_user.id)

@router.message(F.text == "Случайный кадр")
async def send_random_image_button(message:Message, tmdb:TMDBClient):
    await random_image(message, tmdb, message.from_user.id)

@router.message(Command("random_image"))
async def send_random_image(message:Message, tmdb:TMDBClient):
    await random_image(message, tmdb, message.from_user.id)

@router.message(F.text == "Начать игру")
async def game_start(message:Message, tmdb:TMDBClient):
    await send_game(message, tmdb, message.from_user.id)

@router.message(F.text == "Статистика")
async def stats_handler(message:Message):
    score = await get_score(message.from_user.id)
    await message.answer(f"Ваши очки: {score}")

@router.callback_query(F.data.startswith("ans:"))
async def answer_handler(callback:CallbackQuery, tmdb:TMDBClient):
    game = games.pop(callback.message.chat.id, None)

    if game is None:
        await callback.answer("Этот вопрос уже закрыт. Нажмите кнопку еще раз", show_alert=True)
        return
    
    chosen = int(callback.data.split(":")[1])
    if chosen == game["movie_id"]:
        await add_point(callback.from_user.id, game["points"])
        result = "Верно!\n"
    else:
        result = "Неверно(\n"

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"{result} Это <<{game["title"]}>>")

    await send_game(callback.message, tmdb, callback.from_user.id)

@router.message(F.text == "Настройки")
async def settings_button(message: Message):
    await message.answer("Настройки игры:", reply_markup=settings_markup(message.from_user.id))

@router.callback_query(F.data.startswith("set:"))
async def settings_handler(callback: CallbackQuery):
    _, kind, value = callback.data.split(":")
    p = get_prefs(callback.from_user.id)
    if kind == "type":
        p["animation"] = value == "anim"
    elif kind == "diff":
        p["difficulty"] = value
    await callback.answer("Сохранено")
    await callback.message.edit_reply_markup(reply_markup=settings_markup(callback.from_user.id))
    