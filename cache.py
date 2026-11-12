import time
from configparser import ConfigParser


class Cache:
    def __init__(self, db, logger):
        self.db = db
        self.logger = logger
        # self.data = {}
        # self.sorted_titles_cache = None
        # self.url_pattern = re.compile(r'^https:\/\/[^\s]+$')
        self.cache_isactive: bool = True
        # self.reload_cache()
        # self.conn = psycopg2.connect(**config())
        # self.cur = self.conn.cursor()

    async def match(self, query: str):
        start = time.perf_counter()

        async with self.db.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT title
                FROM tracks
                WHERE title ILIKE $1
                ORDER BY weight DESC
                LIMIT 25
                """,
                f"%{query}%",
            )

        elapsed = (time.perf_counter() - start) * 1000
        self.logger.info(
            f"Cache query {query!r}: {elapsed:.2f} ms, {len(rows)} results"
        )
        return [row["title"] for row in rows]

    async def check_query(self, query: str):
        try:
            async with self.db.acquire() as conn:
                result = await conn.fetchrow(
                    """
                    SELECT id
                    FROM tracks
                    WHERE similarity(title, $1) > 0.8
                    LIMIT 1
                    """,
                    query,
                )

            if result:
                identifier = result["id"]
                self.logger.debug(
                    f"Found track for {query}: {identifier}"
                )
                return identifier

            self.logger.debug(
                f"Did not find any identifier, searching for: {query}"
            )
            return query

        except Exception:
            self.logger.exception(
                f"Failed to check query: {query}"
            )
            return query


    async def data_parser(self, title: str, identifier: str) -> None:
        if not self.cache_isactive:
            return

        try:
            async with self.db.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO tracks (id, title, weight)
                    VALUES ($1, $2, $3)
                    ON CONFLICT (id)
                    DO UPDATE SET
                        weight = tracks.weight + 1
                    """,
                    identifier,
                    title,
                    20,
                )

        except Exception:
            self.logger.exception(
                "Failed to update track cache for %s (%s)",
                title,
                identifier,
            )
