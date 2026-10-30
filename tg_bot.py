import asyncio
import logging

import aiohttp
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import Settings
from tmdb import TMDBClient
from handlers import router
from db import init_db
from youtube import YouTubeClient
from utils.logging_setup import setup_logging

logger = logging.getLogger(__name__)

async def main():
    settings = Settings()
    setup_logging(settings.log_level)
    bot = Bot(token=settings.bot_token.get_secret_value(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout, trust_env=True) as session:
        dispatcher["tmdb"] = TMDBClient(
            session=session,
            token=settings.tmdb_token.get_secret_value()
        )
        dispatcher["youtube"] = YouTubeClient(
            session=session,
            token=settings.youtube_api_key.get_secret_value()
        )
        await init_db()
        logger.info("Бот старт")
        await bot.delete_webhook(drop_pending_updates=True)
        await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())


