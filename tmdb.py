import random
import aiohttp

from cache import cache
from models import Frame, Movie
from retry import with_retry, ServiceUnavailable

class NoMoviesFound(ServiceUnavailable):
    """TMDB не вернул подходящих фильмов или кадров."""

class TMDBClient:
    BASE_URL = "https://api.themoviedb.org/3"
    IMG_URL = "https://image.tmdb.org/t/p/original"
    DISCOVER_TTL = 3600
    IMAGES_TTL = 24 * 3600
    DETAILS_TTL = 7 * 24 * 3600
    MAX_PAGE = 500

    def __init__(self, session: aiohttp.ClientSession, token: str, language: str = "ru-RU"):
        self.session = session
        self.language = language
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

    async def _get_json(self, url: str, params: dict | None = None) -> dict:
        async def call():
            async with self.session.get(url, params=params, headers=self.headers,
                                        timeout=aiohttp.ClientTimeout(total=15)) as req:
                req.raise_for_status()
                return await req.json()
        return await with_retry(call, name="TMDB")

    async def _discover(self, animation: bool, page: int, years: tuple[int, int] | None) -> dict:
        key = f"discover:{animation}:{self.language}:{years}:{page}"

        async def fetch():
            params = {
                "sort_by": "popularity.desc",
                "page": page,
                "language": self.language,
                "vote_count.gte": 500,
                "include_adult": "false"
            }
            if animation:
                params["with_genres"] = "16"
            else:
                params["without_genres"] = "16"
            if years:
                params["primary_release_date.gte"] = f"{years[0]}-01-01"
                params["primary_release_date.lte"] = f"{years[1]}-12-31"
            return await self._get_json(f"{self.BASE_URL}/discover/movie", params)

        return await cache.get_or_fetch(key, self.DISCOVER_TTL, fetch) 

    @staticmethod
    def _to_movie(raw: dict) -> Movie:
        return Movie(
            id=raw["id"],
            title=raw.get("title") or "Без названия",
            year=(raw.get("release_date") or "")[:4],
            rating=float(raw.get("vote_average") or 0),
            votes=int(raw.get("vote_count") or 0)
        )

    async def random_movie(self, animation: bool = False, pages: tuple[int, int] = (1, 100),
                           years: tuple[int, int] | None = None) -> Movie:
        for _ in range(3):
            page = random.randint(*pages)
            data = await self._discover(animation, page, years)
            results = data.get("results", [])
            if results:
                return self._to_movie(random.choice(results))

            total = min(data.get("total_pages") or 1, self.MAX_PAGE)
            pages = (1, total)
        raise NoMoviesFound("TMDB не нашел фильм")

    async def imdb_id(self, movie_id: int) -> str | None:
        key = f"details:{movie_id}"

        async def fetch():
            return await self._get_json(f"{self.BASE_URL}/movie/{movie_id}", {"language": self.language})

        try:
            data = await cache.get_or_fetch(key, self.DETAILS_TTL, fetch)
        except ServiceUnavailable:
            return None
        return data.get("imdb_id")
        

    async def _backdrops(self, movie_id: int) -> list[dict]:
        key = f"images:{movie_id}"

        async def fetch():
            return await self._get_json(
                f"{self.BASE_URL}/movie/{movie_id}/images",
                {"include_image_language": "null"}
            )

        data = await cache.get_or_fetch(key, self.IMAGES_TTL, fetch)
        return data.get("backdrops", [])

    async def random_image(self, animation: bool = False, pages: tuple[int, int] = (1, 100),
                           years: tuple[int, int] | None = None) -> Frame:
        for _ in range(5):
            movie = await self.random_movie(animation, pages, years)
            frames = [f for f in await self._backdrops(movie.id) if f.get("iso_639_1") is None 
                      and f["width"] >= 1280
                      and f["width"] / f["height"] >= 1.7]
            if frames:
                frame = random.choice(frames)
                return Frame(movie=movie, url=self.IMG_URL + frame["file_path"])
            
        raise NoMoviesFound("Не удалось найти фильма с картинками")

    
