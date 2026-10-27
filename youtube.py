import logging
import aiohttp

from cache import cache
from retry import ServiceUnavailable, with_retry

logger = logging.getLogger(__name__)

class YouTubeClient:
    URL = "https://www.googleapis.com/youtube/v3/search"
    TTL = 7 * 24 * 3600

    def __init__(self, session: aiohttp.ClientSession, token: str):
        self.session = session
        self.token = token

    async def trailer_url(self, title: str, year: str | None = None) -> str | None:
        if not self.token:
            return None
        query = " ".join(x for x in (title, year, "трейлер") if x)
        try:
            return await cache.get_or_fetch(f"yt:{query}", self.TTL, lambda: self._search(query))
        except ServiceUnavailable:
            return None

    async def _search(self, query: str) -> str | None:
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "maxResults": 1,
            "regionCode": "RU",
            "relevanceLanguage": "ru",
            "key": self.token
        }

        async def call():
            async with self.session.get(self.URL, params=params,
                                        timeout=aiohttp.ClientTimeout(total=15)) as req:
                req.raise_for_status()
                return await req.json()

        data = await with_retry(call, name="YouTube")
        items = data.get("items", [])
        if not items:
            return None
        video_id = items[0].get("id", {}).get("videoId")
        return f"https://www.youtube.com/watch?v={video_id}" if video_id else None