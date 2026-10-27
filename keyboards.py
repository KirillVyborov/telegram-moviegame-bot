from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

def main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.button(text="Случайный фильм")
    builder.button(text="Случайный кадр")
    builder.button(text="Начать игру")
    builder.button(text="Статистика")
    builder.button(text="Настройки")
    builder.adjust(2)
    return builder.as_markup()

def trailer_markup(url: str | None):
    if not url:
        return None
    builder = InlineKeyboardBuilder()
    builder.button(text="Трейлер на YouTube", url=url)
    return builder.as_markup()