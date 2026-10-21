import asyncio
import logging

import aiohttp
from aiogram import Bot, Dispatcher

from config import Settings
from tmdb import TMDBClient
from handlers import router
from db import init_db

logger = logging.getLogger(__name__)

async def main():
    settings = Settings()
    bot = Bot(token=settings.bot_token.get_secret_value())
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
        dispatcher["tmdb"] = TMDBClient(
            session=session,
            token=settings.tmdb_token.get_secret_value()
        )
        await init_db()
        await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


