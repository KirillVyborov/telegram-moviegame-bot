import logging
from html import escape

from aiogram import F, Router
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart, ExceptionTypeFilter
from aiogram.types import Message, CallbackQuery, ErrorEvent
from aiogram.exceptions import TelegramBadRequest
from aiogram.utils.keyboard import InlineKeyboardBuilder

from db import add_point, get_score, get_rank, get_top, reset_progress
from game import games, send_game, StopGameMiddleware, settings_markup, get_prefs, prefs
from keyboards import main_keyboard, trailer_markup
from retry import ServiceUnavailable
from tmdb import TMDBClient
from youtube import YouTubeClient

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)
router.message.outer_middleware(StopGameMiddleware())

async def random_film(message:Message, tmdb:TMDBClient, youtube: YouTubeClient, user_id: int):
    p = get_prefs(user_id)
    movie = await tmdb.random_movie(animation=p["animation"])
    title = movie["title"]
    id = movie["id"]
    date = movie.get("release_date", " ")[:4]
    trailer = await youtube.trailer_url(title, date)
    await message.answer(f"Название фильма: {title} ({date})\n id:{id}", reply_markup=trailer_markup(trailer))

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
async def send_random_film(message:Message, tmdb:TMDBClient, youtube: YouTubeClient):
    await random_film(message, tmdb, youtube, message.from_user.id)

@router.message(F.text == "Случайный фильм")
async def send_random_film_button(message:Message, tmdb:TMDBClient, youtube: YouTubeClient):
    await random_film(message, tmdb, youtube, message.from_user.id)

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
    user_id = message.from_user.id
    score = await get_score(user_id)
    rank = await get_rank(user_id)
    top = await get_top(3)

    lines = [f"Ваши очки: {score}, место: {rank}\nТоп-3 игроков:"]
    if top:
        for i, (name, points) in enumerate(top, start=1):
            lines.append(f"{i} {name or "Игрок"} - {points}")
    else:
        lines.append("Пока никто не набрал очков")

    await message.answer("\n".join(lines))
    

@router.callback_query(F.data.startswith("ans:"))
async def answer_handler(callback:CallbackQuery, tmdb:TMDBClient):
    game = games.pop(callback.message.chat.id, None)

    if game is None:
        await callback.answer("Этот вопрос уже закрыт. Нажмите кнопку еще раз", show_alert=True)
        return
    
    chosen = int(callback.data.split(":")[1])
    if chosen == game["movie_id"]:
        await add_point(callback.from_user.id, game["points"], callback.from_user.full_name)
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
    try:
        await callback.message.edit_reply_markup(reply_markup=settings_markup(callback.from_user.id))
    except TelegramBadRequest as e:
        if "message is not modified" not in e.message:
            raise

@router.callback_query(F.data == "reset:ask")
async def reset_ask(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="Да, сбросить прогресс", callback_data="reset:yes")
    builder.button(text="Нет", callback_data="reset:no")
    builder.adjust(2)
    await callback.message.answer("Сбросить ваш прогресс?", reply_markup=builder.as_markup())
    await callback.answer()

@router.callback_query(F.data == "reset:yes")
async def reset_yes(callback: CallbackQuery):
    user_id = callback.from_user.id
    await reset_progress(user_id)
    prefs.pop(user_id, None)
    games.pop(callback.message.chat.id, None)
    await callback.message.edit_text("Прогресс сброшен")
    await callback.message.answer("Готово")

@router.callback_query(F.data == "reset:no")
async def reset_no(callback: CallbackQuery):
    await callback.message.edit_text("Сброс отменен")
    await callback.answer()

@router.errors(ExceptionTypeFilter(ServiceUnavailable))
async def service_unavailable_handler(event: ErrorEvent):
    update = event.update
    message = update.message or (update.callback_query.message if update.callback_query else None)
    logger.warning("Внешний сервис недоступен")
    if message:
        await message.answer("Сервис временно недоступен")