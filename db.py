from contextlib import asynccontextmanager
from dataclasses import dataclass
import functools
from typing import Awaitable, Callable, Concatenate, Optional, ParamSpec, TypeVar
from aiosqlite import connect, Row, Cursor


PATH = "/database/modmail.db"

P = ParamSpec("P")
R = TypeVar("R")


@asynccontextmanager
async def db_ops():
    conn = await connect(PATH)
    conn.row_factory = Row
    cursor = await conn.cursor()
    yield cursor
    await conn.commit()
    await conn.close()


def async_db_cursor(
    func: Callable[Concatenate[Cursor, P], Awaitable[R]]
) -> Callable[P, Awaitable[R]]:
    @functools.wraps(func)
    async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
        async with db_ops() as cursor:
            return await func(cursor, *args, **kwargs)

    return wrapper


@dataclass
class Ticket:
    ticket_id: int
    user: int
    open: int
    message_id: Optional[int]


@dataclass
class TicketResponse:
    user: int
    response: str
    timestamp: int
    as_server: bool


@dataclass
class Timeout:
    timeout_id: int
    timestamp: int


@async_db_cursor
async def get_ticket(cursor: Cursor, ticket_id: int) -> Optional[Ticket]:
    sql = """
        SELECT ticket_id, user, open, message_id
        FROM mm_tickets
        WHERE ticket_id=?
    """
    await cursor.execute(sql, [ticket_id])
    ticket = await cursor.fetchone()
    if ticket is None or len(ticket) == 0:
        return None
    else:
        return Ticket(*ticket)


@async_db_cursor
async def get_ticket_by_user(cursor: Cursor, user: int) -> Optional[Ticket]:
    sql = """
        SELECT ticket_id, user, open, message_id
        FROM mm_tickets
        WHERE user=?
        AND open=1
    """
    await cursor.execute(sql, [user])
    ticket = await cursor.fetchone()
    if ticket is None or len(ticket) == 0:
        return None
    else:
        return Ticket(*ticket)


@async_db_cursor
async def get_ticket_by_message(cursor: Cursor, message_id: int) -> Optional[Ticket]:
    sql = """
        SELECT ticket_id, user, open, message_id
        FROM mm_tickets
        WHERE message_id=?
    """
    await cursor.execute(sql, [message_id])
    ticket = await cursor.fetchone()
    if ticket is None or len(ticket) == 0:
        return None
    else:
        return Ticket(*ticket)


@async_db_cursor
async def open_ticket(cursor: Cursor, user: int) -> Optional[int]:
    sql = """
        INSERT INTO mm_tickets (user)
        VALUES (?)
    """
    await cursor.execute(sql, [user])
    return cursor.lastrowid


@async_db_cursor
async def update_ticket_message(
    cursor: Cursor, ticket_id: int, message_id: int
) -> bool:
    sql = """
        UPDATE mm_tickets
        SET message_id=?
        WHERE ticket_id=?
    """
    await cursor.execute(sql, [message_id, ticket_id])
    return cursor.rowcount != 0


@async_db_cursor
async def close_ticket(cursor: Cursor, ticket_id: int) -> bool:
    sql = """
        UPDATE mm_tickets
        SET open=0
        WHERE ticket_id=?
    """
    await cursor.execute(sql, [ticket_id])
    return cursor.rowcount != 0


@async_db_cursor
async def get_ticket_responses(cursor: Cursor, ticket_id: int) -> list[TicketResponse]:
    sql = """
        SELECT user, response, timestamp, as_server
        FROM mm_ticket_responses
        WHERE ticket_id=?
    """
    await cursor.execute(sql, [ticket_id])
    rows = await cursor.fetchall()
    return [TicketResponse(*row) for row in rows]


@async_db_cursor
async def add_ticket_response(
    cursor: Cursor, ticket_id: int, user: int, response: str, as_server: bool
) -> Optional[int]:
    sql = """
        INSERT INTO mm_ticket_responses (ticket_id, user, response, as_server)
        VALUES (?, ?, ?, ?)
    """
    await cursor.execute(sql, [ticket_id, user, response, as_server])
    return cursor.lastrowid


@async_db_cursor
async def get_timeout(cursor: Cursor, user: int) -> Optional[Timeout]:
    sql = """
        SELECT timeout_id, timestamp
        FROM mm_timeouts
        WHERE user=?
    """
    await cursor.execute(sql, [user])
    timeout = await cursor.fetchone()
    if timeout is None or len(timeout) == 0:
        return None
    else:
        return Timeout(*timeout)


@async_db_cursor
async def set_timeout(cursor: Cursor, user: int, timestamp: int) -> Optional[int]:
    sql = """
        INSERT OR REPLACE INTO mm_timeouts (user, timestamp)
        VALUES (?, ?)
    """
    await cursor.execute(sql, [user, timestamp])
    return cursor.lastrowid


@async_db_cursor
async def init(cursor: Cursor):
    # Create modmail tickets table
    sql = """
    CREATE TABLE IF NOT EXISTS mm_tickets (
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user INTEGER NOT NULL,
        open BOOLEAN DEFAULT 1 NOT NULL,
        message_id INTEGER
    );
    """
    await cursor.execute(sql)

    # Create modmail ticket user index
    sql = "CREATE INDEX IF NOT EXISTS mm_tickets_user ON mm_tickets(user);"
    await cursor.execute(sql)

    # Create modmail ticket message index
    sql = "CREATE INDEX IF NOT EXISTS mm_tickets_message ON mm_tickets(message_id);"
    await cursor.execute(sql)

    # Create modmail ticket repsonses table
    sql = """
    CREATE TABLE IF NOT EXISTS mm_ticket_responses (
        response_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER,
        user INTEGER NOT NULL,
        response TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT (strftime('%s', 'now')) NOT NULL,
        as_server BOOLEAN NOT NULL,
        FOREIGN KEY (ticket_id) REFERENCES mm_tickets (ticket_id)
    );
    """
    await cursor.execute(sql)

    # Create modmail ticket response ticket id index
    sql = "CREATE INDEX IF NOT EXISTS mm_ticket_responses_ticket_id ON mm_ticket_responses(ticket_id);"
    await cursor.execute(sql)

    # Create modmail ticket response user index
    sql = "CREATE INDEX IF NOT EXISTS mm_ticket_responses_user ON mm_ticket_responses(user);"
    await cursor.execute(sql)

    # Create modmail timeouts table
    sql = """
    CREATE TABLE IF NOT EXISTS mm_timeouts (
        timeout_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user INTEGER NOT NULL UNIQUE,
        timestamp TIMESTAMP DEFAULT (strftime('%s', 'now')) NOT NULL
    );
    """
    await cursor.execute(sql)

    # Create modmail timeout user index
    sql = "CREATE UNIQUE INDEX IF NOT EXISTS mm_timeouts_user ON mm_timeouts(user);"
    await cursor.execute(sql)

    return True
