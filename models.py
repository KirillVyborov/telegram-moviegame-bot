from dataclasses import dataclass

@dataclass(frozen=True)
class Movie:
    id: int
    title: str
    year: str
    rating: float
    votes: int

@dataclass(frozen=True)
class Frame:
    movie: Movie
    url: str
