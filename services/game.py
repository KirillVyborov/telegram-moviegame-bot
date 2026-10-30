import random
from dataclasses import dataclass

from models import Movie
from services.prefs import DIFFICULTY, EPOCHS, Prefs
from tmdb import NoMoviesFound, TMDBClient

@dataclass(frozen=True)
class Question:
    movie_id: int
    title: str
    year: str
    points: int
    movie: Movie

@dataclass(frozen=True)
class Round:
    question: Question
    photo_url: str
    options: list[Movie]

games: dict[int, Question] = {}

async def new_round(tmdb: TMDBClient, prefs: Prefs) -> Round:
    pages, points = DIFFICULTY[prefs.difficulty]
    years = EPOCHS[prefs.epoch]

    frame = await tmdb.random_image(animation=prefs.animation, pages=pages, years=years)

    wrong = None
    for _ in range(5):
        candidate = await tmdb.random_movie(animation=prefs.animation, pages=pages, years=years)
        if candidate.id != frame.movie.id:
            wrong = candidate
            break

    if wrong is None:
        raise NoMoviesFound("TMDB: не удалось подобрать вариант ответа")

    options = [frame.movie, wrong]
    random.shuffle(options)
    question = Question(
        movie_id=frame.movie.id,
        title=frame.movie.title,
        year=frame.movie.year,
        points=points,
        movie=frame.movie
    )
    return Round(question=question, photo_url=frame.url, options=options)
