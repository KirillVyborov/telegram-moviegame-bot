import aiosqlite

DB_PATH = "bot.db"

_cache: dict[int, int] = {}

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """CREATE TABLE IF NOT EXISTS scores (
            user_id INTEGER PRIMARY KEY,
            score INTEGER NOT NULL DEFAULT 0)"""
        )
        await db.commit()

async def add_point(user_id: int) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO scores (user_id, score) VALUES (?, 1)
            ON CONFLICT(user_id) DO UPDATE SET score = score + 1""",
            (user_id,)
        )

        await db.commit()
        async with db.execute(
            "SELECT score FROM scores WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()

    score = row[0]
    _cache[user_id] = score
    return score

async def get_score(user_id: int) -> int:
    if user_id in _cache:
        return _cache[user_id]

    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT score FROM scores WHERE user_id = ?", (user_id,)
        ) as cur:
            row = await cur.fetchone()

    score = row[0] if row else 0
    _cache[user_id] = score
    return score