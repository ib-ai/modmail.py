import sqlite3

def database(func):
    def wrapper(*args,**kwargs):
        conn = sqlite3.connect('/database/modmail.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        ret = func(cursor, *args, *kwargs)
        conn.commit()
        conn.close()
        return ret
    return wrapper

@database
def get_ticket(cursor, ticket_id):
    sql = """
        SELECT ticket_id, user, open, message_id
        FROM mm_tickets
        WHERE ticket_id=?
    """
    cursor.execute(sql, [ticket_id])
    ticket = cursor.fetchone()
    if ticket is None or len(ticket) == 0:
        return -1
    else:
        return ticket

@database
def get_ticket_by_user(cursor, user):
    sql = """
        SELECT ticket_id, user, open, message_id
        FROM mm_tickets
        WHERE user=?
        AND open=1
    """
    cursor.execute(sql, [user])
    ticket = cursor.fetchone()
    if ticket is None or len(ticket) == 0:
        return {'ticket_id': -1, 'user': -1, 'open':0, 'message_id':-1}
    else:
        return ticket 

@database
def get_ticket_by_message(cursor, message_id):
    sql = """
        SELECT ticket_id, user, open, message_id
        FROM mm_tickets
        WHERE message_id=?
    """
    cursor.execute(sql, [message_id])
    ticket = cursor.fetchone()
    if ticket is None or len(ticket) == 0:
        return {'ticket_id': -1, 'user': -1, 'open':0, 'message_id':-1}
    else:
        return ticket 

@database
def open_ticket(cursor, user):
    sql = """
        INSERT INTO mm_tickets (user)
        VALUES (?)
    """
    cursor.execute(sql, [user])
    return cursor.lastrowid

@database
def update_ticket_message(cursor, ticket_id, message_id):
    sql = """
        UPDATE mm_tickets
        SET message_id=?
        WHERE ticket_id=?
    """
    cursor.execute(sql, [message_id, ticket_id])
    return cursor.rowcount != 0

@database
def close_ticket(cursor, ticket_id):
    sql = """
        UPDATE mm_tickets
        SET open=0
        WHERE ticket_id=?
    """
    cursor.execute(sql,[ticket_id])

    return cursor.rowcount != 0

@database
def get_ticket_responses(cursor, ticket_id):
    sql = """
        SELECT user, response, timestamp, as_server
        FROM mm_ticket_responses
        WHERE ticket_id=?
    """
    cursor.execute(sql, [ticket_id])
    return cursor.fetchall()

@database
def add_ticket_response(cursor, ticket_id, user, response, as_server):
    sql = """
        INSERT INTO mm_ticket_responses (ticket_id, user, response, as_server)
        VALUES (?, ?, ?, ?)
    """
    cursor.execute(sql, [ticket_id, user, response, as_server])
    return True

@database
def get_timeout(cursor, user):
    sql = """
        SELECT timestamp
        FROM mm_timeouts
        WHERE user=?
    """
    cursor.execute(sql , [user])
    timeout = cursor.fetchone()
    if timeout is None or len(timeout) == 0:
        return False
    else:
        return timeout

@database
def set_timeout(cursor, user, timestamp):
    sql = """
        INSERT OR REPLACE INTO mm_timeouts (user, timestamp)
        VALUES (?, ?)
    """
    cursor.execute(sql, [user, timestamp])
    return True

@database
def init(cursor):

    #Create modmail tickets table
    sql = """
    CREATE TABLE IF NOT EXISTS mm_tickets (
        ticket_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user INTEGER NOT NULL,
        open BOOLEAN DEFAULT 1 NOT NULL,
        message_id INTEGER
    );
    """
    result = cursor.execute(sql)

    #Create modmail ticket user index
    sql = "CREATE INDEX IF NOT EXISTS mm_tickets_user ON mm_tickets(user);"
    result = cursor.execute(sql)

    #Create modmail ticket message index
    sql = "CREATE INDEX IF NOT EXISTS mm_tickets_message ON mm_tickets(message_id);"
    result = cursor.execute(sql)

    #Create modmail ticket repsonses table
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
    result = cursor.execute(sql)

    #Create modmail ticket response ticket id index
    sql = "CREATE INDEX IF NOT EXISTS mm_ticket_responses_ticket_id ON mm_ticket_responses(ticket_id);"
    result = cursor.execute(sql)

    #Create modmail ticket response user index
    sql = "CREATE INDEX IF NOT EXISTS mm_ticket_responses_user ON mm_ticket_responses(user);"
    result = cursor.execute(sql)

    #Create modmail timeouts table
    sql = """
    CREATE TABLE IF NOT EXISTS mm_timeouts (
        timeout_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user INTEGER NOT NULL UNIQUE,
        timestamp TIMESTAMP DEFAULT (strftime('%s', 'now')) NOT NULL
    );
    """
    result = cursor.execute(sql)

    #Create modmail timeout user index
    sql = "CREATE UNIQUE INDEX IF NOT EXISTS mm_timeouts_user ON mm_timeouts(user);"
    result = cursor.execute(sql)

    return True