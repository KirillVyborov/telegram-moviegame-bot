from html import escape
from models import Movie

MEDALS = ["🥇", "🥈", "🥉"]

def fmt_num(n: int) -> str:
    return f"{n:,}".replace(",", " ")

def rating_line(movie: Movie) -> str:
    if not movie.votes:
        return "⭐ Оценок нет"
    return f"⭐ TMDB: <b>{movie.rating:.1f}</b>/10. {fmt_num(movie.votes)} оценок"

def movie_card(movie: Movie, imdb_id: str | None) -> str:
    year = movie.year or "Год неизвестен"
    lines = [f"🎬 <b>{escape(movie.title)}</b> ({year})", rating_line(movie)]
    if imdb_id:
        lines.append(f'<a href="https://www.imdb.com/title/{escape(imdb_id)}/">Страница на IMDb</a>')
    return "\n".join(lines)

def format_top(rows: list[tuple[str | None, int]]) -> str:
    if not rows:
        return "\nПока никто не набрал очков"
    lines = []
    for i, (name, points) in enumerate(rows):
        place = MEDALS[i] if i < 3 else f"{i + 1}."
        lines.append(f"{place} {escape(name or "Игрок")} - {points}")
    return "\n".join(lines)

def stats_text(score: int, rank: int, top: list[tuple[str | None, int]]) -> str:
    return(
        "📊 <b>Статистика</b>\n"
        f"🏆 Очки: <b>{score}</b>\n"
        f"Место: <b>{rank}</b>\n"
        "<b>Топ-3 игроков:</b>\n"
        f"{format_top(top)}"
    )

