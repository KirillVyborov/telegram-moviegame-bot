import aiosqlite

DB_PATH = "bot.db"

_cache: dict[int, int] = {}

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """CREATE TABLE IF NOT EXISTS scores (
            user_id INTEGER PRIMARY KEY,
            score INTEGER NOT NULL DEFAULT 0,
            name TEXT)"""
        )
        try:
            await db.execute("ALTER TABLE scores ADD COLUMN name TEXT")
        except aiosqlite.OperationalError:
            pass
        await db.commit()

async def add_point(user_id: int, points: int = 1, name: str | None = None) -> int:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            """INSERT INTO scores (user_id, score, name) VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
            score = score + ?,
            name = COALESCE(?, name)""",
            (user_id, points, name, points, name)
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

async def get_rank(user_id: int) -> int:
    score = await get_score(user_id)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT COUNT(*) FROM scores WHERE score > ?", (score,)
        ) as cur:
            row = await cur.fetchone()
    return row[0] + 1

async def get_top(limit: int = 3) -> list[tuple[str | None, int]]:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT name, score FROM scores WHERE score > 0 "
            "ORDER BY score DESC, user_id ASC LIMIT ?", (limit,)
        ) as cur:
            rows = await cur.fetchall()
    return [(name, score) for name, score in rows]

async def reset_progress(user_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM scores WHERE user_id = ?", (user_id,))
        await db.commit()
    _cache.pop(user_id, None)