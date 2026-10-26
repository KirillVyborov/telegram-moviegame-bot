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