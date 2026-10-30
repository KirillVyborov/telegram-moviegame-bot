from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from models import Movie
from services.prefs import DIFFICULTY_LABELS, EPOCHS_LABELS, Prefs

def _mark(active: bool, label: str) -> str:
    return f"✅ {label}" if active else label

def main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="🎬Случайный фильм")
    builder.button(text="🖼Случайный кадр")
    builder.button(text="🎮Начать игру")
    builder.button(text="📊Статистика")
    builder.button(text="⚙️Настройки")
    builder.adjust(2)
    return builder.as_markup(resize_keyboard=True)

def trailer_markup(url: str | None):
    if not url:
        return None
    builder = InlineKeyboardBuilder()
    builder.button(text="▶️Трейлер на YouTube", url=url)
    return builder.as_markup()

def game_markup(options: list[Movie]):
    builder = InlineKeyboardBuilder()
    for m in options:
        label = f"{m.title} ({m.year})" if m.year else m.title
        builder.button(text=label[:64], callback_data=f"ans:{m.id}")
    builder.adjust(1)
    return builder.as_markup()

def settings_markup(p: Prefs):
    builder = InlineKeyboardBuilder()
    builder.button(text=_mark(not p.animation, "Фильмы"), callback_data="set:type:movie")
    builder.button(text=_mark(p.animation, "Мультфильмы"), callback_data="set:type:anim")
    for key, label in DIFFICULTY_LABELS.items():
        builder.button(text=_mark(p.difficulty == key, label), callback_data=f"set:diff:{key}")
    for key, label in EPOCHS_LABELS.items():
        builder.button(text=_mark(p.epoch == key, label), callback_data=f"set:epoch:{key}")
    builder.button(text="Сбросить прогресс", callback_data="reset:ask")
    builder.adjust(2, 3, 2, 2, 2, 1)
    return builder.as_markup()

def reset_confirm_markup():
    builder = InlineKeyboardBuilder()
    builder.button(text="Да, сбросить прогресс", callback_data="reset:yes")
    builder.button(text="Нет", callback_data="reset:no")
    builder.adjust(2)
    return builder.as_markup()