import random
import aiohttp

from cache import cache
from retry import with_retry

class TMDBClient:
    BASE_URL = "https://api.themoviedb.org/3"
    IMG_URL = "https://image.tmdb.org/t/p/original"
    DISCOVER_TTL = 3600
    IMAGES_TTL = 24 * 3600

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

    async def _discover(self, animation: bool, page: int) -> dict:
        key = f"discover:{animation}:{self.language}:{page}"

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
            return await self._get_json(f"{self.BASE_URL}/discover/movie", params)

        return await cache.get_or_fetch(key, self.DISCOVER_TTL, fetch) 

    async def random_movie(self, animation: bool = False, pages: tuple[int, int] = (1, 50)) -> dict:
        for _ in range(3):
            page = random.randint(*pages)
            data = await self._discover(animation, page)
            results = data.get("results", [])
            if results:
                return random.choice(results)

            pages = (1, min(pages[1], data.get("total_pages", 1) or 1))
        raise RuntimeError("TMDB не нашел фильм")

    async def _backdrops(self, movie_id: int) -> list[dict]:
        key = f"images:{movie_id}"

        async def fetch():
            return await self._get_json(
                f"{self.BASE_URL}/movie/{movie_id}/images",
                {"include_image_language": "null"}
            )

        data = await cache.get_or_fetch(key, self.IMAGES_TTL, fetch)
        return data.get("backdrops", [])

    async def random_image(self, animation: bool = False, pages: tuple[int, int] = (1, 50)) -> dict:
        for _ in range(5):
            movie = await self.random_movie(animation, pages)
            frames = [f for f in await self._backdrops(movie["id"]) if f.get("iso_639_1") is None 
                      and f["width"] >= 1280
                      and f["width"] / f["height"] >= 1.7]
            if frames:
                frame = random.choice(frames)
                return {
                    "movie_id": movie["id"],
                    "title": movie["title"],
                    "file_path": frame["file_path"],
                    "url": self.IMG_URL + frame["file_path"]
                }
            
        raise RuntimeError("Не удалось найти фильма с картинками")

    
