from typing import Any
import random
import aiohttp

class TMDBClient:
    BASE_URL = "https://api.themoviedb.org/3"
    IMG_URL = "https://image.tmdb.org/t/p/original"

    def __init__(self, session: aiohttp.ClientSession, token: str, language: str = "ru-RU"):
        self.session = session
        self.language = language
        self.headers = {
            "Authorization": f"Bearer {token}",
            "Accept": "application/json"
        }

    async def random_movie(self, animation: bool = False, pages: tuple[int, int] = (1, 50)) -> dict:
        params = {
            "sort_by": "popularity.desc",
            "page": random.randint(*pages),
            "language": self.language,
            "vote_count.gte": 500,
            "include_adult": "false"
        }
        if animation:
            params["with_genres"] = "16"
        else:
            params["without_genres"] = "16"

        for _ in range(3):
            params["page"] = random.randint(*pages)
            async with self.session.get(f"{self.BASE_URL}/discover/movie",
                                        params=params, headers=self.headers) as request:
                request.raise_for_status()
                data = await request.json()
            results = data.get("results", [])
            if results:
                return random.choice(results)

            pages = (1, min(pages[1], data.get("total_pages", 1) or 1))
        raise RuntimeError("TMDB не нашел фильм")

    async def random_image(self, animation: bool = False, pages: tuple[int, int] = (1, 50)) -> dict:
        for _ in range(5):
            movie = await self.random_movie(animation, pages)
            params = {"include_image_language": "null"}
            url = f"{self.BASE_URL}/movie/{movie["id"]}/images"
            async with self.session.get(url, params=params, headers=self.headers) as request:
                request.raise_for_status()
                data = await request.json()

            frames = [f for f in data.get("backdrops", []) if f.get("iso_639_1") is None and f["width"] <= 1920
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

    
