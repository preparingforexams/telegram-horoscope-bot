from __future__ import annotations

import logging
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Generator

from pendulum import DateTime

from .. import RateLimitingRepo, Usage

_LOG = logging.getLogger(__name__)


class SqliteRateLimitingRepo(RateLimitingRepo):
    def __init__(self, connection: sqlite3.Connection):
        self._connection = connection

    @classmethod
    def connect(cls, db_file: Path) -> SqliteRateLimitingRepo:
        if not db_file.is_file():
            raise ValueError(f"Database file {db_file} does not exist or is not a file")
        connection = sqlite3.connect(db_file)
        return cls(connection)

    @contextmanager
    def _cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        cursor = self._connection.cursor()
        try:
            yield cursor
            cursor.connection.commit()
        finally:
            cursor.close()

    def add_usage(
        self,
        context_id: str,
        user_id: str,
        utc_time: DateTime,
        reference_id: str | None,
        response_id: str | None,
    ):
        with self._cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO usages (
                    context_id,
                    user_id,
                    time,
                    reference_id,
                    response_id
                )
                VALUES (?, ?, ?, ?, ?);
                """,
                [
                    context_id,
                    user_id,
                    int(utc_time.timestamp()),
                    reference_id,
                    response_id,
                ],
            )
        _LOG.debug("Inserted usage for user %s in context %s", user_id, context_id)

    def get_usages(
        self,
        context_id: str,
        user_id: str,
        limit: int = 1,
    ) -> List[Usage]:
        with self._cursor() as cursor:
            result = cursor.execute(
                """
                SELECT time, reference_id, response_id FROM usages
                WHERE context_id = ? AND user_id = ?
                ORDER BY time DESC
                LIMIT ?
                """,
                [context_id, user_id, limit],
            )
            usages = [
                Usage(
                    context_id=context_id,
                    user_id=user_id,
                    time=DateTime.utcfromtimestamp(row[0]),
                    reference_id=row[1],
                    response_id=row[2],
                )
                for row in result
            ]

        _LOG.debug(
            "Found %d usages for user %s in context %s (limit was %d)",
            len(usages),
            user_id,
            context_id,
            limit,
        )

        return usages
