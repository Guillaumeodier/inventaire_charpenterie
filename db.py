import sqlite3

def init_db():
    conn = sqlite3.connect("stock.db")
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS types (
            id INTEGER PRIMARY KEY,
            nom TEXT UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS zones (
            id INTEGER PRIMARY KEY,
            nom TEXT UNIQUE
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS materiaux (
            id INTEGER PRIMARY KEY,
            nom TEXT,
            ref TEXT,
            type_id INTEGER,
            zone_id INTEGER,
            dimensions TEXT,
            qte INTEGER DEFAULT 0,
            prix REAL,
            commentaire TEXT,
            FOREIGN KEY(type_id) REFERENCES types(id),
            FOREIGN KEY(zone_id) REFERENCES zones(id)
        )
    ''')
    conn.commit()
    conn.close()

def get_connection():
    return sqlite3.connect("stock.db")
