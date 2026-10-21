import asyncio
import logging
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

    async def random_movie(self) -> dict:
        page = random.randint(1,50)
        params = {
            "sort_by": "popularity.desc",
            "page": page,
            "language": self.language,
            "vote_count.gte": 500
        }
        async with self.session.get(f"{self.BASE_URL}/discover/movie",
                                     params=params, headers=self.headers) as request:
            request.raise_for_status()
            data = await request.json()
        return random.choice(data["results"])

    async def random_image(self) -> dict:
        for _ in range(5):
            movie = await self.random_movie()
            params = {"include_image_language": "null"}
            async with self.session.get(
                f"{self.BASE_URL}/movie/{movie["id"]}/images",
                        params=params, headers=self.headers) as request:
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

    
