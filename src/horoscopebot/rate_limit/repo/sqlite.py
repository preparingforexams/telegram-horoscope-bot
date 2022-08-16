from __future__ import annotations

import logging
from contextlib import contextmanager
from pathlib import Path
from typing import List, Generator

from pendulum import DateTime
import sqlite3

from .. import RateLimitingRepo

_LOG = logging.getLogger(__name__)


class SqliteRateLimitingRepo(RateLimitingRepo):
    def __init__(self, connection: sqlite3.Connection):
        self._is_initialized = False
        self._connection = connection

    @classmethod
    def connect(cls, db_file: Path) -> SqliteRateLimitingRepo:
        connection = sqlite3.connect(db_file)
        return cls(connection)

    @contextmanager
    def _cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        cursor = self._connection.cursor()
        try:
            if not self._is_initialized:
                _LOG.info("Initializing database")
                cursor.execute(
                    """
                    CREATE TABLE IF NOT EXISTS usages (
                        context_id INT,
                        user_id INT,
                        time INT,
                        PRIMARY KEY (context_id, user_id, time)
                    );
                    """
                )
                cursor.execute(
                    """
                    CREATE INDEX IF NOT EXISTS usages_by_ids on usages (
                        context_id,
                        user_id,
                        time DESC
                    );
                    """
                )
                cursor.connection.commit()
                self._is_initialized = True

            yield cursor
            cursor.connection.commit()
        finally:
            cursor.close()

    def add_usage(
        self,
        context_id: int,
        user_id: int,
        utc_time: DateTime,
    ):
        with self._cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO usages (context_id, user_id, time)
                VALUES (?, ?, ?);
                """,
                [
                    context_id,
                    user_id,
                    int(utc_time.timestamp()),
                ],
            )

    def get_usages(
        self,
        context_id: int,
        user_id: int,
        limit: int = 1,
    ) -> List[DateTime]:
        with self._cursor() as cursor:
            result = cursor.execute(
                """
                SELECT time FROM usages
                WHERE context_id = ? AND user_id = ?
                ORDER BY time DESC
                LIMIT ?
                """,
                [context_id, user_id, limit],
            )
            datetimes = [DateTime.utcfromtimestamp(row[0]) for row in result]

        _LOG.info("Found {} datetimes, latest: {}", len(datetimes), datetimes[0])
        return datetimes
