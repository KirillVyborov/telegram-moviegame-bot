import logging
from html import escape

from aiogram import F, Router, BaseMiddleware
from aiogram.enums import ChatType
from aiogram.filters import Command, CommandStart, ExceptionTypeFilter
from aiogram.types import Message, CallbackQuery, ErrorEvent
from aiogram.exceptions import TelegramBadRequest

from db import add_point, get_score, get_rank, get_top, reset_progress
from keyboards import main_keyboard, trailer_markup, game_markup, reset_confirm_markup, settings_markup
from services.game import games, new_round
from services.prefs import DIFFICULTY_LABELS, EPOCHS, get_prefs, reset_prefs
from utils.text import movie_card, stats_text
from retry import ServiceUnavailable
from tmdb import TMDBClient
from youtube import YouTubeClient

logger = logging.getLogger(__name__)

router = Router()
router.message.filter(F.chat.type == ChatType.PRIVATE)

def log_action(action: str) -> None:
    logger.info("action=%s", action)

class StopGameMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data):
        if event.text != "🎮Начать игру":
            games.pop(event.chat.id, None)
        return await handler(event, data)

router.message.outer_middleware(StopGameMiddleware())

async def random_film(message:Message, tmdb:TMDBClient, youtube: YouTubeClient, user_id: int):
    p = get_prefs(user_id)
    movie = await tmdb.random_movie(animation=p.animation, years=EPOCHS[p.epoch])
    imdb_id = await tmdb.imdb_id(movie.id)
    trailer = await youtube.trailer_url(movie.title, movie.year)
    await message.answer(movie_card(movie, imdb_id), reply_markup=trailer_markup(trailer), disable_web_page_preview=True)

async def random_image(message:Message, tmdb:TMDBClient, user_id: int):
    p = get_prefs(user_id)
    frame = await tmdb.random_image(animation=p.animation, years=EPOCHS[p.epoch])
    await message.answer_photo(photo=frame.url, caption="🖼Кадр из фильма.")

async def send_game(message: Message, tmdb: TMDBClient, user_id: int):
    p = get_prefs(user_id)
    round = await new_round(tmdb, p)
    games[message.chat.id] = round.question
    caption = ("<b>Угадай фильм по кадру</b>\n" f"{DIFFICULTY_LABELS[p.difficulty]}. +{round.question.points}очков")
    await message.answer_photo(photo=round.photo_url, caption=caption, reply_markup=game_markup(round.options))


@router.message(CommandStart())
async def start_handler(message:Message):
    log_action("start")
    await message.answer(
        "Привет, я бот - Угадай фильм по кадру",
        reply_markup=main_keyboard()
    )

@router.message(Command("random_film"))
async def send_random_film(message:Message, tmdb:TMDBClient, youtube: YouTubeClient):
    log_action("random_film")
    await random_film(message, tmdb, youtube, message.from_user.id)

@router.message(F.text == "🎬Случайный фильм")
async def send_random_film_button(message:Message, tmdb:TMDBClient, youtube: YouTubeClient):
    log_action("random_film")
    await random_film(message, tmdb, youtube, message.from_user.id)

@router.message(F.text == "🖼Случайный кадр")
async def send_random_image_button(message:Message, tmdb:TMDBClient):
    log_action("random_image")
    await random_image(message, tmdb, message.from_user.id)

@router.message(Command("random_image"))
async def send_random_image(message:Message, tmdb:TMDBClient):
    log_action("random_image")
    await random_image(message, tmdb, message.from_user.id)

@router.message(F.text == "🎮Начать игру")
async def game_start(message:Message, tmdb:TMDBClient):
    log_action("game_start")
    await send_game(message, tmdb, message.from_user.id)

@router.message(F.text == "📊Статистика")
async def stats_handler(message:Message):
    log_action("stats")
    user_id = message.from_user.id
    score = await get_score(user_id)
    rank = await get_rank(user_id)
    top = await get_top(3)
    await message.answer(stats_text(score, rank, top))
    

@router.callback_query(F.data.startswith("ans:"))
async def answer_handler(callback:CallbackQuery, tmdb:TMDBClient, youtube:YouTubeClient):
    game = games.pop(callback.message.chat.id, None)

    if game is None:
        await callback.answer("Этот вопрос уже закрыт. Нажмите кнопку еще раз", show_alert=True)
        return
    try:
        chosen = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer()
        return
    
    if chosen == game.movie_id:
        await add_point(callback.from_user.id, game.points, callback.from_user.full_name)
        result = f"<b>Верно!</b> +{game.points}\n"
    else:
        result = "<b>Неверно(</b>\n"

    imdb_id = await tmdb.imdb_id(game.movie_id)
    trailer = await youtube.trailer_url(game.movie.title, game.movie.year)

    await callback.answer()
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer(f"{result}\n Это: <b>{movie_card(game.movie, imdb_id)}</b>",
                                  reply_markup=trailer_markup(trailer), disable_web_page_preview=True)

    await send_game(callback.message, tmdb, callback.from_user.id)

@router.message(F.text == "⚙️Настройки")
async def settings_button(message: Message):
    await message.answer("⚙️<b>Настройки игры:</b>", reply_markup=settings_markup(get_prefs(message.from_user.id)))

@router.callback_query(F.data.startswith("set:"))
async def settings_handler(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer()
        return
    
    _, kind, value = parts
    p = get_prefs(callback.from_user.id)
    if kind == "type" and value in ("movie", "anim"):
        p.animation = value == "anim"
    elif kind == "diff" and value in DIFFICULTY_LABELS:
        p.difficulty = value
    elif kind == "epoch" and value in EPOCHS:
        p.epoch = value
    else:
        await callback.answer("Неизвестная настройка", show_alert=True)
        return
    
    await callback.answer("Сохранено")
    try:
        await callback.message.edit_reply_markup(reply_markup=settings_markup(p))
    except TelegramBadRequest as e:
        if "message is not modified" not in e.message:
            raise

@router.callback_query(F.data == "reset:ask")
async def reset_ask(callback: CallbackQuery):
    await callback.message.answer("Сбросить очки и настройки?", reply_markup=reset_confirm_markup())
    await callback.answer()

@router.callback_query(F.data == "reset:yes")
async def reset_yes(callback: CallbackQuery):
    user_id = callback.from_user.id
    await reset_progress(user_id)
    reset_prefs(user_id)
    games.pop(callback.message.chat.id, None)
    log_action("reset")
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