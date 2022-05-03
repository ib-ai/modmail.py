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

    #Create mm_tickets table
    sql = """
    CREATE TABLE IF NOT EXISTS mm_tickets (
        ticket_id INTEGER PRIMARY KEY,
        user INTEGER NOT NULL,
        open BOOLEAN DEFAULT TRUE NOT NULL,
        message_id INTEGER
    );
    """
    result = cursor.execute(sql)

    return True