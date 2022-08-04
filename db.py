import asyncio
import sqlite3

conn = sqlite3.connect('/database/modmail.db', check_same_thread=False)
conn.row_factory = sqlite3.Row

async def get_ticket(ticket_id):
    sql = """
        SELECT ticket_id, user, open, message_id
        FROM mm_tickets
        WHERE ticket_id=?
    """
    cursor = conn.cursor()
    blocking_insert = lambda: cursor.execute(sql, [ticket_id])
    result = await asyncio.to_thread(blocking_insert)
    ticket = result.fetchone()
    cursor.close()
    if ticket is None or len(ticket) == 0:
        return -1
    else:
        return ticket

async def get_ticket_by_user(user):
    sql = """
        SELECT ticket_id, user, open, message_id
        FROM mm_tickets
        WHERE user=?
        AND open=1
    """
    cursor = conn.cursor()
    blocking_insert = lambda: cursor.execute(sql, [user])
    result = await asyncio.to_thread(blocking_insert)
    ticket = result.fetchone()
    cursor.close()
    if ticket is None or len(ticket) == 0:
        return {'ticket_id': -1, 'user': -1, 'open':0, 'message_id':-1}
    else:
        return ticket 

async def get_ticket_by_message(message_id):
    sql = """
        SELECT ticket_id, user, open, message_id
        FROM mm_tickets
        WHERE message_id=?
    """
    cursor = conn.cursor()
    blocking_insert = lambda: cursor.execute(sql, [message_id])
    result = await asyncio.to_thread(blocking_insert)
    ticket = result.fetchone()
    cursor.close()
    if ticket is None or len(ticket) == 0:
        return {'ticket_id': -1, 'user': -1, 'open':0, 'message_id':-1}
    else:
        return ticket 

async def open_ticket(user):
    sql = """
        INSERT INTO mm_tickets (user)
        VALUES (?)
    """
    cursor = conn.cursor()
    blocking_insert = lambda: cursor.execute(sql, [user])
    result = await asyncio.to_thread(blocking_insert)
    rowid = result.lastrowid
    conn.commit()
    cursor.close()
    return rowid

async def update_ticket_message(ticket_id, message_id):
    sql = """
        UPDATE mm_tickets
        SET message_id=?
        WHERE ticket_id=?
    """
    cursor = conn.cursor()
    blocking_insert = lambda: cursor.execute(sql, [message_id, ticket_id])
    result = await asyncio.to_thread(blocking_insert)
    rowcount = result.rowcount != 0
    conn.commit()
    cursor.close()
    return rowcount

async def close_ticket(ticket_id):
    sql = """
        UPDATE mm_tickets
        SET open=0
        WHERE ticket_id=?
    """
    cursor = conn.cursor()
    blocking_insert = lambda: cursor.execute(sql,[ticket_id])
    result = await asyncio.to_thread(blocking_insert)
    rowcount = result.rowcount != 0
    conn.commit()
    cursor.close()

    return rowcount

async def get_ticket_responses(ticket_id):
    sql = """
        SELECT user, response, timestamp, as_server
        FROM mm_ticket_responses
        WHERE ticket_id=?
    """
    cursor = conn.cursor()
    blocking_insert = lambda: cursor.execute(sql, [ticket_id])
    result = await asyncio.to_thread(blocking_insert)
    responses = result.fetchall()
    cursor.close()
    return responses

async def add_ticket_response(ticket_id, user, response, as_server):
    sql = """
        INSERT INTO mm_ticket_responses (ticket_id, user, response, as_server)
        VALUES (?, ?, ?, ?)
    """
    cursor = conn.cursor()
    blocking_insert = lambda: cursor.execute(sql, [ticket_id, user, response, as_server])
    await asyncio.to_thread(blocking_insert)
    conn.commit()
    cursor.close()
    return True

async def get_timeout(user):
    sql = """
        SELECT timestamp
        FROM mm_timeouts
        WHERE user=?
    """
    cursor = conn.cursor()
    blocking_insert = lambda: cursor.execute(sql , [user])
    result = await asyncio.to_thread(blocking_insert)
    timeout = result.fetchone()
    cursor.close()
    if timeout is None or len(timeout) == 0:
        return False
    else:
        return timeout

async def set_timeout(user, timestamp):
    sql = """
        INSERT OR REPLACE INTO mm_timeouts (user, timestamp)
        VALUES (?, ?)
    """
    cursor = conn.cursor()
    blocking_insert = lambda: cursor.execute(sql, [user, timestamp])
    await asyncio.to_thread(blocking_insert)
    conn.commit()
    cursor.close()
    return True

async def init():

    # Create modmail tickets table
    # Create modmail ticket user index
    # Create modmail ticket message index
    # Create modmail ticket responses table
    # Create modmail ticket response ticket id index
    # Create modmail ticket response user index
    # Create modmail timeouts table
    # Create modmail timeout user index

    sql = """
    CREATE TABLE IF NOT EXISTS mm_tickets (
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user INTEGER NOT NULL,
        open BOOLEAN DEFAULT 1 NOT NULL,
        message_id INTEGER
    );
    CREATE INDEX IF NOT EXISTS mm_tickets_user ON mm_tickets(user);
    CREATE INDEX IF NOT EXISTS mm_tickets_message ON mm_tickets(message_id);
    CREATE TABLE IF NOT EXISTS mm_ticket_responses (
        response_id INTEGER PRIMARY KEY AUTOINCREMENT,
        ticket_id INTEGER,
        user INTEGER NOT NULL,
        response TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT (strftime('%s', 'now')) NOT NULL,
        as_server BOOLEAN NOT NULL,
        FOREIGN KEY (ticket_id) REFERENCES mm_tickets (ticket_id)
    );
    CREATE INDEX IF NOT EXISTS mm_ticket_responses_ticket_id ON mm_ticket_responses(ticket_id);
    CREATE INDEX IF NOT EXISTS mm_ticket_responses_user ON mm_ticket_responses(user);
    CREATE TABLE IF NOT EXISTS mm_timeouts (
        timeout_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user INTEGER NOT NULL UNIQUE,
        timestamp TIMESTAMP DEFAULT (strftime('%s', 'now')) NOT NULL
    );
    CREATE UNIQUE INDEX IF NOT EXISTS mm_timeouts_user ON mm_timeouts(user);
    """
    cursor = conn.cursor()
    blocking_insert = lambda: cursor.executescript(sql)
    await asyncio.to_thread(blocking_insert)
    conn.commit()
    cursor.close()

    return True