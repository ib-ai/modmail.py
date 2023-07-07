from contextlib import asynccontextmanager
import aiosqlite
from typing import Optional

path = '/database/modmail.db'


@asynccontextmanager
async def db_ops():
    conn = await aiosqlite.connect(path)
    conn.row_factory = aiosqlite.Row
    cursor = await conn.cursor()
    yield cursor
    await conn.commit()
    await conn.close()


class Ticket:

    def __init__(self, ticket_id: int, user: int, open: int,
                 message_id: Optional[int]):
        self.ticket_id = ticket_id
        self.user = user
        self.open = open
        self.message_id = message_id

    def __repr__(self) -> str:
        return f"Ticket({self.ticket_id}, {self.user}, {self.open}, {self.message_id})"


class TicketResponse:

    def __init__(self, user: int, response: str, timestamp: int,
                 as_server: bool):
        self.user = user
        self.response = response
        self.timestamp = timestamp
        self.as_server = as_server

    def __repr__(self) -> str:
        return f"TicketResponse({self.user}, {self.response}, {self.timestamp}, {self.as_server})"


class Timeout:

    def __init__(self, timeout_id: int, timestamp: int):
        self.timeout_id = timeout_id
        self.timestamp = timestamp

    def __repr__(self) -> str:
        return f"Timeout({self.timeout_id}, {self.user}, {self.timestamp})"


async def get_ticket(ticket_id: int) -> Optional[Ticket]:
    sql = """
        SELECT ticket_id, user, open, message_id
        FROM mm_tickets
        WHERE ticket_id=?
    """
    async with db_ops() as cursor:
        await cursor.execute(sql, [ticket_id])
        ticket = await cursor.fetchone()
        if ticket is None or len(ticket) == 0:
            return None
        else:
            return Ticket(*ticket)


async def get_ticket_by_user(user: int) -> Optional[Ticket]:
    sql = """
        SELECT ticket_id, user, open, message_id
        FROM mm_tickets
        WHERE user=?
        AND open=1
    """
    async with db_ops() as cursor:
        await cursor.execute(sql, [user])
        ticket = await cursor.fetchone()
        if ticket is None or len(ticket) == 0:
            return None
        else:
            return Ticket(*ticket)


async def get_ticket_by_message(message_id: int) -> Optional[Ticket]:
    sql = """
        SELECT ticket_id, user, open, message_id
        FROM mm_tickets
        WHERE message_id=?
    """
    async with db_ops() as cursor:
        await cursor.execute(sql, [message_id])
        ticket = await cursor.fetchone()
        if ticket is None or len(ticket) == 0:
            return None
        else:
            return Ticket(*ticket)


async def open_ticket(user: int) -> Optional[int]:
    sql = """
        INSERT INTO mm_tickets (user)
        VALUES (?)
    """
    async with db_ops() as cursor:
        await cursor.execute(sql, [user])
        return cursor.lastrowid


async def update_ticket_message(ticket_id: int, message_id: int) -> bool:
    sql = """
        UPDATE mm_tickets
        SET message_id=?
        WHERE ticket_id=?
    """
    async with db_ops() as cursor:
        await cursor.execute(sql, [message_id, ticket_id])
        return cursor.rowcount != 0


async def close_ticket(ticket_id: int) -> bool:
    sql = """
        UPDATE mm_tickets
        SET open=0
        WHERE ticket_id=?
    """
    async with db_ops() as cursor:
        await cursor.execute(sql, [ticket_id])
        return cursor.rowcount != 0


async def get_ticket_responses(ticket_id: int) -> list[TicketResponse]:
    sql = """
        SELECT user, response, timestamp, as_server
        FROM mm_ticket_responses
        WHERE ticket_id=?
    """
    async with db_ops() as cursor:
        await cursor.execute(sql, [ticket_id])
        rows = await cursor.fetchall()
        return [TicketResponse(*row) for row in rows]


async def add_ticket_response(ticket_id: int, user: int, response: str,
                              as_server: bool) -> Optional[int]:
    sql = """
        INSERT INTO mm_ticket_responses (ticket_id, user, response, as_server)
        VALUES (?, ?, ?, ?)
    """
    async with db_ops() as cursor:
        await cursor.execute(sql, [ticket_id, user, response, as_server])
        return cursor.lastrowid


async def get_timeout(user: int) -> Optional[Timeout]:
    sql = """
        SELECT timeout_id, timestamp
        FROM mm_timeouts
        WHERE user=?
    """
    async with db_ops() as cursor:
        await cursor.execute(sql, [user])
        timeout = await cursor.fetchone()
        if timeout is None or len(timeout) == 0:
            return None
        else:
            return Timeout(*timeout)


async def set_timeout(user: int, timestamp: int) -> Optional[int]:
    sql = """
        INSERT OR REPLACE INTO mm_timeouts (user, timestamp)
        VALUES (?, ?)
    """
    async with db_ops() as cursor:
        await cursor.execute(sql, [user, timestamp])
        return cursor.lastrowid


async def init():
    async with db_ops() as cursor:
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
