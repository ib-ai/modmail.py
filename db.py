import sqlite3

def database(func):
    def wrapper(*args,**kwargs):
        conn = sqlite3.connect('modmail.db')
        cursor = conn.cursor()
        ret = func(cursor, *args, *kwargs)
        conn.commit()
        conn.close()
        return ret
    return wrapper

@database
def init(cursor):

    #Create modmail tickets table
    sql = """
    CREATE TABLE IF NOT EXISTS mm_tickets (
        ticket_id INTEGER PRIMARY KEY,
        user INTEGER NOT NULL,
        open BOOLEAN DEFAULT TRUE NOT NULL,
        message_id INTEGER
    );
    """
    result = cursor.execute(sql)

    #Create modmail ticket repsonses table
    sql = """
    CREATE TABLE IF NOT EXISTS mm_ticket_responses (
        response_id INTEGER PRIMARY KEY,
        ticket_id INTEGER,
        user INTEGER NOT NULL,
        response TEXT NOT NULL,
        timestamp DATETIME DEFAULT NOW() NOT NULL,
        as_server BOOLEAN NOT NULL,
        FOREIGN KEY(ticket_id) REFERENCES mm_tickets(ticket_id)
    );
    """
    result = cursor.execute(sql)

    #Create modmail timeouts table
    sql = """
    CREATE TABLE IF NOT EXISTS mm_timeouts (
        timeout_id INTEGER PRIMARY KEY,
        user INTEGER NOT NULL,
        timestamp DATETIME DEFAULT NOW() NOT NULL
    );
    """
    result = cursor.execute(sql)

    return True